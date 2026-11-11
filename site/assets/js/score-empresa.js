/* Janela do score da empresa (empresarial/score.html): medidor da nota geral, evolução das notas registradas e alertas
   (prazo de pendência chegando e frente em Risco). A conta é de termometro.js (fonte única); aqui só há desenho e alertas.
   Testável no Node (tests/js/score-empresa.test.js): as funções puras não tocam no DOM.

   Privacidade: as respostas do termômetro ficam na memória da aba (sessionStorage, termometro.CHAVE_RESPOSTAS). O histórico
   guarda SÓ as notas, neste navegador (localStorage, CHAVE_HISTORICO), e só quando o visitante aperta "Registrar a nota de
   hoje". Nada vai para a rede. A nota é nível de atenção, não parecer nem probabilidade de autuação. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).scoreEmpresa = factory();
})(this, function () {
  'use strict';
  var CHAVE_HISTORICO = 'orgatec.score.historico';
  var MAX_REGISTROS = 24;
  // Tom de cada faixa nos gráficos: o mesmo dos selos do site (og-selo-pendente = laranja, definido/futuro = azul)
  var COR = { risco: 'var(--pendente-texto)', atencao: 'var(--acao)', em_dia: 'var(--acao)' };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function dataBR(iso) { var p = String(iso).slice(0, 10).split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : esc(iso); }
  function diasEntre(de, ate) { return Math.round((Date.parse(ate + 'T00:00:00Z') - Date.parse(de + 'T00:00:00Z')) / 86400000); }
  function n1(x) { return Math.round(x * 10) / 10; }

  /* Limites das faixas em nota de 0 a 100 (de FAIXAS do termômetro), do menor para o maior: [60, 85] */
  function limites(faixas) {
    return faixas.filter(function (f) { return f.minimo > 0; }).map(function (f) { return Math.round(f.minimo * 100); }).sort(function (a, b) { return a - b; });
  }
  function textoFaixas(faixas) {
    var l = limites(faixas), por = {};
    faixas.forEach(function (f) { por[f.nivel] = f.rotulo; });
    return (por.risco || 'Risco') + ' abaixo de ' + l[0] + ', ' + (por.atencao || 'Atenção') + ' de ' + l[0] + ' a ' + (l[1] - 1) + ', ' + (por.em_dia || 'Em dia') + ' a partir de ' + l[1];
  }

  // ---------- Medidor: meio arco de 0 a 100, trilho neutro, arco da nota no tom da faixa, marcas nos limites
  var CX = 120, CY = 118, R = 92;
  function ponto(frac, r) { var a = Math.PI * (1 - frac); return [n1(CX + r * Math.cos(a)), n1(CY - r * Math.sin(a))]; }
  function arco(f0, f1, r) { var a = ponto(f0, r), b = ponto(f1, r); return 'M' + a[0] + ' ' + a[1] + ' A' + r + ' ' + r + ' 0 0 1 ' + b[0] + ' ' + b[1]; }

  /* nota: 0..100 ou null; faixa: item de FAIXAS (ou null); faixas: termometro.FAIXAS */
  function medidor(nota, faixa, faixas) {
    var titulo = nota == null ? 'Nota geral: sem resposta ainda.' : 'Nota geral: ' + nota + ' de 100, faixa ' + faixa.rotulo + '.';
    var marcas = limites(faixas).map(function (v) {
      var a = ponto(v / 100, R - 12), b = ponto(v / 100, R + 12), t = ponto(v / 100, R + 24);
      return '<line x1="' + a[0] + '" y1="' + a[1] + '" x2="' + b[0] + '" y2="' + b[1] + '" style="stroke:var(--superficie);stroke-width:3"/>' +
        '<text x="' + t[0] + '" y="' + t[1] + '" text-anchor="middle" style="font-size:11px;fill:var(--tinta-fraca)">' + v + '</text>';
    }).join('');
    var valor = nota == null || nota <= 0 ? '' :
      '<path d="' + arco(0, Math.min(nota, 100) / 100, R) + '" fill="none" style="stroke:' + COR[faixa.nivel] + ';stroke-width:16;stroke-linecap:butt"/>';  // ponta reta: 59 não pode parecer 60
    return '<svg viewBox="0 0 240 150" width="100%" class="block max-w-[340px] mx-auto" role="img" aria-labelledby="medidor-titulo" data-medidor="' + (nota == null ? '' : nota) + '">' +
      '<title id="medidor-titulo">' + esc(titulo + ' Faixas: ' + textoFaixas(faixas) + '.') + '</title>' +
      '<path d="' + arco(0, 1, R) + '" fill="none" style="stroke:var(--linha);stroke-width:16"/>' + valor + marcas +
      '<text x="' + ponto(0, R)[0] + '" y="' + (CY + 20) + '" text-anchor="middle" style="font-size:11px;fill:var(--tinta-fraca)">0</text>' +
      '<text x="' + ponto(1, R)[0] + '" y="' + (CY + 20) + '" text-anchor="middle" style="font-size:11px;fill:var(--tinta-fraca)">100</text>' +
      '<text x="' + CX + '" y="' + (CY - 12) + '" text-anchor="middle" class="font-display" style="font-size:46px;font-weight:800;fill:var(--tinta);font-variant-numeric:tabular-nums">' + (nota == null ? '—' : nota) + '</text>' +
      '<text x="' + CX + '" y="' + (CY + 12) + '" text-anchor="middle" style="font-size:13px;fill:var(--tinta-suave)" data-medidor-faixa="' + (faixa ? faixa.nivel : '') + '">' +
        (faixa ? 'de 100 · ' + esc(faixa.rotulo) : 'responda o termômetro') + '</text></svg>';
  }

  // ---------- Evolução: linha das notas registradas de um perfil, com as linhas de 60 e 85, ponto e dica em cada registro
  function doPerfil(historico, perfil) {
    return (historico || []).filter(function (e) { return e.perfil === perfil; }).sort(function (a, b) { return a.data < b.data ? -1 : a.data > b.data ? 1 : 0; });
  }
  var X0 = 34, X1 = 306, Y0 = 132, ALTURA = 112;  // eixo: nota 0 em Y0, 100 em Y0 - ALTURA
  function y(v) { return n1(Y0 - v / 100 * ALTURA); }

  function evolucao(historico, perfil, faixas) {
    var pts = doPerfil(historico, perfil);
    if (!pts.length) return '<p class="og-cartao-texto" data-evolucao-vazia>Ainda não há nota registrada para este perfil. Use "Registrar a nota de hoje" para começar; só a nota fica guardada, neste navegador.</p>';
    var t0 = Date.parse(pts[0].data), t1 = Date.parse(pts[pts.length - 1].data);
    var xs = pts.map(function (e) { return pts.length === 1 || t1 === t0 ? n1((X0 + X1) / 2) : n1(X0 + (Date.parse(e.data) - t0) / (t1 - t0) * (X1 - X0)); });
    var grade = limites(faixas).map(function (v) {
      return '<line x1="' + X0 + '" y1="' + y(v) + '" x2="' + X1 + '" y2="' + y(v) + '" style="stroke:var(--linha);stroke-dasharray:3 4"/>' +
        '<text x="' + (X0 - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end" style="font-size:11px;fill:var(--tinta-fraca)">' + v + '</text>';
    }).join('') + '<line x1="' + X0 + '" y1="' + Y0 + '" x2="' + X1 + '" y2="' + Y0 + '" style="stroke:var(--linha-campo)"/>' +
      '<text x="' + (X0 - 6) + '" y="' + (Y0 + 4) + '" text-anchor="end" style="font-size:11px;fill:var(--tinta-fraca)">0</text>';
    var linha = pts.length > 1 ? '<polyline points="' + pts.map(function (e, i) { return xs[i] + ',' + y(e.geral); }).join(' ') +
      '" fill="none" style="stroke:var(--acao);stroke-width:2;stroke-linejoin:round;stroke-linecap:round"/>' : '';
    var rotular = pts.length <= 6;  // com muitos registros, só a primeira e a última data (sem colisão de rótulos)
    var marcas = pts.map(function (e, i) {
      var ult = i === pts.length - 1, data = rotular || i === 0 || ult;
      return '<g data-ponto="' + esc(e.data) + '"><title>' + dataBR(e.data) + ': ' + e.geral + ' de 100</title>' +
        '<circle cx="' + xs[i] + '" cy="' + y(e.geral) + '" r="12" fill="transparent"/>' +
        '<circle cx="' + xs[i] + '" cy="' + y(e.geral) + '" r="' + (ult ? 5 : 4) + '" style="fill:var(--acao);stroke:var(--superficie);stroke-width:2"/>' +
        (ult ? '<text x="' + xs[i] + '" y="' + (y(e.geral) - 10) + '" text-anchor="middle" style="font-size:12px;font-weight:700;fill:var(--tinta)">' + e.geral + '</text>' : '') +
        (data ? '<text x="' + xs[i] + '" y="' + (Y0 + 16) + '" text-anchor="middle" style="font-size:11px;fill:var(--tinta-fraca)">' + dataBR(e.data).slice(0, 5) + '</text>' : '') + '</g>';
    }).join('');
    var resumo = pts.map(function (e) { return dataBR(e.data) + ' ' + e.geral; }).join('; ');
    var tabela = '<details class="mt-2 text-sm"><summary class="og-link cursor-pointer">Ver em tabela</summary><table class="mt-2 text-sm" data-evolucao-tabela><thead><tr><th class="text-left pr-4">Data</th><th class="text-left">Nota</th></tr></thead><tbody>' +
      pts.map(function (e) { return '<tr><td class="pr-4">' + dataBR(e.data) + '</td><td>' + e.geral + '</td></tr>'; }).join('') + '</tbody></table></details>';
    return '<svg viewBox="0 0 320 154" width="100%" class="block max-w-[440px] mx-auto" role="img" aria-label="' + esc('Evolução da nota geral: ' + resumo + '.') + '" data-evolucao="' + pts.length + '">' +
      grade + linha + marcas + '</svg>' + tabela;
  }

  // ---------- Alertas: prazo de pendência chegando e frente em Risco
  /* Tom do prazo: até 30 dias, urgente; até 90, atenção; depois, informativo. */
  function tomPrazo(dias) { return dias <= 30 ? 'urgente' : dias <= 90 ? 'atencao' : 'informativo'; }

  /* Lista de alertas do perfil: prazos (em ordem de data) e depois frentes em Risco (da menor nota para a maior).
     Devolve também o plano para o .ics (calendario.gerarIcs). */
  function alertas(T, respostas, perfil, itensPorId, hoje) {
    var pilares = T.pilaresDoPerfil(perfil), r = T.avaliar(respostas || {}, pilares, perfil), n = T.nota(r);
    var porId = {};
    r.pendencias.forEach(function (pd) { porId['termometro-' + pd.pergunta.id] = pd.pergunta; });
    var plano = T.planoDeAcao(r.pendencias, itensPorId, hoje);
    var lista = plano.map(function (ev) {
      var p = porId[ev.id], dias = diasEntre(hoje, ev.data);
      return { tipo: 'prazo', data: ev.data, dias: dias, tom: tomPrazo(dias), pergunta: p, regra: T.regraDe(p) };
    });
    var riscos = pilares.filter(function (p) { return n.porPilar[p] != null && r.porPilar[p].faixa.nivel === 'risco'; })
      .sort(function (a, b) { return n.porPilar[a] - n.porPilar[b]; })
      .map(function (p) {
        var pend = r.pendencias.filter(function (pd) { return pd.pergunta.pilar === p; });
        var regra = T.REGRA[p] || (pend[0] && T.regraDe(pend[0].pergunta));
        return { tipo: 'risco', pilar: p, nota: n.porPilar[p], pendencias: pend.length, regra: regra };
      });
    return { lista: lista.concat(riscos), plano: plano };
  }

  var SELO_PRAZO = { urgente: 'pendente', atencao: 'futuro', informativo: 'definido' };
  function htmlAlertas(lista, nomes, fontesPorId) {
    nomes = nomes || {}; fontesPorId = fontesPorId || {};
    if (!lista.length) return '<p class="og-cartao-texto" data-alertas-vazio>Nenhum alerta para este perfil: não há pendência com prazo oficial nem frente em Risco nas respostas.</p>';
    return '<ul class="grid gap-4">' + lista.map(function (a) {
      var link = a.regra ? '<a class="og-link text-sm" href="../compliance/' + esc(a.regra.pagina) + '">Ver a regra</a>' : '';
      if (a.tipo === 'prazo') {
        var fontes = a.pergunta.fontes.map(function (f) { return fontesPorId[f] ? esc(fontesPorId[f].rotulo) : esc(f); }).join('; ');
        var quando = a.dias === 0 ? 'vence hoje' : a.dias === 1 ? 'falta 1 dia' : 'faltam ' + a.dias + ' dias';
        return '<li data-alerta="prazo" data-alerta-tom="' + a.tom + '" data-alerta-id="' + esc(a.pergunta.id) + '">' +
          '<span class="og-selo og-selo-' + SELO_PRAZO[a.tom] + '">Prazo · ' + quando + '</span>' +
          '<p class="text-tinta font-semibold mt-1">' + esc(a.pergunta.corrigir) +
            (a.pergunta.corrigir.indexOf(dataBR(a.data)) < 0 ? ' Prazo: ' + dataBR(a.data) + '.' : '') + '</p>' +
          '<p class="text-xs text-tinta-fraca">Fonte: ' + fontes + '</p>' + link + '</li>';
      }
      return '<li data-alerta="risco" data-alerta-pilar="' + esc(a.pilar) + '">' +
        '<span class="og-selo og-selo-pendente">Frente em Risco · ' + a.nota + ' de 100</span>' +
        '<p class="text-tinta font-semibold mt-1">' + esc(nomes[a.pilar] || a.pilar) + ': ' + a.pendencias + (a.pendencias === 1 ? ' pendência' : ' pendências') + ' para corrigir ou verificar.</p>' +
        link + '</li>';
    }).join('') + '</ul>';
  }

  // ---------- Histórico: só as notas, uma por dia e perfil, no máximo MAX_REGISTROS
  function nota0a100(v) { return typeof v === 'number' && v >= 0 && v <= 100 && Math.round(v) === v; }
  function entradaValida(e) {
    return e && /^\d{4}-\d{2}-\d{2}$/.test(e.data) && typeof e.perfil === 'string' && nota0a100(e.geral) &&
      e.porPilar && typeof e.porPilar === 'object' && Object.keys(e.porPilar).every(function (k) { return e.porPilar[k] === null || nota0a100(e.porPilar[k]); });
  }
  function limpar(e) {
    var porPilar = {};
    Object.keys(e.porPilar || {}).forEach(function (k) { porPilar[k] = e.porPilar[k]; });
    return { data: e.data, perfil: e.perfil, geral: e.geral, porPilar: porPilar };
  }
  /* Novo histórico com a entrada: substitui a do mesmo dia e perfil; fica com os MAX_REGISTROS mais recentes. */
  function registrar(historico, entrada) {
    if (!entradaValida(entrada)) return (historico || []).slice();
    var novo = (historico || []).filter(function (e) { return !(e.data === entrada.data && e.perfil === entrada.perfil); }).concat([limpar(entrada)]);
    novo.sort(function (a, b) { return a.data < b.data ? -1 : a.data > b.data ? 1 : 0; });
    return novo.slice(-MAX_REGISTROS);
  }
  /* Lê o texto guardado; o que não for entrada válida é descartado. */
  function lerHistorico(texto) {
    try { var h = JSON.parse(texto || '[]'); return Array.isArray(h) ? h.filter(entradaValida).map(limpar) : []; } catch (e) { return []; }
  }

  // ---------- Tela
  function hojeLocal(d) { d = d || new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }

  function iniciar() {
    var raiz = document.querySelector('[data-score-empresa]');
    var O = window.Orgatec || {}, T = O.termometro;
    if (!raiz || !T) return;
    function $(s) { return raiz.querySelector(s); }
    var C = O.config || {}, K = O.conteudo || {}, F = O.fontes || {}, itens = {};
    (O.reformaItens || []).concat(O.complianceItens || []).forEach(function (it) { itens[it.id] = it; });
    if (!T.publicavel(C.ambiente)) {
      raiz.innerHTML = '<p class="og-cartao-texto" data-score-revisao>A janela do score está em revisão técnica e volta em breve. Enquanto isso, fale com o escritório.</p>';
      return;
    }
    var respostas = {}, historico = [], guarda = true;
    try { respostas = JSON.parse(sessionStorage.getItem(T.CHAVE_RESPOSTAS) || '{}') || {}; } catch (e) { respostas = {}; }
    try { historico = lerHistorico(localStorage.getItem(CHAVE_HISTORICO)); } catch (e) { guarda = false; }
    var seletor = $('[data-score-atividade]'), status = $('[data-score-status]'), plano = [], atual = null;
    // #perfil-<id> (vindo da Janela) escolhe a atividade correspondente
    var h = (location.hash || '').replace('#perfil-', '');
    Object.keys(T.ATIVIDADE_PERFIL).forEach(function (a) { if (T.ATIVIDADE_PERFIL[a] === h && seletor) seletor.value = a; });

    function desenhar() {
      var perfil = T.perfilDaAtividade(seletor ? seletor.value : ''), pilares = T.pilaresDoPerfil(perfil);
      var r = T.avaliar(respostas, pilares, perfil), n = T.nota(r), hoje = hojeLocal();
      atual = n.geral == null ? null : { data: hoje, perfil: perfil, geral: n.geral, porPilar: n.porPilar };
      $('[data-score-perfil]').textContent = T.PERFIS[perfil].rotulo;
      $('[data-score-medidor]').innerHTML = medidor(n.geral, r.faixa, T.FAIXAS) +
        '<p class="text-sm text-tinta-suave text-center mt-1">' + r.respondidas + ' de ' + r.total + ' perguntas respondidas para este perfil.</p>' +
        (n.geral == null ? '<p class="mt-3 text-center"><a class="og-btn og-btn-primario og-btn-md" data-score-responder href="../compliance/termometro.html#perfil-' + perfil + '">Responder o termômetro</a></p>'
          : '<p class="mt-2 text-center"><a class="og-link text-sm" href="../compliance/termometro.html#perfil-' + perfil + '">Rever as respostas no termômetro</a></p>');
      $('[data-score-evolucao]').innerHTML = guarda ? evolucao(historico, perfil, T.FAIXAS)
        : '<p class="og-cartao-texto">Este navegador não permite guardar dados do site; a evolução fica indisponível.</p>';
      $('[data-score-registrar]').hidden = !atual || !guarda;
      $('[data-score-apagar]').hidden = !historico.length || !guarda;
      var al = alertas(T, respostas, perfil, itens, hoje);
      plano = al.plano;
      $('[data-score-alertas]').innerHTML = n.geral == null && !al.lista.length
        ? '<p class="og-cartao-texto">Os alertas aparecem depois que você responde o termômetro.</p>' : htmlAlertas(al.lista, K.PILARES, F.porId);
      $('[data-score-ics]').hidden = !plano.length || !O.calendario;
    }
    function avisar(t) { if (status) status.textContent = t; }
    if (seletor) seletor.addEventListener('change', function () { history.replaceState(null, '', '#perfil-' + T.perfilDaAtividade(seletor.value)); avisar(''); desenhar(); });
    $('[data-score-registrar]').addEventListener('click', function () {
      if (!atual) return;
      historico = registrar(historico, atual);
      try { localStorage.setItem(CHAVE_HISTORICO, JSON.stringify(historico)); avisar('Nota de ' + dataBR(atual.data) + ' registrada neste navegador.'); }
      catch (e) { avisar('Não foi possível guardar neste navegador.'); }
      desenhar();
    });
    $('[data-score-apagar]').addEventListener('click', function () {
      historico = [];
      try { localStorage.removeItem(CHAVE_HISTORICO); } catch (e) { /* nada a apagar */ }
      avisar('Histórico de notas apagado deste navegador.');
      desenhar();
    });
    $('[data-score-ics]').addEventListener('click', function () {
      if (!plano.length || !O.calendario) return;
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([O.calendario.gerarIcs(plano)], { type: 'text/calendar;charset=utf-8' }));
      a.download = 'orgatec-prazos-compliance.ics';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    window.addEventListener('pageshow', function () {  // volta do termômetro: relê as respostas da aba
      try { respostas = JSON.parse(sessionStorage.getItem(T.CHAVE_RESPOSTAS) || '{}') || {}; } catch (e) { respostas = {}; }
      desenhar();
    });
    desenhar();
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
  }
  return { CHAVE_HISTORICO: CHAVE_HISTORICO, MAX_REGISTROS: MAX_REGISTROS, limites: limites, medidor: medidor, evolucao: evolucao,
    alertas: alertas, htmlAlertas: htmlAlertas, tomPrazo: tomPrazo, registrar: registrar, lerHistorico: lerHistorico, hojeLocal: hojeLocal };
});
