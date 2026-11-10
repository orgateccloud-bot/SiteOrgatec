/* Exporta a lista de pendências da próxima fase para docs/pendencias-proxima-fase.md.
   Fonte única: site/assets/js/homologacao.js (a mesma lista do painel site/testes/index.html).
   Uso:  node tools/exportar_pendencias.js [AAAA-MM-DD]
   O status das pendências automáticas reflete config.js, fontes.js, ufs.js e reforma-itens.js no momento da execução. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');

const JS = path.join(__dirname, '..', 'site', 'assets', 'js');
const req = (m) => require(path.join(JS, m));
const hoje = process.argv[2] || new Date().toISOString().slice(0, 10);
if (!/^\d{4}-\d{2}-\d{2}$/.test(hoje)) { console.error('Data inválida: use AAAA-MM-DD.'); process.exit(1); }

const H = req('homologacao.js');
const av = H.avaliar({
  config: req('config.js'), fontes: req('fontes.js'), itens: req('reforma-itens.js'), complianceItens: req('compliance-itens.js'),
  ufs: req('ufs.js'), conteudo: req('conteudo.js'), hoje
});
const destino = path.join(__dirname, '..', 'docs', 'pendencias-proxima-fase.md');
fs.writeFileSync(destino, H.comoTexto(av, hoje.split('-').reverse().join('/')) + '\n', 'utf8');
console.log(`gerado: docs/pendencias-proxima-fase.md (${av.resumo.abertas} abertas, ${av.resumo.bloqueios} bloqueiam a produção)`);
