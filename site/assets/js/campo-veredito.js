/* Janela de Campo: o veredito do dia e a faixa horária de cada operação (puro, testável no Node).
   Nada aqui cria regra agronômica: o veredito só conta e nomeia os estados que o boletim já traz (favorável, com restrição,
   evitar), com a janela de cada operação. Boletim vencido ou desatualizado não tem veredito. Plano: docs/ideias/campo-visual-2.md. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).campoVeredito = factory();
})(this, function () {
  'use strict';
  var OPS = [
    { id: 'pulv', nome: 'pulverização', curto: 'Pulv.' }, { id: 'plantio', nome: 'plantio', curto: 'Plantio' },
    { id: 'colheita', nome: 'colheita', curto: 'Colheita' }, { id: 'animais', nome: 'manejo de animais', curto: 'Animais' },
    { id: 'maquinas', nome: 'máquinas', curto: 'Máq.' }
  ];
  var ROTULOS = { ok: 'favorável', atencao: 'com restrição', evitar: 'evitar', sem: 'sem previsão' };
  var HORA_INICIAL = 5, HORA_FINAL = 20, HORAS_UTEIS = HORA_FINAL - HORA_INICIAL + 1;
  var SEM_PREVISAO = /^Sem previsão para as horas úteis/;

  function pad(n) { n = Number(n); return (n < 10 ? '0' : '') + n; }

  /* "05h às 11h" (texto do boletim) vira "05–11h"; qualquer outro formato, null. */
  function janelaCurta(t) {
    var m = /^(\d{1,2})h às (\d{1,2})h$/.exec(String(t || ''));
    return m ? pad(m[1]) + '–' + pad(m[2]) + 'h' : null;
  }

  /* porHora ({"5": "ok", ...}) vira uma sequência de 16 letras, das 05h às 20h: o (favorável), a (restrição), e (evitar),
     x (sem previsão). */
  function faixa(porHora) {
    var s = '', m = { ok: 'o', atencao: 'a', evitar: 'e' };
    for (var h = HORA_INICIAL; h <= HORA_FINAL; h++) s += m[(porHora || {})[h]] || 'x';
    return s;
  }

  /* Trechos seguidos de mesmo estado da faixa, para o texto alternativo: [{estado, de, ate}] (horas, ate inclusive). */
  function trechos(f) {
    var inv = { o: 'ok', a: 'atencao', e: 'evitar', x: 'sem' }, out = [];
    for (var i = 0; i < f.length; i++) {
      var est = inv[f.charAt(i)], h = HORA_INICIAL + i, u = out[out.length - 1];
      if (u && u.estado === est) u.ate = h; else out.push({ estado: est, de: h, ate: h });
    }
    return out;
  }
  function descreverFaixa(f) {
    return trechos(f).map(function (t) { return ROTULOS[t.estado] + ' das ' + pad(t.de) + 'h às ' + pad(t.ate + 1) + 'h'; }).join('; ');
  }

  /* Itens do dia de um polo (boletim automático): estado, janela, motivo e a faixa hora a hora. Polo sem nenhuma hora útil
     prevista vira 'sem' (o boletim o marca como atenção, mas não há previsão). */
  function itensDoPolo(polo) {
    return OPS.map(function (o) {
      var x = (polo && polo.ops && polo.ops[o.id]) || {};
      return { op: o.id, estado: x.horasPrevistas === 0 ? 'sem' : (x.estado || 'sem'), janela: janelaCurta(x.janela), tipoJanela: x.tipoJanela || null,
        motivo: x.motivo || '', horasPrevistas: x.horasPrevistas == null ? null : x.horasPrevistas, faixa: faixa(x.porHora) };
    });
  }

  /* Itens de uma região ([estado, resumo, orientação] por operação): boletim manual ou sem polos. Sem faixa horária. */
  function itensDaRegiao(regiao) {
    return OPS.map(function (o) {
      var v = (regiao && regiao.ops && regiao.ops[o.id]) || [];
      return { op: o.id, estado: SEM_PREVISAO.test(v[1] || '') ? 'sem' : (v[0] || 'sem'), janela: null, tipoJanela: null, motivo: '', horasPrevistas: null, faixa: null };
    });
  }

  function nome(op) { return OPS.filter(function (o) { return o.id === op; })[0].nome; }
  function lista(nomes) {
    if (nomes.length <= 1) return nomes.join('');
    return nomes.slice(0, -1).join(', ') + ' e ' + nomes[nomes.length - 1];
  }
  function maiuscula(t) { return t.charAt(0).toUpperCase() + t.slice(1); }

  /* O veredito. vigencia: 'vigente', 'vencido' (dia passado) ou 'desatualizado' (gerado há mais de 18 h).
     Devolve {tipo: 'normal'|'sem', titulo, linhas: [texto], contagem: {favoraveis, total}, parcial: {de, total}|null,
     glifos: [{op, curto, estado}]}. */
  function veredito(vigencia, itens) {
    var total = itens.length, g = { ok: [], atencao: [], evitar: [], sem: [] };
    itens.forEach(function (i) { (g[i.estado] || g.sem).push(i); });
    var glifos = itens.map(function (i) {
      var o = OPS.filter(function (x) { return x.id === i.op; })[0];
      return { op: i.op, curto: o.curto, estado: vigencia === 'vigente' ? i.estado : 'sem' };
    });
    if (vigencia !== 'vigente') {
      return { tipo: 'sem', titulo: vigencia === 'vencido' ? 'Sem veredito: boletim vencido.' : 'Sem veredito: boletim com mais de 18 horas.',
        linhas: ['Não use esta previsão para decidir. Veja os avisos oficiais do INMET.'], contagem: { favoraveis: 0, total: total }, parcial: null, glifos: glifos };
    }
    if (g.sem.length === total) {
      return { tipo: 'sem', titulo: 'Sem veredito: sem previsão para as horas úteis de hoje.', linhas: ['Veja os avisos oficiais do INMET.'],
        contagem: { favoraveis: 0, total: total }, parcial: null, glifos: glifos };
    }
    var titulo;
    if (g.ok.length === total) titulo = 'Dia favorável para todas as operações.';
    else if (g.ok.length) titulo = 'Favorável hoje: ' + lista(g.ok.map(function (i) { return nome(i.op); })) + '.';
    else if (g.evitar.length === total) titulo = 'Dia ruim: evite todas as operações.';
    else titulo = 'Nenhuma operação está favorável hoje.';
    var linhas = [];
    if (g.atencao.length) {
      linhas.push('Com restrição: ' + lista(g.atencao.map(function (i) {
        return nome(i.op) + (i.janela && i.tipoJanela === 'ok' ? ' (melhor horário ' + i.janela + ')' : '');
      })) + '.');
    }
    if (g.evitar.length && g.evitar.length !== total) linhas.push('Evitar: ' + lista(g.evitar.map(function (i) { return nome(i.op); })) + '.');
    if (g.sem.length) linhas.push('Sem previsão: ' + lista(g.sem.map(function (i) { return nome(i.op); })) + '.');
    var previstas = itens.map(function (i) { return i.horasPrevistas; }).filter(function (h) { return h != null && h > 0; });
    var menor = previstas.length ? Math.min.apply(null, previstas) : null;
    return { tipo: 'normal', titulo: titulo, linhas: linhas, contagem: { favoraveis: g.ok.length, total: total },
      parcial: menor != null && menor < HORAS_UTEIS ? { de: menor, total: HORAS_UTEIS } : null, glifos: glifos };
  }

  /* Texto do cartão da operação: a janela em destaque e o motivo, sem inventar nada além do que o boletim diz. */
  function legendaJanela(item) {
    if (item.estado === 'sem') return { janela: '—', texto: 'sem previsão para as horas úteis' };
    if (!item.janela) return { janela: '—', texto: 'sem horário favorável hoje' + (item.motivo ? ' · ' + item.motivo : '') };
    if (item.tipoJanela === 'ok') {
      return { janela: item.janela, texto: 'melhor horário' + (item.motivo ? ' · fora dele: ' + item.motivo : '') };
    }
    return { janela: item.janela, texto: 'menor restrição' + (item.motivo ? ' · ' + item.motivo : '') };
  }

  /* Colunas da grade das regiões em que todas as regiões têm o mesmo estado. linhas: itens de cada região (itensDaRegiao). */
  function colunasIguais(linhas) {
    return OPS.map(function (o, k) {
      var e0 = linhas[0] && linhas[0][k].estado;
      return { op: o.id, estado: e0, igual: linhas.length > 1 && linhas.every(function (l) { return l[k].estado === e0; }) };
    });
  }
  function fraseIguais(colunas) {
    var it = colunas.filter(function (c) { return c.igual; }).map(function (c) { return nome(c.op) + ' (' + ROTULOS[c.estado] + ')'; });
    return it.length ? 'Igual em todas as regiões: ' + lista(it) + '.' : '';
  }


  /* ---------- Ícones de tempo (conjunto próprio, traço de 2 px, cor do texto) para a tabela dos 7 dias */
  var NUVEM = 'M6.5 17a3.6 3.6 0 0 1-.5-7.17 5.2 5.2 0 0 1 10-1.2A4.2 4.2 0 0 1 16.5 17z';
  var ICONES = {
    sol: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.8 1.8M16.7 16.7l1.8 1.8M18.5 5.5l-1.8 1.8M7.3 16.7l-1.8 1.8"/>',
    'sol-nuvens': '<circle cx="8" cy="8" r="2.8"/><path d="M8 2.5v1.2M2.5 8h1.2M3.9 3.9l.9.9M12.1 3.9l-.9.9"/><path d="M8.5 19a3.4 3.4 0 0 1-.4-6.78 4.6 4.6 0 0 1 8.9-.9A3.8 3.8 0 0 1 17 19z"/>',
    nublado: '<path d="' + NUVEM + '"/>',
    chuva: '<path d="' + NUVEM.replace('17z', '15z').replace('17a', '15a') + '"/><path d="M8 18l-1 2.2M12.5 18l-1 2.2M17 18l-1 2.2"/>',
    'chuva-forte': '<path d="' + NUVEM.replace('17z', '14z').replace('17a', '14a') + '"/><path d="M7.5 16.5l-1.2 3.4M11 16.5l-1.2 3.4M14.5 16.5l-1.2 3.4M18 16.5l-1.2 3.4"/>',
    trovoada: '<path d="' + NUVEM.replace('17z', '14z').replace('17a', '14a') + '"/><path d="M12.8 14.5l-2.8 4h3.6l-2.4 3.7"/>'
  };
  function iconeTempo(familia) {
    return '<svg class="icone-tempo" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">' + (ICONES[familia] || ICONES.nublado) + '</svg>';
  }

  /* ---------- Linha do dia: temperatura, vento e chuva hora a hora (05h às 20h) de um polo, em SVG puro */
  function serieDoDia(polo, dia) {
    var s = [], i;
    for (i = 0; i < HORAS_UTEIS; i++) s.push(null);
    ((polo && polo.horas) || []).forEach(function (h) {
      if (h.dia === dia && h.h >= HORA_INICIAL && h.h <= HORA_FINAL) s[h.h - HORA_INICIAL] = { h: h.h, t: h.t, vento: h.vento, chuva: h.chuva || 0 };
    });
    return s;
  }
  function num(n, casas) { return Number(n).toFixed(casas == null ? 0 : casas).replace('.', ','); }

  /* serie: de serieDoDia. opcoes: {faixa: 16 letras da operação escolhida, agora: hora decimal em Brasília ou null}.
     Devolve null sem temperatura; senão {svg, resumo, tabela} (resumo e tabela para texto e leitor de tela). */
  function linhaDoDia(serie, opcoes) {
    opcoes = opcoes || {};
    var vivos = serie.filter(Boolean), W = 640, H = 200, PAD = 12, N = HORAS_UTEIS, dx = (W - 2 * PAD) / (N - 1);
    var temps = vivos.filter(function (p) { return p.t != null; }).map(function (p) { return p.t; });
    if (!temps.length) return null;
    var tmin = Math.min.apply(null, temps), tmax = Math.max.apply(null, temps);
    var lo = tmin - 1, hi = Math.max(tmax + 1, lo + 6);
    var ventos = vivos.filter(function (p) { return p.vento != null; }).map(function (p) { return p.vento * 3.6; });
    var vmax = Math.max(10, ventos.length ? Math.max.apply(null, ventos) : 0);
    var cmax = Math.max(1, Math.max.apply(null, vivos.map(function (p) { return p.chuva; }).concat([0])));
    var X = function (i) { return PAD + i * dx; };
    var yT = function (t) { return 12 + (hi - t) / (hi - lo) * 88; };      // faixa de cima: 12 a 100
    var yV = function (v) { return 138 - v / vmax * 26; };                   // faixa do meio: 112 a 138
    var traco = function (valor, yf) {
      var d = '', ant = false;
      serie.forEach(function (p, i) {
        var v = p && valor(p);
        if (v == null) { ant = false; return; }
        d += (ant ? 'L' : 'M') + X(i).toFixed(1) + ' ' + yf(v).toFixed(1); ant = true;
      });
      return d;
    };
    var corpo = '', f = opcoes.faixa || '', i0 = -1;
    for (var i = 0; i <= f.length; i++) {
      var ok = i < f.length && f.charAt(i) === 'o';
      if (ok && i0 < 0) i0 = i;
      if (!ok && i0 >= 0) { corpo += '<rect class="dia-janela" x="' + (X(i0) - dx / 2).toFixed(1) + '" y="4" width="' + ((i - i0) * dx).toFixed(1) + '" height="' + (H - 8) + '" rx="8"/>'; i0 = -1; }
    }
    corpo += '<path class="dia-base" d="M' + PAD + ' 192H' + (W - PAD) + '"/>';
    serie.forEach(function (p, i) {
      if (p && p.chuva > 0) { var h = Math.max(3, p.chuva / cmax * 38); corpo += '<rect class="dia-chuva" x="' + (X(i) - dx * 0.3).toFixed(1) + '" y="' + (192 - h).toFixed(1) + '" width="' + (dx * 0.6).toFixed(1) + '" height="' + h.toFixed(1) + '" rx="2"/>'; }
    });
    corpo += '<path class="dia-vento" d="' + traco(function (p) { return p.vento == null ? null : p.vento * 3.6; }, yV) + '"/>';
    corpo += '<path class="dia-temp" d="' + traco(function (p) { return p.t; }, yT) + '"/>';
    if (opcoes.agora != null && opcoes.agora >= HORA_INICIAL && opcoes.agora <= HORA_FINAL + 1) {
      var xa = PAD + (opcoes.agora - HORA_INICIAL) * dx;
      corpo += '<path class="dia-agora" d="M' + xa.toFixed(1) + ' 4V' + (H - 8) + '"/>';
    }
    var chuvaTotal = vivos.reduce(function (a, p) { return a + p.chuva; }, 0);
    var resumo = 'Temperatura de ' + num(tmin) + ' a ' + num(tmax) + ' °C · vento até ' + num(Math.max.apply(null, ventos.concat([0]))) + ' km/h · ' +
      (chuvaTotal >= 0.1 ? 'chuva de ' + num(chuvaTotal, 1) + ' mm nas horas úteis' : 'sem chuva nas horas úteis');
    var tabela = '<div class="sr-only"><table><caption>Hora a hora, 05h às 20h</caption><thead><tr><th scope="col">Hora</th><th scope="col">Temperatura (°C)</th><th scope="col">Vento (km/h)</th><th scope="col">Chuva (mm)</th></tr></thead><tbody>' +
      serie.map(function (p, i) { return p ? '<tr><th scope="row">' + (HORA_INICIAL + i) + 'h</th><td>' + num(p.t, 1) + '</td><td>' + num(p.vento * 3.6) + '</td><td>' + num(p.chuva, 1) + '</td></tr>' : ''; }).join('') + '</tbody></table></div>';
    return { svg: '<svg class="dia-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + resumo + '" focusable="false">' + corpo + '</svg>', resumo: resumo, tabela: tabela };
  }

  return { iconeTempo: iconeTempo, serieDoDia: serieDoDia, linhaDoDia: linhaDoDia, OPS: OPS, ROTULOS: ROTULOS, colunasIguais: colunasIguais, fraseIguais: fraseIguais, HORAS_UTEIS: HORAS_UTEIS, janelaCurta: janelaCurta, faixa: faixa, trechos: trechos, descreverFaixa: descreverFaixa,
    itensDoPolo: itensDoPolo, itensDaRegiao: itensDaRegiao, veredito: veredito, legendaJanela: legendaJanela, maiuscula: maiuscula, lista: lista };
});
