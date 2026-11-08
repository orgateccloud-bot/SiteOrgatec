/* Tela do boletim de mudanças por público. Só DOM: a montagem é de boletim.js. */
(function () {
  'use strict';
  var O = window.Orgatec, C = O.config, K = O.conteudo, B = O.boletim;
  var raiz = document.querySelector('[data-boletim]');
  if (!raiz || !B || !K) return;
  var esc = K.esc, data = K.formatarData;
  var todos = (O.reformaItens || []).concat(O.complianceItens || []);
  var itens = K.publicaveis(todos, O.fontes ? O.fontes.porId : {}, C.ambiente).itens || [];
  var partes = B.montar(itens, K.PUBLICOS).map(function (p) {
    var muds = p.mudancas.length ? '<ul class="grid gap-2 mt-3">' + p.mudancas.map(function (m) {
      return '<li class="og-cartao-texto" data-boletim-mudanca><strong>' + esc(data(m.data)) + '</strong> · ' + esc(m.nota) +
        ' <a href="../reforma/index.html#item-' + esc(m.id) + '">Ver o ponto</a></li>';
    }).join('') + '</ul>' : '<p class="og-cartao-texto mt-3">Nenhuma mudança registrada para este público.</p>';
    var conf = p.conferidos.length ? '<p class="text-xs text-tinta-fraca mt-3">Pontos deste público: ' + p.conferidos.length +
      '. Conferência mais recente em ' + esc(data(p.conferidos[0].consultadoEm)) + '.</p>' : '';
    return '<article class="og-cartao" id="boletim-' + esc(p.publico) + '" data-boletim-publico="' + esc(p.publico) + '"><h2 class="og-cartao-titulo">' +
      esc(p.rotulo) + '</h2>' + muds + conf + '</article>';
  });
  raiz.innerHTML = partes.join('') || '<p class="og-cartao-texto">Nenhum ponto publicado.' +
    (C.ambiente === 'producao' ? ' Itens aguardando revisão técnica não aparecem.' : '') + '</p>';
})();
