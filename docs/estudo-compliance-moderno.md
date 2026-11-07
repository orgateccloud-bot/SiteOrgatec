# Estudo: compliance moderno na área de Compliance do site

**Data:** 07/11/2026. **Branch:** `ideia/compliance-moderno`. **Painel interativo:** `docs/painel-compliance-moderno.html` (abrir no navegador).
**Situação:** estudo e plano. Nada do site mudou. As ondas abaixo só começam depois do "execute".

## 1. Resumo

- **O que já está bem:** a área responde bem à pergunta "o que a lei exige?". São 38 pontos com fonte, 43 perguntas, 9 perfis e 8 páginas de público.
- **A lacuna principal:** a área não ajuda a responder "o controle funciona na prática, e como você sabe?". Essa é a terceira pergunta do DOJ e o centro do compliance moderno. As 43 perguntas do termômetro pedem só que a empresa declare que o controle existe.
- **Os achados mais sólidos:**
  - medir a eficácia (norma, classe A);
  - lembretes ajudam pouco, mas ajudam (meta-análise, classe B);
  - comunicar o código de ética não garantiu entendimento (experimento controlado, classe B);
  - canais muito usados andam junto com menos multas (classe C, só correlação);
  - cruzar todos os registros acha falhas que a amostra não vê (classe C).
- **No Brasil:** os estudos encontrados medem aderência formal, não eficácia. Para empresa pequena, a evidência direta é quase nenhuma, então toda recomendação para MEI e Simples vem com esse aviso.
- **Recomendação:** três ondas.
  - **Rápida:** acrescentar ao termômetro a camada "como você sabe", fazer a rotina de revalidação e o plano de ação em `.ics`.
  - **Média:** pesos por perfil, perguntas de cultura e de relatos, e o boletim de mudanças.
  - **Estrutural:** página de revisão do responsável técnico e o diagnóstico de eficácia como serviço.
- **Bloqueio:** nada disso vai à produção antes da revisão técnica (V1 e V11).

## 2. Diagnóstico da área atual

Contagem feita em 07/11/2026 nos arquivos da branch `desenvolvimento`.

| Item | Situação | Arquivo |
|---|---|---|
| Pontos de compliance | 38: tributário 4, PLD 5, LGPD 5, integridade 3, transporte 7, rural 5, MEI/autônomo/Simples 7, imóveis 2 | `site/assets/js/compliance-itens.js` |
| Revisão técnica | 0 aprovados; em produção não aparecem | idem; V1 |
| Termômetro | 43 perguntas, 9 perfis, pesos de 2 e 3 provisórios, `REVISAO.status = 'pendente'` | `site/assets/js/termometro.js`; V11 |
| Resultado | Nível (em dia, atenção, risco), pendências com fonte e relatório para imprimir | `site/assets/js/compliance.js` |
| Pendências do plano anterior | Plano de ação `.ics`, modelos para baixar, página de revisão do responsável técnico | `docs/plano-area-compliance.md` |
| Normas sem conferência | LCDPR, data da DITR 2026, Res. CGSN 194/2026, Res. ANTT 5.982/2022 | V13 |
| Restrições | Site estático, CSP sem script embutido, sem dados de clientes, sem parecer jurídico (C4), sem probabilidade de autuação | README e decisões C1 a C6 |

**Lição do próprio projeto (frente 8):** o relatório de públicos teve três erros, todos vindos de fonte secundária e todos corrigidos só depois de ler a fonte primária.

| Erro | Fonte secundária dizia | Fonte primária diz |
|---|---|---|
| Data do CIOT | 24/05/2026, na página informativa da ANTT | 18/09/2026, Res. ANTT nº 6.090/2026 |
| Tempo de espera do motorista | Indenização de 30% vigente | Declarada inconstitucional na ADI 5322 |
| Limite do MEI | R$ 81 mil | Alterado pela LC nº 238/2026 |

É exatamente o problema que a gestão de mudança regulatória ataca.

## 3. As nove frentes

Classes de evidência:
- **A:** norma ou regulador, lido no original;
- **B:** meta-análise ou experimento controlado;
- **C:** estudo observacional, de caso ou pesquisa de opinião;
- **D:** opinião ou fornecedor, nunca usado sozinho.

