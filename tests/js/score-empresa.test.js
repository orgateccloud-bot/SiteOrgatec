'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const S = require('../../site/assets/js/score-empresa.js');
const T = require('../../site/assets/js/termometro.js');
const CI = require('../../site/assets/js/compliance-itens.js');
const RI = require('../../site/assets/js/reforma-itens.js');
const F = require('../../site/assets/js/fontes.js');
const K = require('../../site/assets/js/conteudo.js');

const itensPorId = {};
CI.concat(RI).forEach((i) => { itensPorId[i.id] = i; });
const fontesPorId = F.porId || Object.fromEntries(F.lista.map((f) => [f.id, f]));
const doPerfil = (perfil, r) => Object.fromEntries(T.PERGUNTAS
  .filter((p) => T.pilaresDoPerfil(perfil).includes(p.pilar) && T.perguntaVale(p, perfil)).map((p) => [p.id, r]));

test('limites das faixas vêm do termômetro (60 e 85)', () => {
  assert.deepEqual(S.limites(T.FAIXAS), [60, 85]);
});

test('medidor: faixa certa nos limites, rótulo escrito por extenso e título acessível', () => {
  [[59, 'risco'], [60, 'atencao'], [84, 'atencao'], [85, 'em_dia'], [0, 'risco'], [100, 'em_dia']].forEach(([n, nivel]) => {
    const f = T.faixa(n / 100), svg = S.medidor(n, f, T.FAIXAS);
    assert.equal(f.nivel, nivel, String(n));
    assert.match(svg, new RegExp('data-medidor-faixa="' + nivel + '"'));
    assert.match(svg, new RegExp('de 100 · ' + f.rotulo));
    assert.match(svg, /role="img"/);
    assert.match(svg, new RegExp('<title id="medidor-titulo">Nota geral: ' + n + ' de 100'));
  });
  const vazio = S.medidor(null, null, T.FAIXAS);
  assert.match(vazio, />—</);
  assert.match(vazio, /responda o termômetro/);
});

test('evolução: um ponto por registro do perfil, ignora os outros perfis e tem tabela', () => {
  const h = [{ data: '2026-09-01', perfil: 'comercio', geral: 40, porPilar: {} }, { data: '2026-10-01', perfil: 'comercio', geral: 55, porPilar: {} },
    { data: '2026-10-15', perfil: 'servicos', geral: 90, porPilar: {} }, { data: '2026-11-01', perfil: 'comercio', geral: 70, porPilar: {} }];
  const svg = S.evolucao(h, 'comercio', T.FAIXAS);
  assert.match(svg, /data-evolucao="3"/);
  assert.equal((svg.match(/data-ponto=/g) || []).length, 3);
  assert.doesNotMatch(svg, /90 de 100/);
  assert.match(svg, /<polyline/);
  assert.match(svg, /data-evolucao-tabela/);
  const um = S.evolucao(h, 'servicos', T.FAIXAS);
  assert.match(um, /data-evolucao="1"/);
  assert.doesNotMatch(um, /<polyline/);  // um registro: só o ponto
  assert.match(S.evolucao(h, 'mei', T.FAIXAS), /data-evolucao-vazia/);
});

test('alertas de prazo: em ordem de data, com dias e tom; prazo vencido fica fora', () => {
  const respostas = doPerfil('produtor', 'nao');
  const al = S.alertas(T, respostas, 'produtor', itensPorId, '2026-11-11');
  const prazos = al.lista.filter((a) => a.tipo === 'prazo');
  assert.ok(prazos.length >= 2);
  assert.deepEqual(prazos.map((a) => a.data), prazos.map((a) => a.data).slice().sort());
  prazos.forEach((a) => {
    assert.equal(a.dias, Math.round((Date.parse(a.data) - Date.parse('2026-11-11')) / 86400000));
    assert.equal(a.tom, S.tomPrazo(a.dias));
    assert.ok(a.pergunta && a.pergunta.fontes.length);
  });
  assert.equal(al.plano.length, prazos.length);
  assert.equal(S.alertas(T, respostas, 'produtor', itensPorId, '2027-02-01').lista.filter((a) => a.tipo === 'prazo').length, 0);
  assert.equal(S.tomPrazo(30), 'urgente');
  assert.equal(S.tomPrazo(31), 'atencao');
  assert.equal(S.tomPrazo(90), 'atencao');
  assert.equal(S.tomPrazo(91), 'informativo');
});

