const test = require('node:test');
const assert = require('node:assert/strict');
const K = require('../../site/assets/js/calculadoras.js');
const F = require('../../site/assets/js/fontes.js');

test('número em formato brasileiro e internacional', () => {
  assert.equal(K.numero('1.200.000'), 1200000);
  assert.equal(K.numero('1.200.000,50'), 1200000.5);
  assert.equal(K.numero('R$ 3.600.000,00'), 3600000);
  assert.equal(K.numero('2400000'), 2400000);
  assert.equal(K.numero(1500), 1500);
  assert.ok(Number.isNaN(K.numero('')));
  assert.ok(Number.isNaN(K.numero('abc')));
  assert.ok(Number.isNaN(K.numero(null)));
  assert.ok(Number.isNaN(K.numero(Infinity)));
});

test('transição: proporções do ICMS/ISS de 2026 a 2033 (ADCT, arts. 128 e 129)', () => {
  const esperado = { 2026: 1, 2027: 1, 2028: 1, 2029: 0.9, 2030: 0.8, 2031: 0.7, 2032: 0.6, 2033: 0 };
  for (const [ano, prop] of Object.entries(esperado)) {
    const r = K.transicaoAno(+ano, 1000000);
    assert.equal(r.proporcaoIcmsIss, prop, ano);
    assert.equal(r.icmsIssRestante, 1000000 * prop, ano);
    assert.equal(r.linha.ano, ano);
  }
  assert.equal(K.transicaoAno(2026).fase, 'teste');
  assert.equal(K.transicaoAno(2027).fase, 'cbs');
  assert.equal(K.transicaoAno(2030).fase, 'convivencia');
  assert.equal(K.transicaoAno(2033).fase, 'pleno');
});

test('transição: fontes existem e anos fora da faixa', () => {
  for (const id of K.transicaoAno(2029).fontes) assert.ok(F.porId[id] && F.porId[id].validado, id);
  assert.equal(K.transicaoAno(2025).fase, 'anterior');
  const depois = K.transicaoAno(2040, '500.000');
  assert.equal(depois.fase, 'pleno');
  assert.equal(depois.linha.ano, '2033');
  assert.equal(depois.icmsIssRestante, 0);
  assert.equal(K.transicaoAno('2031').proporcaoIcmsIss, 0.7);
});

test('transição: erros de entrada', () => {
  assert.ok(K.transicaoAno('').erro);
  assert.ok(K.transicaoAno('vinte').erro);
  assert.ok(K.transicaoAno(2029.5).erro);
  assert.ok(K.transicaoAno(2029, '-10').erro);
  assert.ok(K.transicaoAno(2029, 'abc').erro);
  assert.equal(K.transicaoAno(2029, '').icmsIssRestante, undefined); // ICMS opcional
  assert.equal(K.transicaoAno(2029, '0').icmsIssRestante, 0);
});

test('produtor: abaixo do limite não é contribuinte (art. 164) e recebe as consequências', () => {
  const r = K.produtorRural({ receita: '3.599.999,99' });
  assert.equal(r.contribuinte, false);
  assert.equal(r.motivo, 'abaixo_limite');
  assert.equal(r.consequencias.length, 3);
  for (const id of r.fontes) assert.ok(F.porId[id], id);
  assert.ok(r.fontes.includes('lc214_credito_presumido'));
  assert.match(r.avisos[0], /IPCA/);
});

test('produtor: receita igual ao limite já não é "inferior" e passa a contribuinte no ano seguinte', () => {
  const r = K.produtorRural({ receita: 3600000 });
  assert.equal(r.contribuinte, true);
  assert.equal(r.motivo, 'excesso_ate_20');
  assert.match(r.inicio, /ano seguinte/);
});

test('produtor: excesso de até 20% (§ 3º) e acima de 20% (§ 2º)', () => {
  assert.equal(K.produtorRural({ receita: 4320000 }).motivo, 'excesso_ate_20'); // exatamente 20%
  const acima = K.produtorRural({ receita: 4320001 });
  assert.equal(acima.motivo, 'excesso_acima_20');
  assert.match(acima.inicio, /informe o mês/);
  assert.match(K.produtorRural({ receita: 5e6, mesExcesso: 1 }).inicio, /março do mesmo ano/);
  assert.match(K.produtorRural({ receita: 5e6, mesExcesso: 10 }).inicio, /dezembro do mesmo ano/);
  assert.match(K.produtorRural({ receita: 5e6, mesExcesso: 11 }).inicio, /janeiro do ano seguinte/);
  assert.match(K.produtorRural({ receita: 5e6, mesExcesso: 12 }).inicio, /fevereiro do ano seguinte/);
  assert.ok(K.produtorRural({ receita: 5e6, mesExcesso: 13 }).erro);
  assert.ok(K.produtorRural({ receita: 5e6, mesExcesso: 0 }).erro);
});

