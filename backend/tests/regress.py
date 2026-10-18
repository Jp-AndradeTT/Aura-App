"""Teste automático do backend. Rode dentro de backend/:  python tests/regress.py
Não envia e-mails nem chama a IA de verdade (são simulados).
Para testar no Postgres: defina TEST_DATABASE_URL (e AUTO_CREATE_DB=0 depois de rodar `flask db upgrade`)."""
import os, sys, json, io, zipfile, time, types, secrets
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cryptography.fernet import Fernet
import tempfile
DB = os.path.join(tempfile.gettempdir(), "aura_regress_test.db")  # banco temporário; nunca toca no seu aura.db
os.environ.update(JWT_SECRET="x"+secrets.token_hex(16), DATA_KEY=Fernet.generate_key().decode(), COOKIE_SECURE="0", DATABASE_URL=os.getenv("TEST_DATABASE_URL") or "sqlite:///" + DB.replace(os.sep, "/"), INVITE_CODE="Turma-Aura-2026")
if os.path.exists(DB): os.remove(DB)
import pyotp, app as A, services.ai as AI
_orig_ai_client = AI._client  # guardado antes de qualquer mock, para testar o caminho real "sem chave de IA" mais abaixo
from models import db
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient

_RawClient = A.app.test_client_class or FlaskClient  # cliente sem Origin automático, para testar o csrf_guard de propósito

class _OriginClient(_RawClient):
    """Todo navegador real envia Origin em POST/PUT/PATCH/DELETE (até no mesmo site); o teste simula isso."""
    def open(self, *a, **kw):
        h = kw.get("headers")
        h = Headers(h) if h is not None and not isinstance(h, Headers) else (h or Headers())
        if "Origin" not in h:
            h.set("Origin", "http://localhost")
        kw["headers"] = h
        return super().open(*a, **kw)

A.app.test_client_class = _OriginClient
A.limiter.enabled = False
with A.app.app_context():  # começa sempre de tabelas vazias (serve para SQLite e Postgres)
    for _t in reversed(db.metadata.sorted_tables):
        db.session.execute(_t.delete())
    db.session.commit()
res = []
def ok(name, cond): res.append((name, bool(cond))); 
mail = {}
A.send_verify_email = lambda e,n,l: mail.update(v=l); A.send_reset_email = lambda e,n,l: mail.update(r=l)
A.send_mfa_reset_email = lambda e,n,l: mail.update(m=l); A.send_exists_email = lambda e,n: None; A.send_security_email = lambda *a: None
S = lambda r: r.status_code
c = A.app.test_client(); P = "senha-forte-123"; EM = "andradejj122@gmail.com"
reg = lambda inv: c.post("/api/auth/register", json={"name":"João Pedro","email":EM,"accept_privacy":True,"invite":inv})
ok("cadastro sem convite recusado (400)", S(reg("")) == 400)
ok("convite com travessão/acento recusado SEM erro 500 (400)", S(reg("Turma–Aura–2026")) == 400 and S(reg("Turmá-Aura-2026")) == 400)
ok("convite certo aceito (202)", S(reg("Turma-Aura-2026")) == 202)
ok("convite com espaço invisível/BOM é normalizado (202)", S(reg("\ufeffTurma-Aura-2026\u200b ")) == 202)
tok = mail["v"].split("#verify=")[1]
ok("ativar com senha fraca (400) e depois forte (200)", S(c.post("/api/auth/verify", json={"token":tok,"password":"123"})) == 400 and S(c.post("/api/auth/verify", json={"token":tok,"password":P})) == 200)
ok("login (200)", S(c.post("/api/auth/login", json={"email":EM,"password":P})) == 200)
raw = _RawClient(A.app, A.app.response_class)
raw.post("/api/auth/login", json={"email":EM,"password":P}, headers={"Origin": "http://localhost"})
ok("CSRF: POST sem header Origin é recusado (403)", S(raw.post("/api/invoices", json={"label":"x","items":[],"profile":{}})) == 403)
ok("CSRF: POST com Origin de outro site é recusado (403)", S(raw.post("/api/invoices", json={"label":"x","items":[],"profile":{}}, headers={"Origin": "https://evil.example"})) == 403)
ok("CSRF: POST com Origin correta é aceito (201)", S(raw.post("/api/invoices", json={"label":"x","items":[],"profile":{}}, headers={"Origin": "http://localhost"})) == 201)
items = [{"d":'=HYPERLINK("http://x","y")',"c":"Alimentação","v":482.35,"a":0,"t":0},{"d":"Notebook","c":"Eletrônicos","v":389.9,"a":4,"t":10}]
r = c.post("/api/invoices", json={"label":"Fatura João","bank":"Nubank","items":items,"profile":{"renda":6500,"fixos":3200,"meta":6,"venc":10},"reserve_pct":60}); i = r.get_json()["id"]
ok("criar fatura (201) com nome acentuado", S(r) == 201 and r.get_json()["label"] == "Fatura João")
ok("listar / abrir / atualizar", S(c.get("/api/invoices")) == 200 and S(c.get(f"/api/invoices/{i}")) == 200 and S(c.put(f"/api/invoices/{i}", json={"label":"Nova","items":items,"profile":{"renda":7000,"fixos":3000,"meta":6,"venc":10},"reserve_pct":50})) == 200)
x = c.get(f"/api/invoices/{i}/export"); xml = zipfile.ZipFile(io.BytesIO(x.data)).read("xl/worksheets/sheet2.xml").decode()
ok("Excel gerado (8 abas) e sem fórmula executável", S(x) == 200 and "<f>" not in xml and len(zipfile.ZipFile(io.BytesIO(x.data)).namelist()) > 8)

