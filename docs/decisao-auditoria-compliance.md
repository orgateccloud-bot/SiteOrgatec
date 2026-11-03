# Decisão: ideias além do tributário puro

Este documento é só para decisão. **Nada aqui está implementado**: cada ideia depende da sua aprovação.

Critério de avaliação: a ideia precisa reforçar o eixo tributário, e não abrir uma frente nova. Perfil considerado: agro, transporte, lucro real e produtor rural com LCDPR.

Objetivos: **C** = captação, **R** = retenção, **A** = autoridade.

| # | Ideia | Como reforça o tributário | Onde fica no site | Obj. | Agro | Transporte | Lucro real | LCDPR | Risco de escopo |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Revisão de créditos de PIS/Cofins antes da extinção** | Créditos não usados continuam válidos depois de 2027, desde que escriturados (LC 214/2025, arts. 378 a 383, conferido). É receita recuperável e tem prazo. | Serviço na página Tributário (o cartão já existe) e calculadora futura | C, A | Médio | Alto | Alto | — | Baixo: é tributário puro |
| 2 | **Prontidão para o programa de conformidade de 2026** | O Ato Conjunto RFB/CGIBS nº 5/2026 exige corrigir inconsistências até 31/12/2026 e indicar contador responsável (conferido). | Área do cliente e item da Central (já publicado) | R, C | Alto | Alto | Alto | Médio | Baixo |
| 3 | **Checklist de documentos fiscais com IBS e CBS** (CT-e, MDF-e, NF-e) | Os campos são obrigatórios desde 03/08/2026 (Ato Conjunto nº 4/2026, conferido); erro de classificação vira inconsistência. | Página Transporte e Área do cliente | R | Médio | Alto | Alto | — | Baixo |
| 4 | **Cruzamento entre LCDPR e notas fiscais do produtor** | Prepara o produtor que vai virar contribuinte (CNPJ e documento fiscal do produtor pessoa física a partir de 01/01/2027, Decreto nº 13.075/2026, conferido) e reduz divergência de receita. | Serviço na página Agro | C, R | Alto | — | — | Alto | Médio: é auditoria; mantenha ligado à transição do IBS e da CBS |
| 5 | **Termômetro de risco de autuação** (questionário com pontuação) | Funciona como porta de entrada para o diagnóstico tributário. | Ferramentas | C | Alto | Alto | Alto | Alto | Médio: as regras de pontuação precisam de base legal por pergunta, para não virar opinião apresentada como fato |
| 6 | **Split payment e capital de giro** (simulação de caixa) | O tributo deixa de passar pelo caixa (LC 214/2025, arts. 31 a 35, conferido); o cronograma ainda não saiu. | Ferramentas e Transporte | C, A | Médio | Alto | Alto | — | Médio: sem cronograma, a simulação fica hipotética |
| 7 | **Conformidade trabalhista do motorista** (jornada e eSocial) | É indireto: reduz passivo do cliente de transporte, mas não é tributo sobre consumo. | Serviço "Pessoal" na página Escritório | R | — | Alto | Médio | — | Alto: dilui o foco. A base legal (lei do motorista profissional) **não foi conferida** neste levantamento. |
| 8 | **Monitor de certidões negativas** (CND federal, estadual e FGTS) | Retém o cliente com alertas de vencimento; a regularidade fiscal condiciona crédito rural e licitações. | Área do cliente | R | Alto | Alto | Médio | Médio | Alto: **exige integração** com os portais (e-CAC, SEFAZ, Caixa), certificado digital e tratamento de dados do cliente. A base legal das certidões **não foi conferida** neste levantamento. |
| 9 | **LGPD para clientes** (adequação) | Fraco: é proteção de dados, não tributação. | Escritório | A | Baixo | Baixo | Médio | — | Alto: frente nova. O site já cumpre a LGPD no próprio tratamento de dados. |

## Recomendação para decidir

- **Dentro do eixo** (reforçam o tributário sem diluir): 1, 2 e 3. As três já têm item ou cartão no site e dependem só de texto e de uma calculadora.
- **Com cuidado:** 4, 5 e 6. Valem pelo perfil agro e transporte, mas precisam de critérios com fonte (5) ou de regulamentação (6).
- **Fora, por ora:** 7, 8 e 9. Diluem o foco ou exigem integração e dados de clientes; a 8 só faz sentido se o ERP escolhido para o portal já oferecer o monitor.

Questões que dependem de você:
- até onde ampliar para auditoria e compliance (só documento, 1 ou 2 serviços dentro da página Tributário, ou uma seção própria);
- se as integrações da ideia 8 entram no escopo do portal.
