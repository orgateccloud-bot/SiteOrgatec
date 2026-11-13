'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const M = require('../../site/assets/js/janela-transporte-mapa.js');

const GEO = path.join(__dirname, '../../site/assets/geo');
const ler = f => JSON.parse(fs.readFileSync(path.join(GEO, f), 'utf8'));
const ufs = ler('ufs.json').ufs, federais = ler('rodovias/BR.json'), rodoviasTO = ler('rodovias/TO.json');
const nomes = Object.fromEntries(ufs.map(e => [e.uf, e.nome]));

const agora = new Date('2026-11-12T15:00:00Z');  // 12/11, 12h em Brasília
const HOJE = '2026-11-12', AMANHA = '2026-11-13';
const quadrado = [[-12.8, -49.4], [-12.8, -48.8], [-12.2, -48.8], [-12.2, -49.4], [-12.8, -49.4]];
const fontes = { inmet: { estado: 'ok', credito: 'INMET' }, firms: { estado: 'ok', credito: 'NASA FIRMS' } };
const vazio = { gravidade: '', gravidade_proxima: '', focos_5km: 0, rodovias: 0 };
const nac = {
  atualizado_em: '2026-11-12T14:50:00+00:00', fontes, raio_fogo_km: 5, passo_calor: 0.25, focos_total: 5,
  avisos: [
    { id: 'inmet:1', tipo: 'chuva', gravidade: 'perigo', titulo: 'Chuvas', inicio: '2026-11-12T12:00:00+00:00', fim: '2026-11-13T02:59:00+00:00',
      vigente: true, ufs: ['TO'], poligonos: [quadrado], riscos: 'Alagamentos.', instrucoes: 'Evite áreas de risco.', link: 'https://avisos.inmet.gov.br/1' },
    { id: 'inmet:2', tipo: 'tempestade', gravidade: 'grande_perigo', titulo: 'Tempestade', inicio: '2026-11-13T03:00:00+00:00', fim: '2026-11-14T02:59:00+00:00',
      vigente: false, ufs: ['TO', 'GO'], poligonos: [quadrado], riscos: '', instrucoes: '', link: '' }
  ],
  calor: [[-12.25, -49.25, 3], [-3.25, -52.5, 40], [48.75, 2.25, 9]],
  ufs: { ...Object.fromEntries(ufs.map(e => [e.uf, vazio])),
    TO: { gravidade: 'perigo', gravidade_proxima: 'grande_perigo', focos_5km: 12, rodovias: 2 },
    PA: { gravidade: '', gravidade_proxima: '', focos_5km: 1635, rodovias: 9 } }
};
const est = {
  atualizado_em: nac.atualizado_em, uf: 'TO', fontes, raio_fogo_km: 5, focos_5km: 12,
  rodovias: [
    { sigla: 'BR-153', avisos: ['inmet:1', 'inmet:2'], gravidade: 'perigo', gravidade_proxima: 'grande_perigo', proximo_inicio: '2026-11-13T03:00:00+00:00', focos_5km: 1 },
    { sigla: 'TO-080', avisos: [], gravidade: '', gravidade_proxima: '', proximo_inicio: null, focos_5km: 11 }
  ],
  focos_perto: [[-12.0, -49.1], [-10.2, -48.6]]
};
const geoTO = { ufs, rodovias: rodoviasTO };
const calmo = { ...nac, avisos: [], calor: [], ufs: Object.fromEntries(ufs.map(e => [e.uf, vazio])) };

test('a verificação vira atrasada depois de 40 min e sem dados quando nunca rodou', () => {
  assert.strictEqual(M.estadoDados(nac, agora), 'ok');
  assert.strictEqual(M.estadoDados({ ...nac, atualizado_em: '2026-11-12T14:10:00+00:00' }, agora), 'atrasado');
  assert.strictEqual(M.estadoDados({ atualizado_em: null }, agora), 'sem_dados');
  assert.strictEqual(M.estadoDados(null, agora), 'sem_dados');
});

