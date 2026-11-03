const test = require('node:test');
const assert = require('node:assert/strict');
const CAL = require('../../site/assets/js/calendario.js');
const UFS = require('../../site/assets/js/ufs.js');

test('Páscoa (algoritmo de Meeus) — datas conhecidas', () => {
  assert.equal(CAL.pascoa(2025).toISOString().slice(0, 10), '2025-04-20');
  assert.equal(CAL.pascoa(2026).toISOString().slice(0, 10), '2026-04-05');
  assert.equal(CAL.pascoa(2027).toISOString().slice(0, 10), '2027-03-28');
});

test('feriados 2026: Carnaval, Sexta-feira Santa, Corpus Christi e 20/11', () => {
  const f = CAL.feriados(2026);
  for (const d of ['2026-02-16', '2026-02-17', '2026-04-03', '2026-06-04', '2026-11-20', '2026-11-02'])
    assert.ok(f[d], d);
});

test('5º dia útil de novembro/2026 (02/11 feriado): 09/11 sem sábados; 07/11 contando sábados (salário)', () => {
  assert.equal(CAL.enesimoDiaUtil(2026, 11, 5).toISOString().slice(0, 10), '2026-11-09');
  assert.equal(CAL.enesimoDiaUtil(2026, 11, 5, true).toISOString().slice(0, 10), '2026-11-07');
  const sal = CAL.obrigacoesDoMes(2026, 11, { esferas: ['trabalhista'] }).find(x => x.id === 'salario');
  assert.equal(sal.data, '2026-11-07');
  assert.equal(sal.pendente, false); // IN MTP 2/2021, art. 14, I: sábado conta
});

test('20/12/2026 é domingo: 13º (2ª parcela) antecipa para 18/12 e sai pendente (lei não regula dia não útil)', () => {
  const o = CAL.obrigacoesDoMes(2026, 12, { regime: 'simples', esferas: ['trabalhista'] }).find(x => x.id === 'decimo2');
  assert.equal(o.data, '2026-12-18');
  assert.equal(o.ajustada, true);
  assert.equal(o.pendente, true);
});

test('DAS prorroga quando dia 20 não é útil (20/06/2026 é sábado → 22/06)', () => {
  const o = CAL.obrigacoesDoMes(2026, 6, { regime: 'simples', esferas: ['federal'] });
  assert.equal(o.find(x => x.id === 'das').data, '2026-06-22');
  assert.equal(o.find(x => x.id === 'irrf').data, '2026-06-19'); // IRRF antecipa
});

test('eSocial e EFD-Reinf prorrogam (15/11/2026 é domingo e feriado → 16/11)', () => {
  const o = CAL.obrigacoesDoMes(2026, 11, { esferas: ['federal', 'trabalhista'] });
  assert.equal(o.find(x => x.id === 'esocial').data, '2026-11-16');
  assert.equal(o.find(x => x.id === 'reinf').data, '2026-11-16');
});

test('ECD no último dia útil de junho (30/06/2026) e não em maio', () => {
  const jun = CAL.obrigacoesDoMes(2026, 6, { regime: 'real', esferas: ['federal'] });
  const mai = CAL.obrigacoesDoMes(2026, 5, { regime: 'real', esferas: ['federal'] });
  assert.equal(jun.find(x => x.id === 'ecd').data, '2026-06-30');
  assert.ok(!mai.find(x => x.id === 'ecd'));
});

test('DCTFWeb no último dia útil do mês (out/2026 = 30/10)', () => {
  const o = CAL.obrigacoesDoMes(2026, 10, { esferas: ['federal'] });
  assert.equal(o.find(x => x.id === 'dctfweb').data, '2026-10-30');
});

test('PIS/Cofins: último vencimento em 01/2027; CBS aparece a partir de 02/2027', () => {
  const jan = CAL.obrigacoesDoMes(2027, 1, { regime: 'real', esferas: ['federal'] }).map(x => x.id);
  const fev = CAL.obrigacoesDoMes(2027, 2, { regime: 'real', esferas: ['federal'] }).map(x => x.id);
  assert.ok(jan.includes('piscofins') && !jan.includes('cbs'));
  assert.ok(!fev.includes('piscofins') && fev.includes('cbs') && fev.includes('ibs'));
  const o = CAL.obrigacoesDoMes(2027, 2, { regime: 'real', esferas: ['federal'] });
  assert.equal(o.find(x => x.id === 'cbs').data, '2027-02-26'); // último dia útil de fev/2027 (Decreto 12.955/2026, art. 45)
  assert.equal(o.find(x => x.id === 'ibs').data, null);
});

test('filtros de regime: DAS só no Simples; IRPJ trimestral só em jan/abr/jul/out', () => {
  const pres = CAL.obrigacoesDoMes(2026, 10, { regime: 'presumido' }).map(x => x.id);
  assert.ok(!pres.includes('das') && pres.includes('irpjcsll'));
  assert.ok(!CAL.obrigacoesDoMes(2026, 11, { regime: 'presumido' }).map(x => x.id).includes('irpjcsll'));
});

test('todas as 27 UFs geram obrigações estaduais, com data ou "pendente"', () => {
  assert.equal(UFS.lista.length, 27);
  for (const u of UFS.lista) {
    const est = CAL.obrigacoesDoMes(2026, 11, { uf: u.sigla, regime: 'real', esferas: ['estadual'] });
    assert.ok(est.length >= 1, u.sigla);
    for (const o of est) assert.ok(o.data !== null || o.pendente || o.regraVariavel, `${u.sigla} ${o.id}: sem data deve ser pendente`);
    assert.ok(est[0].fontes[0].url.startsWith('https://'), u.sigla + ' sem portal oficial');
  }
});

