const test = require('node:test');
const assert = require('node:assert/strict');
const K = require('../../site/assets/js/conteudo.js');
const F = require('../../site/assets/js/fontes.js');
const ITENS = require('../../site/assets/js/reforma-itens.js');

function base(o) {
  return Object.assign({
    id: 'x', titulo: 'Título', fato: 'Fato verificado.', status: 'em_vigor', consultadoEm: '2026-10-31',
    fontes: ['adct_126'], setores: ['todos'], tributos: ['cbs'], destinos: ['reforma'],
    revisao: { status: 'pendente', por: null, em: null }, historico: []
  }, o);
}

test('todos os itens publicados são válidos, com fonte existente e id único', () => {
  const ids = new Set();
  for (const it of ITENS) {
    assert.deepEqual(K.validarItem(it, F.porId), [], it.id);
    assert.ok(!ids.has(it.id), 'id repetido: ' + it.id);
    ids.add(it.id);
  }
  assert.ok(ITENS.length >= 30);
});

test('cobertura mínima do levantamento: tributos, setores, status e destinos', () => {
  const tributos = new Set(ITENS.flatMap(i => i.tributos));
  for (const t of ['cbs', 'ibs', 'is', 'piscofins', 'ipi', 'icms', 'iss', 'irpf']) assert.ok(tributos.has(t), t);
  assert.ok(K.filtrar(ITENS, { setor: 'agro' }).some(i => i.setores.includes('agro')));
  assert.ok(K.filtrar(ITENS, { setor: 'transporte' }).some(i => i.setores.includes('transporte')));
  for (const s of ['em_vigor', 'vigencia_futura', 'pendente_regulamentacao']) assert.ok(ITENS.some(i => i.status === s), s);
  for (const d of ['home', 'tributario', 'reforma', 'setor-agro', 'setor-transporte', 'ferramentas', 'cliente', 'noticias'])
    assert.ok(ITENS.some(i => i.destinos.includes(d)), d);
});

test('nenhum item sai aprovado sem revisão técnica do responsável', () => {
  for (const it of ITENS) assert.equal(it.revisao.status, 'pendente', it.id);
});

test('validação: campos obrigatórios, status, datas, fontes, setor, tributo, destino', () => {
  assert.deepEqual(K.validarItem(base(), F.porId), []);
  assert.deepEqual(K.validarItem(null, F.porId), ['item ausente ou inválido']);
  assert.ok(K.validarItem(base({ fontes: [] }), F.porId).includes('campo obrigatório ausente: fontes'));
  assert.ok(K.validarItem(base({ fato: '' }), F.porId).includes('campo obrigatório ausente: fato'));
  assert.ok(K.validarItem(base({ fontes: ['nao_existe'] }), F.porId).includes('fonte inexistente: nao_existe'));
  assert.ok(K.validarItem(base({ status: 'vigente' }), F.porId).includes('status inválido: vigente'));
  assert.ok(K.validarItem(base({ consultadoEm: '2026-02-30' }), F.porId).some(e => e.startsWith('data de consulta inválida')));
  assert.ok(K.validarItem(base({ consultadoEm: '31/10/2026' }), F.porId).some(e => e.startsWith('data de consulta inválida')));
  assert.ok(K.validarItem(base({ setores: ['saude'] }), F.porId).includes('setor inválido: saude'));
  assert.ok(K.validarItem(base({ tributos: ['iof'] }), F.porId).includes('tributo inválido: iof'));
  assert.ok(K.validarItem(base({ destinos: ['blog'] }), F.porId).includes('destino inválido: blog'));
  assert.ok(K.validarItem(base({ revisao: { status: 'aprovada' } }), F.porId).includes('revisão aprovada exige responsável e data'));
  assert.ok(K.validarItem(base({ historico: [{ data: 'ontem', nota: 'x' }] }), F.porId).includes('histórico inválido'));
});

