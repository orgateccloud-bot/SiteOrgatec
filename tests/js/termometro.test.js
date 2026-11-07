// Termômetro de conformidade: motor puro (site/assets/js/termometro.js).
const test = require('node:test');
const assert = require('node:assert/strict');
const T = require('../../site/assets/js/termometro.js');
const F = require('../../site/assets/js/fontes.js');
const CI = require('../../site/assets/js/compliance-itens.js');
const RI = require('../../site/assets/js/reforma-itens.js');

const itensPorId = {};
CI.concat(RI).forEach((i) => { itensPorId[i.id] = i; });
const todas = (r) => Object.fromEntries(T.PERGUNTAS.map((p) => [p.id, r]));

test('toda pergunta tem fonte e item existentes, frente válida e peso de 1 a 3', () => {
  assert.deepEqual(T.validar(F.porId, itensPorId), []);
  T.PILARES.forEach((p) => assert.ok(T.PERGUNTAS.some((q) => q.pilar === p), 'frente sem pergunta: ' + p));
});

test('a fonte da pergunta é a mesma (ou está entre as) do item que a explica', () => {
  T.PERGUNTAS.forEach((p) => p.fontes.forEach((f) => assert.ok(itensPorId[p.item].fontes.includes(f) || f === 'lc214_2026', p.id + ' cita ' + f)));
});

test('tudo "sim" fica em dia; tudo "não" fica em risco, com todas as pendências para corrigir', () => {
  const ok = T.avaliar(todas('sim'));
  assert.equal(ok.percentual, 1);
  assert.equal(ok.faixa.nivel, 'em_dia');
  assert.equal(ok.pendencias.length, 0);
  const ruim = T.avaliar(todas('nao'));
  assert.equal(ruim.percentual, 0);
  assert.equal(ruim.faixa.nivel, 'risco');
  assert.equal(ruim.pendencias.length, T.PERGUNTAS.length);
  assert.ok(ruim.pendencias.every((p) => p.tipo === 'corrigir'));
});

test('"não se aplica" e perguntas sem resposta ficam fora da conta; "não sei" vira pendência para verificar', () => {
  const r = T.avaliar({ 't-docs-fiscais': 'sim', 't-produtor-2027': 'na', 't-contador-responsavel': 'nao_sei' }, ['tributario']);
  assert.equal(r.maximo, 3 + 2);
  assert.equal(r.pontos, 3);
  assert.equal(r.respondidas, 3);
  assert.equal(r.total, T.PERGUNTAS.filter((p) => p.pilar === 'tributario').length);  // inclui as perguntas de comércio e serviços (sem perfil, todas valem)
  assert.deepEqual(r.pendencias.map((p) => [p.pergunta.id, p.tipo]), [['t-contador-responsavel', 'verificar']]);
  assert.equal(T.avaliar({}).percentual, null);
  assert.equal(T.avaliar({}).faixa, null);
  assert.equal(T.avaliar({ 't-docs-fiscais': 'talvez' }).respondidas, 0);  // resposta inválida é ignorada
});

test('pendências por prioridade: maior peso primeiro, depois a ordem do questionário', () => {
  const r = T.avaliar({ 'l-registro': 'nao', 'l-seguranca': 'nao', 'l-incidente': 'nao_sei' }, ['lgpd']);
  assert.deepEqual(r.pendencias.map((p) => p.pergunta.id), ['l-seguranca', 'l-registro', 'l-incidente']);
});

test('faixas: limites inclusivos e resultado por frente', () => {
  assert.equal(T.faixa(0.85).nivel, 'em_dia');
  assert.equal(T.faixa(0.8499).nivel, 'atencao');
  assert.equal(T.faixa(0.6).nivel, 'atencao');
  assert.equal(T.faixa(0.59).nivel, 'risco');
  const r = T.avaliar(Object.assign(todas('sim'), { 'p-cadastro': 'nao', 'p-comunicacao': 'nao' }));
  assert.equal(r.porPilar.tributario.faixa.nivel, 'em_dia');
  assert.equal(r.porPilar.pld.faixa.nivel, 'risco');  // 4 de 10
});

test('filtrar frentes muda o total considerado', () => {
  assert.equal(T.avaliar({}, ['pld']).total, T.PERGUNTAS.filter((p) => p.pilar === 'pld').length);
  assert.equal(T.avaliar({}).total, T.PERGUNTAS.length);
});

test('em produção, sem revisão técnica dos pesos (V11), o termômetro não aparece', () => {
  assert.equal(T.REVISAO.status, 'pendente');
  assert.equal(T.publicavel('producao'), false);
  assert.equal(T.publicavel('homologacao'), true);
});

test('perfis por público: frentes válidas, o geral não inclui as obrigações do transportador, e toda frente tem página', () => {
  assert.deepEqual(T.validar(F.porId, itensPorId), []);
  assert.deepEqual(T.pilaresDoPerfil('geral'), ['tributario', 'pld', 'lgpd', 'integridade']);
  assert.ok(T.pilaresDoPerfil('transportador').includes('transporte'));
  assert.ok(!T.pilaresDoPerfil('transportador').includes('pld'));
  assert.deepEqual(T.pilaresDoPerfil('inexistente'), T.pilaresDoPerfil('geral'));
  T.PILARES.forEach((p) => assert.ok((T.REGRA[p] && T.REGRA[p].pagina.endsWith('.html')) || T.PERGUNTAS.filter((q) => q.pilar === p).every((q) => q.publicos), p));  // frente sem página: cada pergunta aponta para o público
});

