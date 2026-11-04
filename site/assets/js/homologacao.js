/* Fase de testes (homologação): lista de pendências para a próxima fase e autoteste dos módulos.
   Fonte única da lista: a página site/testes/index.html e o arquivo docs/pendencias-proxima-fase.md
   (tools/exportar_pendencias.js) saem daqui. Pendências com `verifica` mudam de status sozinhas quando
   a configuração ou os dados são atualizados; as demais são marcadas à mão em `resolvidaManual`.
   Funções puras, testadas em tests/js/homologacao.test.js. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).homologacao = factory();
})(this, function () {
  'use strict';

  var CATEGORIAS = {
    decisao: 'Decisões da ORGATEC',
    configuracao: 'Configuração (Plano Diretor)',
    validacao: 'Validação técnica do conteúdo',
    tecnico: 'Implantação técnica'
  };
  var RESPONSAVEL = { orgatec: 'ORGATEC (direção)', rt: 'Responsável técnico (CRC)', dev: 'Desenvolvimento' };

  function lista(arr, max) { return arr.length > max ? arr.slice(0, max).join(', ') + ' e mais ' + (arr.length - max) : arr.join(', '); }

  /* bloqueia: impede virar config.ambiente para 'producao'. depende: ids que precisam ser resolvidos antes. */
  var PENDENCIAS = [
    // ---------- Decisões
    { id: 'D1', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Público prioritário: agro, transporte ou os dois com o mesmo peso',
      onde: 'tools/layout.py (ordem do menu) e tools/gerar_paginas.py → inicio() (bloco "Qual é o seu caso?")', descricao: 'Hoje os dois setores têm o mesmo peso. A escolha muda a home e a ordem da navegação.' },
    { id: 'D2', categoria: 'decisao', responsavel: 'orgatec', bloqueia: true, titulo: 'Área do cliente: só o portal do ERP ou área própria com login',
      onde: 'site/cliente/index.html', depende: [], descricao: 'Área própria exige autenticação, guarda de documentos de clientes e adequação à LGPD (base legal, retenção, encarregado). Só o portal mantém o site sem dados de clientes. Em 01/11/2026 (Warley Veloso): lançamento completo, ou seja, o site só vai para produção com a área do cliente e com o envio dos alertas por e-mail; a forma da área do cliente segue em aberto.' },
    { id: 'D3', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, resolvida: true, titulo: 'Escopo de auditoria e compliance (ideias da entrega 4)',
      onde: 'docs/decisao-auditoria-compliance.md e docs/plano-area-compliance.md', descricao: 'Decidido em 01/11/2026: seção própria (área de Compliance). Fase A publicada com a frente de conformidade tributária; as demais decisões estão em D10.' },
    { id: 'D4', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Comprovar os 51 anos de atuação',
      onde: "site/assets/js/config.js → institucional.inicioAtuacao e institucional.comprovacao",
      descricao: 'Informar a data de início e o documento que a sustenta (escritório antecessor, registro do fundador no CRC). O CRC-TO e o CNPJ atual não servem de base. Sem isso, o número não aparece.',
      verifica: function (c) {
        var i = c.config.institucional || {};
        return { resolvida: !!(i.inicioAtuacao && i.comprovacao), detalhe: i.inicioAtuacao ? 'Início informado: ' + i.inicioAtuacao : 'Campos vazios: o número não aparece no site.' };
      } },
    { id: 'D5', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Enviar os estudos da reforma e a identidade visual da reforma do escritório',
      onde: 'anexar na conversa', descricao: 'Só o Plano Diretor foi recebido. Com o material, o mapeamento e o design system são revistos.' },

    { id: 'D6', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Confirmar o verde do WhatsApp no design ORGATEC Trilha',
      onde: 'tools/gerar_design_system.py → PADRAO; site/assets/marca/',
      descricao: 'Em 31/10/2026 o design ORGATEC Trilha foi aplicado ao site inteiro, com seletor "Cores" em todas as páginas. Paleta padrão escolhida pela ORGATEC em 31/10/2026: Azul flutuante; trocada em 02/11/2026 para Azul flutuante escuro. Símbolo decidido: o logotipo original em esfera, sempre com as cores originais, inclusive nas paletas escuras. Ainda a confirmar: verde mantido só no botão de WhatsApp. Atenção: nas paletas Azul Tribunal, Vinho Toga e Azul flutuante, o texto de alerta sobre o fundo de aviso fica entre 4,2:1 e 4,3:1, abaixo do mínimo de 4,5:1 (valores do original).' },
    { id: 'D7', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Aprovar a nova estrutura do site: página inicial curta e ferramentas em páginas próprias',
      onde: 'tools/gerar_paginas.py (inicio, simulador, calendario, regional) e tools/layout.py (menu e rodapé)',
      descricao: 'Em 31/10/2026 a página inicial passou de 13 para 7 blocos (cerca de 17.100 px → 6.100 px no celular). Simulador, calendário, alertas regionais, captura de XML e formulário de contato ganharam páginas próprias, e o menu passou a ter os grupos Setores e Ferramentas. A versão anterior está em _legado/index-2026-10-31.html, com o roteiro de volta em _legado/LEIA-ME.md. Desde 31/10/2026 a raiz do site (index.html) é a tela de abertura; a vitrine passou para inicio.html. Desde 02/11/2026 a abertura começa só com o holograma, o cartão ORGATEC surge em seguida e o botão "Entrar no site" leva à vitrine; a área tributária virou atalho. Mais tarde em 02/11/2026 a abertura passou ao modelo do trilhum.io: texto direto no fundo, sem caixa de vidro e sem os cards de marcos da reforma (que seguem na vitrine e na Central), e a projeção alternando os logotipos ORGATEC e LOCAR (03/11/2026). Falta a ORGATEC conferir os textos da tela de abertura e da vitrine e a ordem dos blocos. Aprovam os textos: Warley Veloso e Robson Alain Veloso (resposta de 01/11/2026).' },
    { id: 'D8', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Conferir os boletins automáticos da Janela de Campo na primeira semana',
      onde: 'setores/janela-de-campo.html; tools/gerar_boletim_campo.py (agendado às 05h, 11h e 17h no PC); tools/logs/campo.log',
      descricao: 'Desde 02/11/2026 o boletim é gerado sozinho com a previsão hora a hora do MET Norway para 20 polos (tools/campo_polos.json), com mapa de satélite da NASA. Confira por alguns dias se as janelas e os textos fazem sentido no campo e se os polos representam bem os clientes. O agendador depende do PC ligado e conectado ao Windows.' },
    { id: 'D11', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Pedir ao INMET acesso oficial à previsão por programa',
      onde: 'tools/gerar_boletim_campo.py (nova fonte)',
      descricao: 'A API de previsão usada pelo site do INMET fica atrás de uma proteção contra robôs e não tem documentação para terceiros (verificado em 02/11/2026). Com acesso oficial, a previsão do INMET passa a complementar ou substituir a do MET Norway. Hoje o site leva aos avisos oficiais em alertas2.inmet.gov.br.' },
    { id: 'D12', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Autorização do CPTEC/INPE para usar a previsão no site',
      onde: 'tools/gerar_boletim_campo.py (nova fonte)',
      descricao: 'Os termos do CPTEC/INPE proíbem uso comercial e reprodução sem autorização expressa. Por isso a previsão de 7 dias do CPTEC não entra no boletim. Com autorização por escrito, ela pode aparecer ao lado da previsão do MET Norway.' },

    { id: 'D9', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Incorporação dos sistemas: decisões D1 a D6 do plano',
      onde: 'docs/plano-incorporacao-produtos.md, seção 7; site/assets/js/config.js → solucoes',
      descricao: 'Em 01/11/2026 entrou o menu Soluções (Fase 1), com padrões provisórios: nomes descritivos, conciliação apresentada como serviço da ORGATEC com sistema próprio, sem preços e sem crédito. Falta decidir: D1 vender o sistema de conciliação a outros escritórios; D2 nomes públicos; D3 domínio e subdomínios; D4 preços da gestão financeira; D5 quando o crédito ESC entra; D6 quem aprova os textos de cada página de solução.' },
    { id: 'D10', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, resolvida: true, titulo: 'Área de Compliance: decisões C1 a C6 do plano',
      onde: 'docs/plano-area-compliance.md, seção 8; tools/layout.py (COMPLIANCE e NAV)',
      descricao: 'Decidido em 01/11/2026: C1 nome "Compliance"; C2 as quatro frentes (tributária, PLD, LGPD e integridade); C3 grupo próprio no menu, com "Escritório" no rodapé e no menu ☰; C4 o escritório entrega diagnóstico e organização de documentos e rotinas, sem parecer jurídico; C5 termômetro oculto em produção até a revisão técnica (V11); C6 publicar na página Escritório como a ORGATEC cumpre PLD e LGPD, com o canal do encarregado como "em ativação" até o dpo@ funcionar (C4 do painel) e o texto revisado pelo responsável técnico (V12).' },
    { id: 'D13', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, resolvida: true, titulo: 'Ler o relatório de públicos da reforma e escolher a ordem da fase 2 do Compliance',
      onde: 'docs/relatorio-publicos-reforma-compliance.md e docs/plano-area-compliance.md (Fase 2: por público)',
      descricao: 'Decidido em 02/11/2026: a fase 2 cobre os 9 públicos do relatório, na ordem P1 transportador, P2 produtor rural, P3 MEI, autônomo e Simples, P4 comércio e indústria e serviços, P5 pessoa física com imóveis, P6 consumidor de baixa renda (só pergunta frequente). P1 feita em 02/11/2026: compliance/publicos.html e compliance/publico/transportador.html, perfil do transportador no termômetro e relatório para imprimir.' },
    // ---------- Configuração (Plano Diretor, item 4)
    { id: 'C1', categoria: 'configuracao', responsavel: 'orgatec', bloqueia: false, titulo: 'Ferramenta de captura de XML (Sieg, Arquivei ou Omie)',
      onde: 'site/assets/js/config.js → capturaXml.ferramenta',
      verifica: function (c) { var f = c.config.capturaXml.ferramenta; return { resolvida: !!f, detalhe: f ? 'Definida: ' + c.config.capturaXml.opcoes[f].nome : 'Não definida.' }; } },
    { id: 'C2', categoria: 'configuracao', responsavel: 'orgatec', bloqueia: true, titulo: 'ERP do portal do cliente e alvo do CNAME de portal.orgatec.io',
      onde: 'site/assets/js/config.js → portal.erp e portal.cnameAlvo', depende: ['D2'],
      descricao: 'ERP definido em 01/11/2026: Athenas Online (orgatec.athenas.online). Até o CNAME existir, os links do portal vão direto ao login do Athenas. Falta a Athenas informar o alvo do CNAME e se emite o certificado de portal.orgatec.io. Confirmar também com a Athenas a autenticação multifator e o registro de acessos, que a página do cliente e a política de privacidade afirmam.',
      verifica: function (c) { var p = c.config.portal; return { resolvida: !!(p.erp && p.cnameAlvo), detalhe: p.erp ? 'ERP: ' + p.opcoes[p.erp].nome + (p.cnameAlvo ? '' : ' (falta o alvo do CNAME)') : 'ERP não definido.' }; } },
    { id: 'C3', categoria: 'configuracao', responsavel: 'orgatec', bloqueia: false, titulo: 'Ativar o e-mail contato@orgatec.io',
      onde: 'site/assets/js/config.js → emails.contato.ativo',
      verifica: function (c) { return { resolvida: !!c.config.emails.contato.ativo, detalhe: c.config.emails.contato.ativo ? 'Ativo.' : 'Inativo: o endereço não aparece no site.' }; } },
    { id: 'C4', categoria: 'configuracao', responsavel: 'orgatec', bloqueia: true, titulo: 'Ativar o e-mail do encarregado de dados (dpo@orgatec.io)',
      onde: 'site/assets/js/config.js → emails.dpo.ativo', descricao: 'A política de privacidade precisa de um canal ativo para o titular dos dados. Em 01/11/2026 a ORGATEC preferiu não avaliar agora o enquadramento como agente de tratamento de pequeno porte (Res. CD/ANPD nº 2/2022), então o canal do encarregado continua exigido para a produção.',
      verifica: function (c) { return { resolvida: !!c.config.emails.dpo.ativo, detalhe: c.config.emails.dpo.ativo ? 'Ativo.' : 'Inativo.' }; } },
    { id: 'C5', categoria: 'configuracao', responsavel: 'orgatec', bloqueia: true, titulo: 'Validar o WhatsApp oficial +55 62 99294-9161',
      onde: 'site/assets/js/config.js → whatsapp.validado', descricao: 'Decidido em 01/11/2026 (Warley Veloso): validar = migrar o número para o WhatsApp Business, com perfil comercial da ORGATEC. Depois da migração, marque whatsapp.validado: true. Passo a passo em docs/respostas-roteiro-2026-11-01.md.',
      verifica: function (c) { return { resolvida: !!c.config.whatsapp.validado, detalhe: c.config.whatsapp.validado ? 'Validado.' : 'Número em uso, ainda não validado.' }; } },

    // ---------- Validação técnica do conteúdo
    { id: 'V1', categoria: 'validacao', responsavel: 'rt', bloqueia: true, titulo: 'Revisão técnica dos itens da reforma',
      onde: "site/assets/js/reforma-itens.js → revisao: { status: 'aprovada', por, em }", descricao: 'Em produção, só itens aprovados aparecem. Roteiro em docs/revisao-tecnica.md.',
      verifica: function (c) {
        var pend = c.itens.filter(function (i) { return !i.revisao || i.revisao.status !== 'aprovada'; });
        return { resolvida: pend.length === 0, detalhe: pend.length + ' de ' + c.itens.length + ' itens aguardando revisão.' };
      } },
    { id: 'V2', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Fontes legais com o selo "pendente de validação"',
      onde: "site/assets/js/fontes.js → validado: true e conferido", descricao: 'Cada fonte pendente aparece com selo em todo o site. Conferir o dispositivo na fonte primária.',
      verifica: function (c) {
        var pend = c.fontes.lista.filter(function (f) { return !f.validado; }).map(function (f) { return f.id; });
        return { resolvida: pend.length === 0, detalhe: pend.length ? pend.length + ' pendentes: ' + lista(pend, 12) + '.' : 'Todas conferidas.' };
      } },
    { id: 'V3', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Vencimento do ICMS não confirmado em algumas UFs',
      onde: 'site/assets/js/ufs.js → campo icms de cada UF',
      verifica: function (c) {
        var pend = c.ufs.lista.filter(function (u) { return !u.obrigacoes[0].validado; }).map(function (u) { return u.sigla; });
        return { resolvida: pend.length === 0, detalhe: pend.length ? pend.length + ' UFs: ' + pend.join(', ') + '.' : 'Todas confirmadas.' };
      } },
    { id: 'V4', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Guia estadual de arrecadação não confirmada',
      onde: 'site/assets/js/ufs.js → guia e guiaValidada',
      verifica: function (c) {
        var pend = c.ufs.lista.filter(function (u) { return !u.guiaValidada; }).map(function (u) { return u.sigla; });
        return { resolvida: pend.length === 0, detalhe: pend.length ? pend.join(', ') + '.' : 'Todas confirmadas.' };
      } },
    { id: 'V5', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Alíquota de referência estimada usada no simulador',
      onde: 'site/assets/js/config.js → simulador.aliquotaReferenciaEstimada; fontes.js → cfg_aliquota_ref',
      descricao: 'O simulador usa uma estimativa de IBS + CBS. Em 31/10/2026, o TCU havia calculado só a CBS de 2027 (11,3468%); falta a resolução do Senado e o cálculo do IBS.',
      verifica: function (c) {
        var f = c.fontes.porId.cfg_aliquota_ref;
        return { resolvida: !!(f && f.validado), detalhe: 'Valor atual: ' + (c.config.simulador.aliquotaReferenciaEstimada * 100).toLocaleString('pt-BR') + '% (estimativa).' };
      } },
    { id: 'V6', categoria: 'validacao', responsavel: 'rt', bloqueia: true, titulo: 'Prazos de retenção da política de privacidade',
      onde: 'site/privacidade.html', descricao: 'Os prazos de 24 meses para leads e 30 dias para opt-in não confirmado são proposta do desenvolvimento e precisam de aprovação. Situação técnica em 03/11/2026: a rotina existe (python tools/lgpd.py retencao, prazos em backend/retencao.py) e apaga os dados sem quebrar a trilha audit_hash, mas ainda não roda sozinha: falta agendá-la junto com a API (T1). Os logs do Cloud Run seguirão a retenção do Cloud Logging, que precisa ser ajustada aos prazos aprovados.' },
    { id: 'V14', categoria: 'validacao', responsavel: 'rt', bloqueia: true, titulo: 'Aprovar a política de privacidade versão 2026-11',
      onde: 'site/privacidade.html; docs/ideias/privacidade-2026-11.md', descricao: 'Texto reescrito em 03/11/2026. O responsável técnico aprova a redação e resolve os trechos com o selo "pendente de validação": enquadramento das transferências internacionais no art. 33 da LGPD; prazos de guarda (V6); autenticação multifator, registro de acessos e local dos dados no portal (C2). Conferir também se os registros de acesso ao site precisam ser guardados pelo prazo do Marco Civil da Internet. Depende também de quem será o encarregado (C4).' },
    { id: 'V15', categoria: 'validacao', responsavel: 'rt', bloqueia: true, titulo: 'Aprovar os documentos internos de proteção de dados',
      onde: 'docs/lgpd/README.md', descricao: 'Rascunhos de 03/11/2026, fora do site: registro das operações, plano de incidentes, atendimento ao titular e lista de operadores. A equipe preenche o que só ela sabe e o responsável técnico aprova. Sustenta o que o site afirma na V12.' },
    { id: 'V7', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Pontos de leitura da lei marcados para revisão',
      onde: 'docs/revisao-tecnica.md', descricao: 'Receita igual a R$ 3,6 milhões, ausência de redução no transporte de cargas, crédito do diesel, limite do LCDPR e orientação comercial do programa de conformidade.' },
    { id: 'V8', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Itens da reforma com consulta antiga (mais de 90 dias)',
      onde: 'site/assets/js/reforma-itens.js → consultadoEm',
      verifica: function (c) {
        var at = c.conteudo.atrasados(c.itens, c.hoje, 90).map(function (i) { return i.id; });
        return { resolvida: at.length === 0, detalhe: at.length ? 'Reconferir: ' + lista(at, 8) + '.' : 'Nenhum item atrasado.' };
      } },
    { id: 'V9', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Vencimento do IBS no calendário fiscal',
      onde: 'site/assets/js/fontes.js → cal_ibs; site/assets/js/calendario.js',
      verifica: function (c) { var f = c.fontes.porId.cal_ibs; return { resolvida: !!(f && f.validado), detalhe: f && f.validado ? 'Conferido.' : 'Sem data confirmada no regulamento do IBS.' }; } },

    // ---------- Implantação técnica
    { id: 'V10', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Conferir as normas da área de Compliance que ainda estão pendentes',
      onde: 'site/assets/js/fontes.js (bloco "Compliance") e site/assets/js/compliance-itens.js',
      descricao: 'Em 01/11/2026 foram conferidos no texto literal oficial: LC nº 225/2026 (arts. 18 e 19), Decreto nº 13.075/2026, Lei nº 9.613/1998 (arts. 9º a 12), Res. CFC nº 1.721/2024 (DOU de 06/05/2024), LGPD (arts. 37, 41, 46, 48 e 52), Res. CD/ANPD nº 2/2022 (no site da ANPD), Lei nº 12.846/2013, Decreto nº 11.129/2022, Lei nº 14.133/2021 (art. 25, § 4º) e Decreto nº 12.304/2024. Faltam: o texto da IN RFB nº 2.295/2025 do Confia no DOU (lido em 01/11/2026 só em cópia não oficial do LegisWeb, já com as INs nº 2.317/2026 e nº 2.328/2026; a IN nº 2.328/2026 não foi aberta), a Res. CD/ANPD nº 2/2022 no DOU (in.gov.br não respondeu) e alterações posteriores a essas datas. Os 15 itens de compliance aguardam revisão técnica (V1).' },
    { id: 'V11', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Revisar os pesos e as faixas do termômetro de conformidade',
      onde: 'site/assets/js/termometro.js (PERGUNTAS[].peso, FAIXAS e REVISAO)',
      descricao: 'O termômetro (compliance/termometro.html) tem 16 perguntas nas quatro frentes, cada uma com fonte. Pesos de 1 a 3 e faixas (em dia a partir de 85%, atenção a partir de 60%) são provisórios. Em produção, o termômetro só aparece depois de REVISAO.status = aprovada.' },
    { id: 'V12', categoria: 'validacao', responsavel: 'rt', bloqueia: true, titulo: 'Confirmar o bloco "Como a ORGATEC cumpre as próprias obrigações"',
      onde: 'site/escritorio/index.html (tools/gerar_paginas.py, função escritorio)',
      descricao: 'Publicado em 01/11/2026 por decisão da direção (C6): o escritório segue a Res. CFC nº 1.721/2024 (cadastro, comunicação ao COAF e declaração de não ocorrência ao CFC até 31/01), trata dados pessoais conforme a LGPD e não emite parecer jurídico. O responsável técnico confirma que essas rotinas existem de fato no escritório antes da produção.' },
    { id: 'V13', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Conferir as normas que faltam para as páginas por público (fases P2 a P5)',
      onde: 'docs/relatorio-publicos-reforma-compliance.md, seção 6',
      descricao: 'Sem essas normas, a página do público não entra no ar (fica "em preparação" em compliance/publicos.html): Res. ANTT nº 5.982/2022; texto vigente da IN do LCDPR e data da DITR de 2026 (P2); texto oficial da Res. CGSN nº 194/2026 (prorrogação da opção do Simples para 2027). Conferidos em 02/11/2026: P6 cashback (arts. 112 a 118 da LC 214), P5 imóveis (arts. 251, 253, 254, 259, 260 e 261 da LC 214), P1 transportador, P2 produtor rural (CAR, ITR, Funrural, NR-31, EUDR), P4 comércio e serviços (arts. 128 a 130 da LC 214, ADCT art. 134; a ST do ICMS não está na LC 214, segue as leis estaduais até 2033) e P3 (art. 517 e Anexo VII da LC 214, LC nº 238/2026, arts. 4º, 21, 26 e 516 da LC 214, notícia oficial do CGSN). Os itens novos dessas fases entram na revisão técnica V1.' },
    { id: 'T1', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, titulo: 'Publicar no Firebase: site no Hosting, API no Cloud Run e banco no Firestore (São Paulo)',
      onde: 'docs/publicacao.md; firebase.json; firestore.rules; tools/preparar_firebase.py', descricao: 'Pacote pronto e testado em 31/10/2026: repositório Firestore com a mesma trilha audit_hash (contrato no emulador, 12 envios simultâneos), imagem Docker gravando no emulador, rewrite /api/** para o Cloud Run em southamerica-east1, regras que negam acesso pelo navegador. Em 31/10/2026: projeto orgatec-site criado na conta da ORGATEC, Firestore em southamerica-east1 com regras fechadas, site publicado em homologação em https://orgatec-site.web.app (formulários pelo WhatsApp). Falta ativar o faturamento (Blaze; a conta de faturamento está fechada) para publicar a API no Cloud Run e ligar os formulários. Em 01/11/2026: quem abre o faturamento é Warley Moreira Veloso ou Robson Alain Veloso, com cartão de crédito, na conta orgatec.cloud@gmail.com (projeto orgatec-site).' },
    { id: 'T2', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, titulo: 'Envio real do e-mail de confirmação do opt-in', depende: ['C3'],
      onde: 'backend/app.py → /api/optin', descricao: 'Hoje os links de confirmação e de descadastro não são enviados a ninguém: o banco guarda só o hash dos tokens. O serviço de envio precisa mandar o link de confirmação e, em toda mensagem, o de descadastro (/api/optin/sair). Em 01/11/2026 a ORGATEC pediu lançamento completo, então os alertas por e-mail entram na produção. Falta escolher o provedor de e-mail transacional e publicar SPF, DKIM e DMARC no DNS da Hostinger (requisitos em docs/respostas-roteiro-2026-11-01.md).' },
    { id: 'T3', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, resolvida: true, titulo: 'Trocar o Tailwind via CDN pelo CSS compilado',
      onde: 'tools/compilar_css.py → site/assets/css/tailwind.css', descricao: 'Concluída em 31/10/2026: CSS compilado (22 KB) a partir de tailwind.config.js, gerado de tokens.json; nenhuma página usa o CDN; scripts embutidos movidos para arquivos; a CSP passou a aceitar só scripts do próprio site (sem unsafe-inline).' },
    { id: 'T4', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, resolvida: true, titulo: 'Servir as fontes do site localmente',
      onde: 'tools/baixar_fontes.py → site/assets/fontes/', descricao: 'Concluída em 02/11/2026: as fontes do design ORGATEC Trilha (Bricolage Grotesque, Sora, Source Sans 3, IBM Plex Sans e IBM Plex Mono) e as da marca e do design system (Inter e JetBrains Mono) vêm do próprio site (8 arquivos woff2, 244 KB, subconjunto latin). A CSP deixou de liberar fonts.googleapis.com e fonts.gstatic.com, e a política de privacidade foi atualizada. Só o arquivo avulso do design system (dist/) continua usando o Google Fonts.' },
    { id: 'T5', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, titulo: 'DNS, CNAME e certificado de portal.orgatec.io', depende: ['C2'],
      onde: 'Hostinger (hPanel) → DNS de orgatec.io', descricao: 'O DNS de orgatec.io é administrado na Hostinger (resposta de 01/11/2026). O CNAME de portal.orgatec.io depende do alvo que a Athenas Online informar (C2). Em 01/11/2026 portal.orgatec.io não tinha registro na Hostinger. Com o CNAME e o certificado no ar, trocar config.js → portal.url e tools/layout.py → PORTAL_URL para https://portal.orgatec.io.' },
    { id: 'T13', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, titulo: 'Ligar orgatec.io ao Firebase Hosting, com certificado',
      onde: 'Console do Firebase → Hosting → domínio personalizado; Hostinger (hPanel) → DNS de orgatec.io',
      descricao: 'Atualizado em 01/11/2026, à tarde: orgatec.io JÁ aponta para o Hosting (TXT hosting-site=orgatec-site e registro A do Firebase na Hostinger) e responde em HTTPS com certificado, ainda em homologação (noindex). Falta www.orgatec.io: o DNS aponta para o domínio, mas o Firebase não tem o www cadastrado, então a conexão HTTPS falha; adicione www.orgatec.io no console do Firebase como redirecionamento para orgatec.io e ajuste na Hostinger o registro que o console pedir. Antes disso, o site respondia só em orgatec-site.web.app. Caminho: adicionar o domínio no console do Firebase e copiar para a Hostinger os registros TXT e A que o console mostrar; o certificado é emitido pelo Firebase depois da propagação. Passo a passo em docs/respostas-roteiro-2026-11-01.md.' },
    { id: 'T6', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Testes em Safari, Firefox e aparelhos reais (iPhone e Android)',
      onde: 'tests/ROTEIRO-QA.md, roteiro manual; ORGATEC_NAVEGADOR=firefox|webkit python -m pytest tests/e2e', descricao: 'Desde 02/11/2026 a suíte automática roda também no Firefox e no WebKit (motor do Safari), com os mesmos testes do Chromium. No WebKit, o Tab pula links por padrão (preferência do Safari), então o primeiro foco da abertura é conferido só no Chromium e no Firefox. Falta o roteiro manual em aparelhos reais (iPhone com Safari e Android com Chrome).' },
    { id: 'T7', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Incluir o setor de transporte no simulador',
      onde: 'site/assets/js/regras.js → SETORES', descricao: 'Exige regras com fonte para carga e passageiros (LC 214, arts. 169, 180 e 284 a 287).' },
    { id: 'T8', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Republicar o design system orgatec-template2 no Claude',
      onde: 'design-system/orgatec-template2/', descricao: 'Em 02/11/2026 foram republicados no design system do Claude (artefato orgatec-template2) o selo "vigência futura" (tom futuro), os estilos do cartão de item da reforma (og-item) e a regra do símbolo com as cores originais. Falta o componente do cartão de item da reforma: hoje ele existe só no site (reforma-itens.js), e o bundle do design system tem apenas o CSS.' },
    { id: 'T10', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Logotipo em vetor fiel ao original',
      onde: 'fontes-marca/orgatec-logo-original.jpg; tools/extrair_logo_original.py; site/marca.html',
      descricao: 'O site usa o símbolo extraído da imagem original (PNG de 313 × 346 px, sem redesenho). Ele fica nítido até cerca de 300 px. Para impressão, fachada e para refazer as assinaturas e ícones do manual de marca, enviar o arquivo vetorial original (AI, SVG ou PDF). As versões vetoriais atuais do manual são uma reconstrução e diferem do original.' },
    { id: 'V20', categoria: 'validacao', responsavel: 'rt', bloqueia: false, titulo: 'Validar os critérios agronômicos da Janela de Campo',
      onde: 'site/assets/js/campo-regras.js (LIMITES e CRITERIOS)',
      descricao: 'Pulverização (vento 3 a 10 km/h, abaixo de 30 °C, umidade acima de 55%, sem chuva nas 2 h seguintes), ITU 72 e 79 para animais e os limites de chuva e vento de plantio, colheita e máquinas aparecem no site como pendentes de validação. Um agrônomo ou o responsável técnico confere, ajusta e marca validado: true.' },
    { id: 'T20', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Levar o boletim automático para o Cloud Scheduler', depende: ['T1'],
      onde: 'tools/gerar_boletim_campo.py (mesmo script) + Cloud Run job + Cloud Scheduler',
      descricao: 'Hoje o boletim é gerado no PC pelo Agendador de Tarefas do Windows (05h, 11h e 17h) e só roda com o computador ligado. Com o faturamento Blaze ativo, o mesmo script roda na nuvem.' },
    { id: 'D21', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Pedir ao CEPEA autorização para usar as cotações fora do widget',
      onde: 'tools/agro_fontes.json (cepea.autorizacao) e cepea@usp.br',
      descricao: 'Os cards Orgatec Audi Agro mostram as cotações pelo widget oficial do CEPEA, o único uso que a política de direitos autorais dele libera sem autorização (dados sob CC BY-NC 4.0). Com autorização formal, o site pode guardar o último valor válido (aviso de cache quando o CEPEA cair), usar o RSS do CEPEA nas notícias e o indicador mensal do leite.' },
    { id: 'D22', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Cotações da B3 (boi, milho, soja e café futuros)',
      onde: 'contrato de market data com a B3',
      descricao: 'A difusão das cotações da B3 exige consentimento por escrito, em contrato (política de market data em vigor desde 01/11/2026). Sem contrato, os cards não mostram B3.' },
    { id: 'D23', categoria: 'decisao', responsavel: 'orgatec', bloqueia: false, titulo: 'Conferir os termos de reprodução das agências Câmara e Senado',
      onde: 'tools/agro_fontes.json (feeds)',
      descricao: 'Os cards mostram só título, data e link das notícias das agências da Câmara e do Senado. Os termos de reprodução delas não foram conferidos; os da Receita (gov.br) são CC BY-ND 3.0. Confirme antes da produção.' },
    { id: 'T11', categoria: 'tecnico', responsavel: 'dev', bloqueia: true, titulo: 'Calibrar a posição do IP do visitante no Cloud Run',
      onde: 'Cloud Run → ORGATEC_IP_POSICAO e ORGATEC_DIAGNOSTICO_IP', depende: ['T1'],
      descricao: 'O Firebase Hosting não documenta em que posição do X-Forwarded-For o IP do visitante chega. Na homologação, ler o log diagnostico-ip, fixar ORGATEC_IP_POSICAO e desligar o diagnóstico. Sem isso, o limite de envios por visitante pode ser contornado ou valer para todos juntos.' },
    { id: 'T12', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Segurança dos sistemas antes de ligar o botão "Entrar" (Fase 0 do plano)',
      onde: 'docs/plano-incorporacao-produtos.md, Fase 0 (documento interno); depois site/assets/js/config.js → solucoes.<id>.situacao = disponivel',
      descricao: 'Nenhum sistema tem link público hoje. Antes de ligar qualquer um, a ORGATEC conclui a revisão de segurança da Fase 0. Os detalhes ficam só no documento interno: este painel é público.' },
    { id: 'T9', categoria: 'tecnico', responsavel: 'dev', bloqueia: false, titulo: 'Virar o site para produção',
      onde: "site/assets/js/config.js → ambiente: 'producao'", depende: ['todas as que bloqueiam'],
      verifica: function (c) { return { resolvida: c.config.ambiente === 'producao', detalhe: 'Ambiente atual: ' + c.config.ambiente + '.' }; } }
  ];

  /* ctx: { config, fontes, itens, ufs, conteudo, hoje (AAAA-MM-DD), resolvidaManual: [ids] } */
  function avaliar(ctx) {
    var manual = ctx.resolvidaManual || [];
    var itens = PENDENCIAS.map(function (p) {
      var feita = manual.indexOf(p.id) >= 0 || p.resolvida === true;
      var r = { resolvida: feita, detalhe: feita ? 'Marcada como resolvida.' : null, automatica: false };
      if (p.verifica) {
        try { r = p.verifica(ctx); r.automatica = true; }
        catch (e) { r = { resolvida: false, detalhe: 'Não foi possível verificar: ' + e.message, automatica: true, erro: true }; }
      }
      return Object.assign({}, p, { verifica: undefined, status: r.resolvida ? 'resolvida' : 'aberta', detalhe: r.detalhe, automatica: r.automatica, erro: !!r.erro });
    });
    var abertas = itens.filter(function (i) { return i.status === 'aberta'; });
    var bloqueios = abertas.filter(function (i) { return i.bloqueia; });
    return { itens: itens, resumo: { total: itens.length, abertas: abertas.length, resolvidas: itens.length - abertas.length,
      bloqueios: bloqueios.length, prontoParaProducao: bloqueios.length === 0 } };
  }

  /* Texto para copiar ou exportar (Markdown). */
  function comoTexto(av, dataRef) {
    var linhas = ['# Pendências para a próxima fase', '', 'Gerado em ' + dataRef + ' a partir de site/assets/js/homologacao.js.', '',
      '- Abertas: ' + av.resumo.abertas + ' de ' + av.resumo.total, '- Bloqueiam a produção: ' + av.resumo.bloqueios, ''];
    Object.keys(CATEGORIAS).forEach(function (cat) {
      var grupo = av.itens.filter(function (i) { return i.categoria === cat; });
      linhas.push('## ' + CATEGORIAS[cat], '', '| ID | Pendência | Status | Bloqueia produção | Responsável | Onde resolver | Situação |', '|---|---|---|---|---|---|---|');
      grupo.forEach(function (i) {
        linhas.push('| ' + [i.id, i.titulo, i.status, i.bloqueia ? 'sim' : 'não', RESPONSAVEL[i.responsavel], '`' + i.onde + '`',
          (i.detalhe || i.descricao || '') + (i.depende && i.depende.length ? ' Depende de: ' + i.depende.join(', ') + '.' : '')].join(' | ').replace(/\n/g, ' ') + ' |');
      });
      linhas.push('');
    });
    return linhas.join('\n');
  }

  /* Autoteste dos módulos no navegador e no Node: entradas conhecidas → resultado esperado. */
  function autoteste(O, hoje) {
    var casos = [];
    function caso(nome, fn) {
      try { var r = fn(); casos.push({ nome: nome, ok: r === true || (r && r.ok), detalhe: r && r.detalhe || '' }); }
      catch (e) { casos.push({ nome: nome, ok: false, detalhe: e.message }); }
    }
    caso('Módulos carregados', function () {
      var faltam = ['config', 'fontes', 'ufs', 'regras', 'conteudo', 'reformaItens', 'calculadoras'].filter(function (m) { return !O[m]; });
      return { ok: !faltam.length, detalhe: faltam.length ? 'Faltam: ' + faltam.join(', ') : '7 módulos' };
    });
    caso('Modo teste ativo (homologação)', function () { return { ok: O.config.ambiente === 'homologacao', detalhe: 'ambiente = ' + O.config.ambiente }; });
    caso('Itens da reforma válidos e com fonte', function () {
      var r = O.conteudo.publicaveis(O.reformaItens, O.fontes.porId, 'homologacao');
      return { ok: !r.rejeitados.length, detalhe: r.itens.length + ' válidos, ' + r.rejeitados.length + ' rejeitados' };
    });
    caso('Produção esconde itens sem revisão', function () {
      var p = O.conteudo.publicaveis(O.reformaItens, O.fontes.porId, 'producao').itens;
      var aprovados = O.reformaItens.filter(function (i) { return i.revisao && i.revisao.status === 'aprovada'; }).length;
      return { ok: p.length === aprovados, detalhe: p.length + ' visíveis em produção, ' + aprovados + ' aprovados' };
    });
    caso('27 UFs cadastradas', function () { return { ok: O.ufs.lista.length === 27, detalhe: O.ufs.lista.length + ' UFs' }; });
    caso('Simulador: Simples em GO, R$ 1,2 milhão', function () {
      var r = O.regras.simular({ setor: 'servicos', regime: 'simples', perfil: 'b2b', uf: 'GO', faturamento: 1200000, comprasPct: 0.2 });
      return { ok: !r.erros.length && r.alertas.length > 0, detalhe: r.alertas.length + ' alertas' };
    });
    caso('Transição: 2030 mantém 80% do ICMS/ISS', function () {
      var r = O.calculadoras.transicaoAno(2030, 1000000);
      return { ok: r.icmsIssRestante === 800000, detalhe: 'R$ ' + r.icmsIssRestante };
    });
    caso('Produtor: R$ 3,2 milhões não é contribuinte', function () { return O.calculadoras.produtorRural({ receita: 3200000 }).contribuinte === false; });
    caso('Produtor: R$ 3,6 milhões passa a contribuinte', function () { return O.calculadoras.produtorRural({ receita: 3600000 }).contribuinte === true; });
    caso('Anos de atuação ocultos sem comprovação', function () {
      var a = O.conteudo.anosAtuacao(O.config.institucional, hoje);
      var inst = O.config.institucional || {};
      return { ok: (inst.inicioAtuacao && inst.comprovacao) ? a !== null : a === null, detalhe: a === null ? 'oculto' : a + ' anos' };
    });
    if (O.calendario) caso('Calendário: dezembro de 2026 tem 13º salário', function () {
      var l = O.calendario.obrigacoesDoMes(2026, 12, { uf: 'GO', regime: 'presumido' });
      return { ok: l.some(function (o) { return o.id === 'decimo2'; }), detalhe: l.length + ' obrigações' };
    });
    if (O.validadores) caso('Validador: CNPJ do escritório', function () { return O.validadores.cnpjValido('13.155.211/0001-45'); });
    return casos;
  }

  return { CATEGORIAS: CATEGORIAS, RESPONSAVEL: RESPONSAVEL, PENDENCIAS: PENDENCIAS, avaliar: avaliar, comoTexto: comoTexto, autoteste: autoteste };
});
