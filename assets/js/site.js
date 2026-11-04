// S&P Engenharia e Construção — menu, abertura, contadores, portfólio e pedido de orçamento
(function () {
  "use strict";

  var WHATSAPP = "5551984471009";
  var EMAIL = "contato@spconstrutora.com";
  var semMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var ano = document.getElementById("ano");
  if (ano) ano.textContent = new Date().getFullYear();

  // ----- menu no celular -----
  var hamb = document.querySelector(".topo__hamb");
  var menu = document.getElementById("menu");
  function fecharMenu() {
    menu.classList.remove("aberto");
    hamb.setAttribute("aria-expanded", "false");
    hamb.setAttribute("aria-label", "Abrir menu");
    aoRolar();
  }
  hamb.addEventListener("click", function () {
    var abrir = !menu.classList.contains("aberto");
    menu.classList.toggle("aberto", abrir);
    hamb.setAttribute("aria-expanded", String(abrir));
    hamb.setAttribute("aria-label", abrir ? "Fechar menu" : "Abrir menu");
    aoRolar();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && menu.classList.contains("aberto")) { fecharMenu(); hamb.focus(); }
  });

  // ----- ao rolar: cabeçalho sólido, abertura sumindo e botão de voltar ao topo -----
  var topo = document.getElementById("topo");
  var capa = document.getElementById("capa");
  var subir = document.querySelector(".subir");
  function aoRolar() {
    var y = window.scrollY;
    topo.classList.toggle("solido", y > 60 || menu.classList.contains("aberto"));
    document.body.classList.toggle("rolou", y > 60);
    subir.hidden = y < 600;
    if (capa && !semMovimento) capa.style.setProperty("--r", Math.min(y / capa.offsetHeight, 1).toFixed(3));
  }
  window.addEventListener("scroll", aoRolar, { passive: true });
  aoRolar();

  // ----- entrada ao rolar e contadores -----
  function contar(el) {
    var alvo = Number(el.dataset.contar);
    if (semMovimento) { el.textContent = alvo; return; }
    var inicio = null;
    var de = alvo > 1000 ? alvo - 60 : 0;
    function passo(t) {
      if (inicio === null) inicio = t;
      var p = Math.min((t - inicio) / 1600, 1);
      el.textContent = Math.round(de + (alvo - de) * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(passo);
    }
    requestAnimationFrame(passo);
  }
  if ("IntersectionObserver" in window) {
    var visor = new IntersectionObserver(function (itens) {
      itens.forEach(function (item) {
        if (!item.isIntersecting) return;
        var el = item.target;
        if (el.dataset.contar) contar(el); else el.classList.add("visivel");
        visor.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    document.querySelectorAll(".revelar, [data-contar]").forEach(function (el) { visor.observe(el); });
  } else {
    document.querySelectorAll(".revelar").forEach(function (el) { el.classList.add("visivel"); });
  }

  // ----- portfólio: filtro por cliente -----
  var filtros = document.querySelectorAll(".filtro");
  filtros.forEach(function (botao) {
    botao.addEventListener("click", function () {
      filtros.forEach(function (b) { b.classList.toggle("ativo", b === botao); });
      document.querySelectorAll("[data-galeria] .pf-item").forEach(function (item) {
        item.hidden = botao.dataset.filtro !== "todos" && item.dataset.cliente !== botao.dataset.filtro;
        item.classList.add("visivel");
      });
    });
  });

  // ----- portfólio: foto ampliada -----
  var luz = document.getElementById("luz");
  var luzImg = document.getElementById("luz-img");
  var luzLegenda = document.getElementById("luz-legenda");
  var luzConta = document.getElementById("luz-conta");
  var fila = [];
  var atual = 0;

  function mostrar(i) {
    atual = (i + fila.length) % fila.length;
    var a = fila[atual];
    luzImg.src = a.href;
    luzImg.width = a.dataset.w;
    luzImg.height = a.dataset.h;
    luzImg.alt = a.querySelector("img").alt;
    luzLegenda.textContent = a.dataset.legenda;
    luzConta.textContent = (atual + 1) + " / " + fila.length;
    if (fila.length > 1) new Image().src = fila[(atual + 1) % fila.length].href;
  }
  document.querySelectorAll("[data-galeria]").forEach(function (galeria) {
    galeria.addEventListener("click", function (e) {
      var a = e.target.closest(".pf-item");
      if (!a) return;
      e.preventDefault();
      fila = Array.prototype.slice.call(galeria.querySelectorAll(".pf-item:not([hidden])"));
      mostrar(fila.indexOf(a));
      luz.showModal();
    });
  });
  luz.addEventListener("click", function (e) {
    var b = e.target.closest("[data-acao]");
    if (b) {
      if (b.dataset.acao === "fechar") luz.close();
      if (b.dataset.acao === "anterior") mostrar(atual - 1);
      if (b.dataset.acao === "proxima") mostrar(atual + 1);
    } else if (e.target === luz || e.target.tagName === "FIGURE") {
      luz.close();
    }
  });
  luz.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") mostrar(atual - 1);
    if (e.key === "ArrowRight") mostrar(atual + 1);
  });
  luz.addEventListener("close", function () {
    luzImg.removeAttribute("src");
    if (fila[atual]) fila[atual].focus();
  });
  var toqueLuz = null;
  luz.addEventListener("touchstart", function (e) { toqueLuz = e.touches[0].clientX; }, { passive: true });
  luz.addEventListener("touchend", function (e) {
    if (toqueLuz === null) return;
    var dx = e.changedTouches[0].clientX - toqueLuz;
    if (Math.abs(dx) > 50) mostrar(atual + (dx < 0 ? 1 : -1));
    toqueLuz = null;
  }, { passive: true });

  // ----- pedido de orçamento -----
  var form = document.getElementById("form-orcamento");
  if (form) {
    var erro = document.getElementById("form-erro");
    var linkEmail = document.getElementById("link-email");

    function montarMensagem() {
      var d = new FormData(form);
      var nome = (d.get("nome") || "").trim();
      var empresa = (d.get("empresa") || "").trim();
      var msg = (d.get("mensagem") || "").trim();
      if (!nome || !msg) return null;
      return "Olá! Sou " + nome + (empresa ? ", da " + empresa : "") + ".\n" +
        "Serviço: " + d.get("servico") + "\n\n" + msg;
    }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var texto = montarMensagem();
      erro.hidden = Boolean(texto);
      if (!texto) {
        (form.nome.value.trim() ? form.mensagem : form.nome).focus();
        return;
      }
      window.open("https://wa.me/" + WHATSAPP + "?text=" + encodeURIComponent(texto), "_blank", "noopener");
    });
    linkEmail.addEventListener("click", function () {
      var texto = montarMensagem();
      linkEmail.href = "mailto:" + EMAIL + "?subject=" + encodeURIComponent("Pedido de orçamento") +
        (texto ? "&body=" + encodeURIComponent(texto) : "");
    });
  }
})();