test('publicação: inválido nunca aparece; produção só com revisão aprovada', () => {
  const aprovado = base({ id: 'ok', revisao: { status: 'aprovada', por: 'Robson Alain Veloso', em: '2026-11-01' } });
  const lista = [base({ id: 'pend' }), aprovado, base({ id: 'ruim', fontes: [] })];
  const h = K.publicaveis(lista, F.porId, 'homologacao');
  assert.deepEqual(h.itens.map(i => i.id), ['pend', 'ok']);
  assert.deepEqual(h.rejeitados.map(r => r.id), ['ruim']);
  const p = K.publicaveis(lista, F.porId, 'producao');
  assert.deepEqual(p.itens.map(i => i.id), ['ok']);
  assert.ok(p.rejeitados.some(r => r.id === 'pend' && r.erros[0] === 'revisão técnica pendente'));
  assert.equal(K.publicaveis(ITENS, F.porId, 'producao').itens.length, 0);
  assert.deepEqual(K.publicaveis(undefined, F.porId, 'producao').itens, []);
});

test('filtros: setor "todos" aparece em qualquer setor; combinação de filtros', () => {
  const lista = [base({ id: 'a', setores: ['agro'] }), base({ id: 't', setores: ['todos'] }), base({ id: 'tr', setores: ['transporte'], tributos: ['ibs'], status: 'vigencia_futura' })];
  assert.deepEqual(K.filtrar(lista, { setor: 'agro' }).map(i => i.id), ['a', 't']);
  assert.deepEqual(K.filtrar(lista, { setor: 'transporte', tributo: 'ibs' }).map(i => i.id), ['tr']);
  assert.deepEqual(K.filtrar(lista, { status: 'vigencia_futura' }).map(i => i.id), ['tr']);
  assert.equal(K.filtrar(lista, {}).length, 3);
  assert.equal(K.filtrar(lista).length, 3);
});

test('manutenção: itens com consulta antiga aparecem como atrasados', () => {
  const lista = [base({ id: 'novo', consultadoEm: '2026-10-31' }), base({ id: 'velho', consultadoEm: '2026-06-01' })];
  assert.deepEqual(K.atrasados(lista, '2026-10-31').map(i => i.id), ['velho']);
  assert.deepEqual(K.atrasados(lista, '2026-10-31', 200), []);
  assert.equal(K.atrasados(lista, '2027-01-30', 90).filter(i => i.id === 'novo').length, 1); // 91 dias: atrasado
  assert.equal(K.atrasados(lista, '2027-01-29', 90).filter(i => i.id === 'novo').length, 0); // 90 dias: ainda em dia
});

test('notícias: histórico de todos os itens, do mais recente ao mais antigo', () => {
  const n = K.noticias(ITENS);
  assert.ok(n.length >= 5);
  for (let i = 1; i < n.length; i++) assert.ok(n[i - 1].data >= n[i].data);
  assert.equal(K.noticias(ITENS, 3).length, 3);
  assert.deepEqual(K.noticias([base()]), []);
});

test('renderização: selo de status, revisão, fonte com link, data de consulta e orientação separada', () => {
  const html = K.renderItem(base({ orientacao: 'Leitura da ORGATEC.', vigencia: '01/01/2027', status: 'vigencia_futura' }), F.porId);
  assert.match(html, /og-selo-futuro">Aprovado, vigência futura/);
  assert.match(html, /em revisão técnica/);
  assert.match(html, /href="https:\/\/www\.planalto\.gov\.br\/ccivil_03\/constituicao\/constituicao\.htm"/);
  assert.match(html, /Consultado em 31\/10\/2026 · Vigência: 01\/01\/2027/);
  assert.match(html, /Orientação ORGATEC \(interpretação, não é texto legal\)/);
  const aprovado = K.renderItem(base({ revisao: { status: 'aprovada', por: 'RT', em: '2026-11-01' } }), F.porId);
  assert.doesNotMatch(aprovado, /em revisão técnica/);
  assert.doesNotMatch(aprovado, /Orientação ORGATEC/);
});

test('renderização: fonte não validada leva o selo pendente; texto é escapado', () => {
  const html = K.renderItem(base({ fontes: ['rfb_lcdpr'], titulo: '<script>x</script>' }), F.porId);
  assert.match(html, /pendente de validação/);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
});

test('renderização recusa item inválido', () => {
  assert.throws(() => K.renderItem(base({ fontes: [] }), F.porId), /inválido/);
  assert.throws(() => K.renderItem(base({ status: 'x' }), F.porId), /status inválido/);
});

test('anos de atuação: só com data válida, no passado e com comprovação', () => {
  assert.equal(K.anosAtuacao({ inicioAtuacao: null, comprovacao: null }, '2026-10-31'), null);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-03-01', comprovacao: '' }, '2026-10-31'), null);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-03-01' }, '2026-10-31'), null);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-13-01', comprovacao: 'contrato' }, '2026-10-31'), null);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '2030-01-01', comprovacao: 'contrato' }, '2026-10-31'), null);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-03-01', comprovacao: 'contrato' }, '2026-10-31'), 51);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-11-01', comprovacao: 'contrato' }, '2026-10-31'), 50);
  assert.equal(K.anosAtuacao({ inicioAtuacao: '1975-10-31', comprovacao: 'contrato' }, '2026-10-31'), 51);
  assert.equal(K.anosAtuacao(undefined, '2026-10-31'), null);
});

