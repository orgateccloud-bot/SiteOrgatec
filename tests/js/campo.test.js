// Janela de Campo: estrutura dos boletins publicados e regras de vigência (site/assets/js/campo.js).
const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('../../site/assets/js/campo.js');
const BOLETINS = require('../../site/assets/js/boletins-campo.js');

test('todo boletim publicado tem estrutura completa', () => {
  assert.ok(BOLETINS.length >= 1);
  BOLETINS.forEach((b) => assert.deepEqual(C.validar(b), [], b.id));
  const ids = BOLETINS.map((b) => b.id);
  assert.equal(new Set(ids).size, ids.length, 'id de boletim repetido');
});

test('cada região cobre as 5 operações e os 6 períodos do dia', () => {
  BOLETINS.forEach((b) => b.regioes.forEach((r) => {
    assert.equal(r.dia.length, C.PERIODOS.length, r.id);
    C.OPERACOES.forEach((o) => assert.ok(C.ESTADOS[r.ops[o.id][0]], `${b.id}/${r.id}/${o.id}`));
  }));
});

test('toda fonte tem link https', () => {
  BOLETINS.forEach((b) => b.fontes.forEach((f) => assert.match(f.url, /^https:\/\//)));
});

test('validar aponta os erros de um boletim incompleto', () => {
  const b = JSON.parse(JSON.stringify(BOLETINS[0]));
  b.fontes = [];
  b.regioes[0].dia.pop();
  delete b.regioes[1].ops.plantio;
  b.regioes[2].ops.pulv[0] = 'talvez';
  const e = C.validar(b).join(' | ');
  assert.match(e, /sem fontes/);
  assert.match(e, /6 períodos/);
  assert.match(e, /operação plantio/);
  assert.match(e, /operação pulv/);
});

test('vigente até o fim do dia previsto; depois vira arquivo', () => {
  const b = { dia: '2026-10-28' };
  assert.equal(C.situacao(b, '2026-10-27'), 'vigente');
  assert.equal(C.situacao(b, '2026-10-28'), 'vigente');
  assert.equal(C.situacao(b, '2026-10-29'), 'vencido');
});

test('escolher: o pedido por id ou, sem pedido, o mais recente; inválidos ficam de fora', () => {
  const base = BOLETINS[0];
  const antigo = Object.assign({}, base, { id: '2026-10-20', dia: '2026-10-20', emitidoEm: '2026-10-19' });
  const quebrado = Object.assign({}, base, { id: '2026-11-05', dia: '2026-11-05', emitidoEm: '2026-11-04', fontes: [] });
  const lista = [antigo, quebrado, base];
  assert.equal(C.escolher(lista).id, base.id);  // o quebrado, mesmo mais novo, não entra
  assert.equal(C.escolher(lista, '2026-10-20').id, '2026-10-20');
  assert.equal(C.escolher(lista, 'nao-existe').id, base.id);
  assert.equal(C.escolher([], null), null);
});

test('data por extenso sem depender do fuso', () => {
  assert.equal(C.formatarDia('2026-10-28'), 'quarta-feira, 28 de outubro de 2026');
  assert.equal(C.formatarDia('2027-01-01'), 'sexta-feira, 1 de janeiro de 2027');
  assert.equal(C.dataCurta('2026-10-28'), '28/10/2026');
});
