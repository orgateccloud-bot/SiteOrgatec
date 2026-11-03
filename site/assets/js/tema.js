/* Gerado por tools/gerar_design_system.py a partir de design-system/orgatec-trilha/tokens.json. Não edite à mão.
   Paletas do design ORGATEC Trilha. Carregue no <head>, depois de orgatec.css: aplica a paleta salva antes da pintura
   (sem piscar) e liga o botão "Cores" (#btnCores) quando a página termina de carregar. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(null);
  else (root.Orgatec = root.Orgatec || {}).tema = factory(root);
})(this, function (win) {
  'use strict';
  var TEMAS = {"verde": {"nome": "Verde Toga", "escuro": false, "flutuante": false, "cores": {"bg": "#F3F5F2", "surface": "#FFFFFF", "surface2": "#E9EEEA", "ink": "#18211E", "muted": "#4F5C56", "line": "#D5DDD8", "brand": "#1F4D40", "brand-ink": "#F3F5F2", "brand-soft": "#DCE7E1", "hl": "#F2C14E", "hl-ink": "#18211E", "hl-soft": "#FBEFC9", "warn": "#9A5212", "warn-soft": "#F6E6D3", "focus": "#2B6CB0"}}, "azul": {"nome": "Azul Tribunal", "escuro": false, "flutuante": false, "cores": {"bg": "#F2F4F7", "surface": "#FFFFFF", "surface2": "#e2e5e8", "ink": "#131A26", "muted": "#636871", "line": "#ced1d6", "brand": "#1D3F6E", "brand-ink": "#F3F5F2", "brand-soft": "#DDE5F0", "hl": "#F5C451", "hl-ink": "#18211E", "hl-soft": "#f3e6c5", "warn": "#A4471C", "warn-soft": "#e6d8d4", "focus": "#2B6CB0"}}, "vinho": {"nome": "Vinho Toga", "escuro": false, "flutuante": false, "cores": {"bg": "#F6F2F2", "surface": "#FFFFFF", "surface2": "#e7e2e3", "ink": "#1E1416", "muted": "#6c6465", "line": "#d3cecf", "brand": "#6B1E2E", "brand-ink": "#F3F5F2", "brand-soft": "#EEDFE2", "hl": "#F0C04A", "hl-ink": "#18211E", "hl-soft": "#f4e3c0", "warn": "#8A5A10", "warn-soft": "#e5dace", "focus": "#2B6CB0"}}, "ciano": {"nome": "Grafite e Ciano", "escuro": false, "flutuante": false, "cores": {"bg": "#F2F5F6", "surface": "#FFFFFF", "surface2": "#e3e6e7", "ink": "#161B1E", "muted": "#65696c", "line": "#cfd2d3", "brand": "#155E6B", "brand-ink": "#F3F5F2", "brand-soft": "#D9ECEF", "hl": "#F4D35E", "hl-ink": "#18211E", "hl-soft": "#f3ebc8", "warn": "#9B4A12", "warn-soft": "#e4dad2", "focus": "#2B6CB0"}}, "noite": {"nome": "Noturno", "escuro": true, "flutuante": false, "cores": {"bg": "#111916", "surface": "#18221E", "surface2": "#1F2B26", "ink": "#E6ECE8", "muted": "#9AA8A1", "line": "#2C3833", "brand": "#8FC7B2", "brand-ink": "#111916", "brand-soft": "#1F3029", "hl": "#F2C14E", "hl-ink": "#18211E", "hl-soft": "#3A3218", "warn": "#E3A961", "warn-soft": "#33281A", "focus": "#7FB3F2"}}, "azul-fl": {"nome": "Azul flutuante", "escuro": false, "flutuante": true, "cores": {"bg": "#EAF1FB", "surface": "#FFFFFF", "surface2": "#dae2ed", "ink": "#0C1A33", "muted": "#5c677b", "line": "#c6cfdb", "brand": "#1D5FD6", "brand-ink": "#F3F5F2", "brand-soft": "#E3ECFB", "hl": "#4B8FE0", "hl-ink": "#06142b", "hl-soft": "#bad4f3", "warn": "#B03A0A", "warn-soft": "#e1d4d4", "focus": "#2B6CB0"}}, "azul-fl-esc": {"nome": "Azul flutuante escuro", "escuro": true, "flutuante": true, "cores": {"bg": "#08111F", "surface": "#171F2C", "surface2": "#1D2737", "ink": "#E6EEFB", "muted": "#969EAC", "line": "#2B3442", "brand": "#6EA8FF", "brand-ink": "#08111F", "brand-soft": "#12233F", "hl": "#9CC3FF", "hl-ink": "#06142B", "hl-soft": "#293850", "warn": "#FF8A4C", "warn-soft": "#302426", "focus": "#9CC3FF"}}};
  var PADRAO = 'azul-fl-esc', AUTO = ["verde", "noite"], CHAVE = 'orgatec.tema';
  var ORDEM = ['auto'].concat(Object.keys(TEMAS));
  function rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255].join(' '); }
  function escuroDoSistema() { return !!(win && win.matchMedia && win.matchMedia('(prefers-color-scheme: dark)').matches); }
  /* 'auto' → Verde Toga ou Noturno, conforme o sistema; id desconhecido → padrão. */
  function resolver(id, escuro) { if (id === 'auto') return escuro ? AUTO[1] : AUTO[0]; return TEMAS[id] ? id : PADRAO; }
  function nome(id) { return id === 'auto' ? 'Automático' : (TEMAS[id] ? TEMAS[id].nome : TEMAS[PADRAO].nome); }
  var atual = PADRAO;

  function aplicar(id) {
    if (!win) return null;
    var doc = win.document, r = doc.documentElement, efetivo = resolver(id, escuroDoSistema()), t = TEMAS[efetivo];
    Object.keys(t.cores).forEach(function (k) { r.style.setProperty('--' + k, t.cores[k]); r.style.setProperty('--' + k + '-rgb', rgb(t.cores[k])); });
    r.style.setProperty('color-scheme', t.escuro ? 'dark' : 'light');
    if (t.flutuante) r.setAttribute('data-float', t.escuro ? 'dark' : 'light'); else r.removeAttribute('data-float');
    r.setAttribute('data-tema', efetivo);
    r.setAttribute('data-escuro', t.escuro ? 'sim' : 'nao');
    atual = TEMAS[id] || id === 'auto' ? id : PADRAO;
    // O símbolo não muda com a paleta: fica sempre com as cores originais (decisão da ORGATEC, 31/10/2026).
    return efetivo;
  }

  function salvo() { try { return win.localStorage.getItem(CHAVE) || PADRAO; } catch (e) { return PADRAO; } }
  function escolher(id) { aplicar(id); try { win.localStorage.setItem(CHAVE, id); } catch (e) {} }

  function montarSeletor() {
    // #btnCores no cabeçalho e, em telas estreitas, o item "Cores" do menu (data-abrir-cores)
    var doc = win.document, botoes = Array.prototype.slice.call(doc.querySelectorAll('#btnCores, [data-abrir-cores]')), btn = botoes[0];
    if (!btn) return;
    var pop = doc.createElement('div');
    pop.id = 'temaPop'; pop.className = 'tema-pop'; pop.hidden = true; pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', 'Escolher cores');
    var toast = doc.createElement('div'); toast.className = 'tema-toast'; toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
    doc.body.appendChild(pop); doc.body.appendChild(toast);
    var tt;
    function desenhar() {
      pop.innerHTML = '<p class="tema-pop-titulo">Cores</p>' + ORDEM.map(function (id) {
        var c = id === 'auto' ? [TEMAS[AUTO[0]].cores, TEMAS[AUTO[1]].cores] : [TEMAS[id].cores];
        var sw = id === 'auto' ? [c[0].brand, c[0].hl, c[0].bg, c[1].bg] : [c[0].brand, c[0].hl, c[0].ink, c[0].bg];
        return '<button type="button" class="tema-opcao" data-tema-id="' + id + '" aria-pressed="' + (id === atual) + '"><span class="tema-sw">' +
          sw.map(function (x) { return '<i style="background:' + x + '"></i>'; }).join('') + '</span>' + nome(id) + '</button>';
      }).join('');
    }
    function fechar() { pop.hidden = true; botoes.forEach(function (b) { b.setAttribute('aria-expanded', 'false'); }); }
    botoes.forEach(function (b) {
      b.setAttribute('aria-controls', 'temaPop'); b.setAttribute('aria-expanded', 'false');
      b.addEventListener('click', function (ev) {
        ev.stopPropagation(); desenhar(); btn = b;
        var r = b.getBoundingClientRect();
        pop.style.top = (r.bottom + 8) + 'px';
        pop.style.right = Math.max(8, doc.documentElement.clientWidth - r.right) + 'px';
        pop.hidden = !pop.hidden; b.setAttribute('aria-expanded', String(!pop.hidden));
      });
    });
    pop.addEventListener('click', function (ev) {
      ev.stopPropagation();  // a lista é redesenhada: sem isso, o clique chega ao documento como "fora" e fecha o seletor
      var o = ev.target.closest('[data-tema-id]'); if (!o) return;
      var id = o.getAttribute('data-tema-id'); escolher(id); desenhar();
      toast.textContent = 'Cores: ' + nome(id); toast.classList.add('on');
      clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove('on'); }, 1800);
    });
    doc.addEventListener('click', function (ev) { if (!pop.hidden && !pop.contains(ev.target) && botoes.indexOf(ev.target) < 0) fechar(); });
    doc.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && !pop.hidden) { fechar(); btn.focus(); } });
  }

  if (win) {
    aplicar(salvo());
    if (win.matchMedia) {
      var mq = win.matchMedia('(prefers-color-scheme: dark)');
      var mudou = function () { if (atual === 'auto') aplicar('auto'); };
      if (mq.addEventListener) mq.addEventListener('change', mudou);
    }
    var pronto = function () { aplicar(atual); montarSeletor(); };
    if (win.document.readyState === 'loading') win.document.addEventListener('DOMContentLoaded', pronto); else pronto();
  }
  return { TEMAS: TEMAS, PADRAO: PADRAO, AUTO: AUTO, ORDEM: ORDEM, resolver: resolver, nome: nome, aplicar: aplicar, escolher: escolher,
    atual: function () { return atual; } };
});
