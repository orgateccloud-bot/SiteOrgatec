// Ondas 2 e 3 do compliance moderno: cultura e relatos, pesos por perfil, boletim e registro da revisão técnica.
const test = require('node:test');
const assert = require('node:assert/strict');
const T = require('../../site/assets/js/termometro.js');
const F = require('../../site/assets/js/fontes.js');
const B = require('../../site/assets/js/boletim.js');
const R = require('../../docs/revisao/revisao.js');
const CI = require('../../site/assets/js/compliance-itens.js');
const RI = require('../../site/assets/js/reforma-itens.js');

test('perguntas de cultura e relatos: integridade, com fonte do decreto', () => {
  const c = T.PERGUNTAS.filter((p) => p.cultura);
  assert.equal(c.length, 4);
  c.forEach((p) => { assert.equal(p.pilar, 'integridade'); assert.ok(p.fontes.includes('dec11129_2022')); assert.match(p.texto, /art\. 57/); });
});

test('pesos por perfil: só valem depois de aprovados', () => {
  const p = T.PERGUNTAS.find((x) => x.id === 'i-codigo');
  assert.equal(T.PESOS_PERFIL.status, 'proposta');
  assert.equal(T.pesoDe(p, 'simples'), p.peso);
  const aprovada = Object.assign({}, T.PESOS_PERFIL, { status: 'aprovada' });
  assert.equal(T.pesoDe(p, 'simples', aprovada), 1);
  assert.equal(T.pesoDe(p, 'comercio', aprovada), p.peso);
  const r = { 'i-codigo': 'sim', 'i-riscos': 'nao' };
  assert.equal(T.avaliar(r, ['integridade'], 'simples').maximo, 4);
  assert.equal(T.avaliar(r, ['integridade'], 'simples', aprovada).maximo, 2);
});

test('validar cobre os pesos por perfil', () => {
  const its = {}; RI.concat(CI).forEach((i) => { its[i.id] = i; });
  assert.deepEqual(T.validar(F.porId, its), []);
});

test('boletim: mudanças do histórico por público, da mais recente para a mais antiga', () => {
  const itens = [
    { id: 'a', titulo: 'A', consultadoEm: '2026-11-01', destinos: ['publico-mei'], historico: [{ data: '2026-05-01', nota: 'n1' }, { data: '2026-09-01', nota: 'n2' }] },
    { id: 'b', titulo: 'B', consultadoEm: '2026-11-05', destinos: ['publico-mei', 'publico-simples'], historico: [] }
  ];
  const r = B.montar(itens, { mei: 'MEI', simples: 'Simples' });
  assert.deepEqual(r[0].mudancas.map((m) => m.nota), ['n2', 'n1']);
  assert.equal(r[0].conferidos[0].id, 'b');
  assert.equal(r[1].mudancas.length, 0);
  assert.equal(B.montar(itens, { mei: 'MEI' }, '2026-06-01')[0].mudancas.length, 1);
});

test('revisão: registro com hash do conteúdo e audit_hash estável', async () => {
  const O = { reformaItens: RI, complianceItens: CI, termometro: T };
  const itens = R.pendentes(O);
  assert.ok(itens.some((i) => i.tipo === 'Peso por perfil'));
  const id = itens[0].id;
  const reg = await R.registro('Responsável Teste', '2026-11-07', [{ id, decisao: 'aprovada' }], itens);
  assert.match(reg.audit_hash, /^[0-9a-f]{64}$/);
  assert.match(reg.decisoes[0].conteudoHash, /^[0-9a-f]{64}$/);
  const corpo = Object.assign({}, reg); delete corpo.audit_hash;
  assert.equal(await R.sha256(R.canonico(corpo)), reg.audit_hash);
  await assert.rejects(R.registro('', '2026-11-07', [], itens));
  await assert.rejects(R.registro('X', '2026-11-07', [{ id: 'nao-existe', decisao: 'aprovada' }], itens));
});

test('canônico igual ao json.dumps(sort_keys) do Python', () => {
  assert.equal(R.canonico({ b: 1, a: ['ç', null] }), '{"a":["ç",null],"b":1}');
});
