/* Termômetro de conformidade (compliance/termometro.html). Motor puro, sem DOM, testável no Node
   (tests/js/termometro.test.js). Roda só no navegador: nenhuma resposta é enviada.

   Cada pergunta cita a fonte legal (fontes.js) e o item que explica a regra (compliance-itens.js ou
   reforma-itens.js). Respostas: 'sim' | 'nao' | 'nao_sei' | 'na' (não se aplica).
   Pontuação: 'sim' soma o peso; 'nao' e 'nao_sei' entram no máximo e viram pendência; 'na' e as não
   respondidas ficam fora da conta. O resultado é um nível de atenção, NÃO uma probabilidade de autuação.

   PESOS e FAIXAS são provisórios até a revisão técnica (pendência V11). Em produção, enquanto
   REVISAO.status não for 'aprovada', a página não mostra o termômetro. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).termometro = factory();
})(this, function () {
  'use strict';

  var REVISAO = { status: 'pendente', por: null, em: null };
  var RESPOSTAS = { sim: 'Sim', nao: 'Não', nao_sei: 'Não sei', na: 'Não se aplica' };
  // percentual mínimo de cada nível (do maior para o menor)
  var FAIXAS = [
    { nivel: 'em_dia', minimo: 0.85, rotulo: 'Em dia', tom: 'definido' },
    { nivel: 'atencao', minimo: 0.6, rotulo: 'Atenção', tom: 'futuro' },
    { nivel: 'risco', minimo: 0, rotulo: 'Risco', tom: 'pendente' }
  ];
  var PILARES = ['tributario', 'pld', 'lgpd', 'integridade', 'transporte', 'rural', 'pequenos', 'imoveis'];
  // Onde a regra de cada frente aparece: destino dos itens e página (relativa a compliance/), para o "Ver a regra"
  var REGRA = {
    tributario: { destino: 'compliance-tributario', pagina: 'conformidade-tributaria.html' },
    pld: { destino: 'compliance-pld', pagina: 'prevencao-lavagem.html' },
    lgpd: { destino: 'compliance-lgpd', pagina: 'protecao-de-dados.html' },
    integridade: { destino: 'compliance-integridade', pagina: 'integridade.html' },
    transporte: { destino: 'publico-transportador', pagina: 'publico/transportador.html' },
    rural: { destino: 'publico-produtor', pagina: 'publico/produtor-rural.html' }
  };
  // Página de cada público (relativa a compliance/): a pergunta com `publicos` aponta para a página do primeiro deles
  var PAGINA_PUBLICO = { transportador: 'publico/transportador.html', produtor: 'publico/produtor-rural.html', mei: 'publico/mei.html',
    autonomo: 'publico/autonomo.html', simples: 'publico/simples.html', comercio: 'publico/comercio-industria.html', servicos: 'publico/servicos.html',
    imoveis: 'publico/imoveis.html' };
  /* Perfis por público (área "Por público"): as frentes que valem para cada um. 'geral' é o padrão da tela. */
  var PERFIS = {
    geral: { rotulo: 'Qualquer empresa', pilares: ['tributario', 'pld', 'lgpd', 'integridade'] },
    transportador: { rotulo: 'Transportador de cargas', pilares: ['tributario', 'transporte', 'lgpd', 'integridade'] },
    produtor: { rotulo: 'Produtor rural', pilares: ['tributario', 'rural', 'lgpd'] },
    mei: { rotulo: 'MEI', pilares: ['pequenos', 'lgpd'] },
    autonomo: { rotulo: 'Autônomo e profissional liberal', pilares: ['pequenos', 'lgpd'] },
    simples: { rotulo: 'Simples Nacional', pilares: ['pequenos', 'lgpd', 'integridade'] },
    comercio: { rotulo: 'Comércio e indústria', pilares: ['tributario', 'pld', 'lgpd', 'integridade'] },
    servicos: { rotulo: 'Prestador de serviço', pilares: ['tributario', 'lgpd', 'integridade'] },
    imoveis: { rotulo: 'Pessoa física com imóveis', pilares: ['imoveis'] }
  };

  var PERGUNTAS = [
    // Conformidade tributária
    { id: 't-docs-fiscais', pilar: 'tributario', peso: 3, item: 'documentos-fiscais', fontes: ['ato_conjunto_4_2026'],
      texto: 'As notas e os conhecimentos que a empresa emite (NF-e, CT-e, MDF-e) trazem os campos de IBS e CBS desde 03/08/2026?',
      corrigir: 'Ajustar o emissor de documentos fiscais para preencher os campos de IBS e CBS.' },
    { id: 't-obrigacoes-2026', pilar: 'tributario', peso: 3, item: 'teste-2026', fontes: ['lc214_2026'],
      texto: 'A empresa está cumprindo as obrigações acessórias de IBS e CBS de 2026?',
      corrigir: 'Regularizar as obrigações acessórias de IBS e CBS de 2026; quem as cumpre fica dispensado do recolhimento no ano de teste.' },
    { id: 't-inconsistencias', pilar: 'tributario', peso: 3, item: 'conformidade-2026', fontes: ['ato_conjunto_5_2026'],
      texto: 'Se a empresa recebeu apontamentos de inconsistências do Programa Nacional de Conformidade de 2026, eles serão corrigidos até 31/12/2026?',
      corrigir: 'Corrigir as inconsistências do programa de conformidade até 31/12/2026.' },
    { id: 't-contador-responsavel', pilar: 'tributario', peso: 2, item: 'conformidade-2026', fontes: ['ato_conjunto_5_2026'],
      texto: 'A empresa tem um contador responsável indicado no programa de conformidade de 2026?',
      corrigir: 'Indicar um contador responsável no programa de conformidade de 2026.' },
    { id: 't-produtor-2027', pilar: 'tributario', peso: 2, item: 'produtor-cnpj-documento-2027', fontes: ['dec13075_2026'],
      texto: 'Se é produtor rural pessoa física, já se prepara para a inscrição no CNPJ e a emissão de documentos fiscais a partir de 01/01/2027?',
      corrigir: 'Preparar a inscrição no CNPJ e a emissão de documentos fiscais do produtor para 01/01/2027.' },
    // Prevenção à lavagem de dinheiro
    { id: 'p-enquadramento', pilar: 'pld', peso: 2, item: 'pld-quem-e-obrigado', fontes: ['lei9613'],
      texto: 'A empresa sabe se está entre as pessoas obrigadas pela Lei nº 9.613/1998 (por exemplo, comércio de bens de alto valor, inclusive de origem rural ou animal, factoring ou imóveis)?',
      corrigir: 'Verificar se a atividade da empresa está entre as pessoas obrigadas da Lei nº 9.613/1998.' },
    { id: 'p-cadastro', pilar: 'pld', peso: 3, item: 'pld-cadastro-registro', fontes: ['lei9613'],
      texto: 'Se é obrigada: mantém cadastro atualizado dos clientes e o registro das operações por pelo menos cinco anos?',
      corrigir: 'Organizar o cadastro de clientes e o registro das operações, guardados por no mínimo cinco anos.' },
    { id: 'p-controles', pilar: 'pld', peso: 2, item: 'pld-cadastro-registro', fontes: ['lei9613'],
      texto: 'Se é obrigada: adota políticas e controles internos compatíveis com o porte e está cadastrada no órgão regulador ou no COAF?',
      corrigir: 'Formalizar políticas e controles internos de prevenção e fazer o cadastro no órgão regulador ou no COAF.' },
    { id: 'p-comunicacao', pilar: 'pld', peso: 3, item: 'pld-comunicacoes', fontes: ['lei9613'],
      texto: 'Se é obrigada: tem um procedimento para comunicar ao COAF, em 24 horas, as operações suspeitas e para informar a não ocorrência?',
      corrigir: 'Definir quem comunica ao COAF em 24 horas e como informar a não ocorrência.' },
    // Proteção de dados (LGPD)
    { id: 'l-registro', pilar: 'lgpd', peso: 2, item: 'lgpd-registro-seguranca', fontes: ['lei13709'],
      texto: 'A empresa mantém registro das operações com dados pessoais (de clientes, empregados e fornecedores)?',
      corrigir: 'Montar o registro das operações de tratamento de dados pessoais (simplificado, se for pequena empresa).' },
    { id: 'l-encarregado', pilar: 'lgpd', peso: 2, item: 'lgpd-pequeno-porte', fontes: ['lei13709', 'res_anpd_2_2022'],
      texto: 'A empresa indicou um encarregado de dados ou, se for pequena empresa dispensada, mantém um canal de comunicação com os titulares?',
      corrigir: 'Indicar o encarregado ou, se dispensada, abrir um canal de comunicação com os titulares.' },
    { id: 'l-seguranca', pilar: 'lgpd', peso: 3, item: 'lgpd-registro-seguranca', fontes: ['lei13709'],
      texto: 'A empresa adota medidas técnicas e administrativas de segurança para os dados pessoais?',
      corrigir: 'Adotar medidas de segurança técnicas e administrativas para os dados pessoais.' },
    { id: 'l-incidente', pilar: 'lgpd', peso: 2, item: 'lgpd-incidente', fontes: ['lei13709'],
      texto: 'A empresa sabe como comunicar à ANPD e aos titulares um incidente de segurança com risco ou dano relevante?',
      corrigir: 'Definir o procedimento de comunicação de incidentes à ANPD e aos titulares.' },
    // Integridade e anticorrupção
    { id: 'i-codigo', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['lei12846', 'dec11129_2022'],
      texto: 'A empresa tem código de ética ou de conduta aplicado na prática, com um canal para denúncias?',
      corrigir: 'Adotar código de conduta e canal de denúncias, aplicados na prática.' },
    { id: 'i-riscos', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['dec11129_2022'],
      texto: 'A empresa avalia riscos e faz diligência sobre terceiros (fornecedores e intermediários) nas relações com o setor público?',
      corrigir: 'Incluir gestão de riscos e diligência sobre terceiros nas relações com o setor público.' },
    { id: 'i-contrato-publico', pilar: 'integridade', peso: 2, item: 'integridade-contratos-publicos', fontes: ['lei14133_integridade'],
      texto: 'Se a empresa tem ou disputa contratos públicos de grande vulto, está preparada para implantar programa de integridade em até 6 meses da celebração do contrato?',
      corrigir: 'Planejar o programa de integridade para cumprir o prazo de 6 meses dos contratos de grande vulto.' },
    // Cultura e relatos (estudo do compliance moderno, frente 3.3): parâmetros do art. 57 do Decreto nº 11.129/2022
    { id: 'i-alta-direcao', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['dec11129_2022'], cultura: true,
      texto: 'A direção apoia o programa de forma visível e reserva tempo e recursos para ele (art. 57, I)?',
      corrigir: 'Registrar o apoio da direção ao programa e definir quem cuida dele, com tempo e recursos.' },
    { id: 'i-relatos-tratados', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['dec11129_2022'], cultura: true,
      texto: 'O último relato recebido pelo canal teve resposta e registro da apuração, com proteção a quem relatou de boa-fé (art. 57, X)?',
      corrigir: 'Definir prazo de resposta, registro da apuração e proteção a quem relata de boa-fé.' },
    { id: 'i-remediacao', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['dec11129_2022'], cultura: true,
      texto: 'Quando uma irregularidade é confirmada, a empresa interrompe, corrige o dano e aplica a medida disciplinar prevista (art. 57, XI e XII)?',
      corrigir: 'Escrever o procedimento de interrupção, remediação e medida disciplinar, e registrar cada caso.' },
    { id: 'i-monitoramento', pilar: 'integridade', peso: 2, item: 'integridade-programa', fontes: ['dec11129_2022'], cultura: true,
      texto: 'O programa é revisto periodicamente, com mudanças registradas a partir dos riscos e dos casos (art. 57, V e XV)?',
      corrigir: 'Agendar a revisão periódica do programa e registrar o que mudou e por quê.' },
    // Obrigações do transportador (perfil "Transportador de cargas")
    { id: 'tr-rntrc', pilar: 'transporte', peso: 3, item: 'transporte-rntrc', fontes: ['lei11442'],
      texto: 'A inscrição da empresa (ou do autônomo) no RNTRC da ANTT está ativa e revalidada neste ano?',
      corrigir: 'Revalidar a inscrição no RNTRC; a revalidação é anual.' },
    { id: 'tr-ciot', pilar: 'transporte', peso: 3, item: 'transporte-ciot', fontes: ['lei13703', 'res_antt_6090'],
      texto: 'Quando a empresa contrata frete, o CIOT é emitido antes de cada operação, por instituição de pagamento habilitada pela ANTT?',
      corrigir: 'Emitir o CIOT antes de cada operação contratada, por instituição de pagamento habilitada (obrigatório desde 18/09/2026).' },
    { id: 'tr-piso', pilar: 'transporte', peso: 2, item: 'transporte-piso-frete', fontes: ['lei13703'],
      texto: 'Os fretes contratados ou recebidos respeitam o piso mínimo da tabela vigente da ANTT?',
      corrigir: 'Conferir os fretes com a tabela de pisos mínimos vigente da ANTT, atualizada até 20/01 e 20/07.' },
    { id: 'tr-pagamento-tac', pilar: 'transporte', peso: 2, item: 'transporte-pagamento-tac', fontes: ['lei11442'],
      texto: 'Quando contrata autônomo (TAC), o frete é pago na conta escolhida por ele e informado no DT-e, sem custo para o TAC?',
      corrigir: 'Pagar o frete do TAC em conta de livre escolha dele, informado no DT-e, com as tarifas por conta de quem paga.' },
    { id: 'tr-vale-pedagio', pilar: 'transporte', peso: 2, item: 'transporte-vale-pedagio', fontes: ['lei10209'],
      texto: 'Quando a empresa embarca carga ou subcontrata autônomo, o vale-pedágio é antecipado e consignado no DT-e?',
      corrigir: 'Antecipar o vale-pedágio ao transportador e consigná-lo no DT-e.' },
    { id: 'tr-jornada', pilar: 'transporte', peso: 2, item: 'transporte-jornada-motorista', fontes: ['clt_motorista', 'stf_adi5322'],
      texto: 'A jornada dos motoristas empregados é controlada, com o tempo de espera contado como jornada e o descanso de 11 horas sem fracionamento?',
      corrigir: 'Ajustar o controle de jornada dos motoristas ao que ficou valendo depois da ADI 5322.' },
    { id: 'tr-toxicologico', pilar: 'transporte', peso: 2, item: 'transporte-exame-toxicologico', fontes: ['ctb_148a', 'clt_motorista'],
      texto: 'Os motoristas das categorias C, D e E estão com o exame toxicológico em dia (a cada 2 anos e 6 meses)?',
      corrigir: 'Controlar o vencimento do exame toxicológico de cada motorista das categorias C, D e E.' },
    // Obrigações do produtor rural (perfil "Produtor rural")
    { id: 'ru-car', pilar: 'rural', peso: 3, item: 'rural-car', fontes: ['lei12651_car'],
      texto: 'Todos os imóveis rurais (próprios ou em posse) estão inscritos no CAR?',
      corrigir: 'Inscrever no CAR todos os imóveis rurais; sem a inscrição, não há crédito agrícola.' },
    { id: 'ru-itr', pilar: 'rural', peso: 3, item: 'rural-itr', fontes: ['lei9393_itr'],
      texto: 'A declaração do ITR foi entregue e o imposto pago, para cada imóvel, nos últimos cinco exercícios?',
      corrigir: 'Regularizar a declaração e o pagamento do ITR dos últimos cinco exercícios; eles condicionam o crédito rural e os incentivos fiscais.' },
    { id: 'ru-funrural', pilar: 'rural', peso: 2, item: 'rural-funrural', fontes: ['lei8212_funrural'],
      texto: 'Se é empregador rural pessoa física: a forma de contribuição do ano (receita da comercialização ou folha) foi escolhida de propósito, com o pagamento da folha de janeiro se a opção for pela folha?',
      corrigir: 'Comparar o Funrural sobre a receita com a contribuição sobre a folha e, se valer a pena, optar pagando a folha de janeiro.' },
    { id: 'ru-nr31', pilar: 'rural', peso: 2, item: 'rural-nr31', fontes: ['nr31'],
      texto: 'Se tem empregados no campo: cada estabelecimento tem o PGRTR elaborado e os riscos foram comunicados aos trabalhadores?',
      corrigir: 'Elaborar e implementar o PGRTR de cada estabelecimento rural e comunicar os riscos aos trabalhadores.' },
    { id: 'ru-eudr', pilar: 'rural', peso: 2, item: 'rural-eudr', fontes: ['ue_eudr'],
      texto: 'Se vende soja, gado, café, madeira ou outro produto do regulamento para exportação à União Europeia: consegue comprovar que a área não foi desmatada após 31/12/2020?',
      corrigir: 'Organizar o CAR, os mapas da área e os documentos que provam a origem para atender o comprador europeu a partir de 30/12/2026.' },
    // MEI, autônomo e Simples: cada pergunta vale só para os públicos listados (e para o perfil geral, se a frente for marcada)
    { id: 'pq-mei-limite', pilar: 'pequenos', publicos: ['mei'], peso: 3, item: 'mei-limite-2027', fontes: ['lc238_2026'],
      texto: 'A receita bruta prevista para 2027 cabe no limite do MEI de R$ 110.000,00?',
      corrigir: 'Acompanhar a receita do ano: acima do limite do MEI, é preciso mudar de enquadramento.' },
    { id: 'pq-mei-remissao', pilar: 'pequenos', publicos: ['mei'], peso: 2, item: 'mei-remissao', fontes: ['lc238_2026'],
      texto: 'Se há débitos da contribuição mensal do MEI até 13/10/2026: as contribuições dos 6 meses seguintes à lei estão sendo pagas em dia, para não perder o perdão?',
      corrigir: 'Pagar em dia a contribuição mensal do MEI nos 6 meses seguintes à LC nº 238/2026 e pedir a baixa quando a PGFN abrir o procedimento.' },
    { id: 'pq-nanoempreendedor', pilar: 'pequenos', publicos: ['autonomo', 'mei'], peso: 3, item: 'pf-contribuinte', fontes: ['lc214_pf'],
      texto: 'Você sabe se a sua receita como pessoa física passa de metade do limite do MEI, o que faz de você contribuinte de IBS e CBS?',
      corrigir: 'Calcular a receita bruta do ano (motorista e entregador de aplicativo: 25% do valor recebido) e conferir se passa de metade do limite do MEI.' },
    { id: 'pq-cadastro-pf', pilar: 'pequenos', publicos: ['autonomo'], peso: 2, item: 'pf-contribuinte', fontes: ['lc214_pf'],
      texto: 'Se a atividade é habitual ou profissional e a receita passa do limite do nanoempreendedor: você está pronto para se inscrever nos cadastros de IBS e CBS e emitir documento fiscal?',
      corrigir: 'Preparar a inscrição nos cadastros de IBS e CBS e a emissão de documentos fiscais da atividade.' },
    { id: 'pq-profissao-30', pilar: 'pequenos', publicos: ['autonomo'], peso: 2, item: 'profissoes-reducao-30', fontes: ['lc214_art127'],
      texto: 'Se a sua profissão é fiscalizada por conselho (contador, advogado, engenheiro...): os serviços estão ligados à sua habilitação, para usar a redução de 30%?',
      corrigir: 'Conferir se a profissão está entre as 18 do art. 127 e se os serviços estão ligados à habilitação (na sociedade, os requisitos do § 1º).' },
    { id: 'pq-simples-opcao', pilar: 'pequenos', publicos: ['simples'], peso: 3, item: 'simples-janela-opcao', fontes: ['lc214_art41', 'cgsn_opcao'],
      texto: 'A empresa avaliou se vale apurar IBS e CBS fora do DAS e sabe que a próxima janela é março de 2027, para o 2º semestre?',
      corrigir: 'Comparar IBS e CBS dentro e fora do DAS (crédito dos clientes empresas e das compras) antes da janela de março de 2027.' },
    { id: 'pq-simples-docs-2027', pilar: 'pequenos', publicos: ['simples'], peso: 3, item: 'documentos-fiscais', fontes: ['ato_conjunto_4_2026'],
      texto: 'O emissor de notas da empresa estará pronto para os campos de IBS e CBS a partir de 01/01/2027?',
      corrigir: 'Atualizar o emissor de documentos fiscais para os campos de IBS e CBS, obrigatórios no Simples a partir de 01/01/2027.' },
    { id: 'pq-simples-locacao', pilar: 'pequenos', publicos: ['simples'], peso: 2, item: 'simples-locacao-imoveis', fontes: ['lc214_art516'],
      texto: 'Se a empresa aluga imóveis próprios: ela já verificou que essa atividade impede o Simples Nacional?',
      corrigir: 'Rever o enquadramento: a locação de imóveis próprios impede o Simples Nacional desde 01/01/2025.' },
    // Comércio e indústria; prestadores de serviço (perguntas tributárias que valem só para esses perfis e para o geral)
    { id: 'tc-estoque', pilar: 'tributario', publicos: ['comercio'], peso: 2, item: 'estoque-2027', fontes: ['lc214_saldo_piscofins'],
      texto: 'A empresa vai levantar o estoque de 01/01/2027 para o crédito presumido de CBS sobre os bens em estoque?',
      corrigir: 'Planejar o inventário de 01/01/2027 e separar os bens que dão direito ao crédito presumido de CBS.' },
    { id: 'tc-saldo-icms', pilar: 'tributario', publicos: ['comercio'], peso: 2, item: 'comercio-saldo-icms', fontes: ['adct_134_135'],
      texto: 'Os saldos credores de ICMS (inclusive de ativo permanente) estão conciliados com a escrituração, para a homologação e a compensação com o IBS?',
      corrigir: 'Conciliar o saldo credor de ICMS com a escrituração; só o saldo admitido e homologado será compensado com o IBS.' },
    { id: 'ts-reducao-60', pilar: 'tributario', publicos: ['servicos'], peso: 2, item: 'servicos-reducao-60', fontes: ['lc214_saude', 'lc214_educacao'],
      texto: 'Se a empresa presta serviços de saúde ou de educação: conferiu se cada serviço está nos anexos da LC nº 214/2025, com a classificação na NBS?',
      corrigir: 'Classificar cada serviço na NBS e conferir se está no Anexo II (educação) ou III (saúde) para a redução de 60%.' },
    { id: 'ts-profissao-30', pilar: 'tributario', publicos: ['servicos'], peso: 2, item: 'profissoes-reducao-30', fontes: ['lc214_art127'],
      texto: 'Se é sociedade de profissionais com conselho (contadores, advogados, engenheiros...): cumpre todos os requisitos do art. 127, § 1º, para a redução de 30%?',
      corrigir: 'Conferir os requisitos da sociedade: sócios habilitados, nenhum sócio pessoa jurídica e serviços prestados pelos sócios.' },
    // Pessoa física com imóveis
    { id: 'im-enquadramento', pilar: 'imoveis', publicos: ['imoveis'], peso: 3, item: 'imoveis-pf-contribuinte', fontes: ['lc214_imoveis'],
      texto: 'Você conferiu, com a receita de aluguel e as vendas do ano anterior, se passou a ser contribuinte de IBS e CBS como pessoa física?',
      corrigir: 'Somar a receita de aluguel e contar os imóveis alugados e vendidos no ano anterior (art. 251); a calculadora da página faz a conta.' },
    { id: 'im-temporada', pilar: 'imoveis', publicos: ['imoveis'], peso: 2, item: 'imoveis-pf-contribuinte', fontes: ['lc214_imoveis'],
      texto: 'Se aluga por temporada (até 90 dias), essas receitas estão somadas às demais na conta do limite?',
      corrigir: 'Incluir a locação por temporada na conta do limite de receita (art. 253, § 2º).' },
    { id: 'im-redutor', pilar: 'imoveis', publicos: ['imoveis'], peso: 2, item: 'imoveis-reducoes', fontes: ['lc214_imoveis'],
      texto: 'Se já é contribuinte e aluga imóvel residencial: o cálculo usa a redução de 70% e o redutor social de R$ 600,00 por mês por imóvel?',
      corrigir: 'Aplicar a redução de 70% da locação e o redutor social residencial no cálculo do IBS e da CBS.' }
  ];

  /* Camadas de prova (docs/estudo-compliance-moderno.md, seção 3.1): nas perguntas de peso 3, quem responde "sim"
     diz também se o controle funcionou no período e se há registro que mostre. Não muda o percentual, que continua
     medindo declarações: vira um indicador à parte. */
  var CAMADAS = {
    't-docs-fiscais': { funciona: 'Nos últimos 3 meses, alguma nota saiu sem os campos de IBS e CBS?', prova: 'Dá para mostrar o XML de notas recentes com os campos preenchidos?', invertida: true },
    't-obrigacoes-2026': { funciona: 'As obrigações de 2026 foram entregues dentro do prazo até agora?', prova: 'Há recibos ou protocolos das entregas?' },
    't-inconsistencias': { funciona: 'Os apontamentos já corrigidos sumiram da consulta do programa?', prova: 'Há registro do que foi corrigido e quando?' },
    'p-cadastro': { funciona: 'Os cadastros dos clientes do último ano estão completos?', prova: 'Uma amostra de cadastros e registros pode ser mostrada?' },
    'p-comunicacao': { funciona: 'O procedimento foi usado ou testado no último ano?', prova: 'Há registro das comunicações ou da declaração de não ocorrência?' },
    'l-seguranca': { funciona: 'Acessos, senhas e cópias de segurança foram revisados no último ano?', prova: 'Há registro dessa revisão?' },
    'tr-rntrc': { funciona: 'A revalidação deste ano já foi feita?', prova: 'Há o comprovante da ANTT?' },
    'tr-ciot': { funciona: 'Nos últimos 3 meses, algum frete contratado saiu sem CIOT?', prova: 'Dá para listar os CIOT do período pela instituição de pagamento?', invertida: true },
    'ru-car': { funciona: 'Os dados do CAR batem com a área e os documentos atuais do imóvel?', prova: 'Há os recibos de inscrição de cada imóvel?' },
    'ru-itr': { funciona: 'Algum dos últimos 5 exercícios ficou sem entrega ou sem pagamento?', prova: 'Os recibos dos 5 exercícios estão guardados?', invertida: true },
    'pq-mei-limite': { funciona: 'A receita está sendo somada mês a mês?', prova: 'Há o controle mensal de receitas?' },
    'pq-nanoempreendedor': { funciona: 'A receita do ano está sendo somada mês a mês?', prova: 'Há extratos ou um controle que mostre a receita?' },
    'pq-simples-opcao': { funciona: 'A comparação foi feita com números da própria empresa?', prova: 'Há a simulação guardada?' },
    'pq-simples-docs-2027': { funciona: 'Já saiu nota de teste com os campos de IBS e CBS?', prova: 'Há o XML de teste validado?' },
    'im-enquadramento': { funciona: 'A conta usou a receita e os imóveis do ano anterior completos?', prova: 'Há os contratos e recibos que sustentam a conta?' }
  };

  /* Quantas respostas "sim" nas perguntas com camada foram confirmadas na prática e com registro.
     Resposta de "funciona": 'sim' confirma; em pergunta `invertida` (ex.: "alguma nota saiu sem..."), confirma o 'nao'. */
  /* Pesos por perfil (estudo, frente 3.2). Cada ajuste traz justificativa e fonte; enquanto `status` não for
     'aprovada', o peso padrão da pergunta continua valendo. O julgamento fica escrito para o responsável técnico revisar. */
  var PESOS_PERFIL = {
    status: 'proposta', por: null, em: null,
    ajustes: {
      simples: {
        'i-codigo': { peso: 1, fontes: ['dec11129_2022'], justificativa: 'O art. 57, § 1º, I e II, manda considerar o porte: número de empregados, faturamento e o fato de ser ME ou EPP.' },
        'i-riscos': { peso: 1, fontes: ['dec11129_2022'], justificativa: 'O art. 57, § 1º, manda considerar o porte; diligência proporcional ao tamanho da empresa.' }
      },
      transportador: {
        'i-riscos': { peso: 3, fontes: ['dec11129_2022'], justificativa: 'O art. 57, § 1º, VII, manda considerar o grau de interação com o setor público, inclusive autorizações e licenças, frequentes no transporte (RNTRC, fiscalização).' }
      }
    }
  };
  function pesoDe(p, perfil, pesos) {
    pesos = pesos || PESOS_PERFIL;
    if (pesos.status !== 'aprovada' || !perfil) return p.peso;
    var a = (pesos.ajustes[perfil] || {})[p.id];
    return a ? a.peso : p.peso;
  }

  function evidencia(respostas, perguntas) {
    respostas = respostas || {};
    var r = { declaradas: 0, funcionam: 0, comProva: 0, semProva: [] };
    (perguntas || PERGUNTAS).forEach(function (p) {
      var c = CAMADAS[p.id];
      if (!c || respostas[p.id] !== 'sim') return;
      r.declaradas++;
      var f = respostas[p.id + '__funciona'], ok = c.invertida ? f === 'nao' : f === 'sim';
      if (ok) r.funcionam++;
      if (ok && respostas[p.id + '__prova'] === 'sim') r.comProva++;
      else r.semProva.push(p);
    });
    return r;
  }

  /* Plano de ação: pendências cujo item tem prazo de hoje em diante, em ordem de data (para o .ics). */
  function planoDeAcao(pendencias, itensPorId, hoje) {
    return (pendencias || []).map(function (pd) {
      var it = itensPorId[pd.pergunta.item];
      return it && it.prazo && it.prazo >= hoje ? { id: 'termometro-' + pd.pergunta.id, data: it.prazo, titulo: 'ORGATEC: ' + pd.pergunta.corrigir } : null;
    }).filter(Boolean).sort(function (a, b) { return a.data < b.data ? -1 : a.data > b.data ? 1 : 0; });
  }

  function faixa(percentual) {
    if (percentual == null) return null;
    for (var i = 0; i < FAIXAS.length; i++) if (percentual >= FAIXAS[i].minimo) return FAIXAS[i];
    return FAIXAS[FAIXAS.length - 1];
  }

  /* A pergunta vale para o perfil? Sem `publicos`, vale para todos; com a lista, só para eles e para o perfil geral. */
  function perguntaVale(p, perfil) { return !p.publicos || !perfil || perfil === 'geral' || p.publicos.indexOf(perfil) >= 0; }

  /* Onde está a regra da pergunta: a página do primeiro público dela ou, sem `publicos`, a página da frente. */
  function regraDe(p) {
    if (p.publicos && p.publicos.length) return { destino: 'publico-' + p.publicos[0], pagina: PAGINA_PUBLICO[p.publicos[0]] };
    return REGRA[p.pilar];
  }

  /* respostas: { idPergunta: 'sim'|'nao'|'nao_sei'|'na' }; pilares: frentes consideradas (todas por padrão); perfil: filtra as perguntas por público. */
  function avaliar(respostas, pilares, perfil, pesos) {
    respostas = respostas || {};
    pilares = pilares && pilares.length ? pilares : PILARES;
    var consideradas = PERGUNTAS.filter(function (p) { return pilares.indexOf(p.pilar) >= 0 && perguntaVale(p, perfil); });
    var pontos = 0, maximo = 0, respondidas = 0, pendencias = [], porPilar = {};
    pilares.forEach(function (p) { porPilar[p] = { pontos: 0, maximo: 0 }; });
    consideradas.forEach(function (p, ordem) {
      var r = respostas[p.id];
      if (!RESPOSTAS[r]) return;
      respondidas++;
      if (r === 'na') return;
      var peso = pesoDe(p, perfil, pesos);
      maximo += peso; porPilar[p.pilar].maximo += peso;
      if (r === 'sim') { pontos += peso; porPilar[p.pilar].pontos += peso; return; }
      pendencias.push({ pergunta: p, tipo: r === 'nao' ? 'corrigir' : 'verificar', ordem: ordem });
    });
    pendencias.sort(function (a, b) { return b.pergunta.peso - a.pergunta.peso || a.ordem - b.ordem; });
    var percentual = maximo ? pontos / maximo : null;
    Object.keys(porPilar).forEach(function (k) {
      var x = porPilar[k];
      x.percentual = x.maximo ? x.pontos / x.maximo : null;
      x.faixa = faixa(x.percentual);
    });
    return { pontos: pontos, maximo: maximo, percentual: percentual, faixa: faixa(percentual), respondidas: respondidas,
      total: consideradas.length, pendencias: pendencias, porPilar: porPilar };
  }

  /* Erros de consistência: fonte ou item inexistente, frente inválida, id repetido, peso fora de 1 a 3. */
  function validar(fontesPorId, itensPorId) {
    var erros = [], vistos = {};
    PERGUNTAS.forEach(function (p) {
      if (vistos[p.id]) erros.push('id repetido: ' + p.id);
      vistos[p.id] = true;
      if (PILARES.indexOf(p.pilar) < 0) erros.push(p.id + ': frente inválida');
      if (!(p.peso >= 1 && p.peso <= 3)) erros.push(p.id + ': peso fora de 1 a 3');
      if (!p.fontes || !p.fontes.length) erros.push(p.id + ': sem fonte');
      (p.fontes || []).forEach(function (f) { if (!fontesPorId[f]) erros.push(p.id + ': fonte inexistente ' + f); });
      if (!itensPorId[p.item]) erros.push(p.id + ': item inexistente ' + p.item);
      if (!p.texto || !p.corrigir) erros.push(p.id + ': texto ou correção ausente');
      else if (itensPorId[p.item] && regraDe(p) && itensPorId[p.item].destinos.indexOf(regraDe(p).destino) < 0)
        erros.push(p.id + ': o item não aparece na página da frente');
      (p.publicos || []).forEach(function (k) { if (!PERFIS[k] || !PAGINA_PUBLICO[k]) erros.push(p.id + ': público sem perfil ou página ' + k); });
      if (!p.publicos && !REGRA[p.pilar]) erros.push(p.id + ': frente sem página e pergunta sem público');
    });
    Object.keys(PERFIS).forEach(function (k) {
      PERFIS[k].pilares.forEach(function (p) { if (PILARES.indexOf(p) < 0) erros.push('perfil ' + k + ': frente inválida ' + p); });
    });
    PILARES.forEach(function (p) { if (!REGRA[p] && !PERGUNTAS.every(function (q) { return q.pilar !== p || q.publicos; })) erros.push(p + ': frente sem página'); });
    Object.keys(PESOS_PERFIL.ajustes).forEach(function (perfil) {
      if (!PERFIS[perfil]) erros.push('peso de perfil inexistente: ' + perfil);
      Object.keys(PESOS_PERFIL.ajustes[perfil]).forEach(function (id) {
        var a = PESOS_PERFIL.ajustes[perfil][id], q = PERGUNTAS.filter(function (p) { return p.id === id; })[0];
        if (!q) erros.push(perfil + ': peso de pergunta inexistente ' + id);
        if (!(a.peso >= 1 && a.peso <= 3)) erros.push(perfil + '/' + id + ': peso fora de 1 a 3');
        if (!a.justificativa || !a.fontes || !a.fontes.length) erros.push(perfil + '/' + id + ': peso sem justificativa ou fonte');
        (a.fontes || []).forEach(function (f) { if (!fontesPorId[f]) erros.push(perfil + '/' + id + ': fonte inexistente ' + f); });
      });
    });
    Object.keys(CAMADAS).forEach(function (id) {
      var q = PERGUNTAS.filter(function (p) { return p.id === id; })[0];
      if (!q) erros.push('camada sem pergunta: ' + id);
      else if (q.peso !== 3) erros.push(id + ': camada só nas perguntas de peso 3');
      if (!CAMADAS[id].funciona || !CAMADAS[id].prova) erros.push(id + ': camada incompleta');
    });
    return erros;
  }

  /* Frentes de um perfil; perfil desconhecido = 'geral'. */
  function pilaresDoPerfil(perfil) { return (PERFIS[perfil] || PERFIS.geral).pilares.slice(); }

  /* Pode aparecer? Em produção, só com revisão técnica aprovada dos pesos e das faixas. */
  function publicavel(ambiente) { return ambiente !== 'producao' || REVISAO.status === 'aprovada'; }

  return { PERGUNTAS: PERGUNTAS, FAIXAS: FAIXAS, RESPOSTAS: RESPOSTAS, PILARES: PILARES, REVISAO: REVISAO, REGRA: REGRA, PERFIS: PERFIS, PAGINA_PUBLICO: PAGINA_PUBLICO,
    avaliar: avaliar, faixa: faixa, validar: validar, publicavel: publicavel, pilaresDoPerfil: pilaresDoPerfil,
    perguntaVale: perguntaVale, regraDe: regraDe, CAMADAS: CAMADAS, evidencia: evidencia, planoDeAcao: planoDeAcao,
    PESOS_PERFIL: PESOS_PERFIL, pesoDe: pesoDe };
});
