"""Teste automático do backend. Rode dentro de backend/:  python tests/fuzz_inputs.py
Não envia e-mails nem chama a IA de verdade (são simulados).
Para testar no Postgres: defina TEST_DATABASE_URL (e AUTO_CREATE_DB=0 depois de rodar `flask db upgrade`)."""
import os, sys, random, json, io, secrets, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cryptography.fernet import Fernet
import tempfile
DB = os.path.join(tempfile.gettempdir(), "aura_fuzz_test.db")  # banco temporário; nunca toca no seu aura.db
os.environ.update(JWT_SECRET="x"+secrets.token_hex(16), DATA_KEY=Fernet.generate_key().decode(), COOKIE_SECURE="0", DATABASE_URL=os.getenv("TEST_DATABASE_URL") or "sqlite:///" + DB.replace(os.sep, "/"), INVITE_CODE="Turma-Aura-2026")
if os.path.exists(DB): os.remove(DB)
import pyotp
import app as A
from models import db
from werkzeug.datastructures import Headers
from flask.testing import FlaskClient

class _OriginClient(A.app.test_client_class or FlaskClient):
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
sent = {}
A.send_verify_email = lambda e,n,l: sent.update(verify=l); A.send_reset_email = lambda e,n,l: sent.update(reset=l)
A.send_mfa_reset_email = lambda e,n,l: sent.update(mfa=l); A.send_exists_email = lambda e,n: None; A.send_security_email = lambda *a: None
random.seed(7)
VALS = ["", None, "\ud800", "\u202e", "\u200b", 0, 1, -1, 1.5, 1e308, float("inf"), True, False, [], {}, [1, 2], {"a": 1}, ["a"], "ç", "João", "💥", "а" "dmin", "a"*5000, "' OR 1=1 --", "<script>alert(1)</script>", "\x00", "a\x00b", "nan", "999999999999999999999999",
        "Turma-Aura-2026", "Turma–Aura–2026", "\ufeffTurma-Aura-2026", "123456", "12345ç", "a@b.co", "ana@x.com", "senha-forte-123", {"d": "x", "v": "nan", "a": "x", "t": 1e12}, [{"d": "=cmd", "c": None, "v": "x", "a": 99, "t": 1}, 5, None, {"role": "user"}]]
KEYS = ["email","password","name","token","code","mfa_token","invite","accept_privacy","current_password","new_password","label","bank","items","profile","reserve_pct","use_ai","messages","file","id"]
def rnd_body():
    r = random.random()
    if r < .08: return random.choice([None, [], "texto", 123, [1,2,3], True])
    return {k: random.choice(VALS) for k in random.sample(KEYS, random.randint(0, 7))}

def mk_user(email, pw="senha-forte-123", totp=False):
    c = A.app.test_client(); sent.clear()
    c.post("/api/auth/register", json={"name": "Ana", "email": email, "accept_privacy": True, "invite": "Turma-Aura-2026"})
    c.post("/api/auth/verify", json={"token": sent["verify"].split("#verify=")[1], "password": pw})
    c.post("/api/auth/login", json={"email": email, "password": pw})
    return c
auth = mk_user("ana@x.com")
inv = auth.post("/api/invoices", json={"label":"T","items":[{"d":"M","c":"A","v":100,"a":1,"t":3}],"profile":{"renda":5000,"fixos":2000,"meta":6,"venc":10}}).get_json()["id"]
sec = auth.post("/api/2fa/setup").get_json()["secret"]; auth.post("/api/2fa/enable", json={"password":"senha-forte-123","code":pyotp.TOTP(sec).now()})
with A.app.app_context(): tu = A.User.query.first()
mfa_tok = A.make_mfa_token(tu) if tu else ""
anon = A.app.test_client()
rules = [r for r in A.app.url_map.iter_rules() if r.rule.startswith("/api/")]
fails = {}; n = 0; codes = {}
def hit(client, rule, method, **kw):
    global n
    # qualquer <int:...> na rota (iid, rid, etc.) recebe um valor de teste; antes só <int:iid> era substituído,
    # então rotas como DELETE /api/reserve/<int:rid> nunca eram de fato exercitadas (404 literal antes da view).
    path = re.sub(r"<int:\w+>", lambda _m: str(random.choice([inv, inv, 99999, 0, -3])), rule.rule)
    n += 1
    try: r = getattr(client, method.lower())(path, **kw)
    except Exception as e:
        fails.setdefault((rule.rule, method, "EXCEÇÃO " + type(e).__name__ + " " + str(e)[:60]), kw); return
    codes[r.status_code] = codes.get(r.status_code, 0) + 1
    if r.status_code >= 500: fails.setdefault((rule.rule, method, r.status_code), str(kw)[:140])
for _ in range(2200):
    rule = random.choice(rules); m = random.choice(sorted(rule.methods - {"HEAD", "OPTIONS"})); cl = random.choice([auth, anon])
    b = rnd_body()
    if isinstance(b, dict) and random.random() < .4:
        if "mfa_token" in b or "mfa" in rule.rule: b["mfa_token"] = mfa_tok
        if "token" in b: b["token"] = random.choice(["lixo", sent.get("reset","#x=y").split("=")[-1], 123])
    if m == "GET": hit(cl, rule, m)
    elif random.random() < .08: hit(cl, rule, m, data=random.choice([b"{quebrado", b"\xff\xfe\x00", b"", b"[[[[[[[[[[[[[[[[[[[[[[[[["]), content_type="application/json")
    elif random.random() < .08: hit(cl, rule, m, data=json.dumps(b if b is not None else {}), content_type="text/plain")
    elif "extract" in rule.rule: hit(cl, rule, m, data={"file": (io.BytesIO(random.choice([b"", b"%PDF-1.4 x", b"\x89PNG\r\n\x1a\nxx", b"\xff\xd8\xffxx", b"RIFFxxxxWEBP", b"lixo"*50])), random.choice(["a.pdf", "ç.png", "../../x", ""]), random.choice(["application/pdf", "text/html", ""]))}, content_type="multipart/form-data")
    else: hit(cl, rule, m, json=b)
# ataques dirigidos: 2ª etapa e links com entradas estranhas
for code in VALS + ["١٢٣٤٥٦", "12 34 56", "ａｂｃ"]:
    for body in ({"mfa_token": mfa_tok, "code": code}, {"password": "senha-forte-123", "code": code}, {"password": code, "code": "123456"}):
        hit(anon, [r for r in rules if r.rule == "/api/auth/mfa"][0], "POST", json=body)
        hit(auth, [r for r in rules if r.rule == "/api/2fa/disable"][0], "POST", json=body)
        hit(auth, [r for r in rules if r.rule == "/api/2fa/enable"][0], "POST", json=body)
print(f"{n} requisições | status:", dict(sorted(codes.items())))
print("ERROS 500 / exceções:", len(fails))
for k, v in list(fails.items())[:14]: print("  ", k, "<-", v)
