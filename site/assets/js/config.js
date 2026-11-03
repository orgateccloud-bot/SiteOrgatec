/* =============================================================================
   CONFIGURAÇÃO ÚNICA DO SITE ORGATEC
   -----------------------------------------------------------------------------
   Todas as decisões em aberto do Plano Diretor Digital (Quadro de Validação,
   itens 1 a 4) ficam AQUI. Nenhuma foi decidida: os valores padrão são `null`
   ou `false`, e a interface mostra "pendente de definição" enquanto for assim.
   Depois de editar, recarregue a página; não há build.
   ============================================================================= */
(function (root) {
  var config = {

    /* Ambiente. 'homologacao' exibe uma faixa com as pendências abaixo no topo do
       site; troque para 'producao' quando todas estiverem resolvidas. */
    ambiente: 'homologacao',

    /* ---------------------------------------------------------------------------
       PENDÊNCIA 1 — Ferramenta de captura de XML (Plano Diretor, item 1)
       Valores aceitos: 'sieg' | 'arquivei' | 'omie' | null (não definido)
       --------------------------------------------------------------------------- */
    capturaXml: {
      ferramenta: null,
      opcoes: {
        sieg: { nome: 'SIEG' },
        arquivei: { nome: 'Arquivei' },
        omie: { nome: 'Omie' }
      }
    },

    /* ---------------------------------------------------------------------------
       PENDÊNCIA 2 — ERP de destino do CNAME de portal.orgatec.io (Plano Diretor, item 2)
       Valores aceitos: 'athenas' | 'onvio' | 'alterdata' | 'acessorias' | null (não definido)
       ERP definido em 01/11/2026: Athenas Online (instância orgatec.athenas.online).
       `cnameAlvo`: preencha com o host que a Athenas confirmar para o domínio próprio
       (com certificado). Enquanto estiver `null`, `url` aponta direto para o login do
       Athenas Online, porque portal.orgatec.io ainda não existe no DNS (T5). Com o
       CNAME e o certificado no ar, troque `url` para 'https://portal.orgatec.io'.
       --------------------------------------------------------------------------- */
    portal: {
      url: 'https://orgatec.athenas.online/Usuarios/login',
      erp: 'athenas',
      cnameAlvo: null,
      opcoes: {
        athenas: { nome: 'Athenas Online' },
        onvio: { nome: 'Onvio / Domínio (Thomson Reuters)' },
        alterdata: { nome: 'Alterdata' },
        acessorias: { nome: 'Acessórias' }
      }
    },

    /* ---------------------------------------------------------------------------
       PENDÊNCIA 3 — E-mails institucionais (Plano Diretor, item 3)
       Enquanto `ativo: false`, o endereço NÃO aparece no site e os formulários
       informam que o retorno será pelo WhatsApp.
       --------------------------------------------------------------------------- */
    emails: {
      contato: { endereco: 'contato@orgatec.io', ativo: false },
      dpo: { endereco: 'dpo@orgatec.io', ativo: false }
    },

    /* ---------------------------------------------------------------------------
       PENDÊNCIA 4 — WhatsApp oficial (Plano Diretor, item 4)
       Os CTAs continuam apontando para este número; `validado: false` apenas
       mantém o item na faixa de pendências do ambiente de homologação.
       --------------------------------------------------------------------------- */
    whatsapp: {
      numeroE164: '5562992949161',
      exibicao: '+55 (62) 99294-9161',
      validado: false
    },

    /* ---------------------------------------------------------------------------
       TRAJETÓRIA (anos de atuação) — DEPENDE DE COMPROVAÇÃO
       O número de anos só aparece no site quando os DOIS campos estiverem
       preenchidos: `inicioAtuacao` (AAAA-MM-DD) e `comprovacao` (o documento que
       sustenta a data: ex. contrato social do escritório antecessor, registro do
       fundador no CRC). O CNPJ atual e o CRC-TO não servem de base para 51 anos
       (o Tocantins foi criado em 1988). Enquanto vazio, o site mostra CRC e
       responsável técnico.
       --------------------------------------------------------------------------- */
    institucional: {
      inicioAtuacao: null,
      comprovacao: null
    },
    /* ---------------------------------------------------------------------------
       TELA DE ABERTURA (site/abertura.html)
       Destinos dos botões: caminho a partir da raiz do site ou URL completa (https://...).
       `entrada` é o botão principal e leva ao eixo do site, a área tributária.
       O WhatsApp usa o número de `whatsapp` acima; os anos de atuação, `institucional`.
       --------------------------------------------------------------------------- */
    /* ---------------------------------------------------------------------------
       SOLUÇÕES (sistemas da ORGATEC) — docs/plano-incorporacao-produtos.md
       O site só faz LINK para cada sistema; nunca embute nem chama a API dele.
       situacao: 'disponivel' (mostra o botão "Entrar", exige `url` https),
                 'demonstracao' (só pedido de demonstração), 'servico' (serviço do escritório,
                 sem acesso direto), 'em_breve' (lista de interesse), 'rascunho' (fora do site).
       Antes de passar qualquer uma para 'disponivel': Fase 0 do plano (segurança do sistema)
       e domínio próprio (decisão D3).
       --------------------------------------------------------------------------- */
    solucoes: {
      conciliacao: { situacao: 'demonstracao', url: null },       // OrgConc
      auditoriaRural: { situacao: 'servico', url: null },         // OrgAudi (interno)
      gestaoFinanceira: { situacao: 'em_breve', url: null },      // Mini
      credito: { situacao: 'rascunho', url: null }                // OrgCred (decisão D5)
    },
    /* Tela de abertura (raiz): `entrada` é o botão "Entrar no site" (a vitrine, que reúne todas as áreas);
       as demais chaves são os atalhos do cartão. */
    abertura: {
      entrada: 'inicio.html',
      tributario: 'tributario/index.html',
      solucoes: 'solucoes/index.html',
      areaCliente: 'cliente/index.html',
      simuladores: 'ferramentas/index.html',
      noticias: 'reforma/index.html#noticias'
    },

    /* ---------------------------------------------------------------------------
       API DOS FORMULÁRIOS (backend/app.py)
       - publica: endereço da API quando o site está no Firebase Hosting ou em orgatec.io.
         '' = mesma origem (o Hosting encaminha /api/** para o Cloud Run);
         'https://...' = API em outro domínio (ex.: Railway);
         null = sem API: os formulários caem no WhatsApp, sem dados pessoais na URL.
         Preenchido por tools/preparar_firebase.py.
       - base: calculado abaixo (resolverApiBase). Em qualquer outro endereço (localhost,
         Docker, Railway servindo o site) a API está na mesma origem ('').
       --------------------------------------------------------------------------- */
    api: { publica: null, base: '' },

    /* Parâmetro do simulador. As alíquotas de referência do IBS e da CBS ainda não
       foram fixadas, por isso este valor é uma ESTIMATIVA editável e aparece marcado
       como "pendente de validação" na interface. Referências conferidas em 30/10/2026:
       NT SERT/MF de 01/07/2024 = 26,47%; NT de 23/08/2024 = +1,47 p.p. pelas mudanças
       da Câmara. Em 28/10/2026 o TCU calculou só a CBS de 2027 (11,3468%).
       Os 26,5% do art. 475 da LC 214 são gatilho de avaliação (dados de 2030), não teto. */
    simulador: {
      aliquotaReferenciaEstimada: 0.28,
      rotuloEstimativa: 'Estimativa de referência IBS + CBS (pendente de validação)'
    },

    /* Versão da política de privacidade registrada junto de cada consentimento. */
    lgpd: { versaoPolitica: '2026-10' }
  };

  /* Hospedagens só estáticas (sem a API na mesma origem): Firebase Hosting e o domínio final. */
  var ESTATICOS = [/\.web\.app$/, /\.firebaseapp\.com$/, /^(www\.)?orgatec\.io$/];
  function resolverApiBase(host, api) {
    var estatico = ESTATICOS.some(function (r) { return r.test(String(host || '').toLowerCase()); });
    // publica: null = sem API (WhatsApp); '' = mesma origem (rewrite do Firebase Hosting para o Cloud Run)
    return estatico ? (api.publica == null ? null : String(api.publica).replace(/\/+$/, '')) : '';
  }
  config.resolverApiBase = resolverApiBase;
  config.api.base = resolverApiBase(root && root.location ? root.location.hostname : '', config.api);

  if (typeof module === 'object' && module.exports) module.exports = config;
  else (root.Orgatec = root.Orgatec || {}).config = config;
})(this);
