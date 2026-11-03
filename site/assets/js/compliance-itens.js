/* Conteúdo da área de Compliance como dados (docs/plano-area-compliance.md). Mesmo formato de
   reforma-itens.js, validado e renderizado por conteudo.js, com dois campos a mais:
   - pilar: tributario | pld | lgpd | integridade (substitui `tributos` quando o item não é tributo);
   - prazo (opcional, AAAA-MM-DD): data que pede atenção; alimenta "Datas que pedem atenção";
   - pergunta (opcional): vira pergunta frequente da página; a resposta é o próprio `fato`, com fonte e status.
   Itens da reforma que também valem aqui (conformidade-2026, documentos-fiscais) NÃO são copiados:
   ganham o destino 'compliance-tributario' em reforma-itens.js.

   Regra: `fato` só com o que está na fonte citada (conferida em 01/11/2026 no texto literal; ver fontes.js).
   Fonte não conferida aparece com o selo "pendente de validação". Em produção, só itens com revisão
   técnica aprovada vão para a tela. Destino 'compliance' = aparece também na visão geral da área. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).complianceItens = factory();
})(this, function () {
  'use strict';
  var REF = '2026-11-01';
  var PENDENTE = { status: 'pendente', por: null, em: null };
  function item(o) {
    o.consultadoEm = o.consultadoEm || REF;
    o.revisao = o.revisao || PENDENTE;
    o.historico = o.historico || [];
    o.tributos = o.tributos || [];
    return o;
  }

  return [
    // ---------- Conformidade tributária
    item({ id: 'programas-conformidade-receita', pergunta: 'O que são o Confia, o Sintonia e o OEA?', pilar: 'tributario', titulo: 'Programas de conformidade da Receita Federal: Confia, Sintonia e OEA',
      setores: ['todos'],
      fato: 'A LC nº 225/2026 (Código de Defesa do Contribuinte) institui, no âmbito da Receita Federal, o Programa de Conformidade Cooperativa Fiscal (Confia), o Programa de Estímulo à Conformidade Tributária (Sintonia) e o Programa Brasileiro de Operador Econômico Autorizado (Programa OEA). A adesão ao Confia é voluntária.',
      orientacao: 'A adesão ao Confia segue critérios quantitativos e qualitativos da IN RFB nº 2.295/2025, e as vagas de cada edição são definidas por portaria. Segundo a Receita Federal, a primeira edição foi voltada a grandes empresas, com adesão até 20/03/2026. Para a maior parte das empresas, o ponto prático é manter as obrigações acessórias em dia.',
      status: 'em_vigor', fontes: ['lc225_2026', 'in_rfb_2295_2025', 'agenciagov_confia_2026'], destinos: ['compliance', 'compliance-tributario', 'publico-comercio', 'publico-servicos'] }),
    item({ id: 'produtor-cnpj-documento-2027', pergunta: 'O produtor rural pessoa física vai precisar de CNPJ?', pilar: 'tributario', titulo: 'Produtor rural pessoa física: CNPJ e documento fiscal a partir de 2027',
      setores: ['agro'],
      fato: 'O Decreto nº 13.075/2026 alterou o regulamento da CBS (Decreto nº 12.955/2026): a inscrição no CNPJ e a emissão de documentos fiscais passam a ser obrigatórias, a partir de 01/01/2027, para o produtor rural pessoa física de que trata o art. 239, I e II, do regulamento.',
      orientacao: 'Antes da mudança, vale cruzar as notas fiscais com o livro-caixa (LCDPR) para corrigir divergências de receita ainda em 2026.',
      status: 'vigencia_futura', vigencia: '01/01/2027', prazo: '2027-01-01', fontes: ['dec13075_2026', 'dec12955_produtor'], destinos: ['compliance', 'compliance-tributario', 'publico-produtor'] }),

    // ---------- Prevenção à lavagem de dinheiro (PLD/FT)
    item({ id: 'pld-quem-e-obrigado', pergunta: 'Minha empresa é obrigada a comunicar operações ao COAF?', pilar: 'pld', titulo: 'Quem a lei obriga a prevenir a lavagem de dinheiro',
      setores: ['todos', 'agro'],
      fato: 'A Lei nº 9.613/1998 (art. 9º) sujeita às obrigações de cadastro, registro e comunicação ao COAF, entre outros: quem comercializa bens de luxo ou de alto valor ou exerce atividades com grande volume de recursos em espécie; quem comercializa bens de alto valor de origem rural ou animal ou intermedeia a sua comercialização; as empresas de factoring e as Empresas Simples de Crédito; e quem atua na promoção imobiliária ou na compra e venda de imóveis.',
      orientacao: 'No agro, a atenção maior é para quem comercializa ou intermedeia bens de alto valor de origem rural ou animal. O enquadramento depende da atividade de fato exercida e da regulamentação do órgão competente.',
      status: 'em_vigor', fontes: ['lei9613'], destinos: ['compliance', 'compliance-pld'] }),
    item({ id: 'pld-cadastro-registro', pilar: 'pld', titulo: 'Cadastro de clientes, registro de operações e controles internos',
      setores: ['todos'],
      fato: 'As pessoas obrigadas devem identificar os clientes e manter cadastro atualizado, registrar as transações acima do limite fixado pela autoridade competente, adotar políticas, procedimentos e controles internos compatíveis com o seu porte e volume de operações e se cadastrar no órgão regulador ou, na falta dele, no COAF. Cadastros e registros devem ser guardados por, no mínimo, cinco anos.',
      status: 'em_vigor', fontes: ['lei9613'], destinos: ['compliance-pld'] }),
    item({ id: 'pld-comunicacoes', pergunta: 'Em quanto tempo uma operação suspeita deve ser comunicada ao COAF?', pilar: 'pld', titulo: 'Comunicação ao COAF em 24 horas e comunicação de não ocorrência',
      setores: ['todos'],
      fato: 'As operações que possam constituir sérios indícios dos crimes da lei devem ser comunicadas ao COAF em 24 horas, sem dar ciência a ninguém, inclusive à pessoa a que se refere a informação. Quem não tiver propostas ou operações a comunicar informa a não ocorrência ao órgão regulador ou, na falta dele, ao COAF, na periodicidade, forma e condições que eles estabelecerem.',
      status: 'em_vigor', fontes: ['lei9613'], destinos: ['compliance-pld'] }),
    item({ id: 'pld-sancoes', pergunta: 'Quais são as penalidades para quem não cumpre as regras de prevenção?', pilar: 'pld', titulo: 'Sanções por descumprir as obrigações de prevenção',
      setores: ['todos'],
      fato: 'Quem deixa de cumprir as obrigações de cadastro, registro e comunicação está sujeito a advertência; multa de até o dobro do valor da operação, até o dobro do lucro obtido com ela ou até R$ 20 milhões; inabilitação de administradores por até dez anos; e cassação ou suspensão da autorização para funcionar.',
      status: 'em_vigor', fontes: ['lei9613'], destinos: ['compliance-pld'] }),
    item({ id: 'pld-profissionais-contabilidade', pergunta: 'Por que o contador pede documentos sobre a origem dos recursos?', pilar: 'pld', titulo: 'Profissionais e organizações contábeis também têm obrigações de PLD',
      setores: ['todos'],
      fato: 'A Resolução CFC nº 1.721/2024 alcança organizações e profissionais da contabilidade que prestam serviços relativos a operações como compra e venda de imóveis, estabelecimentos ou participações societárias, gestão de ativos e abertura ou gestão de contas. Eles devem manter cadastro dos contratantes, comunicar ao COAF em 24 horas as operações suspeitas e as operações em espécie acima de R$ 100 mil no mês (ainda que fracionadas) e, se não houver ocorrência no ano, enviar a comunicação de não ocorrência ao CFC até 31 de janeiro do ano seguinte. Cadastros e registros são guardados por, no mínimo, cinco anos.',
      orientacao: 'É uma obrigação do escritório, não da empresa cliente; aparece aqui porque explica por que o contador pede documentos de identificação e de origem dos recursos em algumas operações.',
      status: 'em_vigor', prazo: '2027-01-31', fontes: ['res_cfc_1721_2024', 'lei9613'], destinos: ['compliance', 'compliance-pld'] }),

    // ---------- Proteção de dados (LGPD)
    item({ id: 'lgpd-registro-seguranca', pilar: 'lgpd', titulo: 'Registro das operações e medidas de segurança',
      setores: ['todos'],
      fato: 'O controlador e o operador devem manter registro das operações de tratamento de dados pessoais que realizarem (LGPD, art. 37) e adotar medidas de segurança, técnicas e administrativas, aptas a proteger os dados de acessos não autorizados e de situações acidentais ou ilícitas de destruição, perda, alteração ou comunicação (art. 46).',
      status: 'em_vigor', fontes: ['lei13709'], destinos: ['compliance-lgpd'] }),
    item({ id: 'lgpd-encarregado', pilar: 'lgpd', titulo: 'Encarregado pelo tratamento de dados pessoais',
      setores: ['todos'],
      fato: 'O controlador deve indicar um encarregado pelo tratamento de dados pessoais (LGPD, art. 41). A ANPD pode estabelecer hipóteses de dispensa da indicação, conforme a natureza e o porte da entidade ou o volume de operações de tratamento (art. 41, § 3º).',
      status: 'em_vigor', fontes: ['lei13709'], destinos: ['compliance-lgpd'] }),
    item({ id: 'lgpd-incidente', pergunta: 'O que fazer se houver vazamento de dados pessoais?', pilar: 'lgpd', titulo: 'Comunicação de incidente de segurança',
      setores: ['todos'],
      fato: 'O controlador deve comunicar à ANPD e ao titular a ocorrência de incidente de segurança que possa acarretar risco ou dano relevante aos titulares (LGPD, art. 48).',
      status: 'em_vigor', fontes: ['lei13709'], destinos: ['compliance-lgpd'] }),
    item({ id: 'lgpd-pequeno-porte', pergunta: 'Pequena empresa precisa ter encarregado de dados (DPO)?', pilar: 'lgpd', titulo: 'Regras próprias para microempresas e empresas de pequeno porte',
      setores: ['todos'],
      fato: 'Microempresas, empresas de pequeno porte e startups podem ser agentes de tratamento de pequeno porte (Res. CD/ANPD nº 2/2022, art. 2º). Elas não são obrigadas a indicar encarregado, mas devem disponibilizar um canal de comunicação com o titular (art. 11), e podem manter o registro das operações de forma simplificada (art. 9º). O tratamento diferenciado não vale para quem realiza tratamento de alto risco ou tem receita bruta acima do limite do art. 3º, II, da LC nº 123/2006 (art. 3º), e não dispensa o cumprimento do restante da LGPD (art. 6º).',
      status: 'em_vigor', fontes: ['res_anpd_2_2022', 'lei13709'], destinos: ['compliance', 'compliance-lgpd'] }),
    item({ id: 'lgpd-sancoes', pergunta: 'Qual é a multa da LGPD?', pilar: 'lgpd', titulo: 'Sanções da LGPD',
      setores: ['todos'],
      fato: 'Entre as sanções administrativas aplicáveis pela ANPD está a multa simples de até 2% do faturamento da pessoa jurídica, grupo ou conglomerado no Brasil no último exercício, excluídos os tributos, limitada a R$ 50 milhões por infração (LGPD, art. 52, II).',
      status: 'em_vigor', fontes: ['lei13709'], destinos: ['compliance-lgpd'] }),

    // ---------- Integridade e anticorrupção
    item({ id: 'integridade-lei-anticorrupcao', pergunta: 'A empresa responde mesmo sem culpa comprovada?', pilar: 'integridade', titulo: 'Responsabilidade da empresa por atos contra a administração pública',
      setores: ['todos'],
      fato: 'A pessoa jurídica responde objetivamente, nas esferas administrativa e civil, pelos atos lesivos contra a administração pública praticados em seu interesse ou benefício (Lei nº 12.846/2013, arts. 1º e 2º). A multa vai de 0,1% a 20% do faturamento bruto do último exercício anterior ao processo administrativo, excluídos os tributos, e nunca é inferior à vantagem auferida, quando for possível estimá-la (art. 6º, I).',
      status: 'em_vigor', fontes: ['lei12846'], destinos: ['compliance-integridade'] }),
    item({ id: 'integridade-programa', pergunta: 'O que é um programa de integridade?', pilar: 'integridade', titulo: 'Programa de integridade: o que a lei considera',
      setores: ['todos'],
      fato: 'Na aplicação das sanções, conta a existência de mecanismos internos de integridade, auditoria e incentivo à denúncia de irregularidades e a aplicação efetiva de códigos de ética e de conduta (Lei nº 12.846/2013, art. 7º, VIII). O Decreto nº 11.129/2022 define o programa de integridade (art. 56) e lista 15 parâmetros de avaliação, entre eles o comprometimento da alta direção, o código de conduta, os treinamentos, a gestão de riscos, os canais de denúncia e a diligência sobre terceiros, considerando o porte da empresa, inclusive se é microempresa ou empresa de pequeno porte (art. 57).',
      status: 'em_vigor', fontes: ['lei12846', 'dec11129_2022'], destinos: ['compliance', 'compliance-integridade'] }),
    item({ id: 'integridade-contratos-publicos', pergunta: 'Quando o programa de integridade é obrigatório?', pilar: 'integridade', titulo: 'Contratos públicos de grande vulto exigem programa de integridade',
      setores: ['todos', 'transporte'],
      fato: 'Nas contratações de obras, serviços e fornecimentos de grande vulto, o edital deve exigir que o licitante vencedor implante programa de integridade em até 6 meses da celebração do contrato (Lei nº 14.133/2021, art. 25, § 4º). O Decreto nº 12.304/2024 regulamenta os parâmetros e a avaliação desses programas na administração pública federal, também para o desempate de propostas e a reabilitação de licitantes.',
      status: 'em_vigor', fontes: ['lei14133_integridade', 'dec12304_2024'], destinos: ['compliance-integridade', 'publico-transportador'] }),

    // ---------- Por público: transportador de cargas (relatório de públicos, seção 3.6; conferência de 02/11/2026)
    item({ id: 'transporte-rntrc', pergunta: 'O transportador precisa renovar o RNTRC todo ano?', pilar: 'transporte', titulo: 'Registro na ANTT (RNTRC) com revalidação anual',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'O transporte rodoviário de cargas depende de prévia inscrição do interessado em sua exploração no Registro Nacional de Transportadores Rodoviários de Cargas (RNTRC) da ANTT, com revalidação anual, nas categorias TAC (pessoa física), ETC (pessoa jurídica) e CTC (cooperativa) (Lei nº 11.442/2007, art. 2º, red. Lei nº 15.485/2026). Os requisitos de inscrição e manutenção estão na Resolução ANTT nº 5.982/2022. As infrações à lei têm multa de R$ 550,00 a R$ 10.500,00, sem prejuízo do cancelamento da inscrição (art. 21).',
      status: 'em_vigor', fontes: ['lei11442', 'antt_rntrc'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-ciot', pergunta: 'Desde quando o CIOT é obrigatório?', pilar: 'transporte', titulo: 'CIOT antes de cada operação de transporte remunerado',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'Toda operação de transporte rodoviário remunerado de cargas deve ser registrada previamente no Código Identificador da Operação de Transporte (CIOT). A emissão é responsabilidade do contratante, por meio de instituição de pagamento autorizada pelo Banco Central e habilitada pela ANTT. O descumprimento tem multa de R$ 10.500,00, sem prejuízo da indenização ao transportador, e a quitação do frete não pode passar de 30 dias úteis (Lei nº 13.703/2018, art. 7º, caput e §§ 2º, 7º e 12, red. Lei nº 15.485/2026). O registro no CIOT é obrigatório a partir de 18/09/2026 (Resolução ANTT nº 6.090/2026, art. 1º, § 1º).',
      status: 'em_vigor', fontes: ['lei13703', 'res_antt_6090'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-piso-frete', pergunta: 'É possível combinar frete abaixo do piso da ANTT?', pilar: 'transporte', titulo: 'Piso mínimo de frete é obrigatório',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'O frete do transporte rodoviário de cargas deve ser igual ou superior aos pisos mínimos, e é vedado acordo ou convenção em valor inferior (Lei nº 13.703/2018, art. 4º, caput e § 2º). Os pisos têm natureza vinculativa: quem não os observa indeniza o transportador em até 2 vezes o piso aplicável à operação, sem prejuízo das sanções cabíveis (art. 4º, § 4º), e a reincidência sujeita a multa de até R$ 1 milhão (art. 5º-E). A ANTT publica a atualização dos pisos até 20 de janeiro e 20 de julho de cada ano (art. 5º, § 3º-A, red. Lei nº 15.485/2026).',
      status: 'em_vigor', fontes: ['lei13703'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-pagamento-tac', pilar: 'transporte', titulo: 'Frete do autônomo (TAC) pago em conta e informado no DT-e',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'O frete pago ao transportador autônomo (TAC) é depositado em conta de depósito ou conta de pagamento pré-paga de livre escolha do TAC e informado no Documento Eletrônico de Transporte (DT-e); é vedado pagar por outro meio, e as tarifas e custos da operação de pagamento ficam com quem paga, sem ônus ao TAC (Lei nº 11.442/2007, art. 5º-A, caput e §§ 6º e 7º). Contratante, subcontratante e proprietário da carga, entre outros, respondem solidariamente por essa obrigação (art. 5º-A, § 2º).',
      status: 'em_vigor', fontes: ['lei11442'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-vale-pedagio', pergunta: 'Quem paga o pedágio do caminhão contratado?', pilar: 'transporte', titulo: 'Vale-pedágio antecipado pelo embarcador',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'O embarcador antecipa o vale-pedágio obrigatório ao transportador, independentemente do valor do frete (Lei nº 10.209/2001, art. 3º), e a antecipação é consignada no DT-e (art. 3º, § 2º). A empresa transportadora que subcontrata transportador autônomo é equiparada ao embarcador (art. 1º, § 3º, II). O descumprimento tem multa de R$ 550,00 a R$ 10.500,00 (art. 5º), e o embarcador indeniza o transportador em duas vezes o valor do frete (art. 8º), dispositivo que o STF declarou constitucional na ADI 6031.',
      status: 'em_vigor', fontes: ['lei10209', 'stf_adi6031'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-jornada-motorista', pergunta: 'O tempo de espera do motorista conta como jornada?', pilar: 'transporte', titulo: 'Jornada e descanso do motorista empregado',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'A jornada diária do motorista profissional empregado é de 8 horas, prorrogável por até 2 horas extras ou, por convenção ou acordo coletivo, por até 4, com 11 horas de descanso a cada 24 horas (CLT, art. 235-C, caput e § 3º). Na ADI 5322 (2023), o STF declarou inconstitucionais, entre outros pontos, o fracionamento desse descanso, a regra que excluía o tempo de espera da jornada e das horas extras e a indenização de 30% do tempo de espera (§ 9º), com efeitos a partir da publicação da ata do julgamento de mérito.',
      status: 'em_vigor', fontes: ['clt_motorista', 'stf_adi5322'], destinos: ['publico-transportador'] }),
    item({ id: 'transporte-exame-toxicologico', pilar: 'transporte', titulo: 'Exame toxicológico dos motoristas das categorias C, D e E',
      setores: ['transporte'], consultadoEm: '2026-11-02',
      fato: 'Os condutores das categorias C, D e E comprovam resultado negativo em exame toxicológico, com janela de detecção mínima de 90 dias, para obter e renovar a CNH, e os menores de 70 anos repetem o exame a cada 2 anos e 6 meses (CTB, art. 148-A, caput e §§ 1º e 2º). O motorista empregado deve se submeter ao exame e ao programa de controle de uso de droga e de bebida alcoólica pelo menos uma vez a cada 2 anos e 6 meses (CLT, art. 235-B, VII).',
      status: 'em_vigor', fontes: ['ctb_148a', 'clt_motorista'], destinos: ['publico-transportador'] }),

    // ---------- Por público: produtor rural (relatório de públicos, seção 3.7; conferência de 02/11/2026)
    item({ id: 'rural-car', pergunta: 'O CAR é obrigatório para todo imóvel rural?', pilar: 'rural', titulo: 'Cadastro Ambiental Rural (CAR) obrigatório',
      setores: ['agro'], consultadoEm: '2026-11-02',
      fato: 'O Cadastro Ambiental Rural (CAR) é registro público eletrônico obrigatório para todos os imóveis rurais (Lei nº 12.651/2012, art. 29), e a inscrição é obrigatória e por prazo indeterminado para todas as propriedades e posses rurais (art. 29, § 3º, red. Lei nº 13.887/2019). As instituições financeiras só concedem crédito agrícola, em qualquer modalidade, a proprietários de imóveis rurais inscritos no CAR (art. 78-A).',
      status: 'em_vigor', fontes: ['lei12651_car'], destinos: ['publico-produtor'] }),
    item({ id: 'rural-itr', pergunta: 'ITR em atraso impede o crédito rural?', pilar: 'rural', titulo: 'ITR: declaração anual, pagamento e crédito rural',
      setores: ['agro'], consultadoEm: '2026-11-02',
      fato: 'É contribuinte do ITR o proprietário de imóvel rural, o titular do domínio útil ou o possuidor a qualquer título (Lei nº 9.393/1996, art. 4º). A declaração anual (DIAT) é entregue para cada imóvel na data fixada pela Receita Federal (art. 8º), e o imposto é pago até o último dia útil do mês fixado para a entrega (art. 12). A entrega fora do prazo tem multa de 1% ao mês ou fração sobre o imposto devido, não inferior a R$ 50,00 (arts. 7º e 9º). A concessão de incentivos fiscais e de crédito rural, em todas as modalidades, e as respectivas garantias dependem da comprovação do recolhimento do ITR dos últimos cinco exercícios, salvo exigibilidade suspensa ou execução com penhora; a comprovação é dispensada no financiamento do PRONAF (art. 20).',
      status: 'em_vigor', fontes: ['lei9393_itr'], destinos: ['publico-produtor'] }),
    item({ id: 'rural-funrural', pergunta: 'Como o produtor pessoa física escolhe entre o Funrural sobre a receita e sobre a folha?', pilar: 'rural', titulo: 'Funrural do empregador rural pessoa física e a opção pela folha',
      setores: ['agro'], consultadoEm: '2026-11-02',
      fato: 'A contribuição do empregador rural pessoa física, em substituição à contribuição sobre a folha, é de 1,2% da receita bruta da comercialização da produção mais 0,1% para o financiamento das prestações por acidente do trabalho (Lei nº 8.212/1991, art. 25, I e II). Ele pode optar pela contribuição sobre a folha de salários pagando a contribuição da folha de janeiro de cada ano, ou da primeira competência após o início da atividade rural; a opção é irretratável para todo o ano-calendário (art. 25, § 13).',
      status: 'em_vigor', fontes: ['lei8212_funrural'], destinos: ['publico-produtor'] }),
    item({ id: 'rural-nr31', pergunta: 'O que a NR-31 exige de quem tem empregados no campo?', pilar: 'rural', titulo: 'NR-31: segurança e saúde no trabalho rural',
      setores: ['agro'], consultadoEm: '2026-11-02',
      fato: 'A NR-31 se aplica a quaisquer atividades da agricultura, pecuária, silvicultura, exploração florestal e aquicultura (item 31.2.1). O empregador rural ou equiparado deve elaborar, implementar e custear o Programa de Gerenciamento de Riscos no Trabalho Rural (PGRTR) por estabelecimento rural (item 31.3.1); quem tem até 50 empregados por estabelecimento pode usar a ferramenta de avaliação de risco disponibilizada pelo governo para estruturar o programa (item 31.3.1.1), e os riscos e as medidas de prevenção devem ser comunicados aos trabalhadores (item 31.3.1.3).',
      status: 'em_vigor', fontes: ['nr31'], destinos: ['publico-produtor'] }),
    item({ id: 'rural-eudr', pergunta: 'O que muda para quem vende soja, gado, café ou madeira para a União Europeia?', pilar: 'rural', titulo: 'União Europeia: produtos livres de desmatamento (EUDR)',
      setores: ['agro'], consultadoEm: '2026-11-02',
      fato: 'O Regulamento (UE) 2023/1115 proíbe colocar no mercado da União Europeia, disponibilizar ou exportar bovinos, cacau, café, palmeira-dendém, borracha, soja e madeira, e os derivados do anexo I, que não estejam livres de desflorestação (produzidos em terras não desmatadas após 31/12/2020), que não tenham sido produzidos conforme a legislação do país de produção ou que não estejam cobertos por declaração de diligência devida (arts. 1º, 2º, ponto 13, e 3º). O operador guarda por cinco anos as informações e provas de cada produto (art. 9º). As regras valem a partir de 30/12/2026 e, para micro e pequenas empresas criadas até 31/12/2024, a partir de 30/06/2027 (art. 38, red. Regulamento (UE) 2025/2650).',
      orientacao: 'A obrigação recai sobre quem coloca o produto no mercado europeu ou exporta da União Europeia. Na prática, o comprador europeu tende a pedir ao fornecedor brasileiro os dados que provam a origem da área; o CAR e o georreferenciamento organizados ajudam a responder.',
      status: 'vigencia_futura', prazo: '2026-12-30', fontes: ['ue_eudr'], destinos: ['publico-produtor'] }),

    // ---------- Por público: MEI, autônomo e Simples (relatório de públicos, seções 3.1 a 3.3; conferência de 02/11/2026)
    item({ id: 'mei-limite-2027', pergunta: 'Qual é o limite de faturamento do MEI em 2027?', pilar: 'pequenos', titulo: 'MEI: limite de R$ 110 mil em 2027 e de R$ 140 mil a partir de 2028',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'Para o ano-calendário de 2027, o limite de receita bruta anual do MEI é de R$ 110.000,00; no ano de início de atividade, R$ 9.166,67 multiplicados pelos meses entre o início e o fim do ano (LC nº 238/2026, art. 2º). A partir de 01/01/2028, o limite passa a R$ 140.000,00, ou R$ 11.666,67 por mês no ano de início (LC nº 123/2006, art. 18-A, §§ 1º e 2º, red. LC nº 238/2026, art. 10, I). Também a partir de 2027, o MEI pode ter até 2 empregados que recebam exclusivamente 1 salário mínimo ou o piso da categoria (art. 18-C, red. LC nº 238/2026). A opção pelo SIMEI continua sendo feita em janeiro, até o último dia útil.',
      status: 'vigencia_futura', prazo: '2027-01-01', fontes: ['lc238_2026', 'cgsn_opcao'], destinos: ['publico-mei'] }),
    item({ id: 'mei-ibs-cbs-valor-fixo', pergunta: 'Como o MEI paga IBS e CBS?', pilar: 'pequenos', titulo: 'MEI: IBS e CBS dentro do valor fixo mensal',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'A opção pelo MEI importa o recolhimento do ICMS, do ISS, do IBS e da CBS em valores fixos mensais, discriminados no Anexo VII da LC nº 123/2006, somados à contribuição previdenciária (art. 18-A, § 3º, IV e V, red. LC nº 214/2025, art. 517, com efeitos a partir de 01/01/2027). Em 2027 e 2028, a parcela mensal é de R$ 0,994 de CBS e R$ 0,006 de IBS, além de R$ 1,00 de ICMS e R$ 5,00 de ISS; de 2029 a 2032, o ICMS e o ISS diminuem e o IBS aumenta; a partir de 2033, são R$ 1,00 de CBS e R$ 2,00 de IBS (Anexo VII).',
      status: 'vigencia_futura', prazo: '2027-01-01', fontes: ['lc214_mei'], destinos: ['publico-mei'] }),
    item({ id: 'mei-remissao', pergunta: 'O MEI com dívida da contribuição mensal vai ter perdão?', pilar: 'pequenos', titulo: 'MEI: remissão de débitos com a União até 13/10/2026',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'A LC nº 238/2026 concede remissão integral dos créditos da União, inscritos ou não em Dívida Ativa, até 13/10/2026, de responsabilidade de quem estava enquadrado como MEI, referentes à contribuição previdenciária do valor fixo mensal e às obrigações acessórias ligadas a ela, inclusive parcelados (art. 5º e § 1º). A remissão não dá direito a restituir o que já foi pago (§ 3º). Como contrapartida, o beneficiário mantém em dia essa contribuição com vencimento nos 6 meses seguintes à entrada em vigor da lei, sob pena de cancelamento (§ 4º). A baixa depende de requerimento, com desistência de ações judiciais sobre os mesmos débitos, e um ato da PGFN vai disciplinar o procedimento (arts. 6º e 9º). Esses dispositivos produzem efeitos a partir de 01/01/2027 (art. 10, II).',
      status: 'pendente_regulamentacao', fontes: ['lc238_2026'], destinos: ['publico-mei'] }),
    item({ id: 'pf-contribuinte', pergunta: 'Autônomo pessoa física precisa pagar IBS e CBS?', pilar: 'pequenos', titulo: 'Pessoa física: quando passa a ser contribuinte de IBS e CBS',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'É contribuinte de IBS e CBS o fornecedor que realiza operações no desenvolvimento de atividade econômica, de modo habitual ou em volume que caracterize atividade econômica, ou de forma profissional, ainda que a profissão não seja regulamentada, e ele é obrigado a se inscrever nos cadastros do IBS e da CBS (LC nº 214/2025, art. 21, I e § 1º). Não é contribuinte o nanoempreendedor: a pessoa física com receita bruta inferior a 50% do limite do MEI que não tenha aderido ao MEI (art. 26, IV); ele pode optar pelo regime regular (art. 26, § 1º, II). Para motorista de transporte individual de passageiros e entregador, inclusive por aplicativo, conta como receita bruta 25% do valor bruto mensal recebido (art. 26, § 10). Compras e vendas de bens e serviços que não são da atividade seguem as regras de quem não é contribuinte (art. 4º, § 6º).',
      orientacao: 'Com os limites do MEI da LC nº 238/2026, metade do limite corresponde a R$ 55.000,00 em 2027 e a R$ 70.000,00 a partir de 2028. A conta e o enquadramento de cada caso dependem da receita do ano; o escritório confere com você.',
      status: 'em_vigor', fontes: ['lc214_pf'], destinos: ['publico-autonomo', 'publico-mei', 'publico-imoveis'] }),
    item({ id: 'profissoes-reducao-30', pergunta: 'Quais profissões têm redução de 30% no IBS e na CBS?', pilar: 'pequenos', titulo: 'Redução de 30% para profissões fiscalizadas por conselho',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'As alíquotas de IBS e CBS ficam reduzidas em 30% nos serviços de 18 profissões de natureza científica, literária ou artística submetidas à fiscalização por conselho profissional, entre elas administradores, advogados, arquitetos, contabilistas, economistas, engenheiros e agrônomos, médicos veterinários, químicos e técnicos agrícolas (LC nº 214/2025, art. 127). Para a pessoa física, o serviço precisa estar ligado à habilitação; para a sociedade, há requisitos cumulativos, como sócios habilitados, nenhum sócio pessoa jurídica e serviços prestados diretamente pelos sócios (§ 1º).',
      status: 'em_vigor', fontes: ['lc214_art127'], destinos: ['publico-autonomo', 'publico-servicos'] }),
    item({ id: 'simples-janela-opcao', pergunta: 'Quando o Simples pode escolher pagar IBS e CBS fora do DAS?', pilar: 'pequenos', titulo: 'Simples Nacional: janelas de setembro e março para o IBS e a CBS',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'O optante pelo Simples pode apurar e recolher o IBS e a CBS pelo regime regular; a opção vale para os semestres iniciados em janeiro e julho, é irretratável em cada semestre e é feita nos meses de setembro e março imediatamente anteriores, na forma do CGSN (LC nº 123/2006, art. 13, §§ 9º e 10, red. LC nº 227/2026). Para 2027, o CGSN abriu a opção em setembro de 2026, com efeitos de janeiro a junho; quem não optou recolhe os dois tributos no DAS no 1º semestre e tem nova oportunidade em março de 2027, para o 2º semestre.',
      status: 'em_vigor', fontes: ['lc214_art41', 'cgsn_opcao'], destinos: ['publico-simples'] }),
    item({ id: 'simples-locacao-imoveis', pergunta: 'Empresa que aluga imóveis próprios pode ficar no Simples?', pilar: 'pequenos', titulo: 'Locação de imóveis próprios impede o Simples Nacional',
      setores: ['todos'], tributos: [], consultadoEm: '2026-11-02',
      fato: 'Não pode recolher pelo Simples Nacional a microempresa ou empresa de pequeno porte que realize atividade de locação de imóveis próprios (LC nº 123/2006, art. 17, XV, red. LC nº 214/2025, art. 516, com efeitos desde 01/01/2025).',
      status: 'em_vigor', fontes: ['lc214_art516'], destinos: ['publico-simples', 'publico-imoveis'] }),

    // ---------- Por público: comércio e indústria; prestadores de serviço (relatório de públicos, seções 3.4 e 3.5; conferência de 02/11/2026)
    item({ id: 'servicos-reducao-60', pergunta: 'Serviços de saúde e de educação têm redução de IBS e CBS?', pilar: 'tributario', titulo: 'Saúde e educação: redução de 60% para os serviços dos anexos',
      setores: ['todos'], tributos: ['cbs', 'ibs'], consultadoEm: '2026-11-02',
      fato: 'Ficam reduzidas em 60% as alíquotas de IBS e CBS sobre os serviços de educação relacionados no Anexo II da LC nº 214/2025 e sobre os serviços de saúde do Anexo III, com a classificação de cada um na NBS (arts. 128, 129 e 130). Na educação, a redução vale só para a contraprestação dos serviços listados, não para outras operações da escola (art. 129, parágrafo único); na saúde, os valores glosados pela auditoria médica dos planos de saúde e não pagos ficam fora da base de cálculo (art. 130, parágrafo único). O art. 128 também prevê a redução de 60% para dispositivos médicos, medicamentos, alimentos, produções artísticas e culturais e atividades desportivas, entre outros.',
      status: 'em_vigor', fontes: ['lc214_saude', 'lc214_educacao'], destinos: ['publico-servicos'] }),
    item({ id: 'comercio-saldo-icms', pergunta: 'O que acontece com o saldo credor de ICMS quando o imposto acabar?', pilar: 'tributario', titulo: 'Saldos credores de ICMS ao fim de 2032: compensação com o IBS',
      setores: ['todos'], tributos: ['icms', 'ibs'], consultadoEm: '2026-11-02',
      fato: 'Os saldos credores de ICMS existentes ao final de 2032 serão aproveitados na forma de lei complementar, desde que o aproveitamento ou ressarcimento seja admitido pela legislação em vigor em 31/12/2032 e que tenham sido homologados pelo estado; sem resposta no prazo da lei complementar, consideram-se homologados (ADCT, art. 134, caput e § 1º). O saldo homologado é compensado com o IBS: os créditos de entrada de bens do ativo permanente, pelo prazo remanescente; os demais, em 240 parcelas mensais, iguais e sucessivas (§ 3º), atualizadas pelo IPCA a partir de 2033 (§ 5º).',
      orientacao: 'Até lá, a empresa que acumula crédito de ICMS (exportação, diferença de alíquota, substituição tributária) ganha em manter o saldo conciliado com a escrituração: só entra na compensação o que for admitido pela legislação e homologado pelo estado. A substituição tributária do ICMS segue as regras de cada estado até a extinção do imposto.',
      status: 'vigencia_futura', fontes: ['adct_134_135'], destinos: ['publico-comercio'] }),

    // ---------- Por público: pessoa física com imóveis (relatório de públicos, seção 3.8; conferência de 02/11/2026)
    item({ id: 'imoveis-pf-contribuinte', pergunta: 'Quem aluga ou vende imóveis como pessoa física vai pagar IBS e CBS?', pilar: 'imoveis', titulo: 'Pessoa física com imóveis: quando passa a ser contribuinte',
      setores: ['todos'], tributos: ['cbs', 'ibs'], consultadoEm: '2026-11-02',
      fato: 'A pessoa física passa a ser contribuinte do regime regular de IBS e CBS nas operações com imóveis quando, no ano-calendário anterior: (I) a receita com locação, cessão onerosa e arrendamento passou de R$ 240.000,00 e envolveu mais de 3 imóveis distintos; (II) vendeu ou cedeu direitos de mais de 3 imóveis distintos que estavam no patrimônio havia menos de 5 anos; ou (III) vendeu mais de 1 imóvel construído por ela nos 5 anos anteriores (LC nº 214/2025, art. 251, §§ 1º e 3º). Também é contribuinte no próprio ano quem passa dos limites de venda ou excede em 20% o limite de receita da locação (§ 2º). Os R$ 240.000,00 são atualizados mensalmente pelo IPCA (§ 5º), e o regulamento define o que são imóveis distintos (§ 6º). A locação residencial por até 90 dias ininterruptos segue as regras da hotelaria e entra nesses limites (art. 253, red. LC nº 227/2026).',
      orientacao: 'Herança, doação e meação não zeram o prazo de 5 anos: ele conta desde a aquisição pelo falecido, pelo doador ou pelo cônjuge (art. 251, § 4º). Quem passa a contribuinte apura IBS e CBS sobre os aluguéis e as vendas; o restante da vida da pessoa física continua fora da regra (art. 4º, § 6º).',
      status: 'em_vigor', fontes: ['lc214_imoveis'], destinos: ['publico-imoveis'] }),
    item({ id: 'imoveis-reducoes', pergunta: 'Qual é o IBS e a CBS no aluguel e na venda de imóveis?', pilar: 'imoveis', titulo: 'Imóveis: reduções de 50% e 70% e os redutores sociais',
      setores: ['todos'], tributos: ['cbs', 'ibs'], consultadoEm: '2026-11-02',
      fato: 'Nas operações com imóveis, as alíquotas de IBS e CBS são reduzidas em 50%; na locação, cessão onerosa e arrendamento, em 70% (LC nº 214/2025, art. 261). Na locação para uso residencial, o contribuinte deduz da base um redutor social de R$ 600,00 por mês por imóvel (art. 260, red. LC nº 227/2026); na venda de imóvel residencial novo ou de lote residencial, o redutor social é de R$ 100.000,00 por imóvel novo e de R$ 30.000,00 por lote, usado uma vez por imóvel (art. 259). Os dois valores são atualizados pelo IPCA. Na locação, o IBS e a CBS são devidos no momento do pagamento (art. 254, III).',
      status: 'em_vigor', fontes: ['lc214_imoveis'], destinos: ['publico-imoveis'] })
  ];
});
