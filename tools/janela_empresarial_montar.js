/* Ponte usada por tools/gerar_janela_empresarial.py: lê { hoje: 'AAAA-MM-DD', perfis: [{ id, regime, uf }] } da entrada padrão
   e escreve { perfis: { id: [prazos dos próximos 7 dias] }, mudou: [itens que mudaram na semana] } na saída padrão.
   Só usa dados do próprio site (calendario.js e reforma-itens.js): nenhuma fonte externa. */
'use strict';
const CAL = require('../site/assets/js/calendario.js');
const ITENS = require('../site/assets/js/reforma-itens.js');

const DIA = 86400000;
function somaDias(iso, n) { return new Date(Date.parse(iso) + n * DIA).toISOString().slice(0, 10); }

function prazos(hoje, perfil) {
  const fim = somaDias(hoje, 7);
  const [a, m] = hoje.split('-').map(Number);
  const proximo = m === 12 ? [a + 1, 1] : [a, m + 1];
  const lista = [];
  [[a, m], proximo].forEach(([ano, mes]) => {
    CAL.obrigacoesDoMes(ano, mes, { uf: perfil.uf, regime: perfil.regime }).forEach((o) => {
      if (o.data && o.data >= hoje && o.data <= fim) lista.push({ id: o.id, data: o.data, esfera: o.esfera, titulo: o.titulo, ajustada: !!o.ajustada, aConfirmar: !!o.pendente });
    });
  });
  lista.sort((x, y) => (x.data < y.data ? -1 : x.data > y.data ? 1 : x.id < y.id ? -1 : 1));
  return lista;
}

function mudou(hoje) {
  const desde = somaDias(hoje, -7);
  const saida = [];
  ITENS.forEach((it) => (it.historico || []).forEach((h) => {
    if (h.data >= desde && h.data <= hoje) saida.push({ id: it.id, titulo: it.titulo, data: h.data, nota: h.nota });
  }));
  saida.sort((x, y) => (x.data < y.data ? 1 : -1));
  return saida;
}

let texto = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (p) => { texto += p; });
process.stdin.on('end', () => {
  const e = JSON.parse(texto);
  const perfis = {};
  e.perfis.forEach((p) => { perfis[p.id] = prazos(e.hoje, p); });
  process.stdout.write(JSON.stringify({ perfis, mudou: mudou(e.hoje) }));
});
