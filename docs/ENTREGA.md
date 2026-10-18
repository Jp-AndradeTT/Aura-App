# Guia de entrega e operação do Aura

## 1. Contas necessárias (todas em nome do cliente)
| Serviço | Para quê | Observação |
|---|---|---|
| GitHub | Guardar o código | Repositório **privado** |
| Render | Hospedar app + banco | Defina limite de gastos |
| Anthropic (API) | Ler faturas e gerar planos | Crie chave exclusiva e **limite mensal de gasto** no painel |
| E-mail da mentora | Ativação de conta e recuperação de senha | **Gmail** (SMTP + senha de app) ou domínio próprio (ver 2.1) |
| Domínio + Cloudflare | Endereço próprio, HTTPS, proteção | Recomendado |

## 2. Publicar
1. Gere as chaves **localmente** e guarde em cofre de senhas (1Password, Bitwarden…):
   - `DATA_KEY`: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - **Sem a `DATA_KEY` os dados do banco são irrecuperáveis.** Guarde pelo menos 2 cópias em locais diferentes.
2. Suba o código no GitHub. No Render: **New → Blueprint** → escolha o repositório (usa `render.yaml` e `Dockerfile`).
3. Preencha as variáveis: `DATA_KEY`, `ANTHROPIC_API_KEY`, `APP_URL`, `RESEND_API_KEY`, `MAIL_FROM` (nos **dois** serviços que pedirem a `DATA_KEY`).
4. Aponte o domínio para o serviço `aura` e configure `APP_URL` com ele (https).
5. Se usar o proxy do Cloudflare: mude `TRUSTED_PROXIES` para `2`, SSL/TLS em **Full (strict)** e crie regras de *rate limiting* para `/api/auth/*`.
6. Ative backups do Postgres e teste uma restauração.

### 2.1 E-mail de envio
- **Gmail da mentora (mais simples):** ative a verificação em duas etapas na conta Google, crie uma **senha de app** em *Conta Google → Segurança → Senhas de app*, e preencha `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER=email@gmail.com`, `SMTP_PASSWORD=<senha de app>`, `MAIL_FROM=Aura <email@gmail.com>`. O Gmail tem limite diário de envios (suficiente para um grupo pequeno de clientes). A Render pode restringir SMTP em planos gratuitos: por isso o `render.yaml` usa plano pago; confirme nas regras atuais.
- **Domínio próprio** (ex.: `contato@marcadamentora.com.br`): verifique o domínio no Resend e use `RESEND_API_KEY`. O Resend **não** envia em nome de `@gmail.com`/`@outlook.com`.
- Teste a entrega e confira a pasta de **spam**.

Veja também `docs/CHECKLIST_VENDA.md` (o que falta decidir e fazer antes de vender).

## 3. Testes
Antes de publicar, rode `python tests/regress.py` e `python tests/fuzz_inputs.py` (ver README). Os testes automáticos usam SQLite e IA/e-mail simulados: **o Postgres do Render, o envio real de e-mail e a IA real só são validados no primeiro deploy**, com o checklist abaixo.

