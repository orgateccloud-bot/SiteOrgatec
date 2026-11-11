// Veredito do dia e faixa horária da Janela de Campo (site/assets/js/campo-veredito.js): só o que roda sem navegador.
const test = require('node:test');
const assert = require('node:assert/strict');
const V = require('../../site/assets/js/campo-veredito.js');

const ph = (s) => { const o = {}; for (let i = 0; i < s.length; i++) o[5 + i] = { o: 'ok', a: 'atencao', e: 'evitar' }[s[i]]; return o; };
const polo = (ops) => ({ ops: Object.fromEntries(Object.entries(ops).map(([k, v]) => [k, { estado: v[0], janela: v[1], tipoJanela: v[2], motivo: v[3] || '', horasPrevistas: v[5] == null ? 16 : v[5], porHora: ph(v[4] || 'oooooooooooooooo') }])) });
const SORRISO = polo({
  pulv: ['atencao', '05h às 11h', 'ok', 'calor (evaporação)', 'ooooooaaaaaaaaaa'], plantio: ['ok', '05h às 21h', 'ok', ''],
  colheita: ['ok', '08h às 21h', 'ok', 'umidade alta (grão úmido)', 'aaaooooooooooooo'], animais: ['atencao', '05h às 07h', 'ok', 'estresse térmico alto (ITU 82)', 'ooaaaeeeeeeeeeee'],
  maquinas: ['ok', '05h às 21h', 'ok', '']
});

test('janelaCurta: "05h às 11h" vira "05–11h"; outro formato, null', () => {
  assert.equal(V.janelaCurta('05h às 11h'), '05–11h');
  assert.equal(V.janelaCurta('8h às 21h'), '08–21h');
  assert.equal(V.janelaCurta(null), null);
  assert.equal(V.janelaCurta('sem janela'), null);
});

test('faixa: 16 letras das 05h às 20h; hora sem previsão vira x', () => {
  assert.equal(V.faixa(ph('ooooooaaaaaaaaaa')), 'ooooooaaaaaaaaaa');
  assert.equal(V.faixa({ 5: 'ok', 6: 'evitar' }), 'oexxxxxxxxxxxxxx');
  assert.equal(V.faixa(undefined), 'xxxxxxxxxxxxxxxx');
});

test('descreverFaixa: trechos seguidos para o leitor de tela', () => {
  assert.equal(V.descreverFaixa('ooooooaaaaaaaaaa'), 'favorável das 05h às 11h; com restrição das 11h às 21h');
  assert.equal(V.descreverFaixa('xxxxxooooooooooo'), 'sem previsão das 05h às 10h; favorável das 10h às 21h');
});

test('veredito de polo vigente: nomeia os favoráveis, as restrições com a janela e a contagem', () => {
  const v = V.veredito('vigente', V.itensDoPolo(SORRISO));
  assert.equal(v.tipo, 'normal');
  assert.equal(v.titulo, 'Favorável hoje: plantio, colheita e máquinas.');
  assert.deepEqual(v.linhas, ['Com restrição: pulverização (melhor horário 05–11h) e manejo de animais (melhor horário 05–07h).']);
  assert.deepEqual(v.contagem, { favoraveis: 3, total: 5 });
  assert.equal(v.parcial, null);
  assert.deepEqual(v.glifos.map((g) => g.estado), ['atencao', 'ok', 'ok', 'atencao', 'ok']);
});

test('todas favoráveis, nenhuma favorável e todas a evitar', () => {
  const todas = (e) => V.itensDoPolo(polo({ pulv: [e, null, null], plantio: [e, null, null], colheita: [e, null, null], animais: [e, null, null], maquinas: [e, null, null] }));
  assert.equal(V.veredito('vigente', todas('ok')).titulo, 'Dia favorável para todas as operações.');
  assert.equal(V.veredito('vigente', todas('evitar')).titulo, 'Dia ruim: evite todas as operações.');
  const v = V.veredito('vigente', todas('atencao'));
  assert.equal(v.titulo, 'Nenhuma operação está favorável hoje.');
  assert.equal(v.contagem.favoraveis, 0);
});

test('operação a evitar entra numa linha própria; sem previsão também', () => {
  const p = polo({ pulv: ['ok', null, null], plantio: ['evitar', null, null], colheita: ['ok', null, null], animais: ['atencao', null, null, '', 'oooooooooooooooo', 0], maquinas: ['ok', null, null] });
  const v = V.veredito('vigente', V.itensDoPolo(p));
  assert.equal(v.titulo, 'Favorável hoje: pulverização, colheita e máquinas.');
  assert.deepEqual(v.linhas, ['Evitar: plantio.', 'Sem previsão: manejo de animais.']);
});

test('previsão parcial: a menor quantidade de horas previstas entre as operações com previsão', () => {
  const p = polo({ pulv: ['ok', null, null, '', 'oooooooooooxxxxx', 11], plantio: ['ok', null, null, '', 'oooooooooooooooo', 16], colheita: ['ok', null, null], animais: ['ok', null, null], maquinas: ['ok', null, null] });
  assert.deepEqual(V.veredito('vigente', V.itensDoPolo(p)).parcial, { de: 11, total: 16 });
});

