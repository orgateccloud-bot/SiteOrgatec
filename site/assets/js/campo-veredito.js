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

  return { OPS: OPS, ROTULOS: ROTULOS, colunasIguais: colunasIguais, fraseIguais: fraseIguais, HORAS_UTEIS: HORAS_UTEIS, janelaCurta: janelaCurta, faixa: faixa, trechos: trechos, descreverFaixa: descreverFaixa,
    itensDoPolo: itensDoPolo, itensDaRegiao: itensDaRegiao, veredito: veredito, legendaJanela: legendaJanela, maiuscula: maiuscula, lista: lista };
});
