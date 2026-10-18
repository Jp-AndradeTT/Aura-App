import { useEffect, useId, useState } from "react";
import { addReserve, deleteInvoice, deleteReserve, getInvoice, listInvoices, listReserve } from "./api";
import { brl, chipClass } from "./parts";
import {
  CategoryIcon, categoryColor, IconCalendarDown, IconChartUp, IconGauge, IconListCheck,
  IconPiggy, IconSpark, IconUpload, IconUser, IconWallet,
} from "./Icons";

function Onboarding({ onNew }) {
  const steps = [
    { icon: <IconUpload />, title: "Envie sua fatura", text: "PDF ou foto do cartão. A IA lê os lançamentos para você." },
    { icon: <IconListCheck />, title: "Confira os lançamentos", text: "Corrija o que a leitura errou antes de calcular qualquer coisa." },
    { icon: <IconUser />, title: "Conte sua renda e gastos fixos", text: "Sem isso não dá para saber quanto da sua renda está comprometido." },
    { icon: <IconChartUp />, title: "Receba seu plano", text: "Resumo, parcelas, projeção dos próximos meses e um passo a passo para guardar dinheiro." },
  ];
  return (
    <div className="sheet onboard">
      <h3>Bem-vinda ao Aura</h3>
      <p className="lead">Em 4 passos simples você vai entender sua fatura de verdade e ter um plano para não dever nada.</p>
      <ol className="onboard-steps">
        {steps.map((s, i) => (
          <li key={s.title}>
            <span className="onboard-ic">{s.icon}</span>
            <div><b>{i + 1}. {s.title}</b><p>{s.text}</p></div>
          </li>
        ))}
      </ol>
      <div className="note">Seus dados financeiros ficam criptografados e só você tem acesso. A fatura em si não é guardada, só os lançamentos que você confirmar.</div>
      <button className="btn" onClick={onNew}>Enviar minha primeira fatura</button>
    </div>
  );
}

