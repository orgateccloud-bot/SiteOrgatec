# Plano de desenvolvimento: área de Compliance

**Data:** 01/11/2026. **Situação:** fases A a D implementadas em 01/11/2026.
- **Páginas:** visão geral; termômetro (16 perguntas, só no navegador); conformidade tributária; PLD/FT; LGPD; integridade.
- **Calendário fiscal:** esfera "Compliance".
- **Normas:** conferidas no texto literal oficial, exceto a IN do Confia e a Res. CD/ANPD 2/2022 no DOU (pendência V10).
- **Decisões C1 a C6 tomadas em 01/11/2026** (seção 8): nome "Compliance", quatro frentes, grupo próprio no menu, entrega sem parecer jurídico, termômetro oculto em produção até a revisão técnica e o bloco "Como a ORGATEC cumpre as próprias obrigações" publicado na página Escritório (confirmação do responsável técnico na pendência V12).
- **Acréscimos de 01/11/2026 (tarde):**
  - perguntas frequentes nas páginas da área, tiradas do campo `pergunta` dos itens; a resposta é o próprio fato, com fonte;
  - barra de resumo do termômetro no celular;
  - cartão do termômetro em Ferramentas e links na vitrine e na página Escritório;
  - a IN RFB 2.295/2025 do Confia foi lida em cópia não oficial (LegisWeb): a adesão segue critérios quantitativos e qualitativos, e as vagas saem por portaria a cada edição.
- **Correção encontrada na conferência:** a comunicação de não ocorrência dos contadores vai ao **CFC**, até 31/01 (Res. CFC 1.721/2024, art. 7º), e não ao COAF.

**Ponto de partida:** a pendência D3 ("Escopo de auditoria e compliance") pedia escolher entre "só documento", "1 ou 2 serviços na página Tributário" e "seção própria". A decisão agora é **seção própria**. Este plano detalha como montá-la sem tirar o foco do eixo tributário. As 9 ideias avaliadas estão em `docs/decisao-auditoria-compliance.md`.

## 1. O que é a área

Compliance, aqui, é **a empresa cumprir as regras antes de ser cobrada**. A área é organizada em quatro frentes, na ordem de proximidade com o que a ORGATEC já faz:

| # | Frente | Para quem (perfil do site) | Liga com o eixo tributário? | Situação da base legal |
|---|---|---|---|---|
| 1 | **Conformidade tributária** | Lucro real, transporte, agro, produtor com LCDPR | **É o eixo**: programa de conformidade de 2026, documentos fiscais com IBS e CBS, programas da Receita | Em parte conferida (ver seção 3) |
| 2 | **Prevenção à lavagem de dinheiro (PLD/FT)** | Clientes que a lei obriga a comunicar ao COAF, e a própria ORGATEC como escritório contábil | Indireta: fiscalização cruzada e movimentação em espécie | A conferir |
| 3 | **Proteção de dados (LGPD) para empresas** | Pequenas e médias empresas clientes | Fraca. Entra porque o escritório já trata dados fiscais de clientes e conhece o tema | A conferir |
| 4 | **Integridade e anticorrupção** | Transportadoras e fornecedores com contratos públicos | Fraca; é a última fase | A conferir (há indício de norma mais nova) |

**Fora da área, por ora** (como já recomendado em `decisao-auditoria-compliance.md`):
- jornada do motorista e eSocial (ideia 7);
- monitor automático de certidões, que exige integração com e-CAC, SEFAZ e Caixa (ideia 8).

**Regra que não muda:** toda afirmação legal cita uma fonte de `fontes.js`. Fonte não conferida na publicação oficial aparece com o selo "pendente de validação". Em produção, só vão ao ar os itens com revisão técnica aprovada.

## 2. Estrutura (navegação e páginas)

```
Compliance ▾                                   compliance/
├── Visão geral e termômetro                   compliance/index.html
├── Conformidade tributária                    compliance/conformidade-tributaria.html   (Fase A)
├── Termômetro de conformidade (ferramenta)    compliance/termometro.html               (Fase B)
├── Prevenção à lavagem de dinheiro            compliance/prevencao-lavagem.html        (Fase C)
├── Proteção de dados (LGPD)                   compliance/protecao-de-dados.html        (Fase C)
└── Integridade e anticorrupção                compliance/integridade.html              (Fase D)
```

