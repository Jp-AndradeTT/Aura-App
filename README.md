# Aura: mentora financeira para faturas de cartão

React (Vite) + Flask + PostgreSQL. Login, onboarding guiado no primeiro acesso, histórico de faturas,
plano de reserva com IA (Claude), acompanhamento da reserva real guardada mês a mês, planilha Excel detalhada,
painel de uso para a mentora (só números agregados, nunca dados financeiros de um mentorado), recuperação de
senha por e-mail e política de privacidade.

## Segurança já incluída
- **Conta:** cadastro só pelo link do e-mail (a senha é criada nele: ninguém pré-registra o e-mail de outra pessoa),
  **verificação em duas etapas (TOTP)** opcional com códigos de recuperação de uso único e proteção contra reuso de código,
  recuperação do 2FA por link no e-mail + senha, convite opcional, bloqueio de 15 min após 5 erros (senha ou 2ª etapa), senha de 10+ caracteres, troca e exclusão de conta pedindo a senha,
  "sair de todos os dispositivos", avisos de segurança por e-mail e registro de atividade.
- **Sessão:** cookie `__Host-` HttpOnly + SameSite + checagem de origem (CSRF); token de 2ª etapa não abre sessão.
- **Dados:** financeiros **criptografados no banco** (Fernet); arquivo da fatura não é guardado; isolamento por usuário.
- **Recuperação de senha:** link de uso único (30 min) guardado como hash, enviado no fragmento `#`; resposta idêntica
  exista ou não o e-mail; derruba sessões; o 2FA continua exigido depois do reset.
- **Entradas:** tipo de arquivo verificado pelo conteúdo, valores validados (sem NaN), planilha sem injeção de fórmula,
  saída da IA limitada em tipo e tamanho (a IA nunca executa nada).
- **Abuso e custo:** limites por IP, cota diária de IA (leitura, plano e chat) por usuário e teto global mensal, e-mails em segundo plano (SMTP/Gmail ou Resend).
- **Cabeçalhos:** CSP restrita (sem recursos de terceiros: fontes próprias), HSTS, `X-Frame-Options`, `no-referrer`, `no-store`.
- **Dependências** com versão fixa (`npm audit` (completo, com ferramentas de desenvolvimento) e `pip-audit` sem vulnerabilidades conhecidas na data da revisão; rode-os de novo antes de cada entrega).

**Entrega ao cliente:** veja `docs/ENTREGA.md` (contas, publicação, testes, operação e limitações).

## Rodar localmente
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # gere JWT_SECRET e DATA_KEY (comandos no próprio arquivo) e coloque a ANTHROPIC_API_KEY
                          # ADMIN_EMAILS (opcional): e-mail da mentora, para ela ver o Painel de uso
python app.py            # http://localhost:5000 (SQLite local)

# Frontend (outro terminal)
cd frontend && npm install && npm run dev   # requer Node 22 LTS (mínimo 20.19)      # http://localhost:5173 (o Vite encaminha /api ao Flask)
```
Em modo debug (`FLASK_DEBUG=1`) sem `RESEND_API_KEY`, o link de redefinição de senha aparece no console do backend.
Se já criou um banco local antes desta versão, apague `backend/instance/aura.db` (novas tabelas e colunas).

## Banco de dados e migrações
Local: o banco SQLite é criado sozinho. **Produção (Postgres):** o `Dockerfile` roda `flask db upgrade` a cada deploy. Ao mudar `models.py`: `flask --app app db migrate -m "descrição"`, **revise o arquivo gerado** em `migrations/versions/` e faça commit.

## Testes automáticos
Dentro de `backend/` (com o ambiente virtual ativo): `python tests/regress.py` (todas as funções: cadastro, 2FA, planos, chat, Excel…) e `python tests/fuzz_inputs.py` (milhares de entradas malformadas contra todas as rotas; o resultado esperado é **0 erros 500**). Usam um banco temporário e simulam e-mail e IA. `python tests/run_on_postgres.py` roda tudo num PostgreSQL real embutido (`pip install pgserver`). **Rode os dois antes de cada entrega.**

## Publicar, operar e entregar
Tudo em `docs/ENTREGA.md`.