test('vistas: o Brasil cabe em 9 imagens da NASA e o estado aproxima sem passar de 900 × 1100', () => {
  assert.deepStrictEqual(M.BRASIL, { oeste: -74.5, leste: -34.5, norte: 5.5, sul: -34.0 });
  const br = M.vista(M.BRASIL, 0);
  assert.deepStrictEqual([br.z, br.tiles.length], [4, 9]);
  for (const e of ufs) {
    const v = M.vista({ sul: e.caixa[0], oeste: e.caixa[1], norte: e.caixa[2], leste: e.caixa[3] });
    assert.ok(v.z > 4 && v.z <= 8 && v.LARG <= 900 && v.ALT <= 1100 && v.tiles.length <= 30, e.uf + ' z' + v.z + ' ' + v.tiles.length);
    const [x, y] = M.xy(v, (e.caixa[0] + e.caixa[2]) / 2, (e.caixa[1] + e.caixa[3]) / 2);
    assert.ok(x > 0 && x < v.LARG && y > 0 && y < v.ALT, e.uf);
  }
});

test('os três dias seguem o horário de Brasília; no estado só entram os avisos que cruzam rodovia dali', () => {
  assert.deepStrictEqual(M.dias(agora).map(d => [d.chave, d.rotulo]), [[HOJE, 'Hoje'], [AMANHA, 'Amanhã'], ['2026-11-14', 'sáb 14/11']]);
  assert.strictEqual(M.dias(new Date('2026-11-13T01:00:00Z'))[0].chave, HOJE);  // 01h UTC ainda é o dia anterior em Brasília
  assert.deepStrictEqual(M.avisosDoDia(nac, HOJE).map(a => a.id), ['inmet:1']);
  assert.deepStrictEqual(M.avisosDoDia(nac, AMANHA, 'GO').map(a => a.id), ['inmet:2']);
  assert.deepStrictEqual(M.avisosDoDia(nac, HOJE, 'GO'), []);
});

test('mapa do Brasil: 27 estados clicáveis, federais, manchas de fogo e os avisos do dia sem roubar o toque', () => {
  const svg = M.svgBrasil(nac, { ufs, federais }, {}, { dia: HOJE });
  for (const e of ufs) assert.match(svg, new RegExp('class="jtm-uf" data-uf="' + e.uf + '"'));
  assert.match(svg, /data-rodovia="BR-153"/);
  assert.strictEqual((svg.match(/class="jtm-calor"/g) || []).length, 2, 'a célula fora do recorte não é desenhada');
  assert.match(svg, /data-aviso="inmet:1" data-vigente="1"[^>]*pointer-events="none"/);
  assert.doesNotMatch(svg, /inmet:2|data-rodovia-alvo/);
  const semCamadas = M.svgBrasil(nac, { ufs, federais }, { avisos: true, focos: true, rodovias: true }, { dia: HOJE });
  assert.doesNotMatch(semCamadas, /jtm-calor|jtm-area|data-rodovia=/);
  assert.match(semCamadas, /class="jtm-uf"/);
  assert.match(M.svgBrasil(null, { ufs, federais: null }, {}, {}), /class="jtm-uf"/);  // sem dados e sem federais ainda desenha os estados
});

test('mapa do estado: rodovias com alvo de toque, focos junto a elas, aviso clicável e rodovia marcada', () => {
  const svg = M.svgEstado(nac, est, geoTO, {}, { dia: HOJE }, 'TO');
  for (const r of rodoviasTO.rodovias.slice(0, 5)) assert.match(svg, new RegExp('data-rodovia-alvo="' + r.sigla + '"'));
  assert.strictEqual((svg.match(/class="jtm-foco-perto"/g) || []).length, 2);
  assert.match(svg, /class="jtm-uf" data-uf="TO" data-marcada="1"/);
  assert.match(svg, /data-aviso="inmet:1" data-vigente="1"/);
  assert.doesNotMatch(svg, /data-aviso="inmet:1"[^>]*pointer-events="none"/);
  assert.doesNotMatch(svg, /inmet:2/);
  const amanha = M.svgEstado(nac, est, geoTO, {}, { dia: AMANHA, rodovia: 'BR-153' }, 'TO');
  assert.match(amanha, /data-aviso="inmet:2" data-vigente="0"[^>]*fill-opacity="\.08"[^>]*stroke-dasharray/);
  assert.match(amanha, /data-rodovia="BR-153" data-marcada="1"[^>]*stroke="#38bdf8"/);
  assert.match(amanha, /class="jtm-rotulo jtm-rotulo-marcado"/);
  const semCamadas = M.svgEstado(nac, est, geoTO, { avisos: true, focos: true, rodovias: true }, {}, 'TO');
  assert.doesNotMatch(semCamadas, /jtm-area|jtm-foco-perto|jtm-calor|data-rodovia/);
  assert.strictEqual(M.svgEstado(nac, est, geoTO, {}, {}, 'XX'), '');
  assert.match(M.svgEstado(nac, null, { ufs, rodovias: null }, {}, {}, 'TO'), /data-uf="TO"/);  // estado ainda carregando
});

