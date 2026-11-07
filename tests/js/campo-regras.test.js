// Janela de Campo automática: regras por hora, normalização do MET Norway e montagem do boletim
// (site/assets/js/campo-regras.js). Usa a resposta gravada em tests/fixtures/campo (sem rede).
const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../../site/assets/js/campo-regras.js');
const C = require('../../site/assets/js/campo.js');
const MET = require('../fixtures/campo/met-rio-verde.json');
const CFG = require('../../tools/campo_polos.json');

const hora = (o) => Object.assign({ h: 9, dia: '2026-11-02', t: 25, ur: 70, vento: 6, chuva: 0, simbolo: 'fair_day', trovoada: false }, o);

test('pulverização: vento de 3 a 10 km/h, abaixo de 30 °C, umidade acima de 55% e sem chuva logo depois', () => {
  assert.equal(R.avaliar('pulv', hora({ vento: 3 })).estado, 'ok');
  assert.equal(R.avaliar('pulv', hora({ vento: 10 })).estado, 'ok');
  assert.match(R.avaliar('pulv', hora({ vento: 2.9 })).motivos.join(), /vento fraco/);
  assert.match(R.avaliar('pulv', hora({ vento: 10.1 })).motivos.join(), /vento forte/);
  assert.equal(R.avaliar('pulv', hora({ t: 30 })).estado, 'atencao');
  assert.equal(R.avaliar('pulv', hora({ ur: 55 })).estado, 'atencao');
  assert.match(R.avaliar('pulv', hora(), [hora({ chuva: 2 })]).motivos.join(), /chuva logo depois/);
  assert.equal(R.avaliar('pulv', hora(), [hora(), hora(), hora({ chuva: 2 })]).estado, 'ok');  // só as 2 horas seguintes contam
  assert.equal(R.avaliar('pulv', hora({ trovoada: true })).estado, 'evitar');
  assert.equal(R.avaliar('pulv', hora({ chuva: 0.5 })).estado, 'evitar');
});

test('ITU (Thom/Buffington) e faixas de 72 e 79 para o manejo de animais', () => {
  assert.equal(Math.round(R.itu(30, 60)), 80);  // 0,8·30 + 60·(30−14,3)/100 + 46,3 = 79,72
  assert.equal(R.avaliar('animais', hora({ t: 22, ur: 60 })).estado, 'ok');       // ITU ≈ 68,5
  assert.equal(R.avaliar('animais', hora({ t: 26, ur: 70 })).estado, 'atencao');  // ITU ≈ 75,3
  assert.equal(R.avaliar('animais', hora({ t: 30, ur: 60 })).estado, 'evitar');   // ITU ≈ 79,7
  assert.equal(R.avaliar('animais', hora({ trovoada: true, t: 20 })).estado, 'evitar');
});

test('plantio, colheita e máquinas', () => {
  assert.equal(R.avaliar('plantio', hora({ chuva: 4.9 })).estado, 'ok');
  assert.equal(R.avaliar('plantio', hora({ chuva: 5 })).estado, 'atencao');
  assert.equal(R.avaliar('plantio', hora({ chuva: 20 })).estado, 'evitar');
  assert.equal(R.avaliar('colheita', hora({ ur: 86 })).estado, 'atencao');
  assert.equal(R.avaliar('colheita', hora({ chuva: 5 })).estado, 'evitar');
  assert.equal(R.avaliar('maquinas', hora({ vento: 40 })).estado, 'evitar');
  assert.equal(R.avaliar('maquinas', hora({ chuva: 5 })).estado, 'atencao');
  assert.throws(() => R.avaliar('irrigacao', hora()), /desconhecida/);
});

test('símbolo do MET: trovoada, chuva e céu', () => {
  assert.equal(R.familia('heavyrainshowersandthunder_day'), 'trovoada');
  assert.equal(R.familia('heavyrain'), 'chuva-forte');
  assert.equal(R.familia('lightrainshowers_night'), 'chuva');
  assert.equal(R.familia('partlycloudy_day'), 'sol-nuvens');
  assert.equal(R.familia('clearsky_day'), 'sol');
  assert.equal(R.rotuloDia('chuva', 0.3), 'Chuva isolada');  // 0,3 mm não vira "Chuva"
  assert.equal(R.rotuloDia('chuva-forte', 25), 'Chuva forte');
});

test('janela: maior sequência de horas aceitáveis', () => {
  const est = { 5: 'evitar', 6: 'ok', 7: 'ok', 8: 'ok', 9: 'atencao', 10: 'ok', 11: 'ok' };
  assert.deepEqual(R.janela(est, 'ok', 5, 20), { de: 6, ate: 9 });
  assert.deepEqual(R.janela(est, 'atencao', 5, 20), { de: 6, ate: 12 });
  assert.equal(R.janela({ 5: 'evitar' }, 'ok', 5, 20), null);
});

