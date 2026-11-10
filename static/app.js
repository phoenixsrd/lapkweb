(() => {
  "use strict";

  // Confirmação antes de enviar formulários marcados com data-confirm.
  document.addEventListener("submit", (e) => {
    const msg = e.target.dataset && e.target.dataset.confirm;
    if (msg && !window.confirm(msg)) e.preventDefault();
  });

  // Botões com data-busy ficam desabilitados e mostram o texto de espera.
  document.addEventListener("submit", (e) => {
    if (e.defaultPrevented) return;
    const botao = e.submitter || e.target.querySelector("button[data-busy]");
    if (!botao || !botao.dataset.busy) return;
    setTimeout(() => {
      botao.dataset.original = botao.textContent;
      botao.textContent = botao.dataset.busy;
      botao.disabled = true;
    }, 0);
  });

  // Ao voltar pelo histórico, a página pode voltar com o botão travado.
  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    document.querySelectorAll("button[data-busy][disabled]").forEach((b) => {
      b.textContent = b.dataset.original || b.textContent;
      b.disabled = false;
    });
  });

  // Busca e filtros da lista (sem JS, a lista aparece completa).
  const barra = document.getElementById("toolbar");
  const lista = document.getElementById("lista");
  if (!barra || !lista) return;
  barra.hidden = false;

  const busca = document.getElementById("busca");
  const chips = barra.querySelectorAll(".chip");
  const vazio = document.getElementById("sem-resultados");
  const cards = Array.from(lista.querySelectorAll(".card"));
  let filtro = "todos";

  const limpar = (s) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().trim();

  function aplicar() {
    const termo = limpar(busca.value);
    let visiveis = 0;
    cards.forEach((card) => {
      const passaFiltro =
        filtro === "todos" ||
        (filtro === "update" && card.dataset.update === "1") ||
        (filtro === "erro" && card.dataset.erro === "1");
      const passaBusca = !termo || limpar(card.dataset.nome || "").includes(termo);
      const mostrar = passaFiltro && passaBusca;
      card.hidden = !mostrar;
      if (mostrar) visiveis++;
    });
    vazio.hidden = visiveis > 0;
  }

  busca.addEventListener("input", aplicar);
  chips.forEach((chip) =>
    chip.addEventListener("click", () => {
      filtro = chip.dataset.filtro;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      aplicar();
    })
  );
})();
