// Mapa da Central de Viagem (site/assets/js/transporte-mapa.js): a parte que roda sem navegador, isto é, a transformação do resultado
// da viagem em marcadores com detalhes e fonte. O carregamento do Google Maps só é exercitado no navegador.
const test = require('node:test');
const assert = require('node:assert/strict');
const M = require('../../site/assets/js/transporte-mapa.js');

const resultado = {
  rota: { distancia_km: 100, geometria: [[-16.0, -49.0], [-15.5, -49.0], [-15.0, -49.0]] },
  pontos: [{ nome: 'Goiânia', uf: 'GO', lat: -16.0, lon: -49.0, km: 0 }, { nome: 'Uruaçu', lat: -15.5, lon: -49.0, km: 50 },
    { nome: 'Palmas', uf: 'TO', lat: null, lon: null, km: 100 }],
  pedagios: [{ nome: 'P5 - Campinorte', km: 30, lat: -15.7, lon: -49.0, valor: '85.80', tarifa_cat1: '14.30', eixos: 6, tarifa_oficial: true, fonte: 'ANTT; tarifa: tabela oficial' },
    { nome: 'Outra', km: 60, lat: -15.4, lon: -49.0, valor: '48.00', tarifa_cat1: '8.00', eixos: 6, tarifa_oficial: false, fonte: 'ANTT; tarifa: parâmetro' }],
  postos: [{ nome: 'Posto X', km: 40, lat: -15.6, lon: -49.0, endereco: 'BR-153', preco_diesel_referencia: null, preco_fonte: 'preço não disponível', fonte: 'Google Places' }],
  bloqueios: [{ descricao: 'Obra', km: 20, lat: -15.8, lon: -49.0, passagem_prevista: '2026-11-10T12:00:00+00:00', fonte: 'cadastrado pela transportadora' }],
  jornada: { eventos: [{ tipo: 'pernoite', km_inicio: 50, inicio: '2026-11-10T22:00:00+00:00' }] }
};

test('cada dado da viagem vira um marcador com fonte; ponto sem coordenada não aparece', () => {
  const c = M.camadas(resultado, {});
  const tipos = c.marcadores.map((m) => m.tipo);
  assert.deepEqual(tipos, ['origem', 'parada', 'pedagio', 'pedagio', 'posto', 'bloqueio', 'pernoite']);  // Palmas sem coordenada fica de fora
  c.marcadores.forEach((m) => { assert.ok(m.fonte, m.id); assert.ok(m.titulo); });
  const ped = c.marcadores.find((m) => m.id === 'pedagio-1');
  assert.match(ped.linhas[1][1], /48,00 \(estimado\)/);
  const posto = c.marcadores.find((m) => m.tipo === 'posto');
  assert.equal(posto.linhas.find((l) => l[0].startsWith('Diesel'))[1], 'não disponível');  // nada inventado
  assert.equal(c.posicao, null);
});

test('pernoite fica sobre o traçado, no km do plano', () => {
  const p = M.camadas(resultado, {}).marcadores.find((m) => m.tipo === 'pernoite');
  assert.ok(Math.abs(p.lat - -15.5) < 1e-9 && p.lon === -49.0);
});

test('caminhão: telemetria vence a posição informada; sem telemetria, vale a última informada', () => {
  const lanc = [
    { id: '1', tipo: 'posicao_manual', ts: '2026-11-10T10:00:00+00:00', lat: -15.9, lon: -49.0 },
    { id: '2', tipo: 'posicao_manual', ts: '2026-11-10T11:00:00+00:00', lat: -15.8, lon: -49.0 },
    { id: '3', tipo: 'abastecimento', ts: '2026-11-10T09:00:00+00:00', lat: -15.95, lon: -49.0, valor: '1500.00', litros: '250' }
  ];
  let c = M.camadas(resultado, { lancamentos: lanc });
  const cam = c.marcadores.find((m) => m.tipo === 'caminhao');
  assert.equal(cam.lat, -15.8);
  assert.equal(cam.fonte, 'informado manualmente');
  assert.equal(c.marcadores.filter((m) => m.tipo === 'lancamento').length, 1);  // a posição informada não duplica como lançamento
  assert.equal(c.marcadores.find((m) => m.tipo === 'lancamento').fonte, 'informado manualmente');
  c = M.camadas(resultado, { lancamentos: lanc, posicao: { lat: -15.1, lon: -49.0, ts: '2026-11-10T12:00:00+00:00', sensor: 'Rastreador 1', km_percorrido: 90 } });
  const tel = c.marcadores.find((m) => m.tipo === 'caminhao');
  assert.equal(tel.lat, -15.1);
  assert.match(tel.fonte, /^telemetria: Rastreador 1/);
});

test('traçado apagado (30 dias) não quebra: sem rota nem pernoite, o resto continua', () => {
  const c = M.camadas({ ...resultado, rota: { distancia_km: 100, geometria: [] } }, {});
  assert.deepEqual(c.rota, []);
  assert.ok(!c.marcadores.some((m) => m.tipo === 'pernoite'));
  assert.ok(c.marcadores.some((m) => m.tipo === 'pedagio'));
});

test('legenda cobre todos os tipos de marcador', () => {
  const grupos = new Set(M.GRUPOS.map((g) => g[0]));
  Object.keys(M.TIPOS).forEach((t) => assert.ok(grupos.has(['origem', 'destino', 'parada'].includes(t) ? 'pontos' : t), t));
});

test('alerta de rota ativo vira marcador na cor da gravidade e área; encerrado não aparece', () => {
  const alerta = (id, estado, gravidade) => ({
    id, estado, lat: -15.0, lon: -49.1, km_ini: 120, km_fim: 160, chegada_prevista: '2026-11-12T15:00:00+00:00',
    alerta: { tipo: 'tempestade', gravidade, titulo: 'Tempestade (Perigo)', fim: '2026-11-13T02:59:00+00:00', fonte: 'INMET',
      poligonos: [[[-15.2, -49.3], [-15.2, -48.9], [-14.8, -48.9], [-15.2, -49.3]]] }
  });
  const c = M.camadas(resultado, { alertas: [alerta('a1', 'ativo', 'grande_perigo'), alerta('a2', 'encerrado', 'perigo')] });
  const mk = c.marcadores.filter((m) => m.tipo === 'alerta');
  assert.equal(mk.length, 1);
  assert.equal(mk[0].id, 'alerta-a1');
  assert.equal(mk[0].cor, M.COR_GRAVIDADE.grande_perigo);
  assert.equal(mk[0].letra, 'T');
  assert.equal(mk[0].fonte, 'INMET');
  assert.equal(c.areas.length, 1);
  assert.equal(c.areas[0].grupo, 'alerta');
  assert.deepEqual(M.camadas(resultado, {}).areas, []);
});
