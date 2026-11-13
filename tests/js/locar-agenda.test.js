'use strict';
// Regras de prazo da agenda do painel LOCAR e o catálogo de modelos (só normas e datas já conferidas, com fonte).
const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('../../site/assets/js/locar-agenda.js');
const M = require('../../site/assets/js/locar-modelos.js');
const F = require('../../site/assets/js/fontes.js');

const HOJE = '2026-11-12';
const item = (o) => Object.assign({ id: 'i', entidade_id: 'e1', tipo: 'obrigacao', titulo: 'T', prazo: null, prazo_a_confirmar: false, status: 'a_fazer' }, o);

test('diasEntre conta em dias inteiros, sem depender do fuso', () => {
  assert.equal(A.diasEntre('2026-11-12', '2026-11-12'), 0);
  assert.equal(A.diasEntre('2026-11-12', '2026-12-12'), 30);
  assert.equal(A.diasEntre('2026-11-12', '2026-11-10'), -2);
  assert.equal(A.diasEntre('2026-12-31', '2027-01-01'), 1);  // vira o ano
  assert.equal(A.diasEntre('2026-11-12', 'lixo'), null);
  assert.equal(A.diasEntre(null, '2026-11-12'), null);
});

test('classificar: atrasada, próxima (até 30 dias), futura, sem prazo e estados finais', () => {
  assert.equal(A.classificar(item({ prazo: '2026-11-11' }), HOJE), 'atrasada');
  assert.equal(A.classificar(item({ prazo: '2026-11-12' }), HOJE), 'proxima');   // vence hoje não é atraso
  assert.equal(A.classificar(item({ prazo: '2026-12-12' }), HOJE), 'proxima');   // exatamente 30 dias
  assert.equal(A.classificar(item({ prazo: '2026-12-13' }), HOJE), 'futura');
  assert.equal(A.classificar(item({ prazo: '2026-11-01', prazo_a_confirmar: true }), HOJE), 'sem_prazo');  // prazo a confirmar nunca é atraso
  assert.equal(A.classificar(item({}), HOJE), 'sem_prazo');
  assert.equal(A.classificar(item({ prazo: '2026-11-01', status: 'entregue' }), HOJE), 'entregue');
  assert.equal(A.classificar(item({ prazo: '2026-11-01', status: 'nao_se_aplica' }), HOJE), 'nao_se_aplica');
  assert.equal(A.classificar(item({ prazo: '2026-11-01', tipo: 'evento_reforma' }), HOJE), 'informativo');  // marco da reforma não atrasa
});

test('resumo conta atrasadas, próximas, em andamento e entregues do mês', () => {
  const itens = [
    item({ id: '1', prazo: '2026-11-01' }), item({ id: '2', prazo: '2026-11-20' }), item({ id: '3', prazo: '2026-12-30', status: 'em_andamento' }),
    item({ id: '4', status: 'entregue', atualizado_em: '2026-11-05T10:00:00+00:00' }), item({ id: '5', status: 'entregue', atualizado_em: '2026-10-05T10:00:00+00:00' }),
    item({ id: '6', tipo: 'evento_reforma', prazo: '2026-11-01' }),
  ];
  assert.deepEqual(A.resumo(itens, HOJE), { atrasadas: 1, proximas30: 1, andamento: 1, entreguesMes: 1, total: 6 });
});

test('filtrar por entidade, situação, período, busca e número', () => {
  const itens = [item({ id: 'a', prazo: '2026-11-01', titulo: 'Escrituração do mês' }), item({ id: 'b', entidade_id: 'e2', prazo: '2026-12-01' }),
    item({ id: 'c', entidade_id: null, tipo: 'evento_reforma', prazo: '2027-01-01', titulo: 'CBS' }), item({ id: 'd', status: 'entregue', prazo: '2026-10-01' }), item({ id: 'e', prazo: '2027-06-01' })];
  const ids = (f) => A.filtrar(itens, f, HOJE).map((i) => i.id);
  assert.deepEqual(ids({ status: 'abertos' }), ['a', 'b', 'c', 'e']);              // o informativo aparece entre os abertos
  assert.deepEqual(ids({ status: 'entregues' }), ['d']);
  assert.deepEqual(ids({ status: 'todos' }), ['a', 'b', 'c', 'd', 'e']);
  assert.deepEqual(ids({ status: 'abertos', entidade: 'e2' }), ['b']);
  assert.deepEqual(ids({ status: 'abertos', entidade: '__grupo' }), ['c']);
  assert.deepEqual(ids({ status: 'abertos', janela: '30' }), ['a', 'b']);          // atrasada fica na janela; o que vence depois dela, não
  assert.deepEqual(ids({ status: 'abertos', janela: '90' }), ['a', 'b', 'c']);  // o marco de 01/01/2027 (50 dias) entra em 90
  assert.deepEqual(ids({ status: 'todos', busca: 'ESCRITURAÇÃO' }), ['a']);        // busca sem diferenciar maiúsculas
  assert.deepEqual(ids({ kpi: 'atrasadas' }), ['a']);
  assert.deepEqual(ids({ kpi: 'entregues' }), ['d']);
  assert.deepEqual(ids({ kpi: 'proximas', status: 'entregues' }), ['b']);           // o botão de número vale por cima dos outros filtros
});

