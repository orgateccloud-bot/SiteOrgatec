/* Validadores determinísticos (rodam no navegador e no Node). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).validadores = factory();
})(this, function () {
  'use strict';

  // Código IBGE da UF (posições 1-2 da chave de acesso) — tabela IBGE de UFs.
  var CUF = {
    RO: '11', AC: '12', AM: '13', RR: '14', PA: '15', AP: '16', TO: '17',
    MA: '21', PI: '22', CE: '23', RN: '24', PB: '25', PE: '26', AL: '27', SE: '28', BA: '29',
    MG: '31', ES: '32', RJ: '33', SP: '35',
    PR: '41', SC: '42', RS: '43',
    MS: '50', MT: '51', GO: '52', DF: '53'
  };

  // Modelo do documento (posições 21-22): 55 = NF-e, 57 = CT-e, 65 = NFC-e (MOC NF-e / MOC CT-e).
  var MODELO_POR_TIPO = { 'NF-e': '55', 'CT-e': '57', 'NFC-e': '65' };

  function digitos(s) { return String(s == null ? '' : s).replace(/\D/g, ''); }

  function cnpjValido(cnpj) {
    var d = digitos(cnpj);
    if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false;
    function dv(n) {
      var pesos = n === 12 ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
      var s = 0;
      for (var i = 0; i < n; i++) s += Number(d[i]) * pesos[i];
      var r = s % 11;
      return r < 2 ? 0 : 11 - r;
    }
    return dv(12) === Number(d[12]) && dv(13) === Number(d[13]);
  }

  // Dígito verificador da chave de acesso (módulo 11, pesos 2..9 da direita para a esquerda).
  function dvChave(chave43) {
    var s = 0, peso = 2;
    for (var i = chave43.length - 1; i >= 0; i--) {
      s += Number(chave43[i]) * peso;
      peso = peso === 9 ? 2 : peso + 1;
    }
    var r = s % 11;
    return r < 2 ? 0 : 11 - r;
  }

  /**
   * Analisa um documento capturado (linha do modelo de homologação) e devolve a
   * lista de verificações. NFS-e não usa a chave de 44 posições da NF-e: o padrão
   * nacional (ADN) tem chave própria e não é autorizada pela SEFAZ estadual.
   */
  function analisarDocumento(doc) {
    var chave = digitos(doc.chave);
    var checks = [];
    function add(id, ok, msg) { checks.push({ id: id, ok: ok, msg: msg }); }

    add('cnpj_dv', cnpjValido(doc.cnpj), cnpjValido(doc.cnpj)
      ? 'CNPJ do emitente com dígitos verificadores válidos'
      : 'CNPJ do emitente com DV inválido (dado fictício de teste)');

    if (doc.tipo === 'NFS-e') {
      add('nfse_origem', false,
        'NFS-e não é autorizada pela SEFAZ e não usa chave de 44 posições modelo 55: verificar origem (prefeitura ou Ambiente de Dados Nacional da NFS-e)');
      return { ok: false, checks: checks };
    }

    add('chave_tamanho', chave.length === 44, 'Chave com ' + chave.length + ' dígitos (esperado 44)');
    if (chave.length === 44) {
      add('chave_uf', chave.slice(0, 2) === CUF[doc.uf],
        'cUF da chave = ' + chave.slice(0, 2) + ' (' + doc.uf + ' = ' + CUF[doc.uf] + ')');
      var aamm = String(doc.data || '').slice(2, 4) + String(doc.data || '').slice(5, 7);
      add('chave_aamm', chave.slice(2, 6) === aamm, 'AAMM da chave = ' + chave.slice(2, 6) + ' (emissão ' + doc.data + ')');
      add('chave_cnpj', chave.slice(6, 20) === digitos(doc.cnpj), 'CNPJ embutido na chave confere com o emitente');
      var modelo = MODELO_POR_TIPO[doc.tipo];
      add('chave_modelo', !!modelo && chave.slice(20, 22) === modelo,
        'Modelo ' + chave.slice(20, 22) + ' para ' + doc.tipo + (modelo ? ' (esperado ' + modelo + ')' : ''));
      var dv = dvChave(chave.slice(0, 43));
      add('chave_dv', dv === Number(chave[43]),
        'DV da chave = ' + chave[43] + ' (calculado ' + dv + ')' + (dv === Number(chave[43]) ? '' : ' — chave fictícia de teste'));
    }
    return { ok: checks.every(function (c) { return c.ok; }), checks: checks };
  }

  function emailValido(e) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(e || '').trim());
  }

  // Celular brasileiro com DDD: 11 dígitos (DDD + 9 + 8 dígitos), aceita prefixo 55.
  function celularValido(t) {
    var d = digitos(t);
    if (d.length === 13 && d.slice(0, 2) === '55') d = d.slice(2);
    return d.length === 11 && d[2] === '9' && Number(d.slice(0, 2)) >= 11;
  }

  function mascararCnpj(c) {
    var d = digitos(c);
    return d.length === 14 ? d.slice(0, 2) + '.' + d.slice(2, 5) + '.***/****-' + d.slice(12) : '***';
  }

  return {
    CUF: CUF, cnpjValido: cnpjValido, dvChave: dvChave, analisarDocumento: analisarDocumento,
    emailValido: emailValido, celularValido: celularValido, mascararCnpj: mascararCnpj, digitos: digitos
  };
});
