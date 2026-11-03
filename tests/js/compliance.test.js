// Área de Compliance: conteúdo como dados (compliance-itens.js) validado por conteudo.js.
const test = require('node:test');
const assert = require('node:assert/strict');
const F = require('../../site/assets/js/fontes.js');
const K = require('../../site/assets/js/conteudo.js');
const CI = require('../../site/assets/js/compliance-itens.js');
const RI = require('../../site/assets/js/reforma-itens.js');

const base = (o) => Object.assign({ id: 'x', titulo: 't', fato: 'f', status: 'incerto', consultadoEm: '2026-11-01',
  fontes: ['lei13709'], setores: ['todos'], tributos: [], pilar: 'lgpd', destinos: ['compliance-lgpd'],
  revisao: { status: 'pendente', por: null, em: null } }, o);

test('todo item de compliance é válido, tem pilar e aparece na área (frente ou página de público)', () => {
  assert.ok(CI.length >= 2);
  CI.forEach((it) => {
    assert.deepEqual(K.validarItem(it, F.porId), [], it.id);
    assert.ok(K.PILARES[it.pilar], it.id + ' sem pilar válido');
    assert.ok(it.destinos.some((d) => d.startsWith('compliance') || d.startsWith('publico-')), it.id + ' sem destino na área de compliance');
  });
});

test('ids únicos entre compliance e reforma (o item não é copiado de um arquivo para o outro)', () => {
  const ids = CI.concat(RI).map((i) => i.id);
  assert.equal(new Set(ids).size, ids.length);
});

test('fonte não conferida: item fica "incerto" e nunca aprovado', () => {
  CI.concat(RI).filter((it) => it.destinos.some((d) => d.startsWith('compliance'))).forEach((it) => {
    const pendentes = it.fontes.filter((id) => !F.porId[id].validado);
    if (it.fontes.every((id) => !F.porId[id].validado)) assert.equal(it.status, 'incerto', it.id);
    if (pendentes.length) assert.notEqual(it.revisao.status, 'aprovada', it.id + ' aprovado com fonte pendente');
  });
});

test('validação: pilar substitui tributo, mas tributo vazio sem pilar continua erro', () => {
  assert.deepEqual(K.validarItem(base(), F.porId), []);
  assert.ok(K.validarItem(base({ pilar: 'outro' }), F.porId).includes('pilar inválido: outro'));
  assert.ok(K.validarItem(base({ pilar: undefined }), F.porId).includes('campo obrigatório ausente: tributos'));
  assert.ok(K.validarItem(base({ prazo: '2026-02-30' }), F.porId).includes('prazo inválido: 2026-02-30'));
  assert.ok(K.validarItem(base({ destinos: ['compliance-xpto'] }), F.porId).includes('destino inválido: compliance-xpto'));
});

test('cartão do item de compliance mostra a frente e o prazo', () => {
  const html = K.renderItem(base({ prazo: '2027-01-01', fontes: ['lei13709', 'in_rfb_2295_2025'] }), F.porId);  // uma conferida, uma pendente
  assert.match(html, /Proteção de dados \(LGPD\)/);
  assert.match(html, /Prazo: 01\/01\/2027/);
  assert.match(html, /pendente de validação/);
});

test('datas que pedem atenção: só de hoje em diante, da mais próxima à mais distante', () => {
  const itens = [base({ id: 'a', prazo: '2027-01-01' }), base({ id: 'b', prazo: '2026-12-31' }), base({ id: 'c', prazo: '2026-10-01' }), base({ id: 'd' })];
  assert.deepEqual(K.proximosPrazos(itens, '2026-11-01').map((i) => i.id), ['b', 'a']);
  assert.deepEqual(K.proximosPrazos(itens, '2026-11-01', 1).map((i) => i.id), ['b']);
  assert.deepEqual(K.proximosPrazos(itens, '2027-01-02'), []);
});

test('em produção, sem revisão aprovada, nenhum item de compliance vai à tela', () => {
  assert.equal(K.publicaveis(CI, F.porId, 'producao').itens.length, 0);
  assert.equal(K.publicaveis(CI, F.porId, 'homologacao').itens.length, CI.length);
});

test('as quatro frentes têm itens, e toda fonte de compliance conferida tem data e link oficial', () => {
  ['tributario', 'pld', 'lgpd', 'integridade'].forEach((p) => assert.ok(CI.some((it) => it.pilar === p), 'frente sem itens: ' + p));
  ['lc225_2026', 'dec13075_2026', 'lei9613', 'res_cfc_1721_2024', 'lei13709', 'res_anpd_2_2022', 'lei12846', 'dec11129_2022', 'lei14133_integridade', 'dec12304_2024']
    .forEach((id) => {
      const f = F.porId[id];
      assert.ok(f && f.validado && f.conferido === '2026-11-01', id);
      assert.match(f.url, /^https:\/\/(www\.planalto\.gov\.br|www\.gov\.br)\//, id);
    });
});

test('PLD: a não ocorrência dos contadores vai ao CFC até 31 de janeiro (Res. CFC 1.721/2024, art. 7º)', () => {
  const it = CI.find((i) => i.id === 'pld-profissionais-contabilidade');
  assert.match(it.fato, /ao CFC até 31 de janeiro/);
  assert.equal(it.prazo.slice(5), '01-31');
});

test('área por público: destinos válidos e itens do transportador com fonte conferida', () => {
  Object.keys(K.PUBLICOS).forEach((p) => assert.ok(K.DESTINOS.includes('publico-' + p), p));
  const tr = CI.concat(RI).filter((i) => i.destinos.includes('publico-transportador'));
  assert.ok(tr.length >= 12, 'itens do transportador: ' + tr.length);
  CI.filter((i) => i.pilar === 'transporte').forEach((i) => {
    assert.deepEqual(i.setores, ['transporte'], i.id);
    i.fontes.forEach((f) => assert.ok(F.porId[f].validado, i.id + ' cita fonte não conferida ' + f));
  });
  // o fato do CIOT segue a resolução da ANTT (18/09/2026), não a data antiga da página informativa
  assert.match(CI.find((i) => i.id === 'transporte-ciot').fato, /18\/09\/2026/);
  // a indenização de 30% do tempo de espera caiu na ADI 5322: o item não pode apresentá-la como regra vigente
  assert.match(CI.find((i) => i.id === 'transporte-jornada-motorista').fato, /declarou inconstitucionais/);
});

test('área por público: itens do produtor rural com fonte conferida e página com os itens do agro', () => {
  CI.filter((i) => i.pilar === 'rural').forEach((i) => {
    assert.deepEqual(i.setores, ['agro'], i.id);
    i.fontes.forEach((f) => assert.ok(F.porId[f].validado, i.id + ' cita fonte não conferida ' + f));
  });
  const pr = CI.concat(RI).filter((i) => i.destinos.includes('publico-produtor')).map((i) => i.id);
  ['produtor-nao-contribuinte', 'produtor-cnpj-documento-2027', 'rural-car', 'rural-itr', 'rural-eudr'].forEach((id) => assert.ok(pr.includes(id), id));
});
