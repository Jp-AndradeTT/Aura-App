"""Roda migração + regressão + ataque de entradas num PostgreSQL REAL embutido (não mexe em nenhum banco seu).
Requisito (só para testar): pip install pgserver.   Uso, dentro de backend/:  python tests/run_on_postgres.py"""
import os, sys, subprocess, tempfile, secrets
import pgserver
from cryptography.fernet import Fernet
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
srv = pgserver.get_server(tempfile.mkdtemp(), cleanup_mode="stop"); uri = srv.get_uri().replace("postgresql+psycopg://", "postgresql://"); print("URI:", uri[:48])
env = dict(os.environ, DATABASE_URL=uri, TEST_DATABASE_URL=uri, AUTO_CREATE_DB="0", JWT_SECRET="x" + secrets.token_hex(16), DATA_KEY=Fernet.generate_key().decode(), COOKIE_SECURE="0")
def run(label, *cmd, tail=6):
    r = subprocess.run(cmd, cwd=B, env=env, capture_output=True, text=True, timeout=280)
    out = [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and "Warning" not in l and "jwt" not in l and "return self" not in l]
    print(f"[{label}] exit={r.returncode}", *out[-tail:], sep="\n   ")
try:
    run("flask db upgrade (Postgres vazio)", "flask", "--app", "app", "db", "upgrade", tail=3)
    print("tabelas no Postgres:", srv.psql("select string_agg(tablename, ', ' order by tablename) from pg_tables where schemaname='public';").strip().splitlines()[2].strip())
    run("flask db check (migração = modelos?)", "flask", "--app", "app", "db", "check", tail=2)
    run("regressão no Postgres", sys.executable, "tests/regress.py")
    run("ataque de entradas no Postgres", sys.executable, "tests/fuzz_inputs.py")
finally:
    srv.cleanup()
