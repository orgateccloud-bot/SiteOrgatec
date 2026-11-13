'use strict';
/* Mapa interativo da Janela do Transporte (janela-transporte-gl.js): GeoJSON das camadas, horários do satélite, ponto da previsão e
   o balão; e, no painel (janela-transporte-mapa.js), a chuva forte prevista no Sul. */
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const G = require('../../site/assets/js/janela-transporte-gl.js');
const M = require('../../site/assets/js/janela-transporte-mapa.js');

const GEO = path.join(__dirname, '../../site/assets/geo');
const ufs = JSON.parse(fs.readFileSync(path.join(GEO, 'ufs.json'), 'utf8')).ufs;
const agora = Date.parse('2026-11-13T12:00:00Z');  // 9h em Brasília

test('rodovias, avisos e estados viram GeoJSON em (lon, lat)', () => {
  const l = G.geoLinhas([{ sigla: 'BR-153', linhas: [[[-12, -49], [-11, -49.1]]] }, { sigla: 'TO-080', linhas: [[[-10.2, -48.9], [-10.2, -48.3]]] }]);
  assert.deepStrictEqual(l.features[0].geometry.coordinates, [[-49, -12], [-49.1, -11]]);
  assert.deepStrictEqual(l.features.map(f => f.properties), [{ sigla: 'BR-153', federal: true }, { sigla: 'TO-080', federal: false }]);
  assert.strictEqual(G.geoLinhas(undefined).features.length, 0);
  const a = G.geoAvisos([{ id: 'x', gravidade: 'grande_perigo', vigente: false, poligonos: [[[-12, -49], [-12, -48], [-11, -48], [-12, -49]]] }]);
  assert.deepStrictEqual(a.features[0].properties, { id: 'x', cor: '#ef4444', vigente: false });
  const e = G.geoUfs(ufs);
  assert.ok(e.features.length >= 27 && e.features.every(f => f.geometry.coordinates[0][0][0] < -28));  // longitude primeiro
});

test('manchas de fogo no centro da célula e focos do estado', () => {
  const c = G.geoCalor({ passo_calor: 0.25, calor: [[-12.25, -49.25, 3]] });
  assert.deepStrictEqual(c.features[0], { type: 'Feature', properties: { n: 3 }, geometry: { type: 'Point', coordinates: [-49.125, -12.125] } });
  assert.deepStrictEqual(G.geoPontos([[-12, -49]]).features[0].geometry.coordinates, [-49, -12]);
});

test('chuva forte no Sul: só as células com nível, em quadrados do tamanho da grade', () => {
  const t = { estado: 'ok', passo: 0.75, pontos: [[-30, -51, 'RS', 'muito_forte', '2026-11-13T18:00:00+00:00', 40, 22], [-25, -50, 'PR', '', null, 2, 1]] };
  const g = G.geoTemporal(t);
  assert.strictEqual(g.features.length, 1);
  assert.deepStrictEqual(g.features[0].geometry.coordinates[0][0], [-51.375, -30.375]);
  assert.strictEqual(g.features[0].properties.nivel, 'muito_forte');
  assert.strictEqual(G.geoTemporal(null).features.length, 0);
  assert.strictEqual(G.geoTemporal({ estado: 'indisponivel', pontos: [] }).features.length, 0);
});

test('12 quadros do GOES de 10 em 10 min, do mais antigo ao mais novo, com 1 h de folga', () => {
  const t = G.temposSatelite(Date.parse('2026-11-13T12:07:30Z'));
  assert.strictEqual(t.length, G.QUADROS);
  assert.strictEqual(t[t.length - 1], '2026-11-13T11:00:00Z');
  assert.strictEqual(t[0], '2026-11-13T09:10:00Z');
  assert.ok(t.every(x => /T\d\d:\d0:00Z$/.test(x)));
});

test('o ponto vai à API arredondado a 0,1°', () => {
  assert.deepStrictEqual(G.pontoArredondado(-27.6123, -48.5512), [-27.6, -48.6]);
});

