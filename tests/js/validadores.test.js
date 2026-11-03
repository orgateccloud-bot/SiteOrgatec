const test = require('node:test');
const assert = require('node:assert/strict');
const V = require('../../site/assets/js/validadores.js');
const D = require('../../site/assets/js/demo-dados.js');

test('CNPJ: válido conhecido e inválidos', () => {
  assert.equal(V.cnpjValido('11.222.333/0001-81'), true);
  assert.equal(V.cnpjValido('11.222.333/0001-44'), false);
  assert.equal(V.cnpjValido('00.000.000/0000-00'), false);
});

test('DV da chave de acesso (módulo 11) recalculado', () => {
  const k = '5226100734651200019055001000025412110254891';
  const dv = V.dvChave(k);
  assert.equal(V.analisarDocumento({ cnpj: '07.346.512/0001-90', uf: 'GO', tipo: 'NF-e', data: '2026-10-28', chave: k + dv })
    .checks.find(c => c.id === 'chave_dv').ok, true);
});

test('modelos de homologação: estrutura confere; DVs fictícios e NFS-e sinalizados', () => {
  assert.equal(D.capturaXml.length, 4);
  for (const d of D.capturaXml.filter(x => x.tipo !== 'NFS-e')) {
    const c = Object.fromEntries(V.analisarDocumento(d).checks.map(x => [x.id, x.ok]));
    assert.equal(c.chave_tamanho && c.chave_uf && c.chave_aamm && c.chave_cnpj && c.chave_modelo, true, d.id);
    assert.equal(c.chave_dv, false, d.id); // DV fictício na planilha
  }
  const nfse = V.analisarDocumento(D.capturaXml.find(x => x.tipo === 'NFS-e'));
  assert.equal(nfse.checks.find(c => c.id === 'nfse_origem').ok, false);
});

test('protocolos do portal: 4 registros, IPs mascarados, MFA lido', () => {
  assert.equal(D.protocolos.length, 4);
  for (const p of D.protocolos) {
    assert.match(p.auditoria.ip, /^\d{1,3}\.\d{1,3}\.\*\*\*\.\*\*\*$/);
    assert.equal(p.auditoria.mfa, true);
  }
  assert.ok(!JSON.stringify(D).includes('177.18.22.90'));
});

test('contato: e-mail e celular', () => {
  assert.ok(V.emailValido('a@b.com.br'));
  assert.ok(!V.emailValido('a@b'));
  assert.ok(V.celularValido('(62) 99294-9161'));
  assert.ok(V.celularValido('+55 62 99294-9161'));
  assert.ok(!V.celularValido('62 3333-4444'));
});
