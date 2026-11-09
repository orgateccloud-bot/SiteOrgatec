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
