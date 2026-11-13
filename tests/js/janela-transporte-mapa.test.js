'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const M = require('../../site/assets/js/janela-transporte-mapa.js');

const agora = new Date('2026-11-12T15:00:00Z');  // 12/11, 12h em Brasília
const HOJE = '2026-11-12', AMANHA = '2026-11-13';
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
  rodovias: [
    { sigla: 'BR-153', avisos: ['inmet:1', 'inmet:2'], gravidade: 'perigo', gravidade_proxima: 'grande_perigo', proximo_inicio: '2026-11-13T03:00:00+00:00', focos_5km: 1 },
    { sigla: 'BR-230', avisos: [], gravidade: '', gravidade_proxima: '', proximo_inicio: null, focos_5km: 84 }
  ],
  raio_fogo_km: 5
};
const calmo = { ...dados, avisos: [], focos: [], rodovias: dados.rodovias.map(r => ({ ...r, avisos: [], gravidade: '', focos_5km: 2 })) };

test('a verificação vira atrasada depois de 40 min e sem dados quando nunca rodou', () => {
  assert.strictEqual(M.estadoDados(dados, agora), 'ok');
  assert.strictEqual(M.estadoDados({ ...dados, atualizado_em: '2026-11-12T14:10:00+00:00' }, agora), 'atrasado');
  assert.strictEqual(M.estadoDados({ atualizado_em: null }, agora), 'sem_dados');
  assert.strictEqual(M.estadoDados(null, agora), 'sem_dados');
});

test('os três dias seguem o horário de Brasília, e cada aviso cai no seu dia', () => {
  assert.deepStrictEqual(M.dias(agora).map(d => [d.chave, d.rotulo]), [[HOJE, 'Hoje'], [AMANHA, 'Amanhã'], ['2026-11-14', 'sáb 14/11']]);
  // 01h UTC ainda é o dia anterior em Brasília
  assert.strictEqual(M.dias(new Date('2026-11-13T01:00:00Z'))[0].chave, HOJE);
  assert.deepStrictEqual(M.avisosDoDia(dados, HOJE).map(a => a.id), ['inmet:1']);
  assert.deepStrictEqual(M.avisosDoDia(dados, AMANHA).map(a => a.id), ['inmet:2']);
});

test('veredito: aviso grave primeiro, depois o fogo; nunca "sem alerta" com verificação incompleta', () => {
  const v = M.veredito(dados, agora);
  assert.strictEqual(v.nivel, 'perigo');
  assert.match(v.frases[0], /^BR-153 sob aviso de Perigo do INMET agora\.$/);
  assert.match(v.frases[1], /^BR-230: 84 focos de fogo a até 5 km nas últimas 24 h\. Atenção à fumaça\.$/);
  assert.deepStrictEqual(M.veredito(calmo, agora), { nivel: 'ok', frases: ['Sem aviso do INMET e sem concentração de focos de fogo perto das rodovias agora.'] });
  const leve = { ...calmo, rodovias: calmo.rodovias.map(r => ({ ...r, gravidade: 'potencial' })) };
  assert.strictEqual(M.veredito(leve, agora).nivel, 'atencao');
  assert.match(M.veredito(leve, agora).frases[0], /perigo potencial do INMET em todas as rodovias, sem aviso grave agora/);
  const fora = { ...calmo, fontes: { ...calmo.fontes, firms: { estado: 'indisponivel', credito: 'x' } } };
  assert.strictEqual(M.veredito(fora, agora).nivel, 'incerto');
  assert.strictEqual(M.veredito({ ...calmo, atualizado_em: '2026-11-12T13:00:00+00:00' }, agora).nivel, 'incerto');
  assert.strictEqual(M.veredito({ atualizado_em: null }, agora).nivel, 'incerto');
});

test('focos junto à rodovia viram pontos; os demais, manchas por célula', () => {
  const br153 = rodovias.rodovias.find(r => r.sigla === 'BR-153').linhas[0];
  const junto = [br153[1][0] + 0.01, br153[1][1], 'x'];  // ~1 km do traçado
  const longe = [[-3.11, -55.02, 'x'], [-3.12, -55.03, 'x'], [-3.13, -55.04, 'x'], [-30, -51, 'x']];  // três na mesma célula e um fora do recorte
  const sep = M.separarFocos([junto].concat(longe), rodovias, 5);
  assert.deepStrictEqual(sep.perto, [[junto[0], junto[1]]]);
  assert.deepStrictEqual(sep.celulas, [{ lat: -3.25, lon: -55.25, n: 3 }]);
  const svg = M.svgCamadas({ ...dados, focos: [junto].concat(longe) }, rodovias, {});
  assert.strictEqual((svg.match(/class="jtm-foco-perto"/g) || []).length, 1);
  assert.match(svg, /class="jtm-calor"[^>]*><title>3 foco\(s\)<\/title>/);
});

