/* Janela de Campo automática: regras por hora e montagem do boletim a partir da previsão do MET Norway
   (api.met.no, locationforecast/2.0/complete, licença CC BY 4.0). Puro: roda no Node (tools/campo_montar.js,
   chamado por tools/gerar_boletim_campo.py) e nos testes. Sem rede, sem DOM.

   Limitações da fonte para o Brasil (conferidas em 02/11/2026): não há rajada nem probabilidade de chuva ou de
   trovoada; a trovoada vem do símbolo ("...thunder"). Por isso as regras usam vento médio, chuva prevista,
   temperatura, umidade e o símbolo. Os limites abaixo são editáveis; os marcados validado:false aparecem no site
   como "pendente de validação" até o responsável técnico ou um agrônomo confirmar. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).campoRegras = factory();
})(this, function () {
  'use strict';

  var LIMITES = {
    pulv: { ventoMin: 3, ventoMax: 10, tempMax: 30, urMin: 55, chuvaHorasDepois: 2, chuva: 0.5 },
    plantio: { chuvaModerada: 5, chuvaForte: 20 },
    colheita: { chuva: 0.5, chuvaForte: 5, urMax: 85 },
    animais: { itu: 72, ituAlto: 79 },
    maquinas: { chuvaForte: 5, ventoForte: 40 },
    condicao: { chuva: 0.5, chuvaForte: 5 },
    diaChuvaForte: 20
  };
  var CRITERIOS = [
    { op: 'pulv', texto: 'Favorável com vento entre 3 e 10 km/h, temperatura abaixo de 30 °C, umidade acima de 55% e sem chuva nas 2 horas seguintes. Trovoada ou chuva na hora: evitar.', fonte: 'Recomendações usuais de tecnologia de aplicação (Embrapa); siga sempre a bula do produto', validado: false },
    { op: 'plantio', texto: 'Chuva de 20 mm/h ou mais, ou trovoada: evitar (enxurrada). Chuva de 5 mm/h ou mais: com restrição. Confira a umidade do solo no local.', fonte: 'Critério ORGATEC', validado: false },
    { op: 'colheita', texto: 'Chuva de 5 mm/h ou mais, ou trovoada: evitar. Chuva a partir de 0,5 mm/h ou umidade acima de 85%: com restrição.', fonte: 'Critério ORGATEC', validado: false },
    { op: 'animais', texto: 'Índice de temperatura e umidade (ITU) a partir de 72: com restrição; a partir de 79, ou com trovoada: evitar o manejo e recolher.', fonte: 'ITU de Thom (fórmula de Buffington et al.); faixas de Armstrong (1994) citadas pela Embrapa', validado: false },
    { op: 'maquinas', texto: 'Trovoada ou vento médio de 40 km/h ou mais: recolher máquinas e insumos. Chuva de 5 mm/h ou mais: com restrição.', fonte: 'Critério ORGATEC', validado: false }
  ];
  var OPERACOES = ['pulv', 'plantio', 'colheita', 'animais', 'maquinas'];
  var NOME_OP = { pulv: 'Pulverização', plantio: 'Plantio', colheita: 'Colheita', animais: 'Manejo de animais', maquinas: 'Máquinas e insumos' };
  var PERIODOS = [[0, 5], [6, 9], [10, 11], [12, 14], [15, 17], [18, 23]];  // mesmos 6 períodos do boletim manual
  var GRAVIDADE = { ok: 0, atencao: 1, evitar: 2 };
  var FUSO = -3;  // horário de Brasília

  function arred(n, casas) { var f = Math.pow(10, casas || 0); return Math.round(n * f) / f; }
  function pior(a, b) { return GRAVIDADE[a] >= GRAVIDADE[b] ? a : b; }
  function doisDig(n) { return (n < 10 ? '0' : '') + n; }

  /* Índice de temperatura e umidade (Thom; forma de Buffington et al., 1982): T em °C, UR em %. */
  function itu(t, ur) { return 0.8 * t + ur * (t - 14.3) / 100 + 46.3; }

  /* ---------- Normalização da resposta do MET Norway (horas e dias no horário de Brasília) */
  function familia(simbolo) {
    var s = simbolo || '';
    if (/thunder/.test(s)) return 'trovoada';
    if (/heavyrain|heavysleet/.test(s)) return 'chuva-forte';
    if (/rain|sleet|snow/.test(s)) return 'chuva';
    if (/^cloudy|fog/.test(s)) return 'nublado';
    if (/partlycloudy/.test(s)) return 'sol-nuvens';
    if (/clearsky|fair/.test(s)) return 'sol';
    return 'nublado';
  }
  var SEV_FAMILIA = { sol: 0, 'sol-nuvens': 1, nublado: 2, chuva: 3, 'chuva-forte': 4, trovoada: 5 };

  function local(iso) {
    var d = new Date(Date.parse(iso) + FUSO * 3600000);
    var dia = d.getUTCFullYear() + '-' + doisDig(d.getUTCMonth() + 1) + '-' + doisDig(d.getUTCDate());
    return { dia: dia, h: d.getUTCHours() };
  }

  function normalizarMet(raw) {
    var ts = (raw && raw.properties && raw.properties.timeseries) || [];
    var horas = [], dias = {};
    function diaDe(k) { return dias[k] || (dias[k] = { dia: k, max: -Infinity, min: Infinity, chuva: 0, familia: 'sol', trovoada: false, ventoMax: 0 }); }
    ts.forEach(function (e) {
      var inst = (e.data.instant || {}).details || {}, l = local(e.time), d = diaDe(l.dia);
      var t = inst.air_temperature, ur = inst.relative_humidity, vento = arred((inst.wind_speed || 0) * 3.6, 1);
      if (typeof t === 'number') { d.max = Math.max(d.max, t); d.min = Math.min(d.min, t); }
      d.ventoMax = Math.max(d.ventoMax, vento);
      var n1 = e.data.next_1_hours, n6 = e.data.next_6_hours;
      if (n1) {
        var simb = n1.summary && n1.summary.symbol_code, fam = familia(simb), chuva = (n1.details && n1.details.precipitation_amount) || 0;
        horas.push({ hora: l.dia + 'T' + doisDig(l.h), dia: l.dia, h: l.h, t: arred(t, 1), ur: arred(ur, 0), vento: vento, chuva: arred(chuva, 1), simbolo: simb, trovoada: fam === 'trovoada' });
        d.chuva += chuva;
        if (SEV_FAMILIA[fam] > SEV_FAMILIA[d.familia]) d.familia = fam;
      } else if (n6) {  // depois das primeiras ~60 h o MET passa a blocos de 6 h
        var f6 = familia(n6.summary && n6.summary.symbol_code), det = n6.details || {};
        d.chuva += det.precipitation_amount || 0;
        if (typeof det.air_temperature_max === 'number') d.max = Math.max(d.max, det.air_temperature_max);
        if (typeof det.air_temperature_min === 'number') d.min = Math.min(d.min, det.air_temperature_min);
        if (SEV_FAMILIA[f6] > SEV_FAMILIA[d.familia]) d.familia = f6;
      }
    });
    var lista = Object.keys(dias).sort().map(function (k) {
      var d = dias[k];
      return { dia: d.dia, max: isFinite(d.max) ? arred(d.max, 0) : null, min: isFinite(d.min) ? arred(d.min, 0) : null,
        chuva: arred(d.chuva, 1), familia: d.familia, trovoada: d.familia === 'trovoada', ventoMax: arred(d.ventoMax, 0) };
    });
    return { horas: horas, dias: lista };
  }

  /* ---------- Avaliação de uma hora para uma operação: { estado, motivos[] } */
  function avaliar(op, h, seguintes) {
    var L = LIMITES[op], m = [];
    if (op === 'pulv') {
      if (h.trovoada) return { estado: 'evitar', motivos: ['trovoada'] };
      if (h.chuva >= L.chuva) return { estado: 'evitar', motivos: ['chuva'] };
      if (h.vento < L.ventoMin) m.push('vento fraco (inversão térmica)');
      if (h.vento > L.ventoMax) m.push('vento forte (deriva)');
      if (h.t >= L.tempMax) m.push('calor (evaporação)');
      if (h.ur <= L.urMin) m.push('umidade baixa');
      if ((seguintes || []).slice(0, L.chuvaHorasDepois).some(function (s) { return s.chuva >= L.chuva || s.trovoada; })) m.push('chuva logo depois (lavagem)');
      return { estado: m.length ? 'atencao' : 'ok', motivos: m };
    }
    if (op === 'plantio') {
      if (h.trovoada || h.chuva >= L.chuvaForte) return { estado: 'evitar', motivos: [h.trovoada ? 'trovoada' : 'chuva forte (enxurrada)'] };
      return h.chuva >= L.chuvaModerada ? { estado: 'atencao', motivos: ['chuva moderada'] } : { estado: 'ok', motivos: [] };
    }
    if (op === 'colheita') {
      if (h.trovoada || h.chuva >= L.chuvaForte) return { estado: 'evitar', motivos: [h.trovoada ? 'trovoada' : 'chuva'] };
      if (h.chuva >= L.chuva) m.push('chuva fraca');
      if (h.ur > L.urMax) m.push('umidade alta (grão úmido)');
      return { estado: m.length ? 'atencao' : 'ok', motivos: m };
    }
    if (op === 'animais') {
      if (h.trovoada) return { estado: 'evitar', motivos: ['trovoada (raios)'] };
      var i = itu(h.t, h.ur);
      if (i >= L.ituAlto) return { estado: 'evitar', motivos: ['estresse térmico alto (ITU ' + arred(i, 0) + ')'] };
      if (i >= L.itu) return { estado: 'atencao', motivos: ['estresse térmico (ITU ' + arred(i, 0) + ')'] };
      return { estado: 'ok', motivos: [] };
    }
    if (op === 'maquinas') {
      if (h.trovoada || h.vento >= L.ventoForte) return { estado: 'evitar', motivos: [h.trovoada ? 'trovoada' : 'vento forte'] };
      return h.chuva >= L.chuvaForte ? { estado: 'atencao', motivos: ['chuva forte'] } : { estado: 'ok', motivos: [] };
    }
    throw new Error('operação desconhecida: ' + op);
  }

  /* Condição geral da hora (linha do dia): trovoada ou chuva forte = evitar; chuva = com restrição. */
  function condicao(h) {
    if (h.trovoada || h.chuva >= LIMITES.condicao.chuvaForte) return 'evitar';
    return h.chuva >= LIMITES.condicao.chuva ? 'atencao' : 'ok';
  }

  /* Maior sequência de horas com estado <= alvo dentro de [ini, fim]: { de, ate } (ate exclusivo) ou null. */
  function janela(estados, alvo, ini, fim) {
    var melhor = null, inicio = null;
    for (var hh = ini; hh <= fim + 1; hh++) {
      var e = hh <= fim ? estados[hh] : undefined, cabe = e && GRAVIDADE[e] <= GRAVIDADE[alvo];
      if (cabe && inicio === null) inicio = hh;
      if (!cabe && inicio !== null) {
        if (!melhor || hh - inicio > melhor.ate - melhor.de) melhor = { de: inicio, ate: hh };
        inicio = null;
      }
    }
    return melhor;
  }
  function textoJanela(j) { return j ? doisDig(j.de) + 'h às ' + doisDig(j.ate) + 'h' : null; }

  /* Uma operação num polo, no dia: estado por hora, estado do dia e melhor janela entre 05h e 20h. */
  function diaOperacao(op, horasDia) {
    var porHora = {}, motivos = {};
    horasDia.forEach(function (h, i) {
      var r = avaliar(op, h, horasDia.slice(i + 1));
      porHora[h.h] = r.estado;
      r.motivos.forEach(function (x) { motivos[x] = (motivos[x] || 0) + 1; });
    });
    var ok = janela(porHora, 'ok', 5, 20), ate = janela(porHora, 'atencao', 5, 20);
    var uteis = Object.keys(porHora).filter(function (k) { return k >= 5 && k <= 20; }).length;
    var estado = ok && (ok.ate - ok.de) >= Math.min(8, uteis) ? 'ok' : (ok && ok.ate - ok.de >= 3) || (ate && ate.ate - ate.de >= 3) ? 'atencao' : 'evitar';
    var principal = Object.keys(motivos).sort(function (a, b) { return motivos[b] - motivos[a]; })[0] || null;
    var livre = ok && ok.ate - ok.de >= 2;
    return { estado: estado, porHora: porHora, janela: livre ? ok : ate, tipoJanela: livre ? 'ok' : ate ? 'atencao' : null, motivo: principal };
  }

  /* Estado da região: o de pelo menos metade dos polos (empate puxa para o pior). */
  function agregar(estados) {
    var ord = estados.slice().sort(function (a, b) { return GRAVIDADE[b] - GRAVIDADE[a]; });
    return ord[Math.floor((ord.length - 1) / 2)] || 'ok';
  }

  function dataCurta(iso) { var p = iso.split('-'); return p[2] + '/' + p[1]; }
  function listaPolos(nomes) { return nomes.length > 1 ? nomes.slice(0, -1).join(', ') + ' e ' + nomes[nomes.length - 1] : nomes[0]; }
  var NOME_FAMILIA = { sol: 'Sol', 'sol-nuvens': 'Sol e nuvens', nublado: 'Nublado', chuva: 'Chuva', 'chuva-forte': 'Chuva forte', trovoada: 'Pancadas com trovoada' };
  /* Rótulo do dia: a família do símbolo, qualificada pela chuva acumulada (0,3 mm não vira "Chuva"). */
  function rotuloDia(fam, chuva) {
    if (fam === 'trovoada') return chuva >= 20 ? 'Trovoada e chuva forte' : 'Pancadas com trovoada';
    if (fam === 'chuva' || fam === 'chuva-forte') return chuva < 1 ? 'Chuva isolada' : chuva < 5 ? 'Chuva fraca' : chuva < 20 ? 'Chuva moderada' : 'Chuva forte';
    return NOME_FAMILIA[fam];
  }
  var TURNOS = [['de madrugada', 0, 5], ['pela manhã', 6, 11], ['à tarde', 12, 17], ['à noite', 18, 23]];
  function turnoDe(horas) {
    var cont = TURNOS.map(function (t) { return horas.filter(function (h) { return h >= t[1] && h <= t[2]; }).length; });
    var i = cont.indexOf(Math.max.apply(null, cont));
    return TURNOS[i][0];
  }

  var PREFIXO = {
    pulv: { ok: 'Condições dentro dos limites de aplicação na maior parte do dia.', atencao: 'Condição ideal só em parte do dia, ou em nenhum horário: aplique na janela indicada e observe o motivo.', evitar: 'Sem janela segura de aplicação hoje.' },
    plantio: { ok: 'Sem chuva forte prevista; confira a umidade do solo no local.', atencao: 'Chuva moderada em parte do dia; evite áreas sujeitas a enxurrada.', evitar: 'Chuva forte ou trovoada: risco de enxurrada e arraste de sementes.' },
    colheita: { ok: 'Dia favorável para colher e transportar.', atencao: 'Colher na janela seca; fora dela, grão úmido exige secagem.', evitar: 'Chuva forte ou trovoada na maior parte do dia.' },
    animais: { ok: 'Manejo normal.', atencao: 'Calor com umidade: manejo nas horas frescas, com sombra e água.', evitar: 'Estresse térmico alto ou trovoada: evite o manejo e recolha os animais de áreas abertas.' },
    maquinas: { ok: 'Sem necessidade de recolhimento especial.', atencao: 'Chuva forte em parte do dia: deixe insumos cobertos.', evitar: 'Trovoada ou vento forte: recolha máquinas, sementes, adubo e defensivos.' }
  };

  /* ---------- Montagem do boletim (mesmo formato validado por campo.js) */
  function montar(e) {
    var dia = e.dia, porPolo = {};
    e.polos.forEach(function (p) {
      var n = normalizarMet(p.met), horasDia = n.horas.filter(function (h) { return h.dia === dia; });
      var ant = e.anterior && (e.anterior.polos || []).filter(function (x) { return x.id === p.id; })[0];
      if (ant && ant.horas) {  // horas que já passaram hoje vêm da rodada anterior do mesmo dia
        var tem = {}; horasDia.forEach(function (h) { tem[h.h] = true; });
        ant.horas.forEach(function (h) { if (h.dia === dia && !tem[h.h]) horasDia.push(h); });
        horasDia.sort(function (a, b) { return a.h - b.h; });
      }
      var ops = {};
      OPERACOES.forEach(function (op) { ops[op] = diaOperacao(op, horasDia); });
      var cond = {}; horasDia.forEach(function (h) { cond[h.h] = condicao(h); });
      porPolo[p.id] = { cfg: p, horas: horasDia, dias: n.dias.filter(function (d) { return d.dia >= dia; }).slice(0, 7), ops: ops, cond: cond };
    });

    var regioes = e.regioes.map(function (r) {
      var ps = r.polos.map(function (id) { return porPolo[id]; }).filter(Boolean);
      var hoje = ps.map(function (p) { return p.dias[0] || {}; });
      var periodos = PERIODOS.map(function (per) {
        var est = ps.map(function (p) {
          var s = null;
          for (var hh = per[0]; hh <= per[1]; hh++) if (p.cond[hh]) s = s ? pior(s, p.cond[hh]) : p.cond[hh];
          return s;
        }).filter(Boolean);
        return est.length ? agregar(est) : 'passado';
      });
      var trov = ps.filter(function (p) { return p.horas.some(function (h) { return h.trovoada && h.h >= 6 && h.h <= 20; }); });
      var chuvaH = [], trovH = [];
      ps.forEach(function (p) { p.horas.forEach(function (h) { if (h.h >= 6 && h.h <= 20) { if (h.trovoada) trovH.push(h.h); else if (h.chuva >= 0.5) chuvaH.push(h.h); } }); });
      var famDia = {};
      ps.forEach(function (p) { p.horas.forEach(function (h) { if (h.h >= 6 && h.h <= 18) { var f = familia(h.simbolo); famDia[f] = (famDia[f] || 0) + 1; } }); });
      var seco = Object.keys(famDia).filter(function (f) { return SEV_FAMILIA[f] <= 2; }).sort(function (a, b) { return famDia[b] - famDia[a]; })[0];
      var ceu = [seco ? NOME_FAMILIA[seco] : null, trovH.length ? 'pancadas com trovoada ' + turnoDe(trovH) : chuvaH.length ? 'chuva ' + turnoDe(chuvaH) : null].filter(Boolean).join('; ');
      var maxs = hoje.map(function (d) { return d.max; }).filter(function (x) { return x != null; }), mins = hoje.map(function (d) { return d.min; }).filter(function (x) { return x != null; });
      var chuvaMax = 0, poloChuva = null, ventoMax = 0, poloVento = null;
      ps.forEach(function (p) {
        var c = p.dias[0] ? p.dias[0].chuva : 0, v = Math.max.apply(null, p.horas.map(function (h) { return h.vento; }).concat([0]));
        if (c > chuvaMax) { chuvaMax = c; poloChuva = p.cfg.nome; }
        if (v > ventoMax) { ventoMax = v; poloVento = p.cfg.nome; }
      });
      var faixa = function (a) { var lo = Math.min.apply(null, a), hi = Math.max.apply(null, a); return lo === hi ? lo + ' °C' : lo + '–' + hi + ' °C'; };
      var alertas = [];
      if (trov.length) alertas.push(['evitar', 'Trovoada: ' + listaPolos(trov.map(function (p) { return p.cfg.nome; }))]);
      if (chuvaMax >= LIMITES.diaChuvaForte) alertas.push(['evitar', 'Chuva forte: até ' + arred(chuvaMax, 0) + ' mm em ' + poloChuva]);
      if (ps.some(function (p) { return p.ops.animais.estado !== 'ok' && /ITU/.test(p.ops.animais.motivo || ''); })) alertas.push(['atencao', 'Calor para o rebanho (ITU)']);
      if (!alertas.length) alertas.push(['ok', 'Sem alerta relevante']);
      var okP = janela(periodos.reduce(function (acc, s, i) { for (var hh = PERIODOS[i][0]; hh <= PERIODOS[i][1]; hh++) acc[hh] = s === 'passado' ? undefined : s; return acc; }, {}), 'ok', 5, 20);
      var nota = periodos.every(function (s) { return s === 'ok' || s === 'passado'; }) ? 'Dia todo operável na maior parte dos polos.'
        : okP ? 'Melhor janela: ' + textoJanela(okP) + ' (horário de Brasília).' : 'Sem período livre de chuva na maior parte dos polos.';
      var ops = {};
      OPERACOES.forEach(function (op) {
        var est = agregar(ps.map(function (p) { return p.ops[op].estado; }));
        var porPoloTxt = ps.map(function (p) {
          var o = p.ops[op];
          var motivo = o.motivo ? ' (' + o.motivo + ')' : '';
          if (o.tipoJanela === 'ok') return p.cfg.nome + ': ' + textoJanela(o.janela);
          if (o.tipoJanela === 'atencao') return p.cfg.nome + ': com restrição das ' + textoJanela(o.janela) + motivo;
          return p.cfg.nome + ': sem janela' + motivo;
        }).join('; ');
        ops[op] = [est, PREFIXO[op][est] + ' ' + porPoloTxt + '.'];
      });
      return { id: r.id, nome: r.nome, uf: r.uf, polos: r.polos,
        ceu: ceu || 'Sem dado suficiente para o período diurno',
        temp: maxs.length ? 'Máx. ' + faixa(maxs) + '; mín. ' + faixa(mins) : 'Sem dado de temperatura',
        chuva: chuvaMax < 0.5 ? 'Sem chuva relevante prevista' : (chuvaMax < 5 ? 'Fraca' : chuvaMax < 20 ? 'Moderada' : 'Forte') + ': até ' + arred(chuvaMax, 0) + ' mm no dia em ' + poloChuva,
        vento: 'Médio até ' + arred(ventoMax, 0) + ' km/h' + (poloVento ? ' (' + poloVento + ')' : '') + '; a fonte não traz rajadas',
        alertas: alertas, dia: periodos, nota: nota, ops: ops };
    });

    // Próximos dias por região: máxima e mínima extremas, chuva do polo mais chuvoso, condição mais severa
    var datas = [];
    Object.keys(porPolo).forEach(function (k) { porPolo[k].dias.forEach(function (d) { if (datas.indexOf(d.dia) < 0) datas.push(d.dia); }); });
    datas = datas.sort().slice(0, 7);
    var proximos = { dias: datas, regioes: e.regioes.map(function (r) {
      return { id: r.id, nome: r.nome, dias: datas.map(function (dd) {
        var ds = r.polos.map(function (id) { return porPolo[id] && porPolo[id].dias.filter(function (d) { return d.dia === dd; })[0]; }).filter(Boolean);
        if (!ds.length) return { dia: dd };
        var fam = ds.map(function (d) { return d.familia; }).sort(function (a, b) { return SEV_FAMILIA[b] - SEV_FAMILIA[a]; })[0];
        return { dia: dd, max: Math.max.apply(null, ds.map(function (d) { return d.max; }).filter(function (x) { return x != null; })),
          min: Math.min.apply(null, ds.map(function (d) { return d.min; }).filter(function (x) { return x != null; })),
          chuva: arred(Math.max.apply(null, ds.map(function (d) { return d.chuva; })), 0), familia: fam, rotulo: rotuloDia(fam, Math.max.apply(null, ds.map(function (d) { return d.chuva; }))) };
      }) };
    }) };

    // Tendência em texto (amanhã, depois de amanhã e o restante da semana)
    function resumoDias(idx) {
      var fortes = [], secas = [];
      proximos.regioes.forEach(function (r) {
        var ds = idx.map(function (i) { return r.dias[i]; }).filter(function (d) { return d && d.familia; });
        if (!ds.length) return;
        var chuva = Math.max.apply(null, ds.map(function (d) { return d.chuva || 0; }));
        if (chuva >= LIMITES.diaChuvaForte || ds.some(function (d) { return d.familia === 'trovoada'; })) fortes.push(r.nome);
        else if (chuva < 1) secas.push(r.nome);
      });
      return ((fortes.length ? 'Chuva forte ou trovoada: ' + listaPolos(fortes) + '. ' : 'Sem chuva forte prevista nas regiões acompanhadas. ') +
        (secas.length ? 'Tempo seco: ' + listaPolos(secas) + '.' : '')).trim();
    }
    var tendencia = [];
    if (datas[1]) tendencia.push({ quando: 'Amanhã ' + dataCurta(datas[1]), titulo: 'Amanhã', texto: resumoDias([1]) });
    if (datas[2]) tendencia.push({ quando: dataCurta(datas[2]), titulo: 'Depois de amanhã', texto: resumoDias([2]) });
    if (datas[6]) tendencia.push({ quando: dataCurta(datas[3]) + ' → ' + dataCurta(datas[6]), titulo: 'Restante da semana', texto: resumoDias([3, 4, 5, 6]) });

    var comTrov = regioes.filter(function (r) { return r.alertas.some(function (a) { return /^Trovoada/.test(a[1]); }); });
    var alerta = comTrov.length ? { titulo: 'Atenção · trovoadas previstas', itens: comTrov.map(function (r) {
      return r.nome + ': ' + r.ceu.toLowerCase() + '. ' + r.nota;
    }).concat(['Raios: recolha animais de áreas abertas e de perto de cercas de arame; não opere máquinas em campo aberto durante a trovoada.']) } : null;

    var hora = e.geradoEm.slice(11, 16).replace(':', 'h');
    return {
      id: dia, dia: dia, emitidoEm: dia, geradoEm: e.geradoEm, automatico: true, proximaAtualizacao: e.proximaAtualizacao || null,
      resumo: 'Boletim automático gerado às ' + hora + ' com a previsão hora a hora para ' + e.polos.length + ' polos agrícolas. Escolha a região e a operação no painel para ver a janela do dia; no mapa, as nuvens e a chuva por satélite.',
      alerta: alerta, regioes: regioes, proximos: proximos, tendencia: tendencia, criterios: CRITERIOS,
      polos: e.polos.map(function (p) {
        var x = porPolo[p.id];
        return { id: p.id, nome: p.nome, uf: p.uf, regiao: p.regiao, lat: p.lat, lon: p.lon, horas: x.horas,
          ops: OPERACOES.reduce(function (acc, op) { acc[op] = { estado: x.ops[op].estado, janela: textoJanela(x.ops[op].janela), tipoJanela: x.ops[op].tipoJanela, motivo: x.ops[op].motivo, porHora: x.ops[op].porHora }; return acc; }, {}),
          dias: x.dias };
      }),
      confianca: [
        { rotulo: 'Previsão por ponto, não por fazenda.', texto: 'Cada polo representa o município; pancadas de verão são irregulares e uma propriedade pode receber chuva forte enquanto a vizinha fica seca.' },
        { rotulo: 'Até 2 dias: hora a hora.', texto: 'Do terceiro dia em diante a fonte passa a blocos de 6 horas, com menos detalhe.' },
        { rotulo: 'Lacunas da fonte:', texto: 'sem rajadas e sem probabilidade de chuva para o Brasil; a trovoada vem do símbolo previsto.' },
        { rotulo: 'Critérios:', texto: 'os limites por operação estão descritos abaixo e aguardam validação técnica.' }
      ],
      fontes: [
        { rotulo: 'MET Norway · previsão hora a hora (locationforecast 2.0), licença CC BY 4.0', url: 'https://api.met.no/weatherapi/locationforecast/2.0/documentation' },
        { rotulo: 'NASA GIBS · imagens GOES-East (NOAA) e IMERG', url: 'https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api' },
        { rotulo: 'INMET · avisos meteorológicos oficiais', url: 'https://alertas2.inmet.gov.br' },
        { rotulo: 'INMET · portal (previsão, satélite e radar)', url: 'https://portal.inmet.gov.br' }
      ]
    };
  }

  return { LIMITES: LIMITES, CRITERIOS: CRITERIOS, OPERACOES: OPERACOES, NOME_OP: NOME_OP, PERIODOS: PERIODOS, FUSO: FUSO,
    itu: itu, familia: familia, rotuloDia: rotuloDia, normalizarMet: normalizarMet, avaliar: avaliar, condicao: condicao, janela: janela,
    diaOperacao: diaOperacao, agregar: agregar, montar: montar };
});