# reserva real
res0 = c.get("/api/reserve").get_json()
ok("reserva vazia no início, com meta vinda da fatura", res0["entries"] == [] and res0["total"] == 0.0 and res0["meta"]["valor"] > 0)
ok("registrar reserva com valor zero/negativo/não numérico é recusado (400)", S(c.post("/api/reserve", json={"valor": 0})) == 400 and S(c.post("/api/reserve", json={"valor": -5})) == 400 and S(c.post("/api/reserve", json={"valor": "abc"})) == 400)
r = c.post("/api/reserve", json={"valor": 250.5, "nota": "13º adiantado"}); rid = r.get_json()["entries"][0]["id"]
ok("registrar reserva válida soma no total (201)", S(r) == 201 and r.get_json()["total"] == 250.5 and r.get_json()["entries"][0]["nota"] == "13º adiantado")
c.post("/api/reserve", json={"valor": 100})
ok("segunda entrada soma certo (350.5)", c.get("/api/reserve").get_json()["total"] == 350.5)
reg2 = c.post("/api/auth/register", json={"name":"Outra Pessoa","email":"outra.pessoa@example.com","accept_privacy":True,"invite":"Turma-Aura-2026"})
tok2 = mail["v"].split("#verify=")[1]
c.post("/api/auth/verify", json={"token":tok2,"password":P})
c_outra = A.app.test_client(); c_outra.post("/api/auth/login", json={"email":"outra.pessoa@example.com","password":P})

# IDOR de fatura: outro usuário não pode ler, editar, exportar nem apagar a fatura de quem não é dele
ok("IDOR: outro usuário não vê/edita/exporta/apaga fatura alheia (404 em tudo)",
   S(c_outra.get(f"/api/invoices/{i}")) == 404 and S(c_outra.put(f"/api/invoices/{i}", json={"label":"hackeado","items":[],"profile":{}})) == 404 and
   S(c_outra.get(f"/api/invoices/{i}/export")) == 404 and S(c_outra.delete(f"/api/invoices/{i}")) == 404)
ok("fatura do dono segue intacta depois das tentativas alheias", c.get(f"/api/invoices/{i}").get_json()["label"] == "Nova")

# apagar fatura: caminho de sucesso (sem nenhuma cobertura antes)
r_del = c.post("/api/invoices", json={"label":"Para apagar","items":[],"profile":{"renda":1000,"fixos":500,"meta":6,"venc":5}})
id_del = r_del.get_json()["id"]
ok("apagar fatura: sucesso (204) e some da lista (404 depois)", S(c.delete(f"/api/invoices/{id_del}")) == 204 and S(c.get(f"/api/invoices/{id_del}")) == 404)

ok("IDOR: outro usuário não apaga reserva alheia (404) e total não muda", S(c_outra.delete(f"/api/reserve/{rid}")) == 404 and c.get("/api/reserve").get_json()["total"] == 350.5)
ok("dono apaga sua própria entrada (total volta a 100)", S(c.delete(f"/api/reserve/{rid}")) == 200 and c.get("/api/reserve").get_json()["total"] == 100.0)

