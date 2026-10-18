# Checklist para colocar o Aura à venda

## Segunda auditoria: segurança e otimização (16/10/2026)
Revisão linha a linha de todo o backend, frontend, infraestrutura e testes, feita em paralelo por área
(autenticação/sessão, rotas de dados, serviços de IA e e-mail, modelos/banco, frontend React, infraestrutura e
suíte de testes). Cada achado foi conferido contra o código real antes de corrigir (dois "achados" de um dos
agentes eram falsos positivos — tratamento de erro que já existia no chamador — e não geraram mudança).
Corrigido nesta rodada:
- **Condições de corrida (concorrência real: o servidor roda com várias threads no mesmo processo)**:
  - Bloqueio após 5 tentativas de senha/2FA: o contador era lido e regravado em Python; duas tentativas
    simultâneas podiam "pisar" uma na outra e nunca disparar o bloqueio. Agora é um `UPDATE` atômico no banco.
  - Cota mensal global de IA: mesmo risco, corrigido travando a linha do usuário (`SELECT ... FOR UPDATE`) até o
    commit.
  - Login com 2FA: duas requisições simultâneas com o **mesmo** código TOTP não conseguem mais autenticar as
    duas (a linha do usuário é travada antes de validar o código).
  - `change-password`, `2fa/enable`, `2fa/disable` e excluir conta não respeitavam o bloqueio por tentativas nem
    contavam senha errada como falha — um cookie de sessão roubado permitia tentar a senha sem limite. Corrigido.
- **Perda silenciosa de dados**: `PUT /api/invoices/<id>` com corpo parcial (por exemplo, só o rótulo) apagava
  lançamentos e perfil, porque a rota sempre reconstruía os 5 campos da fatura. Agora só altera o que vier no
  corpo. (O frontend atual sempre envia o corpo completo, então isso nunca foi disparado em uso real, mas era um
  risco de contrato de API para qualquer integração futura.)
- **Segredo de sessão (`JWT_SECRET`)**: o servidor agora recusa iniciar se a variável não estiver definida ou
  tiver menos de 32 caracteres, em vez de seguir com um valor fraco.
- **IA mais isolada de conteúdo não confiável**: as instruções de sistema passaram do texto do usuário para o
  parâmetro `system` da API da Anthropic (prioridade maior, menos sujeito a uma fatura tentar "instruir" o
  modelo); cliente da IA agora reaproveitado entre chamadas e com tempo-limite configurável.
- **Banco de dados**: `created_at` de `User`, `AuditLog`, `UsageLog` e `ReserveEntry` agora é obrigatório
  (`NOT NULL`); os índices separados de `user_id` e `created_at` em `UsageLog`/`ReserveEntry` foram substituídos
  por um único índice composto `(user_id, created_at)`, que é o que as consultas reais usam (cota diária, resumo
  da reserva). Migração gerada e testada em PostgreSQL real — incluindo o caso de linhas antigas com
  `created_at` nulo, preenchidas automaticamente antes de travar a coluna.
- **Frontend**: resposta antiga sobrescrevendo a tela atual ao trocar de fatura ou mover o slider do plano
  rapidamente (corrigido com guarda de sequência/"ignore" nas telas afetadas); uso do índice da lista como
  identidade de linha ao editar lançamentos (podia confundir um campo com outro ao apagar um item do meio);
  validações que faltavam no navegador (tamanho/tipo de arquivo, limites de caracteres).
- **Infraestrutura**: `.gitignore`/`.dockerignore` não cobriam todas as variações de banco SQLite local;
  `.dockerignore` agora também exclui testes e documentação da imagem de produção; `ALLOWED_ORIGINS` passou a
  estar documentada no `.env.example`.
- **Testes**: corrigido um bug no ataque de entradas malformadas que nunca exercitava a rota de apagar reserva
  (só `<int:iid>` era substituído na URL, nunca `<int:rid>`); a regressão funcional ganhou 13 novos casos —
  acesso cruzado a fatura de outro cliente (IDOR) em leitura/edição/exclusão/exportação, apagar fatura (caminho
  de sucesso, sem nenhuma cobertura antes), `logout-all` derrubando **outros** dispositivos de verdade, trocar
  senha e desativar 2FA. Total: **47/47** verificações, 0 erros 500 em 2578 requisições, confirmado várias vezes
  em SQLite e em PostgreSQL real.