test('porMes agrupa por mês em ordem e deixa os sem prazo confirmado no fim', () => {
  const g = A.porMes([item({ id: 'x', prazo: '2027-01-10' }), item({ id: 'y', prazo: '2026-12-05' }), item({ id: 'z', prazo_a_confirmar: true, prazo: '2026-11-30' }),
    item({ id: 'w', prazo: '2026-12-20' }), item({ id: 'v' })]);
  assert.deepEqual(g.map((m) => m.chave), ['2026-12', '2027-01', 'sem-prazo']);
  assert.equal(g[0].rotulo, 'dezembro de 2026');
  assert.deepEqual(g[0].itens.map((i) => i.id), ['y', 'w']);
  assert.deepEqual(g[2].itens.map((i) => i.id).sort(), ['v', 'z']);
});

test('relativo e dataCurta', () => {
  assert.equal(A.relativo(HOJE, '2026-11-12'), 'hoje');
  assert.equal(A.relativo(HOJE, '2026-11-13'), 'amanhã');
  assert.equal(A.relativo(HOJE, '2026-11-17'), 'em 5 dias');
  assert.equal(A.relativo(HOJE, '2026-11-09'), 'há 3 dias');
  assert.equal(A.dataCurta('2026-12-05'), '05/12/2026');
  assert.equal(A.dataCurta(null), '');
});

test('ciclo de vida marca o passo atual e os já cumpridos', () => {
  const c = A.cicloDeVida({ status: 'em_incorporacao' });
  assert.deepEqual(c.map((p) => p.id), ['planejada', 'ativa', 'em_incorporacao', 'extinta']);
  assert.deepEqual(c.map((p) => [p.passado, p.atual]), [[true, false], [true, false], [false, true], [false, false]]);
});

test('porEntidade conta abertos e atrasados e ignora marcos e itens do grupo', () => {
  const r = A.porEntidade([item({ id: '1', prazo: '2026-11-01' }), item({ id: '2', prazo: '2026-12-01' }), item({ id: '3', status: 'entregue' }),
    item({ id: '4', entidade_id: null }), item({ id: '5', tipo: 'evento_reforma' })], HOJE);
  assert.deepEqual(r, { e1: { abertos: 2, atrasados: 1 } });
});

// ---------------------------------------------------------------- catálogo

test('todo modelo cita fontes que existem em fontes.js e têm id válido para a API', () => {
  const ids = new Set();
  for (const m of M.MODELOS) {
    assert.ok(!ids.has(m.id), 'id repetido ' + m.id); ids.add(m.id);
    assert.match(m.id, /^[a-z0-9_]{1,64}$/);
    assert.ok(m.fontes.length >= 1, m.id + ' sem fonte');
    for (const f of m.fontes) { assert.ok(F.porId[f], m.id + ': fonte inexistente ' + f); assert.match(f, /^[a-z0-9_]{1,64}$/); }
    assert.ok(['evento_reforma', 'obrigacao', 'marco_societario'].includes(m.tipo));
    assert.ok(['transporte', 'rural', 'simples', 'todos'].includes(m.perfil));
    assert.ok(m.titulo.length > 0 && m.titulo.length <= 160, m.id + ' título fora do limite da API');
  }
});

test('o catálogo não inventa prazo: sem data ou com data a confirmar, o item diz que falta confirmar', () => {
  for (const m of M.MODELOS) {
    if (m.prazo === null) assert.equal(m.prazoAConfirmar, true, m.id + ' sem data precisa estar "a confirmar"');
    else assert.match(m.prazo, /^\d{4}-\d{2}-\d{2}$/);
  }
  assert.equal(M.porId.piscofins_escrituracao.prazoAConfirmar, true);  // 31/12/2026 é conta a partir da extinção, não prazo literal
  assert.equal(M.porId.aliquota_cbs_senado.prazo, null);               // as fontes divergem (15/12 e 22/12)
});

test('paraItem monta o corpo do POST e doPerfil filtra', () => {
  const corpo = M.paraItem(M.porId.cbs_2027, 'e-x');
  assert.deepEqual(corpo, { tipo: 'evento_reforma', titulo: M.porId.cbs_2027.titulo, prazo: '2027-01-01', prazo_a_confirmar: false, responsavel: 'equipe',
    status: 'a_fazer', fonte_id: 'adct_126', modelo_id: 'cbs_2027', entidade_id: 'e-x' });
  assert.equal('entidade_id' in M.paraItem(M.porId.cbs_2027, null), false);
  assert.ok(M.doPerfil('rural').every((m) => m.perfil === 'rural' || m.perfil === 'todos'));
  assert.equal(M.doPerfil('todos').length, M.MODELOS.length);
});
