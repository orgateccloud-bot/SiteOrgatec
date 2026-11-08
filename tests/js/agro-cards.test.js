// Cards Orgatec Audi Agro: textos das notícias e dos avisos (site/assets/js/agro-cards.js).
const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('../../site/assets/js/agro-cards.js');

const item = { titulo: 'Projeto cria política de rastreabilidade bovina <individual>', link: 'https://www.camara.leg.br/noticias/1', data: '2026-10-27T18:19-03:00',
  fonte: 'camara-agro', fonteNome: 'Agência Câmara · Agropecuária', coletadoEm: '2026-11-02T12:40-03:00' };

test('data e hora em Brasília', () => {
  assert.equal(A.dataHora('2026-11-02T12:40-03:00'), '02/11/2026 às 12h40');
  assert.equal(A.dataCurta('2026-10-27T18:19-03:00'), '27/10');
  assert.equal(A.dataHora(null), '');
});

test('manchete: link da fonte, texto escapado, fonte e data', () => {
  const h = A.itemHtml(item, {});
  assert.match(h, /href="https:\/\/www\.camara\.leg\.br\/noticias\/1" target="_blank" rel="noopener"/);
  assert.match(h, /&lt;individual&gt;/);
  assert.match(h, /Agência Câmara · Agropecuária · 27\/10/);
  assert.doesNotMatch(h, /coletado em/);
});

test('item de fonte que falhou mostra a data da coleta; link sem http é descartado', () => {
  assert.match(A.itemHtml(item, { 'camara-agro': true }), /coletado em 02\/11\/2026 às 12h40/);
  assert.equal(A.itemHtml(Object.assign({}, item, { link: 'javascript:alert(1)' }), {}), '');
});

test('lista vazia vira o aviso, sem inventar notícia', () => {
  assert.match(A.listaHtml([], {}, 'Sem notícia recente'), /Sem notícia recente/);
  assert.match(A.listaHtml(undefined, {}, 'Sem notícia recente'), /Sem notícia recente/);
});

test('situação das fontes: data da coleta e falhas com o último dado válido', () => {
  const ok = { geradoEm: '2026-11-02T12:40-03:00', fontes: [{ id: 'senado', nome: 'Agência Senado', ok: true }] };
  assert.equal(A.situacao(ok), 'Notícias coletadas em 02/11/2026 às 12h40 (horário de Brasília).');
  const falha = { geradoEm: '2026-11-02T17:00-03:00', fontes: [
    { id: 'senado', nome: 'Agência Senado', ok: false, ultimaColetaValida: '2026-11-02T12:40-03:00' },
    { id: 'receita', nome: 'Receita Federal', ok: false, ultimaColetaValida: null }] };
  assert.match(A.situacao(falha), /Agência Senado \(mostrando itens de 02\/11\/2026 às 12h40\)/);
  assert.match(A.situacao(falha), /Receita Federal \(sem itens anteriores\)/);
});

// ---- Fase 6: tema sem notícia recente mostra a última que houver e os links das fontes oficiais

const oficiais = [{ nome: 'Conab', url: 'https://www.gov.br/conab/pt-br/assuntos/noticias' }, { nome: 'Ruim', url: 'javascript:alert(1)' }];

test('data longa, para a notícia que pode ser antiga', () => {
  assert.equal(A.dataLonga('2026-07-06T09:00-03:00'), '06/07/2026');
  assert.equal(A.dataLonga(null), '');
});

test('tema sem notícia recente: aviso, última encontrada com a data completa e links das fontes oficiais', () => {
  const h = A.listaHtml([], {}, 'Sem notícia sobre o tema nos últimos 90 dias.', item, oficiais);
  assert.match(h, /Sem notícia sobre o tema nos últimos 90 dias\./);
  assert.match(h, /Última encontrada, de 27\/10\/2026:/);
  assert.match(h, /href="https:\/\/www\.camara\.leg\.br\/noticias\/1" target="_blank" rel="noopener"/);
  assert.match(h, /Acompanhe nas fontes oficiais: <a class="og-link" href="https:\/\/www\.gov\.br\/conab\/pt-br\/assuntos\/noticias"/);
  assert.doesNotMatch(h, /javascript:/);  // link que não é http(s) nunca vai para a tela
  assert.match(A.listaHtml([], { 'camara-agro': true }, 'x', item, []), /coletado em 02\/11\/2026 às 12h40/);
});

test('sem última nem links, só o aviso: nada é inventado', () => {
  const h = A.listaHtml([], {}, 'Sem notícia sobre o tema nos últimos 90 dias.', null, []);
  assert.equal((h.match(/<li/g) || []).length, 1);
  assert.equal(A.ultimaHtml({ titulo: 'x', link: 'ftp://x' }, {}), '');
  assert.equal(A.acompanheHtml(undefined), '');
});

test('com notícia recente a lista não mostra a última nem os links', () => {
  const h = A.listaHtml([item], {}, 'vazio', Object.assign({}, item, { titulo: 'Outra' }), oficiais);
  assert.doesNotMatch(h, /Última encontrada|Acompanhe|vazio/);
  assert.match(h, /rastreabilidade bovina/);
});
