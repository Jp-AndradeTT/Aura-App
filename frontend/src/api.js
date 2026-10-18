const BASE = import.meta.env.VITE_API_URL || "/api";
let onExpired = () => {};
export const onUnauthorized = (fn) => { onExpired = fn; };

// A sessão fica num cookie HttpOnly (o navegador envia sozinho; o JavaScript não consegue ler).
async function request(path, options = {}) {
  const { timeout = 20000, ...rest } = options;
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeout);
  let res;
  try {
    res = await fetch(BASE + path, { credentials: "same-origin", signal: ctl.signal, ...rest });
  } catch (e) {
    throw new Error(e.name === "AbortError" ? "O servidor demorou demais para responder. Tente novamente." : "Não consegui falar com o servidor. Verifique se o backend está rodando e tente de novo.");
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    let msg = "Algo deu errado. Tente novamente.";
    try { msg = (await res.json()).error || msg; } catch { /* sem JSON */ }
    if (res.status === 401 && !path.startsWith("/auth/") && path !== "/me") onExpired();
    throw new Error(msg);
  }
  return res;
}

// Para respostas 2xx que deveriam ser JSON: se vier corpo vazio/HTML (ex.: proxy/CDN na frente do servidor
// respondendo algo inesperado), devolve um erro amigável em vez do SyntaxError cru do .json() vazando pra tela.
async function requestJson(path, options) {
  const res = await request(path, options);
  try {
    return await res.json();
  } catch {
    throw new Error("Resposta inesperada do servidor. Tente novamente.");
  }
}

const send = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const save = (blob, name) => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
};

export const register = (b) => requestJson("/auth/register", send("POST", b));
export const login = (b) => requestJson("/auth/login", send("POST", b));
export const me = () => requestJson("/me");
export const deleteAccount = (password) => request("/me", send("DELETE", { password }));
export const logout = () => request("/auth/logout", { method: "POST" });
export const logoutAll = () => request("/auth/logout-all", { method: "POST" });
export const forgotPassword = (email) => requestJson("/auth/forgot", send("POST", { email }));
export const resetPassword = (token, password) => requestJson("/auth/reset", send("POST", { token, password }));
export const changePassword = (current_password, new_password) => requestJson("/auth/change-password", send("POST", { current_password, new_password }));
export const exportMyData = async () => save(await (await request("/me/export")).blob(), "meus-dados-aura.json");

export const extractInvoice = (file) => {
  const form = new FormData();
  form.append("file", file);
  return requestJson("/invoices/extract", { method: "POST", body: form, timeout: 120000 });
};
export const listInvoices = () => requestJson("/invoices");
export const getInvoice = (id) => requestJson(`/invoices/${encodeURIComponent(id)}`);
export const createInvoice = (b) => requestJson("/invoices", send("POST", b));
export const updateInvoice = (id, b) => requestJson(`/invoices/${encodeURIComponent(id)}`, send("PUT", b));
export const deleteInvoice = (id) => request(`/invoices/${encodeURIComponent(id)}`, { method: "DELETE" });
export const makePlan = (id, b) => requestJson(`/invoices/${encodeURIComponent(id)}/plan`, { ...send("POST", b), timeout: 120000 });
export const downloadExcel = async (id) => save(await (await request(`/invoices/${encodeURIComponent(id)}/export`)).blob(), "aura-plano-financeiro.xlsx");

export const verifyAccount = (token, password) => requestJson("/auth/verify", send("POST", { token, password }));
export const resendVerification = (email) => requestJson("/auth/resend", send("POST", { email }));
export const loginMfa = (mfa_token, code) => requestJson("/auth/mfa", send("POST", { mfa_token, code }));
export const setup2fa = () => requestJson("/2fa/setup", { method: "POST" });
export const enable2fa = (password, code) => requestJson("/2fa/enable", send("POST", { password, code }));
export const disable2fa = (password, code) => requestJson("/2fa/disable", send("POST", { password, code }));
export const activity = () => requestJson("/me/activity");

export const getConfig = () => requestJson("/config");
export const recoverMfa = (mfa_token) => requestJson("/auth/mfa-recover", send("POST", { mfa_token }));
export const resetMfa = (token, password) => requestJson("/auth/mfa-reset", send("POST", { token, password }));

export const chat = (id, messages) => requestJson(`/invoices/${encodeURIComponent(id)}/chat`, { ...send("POST", { messages }), timeout: 120000 });

export const listReserve = () => requestJson("/reserve");
export const addReserve = (valor, nota) => requestJson("/reserve", send("POST", { valor, nota }));
export const deleteReserve = (id) => requestJson(`/reserve/${encodeURIComponent(id)}`, { method: "DELETE" });

export const adminUsage = () => requestJson("/admin/usage");
