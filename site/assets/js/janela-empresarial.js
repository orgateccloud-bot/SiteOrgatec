/* Janela Empresarial e do Transporte (empresarial/janela.html). Lê /dados/empresarial/atual.json, do próprio site
   (connect-src 'self'), gerado por tools/gerar_janela_empresarial.py. Regras: todo cartão mostra fonte, horário da coleta e
   estado (ok, atrasado, indisponível); cartão fora da validade vira "atrasado" com o carimbo; indisponível nunca mostra valor. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).janelaEmpresarial = factory();
})(this, function () {
  'use strict';
  var ROTULO = { ok: 'Em dia', atrasado: 'Atrasado', indisponivel: 'Indisponível' };
  var TRANSPORTE = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'];

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function dataBR(iso) { var p = String(iso).slice(0, 10).split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : esc(iso); }
  function horaBR(iso) { return iso ? dataBR(iso) + ' ' + String(iso).slice(11, 16) : ''; }

  /* Estado efetivo no navegador: ok vira atrasado quando a coleta passou da validade (ou a data é ilegível). */
  function estadoEfetivo(c, agora) {
    if (c.estado === 'indisponivel' || !c.coletadoEm) return 'indisponivel';
    var t = Date.parse(c.coletadoEm);
    if (isNaN(t)) return 'atrasado';
    return (agora.getTime() - t) / 3600000 > c.validadeHoras ? 'atrasado' : c.estado;
  }

  function lista(itens, vazio) {
    if (!itens.length) return '<p class="og-cartao-texto">' + vazio + '</p>';
    return '<ul class="og-lista">' + itens.map(function (i) { return '<li>' + i + '</li>'; }).join('') + '</ul>';
  }

  function corpoCartao(c, perfil) {
    var d = c.dados || {};
    if (c.id === 'E1' || c.id === 'T4') {
      var prazos = (d.porPerfil && d.porPerfil[perfil]) || [];
      return lista(prazos.map(function (p) { return '<strong>' + dataBR(p.data) + '</strong> ' + esc(p.titulo) + (p.aConfirmar ? ' <em>(data a confirmar)</em>' : ''); }),
        'Nenhum prazo nos próximos 7 dias para este perfil.');
    }
    if (c.id === 'E4') {
      return lista((d.itens || []).map(function (i) { return '<strong>' + dataBR(i.data) + '</strong> ' + esc(i.titulo) + ': ' + esc(i.nota); }),
        'Nenhuma mudança registrada nos itens da reforma nos últimos 7 dias.');
    }
    if (c.id === 'T1') {
      return '<p class="og-cartao-texto">' + esc(d.resolucao) + ', publicada em ' + dataBR(d.publicadaEm) + ', vigência em ' + dataBR(d.vigenciaEm) +
        '. Revisado por ' + esc(d.revisadoPor) + ' em ' + dataBR(d.revisadoEm) + '.</p>';
    }
    return '<p class="og-cartao-texto">' + esc(JSON.stringify(d)) + '</p>';
  }

  function htmlCartao(c, perfil, agora) {
    var est = estadoEfetivo(c, agora);
    var carimbo = c.coletadoEm ? 'Coletado em ' + horaBR(c.coletadoEm) : 'Sem coleta';
    var corpo = est === 'indisponivel'
      ? '<p class="og-cartao-texto">' + esc(c.motivo || 'Fonte indisponível no momento.') + '</p>'
      : (est === 'atrasado' ? '<p class="og-cartao-texto"><strong>Atrasado:</strong> este dado é de ' + horaBR(c.coletadoEm) + ' e pode não estar mais valendo.</p>' : '') + corpoCartao(c, perfil);
    return '<article class="og-cartao" data-cartao="' + esc(c.id) + '" data-estado="' + est + '"><span class="og-cartao-ref">' + esc(c.modulo) + ' · ' + ROTULO[est] + '</span>' +
      corpo + '<p class="text-xs text-tinta-fraca">Fonte: ' + esc(c.fonte) + '. ' + carimbo + '.</p></article>';
  }

  /* Score de compliance (nota de 0 a 100, geral e por frente), calculado por termometro.js com as respostas que o visitante
     deu no termômetro, nesta aba. Função pura: T = termometro.js; nomes = conteudo.PILARES; fontesPorId = fontes.porId.
     Estados: 'revisao' (produção sem a revisão V11: sem nota), 'sem-resposta' (convite ao termômetro) e 'nota'. */
  var AVISO_SCORE = 'Calculado só no seu navegador, com as respostas do termômetro. Não é parecer nem probabilidade de autuação. Pesos e faixas aprovados na revisão técnica de 12/11/2026.';
  function cartaoScore(T, respostas, atividade, ambiente, nomes, fontesPorId) {
    nomes = nomes || {}; fontesPorId = fontesPorId || {};
    var perfil = T.perfilDaAtividade(atividade), rotulo = T.PERFIS[perfil].rotulo;
    var link = '../compliance/termometro.html#perfil-' + perfil;
    function cartao(estado, corpo) {
      return '<article class="og-cartao" data-cartao="score" data-score-estado="' + estado + '" data-score-perfil="' + perfil + '">' +
        '<span class="og-cartao-ref">Compliance · Score de ' + esc(rotulo) + '</span>' + corpo + '</article>';
    }
    if (!T.publicavel(ambiente)) {
      return cartao('revisao', '<p class="og-cartao-texto">O score de compliance está em revisão técnica e volta em breve. Enquanto isso, fale com o escritório.</p>');
    }
    var pilares = T.pilaresDoPerfil(perfil), r = T.avaliar(respostas || {}, pilares, perfil), n = T.nota(r);
    if (n.geral == null) {
      return cartao('sem-resposta', '<p class="og-cartao-texto">Responda o termômetro de conformidade para ver a nota de 0 a 100 da sua empresa, no geral e por frente, ' +
        'com o que corrigir e a fonte de cada ponto. As respostas ficam só neste navegador.</p>' +
        '<p class="mt-3"><a class="og-btn og-btn-primario og-btn-md" data-score-responder href="' + link + '">Responder o termômetro</a></p>');
    }
    var selo = '<span class="og-selo og-selo-' + r.faixa.tom + '" data-score-faixa="' + r.faixa.nivel + '">' + esc(r.faixa.rotulo) + '</span>';
    var frentes = pilares.map(function (p) {
      var x = r.porPilar[p], v = n.porPilar[p];
      return '<li class="flex items-center justify-between gap-3" data-score-frente="' + p + '"><span>' + esc(nomes[p] || p) + '</span>' +
        (v == null ? '<span class="text-tinta-fraca text-sm">—</span>' : '<span class="og-selo og-selo-' + x.faixa.tom + '">' + v + '</span>') + '</li>';
    }).join('');
    var pend = r.pendencias.slice(0, 3).map(function (pd) {
      var p = pd.pergunta, fontes = p.fontes.map(function (f) { return fontesPorId[f] ? esc(fontesPorId[f].rotulo) : esc(f); }).join('; ');
      return '<li data-score-pendencia="' + p.id + '"><span class="og-selo og-selo-' + (pd.tipo === 'corrigir' ? 'pendente' : 'futuro') + '">' + (pd.tipo === 'corrigir' ? 'corrigir' : 'verificar') + '</span> ' +
        esc(p.corrigir) + '<span class="block text-xs text-tinta-fraca">Fonte: ' + fontes + '</span></li>';
    }).join('');
    return cartao('nota',
      '<div class="flex flex-wrap items-center justify-between gap-3 mt-1"><p class="text-4xl font-extrabold text-tinta font-display" data-score-nota>' + n.geral +
        '<span class="text-base font-semibold text-tinta-suave"> de 100</span></p>' + selo + '</div>' +
      '<div class="barra" aria-hidden="true"><i style="width:' + n.geral + '%"></i></div>' +
      '<p class="text-sm text-tinta-suave mt-2">' + r.respondidas + ' de ' + r.total + ' perguntas respondidas para este perfil.</p>' +
      '<ul class="grid gap-2 mt-4 text-sm">' + frentes + '</ul>' +
      (pend ? '<h3 class="og-cartao-titulo mt-5">O que corrigir primeiro</h3><ol class="grid gap-3 text-sm">' + pend + '</ol>' : '') +
      '<p class="mt-4 flex flex-wrap gap-3"><a class="og-btn og-btn-primario og-btn-md" data-score-janela href="score.html#perfil-' + perfil + '">Abrir a janela do score</a>' +
        '<a class="og-btn og-btn-contorno og-btn-md" data-score-termometro href="' + link + '">Ver tudo no termômetro</a></p>' +
      '<p class="text-xs text-tinta-fraca mt-3">' + AVISO_SCORE + '</p>');
  }

  /* atividade 'transportador' mostra também os cartões do transporte; as demais, só os empresariais. */
  function renderizar(janela, opcoes, agora) {
    var perfil = (opcoes.regime || 'real') + '-' + (opcoes.uf || 'GO');
    var cartoes = janela.cartoes.filter(function (c) { return opcoes.atividade === 'transportador' || TRANSPORTE.indexOf(c.id) < 0; });
    var cab = '<p class="text-sm text-tinta-fraca">Gerado em ' + horaBR(janela.geradoEm) + '. Próxima atualização: ' + esc(janela.proximaAtualizacao) + '.</p>';
    return cab + '<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">' + cartoes.map(function (c) { return htmlCartao(c, perfil, agora); }).join('') + '</div>' +
      '<p class="text-sm text-tinta-fraca mt-4">' + esc(janela.aviso) + '</p>';
  }

  function iniciar() {
    var raiz = document.querySelector('[data-janela-empresarial]');
    if (!raiz) return;
    var alvo = raiz.querySelector('[data-janela-lista]'), estado = { atividade: '', regime: 'real', uf: 'GO' }, janela = null;
    var O = window.Orgatec || {}, T = O.termometro, caixaScore = document.querySelector('[data-janela-score]');
    function desenharScore() {
      if (!caixaScore || !T) return;
      var respostas = {};
      try { respostas = JSON.parse(sessionStorage.getItem(T.CHAVE_RESPOSTAS) || '{}') || {}; } catch (e) { respostas = {}; }
      caixaScore.innerHTML = cartaoScore(T, respostas, estado.atividade, (O.config || {}).ambiente,
        (O.conteudo || {}).PILARES, (O.fontes || {}).porId);
    }
    function desenhar() { desenharScore(); if (janela) alvo.innerHTML = renderizar(janela, estado, new Date()); }
    document.querySelectorAll('[data-filtro-janela]').forEach(function (s) {
      estado[s.getAttribute('data-filtro-janela')] = s.value;  // o navegador pode restaurar a escolha ao voltar
      s.addEventListener('change', function () { estado[s.getAttribute('data-filtro-janela')] = s.value; desenhar(); });
    });
    desenharScore();
    window.addEventListener('pageshow', desenharScore);  // volta do termômetro (inclusive pelo cache de navegação)
    fetch(raiz.getAttribute('data-origem'), { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) { janela = j; desenhar(); })
      .catch(function () { alvo.innerHTML = '<p class="og-cartao-texto">A janela está indisponível no momento. Nenhum dado antigo é exibido; fale com o escritório.</p>'; });
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
  }
  return { estadoEfetivo: estadoEfetivo, renderizar: renderizar, cartaoScore: cartaoScore };
});
