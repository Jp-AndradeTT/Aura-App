import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { activity, changePassword, deleteAccount, disable2fa, enable2fa, exportMyData, logoutAll, me, setup2fa } from "./api";

const LABEL = {
  login_ok: "Entrada na conta", login_fail: "Tentativa de entrada com senha incorreta", mfa_ok: "Entrada com verificação em duas etapas",
  mfa_fail: "Código de duas etapas incorreto", "2fa_reset_email": "Verificação em duas etapas desativada por link no e-mail", mfa_recover_request: "Pedido para recuperar acesso à verificação em duas etapas", lockout: "Conta bloqueada por 15 minutos após várias tentativas", register: "Cadastro iniciado",
  verify: "E-mail confirmado e senha criada", password_reset: "Senha redefinida por e-mail", password_change: "Senha alterada",
  "2fa_enable": "Verificação em duas etapas ativada", "2fa_disable": "Verificação em duas etapas desativada",
  logout_all: "Saída de todos os dispositivos", "2fa_reset_support": "Verificação em duas etapas redefinida pelo suporte",
};

function TwoFactor({ user, onChanged, say }) {
  const [setup, setSetup] = useState(null); // { secret, uri, qr }
  const [f, setF] = useState({ password: "", code: "" });
  const [codes, setCodes] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = async (fn) => { setBusy(true); try { await fn(); } catch (e) { say({ err: e.message }); } finally { setBusy(false); } };
  const refresh = async () => onChanged((await me()).user);

  const start = () => run(async () => { const s = await setup2fa(); setSetup({ ...s, qr: await QRCode.toDataURL(s.uri, { width: 200, margin: 1 }) }); });
  const enable = (e) => { e.preventDefault(); run(async () => { setCodes((await enable2fa(f.password, f.code)).recovery_codes); setSetup(null); setF({ password: "", code: "" }); await refresh(); }); };
  const disable = (e) => { e.preventDefault(); run(async () => { await disable2fa(f.password, f.code); setF({ password: "", code: "" }); say({ ok: "Verificação em duas etapas desativada." }); await refresh(); }); };
  const download = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([`Códigos de recuperação do Aura (cada um vale uma vez)\n\n${codes.join("\n")}\n`], { type: "text/plain" }));
    a.download = "aura-codigos-de-recuperacao.txt"; a.click(); URL.revokeObjectURL(a.href);
  };
  const fields = (
    <div className="fields">
      <label className="field"><span>Sua senha</span><input type="password" required autoComplete="current-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></label>
      <label className="field"><span>Código do aplicativo{user.totp ? " (ou de recuperação)" : ""}</span><input type="text" inputMode="numeric" required autoComplete="one-time-code" value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} /></label>
    </div>
  );

  return (
    <div className="sheet">
      <h3>Verificação em duas etapas {user.totp && <span className="chip ok">ativa</span>}</h3>
      <p className="lead">Além da senha, o login pede um código do seu celular. Protege sua conta mesmo se a senha vazar.</p>
      {codes && (
        <div className="note warn"><b>Guarde estes códigos de recuperação agora.</b> Cada um vale uma vez e só aparecem nesta tela. Use-os se perder o celular.
          <pre className="codes">{codes.join("\n")}</pre>
          <div className="row"><button className="btn ghost" onClick={download}>Baixar .txt</button><button className="btn" onClick={() => setCodes(null)}>Já guardei</button></div></div>
      )}
      {!user.totp && !setup && !codes && <button className="btn" disabled={busy} onClick={start}>Ativar</button>}
      {setup && (
        <form onSubmit={enable}>
          <p>1. Abra um aplicativo autenticador (Google Authenticator, Microsoft Authenticator, Authy…) e leia o QR code.</p>
          <img src={setup.qr} alt="QR code para o aplicativo autenticador" width="200" height="200" />
          <p className="muted">Sem câmera? Digite esta chave: <code>{setup.secret}</code></p>
          <p>2. Digite sua senha e o código de 6 dígitos que o aplicativo mostra.</p>
          {fields}
          <div className="row"><button className="btn" disabled={busy}>Confirmar e ativar</button><button type="button" className="btn ghost" disabled={busy} onClick={() => setSetup(null)}>Cancelar</button></div>
        </form>
      )}
      {user.totp && !codes && <form onSubmit={disable}><p className="muted">Para desativar, confirme com a senha e um código.</p>{fields}<div className="row"><button className="btn ghost" disabled={busy}>Desativar</button></div></form>}
    </div>
  );
}