test('veredito do Brasil: aviso grave, depois os estados com mais fogo; incerto com verificação incompleta', () => {
  const v = M.vereditoBrasil(nac, agora);
  assert.strictEqual(v.nivel, 'perigo');
  assert.strictEqual(v.frases[0], 'Aviso de Perigo do INMET sobre rodovias de TO agora.');
  assert.strictEqual(v.frases[1], 'Mais focos de fogo junto a rodovias nas últimas 24 h: PA (1.635). Atenção à fumaça.');
  assert.deepStrictEqual(M.vereditoBrasil(calmo, agora), { nivel: 'ok', frases: ['Sem aviso do INMET sobre rodovias e sem concentração de focos de fogo junto a elas agora.'] });
  const leve = { ...calmo, ufs: { ...calmo.ufs, GO: { ...vazio, gravidade: 'potencial' }, MT: { ...vazio, gravidade: 'potencial' } } };
  assert.deepStrictEqual(M.vereditoBrasil(leve, agora), { nivel: 'atencao', frases: ['Aviso de perigo potencial do INMET sobre rodovias de 2 estados, sem aviso grave agora.'] });
  assert.strictEqual(M.vereditoBrasil({ ...calmo, fontes: { ...fontes, firms: { estado: 'indisponivel' } } }, agora).nivel, 'incerto');
  assert.strictEqual(M.vereditoBrasil({ ...calmo, atualizado_em: '2026-11-12T13:00:00+00:00' }, agora).nivel, 'incerto');
  assert.strictEqual(M.vereditoBrasil({ atualizado_em: null }, agora).nivel, 'incerto');
});

test('veredito do estado: rodovias sob aviso e a que tem mais focos', () => {
  const v = M.veredito(est, agora);
  assert.strictEqual(v.nivel, 'perigo');
  assert.strictEqual(v.frases[0], 'BR-153 sob aviso de Perigo do INMET agora.');
  assert.strictEqual(v.frases[1], 'TO-080: 11 focos de fogo a até 5 km nas últimas 24 h. Atenção à fumaça.');
  assert.strictEqual(M.veredito({ ...est, rodovias: [] }, agora).nivel, 'ok');
  assert.strictEqual(M.veredito({ atualizado_em: null }, agora).nivel, 'incerto');
});

test('cartões dos estados: os com aviso ou foco primeiro, pela gravidade do dia', () => {
  const linhas = M.resumoEstados(nac, HOJE, nomes);
  assert.strictEqual(linhas.length, 27);
  assert.deepStrictEqual([linhas[0].uf, linhas[0].nome, linhas[0].gravidade, linhas[0].valendo, linhas[0].focos], ['TO', 'Tocantins', 'perigo', true, 12]);
  assert.deepStrictEqual([linhas[1].uf, linhas[1].gravidade, linhas[1].focos, linhas[1].parte], ['PA', '', 1635, 1]);
  const amanha = M.resumoEstados(nac, AMANHA, nomes);
  assert.deepStrictEqual(amanha.slice(0, 2).map(l => [l.uf, l.gravidade, l.valendo, l.inicio]),
    [['TO', 'grande_perigo', false, '2026-11-13T03:00:00+00:00'], ['GO', 'grande_perigo', false, '2026-11-13T03:00:00+00:00']]);
  const html = M.painelBrasil(nac, agora, { dia: HOJE }, nomes);
  assert.match(html, /^<div class="jtm-veredito"[^>]*data-nivel="perigo" role="status">/);
  assert.match(html, /data-jtm-uf="TO"><span class="jtm-via-sigla">TO <span class="jtm-fraco">Tocantins<\/span>/);
  assert.strictEqual((html.match(/data-jtm-uf=/g) || []).length, 2, 'só os estados com aviso ou foco viram cartão');
  assert.strictEqual((html.match(/<option value="[A-Z]{2}">/g) || []).length, 27);
  assert.match(html, /Avisos de hoje no Brasil <span class="jtm-fraco">\(1\)/);
  assert.match(html, /<p class="jtm-rodape">INMET ok · NASA FIRMS ok · verificado em 12\/11 11:50<\/p>$/);
  assert.doesNotMatch(M.painelBrasil(nac, agora, { dia: HOJE }, nomes, true), /jtm-veredito/);
});

