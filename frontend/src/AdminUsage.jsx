import { useEffect, useState } from "react";
import { adminUsage } from "./api";
import { IconBot, IconDoc, IconSpark, IconUsers } from "./Icons";

const KIND_LABEL = { extract: "Leituras de fatura", plan: "Planos gerados", chat: "Mensagens no chat" };

export default function AdminUsage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { adminUsage().then(setData).catch((e) => setError(e.message)); }, []);

  if (error) return <div className="err" role="alert">{error}</div>;
  if (!data) return <p className="lead">Carregando números de uso…</p>;
  const { usuarios: u, faturas: f, ia } = data;

  return (
    <>
      <h2>Painel de uso</h2>
      <p className="lead">Números agregados de todos os mentorados, para acompanhar a adoção e o custo da IA. Nenhum valor, fatura ou dado financeiro de ninguém aparece aqui.</p>
      <div className="sheet">
        <h3>Mentorados</h3>
        <div className="insights">
          <div className="insight-card">
            <div className="ic-head"><IconUsers />Contas criadas</div>
            <div className="ic-val">{u.total}</div>
            <div className="ic-sub">{u.verificados} com e-mail confirmado</div>
          </div>
          <div className="insight-card ok">
            <div className="ic-head"><IconUsers />Ativos nos últimos 30 dias</div>
            <div className="ic-val">{u.ativos_30d}</div>
            <div className="ic-sub">Fizeram login no período</div>
          </div>
          <div className="insight-card">
            <div className="ic-head"><IconUsers />Novos na última semana</div>
            <div className="ic-val">{u.novos_7d}</div>
            <div className="ic-sub">Cadastros nos últimos 7 dias</div>
          </div>
          <div className="insight-card">
            <div className="ic-head"><IconDoc />Faturas analisadas</div>
            <div className="ic-val">{f.total}</div>
            <div className="ic-sub">No total, desde o início</div>
          </div>
        </div>
      </div>
      <div className="sheet">
        <h3>Uso da IA (controle de custo)</h3>
        <p className="lead" style={{ marginBottom: 14 }}>Hoje vs. o limite diário por mentorado, e o total nos últimos 30 dias vs. o teto mensal do app.</p>
        <div className="insights">
          {Object.entries(ia.hoje).map(([kind, n]) => {
            const limite = ia.limites_diarios[kind];
            const pct = limite ? Math.min(100, Math.round((n / limite) * 100)) : 0;
            return (
              <div className={`insight-card ${pct >= 90 ? "warn" : ""}`} key={kind}>
                <div className="ic-head"><IconBot />{KIND_LABEL[kind] || kind}</div>
                <div className="ic-val">{n}</div>
                <div className="ic-sub">Hoje, no app inteiro (limite {limite}/mentorado por dia)</div>
              </div>
            );
          })}
          <div className={`insight-card ${ia.ultimos_30d >= ia.limite_mensal * 0.9 ? "warn" : ""}`}>
            <div className="ic-head"><IconSpark />Total nos últimos 30 dias</div>
            <div className="ic-val">{ia.ultimos_30d}</div>
            <div className="ic-sub">Teto mensal do app: {ia.limite_mensal}</div>
          </div>
        </div>
      </div>
    </>
  );
}