### 3.1 Eficácia: existe, funciona, como sabe

- **Evidência:** DOJ, ECCP (set/2024, lido no PDF), A. As três perguntas são: o programa é bem desenhado? Tem recursos e funciona de boa-fé? Funciona na prática? O documento pede ainda que se meça a eficácia do treinamento e de cada componente.
  - Soltes (2018, NYU JLB) e Chen e Soltes (2018, HBR), C. Medir resultado, não só documento. Lido só o sumário: **a conferir**.
- **Para pequena empresa:** o ECCP é americano e pensado para empresas investigadas. A lógica vale; a escala, não.
- **No site:**
  - termômetro em três camadas, em que cada pergunta-chave ganha "funcionou no período?" e "que registro mostra?";
  - o resultado separa o que é só declaração.
- **No serviço:** o diagnóstico pede amostra de registros, como CIOT emitidos, cadastros e protocolo do canal.
- **Custo:** baixo no site, médio no serviço. **Risco:** perguntas longas cansam; usar a camada extra só nas perguntas de peso 3.

### 3.2 Risco e proporcionalidade

- **Evidência:**
  - Decreto nº 11.129/2022, art. 57 (avaliação considera o porte, inclusive ME e EPP), A, já conferido no site;
  - ECCP (metodologia de risco e lições aprendidas), A;
  - Pró-Ética 2025-2026 (dez áreas, 70% para aprovar), A, lido em fonte da CGU.
- **No site:** pesos por perfil com justificativa e fonte em cada um, que resolve a V11. Hoje são pesos de opinião, provisórios.
- **No serviço:** matriz de risco anual do cliente, de uma página para MEI e Simples.
- **Risco:** pesos continuam sendo julgamento. A diferença é que o julgamento fica escrito e revisado.

### 3.3 Cultura e relatos

- **Evidência:**
  - Weaver e Treviño (1999, BEQ), C: a orientação por valores tem contribuição única maior que a orientação por regra (pesquisa numa empresa).
  - Treviño et al. (1999, CMR), C: o que mais atrapalha é o programa visto como proteção da chefia.
  - Stubben e Welch (2020, JAR), C: quase 2 milhões de relatos em mais de 1.000 empresas; mais relatos, menos multas e processos. É correlação, com dados de fornecedor.
  - Ferrère, Rider, Renerte e Edmondson (MIT SMR), C: segurança psicológica ligada ao clima ético e à disposição de relatar. Os autores dizem que a causalidade está aberta.
- **No site:** perguntas de cultura e de tratamento de relatos na frente de integridade. Por exemplo: "o último relato recebido teve resposta e registro?".
- **No serviço:** canal com prazo de resposta e registro de apuração.
- **Risco:** relato alto pode parecer problema para o cliente. É preciso explicar que, na evidência, costuma ser bom sinal.

### 3.4 Monitoramento: toda a base

- **Evidência:** Jans, Alles e Vasarhelyi (2014, The Accounting Review), C. A mineração de processos achou pagamentos sem aprovação e falta de segregação de funções que a auditoria interna não tinha visto. Foi um banco.
- **No site:** página explicando o cruzamento como serviço, sem nenhum dado no site.
- **No serviço:** a conciliação bancária e a auditoria rural já cruzam notas, extratos e escrituração. **A conferir:** o que cada sistema faz de fato, lido nos projetos, sem abrir `.env`, bancos ou dados de clientes.
- **Risco:** prometer o que o sistema não faz.

### 3.5 Conformidade embutida

- **Evidência:** OCDE, Tax Administration 3.0 (2020), A. A ideia é a conformidade "por desenho", dentro dos sistemas que a empresa já usa. Lida em fonte secundária e no relatório OCDE Tax Administration 2023; a página original deu erro: **a conferir**.
- **No site:** o plano de ação em `.ics` (pendência antiga) e lembretes no calendário.
- **No serviço:** revisão do cadastro de produtos e do emissor para os campos de IBS e CBS.

### 3.6 Comportamento