export default function Account({ user, onLoggedOut, onChanged }) {
  const [pw, setPw] = useState({ current: "", next: "" });
  const [del, setDel] = useState("");
  const [msg, setMsg] = useState({ ok: "", err: "" });
  const [events, setEvents] = useState([]);
  const [busy, setBusy] = useState(false);
  const say = (m) => setMsg({ ok: "", err: "", ...m });
  useEffect(() => {
    let ignore = false;
    activity().then((r) => { if (!ignore) setEvents(r.events); }).catch(() => {});
    return () => { ignore = true; }; // duas ações em sequência rápida não deixam a lista "regredir" com a resposta mais antiga
  }, [user.totp, msg.ok]);
  const act = async (fn, okText) => { say({}); setBusy(true); try { await fn(); if (okText) say({ ok: okText }); } catch (e) { say({ err: e.message }); } finally { setBusy(false); } };

  return (
    <>
      <h2>Minha conta</h2>
      <p className="lead">{user.name} · {user.email}</p>
      {msg.err && <div className="err" role="alert">{msg.err}</div>}
      {msg.ok && <div className="ok-msg" role="status">{msg.ok}</div>}

      <form className="sheet" onSubmit={(e) => { e.preventDefault(); act(async () => { await changePassword(pw.current, pw.next); setPw({ current: "", next: "" }); }, "Senha alterada. Os outros dispositivos foram desconectados e enviamos um aviso ao seu e-mail."); }}>
        <h3>Alterar senha</h3>
        <div className="fields">
          <label className="field"><span>Senha atual</span><input type="password" required autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} /></label>
          <label className="field"><span>Nova senha (mínimo de 10 caracteres)</span><input type="password" required minLength={10} autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} /></label>
        </div>
        <div className="row"><button className="btn" disabled={busy}>Salvar nova senha</button></div>
      </form>

      <TwoFactor user={user} onChanged={onChanged} say={say} />

      <div className="sheet">
        <h3>Atividade recente</h3>
        {!events.length ? <p className="lead">Sem eventos ainda.</p> : (
          <div className="tw"><table><tbody>{events.map((e, i) => (
            <tr key={i}><td>{LABEL[e.event] || e.event}</td><td className="muted">{new Date(e.at).toLocaleString("pt-BR")}</td><td className="muted">{e.ip}</td></tr>
          ))}</tbody></table></div>
        )}
        <p className="muted">Não reconhece algo? Altere a senha e saia de todos os dispositivos.</p>
        <button className="btn ghost" disabled={busy} onClick={() => act(async () => { await logoutAll(); onLoggedOut(); })}>Sair de todos os dispositivos</button>
      </div>

      <div className="sheet">
        <h3>Meus dados</h3>
        <p className="lead">Baixe uma cópia de tudo que guardamos sobre você (cadastro, faturas e planos).</p>
        <button className="btn ghost" disabled={busy} onClick={() => act(exportMyData)}>Exportar meus dados</button>
      </div>

      <form className="sheet danger" onSubmit={(e) => { e.preventDefault(); if (!window.confirm("Isso apaga sua conta, faturas e planos de forma definitiva. Continuar?")) return; act(async () => { await deleteAccount(del); onLoggedOut(); }); }}>
        <h3>Excluir minha conta</h3>
        <p className="lead">Apaga cadastro, faturas e planos de forma definitiva. Digite sua senha para confirmar.</p>
        <label className="field" style={{ maxWidth: 320 }}><span>Senha</span><input type="password" required autoComplete="current-password" value={del} onChange={(e) => setDel(e.target.value)} /></label>
        <div className="row"><button className="btn bad" disabled={busy}>Excluir conta</button></div>
      </form>
    </>
  );
}
