import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request

from models import User, db

SECRET = os.getenv("JWT_SECRET")
if not SECRET or len(SECRET) < 32:
    # um segredo curto/fraco permite forjar um cookie de sessão válido por força bruta offline (bypass total de login/2FA).
    raise RuntimeError("Defina JWT_SECRET no ambiente (.env) com pelo menos 32 caracteres (ex.: python -c \"import secrets;print(secrets.token_hex(32))\").")

SECURE = os.getenv("COOKIE_SECURE", "1") == "1"
COOKIE = "__Host-aura_session" if SECURE else "aura_session"  # prefixo __Host-: só HTTPS, sem Domain, Path=/
MAX_AGE = 12 * 3600


def _encode(user, purpose, seconds):
    exp = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    return jwt.encode({"sub": str(user.id), "tv": user.token_version, "pur": purpose, "exp": exp}, SECRET, algorithm="HS256")


def _decode(token, purpose):
    try:
        p = jwt.decode(token or "", SECRET, algorithms=["HS256"])
        user = db.session.get(User, int(p["sub"]))
        if user and p.get("pur") == purpose and user.token_version == p.get("tv"):
            return user
    except Exception:
        pass
    return None


def make_mfa_token(user):  # vale 5 min e NÃO abre sessão: só permite informar o código de 2 etapas
    return _encode(user, "mfa", 300)


def read_mfa_token(token):
    return _decode(token, "mfa")


def set_session(resp, user):
    # HttpOnly: o JavaScript da página não lê. SameSite=Lax: não vai em requisições de outros sites.
    resp.set_cookie(COOKIE, _encode(user, "session", MAX_AGE), max_age=MAX_AGE, httponly=True, secure=SECURE, samesite="Lax", path="/")


def clear_session(resp):
    resp.delete_cookie(COOKIE, path="/")


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        g.user = _decode(request.cookies.get(COOKIE), "session")
        if not g.user:
            return jsonify(error="Sessão expirada. Entre novamente."), 401
        return fn(*a, **kw)
    return wrapper
