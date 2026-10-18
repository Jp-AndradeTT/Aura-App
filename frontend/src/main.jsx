import React from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/bricolage-grotesque/500.css";
import "@fontsource/bricolage-grotesque/700.css";
import "@fontsource/public-sans/400.css";
import "@fontsource/public-sans/500.css";
import "@fontsource/public-sans/600.css";
import App from "./App.jsx";
import "./styles.css";

// Se algo quebrar durante a execução, mostra uma mensagem em vez de tela em branco.
class Boundary extends React.Component {
  state = { err: null };
  static getDerivedStateFromError(err) { return { err }; }
  render() {
    if (!this.state.err) return this.props.children;
    return (
      <div className="auth">
        <div className="brand">Aura</div>
        <h2>Algo deu errado</h2>
        <p className="lead">Recarregue a página (Ctrl+Shift+R). Se continuar, informe este detalhe ao suporte:</p>
        <pre className="codes">{String(this.state.err.message || this.state.err)}</pre>
      </div>
    );
  }
}

createRoot(document.getElementById("root")).render(<Boundary><App /></Boundary>);
