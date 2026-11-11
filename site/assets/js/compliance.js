/* Tela do termômetro de conformidade (compliance/termometro.html). Só DOM: a conta é de termometro.js.
   Nenhuma resposta sai do navegador: não há fetch, formulário enviado nem dado na URL. As respostas
   ficam na memória da aba (sessionStorage) só para sobreviver a um recarregamento, e "Limpar" apaga. */
(function () {
  'use strict';
  var O = window.Orgatec, C = O.config, F = O.fontes, K = O.conteudo, T = O.termometro;
  var raiz = document.querySelector('[data-termometro]');
  if (!raiz || !T) return;
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  if (!T.publicavel(C.ambiente)) {  // produção sem revisão técnica dos pesos (pendência V11)
    raiz.innerHTML = '<p class="og-cartao-texto">O termômetro está em revisão técnica e volta em breve. Enquanto isso, fale com o escritório.</p>';
    return;
  }
  // "Ver a regra": a página da frente (ou do público) se o item aparece nela; senão, a Central da Reforma
  var itens = {};
  (O.reformaItens || []).concat(O.complianceItens || []).forEach(function (it) { itens[it.id] = it; });
  function linkRegra(p) {
    var it = itens[p.item], r = T.regraDe(p);
    return it && r && it.destinos.indexOf(r.destino) >= 0 ? r.pagina + '#item-' + p.item : '../reforma/index.html#item-' + p.item;
  }
  var CHAVE = T.CHAVE_RESPOSTAS;
  var respostas = {};
  try { respostas = JSON.parse(sessionStorage.getItem(CHAVE) || '{}') || {}; } catch (e) { respostas = {}; }

  // Camadas "funciona" e "como sabe" (só nas perguntas de peso 3; aparecem depois de um "sim")
  var SN = { sim: 'Sim', nao: 'Não', nao_sei: 'Não sei' };
  function camadas(p) {
    var c = T.CAMADAS[p.id];
    if (!c) return '';
    function grupo(chave, texto) {
      var nome = p.id + '__' + chave;
      return '<div class="camada-pergunta" role="radiogroup" aria-label="' + K.esc(texto) + '"><p class="text-sm text-tinta-suave">' + K.esc(texto) + '</p><div class="chips mt-1">' +
        Object.keys(SN).map(function (r) {
          return '<label class="chip-opcao"><input type="radio" name="' + nome + '" value="' + r + '"' + (respostas[nome] === r ? ' checked' : '') + '><span>' + SN[r] + '</span></label>';
        }).join('') + '</div></div>';
    }
    return '<div class="camadas-prova mt-3" data-camadas="' + p.id + '" hidden><p class="eyebrow">Na prática</p>' + grupo('funciona', c.funciona) + grupo('prova', c.prova) + '</div>';
  }

  // ---------- Perguntas, agrupadas por frente (a partir de termometro.js: fonte única)
  var form = $('[data-termometro-perguntas]', raiz);
  form.innerHTML = T.PILARES.map(function (pilar) {
    var qs = T.PERGUNTAS.filter(function (p) { return p.pilar === pilar; });
    return '<fieldset class="og-cartao grid gap-5" data-pilar="' + pilar + '" id="frente-' + pilar + '"><legend class="sr-only">' + K.esc(K.PILARES[pilar]) + '</legend>' +
      '<h2 class="text-xl font-bold text-tinta" aria-hidden="true">' + K.esc(K.PILARES[pilar]) + '</h2>' +
      qs.map(function (p) {
        return '<div class="pergunta" data-pergunta="' + p.id + '" role="radiogroup" aria-labelledby="q-' + p.id + '">' +
          '<p id="q-' + p.id + '" class="text-tinta font-semibold">' + K.esc(p.texto) + '</p>' +
          '<div class="og-item-fontes mt-1">' + K.citacoes(p.fontes, F.porId) + '</div>' +
          '<div class="chips mt-2">' + Object.keys(T.RESPOSTAS).map(function (r) {
            return '<label class="chip-opcao"><input type="radio" name="' + p.id + '" value="' + r + '"' + (respostas[p.id] === r ? ' checked' : '') + '><span>' + T.RESPOSTAS[r] + '</span></label>';
          }).join('') + '</div>' + camadas(p) + '</div>';
      }).join('') + '</fieldset>';
  }).join('');

  // ---------- Perfil (público) e frentes consideradas: o perfil marca as frentes dele; o visitante ainda pode ajustar
  var filtros = $$('[data-filtro-pilar]', raiz);
  function pilaresAtivos() { return filtros.filter(function (c) { return c.checked; }).map(function (c) { return c.value; }); }
  var perfil = 'geral';
  var caixaPerfis = $('[data-termometro-perfis]', raiz);
  if (caixaPerfis) caixaPerfis.innerHTML = Object.keys(T.PERFIS).map(function (k) {
    return '<label class="chip-opcao"><input type="radio" name="perfil" value="' + k + '" data-perfil' + (k === perfil ? ' checked' : '') + '><span>' + K.esc(T.PERFIS[k].rotulo) + '</span></label>';
  }).join('');
  function aplicarPerfil(k) {
    perfil = T.PERFIS[k] ? k : 'geral';
    var ps = T.pilaresDoPerfil(perfil);
    filtros.forEach(function (c) { c.checked = ps.indexOf(c.value) >= 0; });
    $$('[data-perfil]', raiz).forEach(function (r) { r.checked = r.value === perfil; });
  }

  // ---------- Resultado ao vivo
  var saida = $('[data-termometro-resultado]', raiz);
  function desenhar() {
    var ativos = pilaresAtivos();
    T.PILARES.forEach(function (p) { var fs = $('#frente-' + p, raiz); if (fs) fs.hidden = ativos.indexOf(p) < 0; });
    T.PERGUNTAS.forEach(function (p) { var d = $('[data-pergunta="' + p.id + '"]', raiz); if (d) d.hidden = !T.perguntaVale(p, perfil); });
    $$('[data-camadas]', raiz).forEach(function (d) { d.hidden = respostas[d.getAttribute('data-camadas')] !== 'sim'; });
    var r = T.avaliar(respostas, ativos, perfil);
    var consideradas = T.PERGUNTAS.filter(function (p) { return ativos.indexOf(p.pilar) >= 0 && T.perguntaVale(p, perfil); });
    var ev = T.evidencia(respostas, consideradas);
    plano = T.planoDeAcao(r.pendencias, itens, new Date().toISOString().slice(0, 10));
    if (botaoIcs) botaoIcs.hidden = !plano.length;
    var notas = T.nota(r), pct = notas.geral;
    var nivel = r.faixa ? '<span class="og-selo og-selo-' + r.faixa.tom + '" data-nivel="' + r.faixa.nivel + '">' + r.faixa.rotulo + '</span>' : '<span class="og-selo og-selo-pendente" data-nivel="">Responda para ver</span>';
    var porFrente = ativos.map(function (p) {
      var x = r.porPilar[p];
      return '<li class="flex items-center justify-between gap-3"><span>' + K.esc(K.PILARES[p]) + '</span>' +
        (x.faixa ? '<span class="og-selo og-selo-' + x.faixa.tom + '">' + notas.porPilar[p] + '%</span>' : '<span class="text-tinta-fraca text-sm">—</span>') + '</li>';
    }).join('');
    var pend = r.pendencias.map(function (pd) {
      var p = pd.pergunta;
      return '<li class="og-item" data-pendencia="' + p.id + '"><span class="og-selo og-selo-' + (pd.tipo === 'corrigir' ? 'pendente' : 'futuro') + '">' + (pd.tipo === 'corrigir' ? 'corrigir' : 'verificar') + '</span> ' +
        K.esc(p.corrigir) + '<div class="og-item-fontes">' + K.citacoes(p.fontes, F.porId) + '</div>' +
        '<a class="og-link text-sm" data-ver-regra href="' + K.esc(linkRegra(p)) + '">Ver a regra</a></li>';
    }).join('');
    saida.innerHTML =
      '<div class="flex flex-wrap items-center justify-between gap-3"><p class="eyebrow">Resultado</p>' + nivel + '</div>' +
      '<p class="text-4xl font-extrabold text-tinta font-display mt-2" data-percentual>' + (pct == null ? '—' : pct + '%') + '</p>' +
      '<div class="barra" aria-hidden="true"><i style="width:' + (pct || 0) + '%"></i></div>' +
      '<p class="text-sm text-tinta-suave mt-2">' + r.respondidas + ' de ' + r.total + ' perguntas respondidas.</p>' +
      '<ul class="grid gap-2 mt-4 text-sm">' + porFrente + '</ul>' +
      (pend ? '<h3 class="og-cartao-titulo mt-6">O que corrigir ou verificar, por prioridade</h3><ol class="grid gap-3 text-sm" data-pendencias-termometro>' + pend + '</ol>' : '') +
      '<div class="mt-6" data-termometro-evidencia><h3 class="og-cartao-titulo">Prova do que foi declarado</h3>' +
        (ev.declaradas ? '<p class="text-sm" data-evidencia-resumo>' + ev.comProva + ' de ' + ev.declaradas + ' respostas "sim" nas perguntas principais têm prática e registro confirmados.</p>' +
          (ev.semProva.length ? '<ul class="grid gap-1 text-sm mt-2">' + ev.semProva.map(function (p) { return '<li data-sem-prova="' + p.id + '">' + K.esc(T.CAMADAS[p.id].prova) + '</li>'; }).join('') + '</ul>' : '')
          : '<p class="text-sm text-tinta-suave">Responda "sim" a uma pergunta principal para ver a camada de prova.</p>') +
        '<p class="text-xs text-tinta-fraca mt-2">O percentual acima mede o que foi declarado. Um controle só está comprovado quando funciona na prática e deixa registro.</p></div>' +
      '<p class="text-xs text-tinta-fraca mt-6">Resultado orientativo, calculado só no seu navegador. Não é parecer nem probabilidade de autuação. Pesos e faixas em revisão técnica.</p>';
    relatorio(r, ativos, pct);
    if (resumo) {
      resumo.innerHTML = '<span>Resultado: <strong data-resumo-percentual>' + (pct == null ? '—' : pct + '%') + '</strong></span>' +
        (r.faixa ? '<span class="og-selo og-selo-' + r.faixa.tom + '">' + r.faixa.rotulo + '</span>' : '') +
        '<span class="termometro-resumo-ver">Ver o resultado ↓</span>';
      resumo.hidden = r.respondidas === 0;  // só depois da primeira resposta
    }
  }

  // ---------- Relatório para imprimir ou salvar em PDF (só aparece na impressão; mesmo cálculo da tela, sem as respostas brutas)
  var folha = $('[data-termometro-relatorio]', raiz);
  function relatorio(r, ativos, pct) {
    if (!folha) return;
    var hoje = new Date().toLocaleDateString('pt-BR');
    var linhasFrente = ativos.map(function (p) {
      var x = r.porPilar[p];
      return '<li>' + K.esc(K.PILARES[p]) + ': ' + (x.faixa ? Math.round(x.percentual * 100) + '% (' + x.faixa.rotulo + ')' : 'sem resposta') + '</li>';
    }).join('');
    var linhasPend = r.pendencias.map(function (pd) {
      var p = pd.pergunta, it = itens[p.item];
      var fontes = p.fontes.map(function (f) { var x = F.porId[f]; return K.esc(x.rotulo) + (x.url ? ' — ' + K.esc(x.url) : '') + (x.validado ? '' : ' (pendente de validação)'); }).join('; ');
      return '<li><strong>' + (pd.tipo === 'corrigir' ? 'Corrigir' : 'Verificar') + ':</strong> ' + K.esc(p.corrigir) +
        '<br><small>Fonte: ' + fontes + (it ? '. Consultado em ' + K.formatarData(it.consultadoEm) : '') + '.</small></li>';
    }).join('');
    folha.innerHTML = '<h1>Termômetro de conformidade — ORGATEC</h1>' +
      '<p>Gerado em ' + hoje + ' · Perfil: ' + K.esc((T.PERFIS[perfil] || T.PERFIS.geral).rotulo) + ' · ' + r.respondidas + ' de ' + r.total + ' perguntas respondidas.</p>' +
      '<p class="relatorio-nivel">Resultado: ' + (pct == null ? '—' : pct + '%') + (r.faixa ? ' · ' + r.faixa.rotulo : '') + '</p>' +
      '<h2>Por frente</h2><ul>' + linhasFrente + '</ul>' +
      (linhasPend ? '<h2>O que corrigir ou verificar, por prioridade</h2><ol>' + linhasPend + '</ol>' : '<p>Nenhuma pendência nas respostas dadas.</p>') +
      (function () { var ev = T.evidencia(respostas, T.PERGUNTAS.filter(function (p) { return ativos.indexOf(p.pilar) >= 0 && T.perguntaVale(p, perfil); }));
        return ev.declaradas ? '<h2>Prova do que foi declarado</h2><p>' + ev.comProva + ' de ' + ev.declaradas + ' respostas "sim" nas perguntas principais têm prática e registro confirmados.</p>' : ''; })() +
      '<p class="relatorio-aviso">Orientação geral, calculada no navegador a partir das respostas do próprio visitante. Não é parecer, não é diagnóstico e não indica probabilidade de autuação. Pesos e faixas em revisão técnica. Fale com o escritório para o diagnóstico: orgatec.io.</p>';
  }
  // ---------- Plano de ação em .ics: pendências com prazo legal, no calendário do visitante (sem envio de dados)
  var plano = [], botaoIcs = $('[data-termometro-ics]', raiz);
  if (botaoIcs) botaoIcs.addEventListener('click', function () {
    if (!plano.length || !O.calendario) return;
    var blob = new Blob([O.calendario.gerarIcs(plano)], { type: 'text/calendar;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'orgatec-plano-de-acao.ics';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  });
  var imprimir = $('[data-termometro-imprimir]', raiz);
  if (imprimir) imprimir.addEventListener('click', function () { desenhar(); window.print(); });

  // Celular: barra fixa com o resumo enquanto o painel de resultado está fora da tela (no desktop o painel é fixo)
  var resumo = $('[data-termometro-resumo]', raiz), painel = $('#resultado', raiz);
  if (resumo && painel && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { resumo.classList.toggle('fora', !es[0].isIntersecting); }).observe(painel);
  }

  form.addEventListener('change', function (ev) {
    var el = ev.target;
    if (el.type !== 'radio') return;
    respostas[el.name] = el.value;
    try { sessionStorage.setItem(CHAVE, JSON.stringify(respostas)); } catch (e) { /* sem memória da aba: só nesta visita */ }
    desenhar();
  });
  filtros.forEach(function (c) { c.addEventListener('change', desenhar); });
  if (caixaPerfis) caixaPerfis.addEventListener('change', function (ev) { if (ev.target.name === 'perfil') { aplicarPerfil(ev.target.value); desenhar(); } });
  var limpar = $('[data-termometro-limpar]', raiz);
  if (limpar) limpar.addEventListener('click', function () {
    respostas = {};
    try { sessionStorage.removeItem(CHAVE); } catch (e) { /* nada a apagar */ }
    $$('input[type=radio]', form).forEach(function (i) { i.checked = false; });
    desenhar();
  });
  // Âncora #perfil-transportador: abre no perfil do público; #pld, #lgpd...: só aquela frente
  var alvo = (location.hash || '').slice(1);
  aplicarPerfil(alvo.indexOf('perfil-') === 0 ? alvo.slice(7) : 'geral');
  if (T.PILARES.indexOf(alvo) >= 0) filtros.forEach(function (c) { c.checked = c.value === alvo; });
  desenhar();
})();
