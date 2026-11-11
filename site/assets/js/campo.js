/* Janela de Campo: validação e vigência dos boletins (puro, testável no Node) e a tela de
   site/rural/janela-de-campo.html (só no navegador, em [data-campo]). Lê o boletim automático publicado em
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
  var VD = O.campoVeredito;  // veredito do dia e faixa horária (campo-veredito.js, carregado antes)

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
  var orientAberta = true;  // a orientação da operação escolhida abre dentro do cartão
  var selR = pref.r, selO = OPERACOES.some(function (o) { return o.id === pref.o; }) ? pref.o : OPERACOES[0].id, selP = pref.p, selA = typeof pref.a === 'string' ? pref.a : '';  // selA: atividade do produtor

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

  /* 'vigente', 'vencido' (o dia previsto já passou) ou 'desatualizado' (gerado há mais de LIMITE_HORAS). */
  function vigencia() {
    if (situacao(b, HOJE) !== 'vigente') return 'vencido';
    var horas = horasDesde(b, Date.now());
    return horas != null && horas > LIMITE_HORAS ? 'desatualizado' : 'vigente';
  }

  function textoSituacao() {
    var vig = vigencia(), horas = horasDesde(b, Date.now());
    var inmet = '<a href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">INMET</a>';
    if (vig === 'vencido') return ['vencido', '<strong>Boletim vencido: arquivo de ' + esc(dataCurta(b.dia)) + '.</strong> Não use para decidir o trabalho de hoje. Avisos oficiais: ' + inmet + '.'];
    if (vig === 'desatualizado') return ['vencido', '<strong>Boletim desatualizado:</strong> gerado há ' + Math.round(horas) + ' horas. A atualização automática pode ter falhado. Avisos oficiais: ' + inmet + '.'];
    var ponto = '<span class="campo-ponto" aria-hidden="true"></span>';
    if (b.automatico) {
      var hora = b.geradoEm.slice(11, 16).replace(':', 'h');
      var prox = b.proximaAtualizacao ? ' · próxima ' + esc(String(b.proximaAtualizacao).replace(/^hoje às /, '')) : '';
      return ['vigente', ponto + '<strong>Vigente</strong> · atualizado ' + esc(hora) + prox + ' · ' + inmet +
        (b.semDados && b.semDados.length ? ' Sem previsão neste horário: ' + esc(b.semDados.map(function (p) { return p.nome; }).join(', ')) + '.' : '')];
    }
    return ['vigente', ponto + '<strong>Boletim em vigor</strong> para ' + esc(formatarDia(b.dia)) + '. Avisos oficiais: ' + inmet + '.'];
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

  /* Glifos de estado: forma + ícone + cor (cheio com ✓, vazado com !, cheio com ✕, pontilhado com –). Só SVG inline. */
  function glifoSvg(e) {
    var corpo = {
      ok: '<circle cx="12" cy="12" r="11"/><path d="M7 12.5l3.2 3.2L17 8.8"/>',
      atencao: '<circle cx="12" cy="12" r="10"/><path d="M12 7v6"/><circle class="ponto" cx="12" cy="16.6" r="1.4"/>',
      evitar: '<circle cx="12" cy="12" r="11"/><path d="M8 8l8 8M16 8l-8 8"/>',
      sem: '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/>'
    }[e] || '';
    return '<svg class="glifo glifo-' + (corpo ? e : 'sem') + '" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + (corpo || '<circle cx="12" cy="12" r="10"/>') + '</svg>';
  }

  function dataBarra() {
    var d = new Date(b.dia + 'T12:00:00Z'), dia = DSEM[d.getUTCDay()];
    return dia.charAt(0).toUpperCase() + dia.slice(1) + ' ' + dataCurta(b.dia).slice(0, 5);
  }

  function folhaHtml() {
    return '<dialog class="campo-folha" data-campo-folha aria-labelledby="campoFolhaTitulo"><div class="campo-folha-corpo">' +
      '<div class="campo-folha-topo"><h3 id="campoFolhaTitulo" class="text-lg font-bold text-tinta">Onde você trabalha</h3>' +
        '<button type="button" class="campo-folha-fechar" data-campo-fechar aria-label="Fechar">✕</button></div>' +
      '<div class="campo-seletor" data-campo-seletor>' +
        '<div class="grid gap-1"><p class="eyebrow">Região</p><div class="campo-abas" role="group" aria-label="Região">' +
          b.regioes.map(function (r) { return '<button type="button" class="campo-aba" data-r="' + esc(r.id) + '">' + esc(r.nome) + '</button>'; }).join('') + '</div></div>' +
        (b.polos ? '<div class="grid gap-1"><p class="eyebrow">Polo</p><div class="campo-abas" role="group" aria-label="Polo" data-campo-polos></div></div>' : '') +
      '</div></div></dialog>';
  }
  function abrirFolha() {
    var d = alvo.querySelector('[data-campo-folha]');
    if (!d || d.open) return;
    if (typeof d.showModal === 'function') d.showModal(); else d.setAttribute('open', '');
  }
  function fecharFolha() {
    var d = alvo.querySelector('[data-campo-folha]');
    if (!d || !d.open) return;
    if (typeof d.close === 'function') d.close(); else d.removeAttribute('open');
  }

  /* A barra do local gruda sob o cabeçalho do site; ao grudar, mostra os cinco glifos do dia (classe "fixo"). */
  var ioBarra = null;
  function observarBarra() {
    if (ioBarra) ioBarra.disconnect();
    var s = alvo.querySelector('[data-campo-sentinela]'), bar = alvo.querySelector('[data-campo-barra]');
    if (!s || !bar || !('IntersectionObserver' in window)) return;
    ioBarra = new IntersectionObserver(function (es) {
      var e = es[es.length - 1];
      bar.classList.toggle('fixo', !e.isIntersecting && e.boundingClientRect.top < 0);
    }, { rootMargin: '-84px 0px 0px 0px' });
    ioBarra.observe(s);
  }

  var abaAtiva = 'horas';
  var mapaMontado = false;
  var largo = window.matchMedia ? window.matchMedia('(min-width: 1024px)') : { matches: false };

  function criteriosHtml() {
    return b.criterios ? '<section class="grid gap-3" aria-labelledby="campoCriterios"><h3 id="campoCriterios" class="text-xl font-bold text-tinta">Critérios por operação</h3><ul class="campo-criterios">' +
      b.criterios.map(function (c) {
        var nome = OPERACOES.filter(function (o) { return o.id === c.op; })[0];
        return '<li><strong>' + esc(nome ? nome.nome : c.op) + ':</strong> ' + esc(c.texto) + ' <span class="text-tinta-suave">Fonte: ' + esc(c.fonte) + '.</span>' +
          (c.validado ? '' : ' <span class="og-selo og-selo-pendente">pendente de validação</span>') + '</li>';
      }).join('') + '</ul></section>' : '';
  }

  function confiancaEFontesHtml() {
    return '<div class="grid grid-cols-1 md:grid-cols-2 gap-6">' +
      '<section class="grid gap-3 content-start" aria-labelledby="campoConfianca"><h3 id="campoConfianca" class="text-xl font-bold text-tinta">Confiança da previsão</h3><ul class="campo-lista">' +
        b.confianca.map(function (c) { return '<li><strong>' + esc(c.rotulo) + '</strong> ' + esc(c.texto) + '</li>'; }).join('') +
        '<li>Confira os avisos do seu município em <a class="og-link" href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">alertas2.inmet.gov.br</a>.</li></ul></section>' +
      '<section class="grid gap-3 content-start" aria-labelledby="campoFontes"><h3 id="campoFontes" class="text-xl font-bold text-tinta">Fontes</h3><ul class="campo-lista" data-campo-fontes>' +
        b.fontes.map(function (f) { return '<li><a class="og-link" href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.rotulo) + '</a></li>'; }).join('') + '</ul></section>' +
    '</div>';
  }

  /* Grade região x operação só com glifos (cabe em 320 px, sem rolar para o lado). Colunas iguais em todas as regiões são ditas
     uma vez, em vez de repetir o mesmo glifo seis vezes. */
  var ABREV = { pulv: 'Pulv.', plantio: 'Plant.', colheita: 'Colh.', animais: 'Anim.', maquinas: 'Máq.' };  // cabeçalho da grade em telas de 320 px
  function matrizHtml() {
    var linhas = b.regioes.map(function (r) { return VD.itensDaRegiao(r); });
    var cols = VD.colunasIguais(linhas), igual = VD.fraseIguais(cols);
    var rot = function (e) { return VD.ROTULOS[e] || 'sem previsão'; };
    return '<div class="campo-legenda-glifos" aria-label="Legenda">' + ['ok', 'atencao', 'evitar', 'sem'].map(function (e) {
        return '<span>' + glifoSvg(e) + esc(rot(e).charAt(0).toUpperCase() + rot(e).slice(1)) + '</span>'; }).join('') + '</div>' +
      '<div class="campo-matriz-rolagem"><table class="campo-matriz campo-regioes"><thead><tr><th scope="col">Região</th>' +
      OPERACOES.map(function (o, k) {
        return '<th scope="col"><span class="campo-col-largo" aria-hidden="true">' + esc(VD.OPS[k].curto) + '</span><span class="campo-col-estreito" aria-hidden="true">' + esc(ABREV[o.id]) + '</span><span class="sr-only">' + esc(o.nome) + '</span>' +
          (cols[k].igual ? '<small class="campo-igual">igual em todas</small>' : '') + '</th>';
      }).join('') + '</tr></thead><tbody>' +
      b.regioes.map(function (r, i) {
        return '<tr data-r="' + esc(r.id) + '"><th scope="row"><button type="button" class="campo-regiao" data-r="' + esc(r.id) + '">' + esc(r.nome) +
          '<small>' + esc(r.uf.split(' · ').slice(0, 3).join(' · ')) + '</small></button></th>' +
          OPERACOES.map(function (o, k) {
            var s = linhas[i][k].estado;
            return '<td><button type="button" class="campo-celula" data-r="' + esc(r.id) + '" data-o="' + o.id + '" aria-label="' + esc(r.nome + ', ' + o.nome + ': ' + rot(s)) + '">' + glifoSvg(s) + '</button></td>';
          }).join('') + '</tr>';
      }).join('') + '</tbody></table></div>' +
      (igual ? '<p class="campo-igual-texto">' + esc(igual) + '</p>' : '');
  }

  function painelHoras() {
    return '<div class="campo-fatos" data-campo-fatos></div>' +
      '<div class="grid gap-2"><p class="eyebrow">Condição ao longo do dia na região (horário de Brasília)</p>' +
        '<div class="campo-dia" role="img" data-campo-linha></div>' +
        '<div class="campo-horas" aria-hidden="true"><span>00h</span><span>06h</span><span>10h</span><span>12h</span><span>15h</span><span><span>18h</span><span>24h</span></span></div>' +
        '<p class="text-sm text-tinta-suave" data-campo-nota></p></div>' +
      (b.polos ? '<div class="grid gap-2" data-campo-polo-bloco><p class="eyebrow">Hora a hora no polo escolhido</p>' +
        '<div class="campo-horaria" role="img" data-campo-horaria></div><div class="campo-horaria-rotulos" aria-hidden="true"><span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>23h</span></div>' +
        '<p class="text-sm text-tinta-suave" data-campo-polo-txt></p></div>' : '');
  }

  function painelSemana() {
    return (b.proximos ? proximosHtml() : '') +
      '<section aria-labelledby="campoTendencia" class="grid gap-3"><h3 id="campoTendencia" class="text-xl font-bold text-tinta">' + (b.proximos ? 'Resumo da semana' : 'Próximos dias') + '</h3>' +
        '<div class="campo-tendencia">' + (b.tendencia || []).map(function (t, i) {
          return '<article' + (i === 0 ? ' class="agora"' : '') + '><p class="eyebrow font-mono">' + esc(t.quando) + '</p><h4 class="font-bold text-tinta text-lg">' + esc(t.titulo) + '</h4><p class="text-tinta-suave">' + esc(t.texto) + '</p></article>';
        }).join('') + '</div></section>';
  }

  function painelSatelite() {
    return '<h3 id="campoMapaTitulo" class="text-xl font-bold text-tinta">Satélite e polos agrícolas</h3>' +
      '<p class="text-sm text-tinta-suave">Os pontos mostram a operação escolhida em cada polo; toque para abrir a região.</p>' +
      '<div class="campo-abas" role="group" aria-label="Operação no mapa">' + OPERACOES.map(function (o) { return '<button type="button" class="campo-aba" data-o="' + o.id + '">' + esc(o.nome) + '</button>'; }).join('') + '</div>' +
      '<div data-campo-mapa></div>';
  }

  function painelComo() {
    return '<p class="text-tinta-suave">' + esc(b.resumo) + '</p>' + opcoesArquivo() + criteriosHtml() + confiancaEFontesHtml();
  }

  /* O mapa só é montado quando aparece (aba Satélite no celular; sempre visível no desktop): as imagens da NASA não pesam
     na abertura da página. */
  function garantirMapa() {
    var pos = alvo.querySelector('[data-campo-mapa]');
    if (mapaMontado || !pos || !b.polos || !O.campoMapa) return;
    mapaMontado = true;
    O.campoMapa.montar(pos, {
      divisas: alvo.getAttribute('data-campo-divisas') || null,
      polos: b.polos,
      estado: function (p) { return p.ops[selO] ? p.ops[selO].estado : 'ok'; },
      rotulo: function (p) { var o = p.ops[selO]; return p.nome + ' (' + p.uf + '): ' + ESTADOS[o.estado].rotulo + (o.janela ? ', ' + (o.tipoJanela === 'ok' ? 'janela ' : 'com restrição ') + o.janela : ''); },
      aoEscolher: function (p) {
        selR = p.regiao; selP = p.id; desenhar();
        var calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        document.getElementById('campoHoje').scrollIntoView({ behavior: calmo ? 'auto' : 'smooth', block: 'start' });
      }
    });
    O.campoMapa.atualizar();
  }

  function abrirAba(id, foco) {
    abaAtiva = id;
    Array.prototype.forEach.call(alvo.querySelectorAll('[data-aba]'), function (t) {
      var on = t.getAttribute('data-aba') === id;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && foco) t.focus();
    });
    Array.prototype.forEach.call(alvo.querySelectorAll('[data-painel]'), function (p) { p.hidden = p.getAttribute('data-painel') !== id; });
    if (id === 'satelite') garantirMapa();
  }

  function montar() {
    ajustarSelecao();
    mapaMontado = false;
    var sit = textoSituacao(), vigente = sit[0] === 'vigente';
    alvo.classList.toggle('campo-arquivo', !vigente);  // boletim vencido ou desatualizado: tudo em cinza, só para consulta
    var temMapa = !!(b.polos && O.campoMapa);
    var abas = [['horas', 'Horas', painelHoras()], ['semana', b.proximos ? '7 dias' : 'Próximos dias', painelSemana()]];
    if (temMapa) abas.push(['satelite', 'Satélite', painelSatelite()]);
    abas.push(['como', 'Como decidimos', painelComo()]);
    if (!abas.some(function (a) { return a[0] === abaAtiva; })) abaAtiva = 'horas';
    alvo.innerHTML =
      '<div class="campo-situacao campo-situacao-' + sit[0] + '" data-campo-situacao>' + sit[1] + '</div>' +
      '<h2 class="sr-only" data-campo-dia>' + esc(formatarDia(b.dia)) + '</h2>' +
      (b.alerta ? '<div class="campo-alerta"' + (vigente ? ' role="alert"' : '') + '><strong>' + esc(b.alerta.titulo) + '</strong><ul>' +
        b.alerta.itens.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>' : '') +
      '<div class="campo-sentinela" data-campo-sentinela aria-hidden="true"></div>' +
      '<div class="campo-local" data-campo-barra>' +
        '<button type="button" class="campo-local-botao" data-campo-local aria-haspopup="dialog" aria-label="Escolher região e polo">' +
          '<span class="campo-local-data" data-campo-data></span><span class="campo-local-nome" data-campo-nome></span><span class="campo-local-seta" aria-hidden="true">▾</span></button>' +
        '<div class="campo-local-mini" data-campo-mini aria-hidden="true"></div>' +
      '</div>' +
      folhaHtml() +
      '<div class="campo-grade">' +
        '<div class="campo-esq">' +
          '<div class="campo-veredito" data-campo-veredito></div>' +
          '<ul class="campo-glifos" data-campo-glifos aria-label="Estado de cada operação hoje"></ul>' +
          '<section aria-labelledby="campoPolo" id="campoHoje" class="grid gap-3">' +
            '<div><h3 id="campoPolo" class="text-lg font-bold text-tinta" data-campo-titulo></h3><p class="campo-quem"><span id="campoRegiao"></span> · <span data-campo-uf></span></p></div>' +
            '<ul class="campo-hoje" data-campo-hoje></ul>' +
            '<div class="flex flex-wrap gap-2" data-campo-alertas></div>' +
          '</section>' +
        '</div>' +
        '<div class="campo-dir">' +
          '<div class="campo-abas-painel" role="tablist" aria-label="Detalhes do boletim" data-campo-abas>' +
            abas.map(function (a) { return '<button type="button" role="tab" class="campo-aba-painel" id="campoAba-' + a[0] + '" aria-controls="campoPainel-' + a[0] + '" data-aba="' + a[0] + '" aria-selected="false" tabindex="-1">' + esc(a[1]) + '</button>'; }).join('') +
          '</div>' +
          '<div class="campo-paineis">' +
            abas.map(function (a) { return '<div role="tabpanel" class="campo-painel" id="campoPainel-' + a[0] + '" aria-labelledby="campoAba-' + a[0] + '" data-painel="' + a[0] + '" tabindex="0" hidden>' + a[2] + '</div>'; }).join('') +
          '</div>' +
        '</div>' +
      '</div>' +
      '<details class="campo-comparar" data-campo-comparar' + (largo.matches ? ' open' : '') + '><summary>Comparar as regiões</summary>' + matrizHtml() + '</details>';

    var sel = document.getElementById('campoBoletim');
    if (sel) sel.addEventListener('change', function () { trocar(sel.value); });
    abrirAba(abaAtiva);
    desenhar();
    observarMapa();
    observarBarra();
  }

  /* No desktop o satélite fica à vista, mas as imagens da NASA só são pedidas quando o painel chega perto da tela
     (rolagem). No celular, quando a aba Satélite é aberta (abrirAba). */
  function observarMapa() {
    var painel = alvo.querySelector('[data-painel="satelite"]');
    if (!painel || !largo.matches) return;
    if (!('IntersectionObserver' in window)) { garantirMapa(); return; }
    var io = new IntersectionObserver(function (es) {
      if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); garantirMapa(); }
    }, { rootMargin: '300px 0px' });
    io.observe(painel);
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
    Array.prototype.forEach.call(alvo.querySelectorAll('.campo-aba, .campo-glifo'), function (a) {
      var v = a.getAttribute('data-r') || a.getAttribute('data-o') || a.getAttribute('data-p');
      var atual = a.hasAttribute('data-r') ? selR : a.hasAttribute('data-o') ? selO : selP;
      a.setAttribute('aria-pressed', String(v === atual));
    });
    q('[data-campo-uf]').textContent = r.uf;
    q('#campoRegiao').textContent = r.nome;
    var polo = b.polos ? poloDe(selP) : null, local = polo ? polo.nome : r.nome;
    var itens = polo ? VD.itensDoPolo(polo) : VD.itensDaRegiao(r), vd = VD.veredito(vigencia(), itens);
    q('[data-campo-data]').textContent = dataBarra();
    q('[data-campo-nome]').textContent = polo ? polo.nome + ' · ' + polo.uf : r.nome;
    q('[data-campo-titulo]').textContent = 'Hoje em ' + local;
    q('[data-campo-veredito]').innerHTML = '<p class="campo-veredito-titulo' + (vd.tipo === 'sem' ? ' campo-veredito-sem' : '') + '">' + esc(vd.titulo) + '</p>' +
      vd.linhas.map(function (l) { return '<p class="campo-veredito-linha">' + esc(l) + '</p>'; }).join('') +
      (vd.tipo === 'normal' ? '<p class="campo-veredito-fonte">' + vd.contagem.favoraveis + ' de ' + vd.contagem.total + ' favoráveis · ' + esc(local) +
        (vd.parcial ? ' · <span class="campo-veredito-aviso">previsão parcial: ' + vd.parcial.de + ' de ' + vd.parcial.total + ' horas</span>' : '') +
        (b.automatico ? ' · MET Norway' : '') + '</p>' : '');
    q('[data-campo-glifos]').innerHTML = vd.glifos.map(function (g) {
      var nome = OPERACOES.filter(function (x) { return x.id === g.op; })[0].nome, rot = g.estado === 'sem' ? 'sem previsão' : ESTADOS[g.estado].rotulo;
      return '<li><button type="button" class="campo-glifo campo-glifo-' + g.estado + '" data-o="' + g.op + '" aria-pressed="' + (g.op === selO) + '" aria-label="' + esc(nome + ': ' + rot) + '">' +
        glifoSvg(g.estado) + '<span>' + esc(g.curto) + '</span></button></li>';
    }).join('');
    q('[data-campo-mini]').innerHTML = vd.glifos.map(function (g) { return glifoSvg(g.estado); }).join('');
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
    q('[data-campo-hoje]').innerHTML = OPERACOES.map(function (x, i) {
      var v = r.ops[x.id], item = itens[i], aberto = x.id === selO && orientAberta;
      var leg = item.faixa ? VD.legendaJanela(item) : null;
      var celulas = item.faixa ? item.faixa.split('').map(function (c) { return '<i class="campo-h campo-h-' + c + '"></i>'; }).join('') : '';
      return '<li class="campo-card campo-card-' + item.estado + '"><button type="button" class="campo-op" data-o="' + x.id + '" aria-expanded="' + aberto + '"' + (aberto ? ' aria-controls="campoOrient"' : '') + '>' +
        '<span class="campo-op-cab"><span class="campo-op-nome">' + esc(x.nome) + '</span>' + (item.estado === 'sem' ? selo('sem', 'Sem previsão') : selo(item.estado)) + '</span>' +
        (item.faixa ? '<span class="campo-faixa" role="img" aria-label="' + esc(x.nome + ', hora a hora: ' + VD.descreverFaixa(item.faixa)) + '">' + celulas + '</span>' +
          '<span class="campo-op-eixo" aria-hidden="true"><span>05h</span><span>12h</span><span>20h</span></span>' : '') +
        '<span class="campo-op-linha">' + (leg ? '<span class="campo-op-janela">' + esc(leg.janela) + '</span><span class="campo-op-txt">' + esc(leg.texto) + '</span>'
          : '<span class="campo-op-txt">' + esc(resumoSemEstado(v[1])) + '</span>') + '</span></button>' +
        (aberto ? '<div class="campo-orient" id="campoOrient" data-campo-rec><p>' + esc(v[2] || v[1]) + '</p></div>' : '') + '</li>';
    }).join('');
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
    if (mapaMontado && O.campoMapa) O.campoMapa.atualizar();
    // nas fileiras de chips com rolagem lateral (celular), a escolha fica à vista
    Array.prototype.forEach.call(alvo.querySelectorAll('.campo-seletor .campo-aba[aria-pressed="true"]'), function (c) {
      var pai = c.parentNode;
      if (pai.scrollWidth > pai.clientWidth) pai.scrollLeft = c.offsetLeft - (pai.clientWidth - c.offsetWidth) / 2;
    });
    try { localStorage.setItem('orgatec.campo', JSON.stringify({ r: selR, o: selO, p: selP, a: selA })); } catch (e) { /* sem memória: só nesta visita */ }
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
    if (ev.target.closest('[data-campo-local]')) { abrirFolha(); return; }
    if (ev.target.closest('[data-campo-fechar]') || (ev.target.hasAttribute && ev.target.hasAttribute('data-campo-folha'))) { fecharFolha(); return; }
    var bt = ev.target.closest('button[data-r], button[data-o], button[data-p]');
    if (!bt) return;
    if (bt.hasAttribute('data-r')) { selR = bt.getAttribute('data-r'); selP = null; }
    if (bt.hasAttribute('data-o')) {
      var novaOp = bt.getAttribute('data-o');
      if (bt.classList.contains('campo-op') && novaOp === selO) orientAberta = !orientAberta;  // tocar de novo no cartão aberto recolhe
      else { selO = novaOp; orientAberta = true; }
    }
    if (bt.hasAttribute('data-p')) selP = bt.getAttribute('data-p');
    ajustarSelecao();
    desenhar();
    if (bt.hasAttribute('data-p')) fecharFolha();
    if ((bt.classList.contains('campo-celula') || bt.classList.contains('campo-regiao')) && !largo.matches) {
      var calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      document.getElementById('campoHoje').scrollIntoView({ behavior: calmo ? 'auto' : 'smooth', block: 'start' });
    }
  });

  alvo.addEventListener('click', function (ev) {
    var t = ev.target.closest('button[data-aba]');
    if (t) abrirAba(t.getAttribute('data-aba'));
  });
  // Abas: setas, Home e End movem entre as abas visíveis (padrão WAI-ARIA de tablist)
  alvo.addEventListener('keydown', function (ev) {
    var t = ev.target.closest('button[data-aba]');
    if (!t || ['ArrowLeft', 'ArrowRight', 'Home', 'End'].indexOf(ev.key) < 0) return;
    var vis = Array.prototype.filter.call(alvo.querySelectorAll('button[data-aba]'), function (x) { return x.offsetParent !== null; });
    var i = vis.indexOf(t);
    i = ev.key === 'Home' ? 0 : ev.key === 'End' ? vis.length - 1 : (i + (ev.key === 'ArrowRight' ? 1 : -1) + vis.length) % vis.length;
    ev.preventDefault();
    abrirAba(vis[i].getAttribute('data-aba'), true);
  });
  if (largo.addEventListener) largo.addEventListener('change', function () {
    if (!b || !largo.matches) return;
    if (abaAtiva === 'satelite') abrirAba('horas');  // no desktop o satélite fica sempre à vista, sem aba
    garantirMapa();
    var d = alvo.querySelector('[data-campo-comparar]');
    if (d) d.open = true;
  });

  // "Minha atividade": o link das cotações e notícias abre o card da atividade escolhida (a escolha fica só neste navegador,
  // na mesma chave orgatec.campo da região e do polo)
  (function () {
    var selAtv = document.querySelector('[data-minha-atividade]'), lnk = document.querySelector('a[data-agro-mercado]');
    if (!selAtv || !lnk) return;
    var base = lnk.getAttribute('href');
    if (selA && Array.prototype.some.call(selAtv.options, function (o) { return o.value === selA; })) selAtv.value = selA;
    function aplicar() {
      selA = selAtv.value;
      lnk.setAttribute('href', selA ? base + '#agro-' + selA : base);
      try { localStorage.setItem('orgatec.campo', JSON.stringify({ r: selR, o: selO, p: selP, a: selA })); } catch (e) { /* sem memória: só nesta visita */ }
    }
    selAtv.addEventListener('change', aplicar);
    lnk.setAttribute('href', selAtv.value ? base + '#agro-' + selAtv.value : base);
  })();

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
