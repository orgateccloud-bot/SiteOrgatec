/* Motor de regras do Simulador Híbrido Nacional. Puro (sem DOM), testável no Node.
   Cada alerta cita IDs de fontes.js; se qualquer fonte citada não estiver validada,
   o alerta sai marcado como "pendente de validação". */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./ufs.js'), require('./fontes.js'), require('./config.js'));
  else (root.Orgatec = root.Orgatec || {}).regras = factory(root.Orgatec.ufs, root.Orgatec.fontes, root.Orgatec.config);
})(this, function (UFS, FONTES, CONFIG) {
  'use strict';

  var LIMITE_SIMPLES = 4800000;      // LC 123/2006, art. 3º, II
  var SUBLIMITE_SIMPLES = 3600000;   // LC 123/2006, arts. 19 e 20
  var LIMITE_PRESUMIDO = 78000000;   // Lei 9.718/1998, art. 13
  var LIMITE_PRODUTOR_NC = 3600000;  // LC 214/2025, art. 164 (produtor rural não contribuinte)

  /* reducao: redução de alíquota de IBS/CBS sobre as VENDAS do setor;
     reducaoCompras: redução que incide sobre as COMPRAS típicas (afeta o crédito);
     comprasPadrao: premissa ilustrativa de compras creditáveis / faturamento (editável na tela). */
  var SETORES = [
    { id: 'comercio_atacadista', rotulo: 'Comércio Atacadista', rotuloCurto: 'Comércio atacadista', comprasPadrao: 0.75, reducao: 0, reducaoCompras: 0 },
    { id: 'comercio_varejista', rotulo: 'Comércio Varejista', rotuloCurto: 'Varejo', comprasPadrao: 0.65, reducao: 0, reducaoCompras: 0 },
    { id: 'servicos', rotulo: 'Prestação de Serviços (geral)', rotuloCurto: 'Serviços', comprasPadrao: 0.15, reducao: 0, reducaoCompras: 0 },
    { id: 'servicos_profissionais', rotulo: 'Profissões fiscalizadas por conselho profissional (contabilidade, advocacia, engenharia…)', rotuloCurto: 'Profissões com conselho', comprasPadrao: 0.10, reducao: 0.30, reducaoCompras: 0, fonteReducao: 'lc214_art127' },
    { id: 'saude', rotulo: 'Serviços de Saúde', rotuloCurto: 'Saúde', comprasPadrao: 0.20, reducao: 0.60, reducaoCompras: 0, fonteReducao: 'lc214_saude' },
    { id: 'educacao', rotulo: 'Educação', rotuloCurto: 'Educação', comprasPadrao: 0.15, reducao: 0.60, reducaoCompras: 0, fonteReducao: 'lc214_educacao' },
    { id: 'industria', rotulo: 'Indústria e Transformação', rotuloCurto: 'Indústria', comprasPadrao: 0.55, reducao: 0, reducaoCompras: 0 },
    { id: 'agro', rotulo: 'Agronegócio e Produtor Rural', rotuloCurto: 'Agronegócio', comprasPadrao: 0.45, reducao: 0.60, reducaoCompras: 0.60, fonteReducao: 'lc214_agro' }
  ];
  var porSetor = {};
  SETORES.forEach(function (s) { porSetor[s.id] = s; });
  var SETORES_REGIONAIS = ['agro', 'comercio_atacadista', 'industria'];
  var ROTULO_REGIME = { simples: 'Simples Nacional', presumido: 'Lucro Presumido', real: 'Lucro Real' };
  var SERVICOS = ['servicos', 'servicos_profissionais', 'saude', 'educacao'];

  /* Cronograma da transição (EC 132/2023, ADCT arts. 125 a 133). */
  var TRANSICAO = [
    { ano: '2026', cbs: '0,9% (teste)', ibs: '0,1% (teste)', piscofins: 'Vigentes', ipi: 'Vigente', icmsiss: '100%' },
    { ano: '2027', cbs: 'Alíquota cheia (−0,1 p.p.)', ibs: '0,1% (0,05% UF + 0,05% município)', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '100%' },
    { ano: '2028', cbs: 'Alíquota cheia (−0,1 p.p.)', ibs: '0,1% (0,05% UF + 0,05% município)', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '100%' },
    { ano: '2029', cbs: 'Cheia', ibs: 'Crescente', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '90%' },
    { ano: '2030', cbs: 'Cheia', ibs: 'Crescente', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '80%' },
    { ano: '2031', cbs: 'Cheia', ibs: 'Crescente', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '70%' },
    { ano: '2032', cbs: 'Cheia', ibs: 'Crescente', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: '60%' },
    { ano: '2033', cbs: 'Cheia', ibs: 'Cheio', piscofins: 'Extintos', ipi: 'Zero (exceto ZFM)', icmsiss: 'Extintos' }
  ];

  function pendente(fontes) {
    return fontes.some(function (id) { var f = FONTES.porId[id]; return !f || !f.validado; });
  }
  function alerta(id, nivel, titulo, texto, fontes) {
    return { id: id, nivel: nivel, titulo: titulo, texto: texto, fontes: fontes, pendente: pendente(fontes) };
  }
  function brl(v) { return 'R$ ' + Math.round(v).toLocaleString('pt-BR'); }

  /* Janela da opção do Simples pelo regime regular de IBS/CBS (LC 123, art. 13, § 10,
     red. LC 227/2026): exercida em setembro (semestre iniciado em janeiro) ou março
     (semestre iniciado em julho); primeira janela: setembro/2026, para 01/2027. */
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  function janelaOpcaoSimples(hoje) {
    var d = hoje ? new Date(hoje) : new Date();
    var a = d.getUTCFullYear(), m = d.getUTCMonth() + 1;
    if (a < 2026 || (a === 2026 && m < 9)) return { aberta: false, mes: 9, ano: 2026, inicio: 'janeiro de 2027' };
    if (m === 3) return { aberta: true, mes: 3, ano: a, inicio: 'julho de ' + a };
    if (m === 9) return { aberta: true, mes: 9, ano: a, inicio: 'janeiro de ' + (a + 1) };
    if (m < 3) return { aberta: false, mes: 3, ano: a, inicio: 'julho de ' + a };
    if (m < 9) return { aberta: false, mes: 9, ano: a, inicio: 'janeiro de ' + (a + 1) };
    return { aberta: false, mes: 3, ano: a + 1, inicio: 'julho de ' + (a + 1) };
  }
  function textoJanela(j) {
    return j.aberta
      ? 'A janela de opção está aberta neste mês (' + MESES[j.mes - 1] + ' de ' + j.ano + '), para o semestre que começa em ' + j.inicio + '.'
      : 'A próxima janela de opção é ' + MESES[j.mes - 1] + ' de ' + j.ano + ', para o semestre que começa em ' + j.inicio + '.';
  }

  function validar(e) {
    var erros = [];
    if (!porSetor[e.setor]) erros.push('Setor inválido.');
    if (!ROTULO_REGIME[e.regime]) erros.push('Regime inválido.');
    if (e.perfil !== 'b2b' && e.perfil !== 'b2c') erros.push('Perfil de clientes inválido.');
    if (!UFS.porSigla[e.uf]) erros.push('UF inválida.');
    if (!(typeof e.faturamento === 'number' && isFinite(e.faturamento) && e.faturamento > 0)) erros.push('Informe o faturamento anual (valor maior que zero).');
    if (!(typeof e.comprasPct === 'number' && isFinite(e.comprasPct) && e.comprasPct >= 0 && e.comprasPct <= 1)) erros.push('Compras com crédito devem estar entre 0% e 100%.');
    return erros;
  }

  /* ---------------- Regras por regime e perfil de clientes ---------------- */
  function regrasRegime(e, s, out) {
    var f = e.faturamento;
    if (e.regime === 'simples') {
      if (f > LIMITE_SIMPLES) {
        out.push(alerta('simples_limite', 'critico', 'Faturamento acima do limite do Simples Nacional',
          'A receita informada (' + brl(f) + ') supera o limite de R$ 4,8 milhões por ano-calendário, o que leva à exclusão do Simples Nacional. É preciso planejar a migração para o Lucro Presumido ou Real.',
          ['lc123_art3']));
      } else if (f > SUBLIMITE_SIMPLES) {
        out.push(alerta('simples_sublimite', 'atencao', 'Faturamento acima do sublimite de R$ 3,6 milhões',
          'Acima do sublimite, o ICMS e o ISS deixam de ser recolhidos no DAS e passam a ser apurados pelas regras normais do estado e do município, embora a empresa continue no Simples para os tributos federais. A partir de 2027, o IBS também passa a ficar fora do DAS nessa situação.',
          ['lc123_sublimite']));
      }
      if (e.perfil === 'b2b') {
        out.push(alerta('simples_b2b', 'critico', 'Clientes PJ: risco de perda de competitividade no DAS',
          'Quem compra de empresa do Simples que recolhe IBS e CBS dentro do DAS só se credita do valor devido por meio do Simples, em geral bem inferior ao de um fornecedor do regime regular. A LC nº 214/2025 permite ao optante apurar IBS e CBS pelo regime regular, fora do DAS, mantendo os demais tributos no Simples (o chamado "Simples Híbrido", com efeitos a partir de 2027). A opção vale por semestre e é irretratável dentro dele. ' + textoJanela(janelaOpcaoSimples(e.hoje)),
          ['lc214_art41', 'lc214_credito_simples', 'cf_146_simples', 'cgsn_opcao']));
      } else {
        out.push(alerta('simples_b2c', 'info', 'Clientes consumidores finais: o DAS tende a continuar vantajoso',
          'Consumidor final não aproveita crédito de IBS e CBS. Para quem vende majoritariamente a pessoas físicas, permanecer com IBS e CBS dentro do DAS costuma manter a carga menor. Ainda assim, compras relevantes de fornecedores do regime regular podem justificar a simulação do regime regular, que permite aproveitar esses créditos.',
          ['lc214_art41']));
      }
    }
    if (e.regime === 'presumido') {
      if (f > LIMITE_PRESUMIDO) {
        out.push(alerta('presumido_limite', 'critico', 'Faturamento acima do limite do Lucro Presumido',
          'Receita total acima de R$ 78 milhões no ano anterior obriga à apuração pelo Lucro Real.',
          ['lei9718_art13']));
      }
      out.push(alerta('presumido_cbs', 'atencao', 'PIS/Cofins cumulativos (3,65%) serão substituídos pela CBS não cumulativa',
        'No Lucro Presumido, PIS e Cofins são cumulativos (0,65% + 3%), sem créditos. A partir de 2027, a CBS é não cumulativa e incide com a alíquota de referência sobre as vendas, com crédito sobre as compras. O IRPJ e a CSLL continuam apurados pelo Presumido.',
        ['lei9718_cumulativo', 'lc214_nao_cumulatividade', 'adct_125_133']));
    }
    if (e.regime === 'real') {
      out.push(alerta('real_cbs', 'info', 'PIS/Cofins não cumulativos (9,25%) dão lugar à CBS com crédito amplo',
        'No Lucro Real, PIS e Cofins não cumulativos (1,65% + 7,6%) têm créditos restritos por lista legal. A CBS e o IBS adotam crédito amplo sobre as aquisições, exceto bens e serviços de uso ou consumo pessoal, condicionado ao pagamento do tributo na etapa anterior. Revise o cadastro de fornecedores e a documentação fiscal.',
        ['lei10637_10833', 'lc214_nao_cumulatividade']));
    }
    if (e.regime !== 'simples' && SERVICOS.indexOf(e.setor) >= 0) {
      out.push(alerta('servicos_margem', 'atencao', 'Serviços: poucos créditos e revisão de preços',
        'Hoje o serviço recolhe ISS de 2% a 5% e PIS/Cofins. No novo modelo, IBS e CBS incidem pela alíquota de referência (com eventual redução setorial) e a folha de salários não gera crédito. Com poucos insumos creditáveis, a carga tende a subir e o preço precisa ser revisto, sobretudo nas vendas a consumidor final.',
        ['lc116_iss', 'lc214_nao_cumulatividade']));
    }
    if (e.regime !== 'simples' && e.perfil === 'b2c') {
      out.push(alerta('b2c_preco', 'info', 'Venda a consumidor final: tributo destacado e "por fora"',
        'IBS e CBS não integram a própria base de cálculo e vêm destacados no documento fiscal. Para o consumidor final, que não toma crédito, o tributo é custo; a formação de preço deve considerar isso desde a transição.',
        ['lc214_base_calculo']));
    }
    out.push(alerta('split_payment', 'info', 'Split Payment: o tributo é separado no pagamento',
      'Na liquidação financeira (cartão, Pix, boleto), a parcela de IBS e CBS poderá ser segregada e recolhida diretamente, antes de o valor chegar à empresa. Isso reduz o capital de giro disponível e exige conciliação entre vendas, recebimentos e créditos. A implantação é gradual.',
      ['lc214_split']));
    if (e.regime === 'simples') {
      out.push(alerta('transicao_simples', 'info', 'Transição no Simples: o DAS muda a partir de 2027',
        'As alíquotas de teste de 2026 (CBS 0,9% e IBS 0,1%) não se aplicam ao optante do Simples Nacional. A partir de 2027, a parcela de PIS/Cofins do DAS dá lugar à CBS e, de 2029 a 2033, a de ICMS/ISS dá lugar gradualmente ao IBS.',
        ['lc214_2026', 'adct_125_133']));
    } else {
      out.push(alerta('transicao_2026', 'info', '2026 é ano de teste: CBS 0,9% e IBS 0,1% em documento fiscal',
        'Em 2026, CBS e IBS são destacados nas notas fiscais com alíquotas de teste e o valor é compensado com PIS/Cofins. Quem cumpre as obrigações acessórias fica dispensado do recolhimento; por isso os cadastros (NCM, NBS, classificação tributária) precisam estar corretos já agora.',
        ['adct_125_133', 'lc214_2026']));
    }
  }

  /* ---------------- Regras por setor ---------------- */
  function regrasSetor(e, s, out) {
    if (s.id === 'servicos_profissionais') {
      out.push(alerta('setor_profissoes', 'oportunidade', 'Redução de 30% para profissões intelectuais fiscalizadas por conselho profissional',
        'Serviços de profissões regulamentadas listadas na LC nº 214/2025 (como contabilidade, advocacia, engenharia e arquitetura) têm redução de 30% das alíquotas de IBS e CBS, desde que prestados por profissional habilitado ou sociedade que atenda às condições legais.',
        ['lc214_art127']));
    }
    if (s.id === 'saude') {
      out.push(alerta('setor_saude', 'oportunidade', 'Saúde: redução de 60% das alíquotas',
        'Os serviços de saúde listados na LC nº 214/2025 têm redução de 60% das alíquotas de IBS e CBS. Confira se cada serviço prestado está no anexo correspondente (classificação pela NBS).',
        ['lc214_saude']));
    }
    if (s.id === 'educacao') {
      out.push(alerta('setor_educacao', 'oportunidade', 'Educação: redução de 60% das alíquotas',
        'Os serviços de educação listados na LC nº 214/2025 têm redução de 60% das alíquotas de IBS e CBS.',
        ['lc214_educacao']));
    }
    if (s.id === 'agro') {
      out.push(alerta('setor_agro_reducoes', 'oportunidade', 'Agro: alíquota zero e redução de 60%',
        'Têm alíquota zero os produtos da Cesta Básica Nacional e os hortícolas, frutas e ovos listados na lei. Têm redução de 60% os produtos agropecuários in natura e os insumos agropecuários dos anexos. O enquadramento é feito item a item pela NCM, por isso a premissa do simulador é apenas ilustrativa.',
        ['lc214_cesta', 'lc214_agro']));
      out.push(alerta('setor_agro_nc', e.faturamento < LIMITE_PRODUTOR_NC ? 'oportunidade' : 'info',
        e.faturamento < LIMITE_PRODUTOR_NC ? 'Produtor rural abaixo de R$ 3,6 milhões não é contribuinte de IBS/CBS, salvo opção' : 'Produtor rural acima de R$ 3,6 milhões é contribuinte de IBS/CBS',
        'O produtor rural com receita inferior a R$ 3,6 milhões no ano-calendário (valor corrigido anualmente pelo IPCA) não é contribuinte de IBS e CBS, mas pode optar, a qualquer tempo, por se inscrever no regime regular; a opção vale para o ano inteiro. Sem a opção, a partir de 2027 o adquirente contribuinte apropria crédito presumido, com percentuais divulgados anualmente. Acima do limite, o produtor apura IBS e CBS normalmente. A escolha afeta o preço negociado com cooperativas, tradings e agroindústrias.',
        ['lc214_produtor_nc', 'lc214_produtor_opcao', 'lc214_credito_presumido']));
    }
    if (s.id === 'industria') {
      out.push(alerta('setor_industria', 'info', 'Indústria: IPI zerado em 2027 e Imposto Seletivo',
        'A partir de 2027, o IPI tem alíquota zero, exceto para produtos que tenham industrialização incentivada na Zona Franca de Manaus. Passam a sofrer o Imposto Seletivo, em incidência única e sem crédito: veículos, embarcações e aeronaves, fumígenos, bebidas alcoólicas e açucaradas, bens minerais e concursos de prognósticos. Revise NCMs e o custo de estoques na virada.',
        ['adct_125_133', 'lc214_is']));
    }
    if (s.id === 'comercio_atacadista') {
      out.push(alerta('setor_atacado', 'atencao', 'Atacado: crédito integral, fim da ST do ICMS e cobrança no destino',
        'O atacadista do regime regular credita o IBS e a CBS pagos nas compras e repassa crédito integral ao varejo. Com a extinção do ICMS em 2033, desaparecem a substituição tributária e o DIFAL; o IBS é devido ao estado e ao município de destino. Centros de distribuição instalados por causa de benefício de ICMS precisam ser reavaliados.',
        ['cf_156a_destino', 'adct_125_133']));
    }
    if (s.id === 'comercio_varejista') {
      out.push(alerta('setor_varejo', 'info', 'Varejo: split payment nos meios de pagamento e cashback',
        'No varejo, a maior parte das vendas passa por cartão e Pix, os primeiros meios a receber o split payment. A lei também prevê a devolução personalizada (cashback) de IBS e CBS a famílias inscritas no CadÚnico com renda mensal per capita de até meio salário mínimo, o que depende da identificação do consumidor (CPF) na nota.',
        ['lc214_split', 'lc214_cashback']));
    }
  }

  /* ---------------- Regras por UF ---------------- */
  function regrasUf(e, s, out) {
    var u = UFS.porSigla[e.uf];
    var setorIncentivo = ['industria', 'agro', 'comercio_atacadista'].indexOf(s.id) >= 0;
    if (u.sudam || u.sudene) {
      var orgao = u.sudam ? 'SUDAM' : 'SUDENE';
      var parcial = u.sudam === 'parcial' || u.sudene === 'parcial' ? ' (apenas os municípios da área de atuação)' : '';
      out.push(alerta('uf_irpj75', e.regime === 'real' && setorIncentivo ? 'oportunidade' : 'info',
        'Área da ' + orgao + ': redução de 75% do IRPJ' + parcial,
        (e.regime === 'real'
          ? 'Empreendimentos de setores prioritários instalados na área da ' + orgao + ' podem reduzir 75% do IRPJ e adicionais, calculados sobre o lucro da exploração, com projeto protocolizado e aprovado até 31/12/2028. O benefício é do IRPJ e não é afetado pela troca de ICMS/PIS/Cofins por IBS/CBS.'
          : 'A redução de 75% do IRPJ da ' + orgao + ' é calculada sobre o lucro da exploração, apurado no Lucro Real. No regime atual (' + ROTULO_REGIME[e.regime] + '), ela não se aplica; vale simular se a migração para o Lucro Real compensa. O prazo para projetos vai até 31/12/2028.') +
          (s.id === 'agro' ? ' No agro, a lista de setores prioritários não inclui a agropecuária em geral: abrange agroindústrias de cadeias específicas (fibras têxteis, óleos vegetais, sucos e conservas, carne e derivados, aquicultura e piscicultura) e a agricultura irrigada em polos.' : ''),
        ['mp2199_art1', 'sudam_prazo', 'lucro_real_exploracao'].concat(s.id === 'agro' ? ['dec4212_setores'] : [])));
    }
    if (u.sudeco && !u.sudam) {
      out.push(alerta('uf_sudeco', 'info', 'Centro-Oeste (SUDECO): sem redução de 75% do IRPJ',
        'A redução de 75% do IRPJ é exclusiva das áreas da SUDAM e da SUDENE. Em ' + u.nome + ', os instrumentos federais regionais são o financiamento do FCO e os benefícios estaduais de ICMS, que serão extintos até 2032.',
        ['mp2199_art1', 'lei7827_fco']));
    }
    if (u.zfm) {
      out.push(alerta('uf_zfm', 'oportunidade', 'Zona Franca de Manaus: tratamento favorecido mantido',
        'A Constituição mantém o diferencial competitivo da Zona Franca de Manaus, e a LC nº 214/2025 traz regras específicas de IBS e CBS (incluindo créditos presumidos) para operações com a ZFM. O IPI segue cobrado sobre produtos concorrentes dos fabricados na zona incentivada.',
        ['adct_92b', 'lc214_zfm']));
    }
    if (u.alc) {
      out.push(alerta('uf_alc', 'info', 'Área de Livre Comércio no estado',
        'Há municípios do estado com Área de Livre Comércio, que tem regime próprio de IBS e CBS na LC nº 214/2025. Verifique se a operação ocorre em uma delas: ' + u.alc + '.',
        ['lc214_zfm']));
    }
    if (e.regime !== 'simples' && setorIncentivo) {
      out.push(alerta('uf_beneficios_icms', 'atencao', 'Benefícios de ICMS em ' + u.sigla + ' terminam até 2032',
        'Incentivos de ICMS concedidos pelo estado perdem efeito com a redução gradual do ICMS (2029 a 2032) e sua extinção em 2033. Benefícios onerosos regulares podem ser compensados, de 2029 a 2032, pelo Fundo de Compensação de Benefícios Fiscais, mediante habilitação. Mapeie os benefícios atuais e os prazos.',
        ['adct_12_fundo', 'adct_125_133']));
      out.push(alerta('uf_subvencao', 'info', 'Subvenções de ICMS e a Lei nº 14.789/2023',
        e.regime === 'real'
          ? 'Desde 2024, subvenções para implantação ou expansão de empreendimento podem gerar crédito fiscal de 25% (alíquota do IRPJ) sobre as receitas de subvenção ligadas à depreciação ou amortização de bens de capital, apurado na ECF. Exige habilitação prévia na Receita Federal e vale só para receitas reconhecidas depois do protocolo.'
          : 'O crédito fiscal de subvenção da Lei nº 14.789/2023 é restrito a empresas do Lucro Real. No Lucro Presumido, o tratamento dos benefícios de ICMS na receita deve ser avaliado caso a caso.',
        ['lei14789']));
    }
    if (['comercio_atacadista', 'industria'].indexOf(s.id) >= 0) {
      out.push(alerta('uf_destino', 'info', 'IBS cobrado no destino',
        'O IBS pertence ao estado e ao município onde está o adquirente. Vendas interestaduais a partir de ' + u.sigla + ' deixam de concentrar arrecadação na origem, e a localização definida apenas por benefício fiscal perde efeito ao fim da transição.',
        ['cf_156a_destino']));
    }
  }

  function estimar(e, s) {
    var ref = CONFIG.simulador.aliquotaReferenciaEstimada;
    var aliqVenda = ref * (1 - s.reducao);
    var debito = e.faturamento * aliqVenda;
    var credito = e.faturamento * e.comprasPct * ref * (1 - s.reducaoCompras);
    var liquido = debito - credito;
    var premissas = [
      'Alíquota de referência estimada de ' + (ref * 100).toFixed(1).replace('.', ',') + '% (IBS + CBS), ainda não fixada.',
      s.reducao ? 'Redução de ' + s.reducao * 100 + '% aplicada a todas as vendas do setor (confira item a item).' : 'Sem redução setorial nas vendas.',
      'Créditos calculados como se todas as compras informadas viessem de fornecedores do regime regular' + (s.reducaoCompras ? ', com redução de ' + s.reducaoCompras * 100 + '% sobre os insumos' : '') + '.',
      'Regime pleno (2033), sem ICMS, ISS, PIS/Cofins residuais da transição.'
    ];
    if (liquido < 0) premissas.push('Resultado negativo indica saldo credor, que pode ser objeto de ressarcimento.');
    var fontes = ['cfg_aliquota_ref'];
    if (s.fonteReducao) fontes.push(s.fonteReducao);
    return {
      titulo: e.regime === 'simples' ? 'Cenário "Simples Híbrido": IBS e CBS no regime regular' : 'Estimativa de IBS + CBS no regime pleno',
      aliquotaReferencia: ref, reducao: s.reducao, aliquotaEfetiva: aliqVenda,
      debito: debito, credito: credito, liquido: liquido, cargaSobreFaturamento: liquido / e.faturamento,
      creditoClienteB2B: e.perfil === 'b2b' ? 100 * aliqVenda : null,
      premissas: premissas, fontes: fontes, pendente: true
    };
  }

  function resumo(e, s, u) {
    var base = 'Para ' + s.rotuloCurto.toLowerCase() + ' em ' + u.nome + ' (' + u.sigla + '), no ' + ROTULO_REGIME[e.regime] +
      ' e com clientes predominantemente ' + (e.perfil === 'b2b' ? 'empresas (B2B)' : 'consumidores finais (B2C)') + ', ';
    if (e.regime === 'simples' && e.perfil === 'b2b') return base + 'o ponto central é a decisão entre manter IBS e CBS no DAS ou apurá-los no regime regular para transferir crédito integral aos clientes.';
    if (e.regime === 'simples') return base + 'o DAS tende a seguir adequado; o foco é revisar cadastros fiscais e acompanhar o split payment.';
    return base + 'o impacto principal está na apuração não cumulativa do IBS e da CBS, na revisão de créditos e preços e na adaptação ao split payment (recolhimento na liquidação financeira).';
  }

  function simular(e) {
    var erros = validar(e);
    if (erros.length) return { entrada: e, erros: erros, alertas: [], estimativa: null, resumo: '' };
    var s = porSetor[e.setor], u = UFS.porSigla[e.uf], alertas = [];
    regrasRegime(e, s, alertas);
    regrasSetor(e, s, alertas);
    regrasUf(e, s, alertas);
    var ordem = { critico: 0, atencao: 1, oportunidade: 2, info: 3 };
    alertas.sort(function (a, b) { return ordem[a.nivel] - ordem[b.nivel]; });
    return { entrada: e, erros: [], alertas: alertas, estimativa: estimar(e, s), resumo: resumo(e, s, u) };
  }

  /* Alertas regionais (seção GO-TO-PA): regras gerais de setor/UF para uma empresa
     do regime regular + alertas específicos do estado (ufs.js → alertasRegionais). */
  function alertasRegionais(uf, setor) {
    var e = { setor: setor, regime: 'real', perfil: 'b2b', uf: uf, faturamento: 10000000, comprasPct: porSetor[setor].comprasPadrao };
    var s = porSetor[setor], out = [];
    (UFS.porSigla[uf].alertasRegionais || []).forEach(function (a) {
      if (a.setores.indexOf(setor) >= 0) out.push(alerta(a.id, a.nivel, a.titulo, a.texto, a.fontes));
    });
    regrasSetor(e, s, out);
    regrasUf(e, s, out);
    return out;
  }

  return { SETORES: SETORES, SETORES_REGIONAIS: SETORES_REGIONAIS, ROTULO_REGIME: ROTULO_REGIME, TRANSICAO: TRANSICAO,
    LIMITES: { simples: LIMITE_SIMPLES, sublimite: SUBLIMITE_SIMPLES, presumido: LIMITE_PRESUMIDO, produtorNaoContribuinte: LIMITE_PRODUTOR_NC },
    setor: function (id) { return porSetor[id]; }, simular: simular, alertasRegionais: alertasRegionais, validar: validar,
    janelaOpcaoSimples: janelaOpcaoSimples };
});