Deixado de propósito para depois (backlog, sem urgência):
- Usar `Decimal` em vez de `float` nos cálculos monetários — nenhum erro de centavo observado na prática, mas
  seria mais correto a longo prazo.
- `HEALTHCHECK` e `EXPOSE` no Dockerfile; fixar a imagem base do Docker por digest em vez de tag.
- Índice composto `(event, created_at)` em `AuditLog` — só compensaria com um volume de eventos por usuário bem
  maior do que o atual.
- Build Docker do serviço de cron reaproveitando camadas com o serviço principal.
- Nota sobre `hide_password` em `migrations/env.py` caso o Sentry (ou outro serviço de erros) seja adotado no
  futuro — não aplicável hoje, pois nenhum está em uso.

## Novidades (16/10/2026): onboarding guiado, reserva real e painel de uso da mentora
Três funcionalidades pedidas pela cliente, implementadas e testadas:
- **Onboarding guiado no primeiro acesso**: quem ainda não enviou nenhuma fatura vê 4 passos simples (enviar
  fatura → conferir lançamentos → informar renda e gastos fixos → receber o plano) em vez de uma tela vazia.
- **Reserva de verdade**: além da projeção (quanto o mentorado *deveria* guardar), agora ele registra quanto
  *guardou de fato* a cada mês (valor + nota opcional), com uma barra de progresso até a meta calculada pelo
  plano mais recente. Guardado em `ReserveEntry`, criptografado como o resto dos dados financeiros, com as
  mesmas proteções de posse (um mentorado nunca acessa ou apaga o registro de outro — testado).
- **Painel de uso (mentora)**: a mentora vê só números agregados — total de contas, ativos nos últimos 30 dias,
  novos cadastros, faturas analisadas, e uso da IA hoje/mês vs. os limites configurados. **Nunca** um valor, nota
  ou dado financeiro de um mentorado específico. Liberado só para e-mails em `ADMIN_EMAILS` (ver `.env.example`
  e `render.yaml`); qualquer outra conta recebe 403 na API e não vê o item no menu — confirmado em teste
  automático (busca pelos valores exatos digitados pelo mentorado de teste na resposta do painel, para garantir
  que não vazam) e em teste manual (conta sem permissão: sem o item no menu e 403 ao chamar a rota direto).
- Isso atualiza a decisão anterior "Painel da mentora: não é necessário" — a cliente pediu um painel, mas
  **apenas de uso/adoção**, mantendo a regra original de que a mentora nunca vê dados financeiros de ninguém.
- Testes automáticos: regressão funcional subiu de 25/25 para **34/34** (9 novos casos cobrindo as rotas de
  reserva e o painel de uso) e o ataque de entradas malformadas continua em **0 erros 500** (2578 requisições),
  ambos confirmados em SQLite e em PostgreSQL real, cada um rodado várias vezes seguidas para garantir
  resultado estável (um teste pré-existente tinha uma pequena falha de ordenação que só aparecia no Postgres;
  foi corrigida).

## Auditoria completa de segurança (15/10/2026)
Revisão de ponta a ponta antes do primeiro envio ao cliente final: leitura de todo o código (backend e frontend),
checagem de dependências, testes automáticos e simulação manual de um usuário real e de um atacante contra um
servidor de produção real (Gunicorn + PostgreSQL, sem debug). Resultado:
- **Dependências**: `pip-audit` (backend) e `npm audit` (frontend) → **0 vulnerabilidades conhecidas**.
- **Testes automáticos**: regressão funcional (25/25) e ataque de 2578 entradas malformadas (0 erros 500), rodados
  em SQLite **e em PostgreSQL real**, confirmando migrações e driver corretos.
- **Testado manualmente como atacante** (servidor de produção real): login/senha forjados, cookie de sessão
  forjado (inclusive truque `alg=none` do JWT), acesso cruzado a fatura de outro cliente (IDOR) em leitura,
  edição, exclusão e exportação, CSRF de outra origem, força bruta de login (bloqueio após 5 tentativas), upload
  de arquivo disfarçado de PDF, arquivo maior que 10 MB, reuso de código 2FA (TOTP e de recuperação) e reuso de
  link de verificação/redefinição de senha. **Todos os ataques foram bloqueados corretamente.**
