'use strict';
const test = require('node:test');
const assert = require('node:assert');
const J = require('../../site/assets/js/janela-empresarial.js');

const agora = new Date('2026-11-09T12:00:00-03:00');
const base = { id: 'E1', modulo: 'Prazos', fonte: 'Calendário', validadeHoras: 36, dados: { porPerfil: {} } };

test('cartão dentro da validade fica em dia', () => {
  assert.strictEqual(J.estadoEfetivo({ ...base, estado: 'ok', coletadoEm: '2026-11-09T05:00-03:00' }, agora), 'ok');
});

test('cartão fora da validade vira atrasado e mostra o carimbo', () => {
  const c = { ...base, estado: 'ok', coletadoEm: '2026-11-05T05:00-03:00' };
  assert.strictEqual(J.estadoEfetivo(c, agora), 'atrasado');
  const html = J.renderizar({ geradoEm: '2026-11-05T05:00-03:00', proximaAtualizacao: 'hoje às 11h', aviso: 'aviso', cartoes: [c] }, {}, agora);
  assert.match(html, /Atrasado/);
  assert.match(html, /05\/11\/2026 05:00/);
});

test('cartão indisponível nunca mostra dados, mesmo que venham no arquivo', () => {
  const c = { ...base, estado: 'indisponivel', coletadoEm: null, motivo: 'sem termos', dados: { segredo: 'valor antigo' } };
  const html = J.renderizar({ geradoEm: '2026-11-09T05:00-03:00', proximaAtualizacao: 'hoje às 11h', aviso: 'aviso', cartoes: [c] }, {}, agora);
  assert.match(html, /sem termos/);
  assert.doesNotMatch(html, /valor antigo/);
});

test('data ilegível conta como atrasado e cartões do transporte só aparecem para o transportador', () => {
  assert.strictEqual(J.estadoEfetivo({ ...base, estado: 'ok', coletadoEm: 'lixo' }, agora), 'atrasado');
  const t1 = { id: 'T1', modulo: 'Piso', fonte: 'ANTT', validadeHoras: 100, estado: 'indisponivel', coletadoEm: null, motivo: 'm' };
  const janela = { geradoEm: '2026-11-09T05:00-03:00', proximaAtualizacao: 'x', aviso: 'a', cartoes: [t1] };
  assert.doesNotMatch(J.renderizar(janela, { atividade: 'comercio' }, agora), /data-cartao="T1"/);
  assert.match(J.renderizar(janela, { atividade: 'transportador' }, agora), /data-cartao="T1"/);
});

const T = require('../../site/assets/js/termometro.js');
const F = require('../../site/assets/js/fontes.js');
const K = require('../../site/assets/js/conteudo.js');
const fontesPorId = F.porId || Object.fromEntries(F.lista.map((f) => [f.id, f]));
const doPerfil = (perfil, r) => Object.fromEntries(T.PERGUNTAS
  .filter((p) => T.pilaresDoPerfil(perfil).includes(p.pilar) && T.perguntaVale(p, perfil)).map((p) => [p.id, r]));

test('score sem resposta convida ao termômetro já no perfil da atividade', () => {
  const html = J.cartaoScore(T, {}, 'transportador', 'homologacao', K.PILARES, fontesPorId);
  assert.match(html, /data-score-estado="sem-resposta"/);
  assert.match(html, /href="\.\.\/compliance\/termometro\.html#perfil-transportador"/);
  assert.doesNotMatch(html, /data-score-nota/);
  assert.match(J.cartaoScore(T, {}, '', 'homologacao', K.PILARES, fontesPorId), /#perfil-geral"/);
});

test('score com respostas: nota geral e por frente do perfil, sem frentes de outro perfil', () => {
  const html = J.cartaoScore(T, doPerfil('transportador', 'sim'), 'transportador', 'homologacao', K.PILARES, fontesPorId);
  assert.match(html, /data-score-estado="nota"/);
  assert.match(html, /data-score-nota>100</);
  assert.match(html, /data-score-faixa="em_dia"/);
  T.pilaresDoPerfil('transportador').forEach((p) => assert.match(html, new RegExp('data-score-frente="' + p + '"')));
  assert.doesNotMatch(html, /data-score-frente="pld"/);
  assert.match(html, /Não é parecer nem probabilidade de autuação/);
});

test('score igual ao do termômetro e as 3 pendências mais pesadas com fonte', () => {
  const respostas = doPerfil('comercio', 'nao');
  const r = T.avaliar(respostas, T.pilaresDoPerfil('comercio'), 'comercio');
  const html = J.cartaoScore(T, respostas, 'comercio', 'homologacao', K.PILARES, fontesPorId);
  assert.match(html, new RegExp('data-score-nota>' + T.nota(r).geral + '<'));
  const ids = [...html.matchAll(/data-score-pendencia="([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual(ids, r.pendencias.slice(0, 3).map((pd) => pd.pergunta.id));
  r.pendencias.slice(0, 3).forEach((pd) => assert.ok(html.includes(fontesPorId[pd.pergunta.fontes[0]].rotulo.replace(/&/g, '&amp;')), pd.pergunta.id));
});

test('em produção, sem a revisão técnica (V11), o score não mostra nota', () => {
  if (T.REVISAO.status === 'aprovada') return;
  const html = J.cartaoScore(T, doPerfil('servicos', 'sim'), 'servicos', 'producao', K.PILARES, fontesPorId);
  assert.match(html, /data-score-estado="revisao"/);
  assert.doesNotMatch(html, /data-score-nota/);
});
