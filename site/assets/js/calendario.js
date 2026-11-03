/* Motor do Calendário Fiscal (federal, trabalhista e estadual). Puro: sem DOM.
   Considera feriados nacionais e dias sem expediente bancário nacional
   (Carnaval, Sexta-feira Santa, Corpus Christi). Feriados estaduais e municipais
   NÃO são considerados — a interface avisa isso. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./ufs.js'), require('./fontes.js'));
  else (root.Orgatec = root.Orgatec || {}).calendario = factory(root.Orgatec.ufs, root.Orgatec.fontes);
})(this, function (UFS, FONTES) {
  'use strict';

  function pascoa(ano) { // algoritmo de Meeus/Jones/Butcher (calendário gregoriano)
    var a = ano % 19, b = Math.floor(ano / 100), c = ano % 100, d = Math.floor(b / 4), e = b % 4;
    var f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3);
    var h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4;
    var l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
    var mes = Math.floor((h + l - 7 * m + 114) / 31), dia = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(Date.UTC(ano, mes - 1, dia));
  }

  function iso(d) { return d.toISOString().slice(0, 10); }
  function somaDias(d, n) { return new Date(d.getTime() + n * 86400000); }
  function dataUTC(a, m, d) { return new Date(Date.UTC(a, m - 1, d)); }

  var cacheFeriados = {};
  function feriados(ano) {
    if (cacheFeriados[ano]) return cacheFeriados[ano];
    var p = pascoa(ano);
    var lista = {};
    // Lei 662/1949 (red. Lei 10.607/2002), Lei 6.802/1980 (12/10) e Lei 14.759/2023 (20/11).
    ['01-01', '04-21', '05-01', '09-07', '10-12', '11-02', '11-15', '11-20', '12-25'].forEach(function (md) {
      lista[ano + '-' + md] = 'Feriado nacional';
    });
    lista[iso(somaDias(p, -48))] = 'Carnaval (sem expediente bancário)';
    lista[iso(somaDias(p, -47))] = 'Carnaval (sem expediente bancário)';
    lista[iso(somaDias(p, -2))] = 'Sexta-feira Santa';
    lista[iso(somaDias(p, 60))] = 'Corpus Christi (sem expediente bancário)';
    cacheFeriados[ano] = lista;
    return lista;
  }

  function diaUtil(d, sabadoUtil) {
    var dow = d.getUTCDay();
    return dow !== 0 && (sabadoUtil || dow !== 6) && !feriados(d.getUTCFullYear())[iso(d)];
  }

  function ajustar(d, regra) {
    var passo = regra === 'prorroga' ? 1 : -1;
    while (!diaUtil(d)) d = somaDias(d, passo);
    return d;
  }

  function enesimoDiaUtil(ano, mes, n, sabadoUtil) {
    var d = dataUTC(ano, mes, 1), cont = 0;
    for (;;) {
      if (diaUtil(d, sabadoUtil)) { cont++; if (cont === n) return d; }
      d = somaDias(d, 1);
    }
  }

  function ultimoDiaUtil(ano, mes) {
    return ajustar(new Date(Date.UTC(ano, mes, 0)), 'antecipa');
  }

  function dia(n) { return function (a, m) { return dataUTC(a, m, n); }; }
  function noMes(mesAlvo, f) { return function (a, m) { return m === mesAlvo ? f(a, m) : null; }; }

  /* Regras. `quando(ano, mes)` devolve a data-base no mês (ou null se não vence no mês).
     `diaNaoUtil`: 'antecipa' | 'prorroga' | 'ja_util' (a regra já resulta em dia útil).
     `regraConfirmada: false` → a norma não fixa o que fazer em dia não útil; adotamos
     antecipar (lado seguro) e, se a data for ajustada, o item sai "pendente de validação". */
  var REGRAS = [
    { id: 'salario', esfera: 'trabalhista', titulo: 'Pagamento de salários (até o 5º dia útil, contando sábados)',
      quando: function (a, m) { return enesimoDiaUtil(a, m, 5, true); }, diaNaoUtil: 'ja_util', sabadoUtil: true, fontes: ['clt_459', 'mte_sabado'] },
    { id: 'esocial', esfera: 'trabalhista', titulo: 'eSocial — eventos periódicos (folha)',
      quando: dia(15), diaNaoUtil: 'prorroga', fontes: ['cal_esocial'] },
    { id: 'reinf', esfera: 'federal', titulo: 'EFD-Reinf — eventos periódicos',
      quando: dia(15), diaNaoUtil: 'prorroga', fontes: ['cal_reinf'] },
    { id: 'fgts', esfera: 'trabalhista', titulo: 'FGTS Digital — recolhimento mensal',
      quando: dia(20), diaNaoUtil: 'antecipa', fontes: ['cal_fgts'] },
    { id: 'inss', esfera: 'trabalhista', titulo: 'Contribuições previdenciárias (DARF da DCTFWeb)',
      quando: dia(20), diaNaoUtil: 'antecipa', fontes: ['cal_inss'] },
    { id: 'irrf', esfera: 'federal', titulo: 'IRRF — rendimentos do trabalho e demais retenções mensais',
      quando: dia(20), diaNaoUtil: 'antecipa', fontes: ['cal_irrf'] },
    { id: 'das', esfera: 'federal', titulo: 'DAS — Simples Nacional (competência anterior)', regimes: ['simples'],
      quando: dia(20), diaNaoUtil: 'prorroga', fontes: ['cal_das'] },
    { id: 'piscofins', esfera: 'federal', titulo: 'PIS/Pasep e Cofins (competência anterior)', regimes: ['presumido', 'real'],
      // PIS/Cofins extintos a partir de 2027 (ADCT, art. 126, II): último vencimento = competência 12/2026.
      quando: dia(25), diaNaoUtil: 'antecipa', fontes: ['cal_piscofins'], ateAnoMes: 202701 },
    { id: 'efdcontrib', esfera: 'federal', titulo: 'EFD-Contribuições (2º mês anterior)', regimes: ['presumido', 'real'],
      quando: function (a, m) { return enesimoDiaUtil(a, m, 10); }, diaNaoUtil: 'ja_util', fontes: ['cal_efdcontrib'], ateAnoMes: 202702 },
    // Regulamento da CBS (Decreto 12.955/2026, art. 45): último dia útil do mês seguinte ao da apuração.
    { id: 'cbs', esfera: 'federal', titulo: 'CBS — pagamento e entrega da apuração (competência anterior)', regimes: ['presumido', 'real'],
      quando: function (a, m) { return ultimoDiaUtil(a, m); }, diaNaoUtil: 'ja_util', desdeAnoMes: 202702, fontes: ['cal_cbs'] },
    { id: 'ibs', esfera: 'federal', titulo: 'IBS — apuração mensal (vencimento a ser fixado pelo Comitê Gestor do IBS)', regimes: ['presumido', 'real'],
      semData: true, desdeAnoMes: 202702, fontes: ['cal_ibs'] },
    { id: 'dctfweb', esfera: 'federal', titulo: 'DCTFWeb — transmissão (competência anterior)',
      quando: function (a, m) { return ultimoDiaUtil(a, m); }, diaNaoUtil: 'ja_util', fontes: ['cal_dctfweb'] },
    { id: 'irpjcsll', esfera: 'federal', titulo: 'IRPJ/CSLL trimestral — quota única ou 1ª quota', regimes: ['presumido', 'real'],
      quando: function (a, m) { return [1, 4, 7, 10].indexOf(m) >= 0 ? ultimoDiaUtil(a, m) : null; }, diaNaoUtil: 'ja_util', fontes: ['cal_irpj'] },
    { id: 'defis', esfera: 'federal', titulo: 'DEFIS — declaração anual do Simples Nacional', regimes: ['simples'],
      quando: noMes(3, function (a) { return dataUTC(a, 3, 31); }), diaNaoUtil: 'antecipa', regraConfirmada: false, fontes: ['cal_defis'] },
    { id: 'dasnsimei', esfera: 'federal', titulo: 'DASN-SIMEI — declaração anual do MEI', regimes: ['simples'],
      quando: noMes(5, function (a) { return dataUTC(a, 5, 31); }), diaNaoUtil: 'antecipa', regraConfirmada: false, fontes: ['cal_dasnsimei'] },
    { id: 'ecd', esfera: 'federal', titulo: 'ECD — Escrituração Contábil Digital', regimes: ['presumido', 'real'],
      quando: noMes(6, function (a) { return ultimoDiaUtil(a, 6); }), diaNaoUtil: 'ja_util', fontes: ['cal_ecd'] },
    { id: 'ecf', esfera: 'federal', titulo: 'ECF — Escrituração Contábil Fiscal', regimes: ['presumido', 'real'],
      quando: noMes(7, function (a) { return ultimoDiaUtil(a, 7); }), diaNaoUtil: 'ja_util', fontes: ['cal_ecf'] },
    { id: 'decimo1', esfera: 'trabalhista', titulo: '13º salário — 1ª parcela',
      quando: noMes(11, function (a) { return dataUTC(a, 11, 30); }), diaNaoUtil: 'antecipa', regraConfirmada: false, fontes: ['lei_4749'] },
    { id: 'decimo2', esfera: 'trabalhista', titulo: '13º salário — 2ª parcela',
      quando: noMes(12, function (a) { return dataUTC(a, 12, 20); }), diaNaoUtil: 'antecipa', regraConfirmada: false, fontes: ['lei_4749'] },
    // Compliance (docs/plano-area-compliance.md, Fase D). Datas fixas da norma, sem ajuste por dia não útil.
    { id: 'conformidade2026', esfera: 'compliance', titulo: 'Programa Nacional de Conformidade 2026 — prazo para corrigir as inconsistências',
      quando: noMes(12, function (a) { return a === 2026 ? dataUTC(a, 12, 31) : null; }), diaNaoUtil: 'ja_util', fontes: ['ato_conjunto_5_2026'] },
    { id: 'produtorcnpj2027', esfera: 'compliance', titulo: 'Produtor rural pessoa física: CNPJ e documento fiscal passam a ser obrigatórios',
      quando: noMes(1, function (a) { return a === 2027 ? dataUTC(a, 1, 1) : null; }), diaNaoUtil: 'ja_util', fontes: ['dec13075_2026'] },
    { id: 'cfcnaoocorrencia', esfera: 'compliance', titulo: 'Profissionais e organizações contábeis: comunicação de não ocorrência ao CFC (PLD)',
      quando: noMes(1, function (a) { return dataUTC(a, 1, 31); }), diaNaoUtil: 'ja_util', fontes: ['res_cfc_1721_2024'] },
    // Transportador (área Por público): prazo legal da ANTT para publicar a atualização dos pisos mínimos de frete
    { id: 'pisosfrete01', esfera: 'compliance', titulo: 'Transporte: ANTT publica a atualização dos pisos mínimos de frete (até 20/01)',
      quando: noMes(1, function (a) { return dataUTC(a, 1, 20); }), diaNaoUtil: 'ja_util', fontes: ['lei13703'] },
    { id: 'pisosfrete07', esfera: 'compliance', titulo: 'Transporte: ANTT publica a atualização dos pisos mínimos de frete (até 20/07)',
      quando: noMes(7, function (a) { return dataUTC(a, 7, 20); }), diaNaoUtil: 'ja_util', fontes: ['lei13703'] },
    // Produtor rural (área Por público)
    { id: 'funruralopcao', esfera: 'compliance', titulo: 'Produtor rural pessoa física: a opção pelo Funrural sobre a folha se faz pagando a folha de janeiro',
      quando: noMes(2, function (a) { return dataUTC(a, 2, 20); }), diaNaoUtil: 'antecipa', fontes: ['lei8212_funrural', 'cal_inss'] },
    { id: 'eudr2026', esfera: 'compliance', titulo: 'União Europeia: regulamento de produtos livres de desmatamento (EUDR) passa a valer',
      quando: noMes(12, function (a) { return a === 2026 ? dataUTC(a, 12, 30) : null; }), diaNaoUtil: 'ja_util', fontes: ['ue_eudr'] },
    { id: 'eudr2027', esfera: 'compliance', titulo: 'União Europeia: EUDR passa a valer para micro e pequenas empresas criadas até 31/12/2024',
      quando: noMes(6, function (a) { return a === 2027 ? dataUTC(a, 6, 30) : null; }), diaNaoUtil: 'ja_util', fontes: ['ue_eudr'] },
    // MEI e Simples (área Por público). Janelas da LC 123, art. 13, § 10: o mês todo, na forma do CGSN; a data marca o fim do mês.
    { id: 'simplesjanela03', esfera: 'compliance', titulo: 'Simples Nacional: fim da janela de março para optar pelo IBS e pela CBS fora do DAS (2º semestre)',
      quando: noMes(3, function (a) { return a >= 2027 ? ultimoDiaUtil(a, 3) : null; }), diaNaoUtil: 'ja_util', fontes: ['lc214_art41', 'cgsn_opcao'] },
    { id: 'simplesjanela09', esfera: 'compliance', titulo: 'Simples Nacional: fim da janela de setembro para optar pelo IBS e pela CBS fora do DAS (1º semestre seguinte)',
      quando: noMes(9, function (a) { return a >= 2027 ? ultimoDiaUtil(a, 9) : null; }), diaNaoUtil: 'ja_util', fontes: ['lc214_art41', 'cgsn_opcao'] },
    { id: 'simeiopcao', esfera: 'compliance', titulo: 'MEI: opção pelo SIMEI (valores fixos mensais) até o último dia útil de janeiro',
      quando: noMes(1, function (a) { return a >= 2027 ? ultimoDiaUtil(a, 1) : null; }), diaNaoUtil: 'ja_util', fontes: ['cgsn_opcao'] }
  ];

  function algumaPendente(ids) {
    return ids.some(function (id) { var f = FONTES && FONTES.porId ? FONTES.porId[id] : null; return !f || !f.validado; });
  }

  /** Obrigações do mês (1-12). `opcoes`: { uf, regime, esferas: [...] } */
  function obrigacoesDoMes(ano, mes, opcoes) {
    opcoes = opcoes || {};
    var esferas = opcoes.esferas || ['federal', 'trabalhista', 'estadual'];
    var anoMes = ano * 100 + mes;
    var saida = [];
    REGRAS.forEach(function (r) {
      if (esferas.indexOf(r.esfera) < 0) return;
      if (r.regimes && opcoes.regime && r.regimes.indexOf(opcoes.regime) < 0) return;
      if (r.ateAnoMes && anoMes > r.ateAnoMes) return;
      if (r.desdeAnoMes && anoMes < r.desdeAnoMes) return;
      if (r.semData) {
        saida.push({ id: r.id, data: null, esfera: r.esfera, titulo: r.titulo, fontes: r.fontes, ajustada: false, pendente: true });
        return;
      }
      var base = r.quando(ano, mes);
      if (!base) return;
      var d = r.diaNaoUtil === 'ja_util' ? base : ajustar(base, r.diaNaoUtil);
      var ajustada = iso(d) !== iso(base);
      saida.push({ id: r.id, data: iso(d), esfera: r.esfera, titulo: r.titulo, fontes: r.fontes, ajustada: ajustada,
        sabadoUtil: !!r.sabadoUtil,
        pendente: algumaPendente(r.fontes) || (ajustada && r.regraConfirmada === false) });
    });
    if (esferas.indexOf('estadual') >= 0 && opcoes.uf && UFS.porSigla[opcoes.uf]) {
      var u = UFS.porSigla[opcoes.uf];
      u.obrigacoes.forEach(function (o) {
        var dataStr = null, ajustada = false;
        if (o.dia) {
          var base = dataUTC(ano, mes, o.dia);
          var d = ajustar(base, 'antecipa'); // regra estadual de dia não útil não conferida: antecipa (lado seguro)
          dataStr = iso(d); ajustada = dataStr !== iso(base);
        }
        saida.push({ id: opcoes.uf + '_' + o.id, data: dataStr, esfera: 'estadual', titulo: o.titulo,
          fontes: [o.base], ajustada: ajustada, regraVariavel: !!o.regraVariavel,
          pendente: !o.validado || ajustada, link: u.portal });
      });
    }
    saida.sort(function (a, b) {
      if (!a.data) return 1;
      if (!b.data) return -1;
      return a.data < b.data ? -1 : a.data > b.data ? 1 : 0;
    });
    return saida;
  }

  /** Arquivo .ics (RFC 5545) com eventos de dia inteiro para as obrigações datadas. */
  function gerarIcs(obrigacoes, agoraIso) {
    var stamp = (agoraIso || new Date().toISOString()).replace(/[-:]/g, '').slice(0, 15) + 'Z';
    var linhas = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ORGATEC//Calendario Fiscal//PT-BR', 'CALSCALE:GREGORIAN'];
    obrigacoes.filter(function (o) { return o.data; }).forEach(function (o) {
      var dt = o.data.replace(/-/g, '');
      var fim = iso(somaDias(new Date(o.data + 'T00:00:00Z'), 1)).replace(/-/g, '');
      linhas.push('BEGIN:VEVENT', 'UID:' + o.id + '-' + dt + '@orgatec.io', 'DTSTAMP:' + stamp,
        'DTSTART;VALUE=DATE:' + dt, 'DTEND;VALUE=DATE:' + fim,
        'SUMMARY:' + o.titulo.replace(/([,;\\])/g, '\\$1'),
        'DESCRIPTION:ORGATEC — confira o prazo com seu contador' + (o.pendente ? ' (pendente de validação)' : ''),
        'END:VEVENT');
    });
    linhas.push('END:VCALENDAR');
    return linhas.join('\r\n') + '\r\n';
  }

  return { REGRAS: REGRAS, pascoa: pascoa, feriados: feriados, diaUtil: diaUtil, ajustar: ajustar,
    enesimoDiaUtil: enesimoDiaUtil, ultimoDiaUtil: ultimoDiaUtil, obrigacoesDoMes: obrigacoesDoMes, gerarIcs: gerarIcs };
});
