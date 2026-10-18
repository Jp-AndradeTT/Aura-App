(function () {
  var problems = [];
  window.addEventListener("error", function (e) {
    problems.push(e.target && e.target.src ? "arquivo não carregou: " + e.target.src : e.message || "erro");
  }, true);
  window.addEventListener("unhandledrejection", function (e) { problems.push(String(e.reason)); });
  setTimeout(function () {
    var root = document.getElementById("root");
    if (!root || root.firstChild) return;
    var box = document.createElement("div");
    box.style.cssText = "font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:48px auto;padding:0 16px";
    var h = document.createElement("h2"); h.textContent = "O Aura não conseguiu carregar";
    var p = document.createElement("p"); p.textContent = "Tente Ctrl+Shift+R. Se continuar, abra o console do navegador (F12 > Console) e envie o erro em vermelho ao suporte.";
    var pre = document.createElement("pre"); pre.textContent = problems.join("\n") || "(sem detalhes)"; pre.style.whiteSpace = "pre-wrap";
    box.appendChild(h); box.appendChild(p); box.appendChild(pre); root.appendChild(box);
  }, 4000);
})();