test('configuração atual não exibe anos de atuação (falta comprovação)', () => {
  global.window = undefined;
  const fs = require('node:fs');
  const src = fs.readFileSync(require.resolve('../../site/assets/js/config.js'), 'utf8');
  const root = {};
  new Function('window', src.replace(/\}\)\(typeof window[^)]*\)\s*;?\s*$/, '})(window);'))(root);
  const C = root.Orgatec ? root.Orgatec.config : null;
  if (C) assert.equal(K.anosAtuacao(C.institucional, '2026-10-31'), null);
  assert.match(src, /inicioAtuacao: null/);
  assert.match(src, /comprovacao: null/);
});


// ---- Página Agro: tema, filtro por tema e item recolhível

test('tema: opcional, mas se vier precisa existir; filtro por tema', () => {
  assert.deepEqual(K.validarItem(base({ tema: 'aliquotas' }), F.porId), []);
  assert.ok(K.validarItem(base({ tema: 'inventado' }), F.porId).some((e) => /tema inválido/.test(e)));
  const lista = [base({ id: 'a', tema: 'aliquotas' }), base({ id: 'b', tema: 'produtor' }), base({ id: 'c' })];
  assert.deepEqual(K.filtrar(lista, { tema: 'produtor' }).map((i) => i.id), ['b']);
  assert.equal(K.filtrar(lista, {}).length, 3);
  assert.ok(Object.keys(K.TEMAS).length >= 2);
});

test('todo item do agro tem tema válido (a lista recolhida do agro se agrupa por tema)', () => {
  const doAgro = ITENS.filter((i) => i.destinos.includes('setor-agro'));
  assert.ok(doAgro.length >= 6);
  doAgro.forEach((i) => assert.ok(K.TEMAS[i.tema], `${i.id} sem tema válido`));
  assert.ok(new Set(doAgro.map((i) => i.tema)).size >= 3);
});

test('item recolhido: título, status e referência à vista; fato, orientação e fontes dentro, sem perder nada', () => {
  const item = base({ tema: 'aliquotas', orientacao: 'Leitura da ORGATEC.', vigencia: '2029–2032', status: 'vigencia_futura' });
  const html = K.renderItem(item, F.porId, { recolhido: true });
  assert.match(html, /^<details class="og-cartao og-item og-item-recolhivel"/);
  assert.match(html, /data-tema="aliquotas"/);
  const [resumo, corpo] = html.split('</summary>');
  assert.match(resumo, /<h3 class="og-cartao-titulo">/);
  assert.match(resumo, /og-selo-futuro">Aprovado, vigência futura/);
  assert.doesNotMatch(resumo, /og-item-fontes|Leitura da ORGATEC/);  // o detalhe fica para depois do clique
  assert.match(corpo, /em revisão técnica/);
  assert.match(corpo, new RegExp(item.fato.slice(0, 20)));
  assert.match(corpo, /Orientação ORGATEC \(interpretação, não é texto legal\)/);
  assert.match(corpo, /href="https:\/\/www\.planalto\.gov\.br\//);
  assert.match(corpo, /Consultado em 31\/10\/2026 · Vigência: 2029–2032/);
  // sem a opção, o HTML continua o de sempre (um <article>, sem <details>)
  const normal = K.renderItem(item, F.porId);
  assert.match(normal, /^<article class="og-cartao og-item"/);
  assert.doesNotMatch(normal, /<details/);
  const aprovado = K.renderItem(base({ revisao: { status: 'aprovada', por: 'RT', em: '2026-11-01' } }), F.porId, { recolhido: true });
  assert.doesNotMatch(aprovado, /em revisão técnica/);
});