- **Evidência:**
  - Antinyan e Asatryan (2025, Economic Journal), B. Numa base em que cerca de 25% cumprem, o lembrete soma 2,7 pontos; dissuasão, mais 3,2; apelo moral, mais 1,4. Os efeitos são pequenos e há algum viés de publicação.
  - Hallsworth et al. (2017, JPubE), B: a norma descritiva em cartas acelerou o pagamento de impostos em atraso.
  - Kirchler et al. (2008) e o estudo em 44 países, C: confiança e poder da autoridade elevam a intenção de cumprir.
- **No site:** lembretes simples, no momento certo.
- **Proibido:** norma social sem dado real ("9 em cada 10 já cumprem").
- **Risco:** exagerar o efeito.

### 3.7 Treinamento

- **Evidência:**
  - Gómez-Alatorre, Cuñado e Ferrero (2022, Business and Society Review), B. Experimento controlado em 206 filiais: o e-mail semanal sobre o código de ética não melhorou o entendimento.
  - Um estudo no repositório de Harvard indica que o treinamento não reduz desvios na média e que só a sessão presencial em turma pequena teve efeito. **Autoria não confirmada**, por isso não entra como evidência.
  - O ECCP (A) pede que se meça o efeito do treinamento.
- **No site:** não prometer que treinamento reduz desvios.
- **No serviço:** turmas pequenas, perguntas de compreensão antes e depois.

### 3.8 Mudança regulatória

- **Evidência:** os três casos deste projeto (seção 2). O ECCP também pede atenção a riscos emergentes, A.
- **No site:**
  - rotina de 90 dias com `conteudo.atrasados(itens, hoje, 90)`, que já existe;
  - ordem de prioridade das fontes: norma no original, ato do regulador e só depois a página informativa.
- **No serviço:** boletim de mudanças por público.

### 3.9 IA e analytics

- **Evidência:**
  - ECCP, A: governança do uso de IA e medição de acurácia, precisão e recall dos modelos.
  - FATF (2021), A: uso responsável e baseado em risco, com proteção de dados. Detalhes sobre explicabilidade e falsos positivos só em fonte secundária: **a conferir**.
  - ISO/IEC 42001:2023, A: sistema de gestão de IA. Só o escopo.
  - Durtschi et al. (2004), C: a Lei de Benford falha com poucos dados e alarma à toa perto de limites de aprovação.
- **No site:** nenhuma IA. Dizer como os sistemas do escritório medem acerto e falsos positivos.
- **No serviço:** relatório de cruzamento com a taxa de falso positivo; Benford só como triagem.

## 4. Mapa do termômetro

Classificação das 43 perguntas contra as três perguntas do DOJ, os parâmetros do Decreto nº 11.129/2022 (art. 57) e as áreas do Pró-Ética. Uma pergunta pode contar em mais de um eixo.

| Eixo | Perguntas | Quantas |
|---|---|---|
| Desenho: o controle existe | Todas | 43 |
| Recursos e responsáveis | `t-contador-responsavel`, `l-encarregado`, `p-controles`, `p-comunicacao` | 4 |
| Funciona na prática, com registro | Nenhuma. `i-codigo` diz "aplicado na prática", mas é declaração | 0 |
| Risco e terceiros | `i-riscos`, `p-enquadramento`, `im-enquadramento` | 3 |
| Cultura e relatos | `i-codigo` (canal) | 1 |
| Medição e prova | Nenhuma | 0 |

**O que falta frente ao Decreto nº 11.129 e ao Pró-Ética:** comprometimento da alta direção, treinamento e comunicação, monitoramento contínuo, investigação de relatos e medidas disciplinares. Para micro e pequena empresa, o Pró-Ética admite que a alta direção seja o próprio dono ou os sócios.

**Ressalva:** o termômetro é ferramenta de conformidade legal por público, não avaliação de programa de integridade. Não precisa cobrir tudo; precisa dizer claramente o que mede.

### 4.1 Cinco perguntas reescritas em camadas (exemplo)