test('o mapa mostra só os avisos do dia escolhido e destaca a rodovia marcada', () => {
  const hoje = M.svgCamadas(dados, rodovias, {}, { dia: HOJE });
  assert.match(hoje, /data-aviso="inmet:1" data-vigente="1"[^>]*fill-opacity="\.16"/);
  assert.doesNotMatch(hoje, /inmet:2/);
  const amanha = M.svgCamadas(dados, rodovias, {}, { dia: AMANHA, rodovia: 'BR-153' });
  assert.match(amanha, /data-aviso="inmet:2" data-vigente="0"[^>]*fill-opacity="\.08"[^>]*stroke-dasharray/);
  assert.doesNotMatch(amanha, /inmet:1/);
  assert.match(amanha, /data-rodovia="BR-153" data-marcada="1"[^>]*stroke="#38bdf8"/);
  assert.match(amanha, /data-rodovia="BR-230"[^>]*opacity="\.5"/);
  for (const r of ['BR-153', 'BR-060', 'BR-010', 'BR-230']) assert.match(hoje, new RegExp('data-rodovia-alvo="' + r + '"'));
});

test('as camadas desligadas somem do SVG', () => {
  const svg = M.svgCamadas(dados, rodovias, { avisos: true, focos: true });
  assert.doesNotMatch(svg, /<polygon|<circle|jtm-calor/);
  assert.match(svg, /data-rodovia=/);
  assert.doesNotMatch(M.svgCamadas(dados, rodovias, { rodovias: true }), /data-rodovia/);
});

test('cartões por rodovia: aviso do dia, hora de início do que ainda não começou e barra de focos', () => {
  const [a, b] = M.resumoRodovias(dados, HOJE);
  assert.deepStrictEqual([a.sigla, a.gravidade, a.valendo, a.tipos, a.inicio, a.focos], ['BR-153', 'perigo', true, ['Chuva forte'], '', 1]);
  assert.deepStrictEqual([b.sigla, b.gravidade, b.focos, b.parte], ['BR-230', '', 84, 1]);
  const [c] = M.resumoRodovias(dados, AMANHA);
  assert.deepStrictEqual([c.gravidade, c.valendo, c.inicio], ['grande_perigo', false, '2026-11-13T03:00:00+00:00']);
  const html = M.painel(dados, agora, { dia: AMANHA });
  assert.match(html, /data-jtm-rodovia="BR-153" aria-pressed="false"/);
  assert.match(html, /a partir de 13\/11 00:00/);
  assert.match(html, /data-jtm-dia="2026-11-13" aria-pressed="true">Amanhã/);
  assert.match(html, /Avisos de amanhã <span class="jtm-fraco">\(1\)/);
});

test('rodovia marcada filtra a lista de avisos e oferece voltar a todas', () => {
  const html = M.painel(dados, agora, { dia: HOJE, rodovia: 'BR-230' });
  assert.match(html, /Avisos de hoje na BR-230 <span class="jtm-fraco">\(0\)/);
  assert.match(html, /Nenhum aviso do INMET no traçado da BR-230 para hoje\./);
  assert.match(html, /class="jtm-limpar" data-jtm-rodovia="BR-230">ver todas as rodovias/);
  assert.match(M.painel(dados, agora, { dia: HOJE, rodovia: 'BR-153' }), /Avisos de hoje na BR-153 <span class="jtm-fraco">\(1\)/);
});

test('painel abre no veredito e fecha com as fontes e a hora da verificação', () => {
  const html = M.painel(dados, agora);
  assert.match(html, /^<div class="jtm-veredito"[^>]*data-nivel="perigo" role="status">/);
  assert.match(html, /<p class="jtm-rodape">INMET ok · NASA FIRMS ok · verificado em 12\/11 11:50<\/p>$/);
});

test('fonte fora do ar e verificação atrasada viram aviso, nunca "sem risco"', () => {
  const fora = { ...dados, atualizado_em: '2026-11-12T13:00:00+00:00', fontes: { ...dados.fontes, firms: { estado: 'indisponivel', credito: 'NASA FIRMS' } } };
  const avisos = M.avisosEstado(fora, agora);
  assert.strictEqual(avisos.length, 2);
  assert.match(avisos[0], /última verificação foi em 12\/11 10:00/);
  assert.match(avisos[1], /NASA FIRMS indisponível.*não quer dizer que não há risco/);
  assert.match(M.avisosEstado({ atualizado_em: null }, agora)[0], /ainda não rodou/);
  assert.deepStrictEqual(M.avisosEstado(dados, agora), []);
  assert.match(M.painel(fora, agora), /data-nivel="incerto"/);
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