- **Menu:** o grupo "Compliance ▾" entra depois de "Soluções". Hoje o menu tem 6 itens e cabe no limite do desktop (1280 px). Com 7, é preciso medir. Se não couber, há duas saídas (decisão C3):
  - "Escritório" sai do menu principal e fica no rodapé e no menu ☰;
  - "Compliance" entra como grupo dentro de "Consultoria".
- **Ligações com o que já existe:**
  - O item "Programa Nacional de Conformidade Tributária 2026" (`reforma-itens.js`, `conformidade-2026`) e o de documentos fiscais (`documentos-fiscais`) passam a aparecer também na página de conformidade, pelo campo `destinos`. Não são duplicados.
  - As páginas de Soluções (conciliação e auditoria rural) entram na área como "como a ORGATEC verifica". Continuam só com link, sem acesso aos sistemas.
  - A **página Escritório** ganha o bloco "Como a ORGATEC cumpre as próprias obrigações": PLD/COAF como escritório contábil e LGPD com encarregado (DPO). Depende da decisão C6.
  - A **tela de abertura** não muda nesta área; o botão principal continua levando à área tributária.

## 3. Bases legais (situação em 01/11/2026)

| Fonte (id proposto em `fontes.js`) | Norma | Situação |
|---|---|---|
| `ato_conjunto_5_2026` (já existe) | Ato Conjunto RFB/CGIBS nº 5/2026, Programa Nacional de Conformidade Tributária de 2026 (LC 214, arts. 471-A a 471-C) | Já no site |
| `ato_conjunto_4_2026` (já existe) | Ato Conjunto RFB/CGIBS nº 4/2026, campos de IBS/CBS obrigatórios em CT-e, MDF-e e NF-e | Já no site |
| `lc225_2026` | LC nº 225/2026, que segundo resumo da Receita incorporou os programas Confia, Sintonia e OEA | **A conferir** no Planalto: artigos e alcance |
| `in_rfb_2295_2025` | IN RFB nº 2.295/2025 (Confia), alterada pela IN RFB nº 2.317/2026 | **A conferir** no portal de normas da Receita; 1ª edição com adesão até 20/03/2026 (já encerrada) |
| `lei9613` | Lei nº 9.613/1998 (lavagem de dinheiro), arts. 9º a 11 (pessoas obrigadas e comunicações) | **A conferir** no Planalto |
| `res_cfc_1721_2024` | Resolução CFC nº 1.721/2024 (PLD/FT para profissionais da contabilidade; revogou a Res. CFC nº 1.530/2017; DOU de 06/05/2024, vigência em 03/06/2024) | **A conferir** no texto oficial (o COAF publica o PDF), inclusive o prazo atual da comunicação de não ocorrência |
| `lei13709` | Lei nº 13.709/2018 (LGPD) | **A conferir**: artigos a citar |
| `res_anpd_2_2022` | Resolução CD/ANPD nº 2/2022 (agentes de tratamento de pequeno porte; dispensa de encarregado e registro simplificado, com exceção para tratamento de alto risco) | **A conferir** no site da ANPD: vigência e alterações |
| `lei12846` / `dec11129` | Lei nº 12.846/2013 e Decreto nº 11.129/2022, arts. 56 e 57 (programa de integridade) | **A conferir**: há indício de que o Decreto nº 12.304/2024 trata de parâmetros de integridade em contratações públicas |
| Decreto nº 13.075/2026 | Documento fiscal do produtor PF a partir de 2027, citado como "conferido" em `decisao-auditoria-compliance.md` | **Não está em `fontes.js`**: cadastrar e conferir |

Todas as fontes novas entram com `validado: false`. O selo "pendente de validação" aparece no site até o responsável técnico conferir cada uma (pendência V2).

## 4. Conteúdo como dados (reaproveita o que já funciona)

- **`site/assets/js/compliance-itens.js`:** mesmo formato de `reforma-itens.js`:
  - `fato` só com o que está na norma;
  - `orientacao` separada e identificada como leitura da ORGATEC;
  - `status`, `fontes`, `consultadoEm` e `revisao`.
- **Mudança de esquema:** o campo novo `pilar` (`tributario | pld | lgpd | integridade`) faz o papel de `tributos` nos itens que não são tributo.
  - O `conteudo.js` passa a aceitar `pilar` quando `tributos` estiver vazio.
  - Entram os destinos `compliance-*` na lista `DESTINOS`.
  - O mesmo `renderItem` e o mesmo filtro de produção (só itens aprovados) valem para os dois arquivos.
