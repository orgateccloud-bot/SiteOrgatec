/* Cadastro das 27 UFs: áreas de incentivo regional, ZFM/ALC, fazenda estadual,
   guia de arrecadação, obrigações estaduais e alertas regionais (GO, TO, PA).
   Campos não confirmados ficam com validado/guiaValidada = false e aparecem
   como "pendente de validação" no site. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).ufs = factory();
})(this, function () {
  'use strict';

  // [sigla, nome, região, sudam, sudene, sudeco, órgão fazendário, portal, guia, guiaValidada, icms]
  // sudam/sudene: true | 'parcial' | false. SUDAM: LC 124/2007, art. 2º; SUDENE: LC 125/2007, art. 2º; SUDECO: LC 129/2009, art. 2º.
  // Órgão, portal e guia conferidos nos portais oficiais em 30/10/2026. `icms`: vencimento do ICMS normal mensal
  //   { dia, nota, base, url } — dia null + nota = regra varia por atividade/CNAE; icms null = não confirmado.
  var BASE = [
    ['AC', 'Acre', 'Norte', true, false, false, 'SEFAZ-AC', 'https://sefaz.ac.gov.br/', null, false, null],
    ['AL', 'Alagoas', 'Nordeste', false, true, false, 'SEFAZ-AL', 'https://www.sefaz.al.gov.br/', 'DAR', true, null],
    ['AP', 'Amapá', 'Norte', true, false, false, 'SEFAZ-AP', 'https://sefaz.portal.ap.gov.br/', 'DAR', true, null],
    ['AM', 'Amazonas', 'Norte', true, false, false, 'SEFAZ-AM', 'https://www.sefaz.am.gov.br/', 'DAR', true,
      { dia: 20, base: 'RICMS-AM (Dec. 20.686/1999), art. 107, II, "c", 1' }],
    ['BA', 'Bahia', 'Nordeste', false, true, false, 'SEFAZ-BA', 'https://www.sefaz.ba.gov.br/', 'DAE', true, null],
    ['CE', 'Ceará', 'Nordeste', false, true, false, 'SEFAZ-CE', 'https://www.ce.gov.br/sefaz/', 'DAE', true, null],
    ['DF', 'Distrito Federal', 'Centro-Oeste', false, false, true, 'Secretaria de Economia do DF (Receita DF)', 'https://www.receita.fazenda.df.gov.br', 'DAR', true,
      { dia: 20, nota: 'comércio e serviços; indústria e produtor: dia 10 do 2º mês', base: 'RICMS-DF (Dec. 18.955/1997), art. 74, I, "a", e IV' }],
    ['ES', 'Espírito Santo', 'Sudeste', false, 'parcial', false, 'SEFAZ-ES', 'https://sefaz.es.gov.br/', 'DUA', true,
      { dia: 18, nota: 'comércio e transporte; indústria: dia 19', base: 'RICMS-ES (Dec. 1.090-R/2002), art. 168, VIII e IX' }],
    ['GO', 'Goiás', 'Centro-Oeste', false, false, true, 'Secretaria de Estado da Economia de Goiás', 'https://goias.gov.br/economia/', 'DARE', true,
      { dia: 20, nota: 'comércio, indústria, transporte, comunicação e energia', base: 'IN 155/94-GSF, art. 2º, I; RCTE, arts. 75 a 77 (Calendário de Recolhimento de ICMS)' }],
    ['MA', 'Maranhão', 'Nordeste', 'parcial', true, false, 'SEFAZ-MA', 'https://portal.sefaz.ma.gov.br/', 'DARE', false, null],
    ['MT', 'Mato Grosso', 'Centro-Oeste', true, false, true, 'SEFAZ-MT', 'https://www5.sefaz.mt.gov.br', 'DAR-1/AUT', true,
      { dia: null, nota: 'dia 6 no regime normal; dia 20 para comércio atacadista/varejista e CNAEs da Port. 037/2020', base: 'Portaria SEFAZ-MT nº 137/2021, art. 1º, I e II' }],
    ['MS', 'Mato Grosso do Sul', 'Centro-Oeste', false, false, true, 'SEFAZ-MS', 'https://www.sefaz.ms.gov.br', 'DAEMS', true,
      { dia: null, nota: 'datas fixadas por Resolução SEFAZ trimestral', base: 'RICMS-MS, art. 82, I, e Anexo VIII' }],
    ['MG', 'Minas Gerais', 'Sudeste', false, 'parcial', false, 'SEF-MG', 'https://www.fazenda.mg.gov.br/', 'DAE', true,
      { dia: 8, nota: 'comércio, indústria não especificada e transporte; outras atividades têm prazos próprios', base: 'RICMS/2023 (Dec. 48.589/2023), art. 112, I' }],
    ['PA', 'Pará', 'Norte', true, false, false, 'Secretaria de Estado da Fazenda do Pará (SEFA)', 'https://www.sefa.pa.gov.br', 'DAE', true, null],
    ['PB', 'Paraíba', 'Nordeste', false, true, false, 'SEFAZ-PB', 'https://www.sefaz.pb.gov.br/', 'DAR', true,
      { dia: 15, nota: 'comércio; transporte, comunicação e energia: dia 20', base: 'Cronograma de Arrecadação (portal SEFAZ-PB)' }],
    ['PR', 'Paraná', 'Sul', false, false, false, 'Secretaria da Fazenda do Paraná (Receita Estadual)', 'https://www.fazenda.pr.gov.br/', 'GR-PR', true,
      { dia: 12, base: 'Página oficial "ICMS – Regime Normal" (Receita Estadual do PR)', url: 'https://www.fazenda.pr.gov.br/Pagina/ICMS-Regime-Normal' }],
    ['PE', 'Pernambuco', 'Nordeste', false, true, false, 'SEFAZ-PE', 'https://www.sefaz.pe.gov.br', 'DAE', true,
      { dia: 15, base: 'Decreto nº 44.650/2017, art. 23' }],
    ['PI', 'Piauí', 'Nordeste', false, true, false, 'SEFAZ-PI', 'https://portal.sefaz.pi.gov.br', 'DAR', true, null],
    ['RJ', 'Rio de Janeiro', 'Sudeste', false, false, false, 'SEFAZ-RJ', 'https://www.fazenda.rj.gov.br/', 'DARJ', false, null],
    ['RN', 'Rio Grande do Norte', 'Nordeste', false, true, false, 'SEFAZ-RN', 'https://www.sefaz.rn.gov.br', 'DARE', true,
      { dia: 15, nota: 'supermercados: dia 20', base: 'RICMS-RN (Dec. 31.825/2022), art. 58, V, "a"' }],
    ['RS', 'Rio Grande do Sul', 'Sul', false, false, false, 'Receita Estadual do RS (Sefaz-RS)', 'https://receita.fazenda.rs.gov.br/inicial', 'GA', true,
      { dia: 12, nota: 'comércio e demais; transporte e complexo industrial: dia 21', base: 'RICMS-RS (Dec. 37.699/1997), Livro I, art. 43, c/c Apêndice III' }],
    ['RO', 'Rondônia', 'Norte', true, false, false, 'SEFIN-RO', 'https://www.sefin.ro.gov.br/', 'DARE', true,
      { dia: 20, base: 'RICMS-RO (Dec. 22.721/2018), art. 57, XI, "a"' }],
    ['RR', 'Roraima', 'Norte', true, false, false, 'SEFAZ-RR', 'https://www.sefaz.rr.gov.br/', 'DARE', true,
      { dia: 20, base: 'RICMS-RR (Dec. 4.335/2001), art. 71, I' }],
    ['SC', 'Santa Catarina', 'Sul', false, false, false, 'SEF-SC', 'https://www.sef.sc.gov.br/', 'DARE-SC', true,
      { dia: 10, nota: 'pode ir ao 16º ou 20º dia para contribuintes com regularidade', base: 'RICMS-SC/01, art. 60, caput e § 4º' }],
    ['SP', 'São Paulo', 'Sudeste', false, false, false, 'Secretaria da Fazenda e Planejamento de SP', 'https://portal.fazenda.sp.gov.br', 'DARE-SP', true,
      { dia: null, nota: 'por código de prazo (CPR) conforme o CNAE; ex.: varejo CPR 1200 = dia 20', base: 'RICMS-SP/2000, Anexo IV, arts. 2º e 3º' }],
    ['SE', 'Sergipe', 'Nordeste', false, true, false, 'SEFAZ-SE', 'https://www.sefaz.se.gov.br', 'DAE', true, null],
    ['TO', 'Tocantins', 'Norte', true, false, false, 'Secretaria da Fazenda do Tocantins (SEFAZ-TO)', 'https://www.to.gov.br/sefaz', 'DARE', true, null]
  ];

  // Áreas de Livre Comércio (municípios) e Zona Franca de Manaus.
  var ALC = {
    AC: 'Brasiléia (com extensão a Epitaciolândia) e Cruzeiro do Sul',
    AM: 'Tabatinga',
    AP: 'Macapá e Santana',
    RO: 'Guajará-Mirim',
    RR: 'Boa Vista e Bonfim'
  };

  // Alertas exclusivos do eixo GO-TO-PA (seção "Alertas regionais").
  var REGIONAIS = {
    GO: [
      { id: 'go_agro_sudeco', setores: ['agro'], nivel: 'atencao', titulo: 'Goiás não está na área da SUDAM',
        texto: 'O produtor e a agroindústria goianos não têm a redução de 75% do IRPJ, exclusiva das áreas da SUDAM e da SUDENE. O planejamento passa pelo FCO, pela escolha entre produtor contribuinte ou não contribuinte de IBS/CBS e pelos benefícios estaduais de ICMS ainda vigentes.',
        fontes: ['lc124_sudam', 'mp2199_art1', 'lei7827_fco'] },
      { id: 'go_agro_fundo', setores: ['agro'], nivel: 'atencao', titulo: 'FUNDEINFRA: contribuição de até 1,65% no agro goiano',
        texto: 'Goiás exige contribuição ao FUNDEINFRA (Lei estadual nº 21.670/2022), de até 1,65%, como condição para fruir benefício fiscal de ICMS, regime especial de exportação e substituição tributária em produtos da agropecuária e da mineração. A EC nº 132/2023 permite que estados com fundos desse tipo em 30/04/2023 mantenham contribuição semelhante até 31/12/2043, mesmo depois do fim do ICMS. Inclua esse custo na formação de preço.',
        fontes: ['go_fundeinfra', 'adct_136'] },
      { id: 'go_atacado', setores: ['comercio_atacadista'], nivel: 'critico', titulo: 'Atacadistas com regime especial de ICMS em Goiás',
        texto: 'Distribuidores instalados em Goiás por causa de regimes especiais ou créditos outorgados de ICMS perdem essa vantagem com a redução do ICMS a partir de 2029 e o IBS no destino. É preciso recalcular a margem por UF de destino e o custo logístico sem o incentivo.',
        fontes: ['adct_12_fundo', 'cf_156a_destino', 'sefaz_uf'] },
      { id: 'go_industria', setores: ['industria'], nivel: 'atencao', titulo: 'ProGoiás, FOMENTAR e PRODUZIR: benefícios até 2032',
        texto: 'O ProGoiás (Lei estadual nº 20.787/2020), que concede crédito outorgado de ICMS e substitui o FOMENTAR e o PRODUZIR para novos projetos, tem validade até 2032, quando o ICMS ainda existe a 6/10. Indústrias beneficiárias devem projetar a margem sem o incentivo a partir de 2033. Benefícios onerosos regulares podem ser compensados pelo Fundo de Compensação de 2029 a 2032; no Lucro Real, verifique o crédito fiscal de subvenção da Lei nº 14.789/2023.',
        fontes: ['go_progoias', 'adct_12_fundo', 'lei14789'] }
    ],
    TO: [
      { id: 'to_agro_sudam', setores: ['agro'], nivel: 'oportunidade', titulo: 'Tocantins: agroindústria na área da SUDAM',
        texto: 'Agroindústrias do Tocantins nas cadeias prioritárias (óleos vegetais, carne e derivados, sucos e conservas, fibras, aquicultura) e projetos de agricultura irrigada em polos, no Lucro Real, podem pleitear a redução de 75% do IRPJ junto à SUDAM, com projeto aprovado até 31/12/2028. Para o produtor rural, a decisão entre ser ou não contribuinte de IBS/CBS deve considerar o preço praticado por tradings e cooperativas.',
        fontes: ['lc124_sudam', 'mp2199_art1', 'dec4212_setores', 'lc214_produtor_nc'] },
      { id: 'to_atacado', setores: ['comercio_atacadista'], nivel: 'atencao', titulo: 'Tocantins: rota logística e regimes especiais de ICMS',
        texto: 'Atacadistas que abastecem o Norte a partir do Tocantins com regime especial de ICMS (como o PROLOGÍSTICA, Lei estadual nº 2.679/2012) precisam simular a margem sem o benefício, com o IBS devido no estado de destino.',
        fontes: ['to_incentivos', 'cf_156a_destino'] },
      { id: 'to_industria', setores: ['industria'], nivel: 'oportunidade', titulo: 'Tocantins: incentivo federal + estadual para indústria',
        texto: 'A indústria no Tocantins pode combinar a redução de 75% do IRPJ (SUDAM, Lucro Real, projeto até 31/12/2028) com os programas estaduais de ICMS, como PROSPERAR (Lei nº 1.355/2002) e PROINDÚSTRIA (Lei nº 1.385/2003), enquanto vigorarem. O incentivo federal sobrevive à reforma; os estaduais perdem efeito até 2032.',
        fontes: ['mp2199_art1', 'to_incentivos', 'adct_12_fundo'] }
    ],
    PA: [
      { id: 'pa_agro_sudam', setores: ['agro'], nivel: 'oportunidade', titulo: 'Pará: pecuária e agroindústria na área da SUDAM',
        texto: 'Frigoríficos e agroindústrias paraenses da cadeia de carne e derivados (e demais cadeias prioritárias), no Lucro Real e com projeto aprovado até 31/12/2028, podem reduzir 75% do IRPJ. A cadeia da pecuária deve revisar a condição de contribuinte dos produtores fornecedores, que define o crédito (pleno ou presumido) de quem compra.',
        fontes: ['lc124_sudam', 'mp2199_art1', 'dec4212_setores', 'lc214_credito_presumido'] },
      { id: 'pa_industria_is', setores: ['industria'], nivel: 'critico', titulo: 'Pará: Imposto Seletivo na extração mineral',
        texto: 'A extração de bens minerais passa a sofrer o Imposto Seletivo, cobrado na extração independentemente da destinação, inclusive quando o minério é exportado. A Constituição limita a alíquota a 1% do valor de mercado e a LC nº 214/2025 fixa teto de 0,25%; a alíquota efetiva depende de lei ordinária ainda não conferida. Mineradoras e indústrias de transformação mineral do Pará devem incluir esse custo na projeção a partir de 2027.',
        fontes: ['lc214_is', 'cf_153_is', 'is_lei_ordinaria'] },
      { id: 'pa_atacado', setores: ['comercio_atacadista'], nivel: 'atencao', titulo: 'Pará: distribuição regional e IBS no destino',
        texto: 'Distribuidores que atendem a Região Norte a partir do Pará passam a recolher IBS para o estado e o município de destino. O tratamento estadual para indústrias e centrais de distribuição (Lei estadual nº 6.913/2006) e a política geral de incentivos (Lei nº 6.489/2002) perdem efeito com o fim do ICMS.',
        fontes: ['cf_156a_destino', 'pa_lei6913', 'pa_lei6489', 'adct_12_fundo'] }
    ]
  };

  var lista = BASE.map(function (b) {
    var icms = b[10];
    var guia = b[8] ? ' (' + b[8] + ')' : '';
    var obrigIcms = icms
      ? { id: 'icms', titulo: 'ICMS — apuração mensal' + guia + (icms.nota ? ': ' + icms.nota : ''),
          dia: icms.dia, regraVariavel: !icms.dia, validado: true, base: { rotulo: icms.base, url: icms.url || b[7], validado: true } }
      : { id: 'icms', titulo: 'ICMS — apuração mensal' + guia + ': vencimento conforme calendário estadual', dia: null, validado: false,
          base: { rotulo: 'Calendário de recolhimento do ICMS — ' + b[6], url: b[7], validado: false } };
    return {
      sigla: b[0], nome: b[1], regiao: b[2], sudam: b[3], sudene: b[4], sudeco: b[5],
      orgao: b[6], portal: b[7], guia: b[8], guiaValidada: b[9],
      zfm: b[0] === 'AM', alc: ALC[b[0]] || null,
      // Obrigações estaduais do calendário. Feriados estaduais/municipais e a regra estadual para dia
      // não útil não foram conferidos: quando a data é ajustada, o item sai "pendente de validação".
      obrigacoes: [
        obrigIcms,
        { id: 'efd', titulo: 'EFD ICMS/IPI (SPED Fiscal): prazo estadual', dia: null, validado: false,
          base: { rotulo: 'Legislação da ' + b[6], url: b[7], validado: false } }
      ],
      alertasRegionais: REGIONAIS[b[0]] || []
    };
  });
  var porSigla = {};
  lista.forEach(function (u) { porSigla[u.sigla] = u; });
  return { lista: lista, porSigla: porSigla, ALC: ALC };
});
