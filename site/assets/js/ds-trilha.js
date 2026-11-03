/* Gerado junto com a página. Não edite à mão. */
(function () {
  'use strict';
  var PRESETS = [{"id": "auto", "name": "Automático"}, {"id": "verde", "p": "#1F4D40", "h": "#F2C14E", "ink": "#18211E", "a": "#9A5212", "s": "#DCE7E1", "bg": "#F3F5F2", "name": "Verde Toga"}, {"id": "azul", "p": "#1D3F6E", "h": "#F5C451", "ink": "#131A26", "a": "#A4471C", "s": "#DDE5F0", "bg": "#F2F4F7", "name": "Azul Tribunal"}, {"id": "vinho", "p": "#6B1E2E", "h": "#F0C04A", "ink": "#1E1416", "a": "#8A5A10", "s": "#EEDFE2", "bg": "#F6F2F2", "name": "Vinho Toga"}, {"id": "ciano", "p": "#155E6B", "h": "#F4D35E", "ink": "#161B1E", "a": "#9B4A12", "s": "#D9ECEF", "bg": "#F2F5F6", "name": "Grafite e Ciano"}, {"id": "noite", "p": "#8FC7B2", "h": "#F2C14E", "ink": "#E6ECE8", "a": "#E3A961", "s": "#22322C", "bg": "#111916", "name": "Noturno"}, {"id": "azul-fl", "p": "#1D5FD6", "h": "#4B8FE0", "ink": "#0C1A33", "a": "#B03A0A", "s": "#E3ECFB", "bg": "#EAF1FB", "fl": 1, "name": "Azul flutuante"}, {"id": "azul-fl-esc", "p": "#6EA8FF", "h": "#9CC3FF", "ink": "#E6EEFB", "a": "#FF8A4C", "s": "#12233F", "bg": "#08111F", "fl": 1, "name": "Azul flutuante escuro"}];
  var USOS = {"bg": "Fundo da página.", "surface": "Cartões.", "surface2": "Áreas internas de cartões.", "ink": "Texto principal, sobre bg e surface (contraste ≥ 4,5:1).", "muted": "Texto secundário e legendas, sobre bg e surface.", "line": "Bordas de 1 px.", "brand": "Títulos, links, aba ativa, bloco de teoria.", "brand-ink": "Texto sobre brand.", "brand-soft": "Etiquetas neutras e fundo de ícone.", "hl": "Marca-texto: hoje, meta, concluído, botão principal. Só marca; nunca texto corrido nem área grande.", "hl-ink": "Texto sobre hl.", "hl-soft": "Fundo de bloco concluído e do dia de hoje.", "warn": "Âmbar de prazo: só alerta.", "warn-soft": "Fundo de aviso.", "focus": "Anel de foco e bloco de áudio."};
  var FOCO = {"claro": "#2B6CB0", "escuro": "#7FB3F2", "azul-fl-esc": "#9CC3FF"};
  var hx = function (h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  var mx = function (a, b, t) { var x = hx(a), y = hx(b); return '#' + x.map(function (v, i) { return Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0'); }).join(''); };
  var lum = function (h) { var c = hx(h).map(function (v) { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; };
  var CHAVES = ['--bg', '--surface', '--surface2', '--ink', '--muted', '--line', '--brand', '--brand-ink', '--brand-soft', '--hl', '--hl-ink', '--hl-soft', '--warn', '--warn-soft', '--focus', 'color-scheme'];
  var r = document.documentElement, tema = 'auto', toastT;
  function toast(m) { var t = document.getElementById('toast'); t.textContent = m; t.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(function () { t.classList.remove('on'); }, 1800); }
  // Mesma regra do applyTheme do Trilha (trilha.html)
  function aplicar(id) {
    delete r.dataset.float; CHAVES.forEach(function (k) { r.style.removeProperty(k); });
    var P = PRESETS.filter(function (p) { return p.id === id; })[0];
    if (P && id !== 'auto') {
      var dark = lum(P.bg) < .2;
      var v = { '--bg': P.bg, '--surface': dark ? mx(P.bg, '#FFFFFF', .06) : '#FFFFFF', '--surface2': mx(P.bg, P.ink, .07), '--ink': P.ink, '--muted': mx(P.ink, P.bg, .36), '--line': mx(P.bg, P.ink, .16),
        '--brand': P.p, '--brand-ink': lum(P.p) > .35 ? '#18211E' : '#F3F5F2', '--brand-soft': P.s, '--hl': P.h, '--hl-ink': P.fl ? '#06142b' : '#18211E', '--hl-soft': mx(P.bg, P.h, dark ? .22 : .3),
        '--warn': P.a, '--warn-soft': mx(P.bg, P.a, .16), '--focus': FOCO[P.id] || (dark ? FOCO.escuro : FOCO.claro) };
      Object.keys(v).forEach(function (k) { r.style.setProperty(k, v[k]); });
      r.style.setProperty('color-scheme', dark ? 'dark' : 'light');
      if (P.fl) r.dataset.float = dark ? 'dark' : 'light';
    }
    tema = id; desenhar();
  }
  function desenhar() {
    document.getElementById('paletas').innerHTML = PRESETS.map(function (p) {
      var sw = p.id === 'auto' ? ['#1F4D40', '#F2C14E', '#F3F5F2', '#111916'] : [p.p, p.h, p.ink, p.bg];
      return '<button class="pre" type="button" data-t="' + p.id + '" aria-pressed="' + (p.id === tema) + '"><span class="sw">' + sw.map(function (c) { return '<i style="background:' + c + '"></i>'; }).join('') + '</span>' + p.name + '</button>';
    }).join('');
    var cs = getComputedStyle(r);
    document.getElementById('tabTokens').innerHTML = Object.keys(USOS).map(function (k) {
      var v = cs.getPropertyValue('--' + k).trim();
      return '<tr><td class="mono">--' + k + '</td><td class="mono"><span class="amostra" style="background:var(--' + k + ')"></span>' + v + '</td><td>' + USOS[k] + '</td></tr>';
    }).join('');
  }
  document.getElementById('paletas').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-t]'); if (!b) return;
    aplicar(b.getAttribute('data-t'));
    try { localStorage.setItem('orgatec.trilha.tema', tema); } catch (e) {}
    toast('Cores: ' + PRESETS.filter(function (p) { return p.id === tema; })[0].name);
  });
  document.getElementById('btnCores').addEventListener('click', function () { document.getElementById('cores').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); });
  Array.prototype.forEach.call(document.querySelectorAll('[data-toast]'), function (b) { b.addEventListener('click', function () { toast(b.getAttribute('data-toast')); }); });
  // Ação destrutiva: o 1º clique arma o botão por 6 s; nunca confirm() do navegador
  var apagar = document.getElementById('btnApagar'), armado = null;
  apagar.addEventListener('click', function () {
    if (armado) { clearTimeout(armado); armado = null; apagar.textContent = 'Apagar exemplo'; toast('Exemplo apagado'); return; }
    apagar.textContent = 'Confirmar: apagar exemplo';
    armado = setTimeout(function () { armado = null; apagar.textContent = 'Apagar exemplo'; }, 6000);
  });
  Array.prototype.forEach.call(document.querySelectorAll('.blk input'), function (c) {
    c.addEventListener('change', function () { c.closest('.blk').classList.toggle('done', c.checked); if (c.checked) toast('Bloco feito'); });
  });
  var salvo = 'azul-fl';
  try { salvo = localStorage.getItem('orgatec.trilha.tema') || salvo; } catch (e) {}
  aplicar(PRESETS.some(function (p) { return p.id === salvo; }) ? salvo : 'auto');
})();
