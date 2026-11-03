const test = require('node:test');
const assert = require('node:assert/strict');
const H = require('../../site/assets/js/homologacao.js');
const req = (m) => require('../../site/assets/js/' + m);
const CONFIG = req('config.js');
const O = { config: CONFIG, fontes: req('fontes.js'), ufs: req('ufs.js'), regras: req('regras.js'), conteudo: req('conteudo.js'),
  reformaItens: req('reforma-itens.js'), calculadoras: req('calculadoras.js'), calendario: req('calendario.js'), validadores: req('validadores.js') };
const HOJE = '2026-10-31';
const ctx = (config) => ({ config: config || CONFIG, fontes: O.fontes, itens: O.reformaItens, ufs: O.ufs, conteudo: O.conteudo, hoje: HOJE });
const clone = (o) => JSON.parse(JSON.stringify(o));
const status = (av, id) => av.itens.find((i) => i.id === id).status;

test('lista: ids únicos, categoria, responsável e onde resolver em toda pendência', () => {
  const ids = new Set();
  for (const p of H.PENDENCIAS) {
    assert.ok(!ids.has(p.id), 'id repetido ' + p.id); ids.add(p.id);
    assert.ok(H.CATEGORIAS[p.categoria], p.id);
    assert.ok(H.RESPONSAVEL[p.responsavel], p.id);
    assert.ok(p.titulo && p.onde, p.id);
    assert.equal(typeof p.bloqueia, 'boolean', p.id);
  }
  for (const cat of Object.keys(H.CATEGORIAS)) assert.ok(H.PENDENCIAS.some((p) => p.categoria === cat), cat);
});

test('modo teste: nada pronto para produção e configuração atual com pendências abertas', () => {
  const av = H.avaliar(ctx());
  assert.equal(CONFIG.ambiente, 'homologacao');
  assert.equal(av.resumo.prontoParaProducao, false);
  assert.ok(av.resumo.bloqueios > 0);
  for (const id of ['C1', 'C2', 'C3', 'C4', 'C5', 'D4', 'V1', 'T9']) assert.equal(status(av, id), 'aberta', id);
  assert.equal(status(av, 'V8'), 'resolvida'); // nenhum item com consulta antiga em 31/10/2026
  assert.equal(av.resumo.total, H.PENDENCIAS.length);
  assert.equal(av.resumo.abertas + av.resumo.resolvidas, av.resumo.total);
});

test('verificação automática acompanha a configuração', () => {
  const c = clone(CONFIG);
  c.capturaXml.ferramenta = 'sieg';
  c.portal.erp = 'onvio';
  c.emails.contato.ativo = true;
  c.emails.dpo.ativo = true;
  c.whatsapp.validado = true;
  c.institucional = { inicioAtuacao: '1975-03-01', comprovacao: 'contrato social' };
  const av = H.avaliar(ctx(c));
  for (const id of ['C1', 'C3', 'C4', 'C5', 'D4']) assert.equal(status(av, id), 'resolvida', id);
  assert.equal(status(av, 'C2'), 'aberta'); // falta o alvo do CNAME
  assert.match(av.itens.find((i) => i.id === 'C2').detalhe, /falta o alvo do CNAME/);
  c.portal.cnameAlvo = 'cliente.exemplo-erp.com';
  assert.equal(status(H.avaliar(ctx(c)), 'C2'), 'resolvida');
});

test('V1 conta itens sem revisão; V2 lista fontes pendentes; V3 lista UFs sem ICMS confirmado', () => {
  const av = H.avaliar(ctx());
  assert.match(av.itens.find((i) => i.id === 'V1').detalhe, new RegExp('^' + O.reformaItens.length + ' de ' + O.reformaItens.length));
  const pendentes = O.fontes.lista.filter((f) => !f.validado).length;
  assert.match(av.itens.find((i) => i.id === 'V2').detalhe, new RegExp('^' + pendentes + ' pendentes'));
  assert.match(av.itens.find((i) => i.id === 'V3').detalhe, /TO/);
});

test('pendência marcada à mão e erro de verificação não derrubam a avaliação', () => {
  const av = H.avaliar(Object.assign(ctx(), { resolvidaManual: ['D1', 'T6'] }));
  assert.equal(status(av, 'D1'), 'resolvida');
  assert.equal(status(av, 'T6'), 'resolvida');
  const quebrado = H.avaliar(Object.assign(ctx(), { config: {} }));
  const c1 = quebrado.itens.find((i) => i.id === 'C1');
  assert.equal(c1.status, 'aberta');
  assert.equal(c1.erro, true);
  assert.match(c1.detalhe, /Não foi possível verificar/);
});

test('exportação em Markdown traz todas as pendências e o resumo', () => {
  const av = H.avaliar(ctx());
  const md = H.comoTexto(av, '31/10/2026');
  assert.match(md, /^# Pendências para a próxima fase/);
  assert.match(md, new RegExp('Abertas: ' + av.resumo.abertas));
  for (const p of H.PENDENCIAS) assert.ok(md.includes('| ' + p.id + ' |'), p.id);
  for (const cat of Object.values(H.CATEGORIAS)) assert.ok(md.includes('## ' + cat), cat);
});

test('autoteste: todos os casos passam no modo teste', () => {
  const casos = H.autoteste(O, HOJE);
  assert.ok(casos.length >= 12);
  for (const c of casos) assert.ok(c.ok, c.nome + ': ' + c.detalhe);
});

test('autoteste acusa falha quando um módulo falta ou o ambiente não é de teste', () => {
  const semCalc = Object.assign({}, O, { calculadoras: undefined });
  const casos = H.autoteste(semCalc, HOJE);
  assert.equal(casos.find((c) => c.nome === 'Módulos carregados').ok, false);
  assert.equal(casos.find((c) => c.nome.startsWith('Transição')).ok, false);
  const prod = Object.assign({}, O, { config: Object.assign(clone(CONFIG), { ambiente: 'producao' }) });
  assert.equal(H.autoteste(prod, HOJE).find((c) => c.nome.startsWith('Modo teste')).ok, false);
});

test('pendência concluída no código (resolvida: true) sai das abertas', () => {
  const av = H.avaliar(ctx());
  assert.equal(status(av, 'T3'), 'resolvida');
  assert.ok(!H.comoTexto(av, '31/10/2026').includes('| T3 | Trocar o Tailwind via CDN pelo CSS compilado | aberta'));
});
