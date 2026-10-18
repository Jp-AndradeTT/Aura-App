import { useEffect, useRef, useState } from "react";
import { chat as sendChat } from "./api";

const GREETING = "Oi! Eu sou a Aura, sua mentora financeira. Já olhei sua fatura e seu plano. O que você quer entender ou decidir?";
const IDEAS = ["Posso fazer uma nova compra parcelada agora?", "Como acelero minha reserva?", "O que muda se eu adiantar uma parcela?", "Onde posso cortar gastos?"];

export default function Chat({ id, messages, setMessages }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [messages, busy]);

  async function send(t) {
    const content = (t ?? text).trim();
    if (!content || busy) return;
    const next = [...messages, { role: "user", content }];
    setMessages(next); setText(""); setError(""); setBusy(true);
    try {
      const r = await sendChat(id, next);
      setMessages([...next, { role: "assistant", content: r.reply }]);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  return (
    <div className="sheet">
      <h3>Converse com a Aura</h3>
      <p className="muted">A Aura é uma inteligência artificial e pode errar: confira os valores antes de decidir. A conversa não fica guardada e some ao fechar a página.</p>
      <div className="chat" aria-live="polite">
        <div className="bubble ai">{GREETING}</div>
        {messages.map((m, i) => <div key={i} className={`bubble ${m.role === "user" ? "me" : "ai"}`}>{m.content}</div>)}
        {busy && <div className="bubble ai muted">A Aura está pensando…</div>}
        <div ref={end} />
      </div>
      {error && <div className="err" role="alert">{error}</div>}
      {!messages.length && <div className="row">{IDEAS.map((q) => <button key={q} className="btn ghost" onClick={() => send(q)}>{q}</button>)}</div>}
      <form className="row" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <input type="text" aria-label="Sua mensagem" placeholder="Pergunte algo sobre sua fatura ou seu plano" maxLength={1000} value={text} onChange={(e) => setText(e.target.value)} style={{ flex: 1, minWidth: 220 }} />
        <button className="btn" disabled={busy || !text.trim()}>Enviar</button>
      </form>
    </div>
  );
}
