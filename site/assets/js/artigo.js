/* Páginas do Hub: renderiza citações a partir de fontes.js (mesma origem do selo
   "pendente de validação" usado no simulador) e textos que dependem da data. */
(function () {
  'use strict';
  var O = window.Orgatec, F = O.fontes, C = O.config;
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

  document.querySelectorAll('[data-fontes]').forEach(function (alvo) {
    var ids = alvo.getAttribute('data-fontes').split(',');
    alvo.textContent = '';
    ids.forEach(function (id, i) {
      var f = F.porId[id.trim()];
      if (i) alvo.appendChild(document.createTextNode('; '));
      if (!f) { alvo.appendChild(el('span', '', id)); return; }
      if (f.url) { var a = el('a', 'underline hover:text-brandBlue', f.rotulo); a.href = f.url; a.target = '_blank'; a.rel = 'noopener'; alvo.appendChild(a); }
      else alvo.appendChild(el('span', '', f.rotulo));
      if (!f.validado) alvo.appendChild(el('span', 'badge-pendente text-[10px] font-semibold px-2 py-0.5 rounded-full ml-1', 'pendente de validação'));
    });
  });

  var j = document.querySelector('[data-janela-simples]');
  if (j && O.regras) {
    var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
    var r = O.regras.janelaOpcaoSimples();
    j.textContent = r.aberta
      ? 'A janela está aberta neste mês (' + MESES[r.mes - 1] + ' de ' + r.ano + '), para o semestre que começa em ' + r.inicio + '.'
      : 'Próxima janela: ' + MESES[r.mes - 1] + ' de ' + r.ano + ', para o semestre que começa em ' + r.inicio + '.';
  }

  var tb = document.querySelector('[data-lista-fontes]');
  if (tb) {
    F.lista.forEach(function (f) {
      var tr = el('tr', 'border-b border-slate-100');
      var c1 = el('td', 'py-2 pr-3 align-top');
      if (f.url) { var a = el('a', 'underline hover:text-brandBlue', f.rotulo); a.href = f.url; a.target = '_blank'; a.rel = 'noopener'; c1.appendChild(a); }
      else c1.textContent = f.rotulo;
      var c2 = el('td', 'py-2 align-top whitespace-nowrap');
      c2.appendChild(f.validado ? el('span', 'text-xs text-emerald-700', 'conferido em ' + f.conferido.split('-').reverse().join('/'))
        : el('span', 'badge-pendente text-[10px] font-semibold px-2 py-0.5 rounded-full', 'pendente de validação'));
      tr.appendChild(c1); tr.appendChild(c2); tb.appendChild(tr);
    });
  }

  document.querySelectorAll('[data-link="whatsapp"]').forEach(function (a) {
    a.href = 'https://wa.me/' + C.whatsapp.numeroE164 + '?text=' + encodeURIComponent('Olá, li o conteúdo sobre a Reforma Tributária no site da ORGATEC e gostaria de agendar um diagnóstico.');
  });
})();