test('produtor: início de atividade reduz o limite proporcionalmente (§ 4º)', () => {
  const r = K.produtorRural({ receita: 1900000, mesesAtividade: 6 });
  assert.equal(r.limite, 1800000);
  assert.equal(r.contribuinte, true);
  assert.equal(K.produtorRural({ receita: 1700000, mesesAtividade: 6 }).contribuinte, false);
  assert.ok(K.produtorRural({ receita: 1, mesesAtividade: 0 }).erro);
  assert.ok(K.produtorRural({ receita: 1, mesesAtividade: 13 }).erro);
  assert.ok(K.produtorRural({ receita: 1, mesesAtividade: 6.5 }).erro);
});

test('produtor: integrado não é contribuinte; opção pelo regime regular prevalece (art. 165)', () => {
  assert.equal(K.produtorRural({ receita: 9e6, integrado: true }).motivo, 'integrado');
  const opt = K.produtorRural({ receita: 100000, optou: true });
  assert.equal(opt.contribuinte, true);
  assert.equal(opt.motivo, 'opcao');
  assert.match(opt.texto, /art\. 165/);
});

test('produtor: erros de entrada', () => {
  assert.ok(K.produtorRural({}).erro);
  assert.ok(K.produtorRural().erro);
  assert.ok(K.produtorRural({ receita: '-1' }).erro);
  assert.ok(K.produtorRural({ receita: 'muito' }).erro);
  assert.equal(K.produtorRural({ receita: 0 }).contribuinte, false);
});

test('progresso da transição: 2026 a 2033, limites e data inválida', () => {
  assert.equal(K.progressoTransicao('2025-12-31'), 0);
  assert.equal(K.progressoTransicao('2026-01-01'), 0);
  assert.equal(K.progressoTransicao('2033-01-01'), 1);
  assert.equal(K.progressoTransicao('2040-05-05'), 1);
  const meio = K.progressoTransicao('2029-07-02');
  assert.ok(meio > 0.49 && meio < 0.51, String(meio));
  assert.equal(K.progressoTransicao('31/10/2026'), null);
  assert.equal(K.progressoTransicao(''), null);
});

test('dias até uma data: futuro, mesmo dia, passado e inválida', () => {
  assert.equal(K.diasAte('2027-01-01', '2026-10-31'), 62);
  assert.equal(K.diasAte('2027-01-01', '2027-01-01'), 0);
  assert.equal(K.diasAte('2027-01-01', '2027-03-01'), 0);
  assert.equal(K.diasAte('2027-02-30', '2026-10-31'), null);
  assert.equal(K.diasAte('2027-01-01', null), null);
});

test('imóveis da pessoa física: limites do art. 251 da LC 214', () => {
  const f = K.imoveisPessoaFisica;
  assert.equal(f({ receitaAnterior: '300.000', locadosAnterior: 4 }).contribuinte, true);
  assert.equal(f({ receitaAnterior: '300.000', locadosAnterior: 3 }).contribuinte, false);  // mais de 3 imóveis, não 3
  assert.equal(f({ receitaAnterior: 240000, locadosAnterior: 10 }).contribuinte, false);  // precisa passar de R$ 240 mil
  assert.equal(f({ vendidosAnterior: 4 }).contribuinte, true);
  assert.equal(f({ construidosAnterior: 2 }).motivos[0].regra, 'art. 251, § 1º, III');
  assert.equal(f({ construidosAnterior: 1 }).contribuinte, false);
  assert.equal(f({ receitaAtual: 288000.01 }).motivos[0].regra, 'art. 251, § 2º, II');  // 20% acima no próprio ano
  assert.equal(f({ receitaAtual: 288000 }).contribuinte, false);
  assert.equal(f({ receitaAnterior: '250.000', locadosAnterior: 5, limite: 260000 }).contribuinte, false);  // limite atualizado pelo IPCA
  assert.ok(f({ receitaAnterior: -1 }).erro);
  assert.deepEqual(f({}).fontes, ['lc214_imoveis']);
});
