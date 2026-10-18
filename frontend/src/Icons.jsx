const base = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true };
export const IconGrid = () => <svg {...base}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>;
export const IconUpload = () => <svg {...base}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /><path d="M12 18v-6M9.5 14.5 12 12l2.5 2.5" /></svg>;
export const IconUser = () => <svg {...base}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" /></svg>;
export const IconShield = () => <svg {...base}><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="m9 12 2 2 4-4" /></svg>;
export const IconDoc = () => <svg {...base}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></svg>;
export const IconOut = () => <svg {...base}><path d="M9 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></svg>;
export const IconListCheck = () => <svg {...base}><path d="m4 7 1.6 1.6L9 5" /><path d="M13 6.5h7" /><path d="m4 15 1.6 1.6L9 13" /><path d="M13 14.5h7" /></svg>;
export const IconChartUp = () => <svg {...base}><path d="M4 20V10M11 20V4M18 20v-7" /><path d="M3 20h18" /></svg>;
export const IconCloud = () => <svg {...base} width="34" height="34" strokeWidth="1.5"><path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 8.5a4.75 4.75 0 0 1-.5 9.5z" /><path d="M12 17v-6M9.5 13.5 12 11l2.5 2.5" /></svg>;

// ---------- ícones dos cartões de insight ----------
const ic = { width: 17, height: 17, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true };
export const IconGauge = () => <svg {...ic}><path d="M4 16a8 8 0 1 1 16 0" /><path d="M12 16 16 9" /><circle cx="12" cy="16" r="1.4" /></svg>;
export const IconPiggy = () => <svg {...ic}><path d="M4 12c0-3.3 3.1-6 7.5-6 3.2 0 4.8 1.1 5.8 2.3L20 8v4l-2 .6c-.3 1-1 1.9-2 2.5V18h-2.3v-1.6a9 9 0 0 1-2.2.3c-1 0-1.9-.1-2.7-.4L8.5 18H6v-2.4C4.8 14.7 4 13.5 4 12Z" /><circle cx="9.5" cy="10.5" r=".9" fill="currentColor" stroke="none" /></svg>;
export const IconWallet = () => <svg {...ic}><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M3 10h18" /><path d="M16 14h2" /><path d="M7 7V5a2 2 0 0 1 2-2h7" /></svg>;
export const IconCalendarDown = () => <svg {...ic}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /><path d="M12 13v5m0 0 2.2-2.2M12 18l-2.2-2.2" /></svg>;
export const IconSpark = () => <svg {...ic}><path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" /><circle cx="12" cy="12" r="3.2" /></svg>;
export const IconUsers = () => <svg {...ic}><circle cx="9" cy="8" r="3.2" /><path d="M2.8 19c0-3.3 2.8-5.2 6.2-5.2s6.2 1.9 6.2 5.2" /><path d="M16.5 5a3.1 3.1 0 0 1 0 6" /><path d="M17 13.9c2.6.4 4.2 2.1 4.2 5.1" /></svg>;
export const IconBot = () => <svg {...ic}><rect x="4" y="9" width="16" height="10" rx="2.5" /><path d="M12 9V5M9.5 3.5h5" /><circle cx="9" cy="14" r="1.1" fill="currentColor" stroke="none" /><circle cx="15" cy="14" r="1.1" fill="currentColor" stroke="none" /></svg>;

// ---------- ícones de categoria de gasto ----------
const cat = { width: 17, height: 17, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true };
const CAT_ICONS = {
  "alimentação": () => <svg {...cat}><path d="M7 3v7a2 2 0 0 0 4 0V3M9 10v11M17 3c-1.7 1.4-2 3-2 5s.5 3 2 3v10" /></svg>,
  "transporte": () => <svg {...cat}><rect x="3" y="10" width="18" height="7" rx="2" /><path d="M5 10 7 5h10l2 5" /><circle cx="7.5" cy="17.5" r="1.6" /><circle cx="16.5" cy="17.5" r="1.6" /></svg>,
  "assinaturas": () => <svg {...cat}><path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3" /><path d="M18 3v4h-4M6 21v-4h4" /></svg>,
  "casa": () => <svg {...cat}><path d="M4 11.5 12 4l8 7.5" /><path d="M6 10v9a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-9" /><path d="M10 20v-5h4v5" /></svg>,
  "saúde": () => <svg {...cat}><path d="M12 21s-7.5-4.6-9.8-9.1C.7 8.4 2.3 5 5.8 5c1.9 0 3.4 1 4.2 2.4C10.8 6 12.3 5 14.2 5c3.5 0 5.1 3.4 3.6 6.9C15.5 16.4 12 21 12 21Z" /></svg>,
  "educação": () => <svg {...cat}><path d="M2 7 12 3l10 4-10 4Z" /><path d="M6 9.5V15c0 1.5 2.7 3 6 3s6-1.5 6-3V9.5" /><path d="M22 7v6" /></svg>,
  "lazer": () => <svg {...cat}><path d="M12 3l2.6 5.8 6.4.6-4.8 4.3 1.4 6.3L12 16.8 6.4 20l1.4-6.3-4.8-4.3 6.4-.6Z" /></svg>,
  "vestuário": () => <svg {...cat}><path d="M9 4 7 6 3 8l2 3 2-1v10h10V10l2 1 2-3-4-2-2-2" /><path d="M9 4a3 3 0 0 0 6 0" /></svg>,
  "eletrônicos": () => <svg {...cat}><rect x="4" y="4" width="16" height="11" rx="1.5" /><path d="M8 19h8M12 15v4" /></svg>,
  "serviços": () => <svg {...cat}><path d="M14.7 6.3a4 4 0 0 1-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 1 5.4-5.4L21 6l-3-3z" /></svg>,
  "outros": () => <svg {...cat}><path d="M12 2 2 9l10 13 10-13z" /><circle cx="12" cy="9" r="2" /></svg>,
};
const CAT_COLORS = {
  "alimentação": "#ff9a8b", "transporte": "#8fb4ff", "assinaturas": "#c9a6ff", "casa": "#f2b84b", "saúde": "#ff9ac0",
  "educação": "#6fd1e0", "lazer": "#5fdcc0", "vestuário": "#ffb877", "eletrônicos": "#7c93e0", "serviços": "#9db0d9", "outros": "#9db0d9",
};
const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
const KEY_BY_NORM = Object.fromEntries(Object.keys(CAT_ICONS).map((k) => [norm(k), k]));

export function categoryColor(name) {
  return CAT_COLORS[KEY_BY_NORM[norm(name)]] || "#9db0d9";
}

export function CategoryIcon({ name, size = 30 }) {
  const key = KEY_BY_NORM[norm(name)] || "outros";
  const color = CAT_COLORS[key];
  const Icon = CAT_ICONS[key];
  return (
    <span className="cat-ic" style={{ width: size, height: size, color, background: `${color}26` }}>
      <Icon />
    </span>
  );
}

// Marca: anel dourado com uma linha de crescimento.
export const Logo = ({ size = 34 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
    <circle cx="20" cy="20" r="17" fill="rgba(242,184,75,.12)" stroke="#f2b84b" strokeWidth="2.4" />
    <path d="M10.5 25.5 16 19l4.5 4 8.5-10.5" fill="none" stroke="#f2b84b" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="29" cy="12.5" r="2.4" fill="#ffe3a3" />
  </svg>
);
