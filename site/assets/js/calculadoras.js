/* Calculadoras da página Ferramentas (funções puras; testes em tests/js/calculadoras.test.js).
   1. transicaoAno: o que vale em cada ano de 2026 a 2033 e quanto resta do ICMS/ISS (ADCT, arts. 125 a 129).
   2. produtorRural: se o produtor é contribuinte de IBS/CBS e desde quando (LC 214/2025, arts. 164 a 168).
   3. imoveisPessoaFisica: se a pessoa física com imóveis passa a contribuinte de IBS/CBS (LC 214/2025, art. 251). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./regras.js'));
  else (root.Orgatec = root.Orgatec || {}).calculadoras = factory(root.Orgatec.regras);
})(this, function (regras) {
  'use strict';

  var PRIMEIRO = 2026, ULTIMO = 2033;
  // ADCT, art. 128: ICMS e ISS a 9/10, 8/10, 7/10 e 6/10 de 2029 a 2032; art. 129: extintos em 2033.
  var PROPORCAO_ICMS_ISS = { 2026: 1, 2027: 1, 2028: 1, 2029: 0.9, 2030: 0.8, 2031: 0.7, 2032: 0.6, 2033: 0 };
  var LIMITE_PRODUTOR = regras.LIMITES.produtorNaoContribuinte; // LC 214/2025, art. 164 (valor nominal; atualizado pelo IPCA, art. 167)
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];

  function numero(v) {
    if (typeof v === 'number') return isFinite(v) ? v : NaN;
    if (v == null || String(v).trim() === '') return NaN;
    var s = String(v).replace(/[R$\s]/g, '');
    if (s.indexOf(',') >= 0) s = s.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
    return /^-?\d+(\.\d+)?$/.test(s) ? parseFloat(s) : NaN;
  }

  /* ano: 2026–2033 (antes = sistema atual; depois = regime pleno). icmsIssAnual: opcional, R$ por ano hoje. */
  function transicaoAno(ano, icmsIssAnual) {
    var a = numero(ano);
    if (!isFinite(a) || a !== Math.floor(a)) return { erro: 'Informe um ano com quatro dígitos, de 2026 a 2033.' };
    var valor = null;
    if (icmsIssAnual != null && String(icmsIssAnual).trim() !== '') {
      valor = numero(icmsIssAnual);
      if (!isFinite(valor) || valor < 0) return { erro: 'Informe o ICMS/ISS anual em reais, sem valor negativo.' };
    }
    var fontes = ['adct_125_133', 'adct_126', 'adct_127', 'adct_128_129'];
    if (a < PRIMEIRO) return { ano: a, fase: 'anterior', texto: 'Antes de 2026 valem só os tributos atuais (PIS, Cofins, IPI, ICMS e ISS); a transição começa em 2026.', fontes: fontes };
    var ref = Math.min(a, ULTIMO);
    var linha = regras.TRANSICAO.filter(function (l) { return +l.ano === ref; })[0];
    var prop = PROPORCAO_ICMS_ISS[ref];
    var out = {
      ano: a, fase: a > ULTIMO ? 'pleno' : (a === ULTIMO ? 'pleno' : (a >= 2029 ? 'convivencia' : (a === 2026 ? 'teste' : 'cbs'))),
      linha: linha, proporcaoIcmsIss: prop, fontes: fontes,
      texto: a > ULTIMO ? 'Depois de 2033 o sistema é o mesmo de 2033: IBS e CBS integrais, sem ICMS e ISS.' : null
    };
    if (valor != null) out.icmsIssRestante = Math.round(valor * prop * 100) / 100;
    return out;
  }

  /* receita: receita do ano-calendário (somada à das empresas agropecuárias em que tem participação, art. 164, § 6º).
     mesesAtividade: 1–12 no ano de início (limite proporcional, § 4º). integrado: produtor integrado (caput e § 1º).
     optou: inscrição voluntária no regime regular (art. 165). mesExcesso: 1–12, mês em que passou do limite (§ 2º). */
  function produtorRural(e) {
    e = e || {};
    var receita = numero(e.receita);
    if (!isFinite(receita) || receita < 0) return { erro: 'Informe a receita anual em reais, sem valor negativo.' };
    var meses = e.mesesAtividade == null || e.mesesAtividade === '' ? 12 : numero(e.mesesAtividade);
    if (!isFinite(meses) || meses < 1 || meses > 12 || meses !== Math.floor(meses)) return { erro: 'Meses de atividade: de 1 a 12.' };
    var limite = Math.round(LIMITE_PRODUTOR * meses / 12 * 100) / 100;
    var fontes = ['lc214_produtor_nc', 'lc214_produtor_opcao'];
    var avisos = ['O limite de R$ 3,6 milhões é atualizado todo ano pelo IPCA (art. 167). O valor corrigido para o ano não está nesta calculadora: confirme antes de decidir.'];
    var base = { receita: receita, limite: limite, fontes: fontes, avisos: avisos };

    if (e.optou) return Object.assign(base, { contribuinte: true, motivo: 'opcao',
      texto: 'Contribuinte por opção: a inscrição no regime regular vale a partir do mês seguinte ao pedido e não pode ser desfeita no mesmo ano (art. 165). A renúncia produz efeitos no ano seguinte (art. 166).' });
    if (e.integrado) return Object.assign(base, { contribuinte: false, motivo: 'integrado',
      texto: 'Produtor rural integrado (contrato de integração vertical) não é contribuinte de IBS e CBS, salvo se optar pelo regime regular.',
      consequencias: consequenciasNaoContribuinte(fontes) });
    if (receita < limite) return Object.assign(base, { contribuinte: false, motivo: 'abaixo_limite',
      texto: 'Com receita abaixo do limite, o produtor não é contribuinte de IBS e CBS, salvo se optar pelo regime regular.',
      consequencias: consequenciasNaoContribuinte(fontes) });

    var excesso = receita - limite;
    var ate20 = excesso <= limite * 0.2;
    var inicio;
    if (ate20) inicio = 'em 1º de janeiro do ano seguinte (excesso de até 20% do limite, § 3º)';
    else {
      var mes = e.mesExcesso == null || e.mesExcesso === '' ? null : numero(e.mesExcesso);
      if (mes != null && (!isFinite(mes) || mes < 1 || mes > 12 || mes !== Math.floor(mes))) return { erro: 'Mês do excesso: de 1 a 12.' };
      inicio = mes == null ? 'a partir do segundo mês seguinte ao do excesso (§ 2º); informe o mês para ver a data'
        : (mes <= 10 ? 'a partir de ' + MESES[mes + 1] + ' do mesmo ano (segundo mês após o excesso em ' + MESES[mes - 1] + ', § 2º)'
          : 'a partir de ' + MESES[mes - 11] + ' do ano seguinte (segundo mês após o excesso em ' + MESES[mes - 1] + ', § 2º)');
    }
    return Object.assign(base, { contribuinte: true, motivo: ate20 ? 'excesso_ate_20' : 'excesso_acima_20', inicio: inicio,
      texto: 'Receita igual ou acima do limite: o produtor passa a ser contribuinte de IBS e CBS ' + inicio + '.' });
  }

  function consequenciasNaoContribuinte(fontes) {
    fontes.push('lc214_credito_presumido', 'lc214_diferimento_insumos', 'lc214_maquinas_agro');
    return [
      'Quem compra do produtor e é contribuinte do regime regular apropria crédito presumido a partir de 2027 (art. 168); os percentuais são definidos todo ano por ato conjunto do Ministério da Fazenda e do Comitê Gestor do IBS.',
      'Nos insumos do Anexo IX vendidos ao produtor não contribuinte, o IBS e a CBS podem ficar diferidos, desde que a produção seja vendida a quem tem direito ao crédito presumido (art. 138, § 2º).',
      'Tratores, máquinas e implementos agrícolas destinados ao produtor não contribuinte têm alíquota zero (art. 110, I).'
    ];
  }

  var DIA = 864e5;
  function utc(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    if (!m) return NaN;
    var t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
    return new Date(t).getUTCDate() === +m[3] ? t : NaN; // recusa 30/02 e afins
  }

  /* Fração da transição já decorrida: de 01/01/2026 (início do teste, ADCT art. 125) a 01/01/2033
     (extinção do ICMS e do ISS, art. 129). Antes: 0; depois: 1. hoje = 'AAAA-MM-DD'. */
  function progressoTransicao(hoje) {
    var t = utc(hoje);
    if (!isFinite(t)) return null;
    var ini = Date.UTC(PRIMEIRO, 0, 1), fim = Date.UTC(ULTIMO, 0, 1);
    return Math.min(1, Math.max(0, (t - ini) / (fim - ini)));
  }

  /* Dias corridos de hoje até a data (0 se já passou; null se alguma data for inválida). */
  function diasAte(alvo, hoje) {
    var a = utc(alvo), h = utc(hoje);
    if (!isFinite(a) || !isFinite(h)) return null;
    return Math.max(0, Math.round((a - h) / DIA));
  }

  /* Pessoa física com imóveis (LC 214/2025, art. 251, §§ 1º e 2º). e: valores do ano anterior (obrigatórios) e do ano atual (opcionais).
     O limite de R$ 240.000 é o valor da lei; ele é atualizado mensalmente pelo IPCA (§ 5º): quem souber o valor atualizado o informa em e.limite. */
  var LIMITE_LOCACAO_PF = 240000;
  function imoveisPessoaFisica(e) {
    e = e || {};
    var limite = e.limite == null || e.limite === '' ? LIMITE_LOCACAO_PF : numero(e.limite);
    var campos = { receitaAnterior: 'receita de locação do ano anterior', locadosAnterior: 'imóveis alugados no ano anterior',
      vendidosAnterior: 'imóveis vendidos no ano anterior', construidosAnterior: 'imóveis construídos por você e vendidos no ano anterior' };
    var v = {};
    for (var k in campos) {
      v[k] = e[k] == null || e[k] === '' ? 0 : numero(e[k]);
      if (!isFinite(v[k]) || v[k] < 0) return { erro: 'Informe ' + campos[k] + ' sem valor negativo.' };
    }
    ['receitaAtual', 'vendidosAtual', 'construidosAtual'].forEach(function (k) { v[k] = e[k] == null || e[k] === '' ? 0 : numero(e[k]); });
    if (!isFinite(limite) || limite <= 0 || [v.receitaAtual, v.vendidosAtual, v.construidosAtual].some(function (x) { return !isFinite(x) || x < 0; }))
      return { erro: 'Os valores do ano atual e o limite não podem ser negativos.' };
    var motivos = [];
    if (v.receitaAnterior > limite && v.locadosAnterior > 3) motivos.push({ regra: 'art. 251, § 1º, I', texto: 'No ano anterior, a receita de locação passou do limite e envolveu mais de 3 imóveis.' });
    if (v.vendidosAnterior > 3) motivos.push({ regra: 'art. 251, § 1º, II', texto: 'No ano anterior, foram vendidos mais de 3 imóveis que estavam no patrimônio havia menos de 5 anos.' });
    if (v.construidosAnterior > 1) motivos.push({ regra: 'art. 251, § 1º, III', texto: 'No ano anterior, foi vendido mais de 1 imóvel construído por você nos 5 anos anteriores.' });
    if (v.vendidosAtual > 3 || v.construidosAtual > 1) motivos.push({ regra: 'art. 251, § 2º, I', texto: 'Neste ano, as vendas já passaram dos limites: contribuinte no próprio ano.' });
    if (v.receitaAtual > limite * 1.2) motivos.push({ regra: 'art. 251, § 2º, II', texto: 'Neste ano, a receita de locação já excede em 20% o limite: contribuinte no próprio ano.' });
    return { contribuinte: motivos.length > 0, motivos: motivos, limite: limite, fontes: ['lc214_imoveis'],
      aviso: 'O limite de R$ 240.000,00 é atualizado mensalmente pelo IPCA, e o regulamento define o que são imóveis distintos. Resultado orientativo.' };
  }

  return { transicaoAno: transicaoAno, produtorRural: produtorRural, imoveisPessoaFisica: imoveisPessoaFisica, LIMITE_LOCACAO_PF: LIMITE_LOCACAO_PF, numero: numero, PROPORCAO_ICMS_ISS: PROPORCAO_ICMS_ISS,
    progressoTransicao: progressoTransicao, diasAte: diasAte };
});