test('balão da previsão: próximas horas, dias em Brasília, crédito do MET e texto escapado', () => {
  const p = {
    atualizado_em: '2026-11-13T09:21:05Z', rotulos: { chuva_forte: 'Chuva forte', limpo: 'Céu limpo', '<x>': '<b>' },
    horas: Array.from({ length: 12 }, (_, i) => ({ hora: new Date(agora + i * 3600000).toISOString(), temp: 20 + i, chuva: i === 2 ? 1.5 : 0, tempo: i === 2 ? 'chuva_forte' : 'limpo' })),
    dias: [{ dia: '2026-11-12', min: 1, max: 2, chuva: 0, vento_max: 5, tempo: 'limpo' },
      { dia: '2026-11-13', min: 19, max: 31, chuva: 12.4, vento_max: 22, tempo: 'chuva_forte', trovoada: false },
      { dia: '2026-11-14', min: 18, max: 29, chuva: 0, vento_max: null, tempo: '<x>' }]
  };
  const h = G.htmlPrevisao(p, agora);
  assert.match(h, /Previsão para este ponto/);
  assert.strictEqual((h.match(/<small>/g) || []).length, 6);  // 6 horas, de 2 em 2
  assert.match(h, /<b>Hoje<\/b><span>Chuva forte<\/span><span>19° a 31°<\/span><span>12,4 mm · vento até 22 km\/h/);
  assert.match(h, /<b>Amanhã<\/b>/);
  assert.ok(!h.includes('2026-11-12') && !h.includes('<b>&lt;') && h.includes('&lt;b&gt;'));  // dia passado fora; rótulo escapado
  assert.match(h, /não é aviso oficial/);
  assert.match(h, /href="https:\/\/api\.met\.no\/doc\/License"[^>]*>Dados do MET Norway<\/a> \(CC BY 4\.0\), rodada de 13\/11 06:21/);
  assert.match(G.htmlPrevisao(null, agora), /indisponível/);
});

test('rótulo dos dias da previsão', () => {
  assert.strictEqual(G.rotuloDia('2026-11-13', agora), 'Hoje');
  assert.strictEqual(G.rotuloDia('2026-11-14', agora), 'Amanhã');
  assert.strictEqual(G.rotuloDia('2026-11-15', agora), 'dom 15');
});

const temporal = { estado: 'ok', atualizado_em: '2026-11-13T09:00:00+00:00', passo: 0.75,
  pontos: [[-30, -51, 'RS', 'muito_forte', '2026-11-13T18:00:00+00:00', 40, 22], [-29, -52, 'RS', '', null, 3, 1], [-27, -50, 'SC', 'forte', '2026-11-14T03:00:00+00:00', 20, 11], [-25, -50, 'PR', '', null, 0, 0]],
  ufs: { PR: { nivel: '', inicio: null, pontos: 0 }, SC: { nivel: 'forte', inicio: '2026-11-14T03:00:00+00:00', pontos: 1 }, RS: { nivel: 'muito_forte', inicio: '2026-11-13T18:00:00+00:00', pontos: 1 } } };

test('painel: chuva forte no Sul por estado, com o aviso de que não é alerta oficial', () => {
  assert.deepStrictEqual(M.temporalSul({ temporal }).map(l => [l.uf, l.nivel, l.pontos, l.total]), [['PR', '', 0, 1], ['SC', 'forte', 1, 1], ['RS', 'muito_forte', 1, 2]]);
  const h = M.htmlTemporal({ temporal });
  assert.match(h, /Chuva forte no Sul nas próximas 48 h/);
  assert.match(h, /data-jtm-uf="RS"[\s\S]*Chuva muito forte prevista[\s\S]*a partir de 13\/11 15:00[\s\S]*1 de 2 áreas/);
  assert.match(h, /sem chuva forte prevista/);
  assert.match(h, /não traz trovoada, granizo nem rajada/);
  assert.match(M.htmlTemporal({ temporal }, 'SC'), /data-jtm-uf="SC"/);
  assert.ok(!M.htmlTemporal({ temporal }, 'SC').includes('data-jtm-uf="RS"'));
  assert.match(M.htmlTemporal({ temporal: { ...temporal, estado: 'indisponivel' } }), /não respondeu na última tentativa: os dados abaixo são de 13\/11 06:00/);
  assert.strictEqual(M.htmlTemporal({}), '');
});

test('veredito do Brasil cita a chuva muito forte prevista sem chamar de aviso oficial', () => {
  const fontes = { inmet: { estado: 'ok' }, firms: { estado: 'ok' } };
  const base = { atualizado_em: new Date(agora - 5 * 60000).toISOString(), fontes, avisos: [], ufs: {} };
  const v = M.vereditoBrasil({ ...base, temporal }, new Date(agora));
  assert.strictEqual(v.nivel, 'atencao');
  assert.match(v.frases.join(' '), /Previsão de chuva muito forte em RS nas próximas 48 h, a partir de 13\/11 15:00 \(modelo do MET Norway, não é aviso oficial\)/);
  assert.strictEqual(M.vereditoBrasil(base, new Date(agora)).nivel, 'ok');
});