# painel de uso (mentora): acesso restrito e sem dados financeiros
ok("painel de uso: usuário comum recebe 403", S(c.get("/api/admin/usage")) == 403)
A.ADMIN_EMAILS.add(EM)
try:
    adm = c.get("/api/admin/usage")
    body_adm = json.dumps(adm.get_json())
    ok("painel de uso: mentora vê números agregados (200) e NUNCA um valor em R$ de mentorado",
       S(adm) == 200 and adm.get_json()["usuarios"]["total"] >= 2 and "250.5" not in body_adm and "350.5" not in body_adm and "13º adiantado" not in body_adm)
    ok("outro usuário (não mentora) continua recebendo 403", S(c_outra.get("/api/admin/usage")) == 403)
finally:
    A.ADMIN_EMAILS.discard(EM)  # mesmo se uma asserção acima falhar, não deixa ADMIN_EMAILS poluído pro resto do teste

# logout-all: derruba a sessão de quem pediu E de qualquer outro dispositivo (token_version muda no servidor)
c_outra2 = A.app.test_client(); c_outra2.post("/api/auth/login", json={"email":"outra.pessoa@example.com","password":P})
ok("dois 'dispositivos' (duas sessões) acessam normalmente antes do logout-all", S(c_outra.get("/api/me/activity")) == 200 and S(c_outra2.get("/api/me/activity")) == 200)
ok("logout-all responde 200 a quem pediu", S(c_outra.post("/api/auth/logout-all")) == 200)
ok("logout-all também derruba a sessão do OUTRO dispositivo (token_version mudou)", S(c_outra.get("/api/me/activity")) == 401 and S(c_outra2.get("/api/me/activity")) == 401)
c_outra.post("/api/auth/login", json={"email":"outra.pessoa@example.com","password":P})  # entra de novo para os próximos testes

# change-password
ok("trocar senha: senha atual errada (403)", S(c_outra.post("/api/auth/change-password", json={"current_password":"senha-errada","new_password":"nova-senha-outra-1"})) == 403)
ok("trocar senha: nova senha fraca (400)", S(c_outra.post("/api/auth/change-password", json={"current_password":P,"new_password":"123"})) == 400)
c_outra3 = A.app.test_client(); c_outra3.post("/api/auth/login", json={"email":"outra.pessoa@example.com","password":P})
ok("trocar senha: sucesso (200)", S(c_outra.post("/api/auth/change-password", json={"current_password":P,"new_password":"nova-senha-outra-1"})) == 200)
ok("trocar senha derruba as outras sessões mas mantém a atual", S(c_outra3.get("/api/me/activity")) == 401 and S(c_outra.get("/api/me/activity")) == 200)

# 2fa/disable
sec_outra = c_outra.post("/api/2fa/setup").get_json()["secret"]; T_outra = pyotp.TOTP(sec_outra)
c_outra.post("/api/2fa/enable", json={"password":"nova-senha-outra-1","code":T_outra.now()})
ok("2fa/disable: código incorreto (403)", S(c_outra.post("/api/2fa/disable", json={"password":"nova-senha-outra-1","code":"000000"})) == 403)
ok("2fa/disable: senha incorreta (403)", S(c_outra.post("/api/2fa/disable", json={"password":"senha-errada","code":T_outra.at(time.time()+30)})) == 403)
ok("2fa/disable: sucesso (200) e desativa de fato", S(c_outra.post("/api/2fa/disable", json={"password":"nova-senha-outra-1","code":T_outra.at(time.time()+30)})) == 200 and c_outra.get("/api/me").get_json()["user"]["totp"] is False)

calls = []
class M:
    def __init__(s, t): s.t = t
    def create(s, **kw): calls.append(kw); return types.SimpleNamespace(content=[types.SimpleNamespace(text=s.t)])
