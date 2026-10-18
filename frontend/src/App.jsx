import { useEffect, useState } from "react";
import { getInvoice, logout, me, onUnauthorized } from "./api";
import Account from "./Account";
import AdminUsage from "./AdminUsage";
import { IconDoc, IconGrid, IconOut, IconShield, IconUpload, IconUser, IconUsers, Logo } from "./Icons";
import Auth from "./Auth";
import Dashboard from "./Dashboard";
import Flow from "./Flow";
import Privacy from "./Privacy";
import Terms from "./Terms";

export default function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [view, setView] = useState("home"); // home | flow | account | policy
  const [current, setCurrent] = useState(null); // fatura aberta (null = nova)
  const [error, setError] = useState("");

  const reset = () => { setUser(null); setView("home"); setCurrent(null); setError(""); };

  useEffect(() => {
    onUnauthorized(reset);
    me().then((r) => setUser(r.user)).catch(() => {}).finally(() => setReady(true));
  }, []);

  async function open(id) {
    setError("");
    try { setCurrent(await getInvoice(id)); setView("flow"); } catch (e) { setError(e.message); }
  }

  if (!ready) return <div className="auth"><div className="brand">Aura</div><p className="lead" role="status">Carregando…</p></div>;
  if (view === "policy") return <div className="main solo"><Privacy back={() => setView("home")} onTerms={() => setView("terms")} /></div>;
  if (view === "terms") return <div className="main solo"><Terms back={() => setView("home")} onPolicy={() => setView("policy")} /></div>;
  if (!user) return <Auth onAuth={setUser} onPolicy={() => setView("policy")} onTerms={() => setView("terms")} />;

  const go = (v) => { setError(""); setCurrent(null); setView(v); };
  return (
    <div className="app">
      <aside className="side">
        <div className="brand"><Logo />Aura</div>
        <p className="brand-sub">Mentora financeira para sua fatura</p>
        <nav className="nav" aria-label="Principal">
          <button className={view === "home" ? "on" : ""} onClick={() => go("home")}><IconGrid />Painel</button>
          <button className={view === "flow" && !current ? "on" : ""} onClick={() => go("flow")}><IconUpload />Nova fatura</button>
          <button className={view === "account" ? "on" : ""} onClick={() => go("account")}><IconUser />Minha conta</button>
          {user.admin && <button className={view === "admin" ? "on" : ""} onClick={() => go("admin")}><IconUsers />Painel de uso</button>}
          <button onClick={() => setView("policy")}><IconShield />Privacidade</button>
          <button onClick={() => setView("terms")}><IconDoc />Termos de uso</button>
        </nav>
        <nav className="nav account" aria-label="Sessão">
          <span className="muted">{user.email}</span>
          <button onClick={() => logout().finally(reset)}><IconOut />Sair</button>
        </nav>
      </aside>
      <main className="main">
        {error && <div className="err" role="alert">{error}</div>}
        {view === "home" && <Dashboard user={user} onNew={() => go("flow")} onOpen={open} />}
        {view === "flow" && <Flow key={current?.id || "new"} initial={current} onDone={() => go("home")} />}
        {view === "account" && <Account user={user} onLoggedOut={reset} onChanged={setUser} />}
        {view === "admin" && user.admin && <AdminUsage />}
      </main>
    </div>
  );
}
