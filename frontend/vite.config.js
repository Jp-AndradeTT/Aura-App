import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em desenvolvimento, /api é encaminhado ao Flask (porta 5000).
export default defineConfig({
  plugins: [react()],
  // changeOrigin: false mantém o endereço original (localhost:5173) nos pedidos; o Flask confere a origem por ele.
  server: { proxy: { "/api": { target: "http://127.0.0.1:5000", changeOrigin: false } } },
});