test('região usa o estado de pelo menos metade dos polos (empate puxa para o pior)', () => {
  assert.equal(R.agregar(['ok', 'ok', 'evitar']), 'ok');
  assert.equal(R.agregar(['ok', 'atencao', 'evitar']), 'atencao');
  assert.equal(R.agregar(['ok', 'ok', 'atencao', 'evitar']), 'atencao');
});

test('normalização: horas em Brasília e dias com máxima, mínima e chuva', () => {
  const n = R.normalizarMet(MET);
  assert.ok(n.horas.length >= 48);
  assert.equal(n.horas[0].hora, '2026-11-02T10');  // 13:00Z = 10h em Brasília
  assert.ok(n.dias.length >= 7);
  n.dias.forEach((d) => assert.ok(d.max >= d.min, d.dia));
  n.horas.forEach((h) => assert.ok(h.vento >= 0 && h.ur >= 0 && h.ur <= 100));
});

test('boletim montado com a amostra é válido e traz polos, 7 dias e critérios pendentes', () => {
  const polos = CFG.polos.map((p) => Object.assign({}, p, { regiao: CFG.regioes.find((r) => r.polos.includes(p.id)).id, met: MET }));
  const b = R.montar({ dia: '2026-11-02', geradoEm: '2026-11-02T11:02-03:00', regioes: CFG.regioes, polos, proximaAtualizacao: 'hoje às 17h' });
  assert.deepEqual(C.validar(b), []);
  assert.equal(b.automatico, true);
  assert.equal(b.regioes.length, CFG.regioes.length);
  assert.equal(b.polos.length, CFG.polos.length);
  assert.equal(b.proximos.dias.length, 7);
  assert.equal(b.regioes[0].dia.slice(0, 2).join(), 'passado,passado');  // 00–10h já passaram quando a amostra foi gravada
  assert.ok(b.criterios.every((c) => c.validado === false));
  assert.ok(b.fontes.some((f) => /api\.met\.no/.test(f.url)) && b.fontes.some((f) => /inmet/.test(f.url)));
  assert.ok(b.fontes.every((f) => !/cptec/.test(f.url)));  // CPTEC não autoriza uso comercial sem autorização
  b.polos.forEach((p) => R.OPERACOES.forEach((op) => assert.ok(C.ESTADOS[p.ops[op].estado], p.id + '/' + op)));
});

test('horas já passadas vêm da rodada anterior do mesmo dia', () => {
  const polos = CFG.polos.slice(0, 1).map((p) => Object.assign({}, p, { regiao: 'co', met: MET }));
  const regioes = [{ id: 'co', nome: 'Centro-Oeste', uf: 'GO', polos: [polos[0].id] }];
  const anterior = { polos: [{ id: polos[0].id, horas: [5, 6, 7, 8, 9].map((h) => hora({ h, dia: '2026-11-02' })) }] };
  const b = R.montar({ dia: '2026-11-02', geradoEm: '2026-11-02T11:00-03:00', regioes, polos, anterior });
  assert.equal(b.polos[0].horas[0].h, 5);
  assert.notEqual(b.regioes[0].dia[1], 'passado');  // 06–10h agora tem dado
});

test('vigência do boletim automático: desatualizado depois de 18 h', () => {
  const ger = Date.parse('2026-11-02T05:00-03:00');
  assert.equal(C.horasDesde({ geradoEm: '2026-11-02T05:00-03:00' }, ger + 3 * 3600000), 3);
  assert.equal(C.horasDesde({}, ger), null);
  assert.equal(C.LIMITE_HORAS, 18);
});

test('polos sem previsão ficam de fora, e o boletim avisa quais são (validação continua passando)', () => {
  const todos = CFG.polos.map((p) => Object.assign({}, p, { regiao: CFG.regioes.find((r) => r.polos.includes(p.id)).id, met: MET }));
  const ausente = todos[0];
  const b = R.montar({ dia: '2026-11-02', geradoEm: '2026-11-02T11:02-03:00', regioes: CFG.regioes, polos: todos.slice(1),
    semDados: [{ id: ausente.id, nome: ausente.nome, uf: ausente.uf, regiao: ausente.regiao }] });
  assert.deepEqual(C.validar(b), []);
  assert.deepEqual(b.semDados.map((p) => p.id), [ausente.id]);
  assert.equal(b.polos.length, CFG.polos.length - 1);
  assert.ok(b.polos.every((p) => p.id !== ausente.id));
  assert.match(b.resumo, /1 sem previsão/);
  assert.match(b.confianca[0].rotulo, /Sem previsão/);
  assert.ok(b.confianca[0].texto.includes(ausente.nome));
});

test('sem falha da fonte, semDados é vazio e a confiança começa pela previsão por ponto', () => {
  const polos = CFG.polos.map((p) => Object.assign({}, p, { regiao: CFG.regioes.find((r) => r.polos.includes(p.id)).id, met: MET }));
  const b = R.montar({ dia: '2026-11-02', geradoEm: '2026-11-02T11:02-03:00', regioes: CFG.regioes, polos });
  assert.deepEqual(b.semDados, []);
  assert.match(b.confianca[0].rotulo, /Previsão por ponto/);
});