AI._client = lambda: types.SimpleNamespace(messages=M(json.dumps({"diagnostico":"d","proximo_passo":"p","passos":[{"titulo":"a","valor":"b","detalhes":["c"]}],"recomendacoes":[{"titulo":"t","texto":"x"}],"incentivo":"i","alertas":[]})))
r = c.post(f"/api/invoices/{i}/plan", json={"use_ai":True}).get_json(); ok("plano com IA (campos de mentora)", r["ai"] and r["plan"]["proximo_passo"] == "p" and len(r["plan"]["recomendacoes"]) == 1)
AI._client = lambda: types.SimpleNamespace(messages=M("Resposta da Aura"))
ok("chat com a Aura", c.post(f"/api/invoices/{i}/chat", json={"messages":[{"role":"user","content":"Posso parcelar? ç"}]}).get_json()["reply"] == "Resposta da Aura")
AI._client = lambda: types.SimpleNamespace(messages=M('{"banco":["x"],"vencimento_dia":"99","itens":[{"descricao":"Mercado ç","categoria":null,"valor":"12.5","parcela_atual":"2","total_parcelas":"5"},7]}'))
r = c.post("/api/invoices/extract", data={"file": (io.BytesIO(b"%PDF-1.4 x"), "f.pdf", "application/pdf")}, content_type="multipart/form-data"); j = r.get_json()
ok("leitura de fatura devolve dados saneados", S(r) == 200 and j["banco"] == "" and j["vencimento_dia"] is None and j["items"][0]["v"] == 12.5 and j["items"][0]["c"] == "Outros" and len(j["items"]) == 1)
# sem chave de IA de verdade: usa a função real (não mockada) com ANTHROPIC_API_KEY ausente
old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
AI._client = _orig_ai_client
r_noai = c.post(f"/api/invoices/{i}/plan", json={"use_ai": True})
r_extract_noai = c.post("/api/invoices/extract", data={"file": (io.BytesIO(b"%PDF-1.4 x"), "f.pdf", "application/pdf")}, content_type="multipart/form-data")
ok("sem ANTHROPIC_API_KEY: plano cai no padrão (200, ai=False) e leitura de fatura responde 503, nunca 500",
   S(r_noai) == 200 and r_noai.get_json()["ai"] is False and S(r_extract_noai) == 503)
if old_key is not None:
    os.environ["ANTHROPIC_API_KEY"] = old_key
# 2FA
sec = c.post("/api/2fa/setup").get_json()["secret"]; T = pyotp.TOTP(sec)
codes = c.post("/api/2fa/enable", json={"password":P,"code":T.now()}).get_json()["recovery_codes"]
c2 = A.app.test_client(); mt = c2.post("/api/auth/login", json={"email":EM,"password":P}).get_json()["mfa_token"]
ok("login pede 2ª etapa; código com letras/acentos -> 401 (não 500)", S(c2.post("/api/auth/mfa", json={"mfa_token":mt,"code":"12ç456"})) == 401)
ok("próximo código TOTP entra (200)", S(c2.post("/api/auth/mfa", json={"mfa_token":mt,"code":T.at(time.time()+30)})) == 200)
c3 = A.app.test_client(); mt3 = c3.post("/api/auth/login", json={"email":EM,"password":P}).get_json()["mfa_token"]
ok("código de recuperação funciona 1 vez", S(c3.post("/api/auth/mfa", json={"mfa_token":mt3,"code":codes[0]})) == 200)
c4 = A.app.test_client(); mt4 = c4.post("/api/auth/login", json={"email":EM,"password":P}).get_json()["mfa_token"]
c4.post("/api/auth/mfa-recover", json={"mfa_token":mt4}); rt = mail["m"].split("#recover=")[1]
ok("recuperar 2FA: senha errada 403, certa 200", S(c4.post("/api/auth/mfa-reset", json={"token":rt,"password":"errada-123456"})) == 403 and S(c4.post("/api/auth/mfa-reset", json={"token":rt,"password":P})) == 200)
c5 = A.app.test_client(); ok("depois disso o login entra direto", c5.post("/api/auth/login", json={"email":EM,"password":P}).get_json().get("user") is not None)
c5.post("/api/auth/forgot", json={"email":EM}); ok("reset de senha", S(c5.post("/api/auth/reset", json={"token":mail["r"].split("#reset=")[1],"password":"nova-senha-987"})) == 200)
c6 = A.app.test_client(); codes6 = [S(c6.post("/api/auth/login", json={"email":EM,"password":"errada-x"})) for _ in range(5)] + [S(c6.post("/api/auth/login", json={"email":EM,"password":"nova-senha-987"}))]
ok("5 erros bloqueiam a conta (último 429)", codes6 == [401,401,401,401,401,429])
with A.app.app_context(): u = A.User.query.filter_by(email=EM).first(); u.locked_until = None; db.session.commit()
c7 = A.app.test_client(); c7.post("/api/auth/login", json={"email":EM,"password":"nova-senha-987"})
ok("exportar meus dados e atividade", S(c7.get("/api/me/export")) == 200 and S(c7.get("/api/me/activity")) == 200)
ok("excluir conta: senha errada 403, certa 200", S(c7.delete("/api/me", json={"password":"x"})) == 403 and S(c7.delete("/api/me", json={"password":"nova-senha-987"})) == 200)
bad = [n for n, v in res if not v]
print(f"{len(res)-len(bad)}/{len(res)} verificações OK"); [print("FALHOU:", b) for b in bad]
