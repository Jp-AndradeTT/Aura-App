import { useState } from "react";
import { CategoryIcon, categoryColor, IconCloud } from "./Icons";

export const brl = (v) => Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const newItemId = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`);
// dá um id estável (só no navegador, nunca é salvo) a cada lançamento, para a lista usar key={it._id} em vez
// do índice: remover um item no meio não faz os de baixo "herdarem" a posição/foco de quem foi removido.
export const withIds = (items) => (items || []).map((it) => (it._id ? it : { ...it, _id: newItemId() }));
export const STEPS = ["Fatura", "Conferência", "Perfil", "Análise"];
export const TABS = ["Resumo", "Parcelas", "Projeção", "Plano de reserva", "Converse com a Aura", "Excel"];
export const chipClass = (p) => (p > 70 ? "hi" : p > 50 ? "mid" : "ok");

export const SAMPLE = [
  ["Supermercado", "Alimentação", 482.35, 0, 0], ["iFood", "Alimentação", 167.9, 0, 0], ["Uber", "Transporte", 96.4, 0, 0],
  ["Posto de combustível", "Transporte", 210, 0, 0], ["Streaming", "Assinaturas", 55.9, 0, 0],
  ["Notebook", "Eletrônicos", 389.9, 4, 10], ["Geladeira", "Casa", 312.5, 7, 12], ["Tênis", "Vestuário", 149.9, 2, 5],
  ["Curso online", "Educação", 99.9, 3, 6], ["Farmácia", "Saúde", 134.2, 0, 0], ["Viagem", "Lazer", 275, 1, 8],
].map(([d, c, v, a, t]) => ({ d, c, v, a, t }));


export function Upload({ onFile, onSample, disabled }) {
  const [over, setOver] = useState(false);
  return (
    <>
      <h2>Envie sua fatura</h2>
      <p className="lead">Enviamos o arquivo só para ler os lançamentos. Você confere tudo antes de gerar a análise.</p>
      <div className={`drop ${over ? "over" : ""}`}
           onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
           onDrop={(e) => { e.preventDefault(); setOver(false); e.dataTransfer.files[0] && onFile(e.dataTransfer.files[0]); }}>
        <IconCloud />
        <p>Arraste o PDF ou a foto da fatura aqui</p>
        <label className="btn" style={{ cursor: "pointer" }}>
          Escolher arquivo
          <input type="file" hidden disabled={disabled} accept=".pdf,image/png,image/jpeg,image/webp"
                 onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />
        </label>
      </div>
      <div className="row"><button className="btn ghost" onClick={onSample}>Usar fatura de exemplo</button></div>
    </>
  );
}

export function Review({ items, setItems, back, next }) {
  const set = (n, k, v) => setItems(items.map((it, i) => (i === n ? { ...it, [k]: v } : it)));
  const num = (n, k) => (e) => set(n, k, Number(e.target.value));
  return (
    <>
      <h2>Confira os lançamentos</h2>
      <p className="lead">Corrija o que a leitura errou. Compras à vista ficam com parcela 0 de 0.</p>
      <div className="sheet tw">
        <table>
          <thead><tr><th>Descrição</th><th>Categoria</th><th>Valor</th><th>Parcela</th><th>De</th><th /></tr></thead>
          <tbody>
            {items.map((it, n) => (
              <tr key={it._id ?? n}>
                <td><input type="text" maxLength={80} aria-label="Descrição" value={it.d} onChange={(e) => set(n, "d", e.target.value)} /></td>
                <td><input type="text" maxLength={40} aria-label="Categoria" value={it.c} onChange={(e) => set(n, "c", e.target.value)} /></td>
                <td><input type="number" min="0" step="0.01" aria-label="Valor" value={it.v} onChange={num(n, "v")} /></td>
                <td><input type="number" min="0" aria-label="Parcela atual" value={it.a} onChange={num(n, "a")} /></td>
                <td><input type="number" min="0" aria-label="Total de parcelas" value={it.t} onChange={num(n, "t")} /></td>
                <td><button className="btn ghost" aria-label="Remover lançamento" onClick={() => setItems(items.filter((_, i) => i !== n))}>×</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row">
          <button className="btn ghost" onClick={() => setItems([...items, { d: "", c: "Outros", v: 0, a: 0, t: 0, _id: newItemId() }])}>Adicionar lançamento</button>
        </div>
      </div>
      <div className="row"><button className="btn" disabled={!items.length} onClick={next}>Continuar</button>
        <button className="btn ghost" onClick={back}>Voltar</button></div>
    </>
  );
}

export function Profile({ profile, setProfile, label, setLabel, bank, setBank, back, next, disabled }) {
  const f = (k, label, extra = {}) => (
    <label className="field"><span>{label}</span>
      <input type="number" min="0" {...extra} value={profile[k]} onChange={(e) => setProfile({ ...profile, [k]: Number(e.target.value) })} /></label>
  );
  return (
    <>
      <h2>Seu perfil financeiro</h2>
      <p className="lead">A fatura sozinha não mostra quanto da sua renda está comprometida. Precisamos de três números.</p>
      <div className="sheet fields">
        <label className="field"><span>Nome desta fatura</span><input type="text" maxLength={80} placeholder="Ex.: Fatura de outubro" value={label} onChange={(e) => setLabel(e.target.value)} /></label>
        <label className="field"><span>Banco ou cartão (opcional)</span><input type="text" maxLength={60} value={bank} onChange={(e) => setBank(e.target.value)} /></label>
        {f("renda", "Renda mensal líquida (R$)")}
        {f("fixos", "Gastos fixos: aluguel, contas… (R$)")}
        {f("meta", "Meta de reserva (meses de gastos fixos)", { max: 36 })}
        {f("venc", "Dia do vencimento da fatura", { min: 1, max: 31 })}
      </div>
      <div className="row"><button className="btn" disabled={disabled || profile.renda <= 0} onClick={next}>Gerar análise</button>
        <button className="btn ghost" onClick={back}>Voltar</button></div>
    </>
  );
}

export function Summary({ an, profile }) {
  const fat = an.total, sobra = Math.max(0, profile.renda - profile.fixos - fat);
  const parts = [["Gastos fixos", profile.fixos, "#5a73b8"], ["Fatura", fat, "#f2b84b"], ["Sobra", sobra, "#5fdcc0"]];
  const tot = parts.reduce((s, p) => s + p[1], 0) || 1;
  const nivel = an.pct_comprometido;
  return (
    <>
      <div className="sheet">
        <div className="lead" style={{ margin: 0 }}>Total da fatura</div>
        <div className="total">{brl(an.total)}</div>
        <div className="lead" style={{ margin: 0 }}>{brl(an.parcelado)} parcelado e {brl(an.a_vista)} à vista</div>
        <div className="split" role="img" aria-label="Como sua renda é dividida">
          {parts.map(([n, v, c]) => <i key={n} style={{ flexGrow: v / tot, background: c }}>{v / tot > 0.12 ? `${Math.round((v / tot) * 100)}%` : ""}</i>)}
        </div>
        <div className="legend">{parts.map(([n, v, c]) => <span key={n}><span className="dot" style={{ background: c }} />{n} {brl(v)}</span>)}</div>
        <div className={`note ${nivel > 70 ? "bad" : nivel > 50 ? "warn" : ""}`}>
          {nivel > 70 ? "Mais de 70% da renda está comprometida. Evite criar novas parcelas."
            : nivel > 50 ? "Comprometimento moderado: pouca margem para imprevistos."
            : "Comprometimento saudável. Use a folga para fortalecer a reserva."}
        </div>
      </div>
      <div className="sheet">
        <h3>Gastos por categoria</h3>
        <div className="cat-list">
          {an.categorias.map((c) => {
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
    </>
  );
}

export function Installments({ an }) {
  return (
    <div className="sheet tw">
      <h3>Histórico de parcelas</h3>
      <table>
        <thead><tr><th>Compra</th><th>Parcela</th><th className="n">Valor</th><th className="n">Restam</th><th className="n">Saldo a pagar</th><th>Termina</th></tr></thead>
        <tbody>{an.parcelas.map((p, i) => (
          <tr key={i}><td>{p.compra}</td><td>{p.parcela}</td><td className="n">{brl(p.valor)}</td><td className="n">{p.restam}</td><td className="n">{brl(p.saldo)}</td><td>{p.termina}</td></tr>
        ))}</tbody>
      </table>
      <div className="note">Total ainda a pagar em parcelas futuras: <b>{brl(an.restante_parcelas)}</b></div>
    </div>
  );
}

export function Projection({ an }) {
  if (!an.projecao.length) return null;
  const peak = an.projecao.reduce((m, x) => (x.pct > m.pct ? x : m), an.projecao[0]);
  return (
    <div className="sheet tw">
      <h3>Projeção dos próximos meses</h3>
      <table>
        <thead><tr><th>Mês</th><th className="n">Fatura estimada</th><th className="n">% da renda</th><th className="n">Sobra</th></tr></thead>
        <tbody>{an.projecao.map((x) => (
          <tr key={x.k}><td>{x.mes}{x.k === 0 ? " (atual)" : ""}</td><td className="n"><b>{brl(x.fatura)}</b></td>
            <td className="n"><span className={`chip ${chipClass(x.pct)}`}>{Math.round(x.pct)}%</span></td><td className="n">{brl(x.sobra)}</td></tr>
        ))}</tbody>
      </table>
      <div className="note">Maior comprometimento: <b>{peak.mes}</b> ({Math.round(peak.pct)}% da renda). A estimativa assume gastos à vista iguais aos desta fatura.</div>
    </div>
  );
}

export function Plan({ data, pct, setPct, busy, onGenerate }) {
  const { plan, analysis: an, ai } = data;
  const [open, setOpen] = useState(0);
  const [done, setDone] = useState({});
  const n = Object.values(done).filter(Boolean).length;
  return (
    <div className="sheet">
      <h3>Plano de reserva, passo a passo</h3>
      <p className="lead">{ai ? "Plano gerado pela IA a partir dos seus números." : "Plano padrão por regras. A IA pode adaptá-lo ao seu perfil."}</p>
      <label className="field"><span>Quanto da sobra guardar por mês: <b>{pct}%</b></span>
        <input type="range" min="20" max="100" step="5" disabled={busy} value={pct} onChange={(e) => setPct(Number(e.target.value))} /></label>
      <div className="row"><button className="btn" disabled={busy} onClick={onGenerate}>{ai ? "Gerar novamente com a Aura" : "Gerar plano personalizado com a Aura"}</button></div>
      <div className="note">{plan.diagnostico}</div>
      {plan.proximo_passo && <div className="next"><b>Sua próxima ação:</b> {plan.proximo_passo}</div>}
      {(plan.alertas || []).map((a, i) => <div key={i} className="note warn">{a}</div>)}
      <div className="progress" aria-hidden="true"><i style={{ width: `${(n / plan.passos.length) * 100}%` }} /></div>
      <p className="lead" style={{ margin: "6px 0 0" }}>{n} de {plan.passos.length} passos concluídos</p>
      <ul className="plan">
        {plan.passos.map((p, i) => (
          <li key={i} className={done[i] ? "done" : ""}>
            <div className="plan-head" role="button" tabIndex={0} aria-expanded={open === i}
                 onClick={() => setOpen(open === i ? -1 : i)}
                 onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen(open === i ? -1 : i); } }}>
              <span className="t">{i + 1}. {p.titulo}</span><span className="v">{p.valor}</span>
              <input className="c" type="checkbox" aria-label="Marcar passo como concluído" checked={!!done[i]}
                     onClick={(e) => e.stopPropagation()} onChange={(e) => setDone({ ...done, [i]: e.target.checked })} />
            </div>
            {open === i && <ol>{(p.detalhes || []).map((d, j) => <li key={j}>{d}</li>)}</ol>}
          </li>
        ))}
      </ul>
      {(plan.recomendacoes || []).length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>Recomendações práticas</h3>
          {plan.recomendacoes.map((r, i) => <p key={i} className="rec"><b>{r.titulo}.</b> {r.texto}</p>)}
        </>
      )}
      {plan.incentivo && <p className="note">{plan.incentivo}</p>}
      <h3 style={{ marginTop: 24 }}>Cronograma mês a mês</h3>
      <div className="tw"><table>
        <thead><tr><th>Mês</th><th className="n">Caixinha (parcelas)</th><th className="n">Reserva</th><th className="n">Acumulado</th><th className="n">% da meta</th></tr></thead>
        <tbody>{an.projecao.slice(1).map((x) => (
          <tr key={x.k}><td>{x.mes}</td><td className="n">{brl(x.parcelas)}</td><td className="n">{brl(x.reserva)}</td>
            <td className="n"><b>{brl(x.acumulado)}</b></td><td className="n">{an.meta_reserva ? Math.min(100, Math.round((x.acumulado / an.meta_reserva) * 100)) : 0}%</td></tr>
        ))}</tbody>
      </table></div>
    </div>
  );
}
