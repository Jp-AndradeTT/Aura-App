import { useEffect, useRef, useState } from "react";
import { extractInvoice, createInvoice, updateInvoice, makePlan, downloadExcel } from "./api";
import Chat from "./Chat";
import { STEPS, TABS, SAMPLE, Upload, Review, Profile, Summary, Installments, Projection, Plan, withIds } from "./parts";

const MAX_FILE_MB = 10;

export default function Flow({ initial, onDone }) {
  const [step, setStep] = useState(initial ? 3 : 0);
  const [id, setId] = useState(initial?.id || null);
  const [items, setItems] = useState(() => withIds(initial?.items || []));
  const [profile, setProfile] = useState(initial?.profile || { renda: 6500, fixos: 3200, meta: 6, venc: 10 });
  const [label, setLabel] = useState(initial?.label || "");
  const [bank, setBank] = useState(initial?.bank || "");
  const [pct, setPct] = useState(initial?.reserve_pct || 60);
  const [data, setData] = useState(initial || null);
  const [tab, setTab] = useState(0);
  const [chat, setChat] = useState([]); // conversa só na memória do navegador
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const reqSeq = useRef(0); // sequência da última chamada de plano iniciada: uma resposta antiga nunca sobrescreve uma mais nova

  async function run(text, fn) {
    setBusy(text); setError("");
    try { return await fn(); } catch (e) { setError(e.message); return null; } finally { setBusy(""); }
  }

  async function onFile(file) {
    if (file.size > MAX_FILE_MB * 1024 * 1024) { setError(`O arquivo passa de ${MAX_FILE_MB} MB. Envie o PDF ou uma foto menor.`); return; }
    if (!["application/pdf", "image/png", "image/jpeg", "image/webp"].includes(file.type)) { setError("Envie um PDF, PNG, JPG ou WEBP."); return; }
    const r = await run("Lendo a fatura com IA…", () => extractInvoice(file));
    if (!r) return;
    setItems(withIds(r.items));
    if (r.banco) setBank(r.banco);
    if (r.vencimento_dia) setProfile((p) => ({ ...p, venc: r.vencimento_dia }));
    setStep(1);
  }

  async function analyze() {
    const body = { label, bank, items, profile, reserve_pct: pct };
    const r = await run("Salvando e calculando…", () => (id ? updateInvoice(id, body) : createInvoice(body)));
    if (r) { setId(r.id); setData(r); setLabel(r.label); setTab(0); setStep(3); }
  }

  async function generate() {
    const seq = ++reqSeq.current;
    const r = await run("A Aura está montando seu plano…", () => makePlan(id, { use_ai: true, reserve_pct: pct }));
    if (!r || seq !== reqSeq.current) return; // uma mudança no slider enquanto isso rodava já pediu algo mais novo
    setData(r);
    if (!r.ai) setError("Não consegui gerar com a IA agora. Mantive o plano padrão.");
  }

  // Mexeu no percentual da reserva: recalcula e salva (plano padrão).
  useEffect(() => {
    if (!data || data.reserve_pct === pct) return;
    const t = setTimeout(async () => {
      const seq = ++reqSeq.current;
      const r = await run("Recalculando…", () => makePlan(id, { use_ai: false, reserve_pct: pct }));
      if (r && seq === reqSeq.current) setData(r);
    }, 400);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pct]);

  return (
    <>
      <ol className="steps flow-steps">
        {STEPS.map((s, i) => (
          <li key={s} className={i === step ? "on" : i < step ? "past" : ""}><b>{i < step ? "✓" : i + 1}</b><span>{s}</span></li>
        ))}
      </ol>
      {error && <div className="err" role="alert">{error}</div>}
      {busy && <div className="busy" role="status">{busy}</div>}

      {step === 0 && <Upload onFile={onFile} disabled={!!busy} onSample={() => { setItems(withIds(SAMPLE)); setStep(1); }} />}
      {step === 1 && <Review items={items} setItems={setItems} back={() => setStep(0)} next={() => setStep(2)} />}
      {step === 2 && <Profile profile={profile} setProfile={setProfile} label={label} setLabel={setLabel} bank={bank} setBank={setBank}
                              back={() => setStep(1)} next={analyze} disabled={!!busy} />}
      {step === 3 && data && (
        <>
          <h2>{data.label}</h2>
          <p className="lead">Os números são calculados pelo sistema e salvos no seu histórico. A IA só escreve o plano.</p>
          <div className="tabs" role="tablist">
            {TABS.map((t, i) => <button key={t} role="tab" aria-selected={tab === i} onClick={() => setTab(i)}>{t}</button>)}
          </div>
          {tab === 0 && <Summary an={data.analysis} profile={data.profile} />}
          {tab === 1 && <Installments an={data.analysis} />}
          {tab === 2 && <Projection an={data.analysis} />}
          {tab === 3 && <Plan key={id} data={data} pct={pct} setPct={setPct} busy={!!busy} onGenerate={generate} />}
          {tab === 4 && <Chat id={id} messages={chat} setMessages={setChat} />}
          {tab === 5 && (
            <div className="sheet">
              <h3>Dados para o Excel</h3>
              <p className="lead">Planilha com 8 abas: resumo, lançamentos, categorias, parcelas, parcelas por mês, projeção, plano de ação e evolução das suas faturas.</p>
              <button className="btn" disabled={!!busy} onClick={() => run("Gerando planilha…", () => downloadExcel(id))}>Baixar planilha (.xlsx)</button>
            </div>
          )}
          <p className="muted">Orientação educativa gerada com apoio de IA. Confira os valores antes de decidir; não é recomendação de investimento nem substitui um profissional.</p>
          <div className="row">
            <button className="btn ghost" onClick={() => setStep(2)}>Corrigir dados desta fatura</button>
            <button className="btn ghost" onClick={onDone}>Voltar ao painel</button>
          </div>
        </>
      )}
    </>
  );
}
