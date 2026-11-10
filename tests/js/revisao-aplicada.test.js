// Trava da revisão técnica: um texto aprovado pelo responsável não pode mudar sem nova revisão.
// tools/aplicar_revisao.py grava, em cada aprovação, o hash do texto revisado. Se alguém editar o texto depois, este teste
// falha e a publicação (tools/publicar.py) para: o item precisa voltar para a revisão (tools/aplicar_revisao.py revoga).
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { calcular } = require('../../tools/revisao_hashes.js');
const T = require('../../site/assets/js/termometro.js');
const RI = require('../../site/assets/js/reforma-itens.js');
const CI = require('../../site/assets/js/compliance-itens.js');

const atuais = calcular(path.join(__dirname, '..', '..', 'site', 'assets', 'js'));
const ITENS = RI.concat(CI);

test('todo ponto aprovado tem responsável, data e o hash do texto que foi revisado', () => {
  for (const it of ITENS) {
    if (it.revisao.status !== 'aprovada') { assert.equal(it.revisao.status, 'pendente', it.id); continue; }
    assert.ok(it.revisao.por, it.id + ' sem responsável');
    assert.match(it.revisao.em, /^\d{4}-\d{2}-\d{2}$/, it.id);
    assert.equal(it.revisao.hash, atuais.itens['item:' + it.id].hash,
      it.id + ': o texto mudou depois da revisão técnica; rode tools/aplicar_revisao.py para voltá-lo à revisão');
  }
});

test('perguntas e pesos por perfil aprovados batem com o conjunto revisado', () => {
  if (T.REVISAO.status === 'aprovada') {
    assert.ok(T.REVISAO.por && T.REVISAO.em);
    assert.equal(T.REVISAO.hash, atuais.perguntas.agregado, 'as perguntas do termômetro mudaram depois da revisão técnica');
  }
  if (T.PESOS_PERFIL.status === 'aprovada') {
    assert.ok(T.PESOS_PERFIL.por && T.PESOS_PERFIL.em);
    assert.equal(T.PESOS_PERFIL.hash, atuais.pesos.agregado, 'os pesos por perfil mudaram depois da revisão técnica');
  }
});

test('o hash cobre todos os pontos, perguntas e pesos', () => {
  assert.equal(Object.keys(atuais.itens).filter((i) => i.startsWith('item:')).length, ITENS.length);
  assert.equal(atuais.perguntas.ids.length, T.PERGUNTAS.length);
});