- **Testes JS:**
  - todo item de compliance tem fonte existente e `pilar` válido;
  - nenhum item `aprovada` aponta para fonte `validado: false`;
  - em produção, sem revisão, a página mostra "aguardando revisão técnica".

## 5. Layout

### Visão geral (`compliance/index.html`)
1. **Herói:** "Cumprir antes de ser cobrado." e uma frase. CTA principal "Fazer o termômetro de conformidade"; secundário "Falar com o escritório".
2. **As quatro frentes:** um cartão por frente, com ícone, "para quem" e selo de situação. As frentes ainda sem página levam o selo "em preparação" e não têm link.
3. **O que vence agora:** os itens com prazo próximo (ex.: correção de inconsistências do programa de 2026 até 31/12/2026), puxados de `compliance-itens.js` e `reforma-itens.js` pela data, com fonte.
4. **Como a ORGATEC verifica:** marcos (levantamento → cruzamento → relatório → acompanhamento), com link para as páginas de Soluções.
5. **Perguntas frequentes** (respostas tiradas dos itens, como na vitrine) e **faixa de diagnóstico**.

### Página de frente (modelo único, função `pilar()` no gerador)
1. **Herói:** o que a regra exige, em uma frase, com o CTA.
2. **Para quem:** cartões de público. Na PLD, quem a lei obriga, em texto conferido na Lei nº 9.613/1998.
3. **O que a lei exige:** os itens de `compliance-itens.js` daquela frente, com fonte, status e data de consulta.
4. **Como a ORGATEC ajuda:** passos do serviço. Só o que o escritório de fato entrega (decisão C4).
5. **Ferramenta:** chamada para o termômetro, filtrado pela frente.
6. **Perguntas frequentes** e **faixa final**.

### Termômetro de conformidade (`compliance/termometro.html`)
- **Funcionamento:** questionário de 10 a 15 perguntas por frente, que roda **só no navegador**; nenhuma resposta sai do aparelho.
- **Perguntas:** cada uma traz a fonte legal ao lado. Exemplos: "Os CT-e emitidos desde 03/08/2026 trazem os campos de IBS e CBS?" (Ato Conjunto nº 4/2026); "Você conferiu as inconsistências apontadas para o programa de 2026?" (Ato Conjunto nº 5/2026).
- **Resultado:** nível (em dia, atenção, risco), a lista do que corrigir com a fonte de cada ponto e o CTA de diagnóstico. **Não** mostra probabilidade de autuação nem valores, porque não há base para isso.
- **Motor:** `site/assets/js/termometro.js`, puro e testável no Node, como `regras.js`. Pesos e faixas ficam num objeto revisado pelo responsável técnico (decisão C5).
- **Envio do resultado:** opcional, pela API do site, com consentimento LGPD e o campo `produto: 'compliance'`. Funciona depois do Cloud Run (pendência T1); até lá, pelo WhatsApp, com uma mensagem que não leva as respostas.

**Visual:** design ORGATEC Trilha, com os componentes que já existem (folhas, marcos, cartões, selos, FAQ). Um ícone em SVG próprio para cada frente. Nenhuma biblioteca nova, e a CSP continua só com scripts próprios.

## 6. Organização do código (para não colidir com as outras sessões)

As outras sessões vinculadas também editam `layout.py`, `gerar_paginas.py`, `config.js`, `fontes.js` e `homologacao.js`. Para reduzir conflito:
- **Gerador próprio:** as páginas da área ficam em **`tools/paginas_compliance.py`**, que reaproveita `pagina()`, `secao()` e os demais blocos de `gerar_paginas.py`. O `main()` de `gerar_paginas.py` ganha só a chamada `paginas_compliance.gerar()`.
- **Arquivos novos só desta área:** `compliance-itens.js`, `termometro.js` e `compliance.js` (ligações de tela).
- **Edições pequenas e localizadas nos arquivos compartilhados:**
  - uma entrada no `NAV`;
  - fontes novas num bloco comentado de `fontes.js`;
  - pendências num bloco próprio de `homologacao.js`.
- **Antes de cada fase:** conferir se há outra sessão ativa e regenerar tudo, para que a última geração não apague a página de outra.

## 7. Fases

### Fase A: fundação e conformidade tributária
1. Cadastrar as fontes da seção 3 (`validado: false`) e o Decreto nº 13.075/2026.
2. Criar `compliance-itens.js` com os itens da frente tributária, o campo `pilar` e os testes de esquema.
3. Criar `tools/paginas_compliance.py`: visão geral e página de conformidade tributária. As outras frentes aparecem como "em preparação", sem link.
4. Grupo "Compliance" no menu (medir o espaço; decisão C3), mapa de páginas e pendências.
5. Testes e2e:
   - páginas sem rolagem lateral e sem erro;
   - itens com fonte;
   - em produção, sem itens aprovados, a página mostra o aviso de revisão;
   - nenhuma frente "em preparação" com link.

