/* Ponte usada por tools/gerar_boletim_campo.py: lê a entrada (JSON) da entrada padrão, monta o boletim com
   site/assets/js/campo-regras.js, valida com site/assets/js/campo.js e escreve o boletim na saída padrão.
   Sai com código 1 se o boletim não passar na validação (o Python então não publica). */
'use strict';
const R = require('../site/assets/js/campo-regras.js');
const C = require('../site/assets/js/campo.js');

let texto = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (p) => { texto += p; });
process.stdin.on('end', () => {
  const boletim = R.montar(JSON.parse(texto));
  const erros = C.validar(boletim);
  if (erros.length) {
    process.stderr.write('boletim inválido: ' + erros.join('; ') + '\n');
    process.exit(1);
  }
  process.stdout.write(JSON.stringify(boletim));
});
