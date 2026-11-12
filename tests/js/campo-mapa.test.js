// Mapa de satélite da Janela de Campo (site/assets/js/campo-mapa.js): só o que roda sem navegador, isto é, o recorte e as
// escalas de cor das legendas (tiradas dos colormaps oficiais da NASA GIBS, consultados em 07/11/2026).
const test = require('node:test');
const assert = require('node:assert/strict');
const M = require('../../site/assets/js/campo-mapa.js').Orgatec.campoMapa;

test('recorte do Brasil em 3 x 3 imagens, com o centro como imagem de sondagem', () => {
  assert.deepEqual(M.CAIXA, { oeste: -75, leste: -33, norte: 6, sul: -34 });
  assert.equal(M.TILES.length, 9);
  assert.ok(M.TILES[4]);
});

test('escala do infravermelho: de -90 a 50 °C, em ordem, cores válidas, cinza no quente e cor nos topos frios', () => {
  const e = M.ESCALA_IR;
  assert.equal(e.de, -90);
  assert.equal(e.ate, 50);
  const ts = e.paradas.map((p) => p[0]);
  assert.deepEqual(ts, [...ts].sort((a, b) => a - b));
  assert.ok(ts[0] >= e.de && ts[ts.length - 1] <= e.ate);
  e.paradas.forEach((p) => assert.match(p[1], /^#[0-9a-f]{6}$/));
  assert.ok(e.marcas.every((t) => t >= e.de && t <= e.ate));
  const cor = (t) => e.paradas.find((p) => p[0] === t)[1];
  assert.equal(cor(-60), '#ff1a00');  // vermelho: topo frio
  assert.equal(cor(0), '#949494');    // cinza: nuvem baixa e superfície
});

test('escala da chuva: 7 faixas em mm/h, de verde a bordô, valores crescentes', () => {
  const c = M.ESCALA_CHUVA;
  assert.equal(c.length, 7);
  c.forEach((p) => assert.match(p[0], /^#[0-9a-f]{6}$/));
  const valores = c.map((p) => parseFloat(p[1].replace(',', '.')));
  assert.deepEqual(valores, [...valores].sort((a, b) => a - b));
  assert.equal(c[0][0], '#00991a');
  assert.equal(c[c.length - 1][0], '#580000');
});

test('resumo dos polos: conta por estado, na ordem da legenda, sem os zerados, e trata estado desconhecido como sem previsão', () => {
  assert.deepEqual(M.resumoDosPolos(['ok', 'atencao', 'ok', 'evitar', 'atencao', 'ok']), [
    { estado: 'ok', n: 3, texto: '3 favoráveis' },
    { estado: 'atencao', n: 2, texto: '2 com restrição' },
    { estado: 'evitar', n: 1, texto: '1 a evitar' },
  ]);
  assert.deepEqual(M.resumoDosPolos(['ok']), [{ estado: 'ok', n: 1, texto: '1 favorável' }]);
  assert.deepEqual(M.resumoDosPolos(['sem', 'qualquer']), [{ estado: 'sem', n: 2, texto: '2 sem previsão' }]);
  assert.deepEqual(M.resumoDosPolos([]), []);
  assert.deepEqual(M.resumoDosPolos(undefined), []);
});

test('giro do modelo 3D: arrastar para os lados gira sem fim, para cima e para baixo inclina dentro do limite', () => {
  assert.deepEqual(M.GIRO_INICIAL, { rx: 54, rz: -22 });
  assert.deepEqual(M.girar(M.GIRO_INICIAL, 0, 0), M.GIRO_INICIAL);
  assert.deepEqual(M.girar({ rx: 54, rz: 0 }, 100, 0), { rx: 54, rz: 40 });     // 0,4 grau por px
  assert.deepEqual(M.girar({ rx: 54, rz: 0 }, 0, 20), { rx: 48, rz: 0 });       // 0,3 grau por px; arrastar para baixo deita menos
  assert.equal(M.girar({ rx: 54, rz: 0 }, 0, -500).rx, 70);                     // limite de cima
  assert.equal(M.girar({ rx: 54, rz: 0 }, 0, 500).rx, 28);                      // limite de baixo: nunca vira vista de cima
  assert.equal(M.girar({ rx: 54, rz: 170 }, 100, 0).rz, -150);                  // dá a volta
  assert.equal(M.girar({ rx: 54, rz: -170 }, -100, 0).rz, 150);
  const g = M.girar({ rx: 54, rz: 0 }, 2000, 0);
  assert.ok(g.rz >= -180 && g.rz < 180);
});
