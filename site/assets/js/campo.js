/* Janela de Campo: validação e vigência dos boletins (puro, testável no Node) e a tela de
   site/setores/janela-de-campo.html (só no navegador, em [data-campo]). Lê o boletim automático publicado em
   site/dados/campo/ (tools/gerar_boletim_campo.py); sem ele, usa os boletins manuais de boletins-campo.js. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).campo = factory();
})(this, function () {
  'use strict';
  var OPERACOES = [
    { id: 'pulv', nome: 'Pulverização' }, { id: 'plantio', nome: 'Plantio' }, { id: 'colheita', nome: 'Colheita' },
    { id: 'animais', nome: 'Manejo de animais' }, { id: 'maquinas', nome: 'Máquinas e insumos' }
  ];
  var ESTADOS = {
    ok: { rotulo: 'Favorável', icone: '✓' },
    atencao: { rotulo: 'Com restrição', icone: '!' },
    evitar: { rotulo: 'Evitar', icone: '✕' }
  };
  var PERIODOS = ['00–06h', '06–10h', '10–12h', '12–15h', '15–18h', '18–24h'];
  var DIAS = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado'];
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  var DATA = /^\d{4}-\d{2}-\d{2}$/;

  /* Erros de estrutura de um boletim (lista vazia = válido). */
  function validar(b) {
    var e = [];
    if (!b || typeof b !== 'object') return ['boletim ausente'];
    ['id', 'dia', 'emitidoEm'].forEach(function (k) { if (!DATA.test(b[k] || '')) e.push(k + ' precisa ser AAAA-MM-DD'); });
    if (b.emitidoEm > b.dia) e.push('emitidoEm depois do dia previsto');
    if (!b.fontes || !b.fontes.length) e.push('boletim sem fontes');
    (b.fontes || []).forEach(function (f, i) { if (!f.rotulo || !/^https:\/\//.test(f.url || '')) e.push('fonte ' + (i + 1) + ' sem rótulo ou sem link https'); });
    if (!b.regioes || !b.regioes.length) e.push('boletim sem regiões');
    var ids = {};
    (b.regioes || []).forEach(function (r) {
      var q = 'região ' + (r.id || '?');
      if (ids[r.id]) e.push(q + ' repetida');
      ids[r.id] = true;
      ['nome', 'uf', 'ceu', 'temp', 'chuva', 'vento', 'nota'].forEach(function (k) { if (!r[k]) e.push(q + ': falta ' + k); });
      if (!r.dia || r.dia.length !== PERIODOS.length) e.push(q + ': a linha do dia precisa de ' + PERIODOS.length + ' períodos');
      (r.dia || []).forEach(function (s) { if (!ESTADOS[s] && s !== 'passado') e.push(q + ': estado inválido na linha do dia: ' + s); });  // 'passado': período já encerrado sem dado (boletim automático)
      (r.alertas || []).forEach(function (a) { if (!ESTADOS[a[0]] || !a[1]) e.push(q + ': alerta inválido'); });
      OPERACOES.forEach(function (o) {
        var op = r.ops && r.ops[o.id];
        if (!op || !ESTADOS[op[0]] || !op[1]) e.push(q + ': falta a operação ' + o.id);
      });
    });
    return e;
  }

  /* 'vigente' até o fim do dia previsto; depois, 'vencido' (fica no ar como arquivo). */
  function situacao(b, hoje) { return b.dia >= hoje ? 'vigente' : 'vencido'; }

  /* Boletins válidos do mais recente para o mais antigo; o escolhido por id, ou o mais recente. */
  function ordenar(lista) {
    return (lista || []).filter(function (b) { return !validar(b).length; })
      .sort(function (a, b) { return a.dia < b.dia ? 1 : a.dia > b.dia ? -1 : 0; });
  }
  function escolher(lista, id) {
    var ok = ordenar(lista);
    for (var i = 0; i < ok.length; i++) if (ok[i].id === id) return ok[i];
    return ok[0] || null;
  }

  function formatarDia(iso) {
    var p = iso.split('-').map(Number), d = new Date(Date.UTC(p[0], p[1] - 1, p[2]));
    return DIAS[d.getUTCDay()] + ', ' + p[2] + ' de ' + MESES[p[1] - 1] + ' de ' + p[0];
  }
  function dataCurta(iso) { return iso.split('-').reverse().join('/'); }

  /* Horas desde a geração de um boletim automático (null para o boletim manual). Passou de 18 h: desatualizado. */
  function horasDesde(b, agoraMs) {
    if (!b.geradoEm) return null;
    var t = Date.parse(b.geradoEm);
    return isNaN(t) ? null : (agoraMs - t) / 3600000;
  }
  var LIMITE_HORAS = 18;

  /* Polo da seleção: o escolhido, se for da região e tiver previsão neste boletim; senão o primeiro da região que tem.
     (Um polo sem previsão consta em regiao.polos, mas não está em polos.) */
  function poloValido(b, regiao, escolhido) {
    var existentes = (regiao.polos || []).filter(function (id) { return (b.polos || []).some(function (p) { return p.id === id; }); });
    return existentes.indexOf(escolhido) >= 0 ? escolhido : existentes[0];
  }

  var api = { poloValido: poloValido, OPERACOES: OPERACOES, ESTADOS: ESTADOS, PERIODOS: PERIODOS, LIMITE_HORAS: LIMITE_HORAS, validar: validar, situacao: situacao,
    ordenar: ordenar, escolher: escolher, formatarDia: formatarDia, dataCurta: dataCurta, horasDesde: horasDesde };

  // ---------- Tela (só no navegador, na página que tem [data-campo])
  if (typeof document === 'undefined') return api;
  var alvo = document.querySelector('[data-campo]');
  var O = (typeof window !== 'undefined' && window.Orgatec) || {};
  if (!alvo) return api;

  var BASE = alvo.getAttribute('data-campo-dados') || '../dados/campo/';
  var HOJE = (function () { var d = new Date(Date.now() - 3 * 3600000); return d.toISOString().slice(0, 10); })();  // dia em Brasília
  var DSEM = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var selo = function (s, texto) {
    var e = ESTADOS[s];
    if (!e) return '<span class="campo-selo campo-passado">' + esc(texto || 'já passou') + '</span>';
    return '<span class="campo-selo campo-' + s + '"><i aria-hidden="true">' + e.icone + '</i>' + esc(texto || e.rotulo) + '</span>';
  };
  var params = new URLSearchParams(location.search);
  var manuais = ordenar(O.boletinsCampo || []);
  var indice = [];          // [{id, dia, geradoEm, arquivo}] dos boletins automáticos publicados
  var lacunas = [];         // dias do arquivo em que nenhum boletim saiu (AAAA-MM-DD)
  var carregados = {};      // id -> boletim já baixado
  var lista = [], b = null;

  var pref = {};
  try { pref = JSON.parse(localStorage.getItem('orgatec.campo') || '{}'); } catch (e) { pref = {}; }
  var selR = pref.r, selO = OPERACOES.some(function (o) { return o.id === pref.o; }) ? pref.o : OPERACOES[0].id, selP = pref.p;

  function json(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); });
  }

  // O selo já diz o estado: no bloco da operação escolhida, o resumo não repete a palavra inicial
  function resumoSemEstado(t) { return String(t).replace(/^(Favorável|Com restrição|Evitar)( · )?/, ''); }

  function poloDe(id) { return (b.polos || []).filter(function (p) { return p.id === id; })[0]; }
  function regiaoDe(id) { return b.regioes.filter(function (r) { return r.id === id; })[0]; }
  function ajustarSelecao() {
    if (!regiaoDe(selR)) selR = b.regioes[0].id;
    var r = regiaoDe(selR);
    if (b.polos) selP = poloValido(b, r, selP);
  }

  function textoSituacao() {
    var vigente = situacao(b, HOJE) === 'vigente', horas = horasDesde(b, Date.now());
    var inmet = 'Para os avisos oficiais do seu município, consulte <a href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">alertas2.inmet.gov.br</a>.';
    if (!vigente) return ['vencido', '<strong>Boletim vencido: arquivo de ' + esc(dataCurta(b.dia)) + '.</strong> Não use para decidir o trabalho de hoje. ' + inmet];
    if (horas != null && horas > LIMITE_HORAS) return ['vencido', '<strong>Boletim desatualizado:</strong> gerado há ' + Math.round(horas) + ' horas. A atualização automática pode ter falhado. ' + inmet];
    if (b.automatico) {
      var hora = b.geradoEm.slice(11, 16).replace(':', 'h');
      return ['vigente', '<strong>Atualizado às ' + esc(hora) + ' de ' + esc(dataCurta(b.dia)) + '</strong>' + (b.proximaAtualizacao ? ' · próxima atualização ' + esc(b.proximaAtualizacao) : '') + '. ' +
        (b.semDados && b.semDados.length ? 'Sem previsão neste horário: ' + esc(b.semDados.map(function (p) { return p.nome; }).join(', ')) + '. ' : '') + inmet];
    }
    return ['vigente', '<strong>Boletim em vigor</strong> para ' + esc(formatarDia(b.dia)) + '. ' + inmet];
  }

  function opcoesArquivo() {
    var ids = {}, itens = [];
    indice.forEach(function (x) { ids[x.id] = true; itens.push({ id: x.id, dia: x.dia, auto: true }); });
    manuais.forEach(function (x) { if (!ids[x.id]) itens.push({ id: x.id, dia: x.dia }); });
    lacunas.forEach(function (d) { if (!ids[d]) itens.push({ id: d, dia: d, lacuna: true }); });
    itens.sort(function (a, c) { return a.dia < c.dia ? 1 : -1; });
    if (itens.length < 2) return '';
    return '<div class="og-campo max-w-xs"><label class="og-campo-rotulo" for="campoBoletim">Boletim</label><select id="campoBoletim" class="og-campo-controle og-campo-md">' +
      itens.map(function (x) { return '<option value="' + esc(x.id) + '"' + (x.lacuna ? ' disabled' : '') + (x.id === b.id ? ' selected' : '') + '>' + esc(dataCurta(x.dia)) + (x.lacuna ? ' (sem boletim)' : x.dia < HOJE ? ' (arquivo)' : '') + '</option>'; }).join('') + '</select></div>';
  }

  function montar() {
    ajustarSelecao();
    var sit = textoSituacao(), vigente = sit[0] === 'vigente';
    var opAbas = function (extra) { return '<div class="campo-abas" role="group" aria-label="Operação"' + (extra || '') + '>' + OPERACOES.map(function (o) { return '<button type="button" class="campo-aba" data-o="' + o.id + '">' + esc(o.nome) + '</button>'; }).join('') + '</div>'; };
    var mapa = b.polos && O.campoMapa
      ? '<section class="grid gap-3" aria-labelledby="campoMapaTitulo"><div class="flex flex-wrap items-baseline justify-between gap-2"><h3 id="campoMapaTitulo" class="text-2xl font-bold text-tinta">Satélite e polos agrícolas</h3>' +
        '<p class="text-sm text-tinta-suave">Os pontos mostram a operação escolhida em cada polo; toque para abrir a região.</p></div>' + opAbas() +
        '<div data-campo-mapa></div></section>'
      : '';
    alvo.innerHTML =
      '<div class="campo-situacao campo-situacao-' + sit[0] + '" data-campo-situacao>' + sit[1] + '</div>' +
      '<div class="flex flex-wrap items-end justify-between gap-4">' +
        '<div><p class="eyebrow">Boletim agrometeorológico · ' + (b.automatico ? 'automático' : 'emitido ' + esc(dataCurta(b.emitidoEm))) + '</p>' +
        '<h2 class="text-3xl sm:text-4xl font-extrabold text-tinta tracking-tight mt-2 first-letter:uppercase" data-campo-dia>' + esc(formatarDia(b.dia)) + '</h2>' +
        '<p class="text-tinta-suave mt-2 max-w-3xl">' + esc(b.resumo) + '</p></div>' + opcoesArquivo() +
      '</div>' +
      (b.alerta ? '<div class="campo-alerta"' + (vigente ? ' role="alert"' : '') + '><strong>' + esc(b.alerta.titulo) + '</strong><ul>' +
        b.alerta.itens.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>' : '') +
      mapa +
      '<section aria-labelledby="campoPainelTitulo" class="grid gap-3">' +
        '<div class="flex flex-wrap items-baseline justify-between gap-2"><h3 id="campoPainelTitulo" class="text-2xl font-bold text-tinta">Painel de decisão</h3>' +
        '<div class="flex flex-wrap gap-3 text-sm" aria-label="Legenda">' + selo('ok') + selo('atencao') + selo('evitar') + '</div></div>' +
        '<div class="campo-matriz-rolagem"><table class="campo-matriz"><thead><tr><th scope="col">Região</th>' +
        OPERACOES.map(function (o) { return '<th scope="col">' + esc(o.nome) + '</th>'; }).join('') + '</tr></thead><tbody>' +
        b.regioes.map(function (r) {
          return '<tr data-r="' + esc(r.id) + '"><th scope="row">' + esc(r.nome) + '<small>' + esc(r.uf.split(' · ').slice(0, 3).join(' · ')) + '</small></th>' +
            OPERACOES.map(function (o) {
              var s = r.ops[o.id][0];
              return '<td><button type="button" class="campo-celula" data-r="' + esc(r.id) + '" data-o="' + o.id + '" aria-label="' + esc(r.nome + ', ' + o.nome + ': ' + ESTADOS[s].rotulo) + '">' + selo(s) + '</button></td>';
            }).join('') + '</tr>';
        }).join('') + '</tbody></table></div>' +
      '</section>' +
      '<section class="og-cartao campo-detalhe" aria-labelledby="campoRegiao" id="campoDetalhe">' +
        '<div class="campo-coluna">' +
          '<div class="campo-abas" role="group" aria-label="Região">' + b.regioes.map(function (r) { return '<button type="button" class="campo-aba" data-r="' + esc(r.id) + '">' + esc(r.nome) + '</button>'; }).join('') + '</div>' +
          '<div><p class="eyebrow" data-campo-uf></p><h3 id="campoRegiao" class="text-2xl font-bold text-tinta mt-1"></h3></div>' +
          '<div class="campo-fatos" data-campo-fatos></div>' +
          '<div class="flex flex-wrap gap-2" data-campo-alertas></div>' +
          '<div class="grid gap-2"><p class="eyebrow">Condição ao longo do dia na região (horário de Brasília)</p>' +
            '<div class="campo-dia" role="img" data-campo-linha></div>' +
            '<div class="campo-horas" aria-hidden="true"><span>00h</span><span>06h</span><span>10h</span><span>12h</span><span>15h</span><span><span>18h</span><span>24h</span></span></div>' +
            '<p class="text-sm text-tinta-suave" data-campo-nota></p></div>' +
        '</div>' +
        '<div class="campo-coluna">' +
          opAbas() +
          '<div class="campo-recomendacao" aria-live="polite" data-campo-rec></div>' +
          (b.polos ? '<div class="grid gap-2" data-campo-polo-bloco><p class="eyebrow">Hora a hora no polo</p><div class="campo-abas" role="group" aria-label="Polo" data-campo-polos></div>' +
            '<div class="campo-horaria" role="img" data-campo-horaria></div><div class="campo-horaria-rotulos" aria-hidden="true"><span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>23h</span></div>' +
            '<p class="text-sm text-tinta-suave" data-campo-polo-txt></p></div>' : '') +
          '<div><p class="eyebrow">Todas as operações nesta região</p><div class="campo-todas" data-campo-todas></div></div>' +
        '</div>' +
      '</section>' +
      (b.proximos ? proximosHtml() : '') +
      '<section aria-labelledby="campoTendencia" class="grid gap-3"><h3 id="campoTendencia" class="text-2xl font-bold text-tinta">' + (b.proximos ? 'Resumo da semana' : 'Próximos dias') + '</h3>' +
        '<div class="campo-tendencia">' + (b.tendencia || []).map(function (t, i) {
          return '<article' + (i === 0 ? ' class="agora"' : '') + '><p class="eyebrow font-mono">' + esc(t.quando) + '</p><h4 class="font-bold text-tinta text-lg">' + esc(t.titulo) + '</h4><p class="text-tinta-suave">' + esc(t.texto) + '</p></article>';
        }).join('') + '</div></section>' +
      (b.criterios ? '<section class="grid gap-3" aria-labelledby="campoCriterios"><h3 id="campoCriterios" class="text-2xl font-bold text-tinta">Critérios por operação</h3><ul class="campo-criterios">' +
        b.criterios.map(function (c) {
          var nome = OPERACOES.filter(function (o) { return o.id === c.op; })[0];
          return '<li><strong>' + esc(nome ? nome.nome : c.op) + ':</strong> ' + esc(c.texto) + ' <span class="text-tinta-suave">Fonte: ' + esc(c.fonte) + '.</span>' +
            (c.validado ? '' : ' <span class="og-selo og-selo-pendente">pendente de validação</span>') + '</li>';
        }).join('') + '</ul></section>' : '') +
      '<div class="grid grid-cols-1 md:grid-cols-2 gap-8">' +
        '<section class="grid gap-3 content-start" aria-labelledby="campoConfianca"><h3 id="campoConfianca" class="text-2xl font-bold text-tinta">Confiança da previsão</h3><ul class="campo-lista">' +
          b.confianca.map(function (c) { return '<li><strong>' + esc(c.rotulo) + '</strong> ' + esc(c.texto) + '</li>'; }).join('') +
          '<li>Confira os avisos do seu município em <a class="og-link" href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">alertas2.inmet.gov.br</a>.</li></ul></section>' +
        '<section class="grid gap-3 content-start" aria-labelledby="campoFontes"><h3 id="campoFontes" class="text-2xl font-bold text-tinta">Fontes</h3><ul class="campo-lista" data-campo-fontes>' +
          b.fontes.map(function (f) { return '<li><a class="og-link" href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.rotulo) + '</a></li>'; }).join('') + '</ul></section>' +
      '</div>';

    var sel = document.getElementById('campoBoletim');
    if (sel) sel.addEventListener('change', function () { trocar(sel.value); });
    if (b.polos && O.campoMapa) {
      O.campoMapa.montar(alvo.querySelector('[data-campo-mapa]'), {
        polos: b.polos,
        estado: function (p) { return p.ops[selO] ? p.ops[selO].estado : 'ok'; },
        rotulo: function (p) { var o = p.ops[selO]; return p.nome + ' (' + p.uf + '): ' + ESTADOS[o.estado].rotulo + (o.janela ? ', ' + (o.tipoJanela === 'ok' ? 'janela ' : 'com restrição ') + o.janela : ''); },
        aoEscolher: function (p) {
          selR = p.regiao; selP = p.id; desenhar();
          var calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          document.getElementById('campoDetalhe').scrollIntoView({ behavior: calmo ? 'auto' : 'smooth', block: 'start' });
        }
      });
    }
    desenhar();
  }

  function proximosHtml() {
    var p = b.proximos;
    return '<section class="grid gap-3" aria-labelledby="campoProximos"><h3 id="campoProximos" class="text-2xl font-bold text-tinta">Próximos 7 dias</h3>' +
      '<div class="campo-matriz-rolagem"><table class="campo-matriz campo-semana"><thead><tr><th scope="col">Região</th>' +
      p.dias.map(function (d) {
        var dt = new Date(d + 'T12:00:00Z');
        return '<th scope="col">' + (d === HOJE ? 'hoje' : DSEM[dt.getUTCDay()]) + '<small>' + esc(dataCurta(d).slice(0, 5)) + '</small></th>';
      }).join('') + '</tr></thead><tbody>' +
      p.regioes.map(function (r) {
        return '<tr><th scope="row">' + esc(r.nome) + '</th>' + r.dias.map(function (d) {
          if (!d.familia) return '<td class="campo-dia-sem">—</td>';
          return '<td><span class="campo-tempo campo-tempo-' + esc(d.familia) + '">' + esc(d.rotulo) + '</span>' +
            '<span class="campo-temp">' + esc(d.max) + '° <small>' + esc(d.min) + '°</small></span>' +
            '<span class="campo-mm">' + (d.chuva >= 1 ? esc(d.chuva) + ' mm' : 'sem chuva') + '</span></td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="text-xs text-tinta-fraca">Máxima e mínima: extremos entre os polos da região. Chuva: polo mais chuvoso. Do terceiro dia em diante a previsão é por blocos de 6 horas.</p></section>';
  }

  function desenhar() {
    var r = regiaoDe(selR), o = OPERACOES.filter(function (x) { return x.id === selO; })[0];
    var q = function (s) { return alvo.querySelector(s); };
    Array.prototype.forEach.call(alvo.querySelectorAll('.campo-matriz tbody tr[data-r]'), function (tr) { tr.classList.toggle('selecionada', tr.getAttribute('data-r') === selR); });
    Array.prototype.forEach.call(alvo.querySelectorAll('.campo-celula'), function (c) {
      var ativa = c.getAttribute('data-r') === selR && c.getAttribute('data-o') === selO;
      c.classList.toggle('ativa', ativa);
      c.setAttribute('aria-pressed', String(ativa));
    });
    Array.prototype.forEach.call(alvo.querySelectorAll('.campo-aba'), function (a) {
      var v = a.getAttribute('data-r') || a.getAttribute('data-o') || a.getAttribute('data-p');
      var atual = a.hasAttribute('data-r') ? selR : a.hasAttribute('data-o') ? selO : selP;
      a.setAttribute('aria-pressed', String(v === atual));
    });
    q('[data-campo-uf]').textContent = r.uf;
    q('#campoRegiao').textContent = r.nome;
    q('[data-campo-fatos]').innerHTML = [['Céu', r.ceu], ['Temperatura', r.temp], ['Chuva', r.chuva], ['Vento', r.vento]]
      .map(function (f) { return '<div class="campo-fato"><span class="eyebrow">' + f[0] + '</span><span>' + esc(f[1]) + '</span></div>'; }).join('');
    q('[data-campo-alertas]').innerHTML = (r.alertas || []).map(function (a) { return selo(a[0], a[1]); }).join('');
    var linha = q('[data-campo-linha]');
    linha.innerHTML = r.dia.map(function (s, i) {
      var e = ESTADOS[s];
      return '<div class="campo-' + (e ? s : 'passado') + '" title="' + PERIODOS[i] + ': ' + (e ? e.rotulo : 'já passou') + '">' + (e ? e.icone : '·') + '</div>';
    }).join('');
    linha.setAttribute('aria-label', r.dia.map(function (s, i) { return PERIODOS[i] + ' ' + (ESTADOS[s] ? ESTADOS[s].rotulo : 'já passou'); }).join('; '));
    q('[data-campo-nota]').textContent = r.nota;
    var op = r.ops[o.id];
    q('[data-campo-rec]').innerHTML = '<div class="flex flex-wrap items-center gap-2"><h4 class="text-lg font-bold text-tinta">' + esc(o.nome) + '</h4>' + selo(op[0]) + '</div>' + (resumoSemEstado(op[1]) ? '<p>' + esc(resumoSemEstado(op[1])) + '</p>' : '') + (op[2] ? '<p class="text-sm">' + esc(op[2]) + '</p>' : '');
    q('[data-campo-todas]').innerHTML = OPERACOES.map(function (x) { return '<div>' + selo(r.ops[x.id][0], x.nome) + '<span>' + esc(r.ops[x.id][1]) + '</span></div>'; }).join('');
    if (b.polos) {
      q('[data-campo-polos]').innerHTML = (r.polos || []).map(function (id) {
        var p = poloDe(id);
        return p ? '<button type="button" class="campo-aba" data-p="' + esc(p.id) + '" aria-pressed="' + (p.id === selP) + '">' + esc(p.nome) + ' · ' + esc(p.uf) + '</button>' : '';
      }).join('');
      var p = poloDe(selP), po = p && p.ops[selO], h = q('[data-campo-horaria]');
      if (p && po) {
        var celulas = [];
        for (var hh = 0; hh < 24; hh++) {
          var s = (po.porHora || {})[hh], e = ESTADOS[s];
          celulas.push('<div class="campo-' + (e ? s : 'passado') + '" title="' + (hh < 10 ? '0' : '') + hh + 'h: ' + (e ? e.rotulo : 'sem previsão (já passou)') + '"></div>');
        }
        h.innerHTML = celulas.join('');
        h.setAttribute('aria-label', o.nome + ' em ' + p.nome + ', hora a hora: ' + celulas.length + ' horas; ' + (po.janela ? (po.tipoJanela === 'ok' ? 'janela favorável ' : 'janela com restrição ') + po.janela : 'sem janela') + '.');
        q('[data-campo-polo-txt]').textContent = p.nome + ': ' + ESTADOS[po.estado].rotulo.toLowerCase() + '. ' +
          (po.janela ? (po.tipoJanela === 'ok' ? 'Janela favorável das ' : 'Janela com restrição das ') + po.janela + '.' : 'Sem janela no dia.') +
          (po.motivo && po.estado !== 'ok' ? ' Motivo mais frequente: ' + po.motivo + '.' : '') +
          (po.horasPrevistas != null && po.horasPrevistas < 16 ? ' Previsão para ' + po.horasPrevistas + ' das 16 horas úteis (05h às 20h).' : '');
      }
    }
    if (b.polos && O.campoMapa) O.campoMapa.atualizar();
    try { localStorage.setItem('orgatec.campo', JSON.stringify({ r: selR, o: selO, p: selP })); } catch (e) { /* sem memória: só nesta visita */ }
  }

  function trocar(id) {
    var pronto = function (novo) {
      b = novo; params.set('boletim', b.id);
      history.replaceState(null, '', '?' + params.toString());
      montar();
    };
    if (carregados[id]) return pronto(carregados[id]);
    var m = manuais.filter(function (x) { return x.id === id; })[0];
    var item = indice.filter(function (x) { return x.id === id; })[0];
    if (item) json(BASE + item.arquivo).then(function (x) { if (!validar(x).length) { carregados[id] = x; pronto(x); } }).catch(function () { if (m) pronto(m); });
    else if (m) pronto(m);
  }

  alvo.addEventListener('click', function (ev) {
    var bt = ev.target.closest('button[data-r], button[data-o], button[data-p]');
    if (!bt) return;
    if (bt.hasAttribute('data-r')) { selR = bt.getAttribute('data-r'); selP = null; }
    if (bt.hasAttribute('data-o')) selO = bt.getAttribute('data-o');
    if (bt.hasAttribute('data-p')) selP = bt.getAttribute('data-p');
    ajustarSelecao();
    desenhar();
    if (bt.classList.contains('campo-celula') && window.innerWidth < 820) {
      var calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      document.getElementById('campoDetalhe').scrollIntoView({ behavior: calmo ? 'auto' : 'smooth', block: 'start' });
    }
  });

  // Boletim automático publicado (mesma origem); sem ele, o manual mais recente
  Promise.all([json(BASE + 'atual.json').catch(function () { return null; }), json(BASE + 'indice.json').catch(function () { return null; })])
    .then(function (r) {
      var atual = r[0] && !validar(r[0]).length ? r[0] : null;
      indice = (r[1] && r[1].boletins) || [];
      lacunas = (r[1] && r[1].lacunas) || [];
      if (atual) carregados[atual.id] = atual;
      lista = (atual ? [atual] : []).concat(manuais);
      b = escolher(lista, params.get('boletim'));
      var pedido = params.get('boletim');
      if (pedido && (!b || b.id !== pedido) && indice.some(function (x) { return x.id === pedido; })) { b = b || atual; montar(); return trocar(pedido); }
      if (!b) { alvo.innerHTML = '<p class="og-cartao-texto">Nenhum boletim publicado. Consulte os avisos do INMET em <a class="og-link" href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">alertas2.inmet.gov.br</a>.</p>'; return; }
      montar();
    });
  return api;
});