### Depois de publicar
- [ ] Se usar `INVITE_CODE`: o cadastro sem o código é recusado.
- [ ] Criar conta: o e-mail chega (confira o spam) e o link permite criar a senha.
- [ ] Entrar, ativar a verificação em duas etapas, sair e entrar de novo com o código.
- [ ] "Esqueci minha senha" chega e funciona; o link não funciona uma segunda vez.
- [ ] Enviar uma fatura real (PDF e foto) e conferir a leitura; gerar o plano com IA; baixar o Excel.
- [ ] Com outra conta, confirmar que não enxerga faturas da primeira.
- [ ] Errar a senha 5 vezes: a conta bloqueia por 15 minutos.
- [ ] Abrir `https://seu-dominio` em [securityheaders.com](https://securityheaders.com) e conferir nota alta.
- [ ] Com o e-mail da mentora em `ADMIN_EMAILS`: ela vê "Painel de uso" no menu; com outra conta, o item some e `/api/admin/usage` responde 403.

## 4. Operação
- **Chaves:** trocar `JWT_SECRET` desconecta todos os usuários (seguro). Para trocar a `DATA_KEY`, use `DATA_KEY=nova,antiga` e mantenha as duas.
- **Limpeza automática:** a tarefa `aura-purge` apaga registros de acesso com mais de 6 meses, links vencidos e contas nunca ativadas (7 dias).
- **Cliente perdeu o celular e os códigos do 2FA:** na tela de código há "Perdi o acesso": o sistema envia um link ao e-mail cadastrado e, ao abri-lo, pede a senha para desativar o 2FA (é o e-mail + senha combinados; ninguém precisa pedir a senha ao cliente). Se nem o e-mail estiver acessível, rode no Shell do serviço no Render: `flask --app app disable-2fa email@do.usuario` (só depois de a mentora confirmar a identidade). Tudo fica no registro de atividade.
- **Pessoa física (sem CNPJ):** a mentora é a controladora dos dados dos clientes dela mesmo sem CNPJ. Preencha nome e e-mail de contato na política; em regra, agentes de pequeno porte têm obrigações simplificadas (por exemplo, dispensa de encarregado), mas peça confirmação a um advogado.
- **Pedido LGPD:** acesso e exclusão são feitos pelo próprio usuário em *Minha conta*. Pedidos por e-mail ao encarregado devem ser respondidos no prazo legal.
- **Incidente de segurança:** troque `JWT_SECRET`, investigue, e avise usuários e ANPD conforme a regulamentação vigente (confirme prazos com o advogado).
- **Custos de IA:** a API da Anthropic é **paga por uso** (não há plano gratuito equivalente ao do site). Três travas: limites por usuário (`AI_EXTRACT_DAILY`, `AI_PLAN_DAILY`, `AI_CHAT_DAILY`), **teto global do app** (`AI_GLOBAL_MONTHLY_LIMIT`: ao atingir, o app segue com digitação manual e plano padrão) e o limite de gasto no painel da Anthropic. A IA é opcional: sem `ANTHROPIC_API_KEY` o app funciona sem ela.
- **A Aura (IA):** além da leitura da fatura e do plano, há o chat "Converse com a Aura". O tom de mentora e as regras (sem recomendar investimentos, sem aconselhamento jurídico) ficam em `backend/services/ai.py` (`PLAN_PROMPT` e `CHAT_SYSTEM`) e podem ser ajustados. **Os prompts não foram testados com a API real**: antes de entregar, rode faturas reais e leia as respostas com a mentora. O chat não é guardado no servidor.
- **Convite:** com `INVITE_CODE` preenchido, só quem recebe o código da mentora cria conta (recomendado, pois o público é fechado). Para trocar o código, altere a variável e republique.
- **Painel de uso da mentora:** preencha `ADMIN_EMAILS` com o e-mail de cadastro da mentora para liberar o item "Painel de uso" no menu dela (contas, atividade, uso da IA — nunca dados financeiros de um mentorado). Em branco, ninguém vê o painel.
- **Escala:** o app roda em **uma instância** (limitador de requisições em memória). Para mais de uma, use Redis em `RATELIMIT_STORAGE_URI`.

## 5. Limitações conhecidas
- A IA pode errar leituras e dar respostas imprecisas; a política e a tela avisam, e o cliente sempre confere os lançamentos.
- Os testes automáticos rodam em SQLite com IA e e-mail simulados; o `render.yaml`, o `Dockerfile`, o Postgres e o envio real de e-mail precisam ser validados no primeiro deploy.
- Mudanças futuras de estrutura do banco exigem uma nova migração (`flask db migrate`), revisada antes do deploy.
- O bloqueio de conta por tentativas pode ser usado por terceiros para travar uma conta por 15 minutos (troca aceitável por proteção contra força bruta).
- A leitura de fatura depende da IA e pode errar: o usuário sempre confere os lançamentos antes de gerar a análise.
- Textos legais (política de privacidade) são **modelo** e precisam de revisão jurídica. Termos de Uso não estão incluídos.