test('alerta de frente em Risco: só abaixo de 60, com link para a regra', () => {
  const tudoSim = S.alertas(T, doPerfil('comercio', 'sim'), 'comercio', itensPorId, '2026-11-11');
  assert.equal(tudoSim.lista.length, 0);
  const respostas = Object.assign(doPerfil('comercio', 'sim'), Object.fromEntries(T.PERGUNTAS.filter((p) => p.pilar === 'integridade').map((p) => [p.id, 'nao'])));
  const riscos = S.alertas(T, respostas, 'comercio', itensPorId, '2026-11-11').lista.filter((a) => a.tipo === 'risco');
  assert.deepEqual(riscos.map((a) => a.pilar), ['integridade']);
  assert.equal(riscos[0].nota, 0);
  assert.equal(riscos[0].regra.pagina, T.REGRA.integridade.pagina);
  const html = S.htmlAlertas(riscos, K.PILARES, fontesPorId);
  assert.match(html, /Frente em Risco · 0 de 100/);
  assert.match(html, /href="\.\.\/compliance\/integridade\.html"/);
});

test('alerta de prazo em HTML traz a contagem, a fonte e não repete a data já escrita', () => {
  const al = S.alertas(T, doPerfil('geral', 'nao'), 'geral', itensPorId, '2026-11-11');
  const html = S.htmlAlertas(al.lista.filter((a) => a.tipo === 'prazo'), K.PILARES, fontesPorId);
  assert.match(html, /Prazo · faltam 50 dias/);
  assert.match(html, /Fonte: /);
  const itens = html.split('<li ').slice(1);
  assert.ok(itens.length >= 1);
  itens.forEach((li) => {  // na frase do alerta (sem a linha da fonte), o prazo aparece uma vez
    const frase = li.match(/font-semibold mt-1">([^<]*)</)[1];
    assert.equal((frase.match(/\d{2}\/\d{2}\/\d{4}/g) || []).length, 1, frase);
  });
  assert.match(S.htmlAlertas([], K.PILARES, fontesPorId), /data-alertas-vazio/);
});

test('registrar: substitui o mesmo dia e perfil, para em 24 e não guarda respostas', () => {
  const e = (data, perfil, geral) => ({ data, perfil, geral, porPilar: { tributario: geral }, respostas: { 't-docs-fiscais': 'sim' } });
  let h = S.registrar([], e('2026-11-11', 'comercio', 50));
  h = S.registrar(h, e('2026-11-11', 'comercio', 60));
  h = S.registrar(h, e('2026-11-11', 'servicos', 70));
  assert.deepEqual(h.map((x) => [x.perfil, x.geral]), [['comercio', 60], ['servicos', 70]]);
  assert.ok(h.every((x) => !('respostas' in x)));
  for (let i = 1; i <= 30; i++) h = S.registrar(h, e('2026-01-' + String(i).padStart(2, '0'), 'comercio', i));
  assert.equal(h.length, S.MAX_REGISTROS);
  assert.equal(h[h.length - 1].data, '2026-11-11');  // ficam os mais recentes
  assert.equal(S.registrar(h, { data: 'ontem', perfil: 'x', geral: 500, porPilar: {} }).length, h.length);  // entrada inválida é ignorada
});

test('lerHistorico descarta o que não for entrada válida', () => {
  assert.deepEqual(S.lerHistorico('lixo'), []);
  assert.deepEqual(S.lerHistorico('{"a":1}'), []);
  const h = S.lerHistorico(JSON.stringify([{ data: '2026-11-11', perfil: 'geral', geral: 40, porPilar: {}, extra: 1 }, { data: '2026-11-12', perfil: 'geral', geral: 'x', porPilar: {} }]));
  assert.deepEqual(h, [{ data: '2026-11-11', perfil: 'geral', geral: 40, porPilar: {} }]);
  assert.equal(S.CHAVE_HISTORICO, 'orgatec.score.historico');
});
