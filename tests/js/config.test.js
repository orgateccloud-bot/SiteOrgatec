const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('../../site/assets/js/config.js');

test('endereço da API por hospedagem: Firebase e orgatec.io usam a API publicada', () => {
  const api = { publica: 'https://orgatec-api.up.railway.app/' };
  assert.equal(C.resolverApiBase('orgatec-site.web.app', api), 'https://orgatec-api.up.railway.app');
  assert.equal(C.resolverApiBase('orgatec-site.firebaseapp.com', api), 'https://orgatec-api.up.railway.app');
  assert.equal(C.resolverApiBase('orgatec.io', api), 'https://orgatec-api.up.railway.app');
  assert.equal(C.resolverApiBase('WWW.ORGATEC.IO', api), 'https://orgatec-api.up.railway.app');
});

test('sem API publicada, a hospedagem estática cai no WhatsApp (null)', () => {
  assert.equal(C.resolverApiBase('orgatec-site.web.app', { publica: null }), null);
});

test('localhost, Docker e Railway servindo o site usam a mesma origem', () => {
  const api = { publica: 'https://a.b' };
  for (const h of ['localhost', '127.0.0.1', 'orgatec-api.up.railway.app', 'portal.orgatec.io', '', undefined])
    assert.equal(C.resolverApiBase(h, api), '', String(h));
});

test('domínio que só imita o da ORGATEC não recebe a API', () => {
  const api = { publica: 'https://a.b' };
  for (const h of ['orgatec.io.evil.com', 'falso-orgatec.io', 'web.app.evil.com'])
    assert.equal(C.resolverApiBase(h, api), '', h);
});

test('estado versionado: API ainda não publicada e mesma origem no Node', () => {
  assert.equal(C.api.publica, null);
  assert.equal(C.api.base, '');
});

test("Cloud Run pelo rewrite do Hosting: publica '' é mesma origem, não WhatsApp", () => {
  assert.equal(C.resolverApiBase('orgatec-site.web.app', { publica: '' }), '');
  assert.equal(C.resolverApiBase('orgatec.io', { publica: '' }), '');
  assert.equal(C.resolverApiBase('orgatec-site.web.app', { publica: undefined }), null);
});
