/* Hash do texto que o responsável técnico revisa, de cada ponto, pergunta e peso por perfil.
   Usado por tools/aplicar_revisao.py (que confere o registro) e por tests/js/revisao-aplicada.test.js (que confere se um
   texto aprovado mudou depois da revisão). Mesma conta da tela de revisão: SHA-256 do JSON canônico do conteúdo.
   Uso:  node tools/revisao_hashes.js [pasta-dos-js]   (padrão: site/assets/js) */
'use strict';
const crypto = require('node:crypto');
const path = require('node:path');

const R = require(path.join(__dirname, '..', 'docs', 'revisao', 'revisao.js'));
const sha = (texto) => crypto.createHash('sha256').update(texto, 'utf8').digest('hex');

/* Hash de um grupo inteiro (todas as perguntas, ou todos os pesos): a revisão deles vale só se o grupo todo estiver igual. */
function agregado(lista) {
  return sha(R.canonico(lista.map((i) => [i.id, sha(R.canonico(i.conteudo))]).sort((a, b) => (a[0] < b[0] ? -1 : 1))));
}

function calcular(js) {
  const req = (m) => require(path.join(js, m));
  const reforma = req('reforma-itens.js');
  const compliance = req('compliance-itens.js');
  const O = { reformaItens: reforma, complianceItens: compliance, termometro: req('termometro.js') };
  const origem = {};
  reforma.forEach((i) => { origem['item:' + i.id] = 'reforma'; });
  compliance.forEach((i) => { origem['item:' + i.id] = 'compliance'; });
  const todos = R.todos(O);
  const itens = {};
  todos.forEach((i) => { itens[i.id] = { tipo: i.tipo, origem: origem[i.id] || null, hash: sha(R.canonico(i.conteudo)) }; });
  const grupo = (tipo) => { const l = todos.filter((i) => i.tipo === tipo); return { ids: l.map((i) => i.id), agregado: l.length ? agregado(l) : null }; };
  return { itens, perguntas: grupo('Pergunta'), pesos: grupo('Peso por perfil') };
}

module.exports = { calcular, agregado };

if (require.main === module) {
  const js = path.resolve(process.argv[2] || path.join(__dirname, '..', 'site', 'assets', 'js'));
  process.stdout.write(JSON.stringify(calcular(js)));
}
