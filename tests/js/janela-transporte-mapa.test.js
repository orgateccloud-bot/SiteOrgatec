'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const M = require('../../site/assets/js/janela-transporte-mapa.js');

const agora = new Date('2026-11-12T15:00:00Z');
const rodovias = JSON.parse(fs.readFileSync(path.join(__dirname, '../../site/assets/geo/rodovias-corredores.json'), 'utf8'));
const quadrado = [[-12.8, -49.4], [-12.8, -48.8], [-12.2, -48.8], [-12.2, -49.4], [-12.8, -49.4]];
const dados = {
  atualizado_em: '2026-11-12T14:50:00+00:00',
  fontes: { inmet: { estado: 'ok', credito: 'INMET' }, firms: { estado: 'ok', credito: 'NASA FIRMS' } },
  avisos: [
    { id: 'inmet:1', tipo: 'chuva', gravidade: 'perigo', titulo: 'Chuvas', inicio: '2026-11-12T12:00:00+00:00', fim: '2026-11-13T02:59:00+00:00',
      vigente: true, poligonos: [quadrado], riscos: 'Alagamentos.', instrucoes: 'Evite áreas de risco.', link: 'https://avisos.inmet.gov.br/1' },
    { id: 'inmet:2', tipo: 'tempestade', gravidade: 'grande_perigo', titulo: 'Tempestade', inicio: '2026-11-13T03:00:00+00:00', fim: '2026-11-14T02:59:00+00:00',
      vigente: false, poligonos: [quadrado], riscos: '', instrucoes: '', link: '' }
  ],
  focos: [[-12.0, -49.1, '2026-11-12T10:00Z'], [-30.0, -51.0, '2026-11-12T10:00Z']],
  rodovias: [{ sigla: 'BR-153', avisos: ['inmet:1', 'inmet:2'], gravidade: 'perigo', gravidade_proxima: 'grande_perigo',
    proximo_inicio: '2026-11-13T03:00:00+00:00', focos_5km: 1 }],
  raio_fogo_km: 5
};

test('a verificação vira atrasada depois de 40 min e sem dados quando nunca rodou', () => {
  assert.strictEqual(M.estadoDados(dados, agora), 'ok');
  assert.strictEqual(M.estadoDados({ ...dados, atualizado_em: '2026-11-12T14:10:00+00:00' }, agora), 'atrasado');
  assert.strictEqual(M.estadoDados({ atualizado_em: null }, agora), 'sem_dados');
  assert.strictEqual(M.estadoDados(null, agora), 'sem_dados');
});

test('aviso de agora é área cheia; o dos próximos dias é só contorno tracejado', () => {
  const svg = M.svgCamadas(dados, rodovias, {});
  assert.match(svg, /data-aviso="inmet:1" data-vigente="1"[^>]*fill-opacity="\.16"/);
  assert.match(svg, /data-aviso="inmet:2" data-vigente="0"[^>]*fill-opacity="0"[^>]*stroke-dasharray/);
  assert.ok(svg.indexOf('inmet:2') < svg.indexOf('inmet:1'), 'o de agora fica por cima');
  assert.strictEqual((svg.match(/<circle/g) || []).length, 1, 'foco fora do recorte não é desenhado');
  for (const r of ['BR-153', 'BR-060', 'BR-010', 'BR-230']) assert.match(svg, new RegExp('data-rodovia="' + r + '"'));
});

test('as camadas desligadas somem do SVG', () => {
  const svg = M.svgCamadas(dados, rodovias, { avisos: true, focos: true });
  assert.doesNotMatch(svg, /<polygon|<circle/);
  assert.match(svg, /data-rodovia/);
  assert.doesNotMatch(M.svgCamadas(dados, rodovias, { rodovias: true }), /data-rodovia/);
});

test('a tabela por rodovia mostra o aviso de agora e o próximo com a hora de Brasília', () => {
  const [l] = M.linhasRodovias(dados);
  assert.deepStrictEqual([l.sigla, l.gravidade, l.proxima, l.focos, l.avisos.map(a => a.id)], ['BR-153', 'perigo', 'grande_perigo', 1, ['inmet:1']]);
  const html = M.painel(dados, agora);
  assert.match(html, /Grande perigo a partir de 13\/11 00:00/);
  assert.match(html, /Avisos do INMET valendo agora <span class="jtm-fraco">\(1\)/);
  assert.match(html, /Próximos dias <span class="jtm-fraco">\(1; tracejados no mapa\)/);
});

test('fonte fora do ar e verificação atrasada viram aviso, nunca "sem risco"', () => {
  const fora = { ...dados, atualizado_em: '2026-11-12T13:00:00+00:00', fontes: { ...dados.fontes, firms: { estado: 'indisponivel', credito: 'NASA FIRMS' } } };
  const avisos = M.avisosEstado(fora, agora);
  assert.strictEqual(avisos.length, 2);
  assert.match(avisos[0], /última verificação foi em 12\/11 10:00/);
  assert.match(avisos[1], /NASA FIRMS indisponível.*não quer dizer que não há risco/);
  assert.match(M.avisosEstado({ atualizado_em: null }, agora)[0], /ainda não rodou/);
  assert.deepStrictEqual(M.avisosEstado(dados, agora), []);
});

test('texto vindo da fonte é escapado', () => {
  const sujo = { ...dados, avisos: [{ ...dados.avisos[0], riscos: '<img src=x onerror=alert(1)>', link: 'javascript:alert(1)"' }] };
  const html = M.painel(sujo, agora);
  assert.doesNotMatch(html, /<img src=x/);
  assert.doesNotMatch(html, /href="javascript/);  // só link https do INMET vira âncora
});

test('recorte cobre GO, TO e o sul do PA com as imagens da NASA inteiras', () => {
  assert.deepStrictEqual(M.CAIXA, { oeste: -56.5, leste: -45.5, norte: -1.0, sul: -19.6 });
  assert.ok(M.TILES.length >= 9 && M.TILES.length <= 16, String(M.TILES.length));
  const [x, y] = M.xy(-16.68, -49.25);  // Goiânia
  assert.ok(x > 0 && x < M.LARG && y > 0 && y < M.ALT);
});