### Fase B: termômetro de conformidade
1. Motor `termometro.js` com perguntas da frente tributária, cada uma com fonte, e testes no Node (pontuação, faixas, toda pergunta com fonte existente).
2. Página do termômetro: resultado com lista de correções e o CTA. Teste e2e garantindo que nenhuma resposta vai para a rede.
3. Revisão dos pesos e das faixas pelo responsável técnico antes de sair de "homologação".

### Fase C: PLD/FT e LGPD
1. Conferir a Lei nº 9.613/1998, a Res. CFC nº 1.721/2024, a LGPD e a Res. CD/ANPD nº 2/2022 na fonte primária e cadastrar os itens.
2. Criar as páginas das duas frentes e as perguntas delas no termômetro.
3. Bloco "Como a ORGATEC cumpre as próprias obrigações" na página Escritório (se a decisão C6 aprovar).

### Fase D: integridade e calendário
1. Conferir o Decreto nº 11.129/2022 e o nº 12.304/2024 e publicar a página de integridade.
2. Obrigações de compliance com data (comunicação anual ao COAF, prazos do programa de conformidade) no **calendário fiscal**, como esfera nova "compliance", com teste por data.
3. Ligação com os sistemas, só como serviço descrito e sem acesso:
   - o módulo de análise de compliance do OrgAgentDoc (regras PLD/FT, fiscal e LGPD) e os achados forenses do OrgConc e do OrgAudi;
   - o site continua sem chamar a API deles.

## 8. Decisões que dependem da ORGATEC

| # | Decisão | Por que importa |
|---|---|---|
| C1 | Nome da área: **"Compliance"** ou **"Conformidade"** | O site é em português simples; "Compliance" é o termo que o mercado procura. **Decidido (01/11/2026):** "Compliance". |
| C2 | Confirmar as **quatro frentes** (tributária, PLD/FT, LGPD, integridade) ou começar só com as duas primeiras | Define as fases C e D. **Decidido:** as quatro frentes. |
| C3 | Lugar no menu: grupo próprio (e "Escritório" vai para o rodapé) ou dentro de "Consultoria" | Espaço do menu no desktop. **Decidido:** grupo próprio; "Escritório" no rodapé e no menu ☰. |
| C4 | O que a ORGATEC **entrega** em PLD e em LGPD: diagnóstico e organização documental pelo escritório, ou também parecer jurídico com um parceiro | Evita prometer serviço que não é do escritório. **Decidido:** diagnóstico e organização de documentos e rotinas, sem parecer jurídico. |
| C5 | **Pesos e faixas do termômetro**, aprovados pelo responsável técnico | É a pontuação que o visitante vê; não pode ser opinião apresentada como fato. **Decidido:** termômetro oculto em produção até a revisão técnica (V11). |
| C6 | Publicar **como a ORGATEC cumpre a PLD e a LGPD** (comunicação ao COAF, encarregado de dados) | Prova de autoridade. Depende de o e-mail `dpo@` estar ativo (pendência C4 do painel). **Decidido:** publicar, com o canal do encarregado "em ativação" até o dpo@ funcionar; confirmação do responsável técnico em V12. |

## 9. Pendências que serão registradas no painel de testes

- **D3:** passa a "resolvida (seção própria)", com link para este plano.
- **D10:** decisões C1 a C6.
- **V10:** conferir na fonte primária as normas da seção 3.
- **V11:** revisão técnica dos pesos e das faixas do termômetro.

## 10. Fontes consultadas para este plano (secundárias; servem só para saber o que conferir)

