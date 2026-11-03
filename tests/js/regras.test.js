const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../../site/assets/js/regras.js');
const UFS = require('../../site/assets/js/ufs.js');
const F = require('../../site/assets/js/fontes.js');

const REGIMES = ['simples', 'presumido', 'real'];
const PERFIS = ['b2b', 'b2c'];
const FATURAMENTOS = [500000, 3600000, 4000000, 4800000, 6000000, 100000000];
const HOJE = '2026-10-30T12:00:00Z';
const ids = res => res.alertas.map(a => a.id);
function sim(o) {
  return R.simular(Object.assign({ setor: 'servicos', regime: 'simples', perfil: 'b2b', uf: 'GO', faturamento: 1e6, comprasPct: 0.2, hoje: HOJE }, o));
}

test('cobertura: 27 UFs com siglas únicas e as 27 do IBGE', () => {
  const siglas = UFS.lista.map(u => u.sigla).sort();
  assert.deepEqual(siglas, ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']);
});

test('todas as combinações setor × regime × perfil × UF × faixa de faturamento produzem resultado consistente', () => {
  let n = 0;
  for (const s of R.SETORES) for (const regime of REGIMES) for (const perfil of PERFIS) for (const u of UFS.lista) for (const fat of FATURAMENTOS) {
    const res = R.simular({ setor: s.id, regime, perfil, uf: u.sigla, faturamento: fat, comprasPct: s.comprasPadrao, hoje: HOJE });
    const tag = `${s.id}/${regime}/${perfil}/${u.sigla}/${fat}`;
    assert.equal(res.erros.length, 0, tag);
    assert.ok(res.alertas.length >= 3, tag);
    assert.equal(new Set(ids(res)).size, res.alertas.length, 'ids duplicados ' + tag);
    for (const a of res.alertas) {
      assert.ok(a.fontes.length >= 1, 'alerta sem fonte ' + a.id);
      for (const f of a.fontes) assert.ok(F.porId[f], `fonte inexistente ${f} em ${a.id}`);
      assert.equal(a.pendente, a.fontes.some(f => !F.porId[f].validado), 'flag pendente incoerente ' + a.id);
      assert.doesNotMatch(a.texto + a.titulo, /undefined|NaN|null/, tag + ' ' + a.id);
    }
    assert.ok(!res.resumo.includes('OUTRAS') && res.resumo.includes(u.sigla), tag);
    const e = res.estimativa;
    for (const k of ['debito', 'credito', 'liquido', 'cargaSobreFaturamento']) assert.ok(Number.isFinite(e[k]), tag + ' ' + k);
    assert.equal(e.pendente, true);
    n++;
  }
  assert.equal(n, R.SETORES.length * 3 * 2 * 27 * FATURAMENTOS.length);
});

test('Simples × perfil: B2B → alerta de crédito (art. 41); B2C → DAS tende a seguir vantajoso; nunca os dois', () => {
  for (const u of UFS.lista) {
    const b2b = ids(sim({ perfil: 'b2b', uf: u.sigla })), b2c = ids(sim({ perfil: 'b2c', uf: u.sigla }));
    assert.ok(b2b.includes('simples_b2b') && !b2b.includes('simples_b2c'));
    assert.ok(b2c.includes('simples_b2c') && !b2c.includes('simples_b2b'));
  }
  for (const regime of ['presumido', 'real']) assert.ok(!ids(sim({ regime })).some(i => i.startsWith('simples_')));
});

test('limites de faturamento: Simples (4,8 mi), sublimite (3,6 mi, art. 13-A) e Presumido (78 mi)', () => {
  assert.ok(!ids(sim({ faturamento: 3600000 })).includes('simples_sublimite'));
  assert.ok(ids(sim({ faturamento: 3600001 })).includes('simples_sublimite'));
  assert.ok(ids(sim({ faturamento: 4800000 })).includes('simples_sublimite'));
  assert.ok(ids(sim({ faturamento: 4800001 })).includes('simples_limite'));
  assert.ok(!ids(sim({ faturamento: 4800001 })).includes('simples_sublimite'));
  assert.ok(!ids(sim({ regime: 'presumido', faturamento: 78000000 })).includes('presumido_limite'));
  assert.ok(ids(sim({ regime: 'presumido', faturamento: 78000001 })).includes('presumido_limite'));
});

test('PIS/Cofins → CBS por regime', () => {
  assert.ok(ids(sim({ regime: 'presumido' })).includes('presumido_cbs'));
  assert.ok(ids(sim({ regime: 'real' })).includes('real_cbs'));
  assert.ok(ids(sim({ regime: 'simples' })).includes('transicao_simples'));
  assert.ok(!ids(sim({ regime: 'simples' })).includes('transicao_2026')); // teste de 2026 não se aplica ao Simples
});

test('redução de 75% do IRPJ só nas áreas SUDAM/SUDENE; "oportunidade" só no Lucro Real com setor incentivável', () => {
  for (const u of UFS.lista) for (const regime of REGIMES) for (const s of R.SETORES) {
    const r = sim({ uf: u.sigla, regime, setor: s.id });
    const a = r.alertas.find(x => x.id === 'uf_irpj75');
    assert.equal(!!a, !!(u.sudam || u.sudene), u.sigla);
    if (a) {
      const esperado = regime === 'real' && ['industria', 'agro', 'comercio_atacadista'].includes(s.id) ? 'oportunidade' : 'info';
      assert.equal(a.nivel, esperado, `${u.sigla}/${regime}/${s.id}`);
    }
  }
  for (const uf of ['GO', 'DF', 'MS', 'SP', 'PR', 'RS', 'SC', 'RJ']) assert.ok(!ids(sim({ uf })).includes('uf_irpj75'), uf);
  for (const uf of ['TO', 'PA', 'AM', 'AC', 'AP', 'RO', 'RR', 'MT', 'MA', 'BA', 'CE', 'PE']) assert.ok(ids(sim({ uf })).includes('uf_irpj75'), uf);
});

test('SUDECO sem 75% do IRPJ: GO, DF e MS (MT está também na SUDAM)', () => {
  const com = UFS.lista.filter(u => ids(sim({ uf: u.sigla })).includes('uf_sudeco')).map(u => u.sigla).sort();
  assert.deepEqual(com, ['DF', 'GO', 'MS']);
});

test('agro na área da SUDAM avisa que a agropecuária em geral não é setor prioritário', () => {
  const a = sim({ uf: 'TO', setor: 'agro', regime: 'real' }).alertas.find(x => x.id === 'uf_irpj75');
  assert.match(a.texto, /não inclui a agropecuária em geral/);
  assert.ok(a.fontes.includes('dec4212_setores'));
});

test('ZFM só no AM; Áreas de Livre Comércio em AC, AM, AP, RO e RR (LC 214, art. 459)', () => {
  const zfm = UFS.lista.filter(u => ids(sim({ uf: u.sigla })).includes('uf_zfm')).map(u => u.sigla);
  const alc = UFS.lista.filter(u => ids(sim({ uf: u.sigla })).includes('uf_alc')).map(u => u.sigla).sort();
  assert.deepEqual(zfm, ['AM']);
  assert.deepEqual(alc, ['AC', 'AM', 'AP', 'RO', 'RR']);
});

test('produtor rural não contribuinte: oportunidade abaixo de R$ 3,6 mi', () => {
  assert.equal(sim({ setor: 'agro', faturamento: 3599999 }).alertas.find(a => a.id === 'setor_agro_nc').nivel, 'oportunidade');
  assert.equal(sim({ setor: 'agro', faturamento: 3600000 }).alertas.find(a => a.id === 'setor_agro_nc').nivel, 'info');
});

test('reduções setoriais na estimativa (saúde/educação 60%, profissões 30%, demais 0%)', () => {
  const red = s => sim({ setor: s }).estimativa.reducao;
  assert.equal(red('saude'), 0.6); assert.equal(red('educacao'), 0.6);
  assert.equal(red('servicos_profissionais'), 0.3); assert.equal(red('servicos'), 0);
  const e = sim({ setor: 'servicos', faturamento: 1000000, comprasPct: 0.1 }).estimativa;
  assert.ok(Math.abs(e.debito - 1000000 * e.aliquotaReferencia) < 1e-6);
  assert.ok(Math.abs(e.credito - 100000 * e.aliquotaReferencia) < 1e-6);
  assert.equal(sim({ perfil: 'b2c' }).estimativa.creditoClienteB2B, null);
});

test('benefícios de ICMS e Lei 14.789: fora do Simples e só para indústria/atacado/agro', () => {
  assert.ok(!ids(sim({ regime: 'simples', setor: 'industria' })).includes('uf_beneficios_icms'));
  assert.ok(ids(sim({ regime: 'real', setor: 'industria' })).includes('uf_beneficios_icms'));
  assert.ok(!ids(sim({ regime: 'real', setor: 'saude' })).includes('uf_beneficios_icms'));
  assert.match(sim({ regime: 'presumido', setor: 'agro' }).alertas.find(a => a.id === 'uf_subvencao').texto, /restrito a empresas do Lucro Real/);
});

test('janela de opção do Simples Híbrido (setembro/março; LC 227/2026)', () => {
  const j = d => R.janelaOpcaoSimples(d);
  assert.deepEqual(j('2026-08-15T00:00:00Z'), { aberta: false, mes: 9, ano: 2026, inicio: 'janeiro de 2027' });
  assert.equal(j('2026-09-10T00:00:00Z').aberta, true);
  assert.deepEqual(j(HOJE), { aberta: false, mes: 3, ano: 2027, inicio: 'julho de 2027' });
  assert.deepEqual(j('2027-03-05T00:00:00Z'), { aberta: true, mes: 3, ano: 2027, inicio: 'julho de 2027' });
  assert.deepEqual(j('2027-05-01T00:00:00Z'), { aberta: false, mes: 9, ano: 2027, inicio: 'janeiro de 2028' });
  assert.match(sim({}).alertas.find(a => a.id === 'simples_b2b').texto, /março de 2027/);
});

test('validação de entrada (inclui regressão do "OUTRAS" da versão anterior)', () => {
  assert.ok(sim({ uf: 'OUTRAS' }).erros.length);
  assert.ok(sim({ faturamento: 0 }).erros.length);
  assert.ok(sim({ faturamento: NaN }).erros.length);
  assert.ok(sim({ comprasPct: 1.5 }).erros.length);
  assert.ok(sim({ setor: 'x' }).erros.length);
  assert.ok(sim({ regime: 'mei' }).erros.length);
});

test('alertas regionais GO/TO/PA × agro/atacado/indústria: não vazios e com alerta específico do estado', () => {
  for (const uf of ['GO', 'TO', 'PA']) for (const s of R.SETORES_REGIONAIS) {
    const al = R.alertasRegionais(uf, s);
    assert.ok(al.length >= 2, uf + s);
    assert.ok(al.some(a => a.id.startsWith(uf.toLowerCase() + '_')), `${uf}/${s} sem alerta estadual`);
    for (const a of al) for (const f of a.fontes) assert.ok(F.porId[f], f);
  }
});