test('perfil transportador: as perguntas do setor entram na conta só nele', () => {
  const tr = T.PERGUNTAS.filter((p) => p.pilar === 'transporte');
  assert.ok(tr.length >= 5);
  const r = T.avaliar({ 'tr-ciot': 'nao', 'tr-rntrc': 'sim' }, T.pilaresDoPerfil('transportador'));
  assert.equal(r.maximo, 6);
  assert.deepEqual(r.pendencias.map((p) => p.pergunta.id), ['tr-ciot']);
  assert.equal(T.avaliar({ 'tr-ciot': 'nao' }, T.pilaresDoPerfil('geral')).respondidas, 0);
});

test('perfil produtor rural: frentes tributária, rural e LGPD, com as perguntas do campo', () => {
  assert.deepEqual(T.pilaresDoPerfil('produtor'), ['tributario', 'rural', 'lgpd']);
  assert.ok(T.PERGUNTAS.filter((p) => p.pilar === 'rural').length >= 5);
  const r = T.avaliar({ 'ru-car': 'sim', 'ru-itr': 'nao' }, T.pilaresDoPerfil('produtor'));
  assert.equal(r.porPilar.rural.maximo, 6);
  assert.deepEqual(r.pendencias.map((p) => p.pergunta.id), ['ru-itr']);
});

test('perguntas por público: cada perfil só conta as perguntas dele, e a regra aponta para a página do público', () => {
  const mei = T.avaliar({ 'pq-mei-limite': 'nao', 'pq-simples-opcao': 'nao' }, T.pilaresDoPerfil('mei'), 'mei');
  assert.deepEqual(mei.pendencias.map((p) => p.pergunta.id), ['pq-mei-limite']);
  const simples = T.avaliar({ 'pq-mei-limite': 'nao', 'pq-simples-opcao': 'nao' }, T.pilaresDoPerfil('simples'), 'simples');
  assert.deepEqual(simples.pendencias.map((p) => p.pergunta.id), ['pq-simples-opcao']);
  const pq = T.PERGUNTAS.find((p) => p.id === 'pq-mei-limite');
  assert.deepEqual(T.regraDe(pq), { destino: 'publico-mei', pagina: 'publico/mei.html' });
  assert.ok(T.perguntaVale(pq, 'geral') && !T.perguntaVale(pq, 'simples'));
  assert.ok(T.PERGUNTAS.filter((p) => p.publicos).every((p) => p.publicos.every((k) => T.PERFIS[k])));
});

test('perfis comércio e serviços: perguntas gerais mais as do público, sem as do outro', () => {
  const r = T.avaliar({ 'tc-estoque': 'nao', 'ts-reducao-60': 'nao', 't-docs-fiscais': 'nao' }, T.pilaresDoPerfil('comercio'), 'comercio');
  assert.deepEqual(r.pendencias.map((p) => p.pergunta.id).sort(), ['t-docs-fiscais', 'tc-estoque']);
  const s = T.avaliar({ 'tc-estoque': 'nao', 'ts-reducao-60': 'nao' }, T.pilaresDoPerfil('servicos'), 'servicos');
  assert.deepEqual(s.pendencias.map((p) => p.pergunta.id), ['ts-reducao-60']);
});

test('camadas de prova: só nas perguntas de peso 3 e sem mudar o percentual', () => {
  Object.keys(T.CAMADAS).forEach((id) => assert.equal(T.PERGUNTAS.find((p) => p.id === id).peso, 3, id));
  const base = T.avaliar({ 'tr-ciot': 'sim' }, ['transporte']);
  const comCamada = T.avaliar({ 'tr-ciot': 'sim', 'tr-ciot__funciona': 'sim', 'tr-ciot__prova': 'nao' }, ['transporte']);
  assert.equal(comCamada.percentual, base.percentual);  // a camada é um indicador à parte
});

test('evidência: confirma prática e registro; pergunta invertida confirma com "não"', () => {
  const ps = T.PERGUNTAS;
  // tr-ciot é invertida ("algum frete saiu sem CIOT?"): "não" confirma a prática
  let e = T.evidencia({ 'tr-ciot': 'sim', 'tr-ciot__funciona': 'nao', 'tr-ciot__prova': 'sim' }, ps);
  assert.deepEqual([e.declaradas, e.funcionam, e.comProva, e.semProva.length], [1, 1, 1, 0]);
  e = T.evidencia({ 'tr-rntrc': 'sim', 'tr-rntrc__funciona': 'sim', 'tr-rntrc__prova': 'nao_sei' }, ps);
  assert.deepEqual([e.declaradas, e.funcionam, e.comProva], [1, 1, 0]);
  assert.equal(e.semProva[0].id, 'tr-rntrc');
  assert.equal(T.evidencia({ 'tr-rntrc': 'nao' }, ps).declaradas, 0);  // só "sim" entra
});

test('plano de ação: só pendências com prazo de hoje em diante, em ordem de data', () => {
  const r = T.avaliar({ 'ru-eudr': 'nao', 't-produtor-2027': 'nao', 'ru-car': 'nao' });
  const plano = T.planoDeAcao(r.pendencias, itensPorId, '2026-11-07');
  assert.deepEqual(plano.map((x) => x.data), ['2026-12-30', '2027-01-01']);
  assert.ok(plano.every((x) => x.titulo.startsWith('ORGATEC: ')));
  assert.equal(T.planoDeAcao(r.pendencias, itensPorId, '2027-02-01').length, 0);  // prazos vencidos ficam fora
});