- **Corrigido nesta rodada**: o bloqueio de CSRF (`csrf_guard` em `backend/app.py`) aceitava uma requisição que
  alterasse dados se ela viesse **sem** o cabeçalho `Origin`. Isso já era mitigado pelo cookie `SameSite=Lax`
  (não é um caminho de ataque fácil num navegador comum), mas foi fechado por completo: agora toda requisição
  que cria, edita ou apaga dados exige um `Origin` correspondente ao site. Os testes automáticos foram
  atualizados para cobrir esse caso (confirmado: sem Origin = recusado, Origin errada = recusada, Origin certa = aceita).
- **Testado também**: exportar meus dados e excluir conta (LGPD) com exclusão em cascata das faturas confirmada
  diretamente no banco; recuperação de 2FA por perda de aparelho; redefinição de senha derruba sessões abertas
  mas continua exigindo o código de 2FA (a senha sozinha não basta).

## Já pronto no produto
- Conta com e-mail confirmado, senha forte, 2FA opcional, bloqueio por tentativas, recuperação de senha e de 2FA.
- Dados financeiros criptografados no banco; isolamento por usuário; exportar e excluir dados (LGPD).
- Cota de IA por usuário e teto mensal global; convite opcional.
- Migrações de banco (`flask db`), checagem de saúde do banco, limpeza automática de dados antigos.
- Testes automáticos, incluindo **PostgreSQL real** e ataque de entradas malformadas (0 erros 500).
- Termos de Uso e Política de Privacidade (**modelos**).

## Antes de vender (decisões e tarefas que NÃO dependem de código)
1. **Revisão jurídica** dos Termos de Uso e da Política (obrigatória). Preencher nome, e-mail de contato, foro, valores e datas.
2. **Contratos dos operadores**: confira os termos de tratamento de dados da Anthropic (IA), da Render (hospedagem) e do provedor de e-mail e reflita na Política.
3. **Domínio próprio** (ex.: `app.seudominio.com.br`) e e-mail remetente do mesmo domínio com SPF, DKIM e DMARC (melhor entrega do que Gmail).
4. **Backups**: ative os backups do Postgres, **teste uma restauração** e guarde a `DATA_KEY` em dois lugares seguros.
5. **Monitoramento**: um monitor de disponibilidade em `/api/health` (UptimeRobot ou similar) e um serviço de erros (ex.: Sentry, que deve constar na Política se for usado).
6. **Qualidade da IA**: teste com 10 ou mais faturas reais de bancos diferentes e ajuste os textos em `backend/services/ai.py`.
7. **Suporte**: defina o canal, o prazo de resposta e quem confirma a identidade em casos de perda de acesso.
8. **Plano de incidente**: quem avisa clientes e a ANPD se houver vazamento (confirme prazos com o advogado).
9. **`ADMIN_EMAILS`**: configure no Render (ou `.env`) o e-mail de cadastro da mentora para ela ver o Painel de
   uso. Em branco, ninguém vê o painel (comportamento seguro por padrão).

## Decisões já confirmadas pela cliente (não exigem código novo)
- **Cobrança**: já está incluída na mentoria da profissional. O app **não** precisa de cobrança/assinatura própria (sem Stripe, Asaas, Pix recorrente, nota fiscal). Nenhuma mudança necessária.
- **Painel da mentora**: implementado como painel de **uso/adoção**, não de dados financeiros (ver seção "Novidades" acima). A mentora continua sem acesso a parcelas, faturas ou planos de nenhum mentorado, atuando só como responsável legal pelo tratamento de dados (já refletido na Política de Privacidade, seção 1).

## Ainda em aberto (aguardando resposta da cliente)
- **Convites**: hoje há um único código compartilhado (`INVITE_CODE`) usado por todos os mentorados. Falta decidir se isso é suficiente ou se cada mentorado deve receber um convite individual por e-mail (mais seguro, permite revogar um convite sem afetar os demais, e facilita saber quem ainda não se cadastrou).

## Funcionalidades que o produto AINDA NÃO tem (fora do escopo atual, não pedidas)
- **Mais de uma mentora** (multi-inquilino): hoje o app atende uma mentora e seus clientes.
- Notificações (lembrete de vencimento), importação por Open Finance, app móvel.
