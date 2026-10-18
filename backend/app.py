import hashlib
import hmac
import os
import re
import secrets
import time
import unicodedata
from datetime import timedelta, timezone
from functools import wraps

from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

import click  # noqa: E402
import pyotp  # noqa: E402
from flask import Flask, g, jsonify, request, send_file, send_from_directory  # noqa: E402
from flask_limiter import Limiter  # noqa: E402
from flask_migrate import Migrate  # noqa: E402
from flask_limiter.util import get_remote_address  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: E402

from auth import SECURE, clear_session, login_required, make_mfa_token, read_mfa_token, set_session  # noqa: E402
from models import AuditLog, Invoice, ReserveEntry, UsageLog, User, UserToken, db, now  # noqa: E402
from services.ai import AIUnavailable, build_plan, extract_invoice, mentor_chat  # noqa: E402
from services.calculator import analyze, clean_items, clean_profile, rule_plan  # noqa: E402
from services.excel_export import build_workbook  # noqa: E402
from services.mailer import send_exists_email, send_mfa_reset_email, send_reset_email, send_security_email, send_verify_email  # noqa: E402

POLICY_VERSION = "1.5"  # Termos de Uso + Política: mantenha igual a frontend/src/Privacy.jsx
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
APP_URL = os.getenv("APP_URL", "http://localhost:5173").rstrip("/")
AI_EXTRACT_DAILY = int(os.getenv("AI_EXTRACT_DAILY", "10"))   # leituras de fatura por usuário a cada 24 h
AI_PLAN_DAILY = int(os.getenv("AI_PLAN_DAILY", "20"))         # planos com IA por usuário a cada 24 h
AI_CHAT_DAILY = int(os.getenv("AI_CHAT_DAILY", "30"))         # mensagens do chat com a Aura por usuário a cada 24 h
AI_GLOBAL_MONTHLY = int(os.getenv("AI_GLOBAL_MONTHLY_LIMIT", "1000"))  # teto de usos da IA no app inteiro em 30 dias (controle de custo)
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}  # e-mail(s) da mentora: só vê números agregados, nunca dados financeiros de um mentorado


def _norm(s):
    """Normaliza o texto de comparação: remove espaço invisível/BOM e unifica variações de caracteres."""
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if ch not in "\u200b\u200c\u200d\u2060\ufeff").strip()


_raw_invite = os.getenv("INVITE_CODE", "")
INVITE_CODE = _norm(_raw_invite)  # se definido, o cadastro exige este código
if _raw_invite and any(ord(ch) > 127 for ch in _raw_invite):
    print("[aviso] INVITE_CODE tem caracteres fora do ASCII (acento, travessão ou espaço invisível). Use só letras, números e hífen comum.")

