/* Registro único de fontes legais citadas no site.
   validado: true  → dispositivo conferido em fonte primária (data em `conferido`).
   validado: false → exibido com o selo "pendente de validação" até o responsável técnico conferir.
   Para validar um item: confira o dispositivo, ajuste `rotulo`, marque `validado: true` e preencha `conferido`.
   Conferência de 30/10/2026 feita nos textos compilados do Planalto (LC 214/2025 já com a LC 227/2026)
   e no portal de normas da RFB. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).fontes = factory();
})(this, function () {
  'use strict';
  var P = 'https://www.planalto.gov.br/ccivil_03/';
  var LC214 = P + 'leis/lcp/lcp214.htm';
  var EC132 = P + 'constituicao/emendas/emc/emc132.htm';
  var CF = P + 'constituicao/constituicao.htm';
  var LC123 = P + 'leis/lcp/lcp123.htm';
  var RFB = 'https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/';
  var OK = '2026-10-30';
  var HOJE = '2026-10-31';

  var lista = [
    // Reforma tributária
    { id: 'adct_125_133', rotulo: 'ADCT, arts. 125 a 129 (EC nº 132/2023) e EC nº 132/2023, art. 22', url: CF, validado: true, conferido: OK },
    { id: 'lc214_2026', rotulo: 'LC nº 214/2025, arts. 343, 346 e 348 (2026: compensação e dispensa; não se aplica ao Simples)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_art41', rotulo: 'LC nº 214/2025, art. 41, §§ 3º e 4º; LC nº 123/2006, art. 13, §§ 9º a 11 (incluídos pelo art. 517 da LC 214, red. LC nº 227/2026)', url: LC214, validado: true, conferido: OK },
    { id: 'cgsn_opcao', rotulo: 'Resolução CGSN nº 186/2026, segundo a notícia oficial do Portal do Simples Nacional de 17/04/2026 (opção para 2027 em setembro de 2026, nova chance em março de 2027; SIMEI segue com opção em janeiro). Prorrogação posterior (Res. CGSN nº 194/2026) não conferida', url: 'https://www8.receita.fazenda.gov.br/simplesnacional/noticias/NoticiaCompleta.aspx?id=c739e03c-8482-473f-8e82-f38ec3b13637', validado: true, conferido: '2026-11-02' },
    { id: 'lc214_credito_simples', rotulo: 'LC nº 214/2025, art. 47, § 9º, II', url: LC214, validado: true, conferido: OK },
    { id: 'cf_146_simples', rotulo: 'CF, art. 146, § 2º e § 3º, II', url: CF, validado: true, conferido: OK },
    { id: 'lc214_nao_cumulatividade', rotulo: 'LC nº 214/2025, art. 47 e seguintes (não cumulatividade)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_base_calculo', rotulo: 'LC nº 214/2025, art. 12, § 2º, I (IBS e CBS fora da própria base)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_split', rotulo: 'LC nº 214/2025, arts. 31 a 35 (split payment; implantação gradual: art. 35, § 2º)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_cashback', rotulo: 'LC nº 214/2025, arts. 112 a 124 (público no art. 113; percentuais no art. 118)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_art127', rotulo: 'LC nº 214/2025, art. 127 (redução de 30%; requisitos da PJ no § 1º, II)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_saude', rotulo: 'LC nº 214/2025, arts. 128 e 130 e Anexo III (saúde, redução de 60%)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_educacao', rotulo: 'LC nº 214/2025, arts. 128 e 129 e Anexo II (educação, redução de 60%)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_agro', rotulo: 'LC nº 214/2025, arts. 137 e 138 e Anexo IX (agropecuários in natura e insumos, redução de 60%)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_cesta', rotulo: 'LC nº 214/2025, art. 125 e Anexo I (cesta básica); art. 148 e Anexo XV (hortícolas, frutas e ovos: alíquota zero)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_produtor_nc', rotulo: 'LC nº 214/2025, arts. 164 e 167 (produtor não contribuinte; limite corrigido pelo IPCA)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_credito_presumido', rotulo: 'LC nº 214/2025, art. 168 (crédito presumido; efeitos a partir de 01/01/2027 — art. 544, III, red. LC 227/2026)', url: LC214, validado: true, conferido: OK },
    { id: 'lc214_is', rotulo: 'LC nº 214/2025, arts. 409 a 438 (lista no art. 409, § 1º; minerais: teto de 0,25% no art. 422, § 2º, red. LC 227/2026)', url: LC214, validado: true, conferido: OK },
    { id: 'cf_153_is', rotulo: 'CF, art. 153, VIII, e § 6º, VII (na extração, cobrado independentemente da destinação; máximo de 1%)', url: CF, validado: true, conferido: OK },
    { id: 'lc214_zfm', rotulo: 'LC nº 214/2025, arts. 439 a 457 (ZFM) e 458 a 470 (ALC; lista no art. 459)', url: LC214, validado: true, conferido: OK },
    { id: 'is_lei_ordinaria', rotulo: 'Lei ordinária que fixa as alíquotas do Imposto Seletivo', url: null, validado: false },
    { id: 'adct_92b', rotulo: 'ADCT, arts. 92-A e 92-B (prazo e diferencial competitivo da ZFM e das ALC)', url: CF, validado: true, conferido: OK },
    { id: 'cf_156a_destino', rotulo: 'CF, art. 156-A, § 1º, VII (IBS no destino)', url: CF, validado: true, conferido: OK },
    { id: 'adct_12_fundo', rotulo: 'EC nº 132/2023, art. 12 (Fundo de Compensação de Benefícios Fiscais, 2029 a 2032)', url: EC132, validado: true, conferido: OK },
    { id: 'adct_136', rotulo: 'ADCT, art. 136 (contribuições estaduais existentes em 30/04/2023; extinção em 31/12/2043)', url: CF, validado: true, conferido: OK },
    // Conferência de 31/10/2026 (Planalto: CF/ADCT compilados e LC 214/2025 compilada)
    { id: 'adct_126', rotulo: 'ADCT, art. 126 (2027: cobrança da CBS e do Imposto Seletivo; extinção do PIS e da Cofins; IPI com alíquota zero, exceto industrialização incentivada na ZFM)', url: CF, validado: true, conferido: HOJE },
    { id: 'adct_127', rotulo: 'ADCT, art. 127 (2027 e 2028: IBS a 0,05% estadual e 0,05% municipal; CBS reduzida em 0,1 ponto percentual)', url: CF, validado: true, conferido: HOJE },
    { id: 'adct_128_129', rotulo: 'ADCT, arts. 128 e 129 (ICMS e ISS a 9/10, 8/10, 7/10 e 6/10 de 2029 a 2032; extinção em 2033)', url: CF, validado: true, conferido: HOJE },
    { id: 'adct_130', rotulo: 'ADCT, art. 130 (alíquotas de referência de IBS e CBS fixadas por resolução do Senado, no ano anterior, com cálculo do TCU)', url: CF, validado: true, conferido: HOJE },
    { id: 'adct_134_135', rotulo: 'ADCT, arts. 134 (saldos credores de ICMS ao fim de 2032) e 135 (créditos de IPI, PIS e Cofins não utilizados)', url: CF, validado: true, conferido: HOJE },
    { id: 'lc214_vigencia', rotulo: 'LC nº 214/2025, art. 544 (produção de efeitos: 2026 em regra; 2027 para os arts. 168 a 171 e outros; 2029 e 2033 para dispositivos listados; red. LC nº 227/2026)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_produtor_opcao', rotulo: 'LC nº 214/2025, arts. 165 e 166 (opção do produtor rural pelo regime regular, a qualquer tempo; irretratável no ano-calendário; renúncia)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_diferimento_insumos', rotulo: 'LC nº 214/2025, art. 138, § 2º (diferimento do IBS e da CBS nos insumos agropecuários do Anexo IX)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_maquinas_agro', rotulo: 'LC nº 214/2025, art. 110 (alíquota zero para tratores, máquinas e implementos destinados ao produtor rural não contribuinte e para veículos de carga destinados ao transportador autônomo não contribuinte)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_tac', rotulo: 'LC nº 214/2025, art. 169 (crédito presumido na contratação de transportador autônomo de carga pessoa física não contribuinte ou MEI; efeitos a partir de 2027, art. 544, III)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_local_operacao', rotulo: 'LC nº 214/2025, art. 11, VI e VII (local da operação: início do transporte de passageiros; entrega do bem no transporte de carga)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_transporte_urbano', rotulo: 'LC nº 214/2025, art. 157 (isenção do transporte público coletivo rodoviário e metroviário urbano, semiurbano e metropolitano)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_transporte_passageiros', rotulo: 'LC nº 214/2025, arts. 284 a 287 (regime específico: passageiros intermunicipal e interestadual com redução de 40% e crédito permitido; ferroviário e hidroviário urbano com redução de 100%; aéreo regional de passageiros ou carga com redução de 40%)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_combustiveis', rotulo: 'LC nº 214/2025, arts. 172 a 180 (combustíveis: incidência única, alíquota por unidade de medida; crédito ao adquirente que não revende, art. 180, § 1º)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_regimes_especificos', rotulo: 'LC nº 214/2025, Livro I, Título V, arts. 172 a 307 (combustíveis, serviços financeiros, planos de saúde, prognósticos, imóveis, cooperativas, hotelaria, bares e restaurantes, transporte de passageiros, SAF, missões diplomáticas)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_is_veiculos', rotulo: 'LC nº 214/2025, arts. 409, § 1º, e 419, e Anexo XVII (veículos sujeitos ao Imposto Seletivo, exceto caminhões; alíquotas em lei ordinária)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc214_saldo_piscofins', rotulo: 'LC nº 214/2025, arts. 378 a 383 (saldos de PIS e Cofins: compensação com a CBS, ressarcimento ou compensação com tributos federais; crédito presumido sobre estoques em 01/01/2027)', url: LC214, validado: true, conferido: HOJE },
    { id: 'lc227', rotulo: 'LC nº 227/2026 (institui o Comitê Gestor do IBS; competência para o regulamento do IBS, art. 2º, I; altera a LC 214)', url: P + 'leis/lcp/lcp227.htm', validado: true, conferido: HOJE },
    { id: 'cgibs_regulamento', rotulo: 'Resolução CGIBS nº 6/2026 (Regulamento do IBS), alterada pela Resolução CGIBS nº 13/2026; Portaria Conjunta MF/CGIBS nº 7/2026 (parte comum). Cláusula de vigência a conferir', url: 'https://www.cgibs.gov.br/regulamentos', validado: true, conferido: HOJE },
    { id: 'dec12955_produtor', rotulo: 'Decreto nº 12.955/2026, arts. 239 a 249 (produtor rural no regulamento da CBS; art. 243: receita de 2024) e arts. 105, § 4º-A, e 115, § 3º, incluídos pelo Decreto nº 13.075/2026 (CNPJ e documento fiscal do produtor pessoa física a partir de 01/01/2027)', url: P + '_ato2023-2026/2026/decreto/D12955.htm', validado: true, conferido: HOJE },
    { id: 'tcu_cbs_2027', rotulo: 'TCU, Plenário, 28/10/2026 (TC 006.529/2026-7): alíquota de referência da CBS para 2027 calculada em 11,3468% e arredondada para 11,3%; redutor das compras públicas de 44,2%; resolução do Senado pendente; sem cálculo do IBS para 2027', url: 'https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo', validado: true, conferido: '2026-11-03' },
    { id: 'lc214_aliquota_senado', rotulo: 'LC nº 214/2025, art. 349 (Senado fixa as alíquotas de referência; se passar de 22/12 do ano anterior, valem as calculadas pelo TCU até a fixação)', url: LC214, validado: true, conferido: '2026-11-03' },
    { id: 'senado_cbs_2027', rotulo: 'Agência Senado, 03/11/2026: cálculo da CBS deve chegar ao Senado em 10/11; a notícia cita 15/12 como prazo da resolução (a LC 214, art. 349, traz outras datas)', url: 'https://www12.senado.leg.br/noticias/materias/2026/11/03/senado-deve-receber-calculo-da-cbs-na-proxima-terca-para-definir-aliquota', validado: true, conferido: '2026-11-03' },
    { id: 'ato_conjunto_1_2025', rotulo: 'Ato Conjunto RFB/CGIBS nº 1/2025, arts. 2º e 3º (documentos aceitos, inclusive CT-e e MDF-e; apuração de 2026 meramente informativa se cumpridas as obrigações acessórias)', url: 'https://www.cgibs.gov.br/upload/arquivos/202609/09104120-ato-conjunto-rfb-cgibs-n-1-de-22-de-dezembro-de-2025.pdf', validado: true, conferido: HOJE },
    { id: 'ato_conjunto_4_2026', rotulo: 'Ato Conjunto RFB/CGIBS nº 4/2026 (campos de IBS/CBS obrigatórios no CT-e, CT-e OS, MDF-e, NF-e e NFC-e desde 03/08/2026; Simples Nacional a partir de 01/01/2027)', url: 'https://www.cgibs.gov.br/atos-conjuntos', validado: true, conferido: HOJE },
    { id: 'ato_conjunto_5_2026', rotulo: 'Ato Conjunto RFB/CGIBS nº 5/2026 (Programa Nacional de Conformidade Tributária de 2026; LC 214, arts. 471-A a 471-C)', url: 'https://www.cgibs.gov.br/upload/arquivos/202608/13065932-ato-conjunto-rfb-cgibs-n-c2-ba-5-2026-regulamenta-o-programa-nacional-de-conformidade-tributaria-docx-assinado.pdf', validado: true, conferido: HOJE },
    { id: 'cgibs_split_atos', rotulo: 'Ato Conjunto RFB/CGIBS nº 2/2026 e Atos Técnicos Conjuntos nº 4 e nº 5/2026 (manuais técnicos do split payment; sem cronograma de obrigatoriedade); Decreto nº 12.955/2026, art. 33 (etapas)', url: 'https://www.cgibs.gov.br/atos-tecnicos-conjuntos', validado: true, conferido: HOJE },
    { id: 'senado_is_mp', rotulo: 'Agência Senado, 29/10/2026: alíquotas do Imposto Seletivo devem sair por medida provisória (publicação não confirmada até 31/10/2026)', url: 'https://www12.senado.leg.br/noticias/audios/2026/10/imposto-seletivo-governo-define-aliquotas-nos-proximos-dias', validado: true, conferido: HOJE },
    { id: 'rfb_lcdpr', rotulo: 'LCDPR: IN SRF nº 83/2001, art. 23-A (incluído pela IN RFB nº 1.848/2018); obrigação acima de R$ 4,8 milhões de receita bruta rural, segundo o manual "IRPF – Atividade Rural" e a notícia Declara Agro da Receita (28/10/2026). Texto vigente da IN não conferido', url: 'https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/orientacao-tributaria/irpf-atividade-rural.pdf', validado: false },
    { id: 'cfg_aliquota_ref', rotulo: 'Alíquota de referência IBS + CBS: estimativa (NT SERT/MF de 01/07/2024: 26,47%; +1,47 p.p. na NT de 23/08/2024). Avaliação: LC 214, art. 475, §§ 9º a 11', url: LC214, validado: false },
    // Compliance (docs/plano-area-compliance.md). Conferência de 01/11/2026 no texto literal das páginas oficiais
    // (Planalto, ANPD e o DOU de 06/05/2024 para a Res. CFC 1.721/2024). Alterações posteriores não verificadas,
    // salvo onde indicado. Pendentes: a IN do Confia (portal de normas da RFB não abriu) e a notícia da Agência Gov.
    { id: 'lc225_2026', rotulo: 'LC nº 225/2026 (Código de Defesa do Contribuinte, de 08/01/2026), arts. 18 e 19 (institui o Confia, o Sintonia e o Programa OEA; adesão voluntária ao Confia)', url: P + 'leis/lcp/lcp225.htm', validado: true, conferido: '2026-11-01' },
    { id: 'in_rfb_2295_2025', rotulo: 'IN RFB nº 2.295/2025 (Confia; DOU de 08/12/2025), alterada pelas INs RFB nº 2.317/2026 e nº 2.328/2026: arts. 7º a 9º (critérios quantitativos e qualitativos), 12 (vagas por portaria a cada edição) e 21 (admissão por ato da Comac). Lida em cópia não oficial (LegisWeb); DOU não conferido', url: 'https://www.legisweb.com.br/legislacao/?id=487374', validado: false },
    { id: 'agenciagov_confia_2026', rotulo: 'Agência Gov, 19/02/2026: Portaria RFB nº 650/2026 prorroga para 20/03/2026 a adesão à 1ª edição do Confia, voltada a grandes empresas', url: 'https://agenciagov.ebc.com.br/noticias/202602/receita-federal-prorroga-20-marco-adesao-programa-confia', validado: false },
    { id: 'dec13075_2026', rotulo: 'Decreto nº 13.075/2026, que altera o Decreto nº 12.955/2026: art. 105, § 4º-A (CNPJ) e art. 115, § 3º (documentos fiscais), a partir de 01/01/2027 para o produtor rural pessoa física do art. 239, I e II', url: P + '_ato2023-2026/2026/decreto/D13075.htm', validado: true, conferido: '2026-11-01' },
    { id: 'lei9613', rotulo: 'Lei nº 9.613/1998, arts. 9º a 12 (pessoas obrigadas, cadastro e registros por 5 anos, comunicação ao COAF em 24 horas, sanções)', url: P + 'leis/l9613.htm', validado: true, conferido: '2026-11-01' },
    { id: 'res_cfc_1721_2024', rotulo: 'Resolução CFC nº 1.721/2024 (DOU de 06/05/2024; vigência em 03/06/2024; revogou a Res. CFC nº 1.530/2017), arts. 2º, 3º, 6º, 7º e 10', url: 'https://www.gov.br/coaf/pt-br/assuntos/informacoes-as-pessoas-obrigadas/orgaos-reguladores-e-fiscalizadores/resolucao-cfc-no-1-721-de-18-de-abril-de-2024-1.pdf/@@display-file/file', validado: true, conferido: '2026-11-01' },
    { id: 'lei13709', rotulo: 'Lei nº 13.709/2018 (LGPD), arts. 37, 41, 46, 48 e 52', url: P + '_ato2015-2018/2018/lei/l13709.htm', validado: true, conferido: '2026-11-01' },
    { id: 'res_anpd_2_2022', rotulo: 'Resolução CD/ANPD nº 2/2022 (agentes de tratamento de pequeno porte; alterada pela Res. CD/ANPD nº 15/2024), arts. 2º, 3º, 4º, 6º, 9º, 11 e 14; texto no site da ANPD, DOU não conferido', url: 'https://www.gov.br/anpd/pt-br/documentos-e-publicacoes/regulamentacoes-da-anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022', validado: true, conferido: '2026-11-01' },
    { id: 'lei12846', rotulo: 'Lei nº 12.846/2013 (Lei Anticorrupção), arts. 1º, 2º, 6º, I, e 7º, VIII', url: P + '_ato2011-2014/2013/lei/l12846.htm', validado: true, conferido: '2026-11-01' },
    { id: 'dec11129_2022', rotulo: 'Decreto nº 11.129/2022, arts. 56 e 57 (programa de integridade e os 15 parâmetros de avaliação; porte e ME/EPP no § 1º)', url: P + '_ato2019-2022/2022/decreto/D11129.htm', validado: true, conferido: '2026-11-01' },
    { id: 'lei14133_integridade', rotulo: 'Lei nº 14.133/2021, art. 25, § 4º (programa de integridade em contratações de grande vulto, em até 6 meses da celebração do contrato)', url: P + '_ato2019-2022/2021/lei/l14133.htm', validado: true, conferido: '2026-11-01' },
    { id: 'dec12304_2024', rotulo: 'Decreto nº 12.304/2024 (parâmetros e avaliação dos programas de integridade nas contratações da administração pública federal: grande vulto, desempate e reabilitação)', url: P + '_ato2023-2026/2024/decreto/D12304.htm', validado: true, conferido: '2026-11-01' },
    // Compliance por público: transportador (docs/relatorio-publicos-reforma-compliance.md, seção 3.6). Conferência de 02/11/2026
    // no texto literal do Planalto, do ANTTLegis e das páginas de processo do STF (redação mais recente marcada na página)
    { id: 'lei11442', rotulo: 'Lei nº 11.442/2007, arts. 2º (RNTRC com revalidação anual, red. Lei nº 15.485/2026), 5º-A (pagamento do frete ao TAC, red. Lei nº 14.206/2021) e 21 (multas)', url: P + '_ato2007-2010/2007/lei/l11442.htm', validado: true, conferido: '2026-11-02' },
    { id: 'antt_rntrc', rotulo: 'ANTT, página do RNTRC (requisitos de inscrição e manutenção na Resolução ANTT nº 5.982/2022)', url: 'https://www.gov.br/antt/pt-br/assuntos/cargas/rntrc-1', validado: true, conferido: '2026-11-02' },
    { id: 'lei13703', rotulo: 'Lei nº 13.703/2018, arts. 4º e 5º (pisos mínimos de frete) e 7º (CIOT), red. Lei nº 15.485/2026', url: P + '_ato2015-2018/2018/lei/l13703.htm', validado: true, conferido: '2026-11-02' },
    { id: 'res_antt_6090', rotulo: 'Resolução ANTT nº 6.090/2026, art. 1º, § 1º (registro da operação no CIOT obrigatório a partir de 18/09/2026)', url: 'https://anttlegis.antt.gov.br/action/ActionDatalegis.php?acao=abrirTextoAto&tipo=RES&numeroAto=00006090&seqAto=000&valorAno=2026&orgao=DG/ANTT/MT&cod_modulo=623&cod_menu=9230', validado: true, conferido: '2026-11-02' },
    { id: 'lei10209', rotulo: 'Lei nº 10.209/2001, arts. 1º, 3º, 5º e 8º (vale-pedágio obrigatório)', url: P + 'leis/leis_2001/l10209.htm', validado: true, conferido: '2026-11-02' },
    { id: 'stf_adi6031', rotulo: 'STF, ADI 6031 (art. 8º da Lei nº 10.209/2001 declarado constitucional; Plenário, sessão virtual de 20 a 26/03/2020; embargos rejeitados em 2020)', url: 'https://portal.stf.jus.br/processos/detalhe.asp?incidente=5564645', validado: true, conferido: '2026-11-02' },
    { id: 'clt_motorista', rotulo: 'CLT, arts. 235-B, VII, e 235-C (motorista profissional empregado, red. Lei nº 13.103/2015)', url: P + 'decreto-lei/del5452.htm', validado: true, conferido: '2026-11-02' },
    { id: 'stf_adi5322', rotulo: 'STF, ADI 5322 (partes da Lei nº 13.103/2015 declaradas inconstitucionais; Plenário, sessão virtual de 23 a 30/06/2023; efeitos a partir da ata do julgamento de mérito, embargos de 2024)', url: 'https://portal.stf.jus.br/processos/detalhe.asp?incidente=4778925', validado: true, conferido: '2026-11-02' },
    // Compliance por público: produtor rural (relatório de públicos, seção 3.7). Conferência de 02/11/2026 no Planalto,
    // no PDF oficial da NR-31 (gov.br/trabalho-e-emprego) e na versão consolidada do EUR-Lex de 18/09/2026
    { id: 'lei12651_car', rotulo: 'Lei nº 12.651/2012, arts. 29 (CAR obrigatório para todos os imóveis rurais, § 3º red. Lei nº 13.887/2019) e 78-A (crédito agrícola condicionado ao CAR, red. Lei nº 13.295/2016)', url: P + '_ato2011-2014/2012/lei/l12651.htm', validado: true, conferido: '2026-11-02' },
    { id: 'lei9393_itr', rotulo: 'Lei nº 9.393/1996, arts. 4º, 7º, 8º, 9º, 12 e 20 (ITR: contribuinte, declaração anual, multa por atraso, pagamento e crédito rural)', url: P + 'leis/l9393.htm', validado: true, conferido: '2026-11-02' },
    { id: 'lei8212_funrural', rotulo: 'Lei nº 8.212/1991, art. 25, I (red. Lei nº 13.606/2018), II e § 13 (contribuição do empregador rural pessoa física e opção pela folha)', url: P + 'leis/l8212cons.htm', validado: true, conferido: '2026-11-02' },
    { id: 'nr31', rotulo: 'NR-31 (red. Portaria SEPRT nº 22.677/2020; última alteração: Portaria MTE nº 342/2024), itens 31.2.1 e 31.3.1', url: 'https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/nr-31-atualizada-2024-2.pdf', validado: true, conferido: '2026-11-02' },
    { id: 'ue_eudr', rotulo: 'Regulamento (UE) 2023/1115 (produtos livres de desflorestação; versão consolidada de 18/09/2026), arts. 1º, 2º, ponto 13, 3º, 9º e 38 (datas de aplicação, red. Regulamento (UE) 2025/2650)', url: 'https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:02023R1115-20260918', validado: true, conferido: '2026-11-02' },
    // Compliance por público: MEI, autônomo e Simples (relatório de públicos, seções 3.1 a 3.3). Conferência de 02/11/2026
    // no texto integral do Planalto (lido no navegador; o WebFetch corta a LC 214 no art. 233)
    { id: 'lc214_mei', rotulo: 'LC nº 214/2025, art. 517 (LC nº 123/2006, art. 18-A, § 3º, IV e V, e Anexo VII: IBS e CBS do MEI em valores fixos) e art. 544, III (efeitos a partir de 01/01/2027, red. LC nº 227/2026)', url: LC214, validado: true, conferido: '2026-11-02' },
    { id: 'lc238_2026', rotulo: 'LC nº 238/2026 (MEI: limite de R$ 110 mil em 2027 e de R$ 140 mil a partir de 2028, até 2 empregados e remissão de débitos; arts. 1º, 2º, 5º, 6º e 10)', url: P + 'leis/lcp/lcp238.htm', validado: true, conferido: '2026-11-02' },
    { id: 'lc214_pf', rotulo: 'LC nº 214/2025, arts. 4º, § 6º, 21, I e § 1º, e 26, IV, § 1º, II, e § 10 (pessoa física contribuinte e nanoempreendedor, red. LC nº 227/2026)', url: LC214, validado: true, conferido: '2026-11-02' },
    { id: 'lc214_art516', rotulo: 'LC nº 214/2025, art. 516 (LC nº 123/2006, art. 17, XV: vedação ao Simples de quem realiza locação de imóveis próprios) e art. 544, II (efeitos desde 01/01/2025)', url: LC214, validado: true, conferido: '2026-11-02' },
    // Compliance por público: pessoa física com imóveis (relatório de públicos, seção 3.8). Conferência de 02/11/2026 no Planalto
    { id: 'lc214_imoveis', rotulo: 'LC nº 214/2025, arts. 251, 253 (red. LC nº 227/2026), 254, 259, 260 (red. LC nº 227/2026) e 261 (imóveis: pessoa física contribuinte, locação por temporada, momento da cobrança, redutores sociais e reduções de 50% e 70%)', url: LC214, validado: true, conferido: '2026-11-02' },
    { id: 'ctb_148a', rotulo: 'Código de Trânsito Brasileiro (Lei nº 9.503/1997), art. 148-A (exame toxicológico das categorias C, D e E)', url: P + 'leis/l9503compilado.htm', validado: true, conferido: '2026-11-02' },
    // Regimes atuais
    { id: 'lc123_art3', rotulo: 'LC nº 123/2006, art. 3º, II (limite de R$ 4,8 milhões)', url: LC123, validado: true, conferido: OK },
    { id: 'lc123_sublimite', rotulo: 'LC nº 123/2006, art. 13-A (sublimite de R$ 3,6 milhões; inclui o IBS a partir de 2027, art. 517 da LC 214)', url: LC123, validado: true, conferido: OK },
    { id: 'lei9718_art13', rotulo: 'Lei nº 9.718/1998, art. 13 (limite de R$ 78 milhões, red. Lei nº 12.814/2013)', url: P + 'leis/l9718compilada.htm', validado: true, conferido: OK },
    { id: 'lei9718_cumulativo', rotulo: 'Lei nº 9.715/1998, art. 8º, I (PIS 0,65%) e Lei nº 9.718/1998, art. 8º (Cofins 3%)', url: P + 'leis/l9718compilada.htm', validado: true, conferido: OK },
    { id: 'lei10637_10833', rotulo: 'Lei nº 10.637/2002, art. 2º (PIS 1,65%) e Lei nº 10.833/2003, art. 2º (Cofins 7,6%)', url: P + 'leis/2003/l10.833.htm', validado: true, conferido: OK },
    { id: 'lc116_iss', rotulo: 'LC nº 116/2003, art. 8º, II (máximo de 5%) e art. 8º-A (mínimo de 2%)', url: P + 'leis/lcp/lcp116.htm', validado: true, conferido: OK },
    // Incentivos regionais
    { id: 'mp2199_art1', rotulo: 'MP nº 2.199-14/2001, art. 1º, red. Lei nº 14.753/2023 (75% do IRPJ sobre o lucro da exploração; projetos até 31/12/2028)', url: P + 'mpv/2199-14.htm', validado: true, conferido: OK },
    { id: 'sudam_prazo', rotulo: 'Lei nº 14.753/2023 (protocolo e aprovação até 31/12/2028)', url: P + '_ato2023-2026/2023/lei/l14753.htm', validado: true, conferido: OK },
    { id: 'lucro_real_exploracao', rotulo: 'Exigência de Lucro Real: decorre do cálculo pelo lucro da exploração (RIR/2018, art. 626; DL 1.598/1977, art. 19) — não é literal na MP', url: P + '_ato2015-2018/2018/decreto/d9580.htm', validado: false },
    { id: 'dec4212_setores', rotulo: 'Decreto nº 4.212/2002, art. 2º (setores prioritários; vigência frente à Res. CONDEL/SUDAM 136/2025 a confirmar)', url: P + 'decreto/2002/d4212.htm', validado: false },
    { id: 'lc124_sudam', rotulo: 'LC nº 124/2007, art. 2º (área da SUDAM)', url: P + 'leis/lcp/lcp124.htm', validado: true, conferido: OK },
    { id: 'lei7827_fco', rotulo: 'Lei nº 7.827/1989, art. 1º (FNO, FNE e FCO)', url: P + 'leis/l7827.htm', validado: true, conferido: OK },
    { id: 'lei14789', rotulo: 'Lei nº 14.789/2023, arts. 1º, 3º, 4º, 6º, 8º e 22', url: P + '_ato2023-2026/2023/lei/l14789.htm', validado: true, conferido: OK },
    // Calendário
    { id: 'clt_459', rotulo: 'CLT, art. 459, § 1º (salário até o 5º dia útil)', url: P + 'decreto-lei/del5452.htm', validado: true, conferido: OK },
    { id: 'mte_sabado', rotulo: 'IN MTP nº 2/2021, art. 14, I (sábado entra na contagem do 5º dia útil; orientação à fiscalização)', url: 'https://www.gov.br/trabalho-e-emprego/pt-br', validado: true, conferido: OK },
    { id: 'lei_4749', rotulo: 'Lei nº 4.749/1965, arts. 1º e 2º (13º: até 30/11 e 20/12)', url: P + 'leis/l4749.htm', validado: true, conferido: OK },
    { id: 'cal_esocial', rotulo: 'MOS do eSocial S-1.3 (dia 15, prorroga)', url: 'https://www.gov.br/esocial/', validado: true, conferido: OK },
    { id: 'cal_reinf', rotulo: 'IN RFB nº 2.043/2021, art. 6º, § 2º (dia 15, prorroga)', url: RFB + '119859/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_dctfweb', rotulo: 'IN RFB nº 2.237/2024, art. 6º, red. IN RFB nº 2.248/2025 (último dia útil do mês seguinte)', url: RFB + '141910/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_fgts', rotulo: 'Lei nº 8.036/1990, art. 15 (dia 20; antecipa, conforme orientação do FGTS Digital)', url: P + 'leis/l8036consol.htm', validado: true, conferido: OK },
    { id: 'cal_inss', rotulo: 'Lei nº 8.212/1991, art. 30, I, "b", e § 2º (dia 20, antecipa)', url: P + 'leis/l8212cons.htm', validado: true, conferido: OK },
    { id: 'cal_irrf', rotulo: 'Lei nº 11.196/2005, art. 70, I, "d" (último dia útil do 2º decêndio)', url: P + '_ato2004-2006/2005/lei/l11196.htm', validado: true, conferido: OK },
    { id: 'cal_das', rotulo: 'Resolução CGSN nº 140/2018, art. 40 (dia 20; prorroga)', url: RFB + '92278/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_piscofins', rotulo: 'MP nº 2.158-35/2001, art. 18, II (dia 25, antecipa)', url: P + 'mpv/2158-35.htm', validado: true, conferido: OK },
    { id: 'cal_efdcontrib', rotulo: 'IN RFB nº 1.252/2012, art. 7º (10º dia útil do 2º mês)', url: RFB + '37466/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_irpj', rotulo: 'Lei nº 9.430/1996, arts. 5º e 28 (IRPJ/CSLL trimestral)', url: P + 'leis/l9430.htm', validado: true, conferido: OK },
    { id: 'cal_defis', rotulo: 'Resolução CGSN nº 140/2018, art. 72, § 1º (31/03)', url: RFB + '92278/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_dasnsimei', rotulo: 'Resolução CGSN nº 140/2018, art. 109 (último dia de maio)', url: RFB + '92278/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_ecd', rotulo: 'IN RFB nº 2.003/2021, art. 5º, red. IN RFB nº 2.142/2023 (último dia útil de junho)', url: RFB + '114965/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_ecf', rotulo: 'IN RFB nº 2.004/2021, art. 3º (último dia útil de julho)', url: RFB + '114966/visao/vigente', validado: true, conferido: OK },
    { id: 'cal_cbs', rotulo: 'Decreto nº 12.955/2026 (Regulamento da CBS), art. 45: último dia útil do mês seguinte (vigência por partes, art. 619)', url: P + '_ato2023-2026/2026/decreto/d12955.htm', validado: true, conferido: OK },
    { id: 'cal_ibs', rotulo: 'Vencimento do IBS (regulamento do Comitê Gestor do IBS)', url: null, validado: false },
    { id: 'go_fundeinfra', rotulo: 'Lei estadual (GO) nº 21.670/2022, arts. 1º e 5º (FUNDEINFRA; até 1,65%)', url: 'https://appasp.economia.go.gov.br/legislacao/arquivos/LEIS/L_21670.htm', validado: true, conferido: OK },
    { id: 'go_progoias', rotulo: 'Lei estadual (GO) nº 20.787/2020 (ProGoiás; substitui FOMENTAR/PRODUZIR, validade até 2032)', url: 'https://goias.gov.br/economia/progoias/', validado: true, conferido: OK },
    { id: 'to_incentivos', rotulo: 'TO: Leis nº 1.355/2002 (PROSPERAR), 1.385/2003 (PROINDÚSTRIA), 1.695/2006 (agronegócio) e 2.679/2012 (PROLOGÍSTICA) — SICS-TO', url: 'https://www.to.gov.br/sics/incentivos-fiscais/6b9wypu38j6p', validado: true, conferido: OK },
    { id: 'pa_lei6913', rotulo: 'Lei estadual (PA) nº 6.913/2006 (indústrias e centrais de distribuição)', url: 'https://bancodeleis.alepa.pa.gov.br/arquivos/lei6913_2006_96939.pdf', validado: true, conferido: OK },
    { id: 'pa_lei6489', rotulo: 'Lei estadual (PA) nº 6.489/2002 (Política de Incentivos ao Desenvolvimento Socioeconômico)', url: null, validado: false },
    { id: 'sefaz_uf', rotulo: 'Legislação e calendário da fazenda estadual', url: null, validado: false }
  ];
  var porId = {};
  lista.forEach(function (f) { porId[f.id] = f; });
  return { lista: lista, porId: porId };
});
