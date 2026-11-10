/* Conteúdo da reforma tributária como dados (renderizado por conteudo.js).

   Data de referência do levantamento: 31/10/2026 (textos compilados do Planalto: CF/ADCT e LC 214/2025
   com as alterações da LC 227/2026).

   Campos:
   - fato: só o que está no dispositivo citado; orientacao: leitura da ORGATEC, sempre separada do fato.
   - status: em_vigor | vigencia_futura | pendente_regulamentacao | incerto.
   - fontes: ids de fontes.js (obrigatório; item sem fonte não é exibido).
   - consultadoEm: data em que o dispositivo foi conferido. Itens com mais de 90 dias aparecem em
     conteudo.atrasados() e devem ser reconferidos.
   - revisao: { status: 'pendente' | 'aprovada', por, em }. Em produção (config.ambiente = 'producao'),
     só itens com revisão aprovada vão para a tela.
   - historico: mudanças com data; alimentam a Central de Notícias.
   - tema (opcional): agrupamento editorial da lista recolhida do agro (conteudo.TEMAS); não é texto legal.

   Como atualizar: confira o dispositivo na fonte oficial, ajuste fato/status, troque consultadoEm,
   acrescente uma linha em historico e volte revisao.status para 'pendente' até o responsável técnico aprovar. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).reformaItens = factory();
})(this, function () {
  'use strict';
  var REF = '2026-10-31';
  var PENDENTE = { status: 'pendente', por: null, em: null };
  /* Aprovações do responsável técnico, gravadas por tools/aplicar_revisao.py (não edite à mão): id → { por, em, hash }.
     O hash é do texto revisado; tests/js/revisao-aplicada.test.js falha se o texto de um item aprovado mudar depois. */
  /* REVISOES:INICIO */
  var APROVADOS = {};
  /* REVISOES:FIM */
  function revisaoDe(id) { var a = APROVADOS['item:' + id]; return a ? { status: 'aprovada', por: a.por, em: a.em, hash: a.hash } : PENDENTE; }
  function item(o) {
    o.consultadoEm = o.consultadoEm || REF;
    o.revisao = o.revisao || revisaoDe(o.id);
    o.historico = o.historico || [];
    return o;
  }

  return [
    // ---------- Cronograma e tributos criados/extintos
    item({ id: 'teste-2026', pergunta: 'O que muda em 2026, o ano de teste?', titulo: '2026: ano de teste da CBS e do IBS', tributos: ['cbs', 'ibs'], setores: ['todos'],
      fato: 'Em 2026, a CBS é cobrada a 0,9% e o IBS a 0,1% (alíquota estadual). O valor recolhido é compensado com PIS e Cofins. Quem cumpre as obrigações acessórias fica dispensado do recolhimento, e a apuração de 2026 é meramente informativa, sem efeitos tributários. O optante do Simples Nacional não participa do teste.',
      status: 'em_vigor', vigencia: '2026', fontes: ['adct_125_133', 'lc214_2026', 'ato_conjunto_1_2025'], destinos: ['reforma', 'home', 'tributario', 'cliente', 'compliance-tributario', 'publico-comercio', 'publico-servicos'] }),
    item({ id: 'cbs-2027', pergunta: 'Quando o PIS e a Cofins acabam?', titulo: 'CBS substitui PIS e Cofins em 2027', tributos: ['cbs', 'piscofins'], setores: ['todos'],
      fato: 'A partir de 2027, a CBS passa a ser cobrada e o PIS e a Cofins são extintos.',
      orientacao: 'Para empresas no lucro real, 2026 é o ano de levantar e usar os créditos de PIS e Cofins, que continuam válidos depois da extinção nas condições da LC 214.',
      status: 'vigencia_futura', vigencia: '01/01/2027', fontes: ['adct_126'], destinos: ['reforma', 'home', 'tributario', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'ipi-zero-2027', titulo: 'IPI com alíquota zero a partir de 2027', tributos: ['ipi'], setores: ['todos', 'industria'],
      fato: 'A partir de 2027, o IPI tem as alíquotas reduzidas a zero, exceto para produtos com industrialização incentivada na Zona Franca de Manaus, e não incide cumulativamente com o Imposto Seletivo.',
      status: 'vigencia_futura', vigencia: '01/01/2027', fontes: ['adct_126'], destinos: ['reforma', 'publico-comercio'] }),
    item({ id: 'ibs-2027-2028', titulo: '2027 e 2028: IBS a 0,1% e CBS reduzida', tributos: ['ibs', 'cbs'], setores: ['todos'],
      fato: 'Em 2027 e 2028, o IBS é cobrado a 0,05% (estadual) mais 0,05% (municipal), e a alíquota da CBS é reduzida em 0,1 ponto percentual.',
      status: 'vigencia_futura', vigencia: '2027–2028', fontes: ['adct_127'], destinos: ['reforma', 'empresarial-lucro-real'] }),
    item({ id: 'icms-iss-2029-2032', tema: 'obrigacoes', titulo: '2029 a 2032: ICMS e ISS diminuem a cada ano', tributos: ['icms', 'iss', 'ibs'], setores: ['todos'],
      fato: 'De 2029 a 2032, as alíquotas do ICMS e do ISS ficam em 9/10, 8/10, 7/10 e 6/10 das alíquotas da legislação de cada ente, e os benefícios fiscais desses impostos são reduzidos na mesma proporção.',
      orientacao: 'Incentivos estaduais de ICMS usados no agro e na indústria em GO, TO e PA perdem valor nesse período; o planejamento de preço e de investimento precisa considerar a queda ano a ano.',
      status: 'vigencia_futura', vigencia: '2029–2032', fontes: ['adct_128_129', 'adct_12_fundo'], destinos: ['reforma', 'ferramentas', 'setor-agro', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'extincao-2033', pergunta: 'Quando o ICMS e o ISS deixam de existir?', titulo: '2033: fim do ICMS e do ISS', tributos: ['icms', 'iss', 'ibs'], setores: ['todos'],
      fato: 'O ICMS e o ISS ficam extintos a partir de 2033. Saldos credores de ICMS existentes ao final de 2032 podem ser aproveitados nas condições do ADCT, art. 134.',
      status: 'vigencia_futura', vigencia: '01/01/2033', fontes: ['adct_128_129', 'adct_134_135'], destinos: ['reforma', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'imposto-seletivo', titulo: 'Imposto Seletivo a partir de 2027', tributos: ['is'], setores: ['todos', 'industria'],
      fato: 'O Imposto Seletivo é cobrado a partir de 2027, uma única vez e sem crédito, sobre veículos, embarcações e aeronaves, fumígenos, bebidas alcoólicas e açucaradas, bens minerais e concursos de prognósticos e fantasy sport. As alíquotas são fixadas em lei ordinária.',
      status: 'vigencia_futura', vigencia: '01/01/2027', fontes: ['adct_126', 'lc214_is', 'cf_153_is', 'is_lei_ordinaria', 'senado_is_mp'], destinos: ['reforma', 'noticias', 'publico-comercio'],
      historico: [{ data: '2026-10-29', nota: 'Agência Senado informa que as alíquotas do Imposto Seletivo devem sair por medida provisória; publicação não confirmada até 31/10/2026.' }] }),
    item({ id: 'aliquota-referencia', titulo: 'Alíquotas de referência ainda não fixadas', tributos: ['ibs', 'cbs'], setores: ['todos'],
      fato: 'As alíquotas de referência do IBS e da CBS são fixadas por resolução do Senado Federal no ano anterior ao da vigência, com cálculo do Tribunal de Contas da União. Em 28/10/2026, o TCU calculou a alíquota de referência da CBS para 2027 em 11,3468%, arredondada para 11,3%, e o redutor das compras públicas em 44,2%. A resolução do Senado ainda não saiu, e não houve cálculo do IBS para 2027.',
      orientacao: 'Até a resolução do Senado, trate os 11,3% como cenário de planejamento, não como alíquota definida. As estimativas oficiais de 2024 para IBS e CBS somados (26,47%, mais 1,47 ponto pelas mudanças no Congresso) são projeção, e os 26,5% citados na LC 214 são gatilho de avaliação, não teto.',
      status: 'pendente_regulamentacao', vigencia: '2027 (CBS)', fontes: ['adct_130', 'lc214_aliquota_senado', 'tcu_cbs_2027', 'senado_cbs_2027', 'cfg_aliquota_ref'], destinos: ['reforma', 'ferramentas', 'noticias', 'home', 'empresarial-lucro-real'], consultadoEm: '2026-11-03',
      historico: [{ data: '2026-10-28', nota: 'TCU calcula a alíquota de referência da CBS para 2027 em 11,3468%, arredondada para 11,3%, com redutor de 44,2% nas compras públicas; falta a resolução do Senado.' },
        { data: '2026-11-03', nota: 'Agência Senado informa que o cálculo deve chegar em 10/11, com audiência na CAE, e cita o prazo de 15/12 para a resolução.' }] }),
    item({ id: 'regulamento-cbs', titulo: 'Regulamento da CBS publicado', tributos: ['cbs'], setores: ['todos'],
      fato: 'O Decreto nº 12.955/2026 aprovou o Regulamento da CBS. O vencimento da CBS é o último dia útil do mês seguinte ao da apuração, e a vigência do regulamento é escalonada.',
      status: 'em_vigor', fontes: ['cal_cbs', 'dec12955_produtor'], destinos: ['reforma', 'noticias', 'cliente'],
      historico: [{ data: '2026-04-30', nota: 'Publicado o Decreto nº 12.955/2026, Regulamento da CBS.' }, { data: '2026-07-22', nota: 'Decreto nº 13.075/2026 altera o regulamento da CBS (CNPJ e documento fiscal do produtor pessoa física a partir de 2027).' }] }),
    item({ id: 'comite-gestor', titulo: 'Comitê Gestor do IBS instalado e regulamento do IBS publicado', tributos: ['ibs'], setores: ['todos'],
      fato: 'A LC nº 227/2026 instituiu o Comitê Gestor do IBS, que edita o regulamento único do imposto. O regulamento do IBS foi aprovado pela Resolução CGIBS nº 6/2026, alterada pela Resolução nº 13/2026; a parte comum com a CBS foi reconhecida pela Portaria Conjunta MF/CGIBS nº 7/2026.',
      status: 'em_vigor', fontes: ['lc227', 'cgibs_regulamento'], destinos: ['reforma', 'noticias'],
      historico: [{ data: '2026-01-13', nota: 'LC nº 227/2026 institui o Comitê Gestor do IBS.' }, { data: '2026-04-30', nota: 'Publicado o regulamento do IBS (Resolução CGIBS nº 6/2026).' }] }),
    item({ id: 'documentos-fiscais', titulo: 'Campos de IBS e CBS obrigatórios no CT-e, MDF-e e NF-e', tributos: ['cbs', 'ibs'], setores: ['todos', 'transporte'],
      fato: 'Desde 03/08/2026, CT-e, CT-e OS, MDF-e, NF-e e NFC-e devem trazer os campos de IBS e CBS. Para o Simples Nacional, a obrigação começa em 01/01/2027.',
      orientacao: 'Para transportadoras, o CT-e é o primeiro ponto de contato com a reforma: erros de classificação hoje viram inconsistência no programa de conformidade.',
      status: 'em_vigor', vigencia: '03/08/2026', fontes: ['ato_conjunto_4_2026', 'ato_conjunto_1_2025'], destinos: ['reforma', 'setor-transporte', 'cliente', 'noticias', 'compliance-tributario', 'publico-transportador', 'publico-simples', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'],
      historico: [{ data: '2026-07-31', nota: 'Ato Conjunto RFB/CGIBS nº 4/2026 fixa 03/08/2026 para os campos de IBS/CBS nos documentos fiscais.' }] }),
    item({ id: 'conformidade-2026', titulo: 'Programa Nacional de Conformidade Tributária 2026', tributos: ['cbs', 'ibs'], setores: ['todos'],
      fato: 'O programa enquadra quem cumpre as obrigações acessórias de IBS e CBS em 2026. Quem ainda não cumpre continua enquadrado se, entre outros requisitos, corrigir as inconsistências até 31/12/2026 e indicar um contador responsável.',
      orientacao: 'É o principal ponto de atenção de 2026 para clientes: o escritório pode ser indicado como contador responsável e acompanhar as intimações.',
      status: 'em_vigor', vigencia: 'até 31/12/2026', prazo: '2026-12-31', fontes: ['ato_conjunto_5_2026'], destinos: ['cliente', 'tributario', 'noticias', 'home', 'compliance', 'compliance-tributario', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'],
      historico: [{ data: '2026-08-12', nota: 'Ato Conjunto RFB/CGIBS nº 5/2026 cria o Programa Nacional de Conformidade Tributária.' }] }),

    // ---------- Regras gerais, lucro real e regimes
    item({ id: 'nao-cumulatividade', pergunta: 'Como funciona o crédito de IBS e CBS?', titulo: 'Crédito amplo de IBS e CBS', tributos: ['cbs', 'ibs'], setores: ['todos'],
      fato: 'O contribuinte do regime regular credita o IBS e a CBS das aquisições de bens e serviços, exceto as de uso ou consumo pessoal, condicionado à extinção do débito na etapa anterior.',
      orientacao: 'No lucro real, a troca de créditos por lista (PIS/Cofins) por crédito amplo muda a conta de margem: cadastro de fornecedores e documentos fiscais passam a definir o custo.',
      status: 'em_vigor', regimes: ['lucro_real'], fontes: ['lc214_nao_cumulatividade'], destinos: ['reforma', 'tributario', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'saldo-piscofins', titulo: 'Saldos de PIS e Cofins depois da extinção', tributos: ['piscofins', 'cbs'], setores: ['todos'],
      fato: 'Créditos de PIS e Cofins não usados até a extinção continuam válidos, desde que escriturados: podem compensar a CBS e, se cumprirem os requisitos da legislação dessas contribuições, ser ressarcidos ou compensados com outros tributos federais. Créditos apropriados por depreciação seguem como crédito presumido da CBS, e os créditos dos arts. 379 a 381 caducam em 5 anos.',
      status: 'vigencia_futura', vigencia: '01/01/2027', regimes: ['lucro_real'], fontes: ['lc214_saldo_piscofins', 'adct_134_135'], destinos: ['reforma', 'tributario', 'cliente', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'estoque-2027', titulo: 'Crédito presumido sobre o estoque de 1º/01/2027', tributos: ['cbs'], setores: ['todos', 'comercio', 'industria'],
      fato: 'O contribuinte do regime regular da CBS pode apropriar crédito presumido sobre o estoque existente em 1º/01/2027 em casos como: empresa no regime cumulativo de PIS/Cofins em 31/12/2026, bens sujeitos a substituição tributária ou incidência monofásica, e parcela com vedação parcial de crédito.',
      status: 'vigencia_futura', vigencia: '01/01/2027', regimes: ['lucro_presumido'], fontes: ['lc214_saldo_piscofins'], destinos: ['reforma', 'tributario', 'publico-comercio', 'empresarial-lucro-real'] }),
    item({ id: 'split-payment', pergunta: 'O que é o split payment?', titulo: 'Split payment: implantação gradual', tributos: ['cbs', 'ibs'], setores: ['todos'],
      fato: 'O IBS e a CBS podem ser recolhidos na liquidação financeira da operação (split payment). A implantação é gradual, definida em ato conjunto do Comitê Gestor do IBS e da Receita Federal. Já saíram os manuais técnicos, mas não há ato com o cronograma de obrigatoriedade.',
      orientacao: 'O tributo deixa de passar pelo caixa até a guia: transportadoras e atacadistas com margem curta devem revisar capital de giro e conciliação.',
      status: 'pendente_regulamentacao', fontes: ['lc214_split', 'cgibs_split_atos'], destinos: ['reforma', 'tributario', 'setor-transporte', 'publico-comercio', 'publico-servicos', 'empresarial-lucro-real'] }),
    item({ id: 'regimes-especificos', titulo: 'Regimes específicos da LC 214', tributos: ['cbs', 'ibs'], setores: ['todos', 'servicos'],
      fato: 'Têm regras próprias de IBS e CBS: combustíveis, serviços financeiros, planos de saúde, concursos de prognósticos, bens imóveis, cooperativas, hotelaria, parques, bares e restaurantes, agências de turismo, transporte coletivo de passageiros, SAF e missões diplomáticas.',
      status: 'em_vigor', fontes: ['lc214_regimes_especificos'], destinos: ['reforma', 'publico-servicos', 'publico-imoveis'] }),
    item({ id: 'simples-hibrido', pergunta: 'A empresa do Simples pode pagar IBS e CBS fora do DAS?', titulo: 'Simples Nacional: IBS e CBS fora do DAS', tributos: ['cbs', 'ibs'], setores: ['todos'],
      fato: 'O optante do Simples pode apurar IBS e CBS no regime regular. A opção é semestral, feita em setembro ou março, e produz efeitos a partir de 1º/01/2027.',
      status: 'em_vigor', regimes: ['simples'], fontes: ['lc214_art41', 'lc214_credito_simples', 'cgsn_opcao'], destinos: ['reforma', 'tributario', 'ferramentas', 'publico-simples'],
      historico: [{ data: '2026-01-13', nota: 'LC 227/2026 muda a janela de opção para setembro e março.' }] }),

    // ---------- Agro e produtor rural
    item({ id: 'agro-reducao-60', tema: 'aliquotas', titulo: 'Agro: redução de 60% para in natura e insumos', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'Produtos agropecuários, aquícolas, pesqueiros, florestais e extrativistas vegetais in natura e os insumos agropecuários do Anexo IX têm redução de 60% nas alíquotas de IBS e CBS. Secagem, limpeza, debulha, resfriamento ou acondicionamento só para transporte não tiram a condição de in natura.',
      status: 'em_vigor', fontes: ['lc214_agro'], destinos: ['setor-agro', 'reforma', 'tributario', 'publico-produtor'] }),
    item({ id: 'cesta-basica', tema: 'aliquotas', titulo: 'Alíquota zero: cesta básica, hortícolas, frutas e ovos', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'Os produtos da Cesta Básica Nacional (Anexo I) e os hortícolas, frutas e ovos do Anexo XV têm alíquota zero de IBS e CBS.',
      status: 'em_vigor', fontes: ['lc214_cesta'], destinos: ['setor-agro', 'publico-produtor'] }),
    item({ id: 'diferimento-insumos', tema: 'credito', titulo: 'Diferimento nos insumos agropecuários', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'Fica diferido o IBS e a CBS na venda de insumos do Anexo IX por contribuinte do regime regular a outro contribuinte, ou a produtor não contribuinte que venda a produção a adquirentes com direito ao crédito presumido; o mesmo vale na importação.',
      status: 'em_vigor', fontes: ['lc214_diferimento_insumos'], destinos: ['setor-agro', 'publico-produtor'] }),
    item({ id: 'produtor-nao-contribuinte', tema: 'produtor', titulo: 'Produtor rural abaixo de R$ 3,6 milhões não é contribuinte', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'O produtor rural, pessoa física ou jurídica, com receita inferior a R$ 3,6 milhões no ano-calendário e o produtor integrado não são contribuintes de IBS e CBS. O limite é atualizado pelo IPCA e considera a soma das receitas das empresas agropecuárias em que o produtor tem participação. Quem passa do limite vira contribuinte no segundo mês após o excesso ou, se o excesso for de até 20%, no ano seguinte. Pelo regulamento da CBS, quem teve receita de R$ 3,6 milhões ou mais em 2024 é contribuinte desde 01/01/2026.',
      orientacao: 'Produtores com LCDPR e receita perto do limite precisam acompanhar a receita mês a mês: o excesso muda a condição no próprio ano.',
      status: 'em_vigor', regimes: ['produtor_rural'], fontes: ['lc214_produtor_nc', 'dec12955_produtor'], destinos: ['setor-agro', 'ferramentas', 'tributario', 'publico-produtor'] }),
    item({ id: 'lcdpr', tema: 'obrigacoes', titulo: 'LCDPR e IBS/CBS do produtor pessoa física', tributos: ['irpf', 'cbs', 'ibs'], setores: ['agro'],
      fato: 'O LCDPR é obrigação do IRPF do produtor rural pessoa física com receita bruta da atividade rural acima de R$ 4,8 milhões, entregue no prazo da declaração. Não foi localizada norma que ligue o LCDPR à apuração de IBS e CBS. Para o produtor pessoa física, a inscrição no CNPJ e a emissão de documento fiscal exigidas pelo regulamento da CBS valem a partir de 01/01/2027.',
      orientacao: 'O produtor que passar a contribuinte terá dois registros convivendo: o LCDPR, para o IRPF, e a escrituração de IBS e CBS. Conciliar os dois evita divergência de receita entre declarações.',
      status: 'em_vigor', regimes: ['produtor_rural'], fontes: ['rfb_lcdpr', 'dec12955_produtor'], destinos: ['setor-agro', 'tributario', 'cliente', 'publico-produtor'] }),
    item({ id: 'produtor-opcao', tema: 'produtor', titulo: 'Opção do produtor pelo regime regular', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'O produtor não contribuinte pode, a qualquer tempo, se inscrever no regime regular. A opção vale a partir do mês seguinte ao pedido, é irretratável no ano e continua nos anos seguintes até a renúncia, que produz efeitos no ano seguinte.',
      orientacao: 'Vale comparar: como contribuinte, o produtor transfere crédito integral e credita os insumos; sem a opção, o comprador usa crédito presumido, em geral menor. A resposta depende de quem compra (cooperativa, trading, frigorífico) e do peso dos insumos.',
      status: 'em_vigor', regimes: ['produtor_rural'], fontes: ['lc214_produtor_opcao'], destinos: ['setor-agro', 'ferramentas', 'publico-produtor'] }),
    item({ id: 'credito-presumido-produtor', tema: 'credito', titulo: 'Crédito presumido na compra de produtor não contribuinte', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'A partir de 2027, o contribuinte do regime regular que compra de produtor rural não contribuinte apropria crédito presumido. Os percentuais são definidos e divulgados até setembro de cada ano por ato conjunto do Ministro da Fazenda e do Comitê Gestor do IBS e podem variar por produto, receita e tipo de produtor.',
      status: 'pendente_regulamentacao', vigencia: '01/01/2027', fontes: ['lc214_credito_presumido', 'lc214_vigencia'], destinos: ['setor-agro', 'reforma', 'publico-produtor'] }),
    item({ id: 'maquinas-agro', tema: 'aliquotas', titulo: 'Máquinas agrícolas com alíquota zero para o produtor não contribuinte', tributos: ['cbs', 'ibs'], setores: ['agro'],
      fato: 'Tratores, máquinas e implementos agrícolas destinados a produtor rural não contribuinte têm alíquota zero de IBS e CBS, conforme a lista do regulamento.',
      status: 'em_vigor', fontes: ['lc214_maquinas_agro'], destinos: ['setor-agro', 'publico-produtor'] }),

    // ---------- Transporte
    item({ id: 'transporte-carga', titulo: 'Transporte de cargas: regra geral de IBS e CBS', tributos: ['cbs', 'ibs'], setores: ['transporte'],
      fato: 'A LC 214 não traz redução de alíquota para o transporte rodoviário de cargas em geral (o regime específico de redução de 40% alcança o transporte aéreo regional de carga). O local da operação no transporte de carga é o da entrega do bem ao destinatário indicado no documento fiscal.',
      orientacao: 'A transportadora no regime regular passa a creditar IBS e CBS de combustível, peças, pneus e manutenção, o que pode compensar parte da alíquota cheia. A conta depende da estrutura de custos de cada empresa.',
      status: 'em_vigor', fontes: ['lc214_regimes_especificos', 'lc214_transporte_passageiros', 'lc214_local_operacao'], destinos: ['setor-transporte', 'tributario', 'publico-transportador'] }),
    item({ id: 'combustiveis', tema: 'aliquotas', titulo: 'Combustíveis: incidência única e crédito para quem não revende', tributos: ['cbs', 'ibs'], setores: ['transporte', 'agro'],
      fato: 'Nos combustíveis, IBS e CBS incidem uma única vez, com alíquota por unidade de medida, uniforme no país. O crédito é vedado na aquisição para distribuição, comercialização ou revenda e permitido nas demais hipóteses.',
      orientacao: 'A lei não cita transportadoras, mas, pela redação, o diesel comprado por transportadora do regime regular para a frota gera crédito, salvo uso pessoal.',
      status: 'em_vigor', fontes: ['lc214_combustiveis'], destinos: ['setor-transporte', 'setor-agro', 'publico-transportador', 'publico-produtor'] }),
    item({ id: 'tac-credito-presumido', titulo: 'Frete de autônomo: crédito presumido para o contratante', tributos: ['cbs', 'ibs'], setores: ['transporte'],
      fato: 'A partir de 2027, o contribuinte do regime regular que contrata transporte de carga de transportador autônomo pessoa física não contribuinte ou MEI apropria crédito presumido, se suportar o frete diretamente (não vale quando o frete vem embutido no preço do bem).',
      status: 'vigencia_futura', vigencia: '01/01/2027', fontes: ['lc214_tac', 'lc214_vigencia'], destinos: ['setor-transporte', 'publico-transportador'] }),
    item({ id: 'caminhao-tac', titulo: 'Caminhão para autônomo com alíquota zero; caminhões fora do Imposto Seletivo', tributos: ['cbs', 'ibs', 'is'], setores: ['transporte'],
      fato: 'Veículos de transporte de carga destinados a transportador autônomo pessoa física não contribuinte têm alíquota zero de IBS e CBS. No Imposto Seletivo, a lista de veículos do Anexo XVII exclui expressamente os caminhões.',
      status: 'em_vigor', fontes: ['lc214_maquinas_agro', 'lc214_is_veiculos'], destinos: ['setor-transporte', 'publico-transportador'] }),
    item({ id: 'transporte-passageiros', titulo: 'Transporte de passageiros: isenção e redução de 40%', tributos: ['cbs', 'ibs'], setores: ['transporte'],
      fato: 'O transporte público coletivo rodoviário e metroviário urbano, semiurbano e metropolitano é isento. O transporte coletivo rodoviário, ferroviário e hidroviário intermunicipal e interestadual tem redução de 40%, com crédito permitido ao prestador; o aéreo regional de passageiros ou de carga também tem redução de 40%.',
      status: 'em_vigor', fontes: ['lc214_transporte_urbano', 'lc214_transporte_passageiros'], destinos: ['setor-transporte'] }),

    // ---------- Consumidor de baixa renda (Compliance por público, fase P6; conferência de 02/11/2026 no texto integral do Planalto)
    item({ id: 'cashback', pergunta: 'O que é o cashback da reforma tributária?', titulo: 'Devolução personalizada (cashback) de CBS e IBS a famílias de baixa renda',
      tributos: ['cbs', 'ibs'], setores: ['todos'], consultadoEm: '2026-11-02',
      fato: 'A CBS e o IBS serão devolvidos às pessoas físicas de famílias de baixa renda (LC nº 214/2025, art. 112). Recebe o responsável pela família inscrita no CadÚnico com renda familiar mensal per capita de até meio salário mínimo, residente no país e com CPF regular, incluído de forma automática (art. 113). A devolução é calculada sobre o tributo do consumo formalizado em documentos fiscais vinculados ao CPF dos membros da família (art. 117). O percentual é de 100% da CBS e 20% do IBS no botijão de gás de até 13 kg, na energia elétrica, na água, no esgoto, no gás canalizado e nas telecomunicações, e de 20% da CBS e do IBS nos demais casos; União, estados e municípios podem fixar percentuais maiores por lei (art. 118). O momento da devolução é definido em regulamento (art. 116).',
      orientacao: 'Para o comércio e os serviços ao consumidor, o efeito prático é o CPF na nota: a devolução usa os documentos fiscais vinculados ao CPF da família.',
      status: 'pendente_regulamentacao', fontes: ['lc214_cashback'], destinos: ['reforma'] })
  ];
});