DUMMY_HASH = generate_password_hash("aura-dummy-password")    # iguala o tempo de resposta quando o e-mail não existe
COMMON = {"1234567890", "0123456789", "senha12345", "senha123456", "password123", "qwerty12345", "1234567891", "abcdefghij", "brasil12345"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")

def _db_url():
    """O Render entrega postgres:// ; o driver do projeto é o psycopg2, e o SQLAlchemy novo assume outro por padrão."""
    url = os.getenv("DATABASE_URL", "sqlite:///aura.db")
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


app = Flask(__name__)
# TRUSTED_PROXIES = quantos proxies ficam na frente do app (Render = 1; Cloudflare + Render = 2).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=int(os.getenv("TRUSTED_PROXIES", "1")), x_proto=1, x_host=1)
app.config.update(
    SQLALCHEMY_DATABASE_URI=_db_url(),
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
)
db.init_app(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["300/hour"],
                  storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"))


def _render_item(type_, obj, autogen_context):
    """Nas migrações, a coluna criptografada é só texto (a criptografia acontece no app)."""
    if type_ == "type" and obj.__class__.__name__ == "EncryptedJSON":
        return "sa.Text()"
    return False


migrate = Migrate(app, db, render_item=_render_item)
if os.getenv("AUTO_CREATE_DB", "1") == "1":  # desenvolvimento local; em produção o banco é criado por `flask db upgrade`
    with app.app_context():
        db.create_all()


# ---------- utilidades ----------
class Body(dict):
    """Corpo JSON da requisição. s() devolve sempre um texto seguro (str, sem NUL nem caracteres inválidos, com tamanho limitado)."""

    def s(self, key, n=500):
        v = self.get(key)
        return v.encode("utf-8", "ignore").decode("utf-8").replace("\x00", "")[:n] if isinstance(v, str) else ""


def body():
    d = request.get_json(silent=True)
    return Body(d if isinstance(d, dict) else {})  # corpo que não é objeto JSON (lista, número, texto) vira {}



def _aware(d):
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def _hash(raw):
    return hashlib.sha256((raw if isinstance(raw, str) else "").encode("utf-8", "ignore")).hexdigest()


def _pct(v, default=60.0):
    try:
        x = float(v)
        return min(100.0, max(0.0, x)) if x == x else default
    except (TypeError, ValueError):
        return default


def _user(u):
    return {"id": u.id, "name": u.name, "email": u.email, "totp": bool(u.totp_enabled), "admin": u.email in ADMIN_EMAILS}


def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if g.user.email not in ADMIN_EMAILS:
            return jsonify(error="Acesso restrito à mentora."), 403
        return fn(*a, **kw)
    return wrapper


def audit(event, user_id=None):
    db.session.add(AuditLog(user_id=user_id, event=event, ip=(request.remote_addr or "")[:45], ua=request.headers.get("User-Agent", "")[:200]))
    db.session.commit()


def weak_password(pw, email=""):
    if len(pw) < 10:
        return "A senha precisa ter pelo menos 10 caracteres."
    if len(pw) > 128:
        return "A senha pode ter no máximo 128 caracteres."
    if pw.lower() in COMMON or len(set(pw.lower())) < 4:
        return "Escolha uma senha menos previsível."
    local = email.split("@")[0].lower()
    if len(local) >= 4 and local in pw.lower():
        return "A senha não pode conter o seu e-mail."
    return None


def session_response(u, status=200):
    resp = jsonify(user=_user(u))
    resp.status_code = status
    set_session(resp, u)
    return resp


def issue_token(u, kind, minutes):
    UserToken.query.filter_by(user_id=u.id, kind=kind, used_at=None).update({"used_at": now()})  # invalida os anteriores
    raw = secrets.token_urlsafe(32)
    db.session.add(UserToken(user_id=u.id, kind=kind, token_hash=_hash(raw), expires_at=now() + timedelta(minutes=minutes)))
    db.session.commit()
    return raw


def find_token(raw, kind):
    t = UserToken.query.filter_by(token_hash=_hash(raw), kind=kind).first()
    return t if t and not t.used_at and _aware(t.expires_at) > now() else None


def recent_token(u, kind):
    return UserToken.query.filter(UserToken.user_id == u.id, UserToken.kind == kind, UserToken.created_at > now() - timedelta(minutes=2)).first() is not None


def is_locked(u):
    return bool(u and _aware(u.locked_until) and _aware(u.locked_until) > now())


def register_failure(u, event):
    """5 erros seguidos (senha ou código 2FA) = conta bloqueada por 15 min.
    O incremento é um UPDATE atômico no banco (não ler-somar-gravar em Python): sob requisições
    concorrentes para o mesmo usuário, nenhuma tentativa é perdida (evita burlar o limite por corrida)."""
    if not u:
        return audit(event)
    db.session.execute(db.update(User).where(User.id == u.id).values(failed_logins=User.failed_logins + 1))
    db.session.commit()
    db.session.refresh(u)
    locked = u.failed_logins >= 5
    if locked:
        db.session.execute(db.update(User).where(User.id == u.id).values(locked_until=now() + timedelta(minutes=15), failed_logins=0))
        db.session.commit()
        db.session.refresh(u)
    audit("lockout" if locked else event, u.id)


def finish_login(u, event="login_ok"):
    u.failed_logins, u.locked_until = 0, None
    db.session.commit()
    audit(event, u.id)
    return session_response(u)


def quota_error(kind, limit):
    """Devolve a mensagem de erro se algum limite de IA foi atingido; senão registra o uso e devolve None.
    Trava a linha do usuário (FOR UPDATE) até o commit: duas chamadas concorrentes do mesmo usuário
    ficam em fila em vez de ambas lerem a contagem antiga e passarem do limite diário."""
    db.session.execute(db.select(User.id).where(User.id == g.user.id).with_for_update())
    if UsageLog.query.filter(UsageLog.created_at > now() - timedelta(days=30)).count() >= AI_GLOBAL_MONTHLY:
        return "O limite de uso da IA deste mês foi atingido. Digite os lançamentos manualmente; o plano padrão continua disponível."
    n = UsageLog.query.filter(UsageLog.user_id == g.user.id, UsageLog.kind == kind, UsageLog.created_at > now() - timedelta(hours=24)).count()
    if n >= limit:
        return "Você atingiu o limite diário de uso da IA. Tente amanhã; o plano padrão e a digitação manual continuam disponíveis."
    db.session.add(UsageLog(user_id=g.user.id, kind=kind))
    db.session.commit()
    return None


def sniff_mime(data):
    """Descobre o tipo pelo conteúdo (o tipo informado pelo navegador pode ser falso)."""
    if data[:5] == b"%PDF-":
        return "application/pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def verify_totp(u, code):
    totp, step_now = pyotp.TOTP(u.totp_secret), int(time.time()) // 30
    for step in (step_now - 1, step_now, step_now + 1):
        if step > (u.totp_last_step or 0) and hmac.compare_digest(totp.at(step * 30).encode(), code.encode("utf-8", "ignore")):
            u.totp_last_step = step  # cada código só vale uma vez
            return True
    return False


def use_recovery_code(u, code):
    h, codes = _hash(code.lower().replace("-", "")), list(u.recovery_codes or [])
    if h in codes:
        codes.remove(h)
        u.recovery_codes = codes
        return True
    return False


# ---------- cabeçalhos e CSRF ----------
@app.before_request
def csrf_guard():
    """Além do SameSite=Lax: recusa requisições que alteram dados vindas de outra origem.
    Exige o header Origin (todo navegador moderno o envia em fetch/XHR com método não-GET,
    inclusive no mesmo site); sem ele, a requisição não veio de um navegador normal e é recusada."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/api/"):
        origin = request.headers.get("Origin")
        allowed = {request.host_url.rstrip("/"), *filter(None, os.getenv("ALLOWED_ORIGINS", "").split(","))}
        if os.getenv("FLASK_DEBUG") == "1":  # só em desenvolvimento: aceita o servidor do Vite
            allowed |= {"http://localhost:5173", "http://127.0.0.1:5173"}
        if origin not in allowed:
            return jsonify(error="Origem não permitida."), 403


@app.after_request
def security_headers(resp):
    resp.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                         "Permissions-Policy": "camera=(), microphone=(), geolocation=()", "Content-Security-Policy": CSP})
    if SECURE:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    elif request.path.startswith("/assets/"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


# ---------- cadastro, e-mail e senha ----------
@app.get("/api/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))  # confirma que o banco responde (o Render reinicia o serviço se falhar)
    except Exception:
        return {"ok": False}, 503
    return {"ok": True}


@app.get("/api/config")
def public_config():
    return {"invite_required": bool(INVITE_CODE)}


GENERIC_REGISTER = "Se o e-mail for válido, enviamos um link para ativar a conta e criar sua senha. Ele vale por 24 horas."


@app.post("/api/auth/register")
@limiter.limit("5/minute")
def register():
    """A senha só é criada pelo link do e-mail: ninguém consegue 'pré-registrar' o e-mail de outra pessoa."""
    d = body()
    email, name = d.s("email", 254).strip().lower(), d.s("name", 80).strip()
    if not name or not EMAIL.match(email) or len(email) > 254:
        return jsonify(error="Informe nome e e-mail válidos."), 400
    if d.get("accept_privacy") is not True:
        return jsonify(error="Aceite a Política de Privacidade para criar a conta."), 400
    if INVITE_CODE and not hmac.compare_digest(_norm(d.s("invite", 100)).encode(), INVITE_CODE.encode()):
        return jsonify(error="Código de convite inválido. Peça o código à sua mentora."), 400
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, name=name, password_hash=generate_password_hash(secrets.token_urlsafe(32)),
                 consent_at=now(), consent_version=POLICY_VERSION, email_verified=False)
        try:
            db.session.add(u)
            db.session.commit()
        except IntegrityError:  # outro pedido criou o mesmo e-mail um instante antes
            db.session.rollback()
            u = User.query.filter_by(email=email).first()
    if not u.email_verified:
        if not recent_token(u, "verify"):
            send_verify_email(u.email, u.name, f"{APP_URL}/#verify={issue_token(u, 'verify', 24 * 60)}")
    else:
        send_exists_email(u.email, u.name)
    audit("register", u.id)
    return jsonify(ok=True, message=GENERIC_REGISTER), 202


@app.post("/api/auth/resend")
@limiter.limit("5/hour")
def resend_verification():
    u = User.query.filter_by(email=body().s("email", 254).strip().lower()).first()
    if u and not u.email_verified and not recent_token(u, "verify"):
        send_verify_email(u.email, u.name, f"{APP_URL}/#verify={issue_token(u, 'verify', 24 * 60)}")
    return jsonify(ok=True, message=GENERIC_REGISTER)


def _set_password(kind, event):
    d = body()
    t = find_token(d.s("token", 200), kind)
    if not t:
        return jsonify(error="Link inválido ou expirado. Peça um novo."), 400
    u = db.session.get(User, t.user_id)
    if err := weak_password(d.s("password", 300), u.email):
        return jsonify(error=err), 400  # o link continua válido para nova tentativa
    u.password_hash = generate_password_hash(d.s("password", 300))
    u.email_verified = True  # abrir o link prova que a pessoa controla o e-mail
    u.token_version += 1     # derruba qualquer sessão aberta
    u.failed_logins, u.locked_until = 0, None
    UserToken.query.filter_by(user_id=u.id, used_at=None).update({"used_at": now()})
    db.session.commit()
    audit(event, u.id)
    if kind == "reset":
        send_security_email(u.email, u.name, "Sua senha foi alterada", "A senha da sua conta foi redefinida e todos os dispositivos foram desconectados.")
    return jsonify(ok=True)


@app.post("/api/auth/verify")
@limiter.limit("10/hour")
def verify_email():
    return _set_password("verify", "verify")


@app.post("/api/auth/forgot")
@limiter.limit("5/hour")
def forgot():
    email = body().s("email", 254).strip().lower()
    u = User.query.filter_by(email=email).first() if EMAIL.match(email) else None
    if u and not recent_token(u, "reset"):
        send_reset_email(u.email, u.name, f"{APP_URL}/#reset={issue_token(u, 'reset', 30)}")  # fragmento (#): fora de logs e do Referer
    return jsonify(ok=True, message="Se esse e-mail tiver cadastro, enviamos um link para criar uma nova senha. Ele vale por 30 minutos.")


@app.post("/api/auth/reset")
@limiter.limit("10/hour")
def reset_password():
    return _set_password("reset", "password_reset")  # a verificação em 2 etapas continua exigida no login


@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login():
    d = body()
    u = User.query.filter_by(email=d.s("email", 254).strip().lower()).first()
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos ou redefina sua senha."), 429
    ok = check_password_hash(u.password_hash if u else DUMMY_HASH, d.s("password", 300))  # sempre roda: tempo igual com ou sem conta
    if not (u and ok):
        register_failure(u, "login_fail")
        return jsonify(error="E-mail ou senha incorretos."), 401
    if not u.email_verified:
        return jsonify(error="Confirme seu e-mail antes de entrar. Procure o link na sua caixa de entrada."), 403
    if u.totp_enabled:
        return jsonify(mfa_required=True, mfa_token=make_mfa_token(u))
    return finish_login(u)


@app.post("/api/auth/mfa")
@limiter.limit("10/minute")
def login_mfa():
    d = body()
    u = read_mfa_token(d.s("mfa_token", 1000))
    if not u or not u.totp_enabled:
        return jsonify(error="A verificação expirou. Entre novamente."), 401
    # trava a linha até o commit: duas requisições simultâneas com o MESMO código (TOTP ou recuperação)
    # não conseguem mais autenticar as duas, porque a segunda só lê o estado depois que a primeira já commitou "usado".
    u = db.session.execute(db.select(User).where(User.id == u.id).with_for_update()).scalar_one()
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    code = d.s("code", 64).strip().replace(" ", "")
    if not (verify_totp(u, code) or use_recovery_code(u, code)):
        register_failure(u, "mfa_fail")
        return jsonify(error="Código incorreto."), 401
    return finish_login(u, "mfa_ok")


@app.post("/api/auth/mfa-recover")
@limiter.limit("3/hour")
def mfa_recover():
    """Perdeu o celular e os códigos: só quem acertou a senha chega aqui; o link vai ao e-mail cadastrado."""
    u = read_mfa_token(body().s("mfa_token", 1000))
    if u and u.totp_enabled and not recent_token(u, "mfa_reset"):
        send_mfa_reset_email(u.email, u.name, f"{APP_URL}/#recover={issue_token(u, 'mfa_reset', 30)}")
        audit("mfa_recover_request", u.id)
    return jsonify(ok=True, message="Enviamos um link para o seu e-mail. Ele vale por 30 minutos e vai pedir a sua senha para confirmar.")


@app.post("/api/auth/mfa-reset")
@limiter.limit("5/hour")
def mfa_reset():
    d = body()
    t = find_token(d.s("token", 200), "mfa_reset")
    if not t:
        return jsonify(error="Link inválido ou expirado. Peça um novo."), 400
    u = db.session.get(User, t.user_id)
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    if not check_password_hash(u.password_hash, d.s("password", 300)):  # e-mail + senha: os dois fatores combinados no MVP
        register_failure(u, "login_fail")
        return jsonify(error="Senha incorreta."), 403
    u.totp_enabled, u.totp_secret, u.recovery_codes, u.totp_last_step = False, None, None, 0
    u.token_version += 1
    UserToken.query.filter_by(user_id=u.id, used_at=None).update({"used_at": now()})
    db.session.commit()
    audit("2fa_reset_email", u.id)
    send_security_email(u.email, u.name, "Verificação em duas etapas desativada", "A verificação em duas etapas foi desativada pelo link enviado ao seu e-mail. Reative em Minha conta.")
    return jsonify(ok=True)


@app.post("/api/auth/logout")
def logout():
    resp = jsonify(ok=True)
    clear_session(resp)
    return resp


@app.post("/api/auth/logout-all")
@login_required
def logout_all():
    g.user.token_version += 1
    db.session.commit()
    audit("logout_all", g.user.id)
    resp = jsonify(ok=True)
    clear_session(resp)
    return resp


@app.post("/api/auth/change-password")
@login_required
@limiter.limit("10/hour")
def change_password():
    d, u = body(), g.user
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    if not check_password_hash(u.password_hash, d.s("current_password", 300)):
        register_failure(u, "login_fail")
        return jsonify(error="A senha atual está incorreta."), 403
    if err := weak_password(d.s("new_password", 300), u.email):
        return jsonify(error=err), 400
    u.password_hash = generate_password_hash(d.s("new_password", 300))
    u.token_version += 1
    db.session.commit()
    audit("password_change", u.id)
    send_security_email(u.email, u.name, "Sua senha foi alterada", "A senha da sua conta acabou de ser alterada e os outros dispositivos foram desconectados.")
    return session_response(u)  # mantém só esta sessão


# ---------- verificação em duas etapas (TOTP) ----------
@app.post("/api/2fa/setup")
@login_required
@limiter.limit("10/hour")
def twofa_setup():
    if g.user.totp_enabled:
        return jsonify(error="A verificação em duas etapas já está ativa."), 409
    g.user.totp_secret = pyotp.random_base32()
    db.session.commit()
    return jsonify(secret=g.user.totp_secret, uri=pyotp.TOTP(g.user.totp_secret).provisioning_uri(name=g.user.email, issuer_name="Aura"))


@app.post("/api/2fa/enable")
@login_required
@limiter.limit("10/hour")
def twofa_enable():
    d, u = body(), g.user
    if u.totp_enabled or not u.totp_secret:
        return jsonify(error="Inicie a configuração primeiro."), 400
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    if not check_password_hash(u.password_hash, d.s("password", 300)):
        register_failure(u, "login_fail")
        return jsonify(error="Senha incorreta."), 403
    if not verify_totp(u, d.s("code", 64).strip().replace(" ", "")):
        return jsonify(error="Código incorreto. Confira o horário do celular e tente de novo."), 400
    codes = [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(8)]
    u.totp_enabled, u.recovery_codes = True, [_hash(c.replace("-", "")) for c in codes]
    db.session.commit()
    audit("2fa_enable", u.id)
    send_security_email(u.email, u.name, "Verificação em duas etapas ativada", "A verificação em duas etapas foi ativada na sua conta.")
    return jsonify(recovery_codes=codes)  # mostrados uma única vez


@app.post("/api/2fa/disable")
@login_required
@limiter.limit("10/hour")
def twofa_disable():
    d, u = body(), g.user
    if is_locked(u):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    code = d.s("code", 64).strip().replace(" ", "")
    if not check_password_hash(u.password_hash, d.s("password", 300)):
        register_failure(u, "login_fail")
        return jsonify(error="Senha ou código incorretos."), 403
    if not (verify_totp(u, code) or use_recovery_code(u, code)):
        return jsonify(error="Senha ou código incorretos."), 403
    u.totp_enabled, u.totp_secret, u.recovery_codes, u.totp_last_step = False, None, None, 0
    db.session.commit()
    audit("2fa_disable", u.id)
    send_security_email(u.email, u.name, "Verificação em duas etapas desativada", "A verificação em duas etapas foi desativada na sua conta.")
    return jsonify(ok=True)


# ---------- minha conta (LGPD) ----------
@app.get("/api/me")
@login_required
def me():
    return jsonify(user=_user(g.user))


@app.get("/api/me/activity")
@login_required
def activity():
    rows = AuditLog.query.filter_by(user_id=g.user.id).order_by(AuditLog.id.desc()).limit(15).all()
    return jsonify(events=[{"event": r.event, "ip": r.ip, "at": r.created_at.isoformat()} for r in rows])


@app.get("/api/me/export")  # acesso e portabilidade
@login_required
def me_export():
    u = g.user
    return jsonify(user={**_user(u), "created_at": u.created_at.isoformat(), "consent_at": u.consent_at.isoformat(),
                         "consent_version": u.consent_version}, invoices=[full(i) for i in u.invoices])


@app.delete("/api/me")  # eliminação: exige a senha
@login_required
@limiter.limit("10/hour")
def me_delete():
    if is_locked(g.user):
        return jsonify(error="Muitas tentativas incorretas. Tente de novo em 15 minutos."), 429
    if not check_password_hash(g.user.password_hash, body().s("password", 300)):
        register_failure(g.user, "login_fail")
        return jsonify(error="Senha incorreta. A conta não foi excluída."), 403
    audit("account_delete", g.user.id)
    UsageLog.query.filter_by(user_id=g.user.id).delete()  # sem FK/cascade: exclusão imediata (LGPD), não espera a limpeza periódica
    db.session.delete(g.user)
    db.session.commit()
    resp = jsonify(ok=True)
    clear_session(resp)
    return resp


# ---------- faturas ----------
def full(inv):
    an = analyze(inv.items, inv.profile, inv.reserve_pct)
    return {"id": inv.id, "label": inv.label, "bank": inv.bank, "created_at": inv.created_at.isoformat(),
            "profile": inv.profile, "items": inv.items, "reserve_pct": inv.reserve_pct, "analysis": an,
            "plan": inv.plan or rule_plan(an, inv.profile, inv.reserve_pct), "ai": bool(inv.plan and inv.plan_ai)}


def summary(inv):
    an = analyze(inv.items, inv.profile, inv.reserve_pct)
    return {"id": inv.id, "label": inv.label, "bank": inv.bank, "created_at": inv.created_at.isoformat(),
            "total": an["total"], "parcelado": an["parcelado"], "a_vista": an["a_vista"],
            "pct": an["pct_comprometido"], "restante": an["restante_parcelas"]}


def own(iid):
    inv = db.session.get(Invoice, iid)
    return inv if inv and inv.user_id == g.user.id else None  # nunca revela faturas de outros usuários


def not_found():
    return jsonify(error="Fatura não encontrada."), 404


def _fields(d):
    label = d.s("label", 80).strip() or f"Fatura de {now():%d/%m/%Y}"
    return {"label": label, "bank": d.s("bank", 60).strip(), "items": clean_items(d.get("items")),
            "profile": clean_profile(d.get("profile")), "reserve_pct": _pct(d.get("reserve_pct"))}


@app.post("/api/invoices/extract")
@login_required
@limiter.limit("20/hour")
def extract():
    f = request.files.get("file")
    data = f.read() if f else b""
    mime = sniff_mime(data)
    if not mime:
        return jsonify(error="Envie um PDF, PNG, JPG ou WEBP."), 400
    if mime != "application/pdf" and len(data) > 5 * 1024 * 1024:
        return jsonify(error="A imagem passa de 5 MB. Envie o PDF ou uma foto menor."), 400
    if msg := quota_error("extract", AI_EXTRACT_DAILY):
        return jsonify(error=msg), 429
    try:
        return jsonify(extract_invoice(data, mime))  # o arquivo não é salvo
    except AIUnavailable:
        return jsonify(error="Leitura por IA indisponível no momento. Digite os lançamentos manualmente."), 503
    except Exception:
        return jsonify(error="Não consegui ler esta fatura. Tente outro arquivo ou digite os lançamentos."), 422


@app.get("/api/invoices")
@login_required
def list_invoices():
    rows = Invoice.query.filter_by(user_id=g.user.id).order_by(Invoice.created_at.asc()).all()
    return jsonify(invoices=[summary(i) for i in rows])


@app.post("/api/invoices")
@login_required
def create_invoice():
    inv = Invoice(user_id=g.user.id, **_fields(body()))
    db.session.add(inv)
    db.session.commit()
    return jsonify(full(inv)), 201


@app.get("/api/invoices/<int:iid>")
@login_required
def get_invoice(iid):
    inv = own(iid)
    return jsonify(full(inv)) if inv else not_found()


@app.put("/api/invoices/<int:iid>")
@login_required
def update_invoice(iid):
    inv = own(iid)
    if not inv:
        return not_found()
    d = body()
    # só sobrescreve o que veio no corpo: um PUT parcial (ex.: só o "label") não pode apagar os
    # lançamentos/perfil existentes, que é o que _fields() faria (ele sempre devolve as 5 chaves).
    if "label" in d or "bank" in d:
        inv.label = d.s("label", 80).strip() or inv.label if "label" in d else inv.label
        inv.bank = d.s("bank", 60).strip() if "bank" in d else inv.bank
    if "items" in d:
        inv.items = clean_items(d.get("items"))
    if "profile" in d:
        inv.profile = clean_profile(d.get("profile"))
    if "reserve_pct" in d:
        inv.reserve_pct = _pct(d.get("reserve_pct"), inv.reserve_pct)
    inv.plan, inv.plan_ai = None, False  # números mudaram: o plano anterior ficou desatualizado
    db.session.commit()
    return jsonify(full(inv))


@app.delete("/api/invoices/<int:iid>")
@login_required
def delete_invoice(iid):
    inv = own(iid)
    if not inv:
        return not_found()
    db.session.delete(inv)
    db.session.commit()
    return "", 204


@app.post("/api/invoices/<int:iid>/plan")
@login_required
def make_plan(iid):
    inv = own(iid)
    if not inv:
        return not_found()
    d = body()
    use_ai = d.get("use_ai") is True
    if use_ai and (msg := quota_error("plan", AI_PLAN_DAILY)):
        return jsonify(error=msg), 429
    inv.reserve_pct = _pct(d.get("reserve_pct"), inv.reserve_pct)
    an = analyze(inv.items, inv.profile, inv.reserve_pct)
    plan, used_ai = build_plan(an, inv.profile, inv.reserve_pct, use_ai)
    inv.plan, inv.plan_ai = (plan if used_ai else None), used_ai
    db.session.commit()
    return jsonify(full(inv))


def _chat_messages(raw):
    """Aceita só user/assistant, limita tamanho e garante alternância começando e terminando em 'user'."""
    out = []
    for m in (raw if isinstance(raw, list) else [])[-12:]:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            continue
        text = Body(m).s("content", 1000).strip()
        if not text:
            continue
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n" + text
        elif out or m["role"] == "user":
            out.append({"role": m["role"], "content": text})
    return out if out and out[-1]["role"] == "user" else []


@app.post("/api/invoices/<int:iid>/chat")
@login_required
@limiter.limit("30/hour")
def chat(iid):
    """Converse com a Aura sobre a fatura. O histórico vem do navegador e NÃO é guardado no servidor."""
    inv = own(iid)
    if not inv:
        return not_found()
    msgs = _chat_messages(body().get("messages"))
    if not msgs:
        return jsonify(error="Escreva uma mensagem."), 400
    if msg := quota_error("chat", AI_CHAT_DAILY):
        return jsonify(error=msg), 429
    try:
        return jsonify(reply=mentor_chat(analyze(inv.items, inv.profile, inv.reserve_pct), inv.profile, msgs))
    except AIUnavailable:
        return jsonify(error="A conversa com a Aura está indisponível no momento."), 503
    except Exception:
        return jsonify(error="Não consegui responder agora. Tente de novo em instantes."), 502


@app.get("/api/invoices/<int:iid>/export")
@login_required
def export(iid):
    inv = own(iid)
    if not inv:
        return not_found()
    hist = [summary(i) for i in Invoice.query.filter_by(user_id=g.user.id).order_by(Invoice.created_at.asc()).all()]
    return send_file(build_workbook(full(inv), hist), as_attachment=True, download_name="aura-plano-financeiro.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ---------- reserva real (quanto o mentorado já guardou, não só a projeção) ----------
def _money(v, maxv=1e9):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x or x <= 0 or x > maxv else round(x, 2)  # recusa NaN, zero/negativo e valores absurdos


def reserve_summary():
    rows = ReserveEntry.query.filter_by(user_id=g.user.id).order_by(ReserveEntry.created_at.asc()).all()
    total = round(sum(r.data["valor"] for r in rows), 2)
    last_inv = Invoice.query.filter_by(user_id=g.user.id).order_by(Invoice.created_at.desc()).first()
    meta = None
    if last_inv:
        an = analyze(last_inv.items, last_inv.profile, last_inv.reserve_pct)
        meta = {"valor": an["meta_reserva"], "mes_meta": an["mes_meta"]}
    return {"entries": [{"id": r.id, "valor": r.data["valor"], "nota": r.data.get("nota", ""),
                         "created_at": r.created_at.isoformat()} for r in rows], "total": total, "meta": meta}


@app.get("/api/reserve")
@login_required
def list_reserve():
    return jsonify(reserve_summary())


@app.post("/api/reserve")
@login_required
@limiter.limit("30/hour")
def add_reserve():
    d = body()
    valor = _money(d.get("valor"))
    if valor is None:
        return jsonify(error="Informe um valor guardado válido, maior que zero."), 400
    if ReserveEntry.query.filter_by(user_id=g.user.id).count() >= 500:
        return jsonify(error="Limite de registros de reserva atingido. Apague algum antigo para continuar."), 400
    db.session.add(ReserveEntry(user_id=g.user.id, data={"valor": valor, "nota": d.s("nota", 120).strip()}))
    db.session.commit()
    audit("reserve_add", g.user.id)
    return jsonify(reserve_summary()), 201


@app.delete("/api/reserve/<int:rid>")
@login_required
def delete_reserve(rid):
    r = ReserveEntry.query.filter_by(id=rid, user_id=g.user.id).first()
    if not r:
        return jsonify(error="Registro não encontrado."), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify(reserve_summary())


# ---------- painel de uso (mentora): só números agregados, nunca dados financeiros de um mentorado ----------
@app.get("/api/admin/usage")
@login_required
@admin_required
def admin_usage():
    since_30d, since_7d, since_24h = now() - timedelta(days=30), now() - timedelta(days=7), now() - timedelta(hours=24)
    active_ids = {uid for (uid,) in db.session.query(AuditLog.user_id).filter(
        AuditLog.event.in_(("login_ok", "mfa_ok")), AuditLog.created_at > since_30d, AuditLog.user_id.isnot(None)).distinct()}
    ai_hoje = {k: UsageLog.query.filter(UsageLog.kind == k, UsageLog.created_at > since_24h).count() for k in ("extract", "plan", "chat")}
    return jsonify(
        usuarios={"total": User.query.count(), "verificados": User.query.filter_by(email_verified=True).count(),
                  "ativos_30d": len(active_ids), "novos_7d": User.query.filter(User.created_at > since_7d).count()},
        faturas={"total": Invoice.query.count()},
        ia={"hoje": ai_hoje, "ultimos_30d": UsageLog.query.filter(UsageLog.created_at > since_30d).count(),
            "limite_mensal": AI_GLOBAL_MONTHLY, "limites_diarios": {"extract": AI_EXTRACT_DAILY, "plan": AI_PLAN_DAILY, "chat": AI_CHAT_DAILY}},
    )


# ---------- front-end e erros ----------
STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
@limiter.exempt
def spa(path):
    if path.startswith("api/"):
        return jsonify(error="Rota não encontrada."), 404
    if path and os.path.isfile(os.path.join(STATIC, path)):
        return send_from_directory(STATIC, path)
    if os.path.isfile(os.path.join(STATIC, "index.html")):
        return send_from_directory(STATIC, "index.html")
    return jsonify(error="Front-end não compilado. Em desenvolvimento, use o Vite (npm run dev)."), 404


@app.errorhandler(HTTPException)
def http_error(e):
    msg = "Arquivo maior que 10 MB." if e.code == 413 else "Muitas tentativas. Aguarde um pouco." if e.code == 429 else e.description
    return jsonify(error=msg), e.code


@app.errorhandler(Exception)
def crash(e):
    app.logger.exception("erro não tratado")  # detalhes só no log do servidor, nunca na resposta
    db.session.rollback()
    return jsonify(error="Erro interno. Tente novamente em instantes."), 500


# ---------- manutenção (rodar por cron e pelo suporte) ----------
@app.cli.command("purge")
def purge():
    """Apaga registros de acesso com mais de 6 meses, links expirados e contas nunca ativadas (7 dias)."""
    AuditLog.query.filter(AuditLog.created_at < now() - timedelta(days=183)).delete()
    UsageLog.query.filter(UsageLog.created_at < now() - timedelta(days=35)).delete()
    UserToken.query.filter(UserToken.expires_at < now() - timedelta(days=1)).delete()
    for u in User.query.filter(User.email_verified.is_(False), User.created_at < now() - timedelta(days=7)).all():
        db.session.delete(u)
    db.session.commit()
    print("purge concluído")


@app.cli.command("disable-2fa")
@click.argument("email")
def disable_2fa_cli(email):
    """Suporte: desativa o 2FA de um usuário DEPOIS de confirmar a identidade dele por outro canal.
    Uso: flask --app app disable-2fa email@exemplo.com"""
    email = email.strip().lower()
    u = User.query.filter_by(email=email).first()
    if not u:
        print("usuário não encontrado")
        return
    u.totp_enabled, u.totp_secret, u.recovery_codes, u.totp_last_step = False, None, None, 0
    u.token_version += 1
    db.session.add(AuditLog(user_id=u.id, event="2fa_reset_support", ip="cli"))
    db.session.commit()
    print(f"2FA desativado para {email}; todas as sessões foram encerradas")


if __name__ == "__main__":
    app.run(port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
