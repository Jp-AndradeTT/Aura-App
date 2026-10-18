"""E-mails por API HTTPS (Resend), enviados em segundo plano. Para outro provedor, troque só _post()."""
import html
import json
import os
import re
import smtplib
import ssl
import threading
import urllib.request
from email.message import EmailMessage


def _smtp(to, subject, body):
    """SMTP: serve para Gmail (senha de app), Brevo, Outlook, servidor do domínio da cliente etc."""
    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))
    user, pwd = os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = os.getenv("MAIL_FROM") or user, to, subject
    links = re.findall(r'href="([^"]+)"', html.unescape(body))
    msg.set_content(re.sub(r"<[^>]+>", " ", body).strip() + "\n\n" + "\n".join(links))  # versão em texto puro
    msg.add_alternative(body, subtype="html")
    ctx = ssl.create_default_context()
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=15, context=ctx)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        if os.getenv("SMTP_STARTTLS", "1") == "1":
            server.starttls(context=ctx)
    with server:
        if user:
            server.login(user, pwd)
        server.send_message(msg)


def _post(to, subject, body):
    if os.getenv("SMTP_HOST"):
        try:
            _smtp(to, subject, body)
        except Exception as e:  # nunca expõe o erro ao usuário
            print(f"[mailer] falha SMTP: {type(e).__name__}")
        return
    key = os.getenv("RESEND_API_KEY")
    if not key:
        print("[mailer] nenhum provedor configurado (SMTP_HOST ou RESEND_API_KEY): e-mail NÃO enviado.")
        return
    data = json.dumps({"from": os.getenv("MAIL_FROM", "Aura <onboarding@resend.dev>"), "to": [to], "subject": subject, "html": body}).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=data, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "aura/1.0"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:  # nunca expõe o erro ao usuário
        print(f"[mailer] falha ao enviar e-mail: {type(e).__name__}")


def send_email(to, subject, body):
    # Em segundo plano: a resposta da API não demora mais (nem revela, pelo tempo, se o e-mail existe).
    threading.Thread(target=_post, args=(to, subject, body), daemon=True).start()


def _wrap(title, content):
    return (f'<div style="font-family:system-ui,sans-serif;max-width:480px;margin:auto;color:#14213d"><h2>{html.escape(title)}</h2>{content}'
            '<p style="color:#5b667c;font-size:13px">Aura · mensagem automática, não responda. Nunca pedimos sua senha por e-mail.</p></div>')


def _button(link, label):
    return (f'<p><a href="{html.escape(link)}" style="background:#2b59c3;color:#fff;padding:12px 18px;border-radius:6px;'
            f'text-decoration:none;display:inline-block">{label}</a></p>')


def _hi(name):
    first = (name or "").strip().split()
    return f"<p>Olá, {html.escape(first[0] if first else 'você')}.</p>"


def send_verify_email(email, name, link):
    if os.getenv("FLASK_DEBUG") == "1":
        print(f"[mailer][debug] link de ativação para {email}: {link}")
    send_email(email, "Confirme seu e-mail no Aura", _wrap("Confirme seu e-mail", _hi(name) + "<p>Para ativar sua conta e criar sua senha, use o botão abaixo. O link vale por <b>24 horas</b> e só pode ser usado uma vez.</p>" + _button(link, "Ativar conta") + "<p>Não pediu? Ignore este e-mail: nenhuma conta será ativada.</p>"))


def send_reset_email(email, name, link):
    if os.getenv("FLASK_DEBUG") == "1":
        print(f"[mailer][debug] link de redefinição para {email}: {link}")
    send_email(email, "Redefinir sua senha no Aura", _wrap("Redefinir sua senha", _hi(name) + "<p>Recebemos um pedido para redefinir a senha da sua conta. O link vale por <b>30 minutos</b> e só pode ser usado uma vez.</p>" + _button(link, "Criar nova senha") + "<p>Não foi você? Ignore este e-mail: sua senha continua a mesma.</p>"))


def send_exists_email(email, name):
    send_email(email, "Você já tem conta no Aura", _wrap("Você já tem uma conta", _hi(name) + "<p>Alguém tentou criar uma conta com este e-mail, mas ele já está cadastrado. Se foi você, basta entrar ou usar \"Esqueci minha senha\". Se não foi, ignore.</p>"))


def send_security_email(email, name, title, text):
    # title/text são sempre texto fixo do próprio código hoje, mas por segurança (defesa em profundidade:
    # cabeçalho de e-mail não aceita \r\n, e um e-mail de segurança que falhe silenciosamente é o pior caso
    # possível aqui) nunca deixamos um caractere de quebra de linha chegar ao cabeçalho do assunto.
    safe_title = (title or "").replace("\r", " ").replace("\n", " ")
    send_email(email, f"Aura: {safe_title}", _wrap(safe_title, _hi(name) + f"<p>{html.escape(text)}</p><p><b>Não foi você?</b> Use \"Esqueci minha senha\" agora para recuperar a conta.</p>"))


def send_mfa_reset_email(email, name, link):
    if os.getenv("FLASK_DEBUG") == "1":
        print(f"[mailer][debug] link para desativar a 2ª etapa de {email}: {link}")
    send_email(email, "Recuperar acesso no Aura", _wrap("Perdeu o acesso ao aplicativo autenticador?", _hi(name) + "<p>Recebemos um pedido para desativar a verificação em duas etapas da sua conta. O link vale por <b>30 minutos</b> e vai pedir a sua senha.</p>" + _button(link, "Desativar verificação") + "<p>Não foi você? Ignore este e-mail e altere sua senha.</p>"))
