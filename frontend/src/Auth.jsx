import { useEffect, useState } from "react";
import { Logo } from "./Icons";
import { forgotPassword, getConfig, login, loginMfa, recoverMfa, register, resendVerification, resetMfa, resetPassword, verifyAccount } from "./api";

function Scene() {
  return <div className="scene" aria-hidden="true"><div className="layer l-far" /><div className="layer l-mid" /><div className="layer l-near" /></div>;
}

const TITLES = { login: "Entrar", register: "Criar conta", forgot: "Recuperar senha", reset: "Criar nova senha", verify: "Ativar sua conta", mfa: "Verificação em duas etapas", recover: "Desativar verificação em duas etapas" };

export default function Auth({ onAuth, onPolicy, onTerms }) {
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ name: "", email: "", password: "", confirm: "", code: "", invite: "", accept_privacy: false });
  const [cfg, setCfg] = useState({});
  const [token, setToken] = useState("");
  const [mfaToken, setMfaToken] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const up = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const go = (m) => { setMode(m); setError(""); setNotice(""); setF((f) => ({ ...f, password: "", confirm: "", code: "" })); };

  // Os links dos e-mails trazem o código no fragmento (#reset=... / #verify=...), que nunca vai para o servidor.
  useEffect(() => {
    const m = window.location.hash.match(/(reset|verify|recover)=([\w-]+)/);
    if (m) { setToken(m[2]); setMode(m[1]); window.history.replaceState(null, "", window.location.pathname); }
    getConfig().then(setCfg).catch(() => {});
  }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      if (mode === "forgot") setNotice((await forgotPassword(f.email)).message);
      else if (mode === "register") setNotice((await register(f)).message);
      else if (mode === "reset" || mode === "verify") {
        if (f.password !== f.confirm) throw new Error("As senhas não são iguais.");
        await (mode === "reset" ? resetPassword : verifyAccount)(token, f.password);
        go("login"); setNotice(mode === "reset" ? "Senha alterada. Entre com a nova senha." : "Conta ativada. Entre com seu e-mail e senha."); setF({ ...f, password: "", confirm: "" });
      } else if (mode === "recover") {
        await resetMfa(token, f.password);
        go("login"); setNotice("Verificação em duas etapas desativada. Entre com sua senha e reative em Minha conta, se quiser."); setF({ ...f, password: "" });
      } else if (mode === "mfa") onAuth((await loginMfa(mfaToken, f.code)).user);
      else {
        const r = await login(f);
        if (r.mfa_required) { setMfaToken(r.mfa_token); setF({ ...f, password: "", code: "" }); go("mfa"); } else onAuth(r.user);
      }
    } catch (err) {
      setError(err.message);
      if (mode === "mfa" && err.message.startsWith("A verificação expirou")) go("login");
    } finally { setBusy(false); }
  }

  const pwd = (k, label) => (
    <label className="field" style={{ marginTop: 12 }}><span>{label}</span>
      <input type="password" required minLength={mode === "login" || mode === "recover" ? undefined : 10} value={f[k]} onChange={up(k)}
             autoComplete={mode === "login" || mode === "recover" ? "current-password" : "new-password"} /></label>
  );
  const setting = mode === "reset" || mode === "verify";
  async function recover() {
    try { setNotice((await recoverMfa(mfaToken)).message); setError(""); } catch (e) { setError(e.message); }
  }

  return (
    <div className="auth-page">
      <Scene />
      <section className="auth-hero">
        <div className="brand"><Logo size={40} />Aura</div>
        <h1>Entenda sua fatura e comece a guardar dinheiro.</h1>
        <p>Envie a fatura do cartão e receba o resumo, as parcelas dos próximos meses e um plano para montar sua reserva.</p>
        <ul><li>Resumo e projeção das suas parcelas</li><li>Plano de reserva passo a passo</li><li>Converse com a Aura, sua mentora financeira</li></ul>
      </section>
      <div>
      <form className="sheet auth-card" onSubmit={submit}>
        <h2>{TITLES[mode]}</h2>
        {error && <div className="err" role="alert">{error}</div>}
        {notice && <div className="ok-msg" role="status">{notice}</div>}
        {error.startsWith("Confirme") && <p><button type="button" className="link" onClick={async () => { try { setNotice((await resendVerification(f.email)).message); setError(""); } catch (e) { setError(e.message); } }}>Reenviar e-mail de confirmação</button></p>}
        {mode === "forgot" && <p className="lead">Informe seu e-mail e enviaremos um link para criar uma nova senha.</p>}
        {mode === "register" && <p className="lead">Enviaremos um link para confirmar seu e-mail. É nele que você cria sua senha.</p>}
        {mode === "verify" && <p className="lead">E-mail confirmado. Agora crie sua senha.</p>}
        {mode === "mfa" && <><p className="lead">Digite o código de 6 dígitos do seu aplicativo autenticador, ou um código de recuperação.</p>
          <label className="field"><span>Código</span><input type="text" inputMode="numeric" autoComplete="one-time-code" autoFocus required value={f.code} onChange={up("code")} /></label>
          <p><button type="button" className="link" onClick={recover}>Perdi o acesso ao aplicativo e aos códigos</button></p></>}
        {mode === "recover" && <p className="lead">Confirme com a sua senha para desativar a verificação em duas etapas.</p>}
        {mode === "register" && <label className="field"><span>Nome</span><input type="text" required value={f.name} onChange={up("name")} /></label>}
        {mode === "register" && cfg.invite_required && <label className="field" style={{ marginTop: 12 }}><span>Código de convite (fornecido pela sua mentora)</span><input type="text" required autoComplete="off" value={f.invite} onChange={up("invite")} /></label>}
        {(mode === "login" || mode === "register" || mode === "forgot") && <label className="field" style={{ marginTop: 12 }}><span>E-mail</span>
          <input type="text" inputMode="email" autoComplete="email" required value={f.email} onChange={up("email")} /></label>}
        {(mode === "login" || mode === "recover") && pwd("password", "Senha")}
        {setting && pwd("password", "Nova senha (mínimo de 10 caracteres)")}
        {setting && pwd("confirm", "Repita a senha")}
        {mode === "register" && (
          <label className="check"><input type="checkbox" checked={f.accept_privacy} onChange={up("accept_privacy")} />
            <span>Li e aceito os <button type="button" className="link" onClick={onTerms}>Termos de Uso</button> e a <button type="button" className="link" onClick={onPolicy}>Política de Privacidade</button>, inclusive o envio dos dados da fatura à IA para gerar a análise.</span></label>
        )}
        <div className="row">
          <button className="btn" disabled={busy || (mode === "register" && !f.accept_privacy)}>
            {mode === "forgot" ? "Enviar link" : mode === "register" ? "Enviar link de ativação" : mode === "mfa" ? "Confirmar" : mode === "recover" ? "Desativar verificação" : setting ? "Salvar senha" : "Entrar"}</button>
          {mode === "login" && <button type="button" className="btn ghost" onClick={() => go("register")}>Criar uma conta</button>}
          {mode !== "login" && <button type="button" className="btn ghost" onClick={() => go("login")}>Voltar para entrar</button>}
        </div>
        {mode === "login" && <p style={{ marginBottom: 0 }}><button type="button" className="link" onClick={() => go("forgot")}>Esqueci minha senha</button></p>}
      </form>
      <div className="auth-foot"><button className="link" onClick={onTerms}>Termos de Uso</button><button className="link" onClick={onPolicy}>Política de Privacidade</button></div>
      </div>
    </div>
  );
}