function Insights({ inv, reserve }) {
  const an = inv.analysis;
  const nivel = an.pct_comprometido > 70 ? "bad" : an.pct_comprometido > 50 ? "warn" : "ok";
  const top = an.categorias[0];
  const metaPct = reserve?.meta?.valor ? Math.min(100, Math.round((reserve.total / reserve.meta.valor) * 100)) : null;
  return (
    <div className="sheet">
      <h3>Insights financeiros</h3>
      <p className="lead" style={{ marginBottom: 14 }}>Leitura rápida da fatura mais recente, <b>{inv.label}</b>.</p>
      <div className="insights">
        <div className={`insight-card ${nivel}`}>
          <div className="ic-head"><IconGauge />Renda comprometida</div>
          <div className="ic-val">{Math.round(an.pct_comprometido)}%</div>
          <div className="ic-sub">{nivel === "bad" ? "Alto: evite novas parcelas" : nivel === "warn" ? "Moderado: pouca margem" : "Saudável"}</div>
        </div>
        <div className="insight-card">
          <div className="ic-head"><IconWallet />Saldo em parcelas</div>
          <div className="ic-val">{brl(an.restante_parcelas)}</div>
          <div className="ic-sub">Ainda a pagar nos próximos meses</div>
        </div>
        <div className={`insight-card ${metaPct >= 100 ? "ok" : ""}`}>
          <div className="ic-head"><IconPiggy />Reserva guardada</div>
          <div className="ic-val">{metaPct === null ? brl(reserve?.total || 0) : `${metaPct}%`}</div>
          <div className="ic-sub">{reserve?.meta?.valor ? `${brl(reserve.total)} de ${brl(reserve.meta.valor)}` : "Defina uma meta enviando uma fatura"}</div>
        </div>
        {top && (
          <div className="insight-card">
            <div className="ic-head"><IconSpark />Maior categoria</div>
            <div className="ic-val" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 20 }}>
              <CategoryIcon name={top.nome} size={24} />{top.nome}
            </div>
            <div className="ic-sub">{brl(top.valor)} ({an.total ? Math.round((top.valor / an.total) * 100) : 0}% da fatura)</div>
          </div>
        )}
        {an.queda && (
          <div className="insight-card ok">
            <div className="ic-head"><IconCalendarDown />Próxima queda</div>
            <div className="ic-val">{brl(an.queda.economia)}</div>
            <div className="ic-sub">A fatura cai em {an.queda.mes}</div>
          </div>
        )}
      </div>
      <div className="cat-list">
        {an.categorias.slice(0, 5).map((c) => {
          const pct = an.total ? Math.round((c.valor / an.total) * 100) : 0;
          return (
            <div className="cat-row" key={c.nome}>
              <CategoryIcon name={c.nome} />
              <div className="cat-info">
                <div className="cat-top"><b>{c.nome}</b><span>{brl(c.valor)}</span></div>
                <div className="cat-bar"><i style={{ width: `${pct}%`, background: categoryColor(c.nome) }} /></div>
              </div>
              <span className="pct">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ReserveTracker({ reserve, onChange }) {
  const [valor, setValor] = useState("");
  const [nota, setNota] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const meta = reserve.meta?.valor || 0;
  const pct = meta ? Math.min(100, Math.round((reserve.total / meta) * 100)) : 0;

  async function add(e) {
    e.preventDefault();
    const n = Number(valor);
    if (!n || n <= 0) { setError("Informe um valor maior que zero."); return; }
    setBusy(true); setError("");
    try { onChange(await addReserve(n, nota)); setValor(""); setNota(""); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function remove(id) {
    if (!window.confirm("Apagar este registro de reserva?")) return;
    try { onChange(await deleteReserve(id)); } catch (err) { setError(err.message); }
  }

  return (
    <div className="sheet">
      <h3>Sua reserva de verdade</h3>
      <p className="lead">Registre quanto você realmente guardou a cada mês. O plano projeta; aqui você acompanha o progresso de fato.</p>
      {meta > 0 && (
        <>
          <div className="cat-top" style={{ marginBottom: 6 }}>
            <b>{brl(reserve.total)} guardado</b><span>{pct}% da meta de {brl(meta)}</span>
          </div>
          <div className="cat-bar" style={{ height: 10, marginBottom: 18 }}><i style={{ width: `${pct}%`, background: "var(--mint)" }} /></div>
        </>
      )}
      {error && <div className="err" role="alert">{error}</div>}
      <form className="row reserve-form" onSubmit={add}>
        <label className="field" style={{ maxWidth: 180 }}><span>Quanto guardou</span>
          <input type="number" min="0.01" max="1000000" step="0.01" placeholder="R$ 0,00" value={valor} onChange={(e) => setValor(e.target.value)} /></label>
        <label className="field" style={{ flex: 1, minWidth: 180 }}><span>Nota (opcional)</span>
          <input type="text" maxLength={120} placeholder="Ex.: 13º adiantado" value={nota} onChange={(e) => setNota(e.target.value)} /></label>
        <button className="btn" disabled={busy} style={{ alignSelf: "end" }}>Registrar</button>
      </form>
      {reserve.entries.length > 0 && (
        <div className="tw" style={{ marginTop: 18 }}>
          <table>
            <thead><tr><th>Data</th><th>Nota</th><th className="n">Valor</th><th /></tr></thead>
            <tbody>{[...reserve.entries].reverse().map((e) => (
              <tr key={e.id}><td>{new Date(e.created_at).toLocaleDateString("pt-BR")}</td><td>{e.nota || "—"}</td>
                <td className="n">{brl(e.valor)}</td>
                <td className="n"><button className="btn ghost" aria-label="Apagar registro" onClick={() => remove(e.id)}>×</button></td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Trend({ rows }) {
  const gradId = `trendFill-${useId()}`;
  if (rows.length < 2) return null;
  const W = 560, H = 120, P = 14, max = Math.max(...rows.map((r) => r.total)) || 1;
  const pts = rows.map((r, i) => [P + (i * (W - 2 * P)) / (rows.length - 1), H - P - (r.total / max) * (H - 2 * P)]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="trend" role="img" aria-label="Evolução do total das faturas">
      <defs><linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f2b84b" stopOpacity=".32" /><stop offset="1" stopColor="#f2b84b" stopOpacity="0" /></linearGradient></defs>
      <polygon points={`${pts.map((p) => p.join(",")).join(" ")} ${pts[pts.length - 1][0]},${H} ${pts[0][0]},${H}`} fill={`url(#${gradId})`} />
      <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke="#f2b84b" strokeWidth="2.5" strokeLinejoin="round" />
      {pts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="4.5" fill="#ffe3a3" stroke="#f2b84b" strokeWidth="2"><title>{rows[i].label}: {brl(rows[i].total)}</title></circle>)}
    </svg>
  );
}

export default function Dashboard({ user, onNew, onOpen }) {
  const [rows, setRows] = useState(null);
  const [latest, setLatest] = useState(null);
  const [reserve, setReserve] = useState(null);
  const [error, setError] = useState("");
  const load = () => listInvoices().then((r) => setRows(r.invoices)).catch((e) => setError(e.message));
  useEffect(() => { load(); listReserve().then(setReserve).catch(() => {}); }, []);
  useEffect(() => {
    let ignore = false;
    if (rows && rows.length) getInvoice(rows[rows.length - 1].id).then((r) => { if (!ignore) setLatest(r); }).catch(() => {});
    else setLatest(null);
    return () => { ignore = true; }; // evita que a resposta de uma fatura já trocada/excluída sobrescreva a mais recente
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows?.length, rows?.[rows?.length - 1]?.id]);

  async function remove(r) {
    if (!window.confirm(`Excluir "${r.label}"? Esta ação não pode ser desfeita.`)) return;
    try { await deleteInvoice(r.id); load(); } catch (e) { setError(e.message); }
  }

  if (!rows) return error ? <div className="err" role="alert">{error}</div> : <p className="lead">Carregando seu histórico…</p>;
  const last = rows[rows.length - 1], prev = rows[rows.length - 2];
  const diff = last && prev ? last.total - prev.total : null;
  return (
    <>
      <h2>Olá, {user.name.split(" ")[0]}</h2>
      {error && <div className="err" role="alert">{error}</div>}
      {!rows.length ? (
        <Onboarding onNew={onNew} />
      ) : (
        <>
          <p className="lead">Sua fatura mais recente é de <b>{brl(last.total)}</b>
            {diff !== null && diff !== 0 && <>, {diff < 0 ? "uma queda" : "um aumento"} de {brl(Math.abs(diff))} em relação à anterior</>}
            {diff === 0 && <>, sem mudança em relação à anterior</>}.</p>
          {latest && <Insights inv={latest} reserve={reserve} />}
          {reserve && <ReserveTracker reserve={reserve} onChange={setReserve} />}
          <div className="sheet"><h3>Evolução das faturas</h3><Trend rows={rows} />
            <div className="tw"><table>
              <thead><tr><th>Fatura</th><th>Data</th><th className="n">Total</th><th className="n">Parcelado</th><th className="n">% da renda</th><th className="n">Saldo em parcelas</th><th /></tr></thead>
              <tbody>{[...rows].reverse().map((r) => (
                <tr key={r.id}><td><b>{r.label}</b>{r.bank ? <div className="muted">{r.bank}</div> : null}</td><td>{new Date(r.created_at).toLocaleDateString("pt-BR")}</td>
                  <td className="n">{brl(r.total)}</td><td className="n">{brl(r.parcelado)}</td>
                  <td className="n"><span className={`chip ${chipClass(r.pct)}`}>{Math.round(r.pct)}%</span></td><td className="n">{brl(r.restante)}</td>
                  <td className="n"><button className="btn ghost" onClick={() => onOpen(r.id)}>Abrir</button>{" "}
                    <button className="btn ghost" aria-label={`Excluir ${r.label}`} onClick={() => remove(r)}>×</button></td></tr>
              ))}</tbody></table></div></div>
          <p className="lead">Pagou parcelas adiantadas ou quitou um empréstimo? Envie a fatura de novo com os valores atualizados para refazer a projeção.</p>
          <button className="btn" onClick={onNew}>Enviar nova fatura</button>
        </>
      )}
    </>
  );
}
