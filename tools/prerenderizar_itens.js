/* Pré-renderiza os itens da reforma e do compliance no HTML gerado, para quem não executa JavaScript (buscadores, leitores).
   Usa o mesmo conteudo.js e os mesmos dados do navegador (reforma-itens.js, compliance-itens.js, fontes.js), então não há segunda
   fonte de verdade. O navegador continua hidratando: paginas.js troca o instantâneo pelo conteúdo vivo (filtros, temas, selos).
   Em produção (config.ambiente = 'producao') só entram itens com revisão aprovada, como na tela.
   Uso:  node tools/prerenderizar_itens.js            grava nas páginas
         node tools/prerenderizar_itens.js --conferir sai com erro se alguma página estiver defasada (usado nos testes)
   Rode depois de gerar_paginas.py e gerar_hub.py (README, "Como regenerar"). É idempotente: o instantâneo fica entre
   <!--pre--> e <!--/pre-->. Só preenche blocos data-itens; notícias, alertas e prazos seguem no navegador. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');

const SITE = path.join(__dirname, '..', 'site');
const JS = path.join(SITE, 'assets', 'js');
const req = (m) => require(path.join(JS, m));
const K = req('conteudo.js');
const F = req('fontes.js');
const C = req('config.js');
const itensTodos = req('reforma-itens.js').concat(req('compliance-itens.js'));
const base = K.publicaveis(itensTodos, F.porId, C.ambiente);

function attr(tag, nome) {
  const m = tag.match(new RegExp('\\s' + nome + '(?:="([^"]*)")?(?=[\\s>])'));
  return m ? (m[1] === undefined ? '' : m[1]) : null;
}

function instantaneo(tag) {
  const fixo = { destino: attr(tag, 'data-destino') || null, setor: attr(tag, 'data-setor') || null };
  const limite = +attr(tag, 'data-limite') || 0;
  const inicial = +attr(tag, 'data-inicial') || 0;
  const recolher = attr(tag, 'data-recolher') !== null;
  let itens = K.filtrar(base.itens, fixo);
  if (limite) itens = itens.slice(0, limite);
  if (inicial && itens.length > inicial) itens = itens.slice(0, inicial);
  if (!itens.length) return '';
  return itens.map((it) => K.renderItem(it, F.porId, { recolhido: recolher })).join('');
}

const BLOCO = /(<div data-itens[^>]*>)([\s\S]*?)(<div class="lista-itens[^"]*">)(<!--pre-->[\s\S]*?<!--\/pre-->)?/g;

function processar(html) {
  return html.replace(BLOCO, (todo, abre, meio, lista) => {
    const dentro = instantaneo(abre);
    return abre + meio + lista + (dentro ? '<!--pre-->' + dentro + '<!--/pre-->' : '');
  });
}

function paginas(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return e.name === 'dados' ? [] : paginas(p);
    return e.name.endsWith('.html') ? [p] : [];
  });
}

const conferir = process.argv.includes('--conferir');
const defasadas = [];
let preenchidas = 0;
for (const arq of paginas(SITE)) {
  const antes = fs.readFileSync(arq, 'utf8');
  if (antes.indexOf('data-itens') < 0) continue;
  const depois = processar(antes);
  if (depois.indexOf('<!--pre-->') >= 0) preenchidas++;
  if (depois !== antes) {
    if (conferir) defasadas.push(path.relative(SITE, arq));
    else fs.writeFileSync(arq, depois, 'utf8');
  }
}
if (conferir && defasadas.length) {
  console.error('Páginas sem o instantâneo atual (rode node tools/prerenderizar_itens.js):\n  ' + defasadas.join('\n  '));
  process.exit(1);
}
console.log(conferir ? 'instantâneos em dia' : 'pré-renderizado: ' + preenchidas + ' páginas com itens (' + base.itens.length + ' itens publicáveis em ' + C.ambiente + ')');
