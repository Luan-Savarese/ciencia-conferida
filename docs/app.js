/* Ciência Conferida: melhorias opcionais (salvar, compartilhar, busca, filtros, curiosidade do dia).
   O site inteiro funciona sem este arquivo; aqui só entra o que precisa de JavaScript. Sem cookies, sem rastreio. */
(function () {
  "use strict";
  var BASE = document.currentScript ? new URL(".", document.currentScript.src).href : location.href;
  var CHAVE = "cc:salvos";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function lerSalvos() {
    try { var v = JSON.parse(localStorage.getItem(CHAVE) || "[]"); return Array.isArray(v) ? v : []; } catch (e) { return []; }
  }
  function gravarSalvos(l) { try { localStorage.setItem(CHAVE, JSON.stringify(l)); } catch (e) { /* sem armazenamento: tudo bem */ } }
  function aviso(txt) {
    var a = $("#aviso");
    if (!a) return;
    a.textContent = txt;
    clearTimeout(aviso.t);
    aviso.t = setTimeout(function () { a.textContent = ""; }, 3500);
  }
  function norm(s) { return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function dataBR(iso) { var p = iso.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; }

  /* contador de salvos no menu e botões de salvar */
  function atualizaContador() {
    var n = lerSalvos().length, c = $("#cont-salvos");
    if (c) { c.textContent = n; c.hidden = n === 0; }
  }
  function iniciaSalvar() {
    var salvos = lerSalvos();
    $$(".salvar").forEach(function (b) {
      var slug = b.getAttribute("data-slug"), rot = $("span", b);
      b.hidden = false;
      function pinta() {
        var s = lerSalvos().indexOf(slug) >= 0;
        b.setAttribute("aria-pressed", s ? "true" : "false");
        if (rot) rot.textContent = s ? "Salvo" : "Salvar";
        b.setAttribute("aria-label", (s ? "Remover dos salvos: " : "Salvar: ") + (b.getAttribute("data-titulo") || ""));
      }
      pinta();
      b.addEventListener("click", function () {
        var l = lerSalvos(), i = l.indexOf(slug);
        if (i >= 0) l.splice(i, 1); else l.push(slug);
        gravarSalvos(l); pinta(); atualizaContador();
        aviso(i >= 0 ? "Removido dos salvos." : "Salvo neste navegador. Veja em Salvos, no menu.");
      });
    });
    atualizaContador();
    return salvos;
  }

  function iniciaCompartilhar() {
    $$(".compartilhar").forEach(function (b) {
      var url = b.getAttribute("data-url"), titulo = b.getAttribute("data-titulo");
      if (!navigator.share && !(navigator.clipboard && navigator.clipboard.writeText)) return;
      b.hidden = false;
      b.addEventListener("click", function () {
        if (navigator.share) {
          navigator.share({ title: titulo, url: url }).catch(function () { /* a pessoa cancelou */ });
        } else {
          navigator.clipboard.writeText(url).then(function () { aviso("Link copiado."); }, function () { aviso("Não deu para copiar. Copie o endereço da barra do navegador."); });
        }
      });
    });
  }

  /* curiosidade do dia: mesma conta do gerador (dias desde 1970 pela data local) */
  function iniciaDia() {
    var caixa = $("#dia"), dados = $("#dados-curiosidades");
    if (!caixa || !dados) return;
    try {
      var lista = JSON.parse(dados.textContent), h = new Date();
      if (!lista.length) return;
      var dias = Math.floor(Date.UTC(h.getFullYear(), h.getMonth(), h.getDate()) / 864e5);
      var c = lista[dias % lista.length];
      $("#dia-texto", caixa).innerHTML = c.html;
      $("#dia-rodape", caixa).innerHTML = c.rodape; /* HTML já escapado pelo gerador */
    } catch (e) { /* mantém a curiosidade que veio pronta */ }
  }

  /* filtros da lista de artigos na página inicial */
  function iniciaFiltros() {
    var barra = $("#filtros"), lista = $("#todos");
    if (!barra || !lista) return;
    barra.hidden = false;
    var cards = $$(".card", lista), vazio = $("#sem-resultado");
    var f = { tema: "", nivel: "" };
    function aplica() {
      var n = 0;
      cards.forEach(function (c) {
        var ok = (!f.tema || c.getAttribute("data-tema") === f.tema) && (!f.nivel || c.getAttribute("data-nivel") === f.nivel);
        c.hidden = !ok; if (ok) n++;
      });
      if (vazio) vazio.hidden = n > 0;
    }
    $$("button", barra).forEach(function (b) {
      b.addEventListener("click", function () {
        var tipo = b.getAttribute("data-tipo"), v = b.getAttribute("data-valor");
        f[tipo] = (f[tipo] === v) ? "" : v;
        $$("button[data-tipo=" + tipo + "]", barra).forEach(function (x) { x.setAttribute("aria-pressed", x.getAttribute("data-valor") === f[tipo] ? "true" : "false"); });
        aplica();
      });
    });
  }

  function carregaIndice() {
    return fetch(new URL("indice.json", BASE).href).then(function (r) { return r.json(); });
  }

  /* página de busca */
  function iniciaBusca() {
    var app = $("#busca-app");
    if (!app) return;
    var campo = $("#q", app), selNivel = $("#nivel", app), chips = $$("button[data-tema]", app), saida = $("#resultados", app), contagem = $("#contagem", app);
    var dados = null, temaAtivo = "";
    var params = new URLSearchParams(location.search);
    campo.value = params.get("q") || ""; temaAtivo = params.get("tema") || ""; selNivel.value = params.get("nivel") || "";

    function itens() {
      var out = [];
      dados.artigos.forEach(function (a) { out.push({ tipo: "Artigo", a: a, texto: norm([a.titulo, a.resumo, a.tema, a.nivel_nome].concat(a.curiosidades).join(" ")), titulo: norm(a.titulo) }); });
      dados.noticias.forEach(function (n) { out.push({ tipo: "Notícia", a: n, texto: norm([n.titulo, n.resumo, n.tema, n.fonte].join(" ")), titulo: norm(n.titulo) }); });
      return out;
    }
    function pinta() {
      var q = norm(campo.value).trim(), toks = q ? q.split(/\s+/) : [], nivel = selNivel.value, res = [];
      itens().forEach(function (it) {
        var a = it.a;
        if (temaAtivo && a.tema_slug !== temaAtivo) return;
        if (nivel && (it.tipo !== "Artigo" || a.nivel !== nivel)) return;
        var pts = 0, ok = true;
        toks.forEach(function (t) {
          if (it.titulo.indexOf(t) >= 0) pts += 5; else if (it.texto.indexOf(t) >= 0) pts += 2; else ok = false;
        });
        if (ok) res.push({ it: it, pts: pts });
      });
      res.sort(function (x, y) { return y.pts - x.pts || (y.it.a.data > x.it.a.data ? 1 : -1); });
      saida.textContent = "";
      res.forEach(function (r) {
        var a = r.it.a, art = r.it.tipo === "Artigo", d = el("div", "res t-" + a.tema_slug);
        var tags = el("div"); tags.appendChild(el("span", "chip", a.tema)); tags.appendChild(document.createTextNode(" "));
        var tp = el("span", "chip nv", r.it.tipo); tags.appendChild(tp); d.appendChild(tags);
        var h = el("h3"), l = el("a", "", a.titulo);
        l.href = art ? new URL(a.url, BASE).href : a.url; if (!art) l.rel = "noopener"; h.appendChild(l); d.appendChild(h);
        d.appendChild(el("p", "", a.resumo));
        if (art) {
          var ach = a.curiosidades.filter(function (c) { return toks.length && toks.every(function (t) { return norm(c).indexOf(t) >= 0; }); })[0];
          if (ach) d.appendChild(el("p", "achou", "Curiosidade: " + ach));
          d.appendChild(el("p", "meta", a.nivel_nome + " · " + a.min + " min de leitura · conferido em " + dataBR(a.conf)));
        } else {
          d.appendChild(el("p", "meta", "Fonte: " + a.fonte + " · publicada em " + dataBR(a.data)));
        }
        saida.appendChild(d);
      });
      contagem.textContent = res.length === 0 ? "Nada encontrado. Tente outra palavra ou tire um filtro." : res.length + (res.length === 1 ? " resultado" : " resultados");
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.getAttribute("data-tema") === temaAtivo ? "true" : "false"); });
      var np = new URLSearchParams();
      if (campo.value) np.set("q", campo.value); if (temaAtivo) np.set("tema", temaAtivo); if (nivel) np.set("nivel", nivel);
      try { history.replaceState(null, "", location.pathname + (np.toString() ? "?" + np : "")); } catch (e) { /* ok */ }
    }
    chips.forEach(function (c) { c.addEventListener("click", function () { var v = c.getAttribute("data-tema"); temaAtivo = temaAtivo === v ? "" : v; pinta(); }); });
    campo.addEventListener("input", pinta); selNivel.addEventListener("change", pinta);
    $("form", app).addEventListener("submit", function (e) { e.preventDefault(); pinta(); });
    carregaIndice().then(function (d) { dados = d; app.removeAttribute("aria-busy"); pinta(); }, function () {
      contagem.textContent = "Não foi possível carregar a busca agora. Use os temas no menu.";
    });
  }

  /* página de salvos */
  function iniciaPaginaSalvos() {
    var app = $("#salvos-app");
    if (!app) return;
    var saida = $("#salvos-lista", app), msg = $("#salvos-msg", app);
    carregaIndice().then(function (d) {
      function pinta() {
        var salvos = lerSalvos(), arts = d.artigos.filter(function (a) { return salvos.indexOf(a.slug) >= 0; });
        saida.textContent = "";
        msg.textContent = arts.length ? "" : "Você ainda não salvou nada. Use o botão Salvar nos artigos: ele guarda a lista só neste navegador.";
        arts.forEach(function (a) {
          var c = el("div", "res t-" + a.tema_slug), tg = el("div"); tg.appendChild(el("span", "chip", a.tema));
          c.appendChild(tg);
          var h = el("h3"), l = el("a", "", a.titulo); l.href = new URL(a.url, BASE).href; h.appendChild(l); c.appendChild(h);
          c.appendChild(el("p", "", a.resumo));
          var rm = el("button", "mini rm", "Remover dos salvos");
          rm.addEventListener("click", function () { gravarSalvos(lerSalvos().filter(function (s) { return s !== a.slug; })); atualizaContador(); pinta(); });
          c.appendChild(rm); saida.appendChild(c);
        });
      }
      pinta();
    }, function () { msg.textContent = "Não foi possível carregar seus salvos agora."; });
  }

  iniciaSalvar(); iniciaCompartilhar(); iniciaDia(); iniciaFiltros(); iniciaBusca(); iniciaPaginaSalvos();
})();