| Pergunta | Existe? | Funciona? | Como você sabe? |
|---|---|---|---|
| `tr-ciot` | O CIOT é emitido antes de cada frete contratado? | Nos últimos 3 meses, algum frete saiu sem CIOT? | Dá para listar os CIOT do período pela instituição de pagamento? |
| `ru-itr` | A DITR é entregue e o ITR pago? | Algum dos últimos 5 exercícios ficou pendente? | Os recibos dos 5 exercícios estão guardados? |
| `i-codigo` | Há código de conduta e canal? | O canal recebeu relato no último ano e houve resposta? | Há registro da resposta e do que mudou? |
| `l-incidente` | Existe procedimento de incidente? | Foi testado ou usado no último ano? | Há registro do teste ou do caso? |
| `pq-simples-docs-2027` | O emissor terá os campos de IBS e CBS? | Já saiu nota de teste com os campos? | Há arquivo XML de teste validado? |

## 5. Plano em três ondas

| Onda | Entrega | Esforço | Depende de | Painel | Pronto quando |
|---|---|---|---|---|---|
| 1 | Camadas "funciona" e "como sabe" nas perguntas de peso 3; aviso de que o resultado é declaração | Médio | Aprovação do formato | V11 | Teste JS da avaliação em camadas; e2e do perfil; sem rede |
| 1 | Rotina de revalidação de 90 dias, que lista itens vencidos no painel de testes | Baixo | — | nova V | Teste com item vencido |
| 1 | Plano de ação em `.ics` com as pendências que têm prazo | Baixo | — | — | Download testado, reusa `calendario.gerarIcs` |
| 2 | Pesos por perfil com justificativa | Médio | Responsável técnico | V11 | Cada peso com fonte; teste de faixas |
| 2 | Perguntas de cultura e de relatos | Baixo | Texto aprovado | V1 | Fonte em cada pergunta |
| 2 | Página "como o escritório verifica" | Médio | Levantamento do que os sistemas fazem | T12 | Só serviço que existe |
| 2 | Boletim de mudanças por público | Médio | Rotina da onda 1 | — | Uma edição revisada |
| 3 | Página de revisão do responsável técnico | Alto | Decisão sobre o formato | V1, V11, V12 | Aprovar gera registro auditável |
| 3 | Diagnóstico de eficácia como serviço | Alto | Decisão comercial | — | Roteiro e modelo com dados fictícios |

## 6. O que não adotar

| Ideia | Por quê |
|---|---|
| Probabilidade de autuação | Não há base. Seria opinião apresentada como fato |
| Assinar no topo do formulário | Shu et al. (PNAS, 2012) foi retratado em 2021 |
| Norma social inventada | Engana. Só com dado real e fonte |
| Prometer que treinamento reduz desvios | Evidência fraca ou nula |
| Benford como prova de fraude | Só triagem: falha com poucos dados e perto de limites |
| Copiar texto das normas ISO | Conteúdo pago |
| IA no site analisando dados de clientes | Site estático, LGPD e CSP |
| Números de fornecedores ("reduz 60% dos falsos positivos") | Classe D, sem estudo verificável |

## 7. Decisões

**Para a direção:**
1. O termômetro ganha camadas, e com isso fica mais longo?
2. O diagnóstico de eficácia vira serviço?
3. Haverá boletim de mudanças por público, e com que frequência?
4. A página "como o escritório verifica" pode citar os sistemas?

**Para o responsável técnico:**
1. Pesos e faixas por perfil (V11).
2. Texto das perguntas de cultura e de relatos.
3. Ordem de prioridade das fontes e o prazo de revalidação (90 dias?).
4. Revisão dos 38 pontos (V1).

## 8. A conferir

- **ECCP:** versão posterior a set/2024 não encontrada. A página do DOJ de 06/10/2026 ainda lista set/2024.
- **OCDE:** Tax Administration 3.0 e Co-operative Compliance no original (as páginas deram erro).
- **FATF:** os trechos sobre explicabilidade e falsos positivos.
- **Soltes (2018), Chen e Soltes (2018), Treviño et al. (1999):** lidos só em resumo ou sumário.
- **Estudo de Harvard sobre treinamento:** autoria.
- **CGU, Integridade para Pequenos Negócios:** se há edição posterior à de 2015.
- **Evidência brasileira de eficácia** (não só de aderência): não encontrada.
- **Sistemas do escritório:** o que fazem de fato.

