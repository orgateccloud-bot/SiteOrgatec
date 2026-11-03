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