- [Resolução CFC nº 1.721/2024 (PDF no portal do COAF)](https://www.gov.br/coaf/pt-br/assuntos/informacoes-as-pessoas-obrigadas/orgaos-reguladores-e-fiscalizadores/resolucao-cfc-no-1-721-de-18-de-abril-de-2024-1.pdf/@@display-file/file) e [cartilha do CFC, 2025](https://cfc.org.br/wp-content/uploads/2025/12/Cartilha_Site_2025.pdf)
- [Programa Confia: resumo técnico do Ministério da Fazenda (2026)](https://www.gov.br/fazenda/pt-br/assuntos/noticias/2026/janeiro/ResumoTcnico.pdf), [prorrogação da adesão até 20/03/2026 (Agência Gov)](https://agenciagov.ebc.com.br/noticias/202602/receita-federal-prorroga-20-marco-adesao-programa-confia) e [IN RFB nº 2.317/2026 (LegisWeb)](https://www.legisweb.com.br/legislacao/?id=493298)
- [Resolução CD/ANPD nº 2/2022 (cópia publicada no gov.br)](https://www.gov.br/palmares/pt-br/midias/arquivos-menu-acesso-a-informacao/legislacao/resolucao-cd-anpd-n2-2022.pdf)
- [Decreto nº 11.129/2022: comentário (Justen)](https://justen.com.br/ultimos_artigos/decreto-11-129-2022-nova-regulamentacao-da-lei-anticorrupcao-lei-12-846-2013/) e [relatório da Rede Nacional de Integridade Privada (CGU)](https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/rede-nacional-de-promocao-da-integridade-privada/arquivos/RelatrioGTREDE.pdf)

## 11. Fase 2: por público (02/11/2026)

Base: `docs/relatorio-publicos-reforma-compliance.md` (9 públicos). Plano aprovado em 02/11/2026, em seis fases, cada uma publicável:

| Fase | Público | Situação |
|---|---|---|
| P1 | Transportador de cargas + base | **Feita em 02/11/2026** |
| P2 | Produtor rural | **Feita em 02/11/2026** (LCDPR segue com a fonte pendente; data da DITR de 2026 não conferida) |
| P3 | MEI, autônomo e Simples | **Feita em 02/11/2026** (prorrogação da Res. CGSN nº 194/2026 não conferida) |
| P4 | Comércio e indústria; serviços | **Feita em 02/11/2026** |
| P5 | Pessoa física com imóveis | **Feita em 02/11/2026**, com a calculadora de enquadramento |
| P6 | Consumidor de baixa renda | **Feita em 02/11/2026**: item `cashback` e perguntas frequentes na Central da Reforma |

**Como está montado:**
- `compliance/publicos.html` lista os 8 públicos. Só os que estão em `PUBLICOS_PRONTOS` (`tools/paginas_compliance.py`) têm link; os demais aparecem "em preparação".
- Cada público tem a página `compliance/publico/<arquivo>.html`, gerada por `publico()` com os mesmos blocos de `frente()`. Os itens chegam pelo destino `publico-<id>` (`conteudo.PUBLICOS`), inclusive os da reforma, sem cópia.
- Obrigações setoriais usam um pilar próprio (`transporte`). O termômetro tem perfis (`termometro.PERFIS`); a âncora `#perfil-<id>` abre no perfil, e `REGRA` diz em que página está a regra de cada frente.
- Relatório do termômetro para imprimir ou salvar em PDF: `[data-termometro-relatorio]`, só visível em `@media print`, sem rede e sem as respostas brutas.
- Calendário: atualização semestral dos pisos de frete pela ANTT (20/01 e 20/07) na esfera Compliance.

**P1, conferido em 02/11/2026:**
- Lei nº 11.442/2007 (RNTRC com revalidação anual e pagamento do frete ao TAC);
- Lei nº 13.703/2018 (pisos e CIOT, red. Lei nº 15.485/2026);
- Res. ANTT nº 6.090/2026 (CIOT obrigatório a partir de 18/09/2026, e não 24/05/2026 como dizia a página informativa da ANTT);
- Lei nº 10.209/2001 e ADI 6031 (art. 8º constitucional);
- CLT, arts. 235-B e 235-C, e ADI 5322: a indenização de 30% do tempo de espera e o fracionamento do descanso foram declarados inconstitucionais;
- CTB, art. 148-A.

**P2, conferido em 02/11/2026:**
- Lei nº 12.651/2012, arts. 29 e 78-A (CAR obrigatório; crédito agrícola só com CAR);
- Lei nº 9.393/1996, arts. 4º, 7º, 8º, 9º, 12 e 20 (crédito rural e incentivos dependem do ITR dos últimos cinco exercícios, salvo PRONAF);
- Lei nº 8.212/1991, art. 25, I e II, e § 13 (Funrural de 1,2% + 0,1% e opção pela folha);
- NR-31, itens 31.2.1 e 31.3.1, no PDF oficial do MTE (última alteração: Portaria MTE nº 342/2024);
- Regulamento (UE) 2023/1115, versão consolidada de 18/09/2026 (EUDR): vale a partir de 30/12/2026, ou de 30/06/2027 para micro e pequenas empresas criadas até 31/12/2024 (red. Reg. (UE) 2025/2650).

Calendário: opção do Funrural pela folha (pagamento da folha de janeiro, até 20/02, antecipando) e as duas datas do EUDR.

**P3, conferido em 02/11/2026** (LC 214 lida inteira no navegador do app; o WebFetch para no art. 233):
- LC nº 214/2025, art. 517 (LC 123, art. 18-A, § 3º, IV e V, e Anexo VII: valores fixos do MEI com IBS e CBS; em 2027 e 2028, R$ 0,994 de CBS e R$ 0,006 de IBS), com efeitos em 01/01/2027 (art. 544, III);
- LC nº 238/2026, de 21/10/2026: limite do MEI de R$ 110 mil em 2027 e de R$ 140 mil a partir de 2028, até 2 empregados e remissão dos débitos da contribuição do MEI até 13/10/2026, com contrapartida (art. 10: efeitos em 2027 e 2028);
- LC nº 214/2025, arts. 4º, § 6º, 21, I e § 1º, e 26, IV, § 1º, II, e § 10 (pessoa física contribuinte; nanoempreendedor abaixo de 50% do limite do MEI; 25% da receita para motorista e entregador de aplicativo);
- LC nº 214/2025, art. 516 (LC 123, art. 17, XV: a locação de imóveis próprios impede o Simples, desde 01/01/2025);
- LC 123, art. 13, §§ 9º a 11 (janelas de setembro e março) e a notícia oficial do CGSN de 17/04/2026 (Res. CGSN nº 186/2026).

Termômetro: o pilar `pequenos` tem perguntas com `publicos` (MEI, autônomo e Simples). `T.perguntaVale(p, perfil)` filtra as perguntas, e `T.regraDe(p)` leva o "Ver a regra" à página do público.

**P4, conferido em 02/11/2026:**
- LC nº 214/2025, arts. 128 a 130 (redução de 60% para os serviços de educação do Anexo II e de saúde do Anexo III; limites dos parágrafos únicos);
- ADCT, art. 134 (saldos credores de ICMS ao fim de 2032: homologação, 240 parcelas e IPCA).
- **Substituição tributária do ICMS:** a LC 214 só a cita no crédito presumido do estoque de 2027 (bens sujeitos a ST ou monofásico de PIS/Cofins). A ST do ICMS é regra estadual e acaba com o ICMS em 2033 (ADCT, arts. 128 e 129). O site não traz regra estadual de ST.
- Itens da reforma reaproveitados pelo destino `publico-comercio` e `publico-servicos`, sem cópia.

**P5, conferido em 02/11/2026** (LC 214 lida no navegador do app):
- art. 251 (pessoa física contribuinte nas operações com imóveis);
- art. 253 (temporada de até 90 dias, que entra nos limites; red. LC nº 227/2026);
- art. 254, III (na locação, o tributo é devido no pagamento);
- art. 259 (redutor social de R$ 100 mil por imóvel residencial novo e de R$ 30 mil por lote);
- art. 260 (redutor social de R$ 600 por mês por imóvel residencial alugado; red. LC nº 227/2026);
- art. 261 (reduções de 50% e de 70% na locação).
- O art. 252, § 7º, remete ao art. 57, § 4º, que a LC nº 227/2026 revogou. O site não usa essa remissão; a regra dos bens fora da atividade está no art. 4º, § 6º.
- Calculadora: `calculadoras.imoveisPessoaFisica` (função pura, testada), ligada em `paginas.js` ao `#formImoveisPF`. Roda só no navegador.

**P6, conferido em 02/11/2026:** LC nº 214/2025, arts. 112 a 118, no texto integral:
- quem recebe: família do CadÚnico com renda de até meio salário mínimo por pessoa, CPF regular e inclusão automática;
- como é calculado: a partir de documentos fiscais vinculados ao CPF;
- quanto: 100% da CBS e 20% do IBS no gás de botijão, na energia, na água, no esgoto e nas telecomunicações, e 20% nos demais casos;
- quando: o momento é definido em regulamento.

A Central da Reforma ganhou o bloco "Perguntas frequentes" (`data-faq-itens="reforma"`), alimentado pelo campo `pergunta` de 7 itens da reforma.

**Situação da fase 2:** os 8 públicos têm página, e a P6 está feita. O que falta é revisão técnica (V1, V11, V12) e o que ainda não foi conferido (V13).
