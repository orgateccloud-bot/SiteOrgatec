/* Itens de conteúdo da reforma: validação, filtro e renderização a partir de dados (reforma-itens.js).
   Funções puras, testáveis no Node (tests/js/conteudo.test.js). Toda afirmação legal sai com a fonte
   (fontes.js), a data de consulta e o status. Em produção, só aparecem itens com revisão técnica aprovada. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).conteudo = factory();
})(this, function () {
  'use strict';

  var STATUS = {
    em_vigor: { rotulo: 'Em vigor', tom: 'definido' },
    vigencia_futura: { rotulo: 'Aprovado, vigência futura', tom: 'futuro' },
    pendente_regulamentacao: { rotulo: 'Pendente de regulamentação', tom: 'pendente' },
    incerto: { rotulo: 'Incerto: não verificado', tom: 'pendente' }
  };
  var SETORES = { todos: 'Todos os setores', agro: 'Agro', transporte: 'Transporte' };
  var TRIBUTOS = { cbs: 'CBS', ibs: 'IBS', is: 'Imposto Seletivo', piscofins: 'PIS/Cofins', ipi: 'IPI', icms: 'ICMS', iss: 'ISS', irpf: 'IRPF' };
  var DESTINOS = ['home', 'tributario', 'reforma', 'noticias', 'setor-agro', 'setor-transporte', 'ferramentas', 'cliente',
    'compliance', 'compliance-tributario', 'compliance-pld', 'compliance-lgpd', 'compliance-integridade'];
  /* Frentes da área de Compliance (compliance-itens.js). Item com `pilar` pode ter `tributos` vazio.
     'transporte' reúne as obrigações setoriais do transportador (ANTT, jornada); aparece na página do público. */
  var PILARES = { tributario: 'Conformidade tributária', pld: 'Prevenção à lavagem de dinheiro', lgpd: 'Proteção de dados (LGPD)', integridade: 'Integridade e anticorrupção',
    transporte: 'Obrigações do transportador', rural: 'Obrigações do produtor rural', pequenos: 'MEI, autônomo e Simples', imoveis: 'Pessoa física com imóveis' };
  /* Públicos da área "Por público" (docs/relatorio-publicos-reforma-compliance.md). Destino de cada página: 'publico-<id>'. */
  var PUBLICOS = { transportador: 'Transportador de cargas', produtor: 'Produtor rural', mei: 'MEI', autonomo: 'Autônomo e profissional liberal',
    simples: 'Simples Nacional', servicos: 'Prestador de serviço', comercio: 'Comércio e indústria', imoveis: 'Pessoa física com imóveis' };
  Object.keys(PUBLICOS).forEach(function (p) { DESTINOS.push('publico-' + p); });
  /* Temas do agro (campo opcional `tema` do item): agrupamento editorial para a lista recolhida da página Agro; não é texto legal. */
  var TEMAS = { aliquotas: 'Alíquotas e reduções', produtor: 'Contribuinte ou não', credito: 'Crédito e insumos', obrigacoes: 'Obrigações e transição' };
  var OBRIGATORIOS = ['id', 'titulo', 'fato', 'status', 'consultadoEm', 'fontes', 'setores', 'tributos', 'destinos', 'revisao'];
  var DATA = /^(\d{4})-(\d{2})-(\d{2})$/;

  function dataValida(s) {
    var m = DATA.exec(s || '');
    if (!m) return false;
    var d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
    return d.getUTCFullYear() === +m[1] && d.getUTCMonth() === +m[2] - 1 && d.getUTCDate() === +m[3];
  }
  function dias(a, b) { return Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 864e5); }
  function formatarData(s) { var m = DATA.exec(s || ''); return m ? m[3] + '/' + m[2] + '/' + m[1] : ''; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* Erros de um item. fontesPorId: o porId de fontes.js. Lista vazia = item publicável. */
  function validarItem(item, fontesPorId) {
    var erros = [];
    if (!item || typeof item !== 'object') return ['item ausente ou inválido'];
    OBRIGATORIOS.forEach(function (c) {
      var v = item[c];
      if (c === 'tributos' && item.pilar && Array.isArray(v)) return;  // item de compliance: a frente substitui o tributo
      if (v == null || v === '' || (Array.isArray(v) && !v.length)) erros.push('campo obrigatório ausente: ' + c);
    });
    if (item.pilar != null && !PILARES[item.pilar]) erros.push('pilar inválido: ' + item.pilar);
    if (item.tema != null && !TEMAS[item.tema]) erros.push('tema inválido: ' + item.tema);
    if (item.prazo != null && !dataValida(item.prazo)) erros.push('prazo inválido: ' + item.prazo);
    if (item.status && !STATUS[item.status]) erros.push('status inválido: ' + item.status);
    if (item.consultadoEm && !dataValida(item.consultadoEm)) erros.push('data de consulta inválida: ' + item.consultadoEm);
    (item.fontes || []).forEach(function (id) { if (!fontesPorId || !fontesPorId[id]) erros.push('fonte inexistente: ' + id); });
    (item.setores || []).forEach(function (s) { if (!SETORES[s]) erros.push('setor inválido: ' + s); });
    (item.tributos || []).forEach(function (t) { if (!TRIBUTOS[t]) erros.push('tributo inválido: ' + t); });
    (item.destinos || []).forEach(function (d) { if (DESTINOS.indexOf(d) < 0) erros.push('destino inválido: ' + d); });
    if (item.revisao && ['pendente', 'aprovada'].indexOf(item.revisao.status) < 0) erros.push('revisão inválida');
    if (item.revisao && item.revisao.status === 'aprovada' && (!item.revisao.por || !dataValida(item.revisao.em)))
      erros.push('revisão aprovada exige responsável e data');
    (item.historico || []).forEach(function (h) { if (!dataValida(h.data) || !h.nota) erros.push('histórico inválido'); });
    return erros;
  }

  /* Itens com `prazo` de hoje em diante, do mais próximo ao mais distante ("Datas que pedem atenção"). */
  function proximosPrazos(itens, hoje, limite) {
    var lista = (itens || []).filter(function (it) { return it.prazo && dataValida(it.prazo) && it.prazo >= hoje; })
      .sort(function (a, b) { return a.prazo < b.prazo ? -1 : a.prazo > b.prazo ? 1 : 0; });
    return limite ? lista.slice(0, limite) : lista;
  }

  /* Itens que podem ir à tela. Inválidos nunca aparecem; em produção, só os de revisão aprovada. */
  function publicaveis(itens, fontesPorId, ambiente) {
    var ok = [], rejeitados = [];
    (itens || []).forEach(function (it) {
      var erros = validarItem(it, fontesPorId);
      if (erros.length) { rejeitados.push({ id: it && it.id, erros: erros }); return; }
      if (ambiente === 'producao' && it.revisao.status !== 'aprovada') { rejeitados.push({ id: it.id, erros: ['revisão técnica pendente'] }); return; }
      ok.push(it);
    });
    return { itens: ok, rejeitados: rejeitados };
  }

  /* Filtro por setor, tributo, status e destino. Um item de setor "todos" aparece em qualquer setor. */
  function filtrar(itens, f) {
    f = f || {};
    return itens.filter(function (it) {
      if (f.setor && f.setor !== 'todos' && it.setores.indexOf(f.setor) < 0 && it.setores.indexOf('todos') < 0) return false;
      if (f.tributo && it.tributos.indexOf(f.tributo) < 0) return false;
      if (f.status && it.status !== f.status) return false;
      if (f.destino && it.destinos.indexOf(f.destino) < 0) return false;
      if (f.tema && it.tema !== f.tema) return false;
      return true;
    });
  }

  /* Itens com consulta mais antiga que `limite` dias: lista de manutenção. */
  function atrasados(itens, hoje, limite) {
    limite = limite == null ? 90 : limite;
    return itens.filter(function (it) { return dias(it.consultadoEm, hoje) > limite; })
      .map(function (it) { return { id: it.id, consultadoEm: it.consultadoEm, dias: dias(it.consultadoEm, hoje) }; });
  }

  /* Central de notícias: entradas de histórico de todos os itens, da mais recente para a mais antiga. */
  function noticias(itens, limite) {
    var lista = [];
    itens.forEach(function (it) {
      (it.historico || []).forEach(function (h) { lista.push({ data: h.data, nota: h.nota, id: it.id, titulo: it.titulo, status: it.status }); });
    });
    lista.sort(function (a, b) { return a.data < b.data ? 1 : a.data > b.data ? -1 : 0; });
    return limite ? lista.slice(0, limite) : lista;
  }

  function selo(tom, texto) { return '<span class="og-selo og-selo-' + tom + '">' + esc(texto) + '</span>'; }

  function citacoes(ids, fontesPorId) {
    return ids.map(function (id) {
      var f = fontesPorId[id];
      var alvo = f.url ? '<a class="og-link" href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.rotulo) + '</a>' : '<span>' + esc(f.rotulo) + '</span>';
      return '<span class="og-citacao">' + alvo + (f.validado ? '' : selo('pendente', 'pendente de validação')) + '</span>';
    }).join('');
  }

  /* HTML de um item (cartão). Item inválido gera erro: quem chama deve passar por publicaveis(). */
  function renderItem(item, fontesPorId, opcoes) {
    var erros = validarItem(item, fontesPorId);
    if (erros.length) throw new Error('item ' + (item && item.id) + ' inválido: ' + erros.join('; '));
    var st = STATUS[item.status];
    var ref = item.tributos.length ? item.tributos.map(function (t) { return TRIBUTOS[t]; }).join(' · ') : (PILARES[item.pilar] || '');
    var vig = (item.vigencia ? ' · Vigência: ' + esc(item.vigencia) : '') + (item.prazo ? ' · Prazo: ' + formatarData(item.prazo) : '');
    var attrs = ' id="item-' + esc(item.id) + '" data-status="' + esc(item.status) + '" data-setores="' + esc(item.setores.join(' ')) + '" data-tributos="' + esc(item.tributos.join(' ')) + '"' +
      (item.tema ? ' data-tema="' + esc(item.tema) + '"' : '');
    var selos = selo(st.tom, st.rotulo) + (item.revisao.status === 'aprovada' ? '' : selo('pendente', 'em revisão técnica'));
    var corpo = '<p class="og-cartao-texto">' + esc(item.fato) + '</p>' +
      (item.orientacao ? '<div class="og-item-orientacao"><span class="og-item-rotulo">Orientação ORGATEC (interpretação, não é texto legal)</span><p>' + esc(item.orientacao) + '</p></div>' : '') +
      '<div class="og-item-fontes">' + citacoes(item.fontes, fontesPorId) + '</div>' +
      '<p class="og-item-meta">Consultado em ' + formatarData(item.consultadoEm) + vig + '</p>';
    if (opcoes && opcoes.recolhido) {
      // leitura sob demanda: título, status e nº de fontes à vista; fato, orientação e fontes ao abrir (nada é omitido)
      return '<details class="og-cartao og-item og-item-recolhivel"' + attrs + '><summary class="og-item-resumo">' +
        '<span class="og-item-linha"><span class="og-cartao-ref">' + esc(ref) + '</span>' + selo(st.tom, st.rotulo) + '</span>' +
        '<h3 class="og-cartao-titulo">' + esc(item.titulo) + '</h3></summary>' +
        '<div class="og-item-corpo">' + (item.revisao.status === 'aprovada' ? '' : '<p>' + selo('pendente', 'em revisão técnica') + '</p>') + corpo + '</div></details>';
    }
    return '<article class="og-cartao og-item"' + attrs + '>' +
      '<span class="og-cartao-ref">' + esc(ref) + '</span>' +
      '<h3 class="og-cartao-titulo">' + esc(item.titulo) + selos + '</h3>' +
      corpo +
      '</article>';
  }

  /* Anos de atuação para a prova de confiança. Só devolve número com data de início válida, no passado,
     E comprovação informada (config.institucional); caso contrário, null e o número não aparece. */
  function anosAtuacao(inst, hoje) {
    if (!inst || !dataValida(inst.inicioAtuacao) || !inst.comprovacao || !String(inst.comprovacao).trim()) return null;
    if (!dataValida(hoje) || inst.inicioAtuacao > hoje) return null;
    var i = inst.inicioAtuacao.split('-').map(Number), h = hoje.split('-').map(Number);
    var anos = h[0] - i[0] - ((h[1] < i[1] || (h[1] === i[1] && h[2] < i[2])) ? 1 : 0);
    return anos >= 1 ? anos : null;
  }

  return { STATUS: STATUS, SETORES: SETORES, TRIBUTOS: TRIBUTOS, DESTINOS: DESTINOS, PILARES: PILARES, PUBLICOS: PUBLICOS, TEMAS: TEMAS,
    validarItem: validarItem, publicaveis: publicaveis, filtrar: filtrar, atrasados: atrasados, proximosPrazos: proximosPrazos,
    noticias: noticias, renderItem: renderItem, citacoes: citacoes, anosAtuacao: anosAtuacao,
    formatarData: formatarData, dataValida: dataValida, esc: esc };
});