test('ICMS estadual: GO dia 20 (DARE); 20/11/2026 é feriado → antecipa para 19/11 e sai pendente', () => {
  const out = CAL.obrigacoesDoMes(2026, 10, { uf: 'GO', esferas: ['estadual'] }).find(x => x.id === 'GO_icms');
  assert.equal(out.data, '2026-10-20'); assert.equal(out.pendente, false);
  const nov = CAL.obrigacoesDoMes(2026, 11, { uf: 'GO', esferas: ['estadual'] }).find(x => x.id === 'GO_icms');
  assert.equal(nov.data, '2026-11-19'); assert.equal(nov.pendente, true);
  assert.match(nov.titulo, /DARE/);
});

test('ICMS estadual: UFs sem prazo confirmado ficam "data a confirmar"; SP/MT/MS por atividade', () => {
  for (const uf of ['TO', 'PA', 'AC', 'AL', 'AP', 'BA', 'CE', 'MA', 'PI', 'SE', 'RJ']) {
    const o = CAL.obrigacoesDoMes(2026, 10, { uf, esferas: ['estadual'] }).find(x => x.id === uf + '_icms');
    assert.equal(o.data, null, uf); assert.equal(o.pendente, true, uf);
  }
  for (const uf of ['SP', 'MT', 'MS']) {
    const o = CAL.obrigacoesDoMes(2026, 10, { uf, esferas: ['estadual'] }).find(x => x.id === uf + '_icms');
    assert.equal(o.regraVariavel, true, uf); assert.equal(o.pendente, false, uf);
  }
});

test('nenhuma data cai em fim de semana ou feriado nacional (12 meses × 27 UFs × 3 regimes)', () => {
  for (const u of UFS.lista) for (const regime of ['simples', 'presumido', 'real']) for (let m = 1; m <= 12; m++) {
    for (const o of CAL.obrigacoesDoMes(2026, m, { uf: u.sigla, regime })) {
      if (!o.data) continue;
      assert.ok(CAL.diaUtil(new Date(o.data + 'T00:00:00Z'), o.sabadoUtil), `${u.sigla} ${regime} ${o.id} ${o.data}`);
    }
  }
});

test('.ics válido: VCALENDAR com um VEVENT por obrigação datada e CRLF', () => {
  const o = CAL.obrigacoesDoMes(2026, 11, { uf: 'GO', regime: 'simples' });
  const ics = CAL.gerarIcs(o, '2026-10-30T12:00:00Z');
  assert.match(ics, /^BEGIN:VCALENDAR\r\n/);
  assert.match(ics, /END:VCALENDAR\r\n$/);
  assert.equal((ics.match(/BEGIN:VEVENT/g) || []).length, o.filter(x => x.data).length);
});

test('esfera compliance: datas fixas da norma, com fonte, e fora da lista quando não pedida', () => {
  const dez = CAL.obrigacoesDoMes(2026, 12, { esferas: ['compliance'] });
  assert.deepEqual(dez.map((o) => [o.id, o.data]).sort(), [['conformidade2026', '2026-12-31'], ['eudr2026', '2026-12-30']]);
  assert.deepEqual(CAL.obrigacoesDoMes(2027, 6, { esferas: ['compliance'] }).map((o) => o.id), ['eudr2027']);
  assert.deepEqual(CAL.obrigacoesDoMes(2027, 2, { esferas: ['compliance'] }).map((o) => [o.id, o.data]), [['funruralopcao', '2027-02-19']]);  // 20/02/2027 é sábado: antecipa
  const jan = CAL.obrigacoesDoMes(2027, 1, { esferas: ['compliance'] });
  assert.deepEqual(jan.map((o) => [o.id, o.data]).sort(), [['cfcnaoocorrencia', '2027-01-31'], ['pisosfrete01', '2027-01-20'], ['produtorcnpj2027', '2027-01-01'], ['simeiopcao', '2027-01-29']]);
  assert.deepEqual(CAL.obrigacoesDoMes(2028, 1, { esferas: ['compliance'] }).map((o) => o.id).sort(), ['cfcnaoocorrencia', 'pisosfrete01', 'simeiopcao']);  // só as anuais
  assert.deepEqual(CAL.obrigacoesDoMes(2027, 3, { esferas: ['compliance'] }).map((o) => [o.id, o.data]), [['simplesjanela03', '2027-03-31']]);
  assert.equal(CAL.obrigacoesDoMes(2026, 9, { esferas: ['compliance'] }).length, 0);  // a janela de setembro/2026 já passou e não é recriada
  assert.deepEqual(CAL.obrigacoesDoMes(2027, 7, { esferas: ['compliance'] }).map((o) => [o.id, o.data]), [['pisosfrete07', '2027-07-20']]);  // pisos da ANTT, 2º semestre
  assert.equal(CAL.obrigacoesDoMes(2027, 12, { esferas: ['compliance'] }).length, 0);  // o programa de 2026 não se repete
  assert.ok(!CAL.obrigacoesDoMes(2026, 12).some((o) => o.esfera === 'compliance'));  // padrão: federal, trabalhista e estadual
  [...dez, ...jan].forEach((o) => assert.equal(o.pendente, false, o.id + ' com fonte pendente'));
});
