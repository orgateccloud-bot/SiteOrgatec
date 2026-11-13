/* Regras puras da agenda do painel LOCAR: classificar prazos, resumir, filtrar e agrupar por mês. Sem DOM, testada no Node
   (tests/js/locar-agenda.test.js). Datas são "AAAA-MM-DD"; a conta é em UTC para não depender do fuso do navegador. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).locarAgenda = factory();
})(this, function () {
  'use strict';

  var ABERTOS = ['a_fazer', 'em_andamento'];
  var ROTULO_STATUS = { a_fazer: 'A fazer', em_andamento: 'Em andamento', entregue: 'Entregue', nao_se_aplica: 'Não se aplica' };
  var ROTULO_TIPO = { obrigacao: 'Obrigação', evento_reforma: 'Marco da reforma', marco_societario: 'Marco societário' };
  var ROTULO_REGIME = { lucro_real: 'Lucro real', lucro_presumido: 'Lucro presumido', simples: 'Simples Nacional', produtor_rural_pf: 'Produtor rural PF', a_definir: 'Regime a definir' };
  var ROTULO_SITUACAO = { planejada: 'Planejada', ativa: 'Ativa', em_incorporacao: 'Em incorporação', extinta: 'Extinta' };
  var CICLO = ['planejada', 'ativa', 'em_incorporacao', 'extinta'];
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];

  function dia(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
    return m ? Date.UTC(+m[1], +m[2] - 1, +m[3]) / 86400000 : null;
  }
  /* Quantos dias de `a` até `b` (negativo se `b` é anterior). null se alguma das datas for inválida. */
  function diasEntre(a, b) {
    var x = dia(a), y = dia(b);
    return x === null || y === null ? null : y - x;
  }

  function aberto(item) { return ABERTOS.indexOf(item.status) >= 0; }
  function informativo(item) { return item.tipo === 'evento_reforma'; }
  function semPrazoCerto(item) { return !item.prazo || !!item.prazo_a_confirmar; }

  /* informativo | entregue | nao_se_aplica | sem_prazo | atrasada | proxima (até 30 dias) | futura */
  function classificar(item, hoje) {
    if (informativo(item)) return 'informativo';
    if (item.status === 'entregue') return 'entregue';
    if (item.status === 'nao_se_aplica') return 'nao_se_aplica';
    if (semPrazoCerto(item)) return 'sem_prazo';
    var d = diasEntre(hoje, item.prazo);
    if (d === null) return 'sem_prazo';
    return d < 0 ? 'atrasada' : (d <= 30 ? 'proxima' : 'futura');
  }

  function resumo(itens, hoje) {
    var r = { atrasadas: 0, proximas30: 0, andamento: 0, entreguesMes: 0, total: itens.length };
    var mes = String(hoje || '').slice(0, 7);
    itens.forEach(function (i) {
      var c = classificar(i, hoje);
      if (c === 'atrasada') r.atrasadas++;
      if (c === 'proxima') r.proximas30++;
      if (!informativo(i) && i.status === 'em_andamento') r.andamento++;
      if (!informativo(i) && i.status === 'entregue' && String(i.atualizado_em || '').slice(0, 7) === mes) r.entreguesMes++;
    });
    return r;
  }

  /* filtro: { entidade: '' (todas) | '__grupo' | id, status: 'abertos' | 'entregues' | 'todos', janela: 'todos' | '30' | '90',
               busca: texto, kpi: '' | 'atrasadas' | 'proximas' | 'andamento' | 'entregues' } */
  function filtrar(itens, filtro, hoje) {
    var f = filtro || {}, busca = String(f.busca || '').trim().toLowerCase();
    return itens.filter(function (i) {
      if (f.entidade === '__grupo' && i.entidade_id) return false;
      if (f.entidade && f.entidade !== '__grupo' && i.entidade_id !== f.entidade) return false;
      if (f.kpi) {
        var c = classificar(i, hoje);
        if (f.kpi === 'atrasadas' && c !== 'atrasada') return false;
        if (f.kpi === 'proximas' && c !== 'proxima') return false;
        if (f.kpi === 'andamento' && !(i.status === 'em_andamento' && !informativo(i))) return false;
        if (f.kpi === 'entregues' && !(i.status === 'entregue' && !informativo(i))) return false;
      } else {
        if (f.status === 'abertos' && !(aberto(i) || informativo(i))) return false;
        if (f.status === 'entregues' && i.status !== 'entregue') return false;
        if (f.janela === '30' || f.janela === '90') {
          var d = i.prazo ? diasEntre(hoje, i.prazo) : null;
          if (d === null || d > Number(f.janela)) return false;  // sem prazo fica fora de uma janela; atrasada (d < 0) fica dentro
        }
      }
      if (busca && (String(i.titulo || '') + ' ' + String(i.evidencia_ref || '')).toLowerCase().indexOf(busca) < 0) return false;
      return true;
    });
  }

  function rotuloMes(chave) {
    var p = chave.split('-');
    return MESES[+p[1] - 1] + ' de ' + p[0];
  }

  /* Agrupa por mês do prazo (ordem cronológica); itens sem prazo ou com prazo a confirmar vão para o fim. */
  function porMes(itens) {
    var grupos = {}, ordem = [], sem = [];
    itens.slice().sort(function (a, b) { return String(a.prazo || '9999') < String(b.prazo || '9999') ? -1 : 1; }).forEach(function (i) {
      if (!i.prazo || i.prazo_a_confirmar) { sem.push(i); return; }
      var chave = i.prazo.slice(0, 7);
      if (!grupos[chave]) { grupos[chave] = { chave: chave, rotulo: rotuloMes(chave), itens: [] }; ordem.push(chave); }
      grupos[chave].itens.push(i);
    });
    var saida = ordem.sort().map(function (c) { return grupos[c]; });
    if (sem.length) saida.push({ chave: 'sem-prazo', rotulo: 'Sem prazo confirmado', itens: sem });
    return saida;
  }

  /* "em 5 dias", "hoje", "há 3 dias" */
  function relativo(hoje, prazo) {
    var d = diasEntre(hoje, prazo);
    if (d === null) return '';
    if (d === 0) return 'hoje';
    if (d === 1) return 'amanhã';
    if (d === -1) return 'ontem';
    return d > 0 ? 'em ' + d + ' dias' : 'há ' + (-d) + ' dias';
  }

  function dataCurta(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
    return m ? m[3] + '/' + m[2] + '/' + m[1] : '';
  }

  /* Passos do ciclo de vida da entidade, com o atual marcado. */
  function cicloDeVida(entidade) {
    var atual = CICLO.indexOf(entidade.status);
    return CICLO.map(function (s, n) { return { id: s, rotulo: ROTULO_SITUACAO[s], atual: n === atual, passado: n < atual }; });
  }

  /* Contagem de itens abertos e atrasados por entidade. */
  function porEntidade(itens, hoje) {
    var r = {};
    itens.forEach(function (i) {
      if (!i.entidade_id || informativo(i)) return;
      var e = r[i.entidade_id] = r[i.entidade_id] || { abertos: 0, atrasados: 0 };
      if (aberto(i)) e.abertos++;
      if (classificar(i, hoje) === 'atrasada') e.atrasados++;
    });
    return r;
  }

  return { ABERTOS: ABERTOS, ROTULO_STATUS: ROTULO_STATUS, ROTULO_TIPO: ROTULO_TIPO, ROTULO_REGIME: ROTULO_REGIME, ROTULO_SITUACAO: ROTULO_SITUACAO,
    CICLO: CICLO, diasEntre: diasEntre, classificar: classificar, resumo: resumo, filtrar: filtrar, porMes: porMes, relativo: relativo,
    dataCurta: dataCurta, cicloDeVida: cicloDeVida, porEntidade: porEntidade, aberto: aberto, informativo: informativo };
});
