/* Cards por atividade (Orgatec Audi Agro) na Janela de Campo: notícias e legislação de site/dados/agro/noticias.json
   (tools/gerar_noticias_agro.py) e o retorno dos widgets do CEPEA (site/cotacoes/*.html, iframe isolado),
   que só informam altura e se a tabela apareceu. Funções de texto puras, testadas no Node. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).agroCards = factory();
})(this, function () {
  'use strict';
  var ESPERA_WIDGET_MS = 4000;  // depois do load do iframe; sem aviso do widget até aqui, o card mostra a falha

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  /* '2026-11-02T12:40-03:00' -> '02/11/2026 às 12h40' (a data já vem no horário de Brasília) */
  function dataHora(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso || '');
    return m ? m[3] + '/' + m[2] + '/' + m[1] + ' às ' + m[4] + 'h' + m[5] : '';
  }
  function dataCurta(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || ''); return m ? m[3] + '/' + m[2] : ''; }

  /* Uma manchete: título com link para a fonte, nome da fonte e data; item de fonte que falhou leva a data da coleta. */
  function itemHtml(it, fontesComFalha) {
    if (!/^https?:\/\//.test(it.link || '')) return '';
    var velho = fontesComFalha && fontesComFalha[it.fonte];
    return '<li class="audi-agro-item"><a href="' + esc(it.link) + '" target="_blank" rel="noopener">' + esc(it.titulo) + '</a>' +
      '<span class="audi-agro-meta">' + esc(it.fonteNome) + (it.data ? ' · ' + esc(dataCurta(it.data)) : '') +
      (velho ? ' · coletado em ' + esc(dataHora(it.coletadoEm)) : '') + '</span></li>';
  }

  function listaHtml(itens, fontesComFalha, vazio) {
    var h = (itens || []).map(function (it) { return itemHtml(it, fontesComFalha); }).join('');
    return h || '<li class="og-cartao-texto">' + esc(vazio) + '</li>';
  }

  /* Aviso das fontes que falharam na última coleta (o site mostra os itens válidos anteriores delas). */
  function situacao(dados) {
    var falhas = (dados.fontes || []).filter(function (f) { return !f.ok; });
    var base = 'Notícias coletadas em ' + dataHora(dados.geradoEm) + ' (horário de Brasília).';
    if (!falhas.length) return base;
    return base + ' Indisponível na última coleta: ' + falhas.map(function (f) {
      return f.nome + (f.ultimaColetaValida ? ' (mostrando itens de ' + dataHora(f.ultimaColetaValida) + ')' : ' (sem itens anteriores)');
    }).join('; ') + '.';
  }

  var api = { esc: esc, dataHora: dataHora, dataCurta: dataCurta, itemHtml: itemHtml, listaHtml: listaHtml, situacao: situacao, ESPERA_WIDGET_MS: ESPERA_WIDGET_MS };
  if (typeof document === 'undefined') return api;
  var secao = document.querySelector('[data-agro]');
  if (!secao) return api;
  var VAZIO = 'Sem notícia recente sobre o tema nas fontes acompanhadas (últimos 90 dias).';

  // ---------- Notícias
  fetch(secao.getAttribute('data-agro-dados') || '../dados/agro/noticias.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
    .then(function (d) {
      var falha = {};
      (d.fontes || []).forEach(function (f) { if (!f.ok) falha[f.id] = true; });
      Array.prototype.forEach.call(secao.querySelectorAll('[data-agro-atividade]'), function (card) {
        var id = card.getAttribute('data-agro-atividade');
        card.querySelector('[data-agro-noticias]').innerHTML = listaHtml((d.atividades || {})[id], falha, VAZIO);
        card.querySelector('[data-agro-atualizado]').textContent = 'Notícias atualizadas em ' + dataHora(d.geradoEm);
      });
      secao.querySelector('[data-agro-tributacao]').innerHTML = listaHtml(d.tributacao, falha, VAZIO);
      secao.querySelector('[data-agro-situacao]').textContent = situacao(d);
    })
    .catch(function () {
      Array.prototype.forEach.call(secao.querySelectorAll('[data-agro-noticias], [data-agro-tributacao]'), function (ul) {
        ul.innerHTML = '<li class="og-cartao-texto">Notícias indisponíveis agora. As cotações abaixo continuam vindo direto do CEPEA.</li>';
      });
    });

  // ---------- Widgets do CEPEA: altura e falha
  var quadros = Array.prototype.slice.call(secao.querySelectorAll('[data-agro-widget]'));
  function aviso(iframe, mostrar) {
    var p = iframe.parentNode.querySelector('[data-agro-aviso]'), card = iframe.closest('[data-agro-atividade]');
    var ref = card.querySelector('.audi-agro-card-topo a');
    if (mostrar) {
      var agora = new Date(Date.now() - 3 * 3600000).toISOString();
      p.innerHTML = 'Cotação do CEPEA indisponível agora (tentativa às ' + esc(agora.slice(11, 16).replace(':', 'h')) + '). ' +
        'Consulte o <a class="og-link" href="' + esc(ref.href) + '" target="_blank" rel="noopener">indicador no site do CEPEA</a>.';
      iframe.hidden = true;
    } else iframe.hidden = false;
    p.hidden = !mostrar;
  }
  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.tipo !== 'orgatec-widget-cepea') return;
    var iframe = quadros.filter(function (q) { return q.contentWindow === ev.source; })[0];  // só aceita os próprios iframes
    if (!iframe) return;
    iframe.setAttribute('data-respondeu', d.ok ? 'ok' : 'falha');
    if (d.ok && d.altura > 0 && d.altura < 1200) iframe.style.height = d.altura + 'px';
    aviso(iframe, !d.ok);
  });
  quadros.forEach(function (iframe) {
    iframe.addEventListener('load', function () {
      if (!iframe.getAttribute('src')) return;
      setTimeout(function () { if (!iframe.hasAttribute('data-respondeu')) aviso(iframe, true); }, ESPERA_WIDGET_MS);
    });
  });
  // Os widgets só carregam quando a seção chega perto da tela, um a cada 300 ms: evita 10 pedidos ao CEPEA de uma vez
  // (o Cloudflare dele recusa rajadas) e não gasta dados de quem não rola até aqui.
  var iniciado = false;
  function carregar() {
    if (iniciado) return;
    iniciado = true;
    quadros.forEach(function (iframe, i) { setTimeout(function () { iframe.src = iframe.getAttribute('data-src'); }, i * 300); });
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); carregar(); } }, { rootMargin: '600px 0px' });
    io.observe(secao);
  } else carregar();
  return api;
});