test('painel do estado: voltar, cartões por rodovia e a lista filtrada pela rodovia marcada', () => {
  const [a, b] = M.resumoRodovias(est, nac, HOJE);
  assert.deepStrictEqual([a.sigla, a.gravidade, a.valendo, a.tipos, a.inicio, a.focos], ['BR-153', 'perigo', true, ['Chuva forte'], '', 1]);
  assert.deepStrictEqual([b.sigla, b.gravidade, b.focos, b.parte], ['TO-080', '', 11, 1]);
  const html = M.painelEstado(nac, est, agora, { dia: AMANHA }, 'TO', 'Tocantins', ['BR-153', 'TO-080', 'TO-010']);
  assert.match(html, /data-jtm-voltar>← Brasil<\/button><h3 class="jtm-titulo jtm-estado-nome">Tocantins/);
  assert.match(html, /data-jtm-rodovia="BR-153" aria-pressed="false"/);
  assert.match(html, /a partir de 13\/11 00:00/);
  assert.match(html, /data-jtm-dia="2026-11-13" aria-pressed="true">Amanhã/);
  assert.match(html, /Avisos de amanhã no estado <span class="jtm-fraco">\(1\)/);
  const marcada = M.painelEstado(nac, est, agora, { dia: HOJE, rodovia: 'TO-080' }, 'TO', 'Tocantins', []);
  assert.match(marcada, /Avisos de hoje na TO-080 <span class="jtm-fraco">\(0\)/);
  assert.match(marcada, /Nenhum aviso do INMET no traçado da TO-080 para hoje\./);
  assert.match(marcada, /class="jtm-limpar" data-jtm-rodovia="TO-080">ver todas as rodovias/);
});

test('busca por sigla acha rodovia sem alerta e mantém a marcada à vista', () => {
  const todas = ['BR-153', 'TO-080', 'TO-010', 'TO-050'];
  assert.deepStrictEqual((M.htmlRodovias(est, nac, { dia: HOJE }, 'to 0', todas).match(/data-jtm-rodovia="[^"]+"/g) || []),
    ['data-jtm-rodovia="TO-080"', 'data-jtm-rodovia="TO-010"', 'data-jtm-rodovia="TO-050"']);
  assert.match(M.htmlRodovias(est, nac, { dia: HOJE }, 'xx999', todas), /Nenhuma rodovia com essa sigla neste estado\./);
  assert.match(M.htmlRodovias(est, nac, { dia: HOJE, rodovia: 'TO-010' }, '', todas), /^<div class="jtm-vias"><button[^>]*data-jtm-rodovia="TO-010" aria-pressed="true"/);
  assert.match(M.htmlRodovias({ ...est, rodovias: [] }, nac, { dia: HOJE }, '', todas), /Nenhuma rodovia do estado com aviso/);
});

test('fonte fora do ar e verificação atrasada viram aviso, nunca "sem risco"', () => {
  const fora = { ...nac, atualizado_em: '2026-11-12T13:00:00+00:00', fontes: { ...fontes, firms: { estado: 'indisponivel', credito: 'NASA FIRMS' } } };
  const avisos = M.avisosEstado(fora, agora);
  assert.strictEqual(avisos.length, 2);
  assert.match(avisos[0], /última verificação foi em 12\/11 10:00/);
  assert.match(avisos[1], /NASA FIRMS indisponível.*não quer dizer que não há risco/);
  assert.match(M.avisosEstado({ atualizado_em: null }, agora)[0], /ainda não rodou/);
  assert.deepStrictEqual(M.avisosEstado(nac, agora), []);
  assert.match(M.painelBrasil(fora, agora, {}, nomes), /data-nivel="incerto"/);
});

test('texto vindo da fonte é escapado', () => {
  const sujo = { ...nac, avisos: [{ ...nac.avisos[0], riscos: '<img src=x onerror=alert(1)>', link: 'javascript:alert(1)"' }] };
  for (const html of [M.painelBrasil(sujo, agora, { dia: HOJE }, nomes), M.painelEstado(sujo, est, agora, { dia: HOJE }, 'TO', '<b>x</b>', [])]) {
    assert.doesNotMatch(html, /<img src=x|<b>x<\/b>/);
    assert.doesNotMatch(html, /href="javascript/);  // só link https do INMET vira âncora
  }
});