test('boletim vencido ou desatualizado não tem veredito e os glifos ficam sem previsão', () => {
  const itens = V.itensDoPolo(SORRISO);
  for (const vig of ['vencido', 'desatualizado']) {
    const v = V.veredito(vig, itens);
    assert.equal(v.tipo, 'sem');
    assert.match(v.titulo, /^Sem veredito: boletim /);
    assert.ok(v.glifos.every((g) => g.estado === 'sem'));
    assert.equal(v.contagem.favoraveis, 0);
  }
  assert.match(V.veredito('desatualizado', itens).titulo, /18 horas/);
});

test('sem nenhuma hora útil prevista: sem veredito', () => {
  const p = polo(Object.fromEntries(['pulv', 'plantio', 'colheita', 'animais', 'maquinas'].map((k) => [k, ['atencao', null, null, '', 'xxxxxxxxxxxxxxxx', 0]])));
  const v = V.veredito('vigente', V.itensDoPolo(p));
  assert.equal(v.tipo, 'sem');
  assert.match(v.titulo, /sem previsão para as horas úteis/);
});

test('região (boletim manual): usa o estado de cada operação, sem faixa horária', () => {
  const r = { ops: { pulv: ['atencao', 'Com restrição · vento', 'x'], plantio: ['ok', 'Favorável', 'x'], colheita: ['ok', 'Favorável', 'x'], animais: ['ok', 'Favorável', 'x'], maquinas: ['ok', 'Favorável', 'x'] } };
  const itens = V.itensDaRegiao(r);
  assert.ok(itens.every((i) => i.faixa === null));
  assert.equal(V.veredito('vigente', itens).titulo, 'Favorável hoje: plantio, colheita, manejo de animais e máquinas.');
  r.ops.pulv = ['atencao', 'Sem previsão para as horas úteis de hoje (05h às 20h).', 'x'];
  assert.equal(V.itensDaRegiao(r)[0].estado, 'sem');
});

test('legendaJanela: janela em destaque e motivo só quando o boletim o traz', () => {
  const it = V.itensDoPolo(SORRISO);
  assert.deepEqual(V.legendaJanela(it[0]), { janela: '05–11h', texto: 'melhor horário · fora dele: calor (evaporação)' });
  assert.deepEqual(V.legendaJanela(it[1]), { janela: '05–21h', texto: 'melhor horário' });
  assert.deepEqual(V.legendaJanela({ estado: 'atencao', janela: null, motivo: 'vento forte' }), { janela: '—', texto: 'sem horário favorável hoje · vento forte' });
  assert.deepEqual(V.legendaJanela({ estado: 'sem' }), { janela: '—', texto: 'sem previsão para as horas úteis' });
});

test('legenda do cartão cabe em 90 caracteres com os motivos do gerador', () => {
  for (const m of ['calor (evaporação)', 'umidade alta (grão úmido)', 'estresse térmico alto (ITU 82)', 'vento forte (deriva)', 'chuva moderada']) {
    const t = V.legendaJanela({ estado: 'atencao', janela: '05–11h', tipoJanela: 'ok', motivo: m }).texto;
    assert.ok(t.length <= 90, t);
  }
});

const regiao = (e) => ({ ops: { pulv: [e[0], 'x', 'x'], plantio: [e[1], 'x', 'x'], colheita: [e[2], 'x', 'x'], animais: [e[3], 'x', 'x'], maquinas: [e[4], 'x', 'x'] } });

test('colunasIguais: só marca a coluna em que todas as regiões têm o mesmo estado', () => {
  const linhas = [regiao(['atencao', 'ok', 'atencao', 'atencao', 'ok']), regiao(['atencao', 'ok', 'ok', 'atencao', 'ok']), regiao(['atencao', 'ok', 'ok', 'ok', 'ok'])].map(V.itensDaRegiao);
  assert.deepEqual(V.colunasIguais(linhas).map((c) => c.igual), [true, true, false, false, true]);
  assert.equal(V.fraseIguais(V.colunasIguais(linhas)), 'Igual em todas as regiões: pulverização (com restrição), plantio (favorável) e máquinas (favorável).');
});

test('colunasIguais: uma região só, ou nenhuma coluna igual, não gera frase', () => {
  const uma = [regiao(['ok', 'ok', 'ok', 'ok', 'ok'])].map(V.itensDaRegiao);
  assert.ok(V.colunasIguais(uma).every((c) => !c.igual));
  assert.equal(V.fraseIguais(V.colunasIguais(uma)), '');
  const duas = [regiao(['ok', 'ok', 'ok', 'ok', 'ok']), regiao(['atencao', 'atencao', 'atencao', 'atencao', 'atencao'])].map(V.itensDaRegiao);
  assert.equal(V.fraseIguais(V.colunasIguais(duas)), '');
});

test('colunasIguais: região sem previsão conta como estado "sem" e diz "sem previsão"', () => {
  const sem = ['Sem previsão para as horas úteis de hoje (05h às 20h).'];
  const r = (v) => ({ ops: { pulv: ['atencao', sem[0], 'x'], plantio: [v, 'x', 'x'], colheita: [v, 'x', 'x'], animais: [v, 'x', 'x'], maquinas: [v, 'x', 'x'] } });
  const linhas = [r('ok'), r('atencao')].map(V.itensDaRegiao);
  assert.match(V.fraseIguais(V.colunasIguais(linhas)), /pulverização \(sem previsão\)/);
});
