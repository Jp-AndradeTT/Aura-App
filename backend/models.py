import json
import os
from datetime import datetime, timezone

from cryptography.fernet import Fernet, MultiFernet
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator

db = SQLAlchemy()


def now():
    return datetime.now(timezone.utc)


_fernet = None


def get_fernet():
    """DATA_KEY aceita várias chaves separadas por vírgula (a primeira cifra; todas decifram = rotação)."""
    global _fernet
    if _fernet is None:
        keys = [k.strip() for k in os.getenv("DATA_KEY", "").split(",") if k.strip()]
        if not keys:
            raise RuntimeError("Defina DATA_KEY (chave Fernet) no ambiente.")
        _fernet = MultiFernet([Fernet(k) for k in keys])
    return _fernet


class EncryptedJSON(TypeDecorator):
    """JSON criptografado em repouso: no banco só existe texto cifrado."""
    impl = db.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return get_fernet().encrypt(json.dumps(value, ensure_ascii=False).encode()).decode()

    def process_result_value(self, value, dialect):
        return None if value is None else json.loads(get_fernet().decrypt(value.encode()))


get_fernet()  # falha logo na inicialização se a chave estiver ausente ou inválida


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    consent_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consent_version = db.Column(db.String(20), nullable=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    totp_secret = db.Column(EncryptedJSON)               # 2FA: segredo criptografado
    totp_enabled = db.Column(db.Boolean, nullable=False, default=False)
    totp_last_step = db.Column(db.Integer, nullable=False, default=0)   # impede reutilizar o mesmo código
    recovery_codes = db.Column(EncryptedJSON)            # só hashes dos códigos de recuperação
    token_version = db.Column(db.Integer, nullable=False, default=0)   # +1 = derruba todas as sessões
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    invoices = db.relationship("Invoice", backref="user", cascade="all, delete-orphan")
    tokens = db.relationship("UserToken", cascade="all, delete-orphan")
    reserve_entries = db.relationship("ReserveEntry", cascade="all, delete-orphan")


class UserToken(db.Model):
    """Links de uso único enviados por e-mail (kind: verify | reset). Só o hash é guardado."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    kind = db.Column(db.String(10), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=now)


class UsageLog(db.Model):
    """Cota diária de usos da IA por usuário (controle de custo)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    # índice composto: toda consulta real filtra user_id E created_at juntos (cota diária, cota global)
    __table_args__ = (db.Index("ix_usage_log_user_id_created_at", "user_id", "created_at"),)


class AuditLog(db.Model):
    """Registro de acessos e eventos de segurança (guarda de 6 meses, Marco Civil art. 15)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)           # sem FK: o registro legal sobrevive à exclusão da conta
    event = db.Column(db.String(30), nullable=False)
    ip = db.Column(db.String(45))
    ua = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, index=True)


class ReserveEntry(db.Model):
    """Registro de quanto o mentorado realmente guardou (reserva de verdade, não só projeção)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    data = db.Column(EncryptedJSON, nullable=False)   # {"valor": 250.0, "nota": "13º adiantado"}
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    __table_args__ = (db.Index("ix_reserve_entry_user_id_created_at", "user_id", "created_at"),)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    label = db.Column(db.String(80), nullable=False)
    bank = db.Column(db.String(60), default="")
    profile = db.Column(EncryptedJSON, nullable=False)   # renda, gastos fixos…
    items = db.Column(EncryptedJSON, nullable=False)     # lançamentos da fatura
    reserve_pct = db.Column(db.Float, default=60.0)
    plan = db.Column(EncryptedJSON)                      # plano gerado pela IA
    plan_ai = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now)