## 9. Referências (lidas em 06 e 07/11/2026)

**Normas e reguladores (A)**
- DOJ, ECCP, set/2024: https://www.justice.gov/criminal/criminal-fraud/compliance (PDF lido)
- ISO 37301:2021, revista e confirmada em 2026: https://www.iso.org/standard/75080.html
- ISO 37001:2025: https://www.iso.org/standard/37001
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- FATF, Opportunities and Challenges of New Technologies for AML/CFT: https://www.fatf-gafi.org/en/publications/Digitaltransformation/Opportunities-challenges-new-technologies-for-aml-cft.html
- CGU, Pró-Ética 2025-2026: https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/avaliacao-e-promocao-da-integridade-privada/empresa-pro-etica/documentos-anteriores/2025-2026/documento-orientativo-pro-etica-2025-2026-geral.pdf
- CGU, Integridade para Pequenos Negócios: https://www.gov.br/cgu/pt-br/centrais-de-conteudo/publicacoes/integridade/arquivos/integridade-para-pequenos-negocios.pdf
- OCDE, Behavioural Insights for Better Tax Administration (2021): https://search.oecd.org/tax/forum-on-tax-administration/publications-and-products/behavioural-insights-for-better-tax-administration-a-brief-guide.htm
- OCDE, Tax Administration 2023: https://www.oecd.org/en/publications/tax-administration-2023_900b6382-en.html

**Experimentos e meta-análises (B)**
- Antinyan e Asatryan, Economic Journal 135(668), 2025: https://www.zew.de/PU90311-1
- Hallsworth, List, Metcalfe e Vlaev, JPubE 148, 2017: https://www.nber.org/papers/w20007
- Gómez-Alatorre, Cuñado e Ferrero, Business and Society Review 127(1), 2022: https://econbiz.de/Record/how-to-effectively-communicate-your-code-of-ethics-an-empirical-study-using-a-cluster-randomized-control-trial-experiment-g%C3%B3mez-alatorre-eugenio/10013188480
- Kish-Gephart, Harrison e Treviño, JAP 95(1), 2010 (meta-análise): https://typeset.io/papers/bad-apples-bad-cases-and-bad-barrels-meta-analytic-evidence-1m0jsbhig3

**Observacionais e de caso (C)**
- Stubben e Welch, JAR 58(2), 2020: https://econpapers.repec.org/RePEc:bla:joares:v:58:y:2020:i:2:p:473-518
- Jans, Alles e Vasarhelyi, The Accounting Review, 2014: https://academicnewsletter.sufe.edu.cn/info/415684
- Weaver e Treviño, BEQ 9(2), 1999: https://www.cambridge.org/core/journals/business-ethics-quarterly/article/compliance-and-values-oriented-ethics-programs-influenceson-employees-attitudes-and-behavior/7CC7F328B583F76C46D2EA9BFB5D2B3A
- Treviño et al., CMR 41(2), 1999: https://cmr.berkeley.edu/1999/02/41-2-managing-ethics-and-legal-compliance-what-works-and-what-hurts
- Kirchler, Hoelzl e Wahl, JoEP 29, 2008: https://econpapers.repec.org/RePEc:eee:joepsy:v:29:y:2008:i:2:p:210-225
- Batrancea et al., 44 países: https://pure.ecnu.edu.cn/zh/publications/trust-and-power-as-determinants-of-tax-compliance-across-44-natio/
- Ferrère, Rider, Renerte e Edmondson, MIT SMR: https://sloanreview.mit.edu/?p=100450
- Soltes, NYU JLB 14(3), 2018: https://nyujlb.org/_files/ugd/716e9c_d2bbd781bef742ba8f74bd65206dd0b2.pdf
- Durtschi, Hillison e Pacini, 2004: https://benfordonline.net/fullreference/145
- Aderência no Brasil (capital aberto): https://scielo.br/j/rcf/a/6RgstbYdxNWwjtQVDzhxzJB/?lang=en

**Não usar**
- Shu et al., PNAS 2012, retratado em 2021: https://pmc.ncbi.nlm.nih.gov/articles/PMC8463784
