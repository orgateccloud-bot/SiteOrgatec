# Relatório de riscos: segurança da informação e continuidade de negócios

**Interpretação adotada:** "eventos" são incidentes de segurança da informação e interrupções de negócio que ameacem dados, operações ou prazos da ORGATEC e de clientes como a LOCAR; acidentes de trabalho e segurança física de pessoas ficam fora do escopo, salvo quando interrompem a operação.

| Ficha | |
|---|---|
| Classificação | **Uso interno e restrito.** Descreve fragilidades reais. Não publicar, não colocar em `site/` nem em `site/assets/js/homologacao.js` |
| Data de referência | 03/11/2026 |
| Elaboração | Claude (sessão responsável por Firebase e Google), sem revisão humana até aqui |
| Validação pendente | Responsável técnico (Robson Alain Veloso), direção e assessoria jurídica. Este relatório não é parecer jurídico |

---

## 1. Resumo executivo

Hoje o site `orgatec.io` tem exposição de dados baixa: o Firestore está vazio, não há login e a API não está no ar. **O risco maior da ORGATEC não está no site.** Está nas contas de administração, nos certificados digitais, no sistema contábil e nos dados de clientes que ficam fora do que pude verificar.

Um incidente no escritório atinge vários clientes ao mesmo tempo. Esse efeito de carteira é o que diferencia a ORGATEC de uma empresa comum: dados protegidos por sigilo profissional, credenciais fiscais e prazos com multa se concentram em um só lugar.

**Achados verificados nesta data:**

| # | Achado | Risco | Fonte da verificação |
|---|---|---|---|
| 1 | A conta Gmail `orgatec.cloud@gmail.com` é **a única proprietária de 12 projetos**, inclusive `orgatec-site`, que fica fora da organização existente | Perda dessa conta significa perda do site e de todos os projetos | IAM e metadados dos projetos |
| 2 | A tarefa `ORGATEC_Backup_Diario` **falha todo dia**: roda às 02h e o script `C:\meu-agente\scripts\backup_postgres.py` não existe | Uma cópia que se presume feita pode não existir. Não identifiquei qual banco ela deveria copiar | Agendador do Windows e sistema de arquivos |
| 3 | Firestore com backup agendado e PITR **desligados** (proteção contra exclusão ligada em 04/11/2026) | Sem efeito hoje (banco vazio). Vira risco alto no dia em que a API entrar no ar | Firebase CLI e `gcloud` |
| 4 | `orgatec.io` **sem SPF, DMARC, MX, DNSSEC e CAA** | Qualquer um consegue enviar e-mail com o domínio da ORGATEC, e isso alimenta fraude contra clientes | DNS público |
| 5 | `OrgAudi/docs/SUPABASE_MIGRATION_STATUS.md` continua no disco, e a pendência T12 aponta senha em texto claro nele | Credencial exposta em arquivo. Li só a contagem de ocorrências, não o valor | Sistema de arquivos e documento interno |
| 6 | Logs ficam em localização `global`, retenção de 30 dias, e não há log de leitura de dados nem log de acesso do Hosting | Pouca capacidade de investigar um incidente; possível conflito com os 6 meses do Marco Civil | API de Logging e IAM |
| 7 | O Firebase Hosting segue termos próprios **sem menção a Brasil, LGPD ou ANPD**, diferente do Firestore e do Cloud Run | Possível lacuna contratual para IPs tratados pelo Hosting. Exige validação jurídica | Termos oficiais lidos em 03/11/2026 |
| 8 | Ponto único de falha: o boletim e várias automações rodam em um PC | Parada do PC interrompe a automação | Agendador do Windows |
| 9 | Duas chaves de conta de serviço **sem validade**, criadas em janeiro de 2026, em `orgatec` e `orgatec-prod` | Quem tiver o arquivo acessa o projeto sem senha nem segunda etapa. Não sei onde os arquivos estão | Metadados no `gcloud` |

**Dez primeiras ações (detalhe na seção 12):**

1. Confirmar segunda etapa forte e códigos de recuperação em `orgatec.cloud@gmail.com`.
2. Adicionar Warley e Robson como proprietários individuais do projeto.
3. Trocar a senha citada na T12 e confirmar as demais credenciais expostas.
4. Descobrir o que o backup diário deveria copiar e corrigir. Fazer um teste real de restauração.
5. Publicar SPF e DMARC restritivos em `orgatec.io`.
6. Fazer inventário de certificados digitais e procurações eletrônicas de clientes. Trocar uso compartilhado de certificado por procuração eletrônica onde couber.
7. Definir, por contrato com cada cliente, quem é controlador e quem é operador, e o prazo para avisar incidente.
8. Pedir à Athenas os dados de continuidade: SLA, backup, MFA, registro de acesso e notificação de incidente.
9. Ativar o faturamento **só com** orçamento, alerta e limite de instâncias. Na mesma etapa, ligar PITR e backup agendado, antes do primeiro dado real.
10. Aprovar um plano de resposta a incidentes de uma página, com papéis, telefones e o relógio de 3 dias úteis.

---

## 2. Método e padrão de evidência

### 2.1 Escalas

As notas são **julgamento profissional do estado atual**, não medida estatística. Não existe base pública de incidentes para escritórios contábeis brasileiros desse porte (seção 7). A direção deve calibrar as notas, em especial o impacto financeiro, que depende da receita da ORGATEC, informação que não tive.

| Nota | Probabilidade (em 12 meses) | Impacto |
|---|---|---|
| 1 | Rara: menos de 1 vez em 20 anos | Inconveniente interno; menos de 0,1% da receita anual |
| 2 | Improvável: 1 vez em 5 a 20 anos | Atraso interno sem efeito em cliente; até 1% da receita |
| 3 | Possível: 1 vez em 2 a 5 anos | Cliente afetado de forma pontual; até 5% da receita |
| 4 | Provável: cerca de 1 vez por ano | Vários clientes afetados, multa ou comunicação legal; até 20% da receita |
| 5 | Quase certa: várias vezes por ano | Carteira afetada, sanção profissional ou ameaça à continuidade; acima de 20% da receita |

**Criticidade = probabilidade × impacto:** 1 a 5 baixa · 6 a 11 média · 12 a 19 alta · 20 a 25 crítica.

**Confiança da nota:** alta (verifiquei a configuração), média (há evidência externa, sem dado interno), baixa (depende de informação que não tive).

**Indicadores:**
- **RTO:** tempo máximo para voltar a operar.
- **RPO:** perda máxima de dados, medida em tempo.
- **MTTD:** tempo médio para detectar.
- **MTTR:** tempo médio para recuperar.

Os valores de RTO, RPO, MTTD e MTTR neste relatório são **metas propostas**, não medições. Nenhum foi medido. A ISO 22301 exige que venham de uma análise de impacto nos negócios (BIA), que ainda não existe.

### 2.2 Status das informações

| Marca | Significado |
|---|---|
| **[V]** | Verifiquei diretamente nesta data, por leitura da configuração ou do texto oficial |
| **[O]** | Consta em fonte oficial, lida por agente de pesquisa, sem nova conferência minha |
| **[I]** | Inferência minha a partir de fatos confirmados |
| **[NC]** | Não confirmado. Não usar como fato |
| **[INT]** | Depende de informação interna da ORGATEC ou do cliente |

O texto do pedido previa que a configuração do Firebase seria desconhecida. Como esta sessão tem acesso de leitura ao projeto, **confirmei o que a API mostra em vez de presumir**. A seção 3 separa o que foi visto do que não dá para ver. Parte da leitura de IAM usou a sessão já salva do Firebase CLI; depois disso, o controle de permissões barrou esse caminho, e as leituras seguintes usaram apenas o `gcloud`.

### 2.3 Limites

- O **DOU (in.gov.br) não abriu**. Datas de publicação vêm da própria norma, da ANPD, do CFC ou da Biblioteca Digital do MJ.
- As **normas ISO e ABNT são pagas**. Edições foram conferidas em catálogo, mas a numeração de controles da ABNT NBR ISO/IEC 27002:2022 usada aqui vem do conhecimento do autor. **Confira em exemplar licenciado antes de usar em auditoria.**
- Não vi dados da LOCAR nem de outros clientes. Não acessei Athenas, Hostinger, e-mail, estações de trabalho nem contratos.

---

## 3. Perímetro e estado verificado

### 3.1 Firebase e Google (projeto `orgatec-site`, leitura em 03/11/2026)

| Item | Estado | Marca |
|---|---|---|
| Proprietário (`roles/owner`) | Só `orgatec.cloud@gmail.com` | [V] |
| Organização no Google Cloud | Existe `orgatec-cloud-org`, mas **`orgatec-site` está fora dela** (`parent: null`) | [V] |
| Faturamento | **Desligado**, sem conta vinculada; plano gratuito (Spark) | [V] |
| Firestore | `southamerica-east1`, Native, **0 coleções** | [V] |
| Regras do Firestore | Negam todo acesso pelo navegador | [V] |
| PITR | Desligado; retenção de versões de 1 hora | [V] |
| Backup agendado | Nenhum | [V] |
| Proteção contra exclusão do banco | **Ligada em 04/11/2026** | [V] |
| Hosting | Site `orgatec-site`, domínio `orgatec.io` ativo com certificado | [V] |
| `www.orgatec.io` | Não cadastrado; a conexão HTTPS falha (T13) | [V] |
| Canais de prévia | `dev` e `ideia-privacidade-2026-11`, expiram em 03/12/2026 | [V] |
| Authentication | Não iniciado (leitura de 02/11/2026) | [O] |
| API no Cloud Run | Não publicada: `/api/saude` responde 404 | [V] |
| Conta de serviço | `firebase-adminsdk`, ativa, **sem chaves criadas pelo usuário** | [V] |
| Chave de API | 1, criada pelo Firebase, com restrições | [V] |
| Logs | `_Default` (30 dias) e `_Required` (400 dias), ambos em `global`; só há log de atividade administrativa | [V] |
| Logs de leitura de dados (Data Access) | Sem configuração (`auditConfigs` vazio) | [V] |
| Cabeçalhos | CSP restrita, HSTS sem `preload`, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `noindex` | [V] |

### 3.2 Outros ativos

| Item | Estado | Marca |
|---|---|---|
| DNS | Hostinger; só TXT `hosting-site`; sem MX, SPF, DMARC, CAA e DNSSEC | [V] |
| Código | GitHub privado `orgateccloud-bot/SiteOrgatec`; proteção de branch indisponível no plano atual | [V] |
| Dependências Python | `pip-audit` sem vulnerabilidade conhecida em `backend/requirements.txt`; dependências npm não auditadas | [V] |
| Automação | Tarefas `ORGATEC\JanelaCampo*`, `OrgatecIA*`, `ORGATEC_Backup_Diario` no mesmo PC | [V] |
| Painel público de pendências | Sem detalhes de senhas ou caminhos nos termos que busquei | [V] |
| `gcloud` no PC | Corrigido pelo usuário: a conta ORGATEC está ativa desde 04/11/2026. A conta pessoal segue registrada no PC | [V] |

### 3.3 Conta Google: visão completa (leitura com `gcloud`)

A conta enxerga 13 projetos: é proprietária de 12 e não tem acesso à política do 13º (`future-subject-83hq8`, em pasta, com faturamento ligado em outra conta, que parece gerenciado pelo Google [NC]).

| Item | Estado | Marca |
|---|---|---|
| Organização | `orgatec-cloud-org` contém `orgatec-contabilidade`, `project-1d1a0887-…` e `project-f590d388-…`. Os outros 9 projetos estão fora | [V] |
| Projetos sem uso claro | 5 projetos chamados "ORGATEC IA", além de `seu-projeto-unico-123`, `My First Project` e `Default Gemini Project` | [V] |
| Faturamento | As 3 contas listadas estão **fechadas**. Nenhum dos 12 projetos tem faturamento ativo | [V] |
| Chaves de conta de serviço | `backup-orgatec` em `orgatec` (21/01/2026) e `orgatec-sa` em `orgatec-prod` (19/01/2026), sem data de expiração | [V] |
| Cloud SQL em `orgatec-prod` | Nenhuma instância listada | [V] |
| Local dos arquivos das chaves | Desconhecido. A busca no disco foi bloqueada pelo controle de permissões, e não a repeti | [INT] |
| Conteúdo de Storage, BigQuery e Firestore nos outros projetos | Não verificado | [INT] |

Projetos esquecidos ampliam a superfície de ataque: cada um é uma permissão e, às vezes, uma chave que ninguém revisa.

### 3.4 O que não dá para ver e precisa ser verificado [INT]

- Se a conta Google tem segunda etapa, com qual método, quem conhece a senha e para onde vão os códigos de recuperação.
- Segunda etapa, bloqueio de transferência e titularidade do domínio na Hostinger.
- Dois fatores nas contas GitHub, Athenas, Supabase, gov.br e demais sistemas.
- Sistema real de produção do escritório: fluxo de documentos, estações, antivírus, compartilhamentos, backup e Wi-Fi.
- Onde estão os certificados digitais de clientes, quem os usa e como estão guardados.
- Quantidade de clientes, de empregados de clientes na folha e de pessoas com acesso.
- Contratos com clientes, com a Athenas e com demais fornecedores; existência de seguro cibernético.
- Situação atual de OrgConc, OrgAudi, Mini e OrgInv, incluindo Supabase e uso da API Claude.
- Regimes e porte para saber se a ORGATEC é agente de tratamento de pequeno porte.

---

## 4. Infraestrutura Firebase e Google

### 4.1 Responsabilidade compartilhada

O Google sempre responde por rede e infraestrutura; o cliente sempre responde por políticas de acesso e dados. Em serviços gerenciados, a parte do Google cresce, mas configuração e dados continuam com o cliente. [O] ([Google Cloud](https://docs.cloud.google.com/architecture/framework/security/shared-responsibility-shared-fate))

| Camada | Google | ORGATEC |
|---|---|---|
| Centros de dados, hardware, rede | Responsável | Sem atuação |
| Criptografia em repouso e em trânsito | Fornece | Decide o que guardar e por quanto tempo |
| CDN e certificado do Hosting | Opera e renova | Mantém o TXT no DNS; autoriza `letsencrypt.org` e `pki.goog` se criar CAA |
| Disponibilidade do Firestore e do Cloud Run | Cumpre o SLA, com crédito como remédio | Desenha para falhas; o SLA não paga o prejuízo |
| Regras do Firestore | Executa | **Escreve e testa.** Regra errada é falha da ORGATEC |
| IAM e contas | Fornece | **Define quem acessa.** Servidor com conta de serviço ignora as regras do Firestore |
| Backup do Firestore | Fornece PITR e agendamento | **Liga, paga, testa e restaura** |
| Conta Google, senha e segunda etapa | Exige MFA em consoles | **Protege a conta e a recuperação** |
| Código, dependências, segredos | Fornece ferramentas | Responsável integral |
| Logs | Fornece os dois buckets | Define retenção, região, alertas e revisão |
| Incidente na infraestrutura do Google | Notifica sem demora indevida | **Comunica ANPD e titulares**; o relógio de 3 dias úteis é do controlador |
| Incidente por conta invadida da ORGATEC | Pode não haver ação do Google | Responsável integral |

### 4.2 Contratos

| Serviço | Termos aplicáveis | Brasil/LGPD | Marca |
|---|---|---|---|
| Firestore, Cloud Run, Logging | Google Cloud Terms e [CDPA](https://cloud.google.com/terms/data-processing-addendum) (versão de 30/10/2026) | Apêndice 3 tem seção Brazil, com LGPD, ANPD e cláusulas-padrão brasileiras | [V] |
| Firebase Hosting | Google APIs Terms, [Firebase DPST](https://firebase.google.com/terms/data-processing-terms) e Paid Services Agreement ([tabela](https://firebase.google.com/terms)) | **Sem menção a Brasil, LGPD ou ANPD** | [V] |

**Pontos do CDPA:**
- Google é processador; o cliente é controlador ou processador (seção 4.1). [O]
- Incidente: aviso "promptly and without undue delay", **sem prazo em horas** (7.2.1), enviado ao e-mail indicado pelo cliente. [V]
- Subprocessadores: aviso com 30 dias; o cliente pode se opor e encerrar em até 90 dias, sem veto (11.4). [O]
- Exclusão: até 180 dias durante o contrato; no fim, recuperação de até 30 dias, depois até 180 dias. [O]

**Consequências para a ORGATEC:**

1. **Lacuna do Hosting [I].** As [cláusulas-padrão brasileiras](https://cloud.google.com/sccs/br-c2p) do CDPA não alcançam o Hosting pelo texto, e o conjunto do Firebase não traz instrumento brasileiro. O Hosting trata IP de visitante, é global e [usou a Fastly como CDN](https://firebase.google.com/terms/subprocessors), em lista de 2021. Levar à assessoria jurídica.
2. **Papel de "parte designada" [O].** Nas cláusulas C2P, o exportador, ou seja, o cliente do Google, é a parte designada para transparência, titulares e incidentes, com aviso à ANPD e ao titular em 3 dias úteis e documento público em português. Não confirmei qual módulo se aplica à ORGATEC: depende do endereço do Google contratante e da condição de país adequado. [NC]
3. **Plano gratuito [NC].** Nenhum texto oficial diz como Spark ou Blaze muda a aplicação do DPST ou do CDPA. Tratar como pendência e revisar ao ativar o faturamento.
4. **Limite de responsabilidade [O].** Google Cloud: taxas pagas em 12 meses. Firebase Paid Services: 6 meses de taxas. No plano gratuito, o crédito tende a zero. [I] O prejuízo real fica com a ORGATEC.

### 4.3 Localização e transferência internacional

| Dado | Onde fica | Consequência sob a LGPD | Marca |
|---|---|---|---|
| Conteúdo do Firestore | São Paulo, múltiplas zonas; local imutável | Compromisso contratual de residência para Customer Data | [O] |
| Metadados (identificadores, rótulos) | Fora do compromisso de residência | Não colocar dado pessoal em nome de coleção, ID ou rótulo | [O] |
| Telemetria e Service Data (inclui IPs) | Pode sair do país, em operações centralizadas | Declarar na política de privacidade | [O] |
| Arquivos e IP no Hosting | CDN global; [IP retido por "a few months"](https://firebase.google.com/support/privacy) | Transferência provável; prazo exato desconhecido | [O] |
| Logs | **`global`, inclusive para os buckets atuais** [V]; bucket existente não muda de local | Criar bucket em `southamerica-east1` e redirecionar o sink `_Default` antes da API | [O] |
| Firebase Authentication | [EUA](https://firebase.google.com/support/privacy) | Transferência internacional se o painel com login for ativado | [O] |
| Backup do Firestore | Mesmo local do banco | Não cobre perda da região | [O] |

Base legal: LGPD, arts. 33 a 36, e [Resolução CD/ANPD nº 19/2024](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-19-de-23-de-agosto-de-2024), com prazo de adequação de 12 meses já vencido pela contagem [I] e documento público em português exigido na transparência. [O] Nenhum termo do Google cita o número da resolução. [O] A retificação de 18/08/2025 não foi lida. [NC]

### 4.4 Continuidade do orgatec.io

| Serviço | SLA oficial | Parada mensal permitida (30 dias) [I] | Remédio |
|---|---|---|---|
| [Hosting](https://firebase.google.com/terms/service-level-agreement) | 99,95% | 21,6 min | Crédito de 10% ou 30%, só sobre taxas pagas |
| [Firestore regional](https://cloud.google.com/firestore/sla) | 99,99% | 4,3 min | Crédito de até 50%, remédio único |
| [Cloud Run](https://cloud.google.com/run/sla) | 99,95% | 21,6 min | Crédito de até 50%, remédio único |

**O precedente:** em 12/06/2025, uma alteração de política replicada globalmente derrubou serviços do Google Cloud, com São Paulo entre as localidades afetadas. As fontes oficiais divergem na duração: [cabeçalho do relatório](https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW) de 10:51 a 18:18 (Pacífico), mini relatório de 3 horas e histórico de 2h54 para Firestore e Cloud Run. O [Hosting](https://status.firebase.google.com/products/hhAxKbKdeaqncSsxMwEx/history) registrou interrupção da API por 2h15. [O] Uma falha assim é global: replicação regional não protege dela.

| Serviço | Estado atual | RTO meta | RPO meta | Como alcançar |
|---|---|---|---|---|
| Site institucional | Código no git e versões no Hosting; rollback possível só no canal live | 4 h (falha nossa); 24 h (falha do Google) | Zero para o código; `site/dados/` em até 8 h | Testar rollback; preparar cópia estática em outro provedor, com troca de DNS na Hostinger |
| API e formulários | Fora do ar; fallback atual pelo WhatsApp | 8 h | 15 min | PITR (uma versão por minuto, 7 dias) |
| Banco do Firestore | Vazio, com proteção contra exclusão e sem backup | 8 h | 15 min; 24 h por backup | PITR + backup diário + proteção contra exclusão. A restauração cria banco novo, sem regras |
| Perda da região | Sem cobertura | 72 h | 24 h | Não existe multirregião na América do Sul; exportar para fora da região exige avaliar transferência |
| Boletim automático | Depende do PC | 24 h | 8 h | Levar ao Cloud Scheduler (T20) |
| Conta Google perdida | **Sem plano** | 72 h | Não se aplica | Segundo proprietário e organização |

**Riscos específicos do plano Spark e Blaze:**
- **Spark:** ao exceder a cota do Hosting, há tolerância curta e depois [o site fica desativado até o início do mês seguinte](https://firebase.google.com/docs/hosting/usage-quotas-pricing). As páginas oficiais divergem sobre a cota gratuita: 10 GB por mês ou 360 MB por dia. [O]
- **Blaze:** [orçamento não limita gasto](https://docs.cloud.google.com/billing/docs/how-to/budgets), e [teto de gasto não cobre Hosting, Firestore e Cloud Run](https://firebase.google.com/docs/projects/billing/spend-caps). Um ataque vira conta (denial of wallet). [O]
- **Abandono:** projeto [suspenso por mais de 9 meses é marcado para exclusão](https://docs.cloud.google.com/resource-manager/docs/project-suspension-guidelines). Sem proprietário, vira órfão. [O]
- **Exclusão:** projeto excluído pode ser [restaurado em até 30 dias](https://docs.cloud.google.com/resource-manager/docs/delete-restore-projects), mas alguns dados podem não voltar. [O]
- **Prévias:** são [públicas para quem tem o link e usam o backend real](https://firebase.google.com/docs/hosting/test-preview-deploy). Com a API no ar, formulário em prévia grava em produção. Use um projeto separado para testes. [O]

---

## 5. Base normativa

### 5.1 Mudanças recentes que invalidam citações antigas

| Norma | O que mudou | Marca |
|---|---|---|
| [Lei 15.352/2026](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/L15352.htm) | ANPD agora é **Agência Nacional de Proteção de Dados** | [V] |
| [Lei 15.397/2026](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/L15397.htm) | CP, art. 171: novo caput e § 2º-A; § 5º revogado. Efeito na ação penal exige parecer | [O] |
| [LC 236/2026](https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp236.htm) | CTN: art. 174 com § 1º e incisos; art. 138 alterado | [O] |
| [Decreto 12.975/2026](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12975.htm) | Alterou o Decreto 8.771/2016; arts. 13 a 16 mantidos | [O] |
| IN RFB 2.237/2024 | Substituiu a IN RFB 2.005/2021 na DCTFWeb | [O] |
| Res. CFC 1.703/2023 | Revogou o art. 11 da Res. CFC 1.590/2020; o PDF ainda o exibe | [O] |
| Res. CD/ANPD 4/2023 | Dosimetria em consulta pública de revisão, de 15/10 a 30/11/2026 | [O] |

### 5.2 Comunicação obrigatória: prazos

| Obrigação | Prazo | Quem | Base |
|---|---|---|---|
| Comunicar incidente à ANPD | **3 dias úteis** do conhecimento de que o incidente afetou dados pessoais | Controlador | [Res. CD/ANPD 15/2024](https://bibliotecadigital.mj.gov.br/bitstream/1/12879/2/RES_ANPD_2024_15.html), art. 6º [V] |
| Complementar a comunicação | 20 dias úteis, de forma fundamentada | Controlador | Art. 6º, § 3º [V] |
| Comunicar titulares | **3 dias úteis**, individualmente quando possível; se inviável, aviso público visível por pelo menos 3 meses | Controlador | Art. 9º e § 3º [V/O] |
| Declarar à ANPD que comunicou titulares | Até 3 dias úteis após o prazo | Controlador | Art. 9º, § 4º [O] |
| Registrar **todo** incidente, comunicado ou não | Guarda mínima de 5 anos | Controlador | Art. 10 [V] |
| Pequeno porte | Prazos em dobro, ou seja, 6 e 40 dias úteis pela conta | Se enquadrada | Art. 6º, § 8º; art. 9º, § 6º; Res. CD/ANPD 2/2022, art. 14 [V] |
| Comunicar ao Coaf | 24 horas, sem dar ciência ao envolvido | Escritório | Lei 9.613/1998, art. 11; Res. CFC 1.721/2024, art. 6º [O] |
| Declarar não ocorrência ao CFC | Até 31/01 | Escritório | Res. CFC 1.721/2024, art. 7º [O] |

**Critério de comunicação (art. 5º) [V]:** o incidente precisa poder afetar significativamente interesses e direitos fundamentais e, ao mesmo tempo, envolver ao menos um destes: dados sensíveis; de crianças, adolescentes ou idosos; financeiros; de autenticação; **protegidos por sigilo legal, judicial ou profissional**; ou em larga escala. Dados de escritório contábil costumam cair em mais de uma dessas hipóteses.

**Controlador ou operador: a questão central.** O dever de comunicar é do controlador. Em folha e escrita fiscal feitas para o cliente, a ORGATEC tende a atuar como operadora, e o cliente, como controlador. Em dados próprios e em deveres legais próprios, como os do Coaf, tende a ser controladora. A classificação depende de contrato e de análise caso a caso. [I]

A LGPD não dá ao operador um prazo em dias para avisar o controlador. Por isso **o contrato precisa fixar esse prazo**. Sugestão: até 24 horas. O relógio do cliente corre a partir do conhecimento dele, mas atraso da ORGATEC gera risco de responsabilização.

**Regra prática:** opere sempre com 3 dias úteis, mesmo que a ORGATEC venha a ser pequeno porte. O enquadramento precisa ser comprovado e não se aplica a tratamento de alto risco (Res. 2/2022, arts. 3º e 4º). [O]

### 5.3 Referências por tema

| Tema | Referência | O que importa |
|---|---|---|
| Proteção de dados | [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm), arts. 6º, 7º, 11, 33 a 37, 39, 41 a 50, 52 | Segurança (46 a 49), incidente (48), reparação (42 a 45), sanção de até 2% do faturamento no Brasil, limitada a R$ 50 milhões por infração (52) |
| ANPD | Res. 2/2022, 4/2023, 15/2024, 18/2024, 19/2024; [guia para pequeno porte](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-sobre-seguranca-da-informacao-para-agentes-de-tratamento-de-pequeno-porte) | Não localizei regulamento de padrões mínimos do art. 46; o tema está na agenda regulatória. Ausência em índice não é prova |
| Internet | [Marco Civil](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm), arts. 10, 13, 15; [Decreto 8.771/2016](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/decreto/d8771.htm), arts. 13 a 16 | Registros de acesso por 6 meses para provedor de aplicação com fins econômicos; padrões de segurança |
| Crimes | [CP](https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm), arts. 154, 154-A, 154-B, 171; Leis 12.737/2012 e 14.155/2021 | Segredo profissional, invasão de dispositivo, fraude eletrônica |
| Contábil | [DL 9.295/1946](https://www.planalto.gov.br/ccivil_03/decreto-lei/del9295.htm); [NBC PG 01](https://www1.cfc.org.br/sisweb/SRE/docs/NBCPG01.pdf), item 4(c) e 5(l); [NBC PG 100 (R1)](https://www1.cfc.org.br/sisweb/SRE/docs/NBCPG100(R1).pdf), R114; [Res. CFC 1.590/2020](https://www1.cfc.org.br/sisweb/SRE/docs/Res_1590.pdf), arts. 1º, 2º, 6º, 7º, 9º e 10; [ITG 2000 (R1)](https://www1.cfc.org.br/sisweb/SRE/docs/ITG2000(R1).pdf) | Sigilo, vedação de reter documentos, contrato escrito, devolução de documentos e arquivos eletrônicos, guarda |
| PLD/FT | [Lei 9.613/1998](https://www.planalto.gov.br/ccivil_03/leis/l9613compilado.htm), arts. 9º a 12; [Res. CFC 1.721/2024](https://www1.cfc.org.br/sisweb/SRE/docs/RES_1721.pdf) | Cadastro, registros por no mínimo 5 anos, comunicação |
| Responsabilidade | [CC](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), arts. 1.177, 1.178, 1.194; [CTN](https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm), arts. 134, 135, 137, 173, 174, 195 | Contador responde por culpa ao preponente e por dolo, solidariamente, a terceiros. Contadores não constam do rol do art. 134 |
| Guarda fiscal | [Lei 8.218/1991](https://www.planalto.gov.br/ccivil_03/leis/l8218compilado.htm), arts. 11 e 12 | Arquivos digitais até o prazo decadencial e multas |
| Certificação | [MP 2.200-2/2001](https://www.planalto.gov.br/ccivil_03/mpv/antigas_2001/2200-2.htm) | Presunção de veracidade do que for assinado com ICP-Brasil |
| Política pública | [Decreto 11.856/2023](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11856.htm) e [Decreto 12.573/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12573.htm) | Sem obrigação direta para escritório privado |

**Multas transferíveis a clientes por perda de prazo:**

| Obrigação | Penalidade | Marca |
|---|---|---|
| DCTFWeb | 2% ao mês ou fração sobre os tributos, limitado a 20%; mínimo de R$ 200 ou R$ 500 (IN RFB 2.237/2024, art. 11) | [O] |
| ECF | 0,25% ao mês sobre o lucro antes de IR/CSLL, limite de 10%, com tetos (DL 1.598/1977, art. 8º-A) | [O] |
| ECD | Lei 8.218/1991, art. 12 | [O] |
| Empregados | CLT, arts. 29-A, 29-B, 47 e 47-A. Não localizei multa própria "por atraso no eSocial": a penalidade vem da obrigação de fundo | [O] |
| FGTS | Lei 8.036/1990, art. 23, § 2º. Atenção: a prescrição trintenária do § 5º foi declarada inconstitucional no Tema 608 do STF | [O] |
| EFD-Contribuições, EFD-ICMS/IPI, EFD-Reinf | Multa específica **não confirmada** | [NC] |

### 5.4 Normas técnicas: edição vigente

| Norma | ISO/IEC | ABNT NBR | Observação |
|---|---|---|---|
| 27001 | :2022 + Amd 1:2024 | :2022 Versão Corrigida:2023 + Emenda 1:2024 | Sistema de gestão |
| 27002 | :2022 | :2022 | Controles: 93 em 4 temas [O] |
| 27005 | :2022 | :2023 | Risco em segurança |
| 27017 | **:2026** | :2016 | ABNT defasada em relação à ISO |
| 27018 | :2025 | **:2026** | Dados pessoais em nuvem pública |
| 27031 | :2025 | **:2026** | Prontidão de TIC para continuidade |
| 27035 | Partes 1 e 2 :2023; 3 :2020; 4 :2024 | 1 e 2 :2023; 3 :2021; parte 4 não localizada | Gestão de incidentes |
| 27701 | **:2025** | **:2026** | Privacidade; edição nova |
| 22301 | :2019 + Amd 1:2024 (em revisão) | :2020 + Emenda 1:2024 | Continuidade |
| 22313 | :2020 (em revisão) | :2020 | Orientação da 22301 |
| 31000 | :2018 (em revisão) | :2018 | Gestão de riscos |
| IEC 31010 | :2019 | :2021 | Técnicas de avaliação |

---

## 6. Papéis no incidente

| Papel | Titular sugerido | Responsabilidade |
|---|---|---|
| Líder do incidente | Direção | Decide contenção, custo e comunicação externa |
| Técnico | Responsável de TI ou fornecedor contratado [INT] | Contém, preserva evidência, restaura |
| Encarregado | A nomear (pendência C4) | Avalia risco, conduz ANPD e titulares |
| Responsável técnico | Robson Alain Veloso | Prazos fiscais e relação com CRC e clientes |
| Jurídico | Assessoria externa [INT] | Enquadramento, sigilo, contratos, boletim de ocorrência |
| Firebase e Google | Esta sessão, sob autorização | Leitura, diagnóstico, rollback. **Não entra com senha e não altera conta** |

---

## 7. Base empírica

Só entram números conferidos no publicador, salvo aviso. **Nenhuma destas fontes mede escritórios contábeis brasileiros pequenos.** Servem como direção, não como probabilidade.

| Fonte | Dado | Limite |
|---|---|---|
| [Verizon DBIR 2026](https://www.verizon.com/business/resources/Tf72/reports/2026-dbir-data-breach-investigations-report.pdf) | Terceiros em 48% das violações; elemento humano em 62%; ransomware em 48% | Global |
| DBIR 2026, SMB | Menos de 1.000 funcionários: terceiros 55%; humano 45%; cerca de 96% das vítimas de ransomware com porte conhecido eram SMB | Não significa que 96% das SMB são atacadas |
| DBIR 2026, América Latina e Caribe | Vulnerabilidades 44%, phishing 20%, credenciais 5%; terceiros 74%; humano 57% | Sem recorte Brasil |
| DBIR 2026, serviços profissionais | 3.578 incidentes, 2.558 violações; dados internos 80%, credenciais 31% | Sem % de terceiros ou vetor |
| [Sophos Brasil 2026](https://assets.sophos.com/X24WTUEQ/at/wbtb698jnfr55j7gcmgm6n/sophos-state-of-ransomware-in-brazil-2026-ptbr.pdf) | Dados criptografados em 56%; 45% pagaram; backup em 85%; 58% recuperam em até 1 semana; 18% levam 1 a 6 meses | **n=71, empresas de 100 a 5.000 funcionários** |
| [IBM 2026](https://www.ibm.com/reports/data-breach) | Custo médio global de US$ 4,99 milhões; ransomware em 39% dos incidentes | Grandes organizações |
| IBM 2026, Brasil | R$ 7,44 milhões (só em imprensa) | **[NC]** Não usar como dado do publicador |
| [ANPD, painéis](https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca) | Comunicações: 186 (2021), 275, 352, 333, 395 (2025), 646 (2026, parcial) | Mede quem comunica, não a incidência. O relatório da ANPD traz 336 para 2024 |
| [Lista de sancionadores da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/decisoes-em-processos-sancionadores) | 10 processos listados. Não localizei multa a empresa privada por incidente | Sem total oficial de sanções |
| [CERT.br](https://stats.cert.br/incidentes/) | 470.885 notificações em 2025; 472.259 de jan a set/2026, puxadas por DoS (94.264) | Notificações voluntárias |
| [IRS](https://www.irs.gov/newsroom/security-summit-irs-reminds-tax-pros-to-guard-against-identity-theft-as-summer-series-wraps-up) | Quase 300 violações em profissionais de imposto nos EUA no 1º semestre de 2025, até 250.000 clientes | É o melhor análogo setorial; país diferente |
| [Coveware 2º tri/2026](https://coveware.com/2026/07/adverse-cyber-extortions-are-more-common-than-commonly-advised/) | Serviços profissionais em 13,1% dos casos | Base própria |
| [BC, Circuito Pix](https://www.bcb.gov.br/content/estabilidadefinanceira/pix/MED/MED_2-0_Circuito_Pix-Dia_1.pdf) | MED recuperou, em média, 9,3% do valor contestado em 2025 | Lido só por índice de busca |

**Casos úteis:**
- **[M.E.Doc/NotPetya (2017)](https://www.cisa.gov/news-events/alerts/2017/07/01/petya-ransomware):** backdoor no software fiscal-contábil ucraniano levou a ataque destrutivo. É o caso-referência de cadeia de suprimentos contábil.
- **[Wojeski & Co. (EUA)](https://ag.ny.gov/press-release/2025/attorney-general-james-announces-settlement-accounting-firm-failing-protect-new):** firma contábil, ransomware em 2023, segunda violação em 2024, aviso tardio, multa de US$ 60.000.
- **[Operação Obsidiana (2025)](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/abril/operacao-obsidiana-receita-federal-e-policia-federal-combatem-falsa-consultoria-tributaria-que-causou-prejuizo-de-r-450-milhoes):** falsa consultoria obtinha procuração no e-CAC e fez compensações fictícias: R$ 451,5 milhões e 496 contribuintes. Foi fraude com procuração dada pelo cliente, não invasão.
- **[Falha nas guias em 20/05/2025](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/maio/copy_of_comunicado-receita-federal-informa-indisponibilidade-momentanea-no-sistema-de-emissao-de-documentos-de-arrecadacao):** DARF e DAE prorrogados para até 28/05. Prorrogação existe, mas não é automática.

**Números a evitar:** "60% das PMEs fecham em 6 meses" ([sem fonte rastreável](https://www.bankinfosecurity.com/blogs/60-hacked-small-businesses-fail-how-reliable-that-stat-p-2464)); "40% nunca reabrem" (FEMA) e "93% quebram" (NARA), sem fonte primária localizada; bilhões de "tentativas de ataque" (Fortinet) e ataques semanais (Check Point), que medem ruído de telemetria; "US$ 10 bilhões" do NotPetya como número oficial.

---

## 8. Mapa de riscos

Notas do estado atual, antes das ações da seção 12.

| ID | Evento | P | I | C | Nível | Confiança |
|---|---|---|---|---|---|---|
| SI-08 | Fraude eletrônica e uso do nome da ORGATEC | 4 | 4 | 16 | Alta | Média |
| SI-12 | Segredos expostos | 4 | 4 | 16 | Alta | Média |
| SI-01 | Ransomware e malware | 3 | 5 | 15 | Alta | Baixa |
| SI-02 | Phishing e engenharia social | 5 | 3 | 15 | Alta | Média |
| SI-03 | Comprometimento de contas de administração | 3 | 5 | 15 | Alta | Média |
| SI-04 | Certificado digital e procuração eletrônica | 3 | 5 | 15 | Alta | Baixa |
| SI-06 | Vazamento de dados de clientes | 3 | 5 | 15 | Alta | Baixa |
| SI-10 | Falha ou ataque em terceiros | 3 | 5 | 15 | Alta | Média |
| CN-02 | Perda de dados por backup inexistente | 3 | 5 | 15 | Alta | Baixa |
| CN-01 | Ponto único: PC e automações | 4 | 3 | 12 | Alta | Alta |
| CN-03 | Sistema contábil indisponível | 3 | 4 | 12 | Alta | Baixa |
| CN-04 | Sistemas do governo fora do ar no vencimento | 4 | 3 | 12 | Alta | Média |
| CN-05 | Perda de prazo com dano ao cliente | 3 | 4 | 12 | Alta | Baixa |
| SI-13 | IA e automações com dados de clientes | 3 | 4 | 12 | Alta | Baixa |
| CN-06 | Pessoa-chave | 2 | 5 | 10 | Média | Média |
| CN-07 | Sinistro físico e infraestrutura local | 2 | 5 | 10 | Média | Baixa |
| CN-10 | Efeito em cascata na carteira | 2 | 5 | 10 | Média | Baixa |
| SI-07 | Indisponibilidade e negação de serviço | 3 | 3 | 9 | Média | Alta |
| CN-11 | Incidente no cliente (LOCAR e ligadas) | 3 | 3 | 9 | Média | Baixa |
| SI-09 | Ameaça interna | 2 | 4 | 8 | Média | Baixa |
| SI-11 | Sequestro de domínio e DNS | 2 | 4 | 8 | Média | Média |
| CN-09 | Sanção regulatória e profissional | 2 | 4 | 8 | Média | Média |
| CN-12 | Reputação e concentração de carteira | 2 | 4 | 8 | Média | Baixa |
| CN-08 | Suspensão ou perda do projeto Google | 2 | 3 | 6 | Média | Alta |
| SI-05 | Configuração incorreta de Firebase e Google | 2 | 3 | 6 | Média (12 após a API) | Alta |

---

## 9. Frente 1: segurança da informação

As respostas citam a **Trilha A** (incidente com dado pessoal) da seção 11. O mesmo vale para a Frente 2. Controles entre parênteses são da ABNT NBR ISO/IEC 27002:2022, com a ressalva da seção 2.3.

### SI-01 · Ransomware e malware

**Criticidade 15 (alta).** RTO meta 24 h para operação essencial · RPO 24 h · MTTD 1 h · MTTR 72 h.

- **Cenário.** Malware por anexo, acesso remoto exposto ou vulnerabilidade criptografa estações e arquivos e rouba dados antes (dupla extorsão). No Brasil, a amostra da Sophos aponta e-mail malicioso em 37% das causas técnicas, com ressalva de porte.
- **Riscos.** Parada em semana de vencimento, vazamento sob sigilo profissional, perda de certificado A1 armazenado em disco.
- **Firebase/Google.** O site e os dados do Hosting ficam fora do alcance direto. Mas um PC infectado com sessão do Firebase CLI ou do GitHub pode publicar ou alterar conteúdo como proprietário.
- **Prevenção.** EDR ou antimalware gerenciado (8.7); atualização (8.8); privilégio mínimo (8.2); segmentação (8.22); backup offline ou imutável, testado (8.13); acesso remoto só com MFA (8.5).
- **Resposta.** Isolar da rede sem desligar, preservar evidência (5.28), acionar Trilha A e boletim de ocorrência. **Não pagar por padrão:** decisão da direção com jurídico. Pagar não elimina o dever de comunicar nem garante apagamento.
- **Recuperação.** Reconstruir em máquina limpa, restaurar de cópia verificada, trocar credenciais, reemitir certificados e reabrir serviços por prioridade da BIA.
- **Normas.** LGPD, arts. 46 a 49; Res. 15/2024; CP, art. 154-A; ISO 27035.

### SI-02 · Phishing e engenharia social

**Criticidade 15 (alta).** MTTD 15 min pelo relato do usuário · MTTR 4 h · meta de clique em simulação abaixo de 5%.

- **Cenário.** E-mail ou WhatsApp simula Receita, CFC, cliente ou diretoria. Há alertas oficiais de [remetente falso da Receita](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/abril/receita-federal-alerta-criminosos-simulam-enderecos-de-e-mail-do-orgao-para-aplicar-golpes), de [Pix em nome de terceiro](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/outubro/receita-federal-alerta-para-novo-golpe-envolvendo-transacoes-financeiras) e de [cobrança falsa de anuidade](https://cfc.org.br/noticias/alerta-de-golpe-fiquem-atentos-a-mensagens-com-cobranca-indevida-de-anuidades/).
- **Riscos.** Roubo de senha, instalação de malware, pagamento indevido. O escritório recebe anexos de terceiros o dia todo, o que normaliza o comportamento que o golpe explora.
- **Firebase/Google.** Phishing do Google visa à conta proprietária. SMS ainda é aceito como segunda etapa: prefira chave de acesso.
- **Prevenção.** Treinamento mensal curto com exemplos do setor (6.3); filtro de e-mail (8.23); canal de relato sem punição (6.8); confirmação por telefone conhecido.
- **Resposta.** Bloquear conta, trocar senha, revogar sessões e verificar regras de encaminhamento. Com dado exposto, Trilha A.
- **Recuperação.** Revisar outras caixas alcançadas e usar o caso no treinamento (5.27).
- **Normas.** LGPD, art. 46; CP, art. 171, § 2º-A; NBC PG 01, item 4(c).

### SI-03 · Comprometimento de contas de administração

**Criticidade 15 (alta).** RTO 4 h · MTTD 1 h · MTTR 24 h.

- **Cenário.** Invasão de `orgatec.cloud@gmail.com`, Hostinger, GitHub, gov.br, Athenas ou Supabase. A conta Google é hoje ponto único do projeto, e pode ser também a caixa dos alertas.
- **Riscos.** Publicar conteúdo falso em `orgatec.io`, excluir o projeto, trocar o DNS, ler dados, redirecionar e-mail.
- **Firebase/Google.** O proprietário [gerencia papéis e faturamento, exclui e restaura projeto](https://firebase.google.com/docs/projects/iam/roles-basic). O projeto está fora da organização `orgatec-cloud-org`, logo não herda política central nem Security Command Center Standard. As chaves sem validade de `orgatec` e `orgatec-prod` são outro caminho de acesso, sem segunda etapa. O Google recomenda [mais de um proprietário e migrar produção para organização](https://docs.cloud.google.com/resource-manager/docs/project-suspension-guidelines). A MFA é [obrigatória para contas pessoais em consoles desde 12/05/2025](https://docs.cloud.google.com/docs/authentication/mfa-requirement), mas o método atual não foi verificado. Duas contas registradas no `gcloud` do PC aumentam a chance de erro humano.
- **Prevenção.** Conta individual para cada pessoa (5.16), chave de acesso (8.5), revisão trimestral (5.18), conta de emergência guardada offline (8.2), alerta para `SetIamPolicy`, Workspace ou Cloud Identity no domínio (5.23).
- **Resposta.** Recuperar a conta pelo [fluxo do Google](https://docs.cloud.google.com/resource-manager/docs/project-suspension-guidelines), remover acessos estranhos, conferir o log de atividade (400 dias), fazer rollback do Hosting. Trilha A se houve acesso a dados.
- **Recuperação.** Rotacionar credenciais, conferir DNS, domínios, chaves e canais de prévia.
- **Normas.** LGPD, art. 46; Decreto 8.771/2016, art. 13; ISO 27017.

### SI-04 · Certificado digital e procuração eletrônica

**Criticidade 15 (alta).** RTO 8 h para revogar · MTTD 24 h · MTTR 5 dias úteis.

- **Cenário.** Certificado A1 de cliente em pasta compartilhada, senha anotada, ou procuração eletrônica usada fora do combinado. **É o risco mais próprio de um escritório contábil.**
- **Riscos.** Transmissão de declaração falsa, compensação fraudulenta, alteração cadastral e acesso a dados fiscais, com presunção de veracidade do que for assinado (MP 2.200-2/2001, art. 10).
- **Evidência.** A Receita [desaconselha entregar credencial ou certificado a terceiros, inclusive contadores](https://www.gov.br/fazenda/pt-br/assuntos/noticias/2023/maio/receita-federal-alerta-contribuintes-para-casos-de-acessos-nao-reconhecidos-ao-portal-e-cac), e indica a procuração eletrônica. A Operação Obsidiana mostra o potencial de dano da procuração.
- **Prevenção.** Inventário com responsável e validade (5.9), procuração eletrônica com serviços mínimos e prazo curto (5.15), cofre para certificados restantes (8.24), token A3 físico para o certificado do escritório, registro de uso, revisão trimestral.
- **Resposta.** Revogar o certificado na autoridade certificadora, cancelar a procuração, avisar o cliente no mesmo dia, consultar a caixa postal e o histórico no e-CAC, boletim de ocorrência e Trilha A.
- **Recuperação.** Emitir novo certificado, revisar transmissões do período e pedir retificação do que for indevido.
- **Normas.** MP 2.200-2/2001; NBC PG 01; CP, arts. 154-A e 171; LGPD, art. 46.

### SI-05 · Configuração incorreta de Firebase e Google

**Criticidade 6 hoje; 12 quando a API tiver dados.** MTTD 24 h · MTTR 4 h.

- **Cenário.** Regra aberta por engano, conta de serviço com papel amplo, segredo em variável, prévia gravando em produção, bucket público.
- **Estado.** Hoje a superfície é pequena: banco vazio, regras fechadas, chave de API restrita e sem chave de conta de serviço. [V]
- **Riscos.** Depois da API: leitura ou escrita indevida. O [modo de teste permite que qualquer um leia e sobrescreva](https://firebase.google.com/docs/firestore/quickstart), [regras não filtram dados](https://firebase.google.com/docs/firestore/security/rules-query) e [servidor ignora as regras](https://firebase.google.com/docs/firestore/security/get-started). Nesse desenho, IAM é o controle real.
- **Prevenção.** Conta de serviço só com `roles/datastore.user` (8.2), Secret Manager (8.24), publicação só por `tools/publicar.py` (8.32), projeto separado para teste (8.31), testes das regras no emulador (8.29), App Check, ressalvando que ele [previne só alguns vetores](https://firebase.google.com/docs/app-check), e logs de Data Access (8.15).
- **Resposta.** Reverter regra ou versão, avaliar acessos nos logs, Trilha A se houve exposição. Sem Data Access ligado, pode ser impossível saber o que foi lido, e a análise deve assumir o pior caso.
- **Recuperação.** Registrar a causa e acrescentar teste automatizado.
- **Normas.** ISO 27017 e 27018; LGPD, arts. 46 e 49.

### SI-06 · Vazamento de dados de clientes

**Criticidade 15 (alta).** Meta: decidir sobre a comunicação em 24 h · MTTD 24 h.

- **Cenário.** Folha enviada à empresa errada, planilha em nuvem pessoal, notebook perdido, grupo de WhatsApp, exfiltração por invasor, descarte de papel.
- **Riscos.** Dados financeiros, sigilo profissional e possíveis dados de saúde na folha (atestados, afastamentos), que são sensíveis. Salários e CPF expostos de empregados de clientes geram dano direto a titulares.
- **Firebase/Google.** Só o que for levado ao projeto. **Regra: nenhum documento de cliente no Firebase** sem decisão formal (D2). O portal segue no Athenas.
- **Prevenção.** Classificação (5.12), mínimo necessário (8.10), portal em vez de e-mail ou WhatsApp, criptografia de disco (8.24), DLP básico (8.12), mesa limpa (7.7), descarte seguro (7.14), mascaramento em testes (8.11).
- **Resposta.** Trilha A. Avisar o controlador no prazo do contrato. Pedir ao destinatário a exclusão, por escrito.
- **Recuperação.** Corrigir o processo e apoiar o cliente na comunicação aos titulares.
- **Normas.** LGPD, arts. 42 a 48 e 52; Res. 15/2024, art. 5º, V; CP, art. 154; NBC PG 01, item 4(c); NBC PG 100, R114.

### SI-07 · Indisponibilidade e negação de serviço

**Criticidade 9 (média).** RTO 4 h · MTTD 15 min · MTTR 4 h.

- **Cenário.** Queda do provedor, ataque de negação de serviço, cota do Spark excedida ou erro de publicação. O CERT.br registra alta de DoS em 2026.
- **Riscos.** Site fora do ar é prejuízo de imagem, não de operação fiscal. No Spark, estourar a cota desativa o site até o mês seguinte. Com o Blaze, o risco vira custo.
- **Firebase/Google.** [Cloud Armor com Firebase Hosting não foi confirmado](https://docs.cloud.google.com/armor/docs/security-policy-overview). A proteção do Hosting contra DDoS não tem texto específico. [NC]
- **Prevenção.** Monitor externo de disponibilidade (8.16), orçamento e alertas, limite de instâncias, cache, página de contingência.
- **Resposta.** Conferir [status do Cloud](https://status.cloud.google.com/) e [do Firebase](https://status.firebase.google.com/summary), fazer rollback se foi publicação, usar WhatsApp como canal alternativo.
- **Recuperação.** Registrar a duração, pedir crédito de SLA quando houver e avaliar a cópia em outro provedor.
- **Normas.** ISO 22301 e 27031; ISO 27002, 5.30 e 8.6.

### SI-08 · Fraude eletrônica e uso do nome da ORGATEC

**Criticidade 16 (alta).** MTTD 1 h · resposta bancária imediata.

- **Cenário.** Criminoso troca dados de pagamento, envia guia, boleto ou Pix falso em nome do escritório, ou clona o WhatsApp. O CFC já alertou sobre [nome de escritórios reais usado em golpe](https://cfc.org.br/noticias/golpe-envolvendo-a-decore-tem-prejudicado-mei-e-profissionais-da-contabilidade/).
- **Riscos.** O cliente paga ao golpista. O MED recuperou, em média, só 9,3% do valor contestado em 2025. A ORGATEC é a fonte confiável que o golpe imita.
- **Firebase/Google.** Sem SPF e DMARC, o domínio pode ser falsificado. Sem `www`, um visitante pode cair em erro e buscar links falsos.
- **Prevenção.** SPF `-all` e DMARC `p=reject` enquanto não houver e-mail; depois SPF, DKIM e DMARC reais (8.20). WhatsApp Business verificado (C5). Regra escrita: **a ORGATEC nunca muda dados bancários por mensagem**. Dupla aprovação para pagamentos.
- **Resposta.** Cliente aciona o banco de imediato para o MED; a ORGATEC registra e avisa a carteira se o golpe for amplo, pede remoção do domínio falso e faz boletim de ocorrência.
- **Recuperação.** Comunicado aos clientes e monitoramento de domínios parecidos.
- **Normas.** CP, art. 171, § 2º-A; CDC se aplicável; LGPD, arts. 42 a 45 quando houver dado vazado.

### SI-09 · Ameaça interna

**Criticidade 8 (média).** MTTD 7 dias · revogação no mesmo dia da saída.

- **Cenário.** Colaborador copia carteira ao sair, consulta dados sem motivo, altera lançamento ou desvia pagamento. Inclui erro não intencional de quem tem acesso amplo.
- **Riscos.** Violação de sigilo, fraude contábil, perda de clientes.
- **Prevenção.** Termo de confidencialidade (6.6), segregação de funções (5.3), acesso por necessidade (5.15), registro de ações (8.15), desligamento com checklist (6.5).
- **Resposta.** Preservar logs, envolver RH e jurídico, revogar acessos, Trilha A quando couber.
- **Recuperação.** Revisar lançamentos e acessos do período e medidas disciplinares (6.4).
- **Normas.** CP, art. 154; CC, arts. 1.177 e 1.178; LGPD, art. 46. Monitoramento de empregados exige base legal e aviso.

### SI-10 · Falha ou ataque em terceiros

**Criticidade 15 (alta).** Depende do contrato. Aviso do fornecedor em até 24 h como cláusula-alvo.

- **Cenário.** Incidente em Athenas, Google, Hostinger, GitHub, Supabase, autoridade certificadora ou biblioteca de software. O M.E.Doc mostrou que o software contábil pode ser o vetor.
- **Riscos.** No DBIR 2026, terceiros aparecem em 48% das violações, 55% entre SMB e 74% na América Latina e Caribe. Concentração em um único ERP e em uma única conta Google.
- **Firebase/Google.** Avisos do Google vão ao contato informado, sem prazo em horas. Não consegui ler Essential Contacts (HTTP 403). Confirme quem recebe e se a caixa é lida.
- **Prevenção.** Inventário de fornecedores (5.19), cláusulas de LGPD e incidente (5.20), avaliação anual (5.22), dependências travadas e auditadas (5.21), ativar Dependabot, plano de saída (5.23).
- **Resposta.** Exigir relatório do fornecedor, avaliar dados afetados, Trilha A. O relógio começa com o conhecimento, mesmo que a falha seja do fornecedor.
- **Recuperação.** Plano alternativo, troca de credenciais usadas no fornecedor e revisão do contrato.
- **Normas.** LGPD, arts. 39 e 42; ISO 27036 (edição não conferida [NC]); ISO 27002, 5.19 a 5.23.

### SI-11 · Sequestro de domínio e DNS

**Criticidade 8 (média).** RTO 8 h · MTTD 1 h.

- **Cenário.** Invasão da Hostinger, expiração do domínio, troca de nameserver, ou registro apontando para serviço abandonado (subdomain takeover). Atenção ao futuro CNAME `portal`.
- **Riscos.** Quem controla o DNS controla site e e-mail, e pode emitir certificado.
- **Prevenção.** Segunda etapa e bloqueio de transferência, renovação automática com alerta, DNSSEC, CAA autorizando `letsencrypt.org` e `pki.goog`, conforme a [documentação](https://firebase.google.com/docs/hosting/custom-domain), inventário de registros (5.9), HSTS `preload` depois de ativar o `www`.
- **Resposta.** Acionar a Hostinger, restaurar registros, avisar clientes e registrar o incidente.
- **Recuperação.** Conferir TXT do Hosting e reemissão do certificado, que pode levar até 24 horas.
- **Normas.** ISO 27002, 8.20 e 8.21.

### SI-12 · Segredos expostos

**Criticidade 16 (alta).** Meta: troca em até 24 h após descoberta.

- **Cenário.** Senha em documento, token em repositório, `.env` copiado, histórico do git. A pendência T12 e o plano de incorporação apontam senha do Supabase em texto claro, troca pendente de chaves do OrgConc e fragilidades no Mini. O OrgAudi não tem separação entre clientes e deve seguir interno. [O, documento interno]
- **Riscos.** Credencial válida é acesso direto, sem invasão. Em arquivo sincronizado ou no histórico, o segredo sobrevive à edição.
- **Prevenção.** Cofre de senhas (5.17), Secret Manager (8.24), varredura automática de segredos no git, `.env` fora do repositório (já aplicado neste repositório), revisão dos demais.
- **Resposta.** Trocar primeiro, limpar depois. Verificar uso indevido nos logs do serviço. Trilha A se o banco tinha dados pessoais.
- **Recuperação.** Remover do histórico, revisar acessos e documentar.
- **Normas.** LGPD, art. 46; Decreto 8.771/2016, art. 13. **A troca é feita pela ORGATEC no painel de cada serviço.**

### SI-13 · IA e automações com dados de clientes

**Criticidade 12 (alta).** Inclui agentes como os usados neste projeto.

- **Cenário.** Colar dados de clientes em IA externa, automação com credenciais amplas, agente que executa conteúdo malicioso de documento, resultado errado usado sem revisão.
- **Riscos.** Transferência a terceiro e, possivelmente, ao exterior; ação indevida com a sessão do usuário. **Observação direta:** nesta sessão, a leitura do IAM usou a sessão do Firebase CLI já salva no PC. Qualquer processo com acesso a esse perfil atua como proprietário do projeto.
- **Prevenção.** Política de uso de IA (5.10), anonimização local antes do envio (8.11), contas de automação com papel restrito em vez do proprietário, aprovação humana para ações irreversíveis, revisão técnica de todo conteúdo fiscal, separar dados de clientes de ambientes de automação.
- **Resposta.** Como SI-06 ou SI-03, conforme o efeito.
- **Recuperação.** Rotacionar sessões, revisar ações registradas.
- **Normas.** LGPD, arts. 6º, 33 e 46. A aplicação efetiva do protocolo de anonimização no OrgConc e nos demais sistemas não foi verificada. [INT]

---

## 10. Frente 2: continuidade e riscos de negócio

### CN-01 · Ponto único: PC e automações

**Criticidade 12 (alta).** RTO 24 h · RPO 8 h.

- **Cenário.** O PC que roda agendador, boletim, notícias e automações queima, é roubado ou é desligado. [V]
- **Riscos.** Site fica sem atualização e pendências ficam invisíveis. As próprias tarefas podem falhar em silêncio, como já ocorre com o backup.
- **Firebase/Google.** O boletim pode ir para o Cloud Scheduler (T20), o que depende do Blaze.
- **Prevenção.** Inventário de tarefas (5.9), alerta quando uma tarefa falha (8.16), documentação (5.37), migração para nuvem.
- **Resposta.** Ativar a rotina manual documentada em outra máquina.
- **Recuperação.** Reinstalar a partir do git. `site/dados/` e `modelos-redes/` ficam fora do git e precisam de cópia própria.
- **Normas.** ISO 22301; ISO 27002, 5.30 e 8.14.

### CN-02 · Perda de dados por backup inexistente ou não testado

**Criticidade 15 (alta).** RTO 24 h · RPO 24 h · teste de restauração trimestral.

- **Cenário.** O backup falha e ninguém percebe. Esse é o estado de `ORGATEC_Backup_Diario`. [V]
- **Riscos.** Perda de escrita e documentos que a ORGATEC deve guardar, e impossibilidade de cumprir devolução de arquivos eletrônicos (Res. CFC 1.590/2020, art. 9º). Na amostra da Sophos no Brasil, 85% das empresas com dados criptografados usaram backup: mesmo em empresas maiores, não é universal.
- **Firebase/Google.** PITR e backup agendado exigem faturamento. Hoje não há nada a proteger no Firestore, mas a ordem deve ser: proteção primeiro, dados depois.
- **Prevenção.** Regra 3-2-1 com cópia isolada (8.13), inventário do que é copiado, alerta de falha, teste de restauração registrado.
- **Resposta.** Parar alterações, identificar o último ponto bom, restaurar em ambiente separado.
- **Recuperação.** Reconstituir com o sistema contábil, clientes e fontes oficiais (SPED, e-CAC) e registrar lacunas.
- **Normas.** CC, art. 1.194; CTN, art. 195; Lei 8.218/1991, art. 11; ITG 2000; Res. CFC 1.721/2024, art. 10; ISO 27002, 8.13.

### CN-03 · Sistema contábil indisponível

**Criticidade 12 (alta).** RTO e RPO definidos pelo contrato com a Athenas. [INT]

- **Cenário.** O Athenas Online para, sofre incidente ou perde o contrato. A instância `orgatec.athenas.online` foi confirmada; a configuração interna, não.
- **Riscos.** Parada de escrita, folha e portal. Dependência alta de um único fornecedor.
- **Prevenção.** SLA por escrito, exportação periódica em formato aberto, processo manual mínimo para folha e guias (5.29), plano de saída.
- **Resposta.** Acionar suporte, avisar clientes, usar portais oficiais direto para o que vence.
- **Recuperação.** Reconciliar lançamentos feitos em contingência.
- **Normas.** ISO 27031; ISO 27002, 5.23 e 5.30; LGPD, art. 39.

### CN-04 · Sistemas do governo fora do ar no vencimento

**Criticidade 12 (alta).** RTO não controlável; meta de transmitir até D-2.

- **Cenário.** Instabilidade em e-CAC, gov.br, eSocial ou SPED perto do prazo.
- **Riscos.** Multa e juros. A prorrogação existe, mas **não é automática** e o ato pode sair depois do vencimento, como em maio de 2025.
- **Prevenção.** Calendário com folga de 2 dias úteis, pagamento antecipado quando possível, contas e certificados reservas, monitorar comunicados oficiais.
- **Resposta.** Guardar prova da indisponibilidade (print com hora, protocolo), avisar clientes, tentar outro canal.
- **Recuperação.** Transmitir assim que normalizar e pedir relevância de multa, quando couber.
- **Normas.** IN RFB 2.237/2024; legislação de cada obrigação; ato de prorrogação, quando houver.

### CN-05 · Perda de prazo com dano ao cliente

**Criticidade 12 (alta).** Meta: zero entrega fora do prazo por causa interna.

- **Cenário.** Falha de calendário, ausência de pessoa, cliente que envia tarde ou erro de cálculo.
- **Riscos.** Multa (seção 5.3), indenização e dano à relação. Responsabilidade civil por culpa (CC, art. 1.177).
- **Prevenção.** Calendário com responsável e substituto, segunda conferência, contrato com prazos de envio de documentos pelo cliente (Res. CFC 1.590/2020, art. 2º), seguro de responsabilidade profissional.
- **Resposta.** Avisar o cliente, regularizar, calcular o prejuízo e acionar o seguro.
- **Recuperação.** Causa raiz e ajuste do calendário.
- **Normas.** CC, arts. 1.177 e 1.178; CTN, arts. 135 e 137, com análise caso a caso; NBC PG 01.

### CN-06 · Pessoa-chave

**Criticidade 10 (média).** RTO 5 dias úteis.

- **Cenário.** Afastamento repentino do responsável técnico ou de quem detém senhas, relacionamentos e conhecimento.
- **Riscos.** Falta de responsável técnico registrado, procurações em nome de uma pessoa, conta Google sem sucessor.
- **Prevenção.** Substituto com habilitação, cofre com acesso de emergência, procedimentos escritos, seguro de pessoa-chave a avaliar.
- **Resposta.** Acionar substituto, informar clientes afetados.
- **Recuperação.** Regularizar responsável técnico no CRC e transferir acessos.
- **Normas.** DL 9.295/1946; ISO 22301; ISO 27002, 5.2 e 5.3. Exigências de substituição no CRC não verificadas. [NC]

### CN-07 · Sinistro físico e infraestrutura local

**Criticidade 10 (média).** Energia e internet têm probabilidade maior e impacto menor. RTO 8 h para trabalho remoto.

- **Cenário.** Incêndio, alagamento, furto, queda de energia ou de internet na sede de Formoso-GO.
- **Riscos.** Perda de equipamentos e documentos em papel. Em 2024, a calamidade no RS levou a [prorrogações oficiais](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2024/maio/prorrogados-prazos-de-vencimento-para-municipios-atingidos-pelas-chuvas-intensas-no-rio-grande-do-sul), mas só por ato específico. As emendas de 2024 às normas 27001 e 22301 tratam de mudança climática, então avalie esse fator.
- **Prevenção.** Nobreak, segunda conexão (dados móveis), trabalho remoto testado, digitalização, cofre ou armazenamento fora da sede (7.5, 7.11).
- **Resposta.** Segurança das pessoas primeiro; depois, ativar trabalho remoto.
- **Recuperação.** Seguro patrimonial, reposição de equipamentos e reconstrução de documentos.
- **Normas.** ISO 22301 e Emenda 1:2024; ISO 27002, 7.1 a 7.14.

### CN-08 · Suspensão ou perda do projeto Google

**Criticidade 6 (média).**

- **Cenário.** Suspensão por suspeita de abuso, conta invadida, inadimplência no Blaze ou inatividade.
- **Riscos.** O Google pode [suspender por pagamento em atraso e de imediato para proteger serviços](https://cloud.google.com/terms), e pode encerrar por conveniência com 30 dias. Com um único proprietário e caixa pouco lida, um aviso pode passar despercebido.
- **Prevenção.** Caixa monitorada, dois meios de pagamento, dois proprietários, cópia do site em outro provedor, conta de faturamento com administrador identificado.
- **Resposta.** Abrir contestação, publicar cópia estática e trocar o DNS.
- **Recuperação.** Restaurar o projeto e revisar a causa.
- **Normas.** Termos do Google Cloud, seções 2.4, 4 e 8.

### CN-09 · Sanção regulatória e profissional

**Criticidade 8 (média).**

- **Cenário.** Fiscalização da ANPD, processo no CRC, descumprimento da Res. CFC 1.721/2024 ou falta de encarregado e de canal do titular.
- **Riscos.** A lista de processos da ANPD não mostra multa a empresa privada por incidente, mas mostra sanção em caso de incidente no setor público e [processo aberto em 2026 contra organização social](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-instaura-processo-de-sancao-contra-organizacao-social-por-falha-na-protecao-de-dados-de-500-mil-pacientes-de-unidades-publicas-de-saude). A dosimetria está em revisão. Pendências abertas no site: V6 (retenção), C4 (dpo@) e V12 (rotinas do escritório).
- **Prevenção.** Registro de operações (LGPD, art. 37), encarregado ou canal, política de retenção, política simplificada de segurança se pequeno porte, relatório anual do Coaf em dia.
- **Resposta.** Jurídico, resposta formal no prazo, preservar documentos.
- **Recuperação.** Plano de adequação. Programa de governança pode atenuar a sanção (Res. 4/2023, art. 13).
- **Normas.** LGPD, arts. 41, 50 e 52; Res. CD/ANPD 2/2022, 4/2023 e 18/2024; Lei 9.613/1998, art. 12.

### CN-10 · Efeito em cascata na carteira

**Criticidade 10 (média), com pior caso muito alto.**

- **Cenário.** Um único incidente no escritório atinge muitos clientes ao mesmo tempo, em dados, prazos e reputação. **Este é o risco transferido à carteira.**
- **Riscos.** Múltiplos controladores com relógios próprios, múltiplas ações de reparação, multas somadas e equipe sobrecarregada. Na prática, cada cliente passa a exigir atenção no mesmo dia.
- **Prevenção.** Segmentação de pastas e acessos por cliente (8.3), lista de contatos por cliente, modelo de comunicação em massa, prioridade pactuada, seguro com limite adequado à carteira, verificação de exclusões.
- **Resposta.** Comitê único, comunicado padronizado, ordem de atendimento pela BIA.
- **Recuperação.** Relatório por cliente e reunião com os maiores afetados.
- **Normas.** LGPD, arts. 42 e 48; Res. 15/2024; Res. CFC 1.590/2020.

### CN-11 · Incidente no cliente (LOCAR e empresas ligadas)

**Criticidade 9 (média) para a ORGATEC; para o cliente, depende da avaliação dele.** [INT]

Não tive acesso a dados da LOCAR. Do acervo, sei apenas do título de um parecer sobre Locar Multserviços e Locar Transporte de Bovinos. As hipóteses abaixo precisam de validação.

- **Cenário.** Cliente sofre ransomware, perde documentos ou tem e-mail invadido. Em empresas ligadas, sistemas, sócios e contas compartilhados espalham o incidente.
- **Riscos.** Falta de XML e de folha para fechar o mês, contaminação por anexo enviado ao escritório, fraude em pagamentos com a ORGATEC como intermediária, conflito sobre responsabilidade. Em transporte de carga, a parada de documentos fiscais eletrônicos ou de dados de motoristas pode interromper operação. [I]
- **Prevenção.** Portal como canal único, varredura de anexos, separação de cada CNPJ, cláusula de responsabilidade, plano mínimo do cliente, orientação sobre procuração eletrônica e pagamento.
- **Resposta.** Separar a ligação com o cliente afetado, apoiar com dados fiscais disponíveis, sem assumir papel de controlador. Registrar orientações.
- **Recuperação.** Reconstruir escrita por fontes oficiais (XML, e-CAC, eSocial).

**Dados a coletar com o cliente:** contratos e papéis LGPD; lista de CNPJs ligados e sócios comuns; sistemas de frota, documentos fiscais e folha; responsável por TI; contatos 24 horas; prazos críticos; certificados e procurações; seguros; volume de empregados.

### CN-12 · Reputação e concentração de carteira

**Criticidade 8 (média).** Depende da distribuição de receita. [INT]

- **Cenário.** Incidente público, perda do cliente maior ou de grupo econômico inteiro.
- **Riscos.** Saída de vários clientes de uma vez. Empresas ligadas costumam sair juntas. Confiança é o principal ativo do escritório.
- **Prevenção.** Medir concentração (receita dos 5 maiores), plano de comunicação, porta-voz único, transparência contratual sobre segurança.
- **Resposta.** Fala factual, sem minimizar, alinhada com o jurídico.
- **Recuperação.** Plano de melhoria compartilhado com clientes.
- **Normas.** ISO 22301; ISO 31000.

---

## 11. Trilha comum de resposta e recuperação

### Trilha A: incidente com possível dado pessoal

| Tempo | Ação | Responsável |
|---|---|---|
| Até 1 h | Registrar hora do conhecimento. Abrir o registro do incidente. Conter sem apagar evidência | Quem detectou e líder |
| Até 4 h | Reunir líder, técnico, encarregado e jurídico. Definir se a ORGATEC é controladora ou operadora em cada conjunto de dados | Líder |
| Até 24 h | Avisar controladores (clientes), conforme contrato. Avaliar risco pelo art. 5º da Res. 15/2024. Acionar seguro, se houver. Boletim de ocorrência | Encarregado e jurídico |
| Até 3 dias úteis | Se controladora e com risco relevante: comunicar ANPD pelo formulário eletrônico e titulares, informando o conteúdo do art. 6º, § 2º, e do art. 9º | Encarregado |
| Até 3 dias úteis após | Declarar à ANPD a comunicação aos titulares | Encarregado |
| Até 20 dias úteis | Complementar a comunicação | Encarregado |
| Sempre | Guardar registro por no mínimo 5 anos, mesmo sem comunicação | Encarregado |

**Avisos importantes:**
- Se a informação estiver incompleta, comunique assim mesmo no prazo e complemente depois.
- Não prometa aos titulares o que ainda não foi apurado.
- O sigilo profissional tem exceção legal; antes de entregar dados a terceiros, consulte o jurídico.
- Preserve logs: `_Default` guarda só 30 dias. Exporte no início do incidente.

### Modelos que precisam existir antes do incidente

Registro de incidente; aviso ao cliente controlador; comunicação ao titular; texto de aviso público; contatos de ANPD, banco, autoridade certificadora, Athenas, Google, Hostinger, advogado e seguradora, impressos e fora do sistema.

### Recuperação, em ordem

1. Pessoas e canais de comunicação.
2. Credenciais e identidade.
3. Sistema contábil e folha.
4. Prazos fiscais da semana, com calendário de contingência.
5. Portal e atendimento.
6. Site institucional.

Depois: revisão em até 15 dias, causa raiz, atualização deste relatório e teste do controle corrigido.

---

## 12. Plano de ação

Quem faz: **Direção** = Warley ou Robson; **RT** = Robson; **Sessão** = esta sessão, sob autorização.

### Até 7 dias: sem custo relevante

| # | Ação | Risco | Quem |
|---|---|---|---|
| 1 | Confirmar segunda etapa com chave de acesso e códigos de recuperação na conta Google | SI-03 | Direção |
| 2 | Adicionar Warley e Robson como proprietários individuais | SI-03, CN-06 | Direção; Sessão orienta |
| 3 | Trocar senha e chaves da T12; verificar uso indevido | SI-12 | Direção |
| 4 | Investigar `ORGATEC_Backup_Diario`: o que copiava, desde quando falha | CN-02 | Direção; Sessão apoia |
| 5 | Publicar SPF `v=spf1 -all` e DMARC `p=reject`, enquanto não houver e-mail no domínio | SI-08 | Sessão prepara; Direção aplica ou autoriza |
| 6 | Conta da Hostinger: segunda etapa, bloqueio de transferência, renovação automática | SI-11 | Direção |
| 7 | Cadastrar `www.orgatec.io` no Firebase | SI-08 | Direção |
| 8 | ~~Ligar proteção contra exclusão do Firestore~~ **Feito em 04/11/2026** | SI-05 | Sessão |
| 9 | Descobrir onde estão as 2 chaves de conta de serviço, se ainda são usadas, e revogar as que não forem | SI-03, SI-12 | Direção; Sessão revoga, sob autorização |

### Até 30 dias

| # | Ação | Risco | Quem |
|---|---|---|---|
| 10 | Inventário de certificados, procurações, sistemas e fornecedores | SI-04, SI-10 | Direção |
| 11 | Plano de resposta de uma página, com modelos e contatos impressos | Todos | Direção + jurídico |
| 12 | Papéis LGPD por contrato e cláusula de aviso em até 24 h | SI-06, CN-10 | Jurídico |
| 13 | Questionário à Athenas: SLA, backup, MFA, logs, exportação, incidente, CNAME | CN-03, SI-10 | Direção |
| 14 | Nomear encarregado ou registrar dispensa fundamentada | CN-09 | Direção |
| 15 | Treinamento de phishing e regra de dados bancários | SI-02, SI-08 | Direção |
| 16 | Backup 3-2-1 com um teste real de restauração | CN-02 | TI |
| 17 | Cotação de seguro cibernético e profissional, com exclusões analisadas | CN-05, CN-10 | Direção |

### Até 90 dias

| # | Ação | Risco | Quem |
|---|---|---|---|
| 18 | Blaze com orçamento e alertas. Antes do primeiro dado real: PITR, backup diário, log regional, Data Access, conta de serviço mínima, Secret Manager, `max-instances` | SI-05, SI-07, CN-02 | Direção ativa; Sessão executa |
| 19 | Parecer sobre Hosting, cláusulas-padrão, Marco Civil e política de privacidade | Seção 4 | Jurídico |
| 20 | Mover `orgatec-site` para `orgatec-cloud-org`, encerrar projetos sem uso e definir conta de emergência. Avaliar Workspace para o e-mail do domínio | SI-03, CN-08 | Direção; Sessão migra |
| 21 | Boletim na nuvem e alerta de tarefa falha | CN-01 | Sessão |
| 22 | Projeto separado para prévias | SI-05 | Sessão |
| 23 | BIA real e exercício de mesa de ransomware | Todos | Direção |
| 24 | Cópia estática do site em outro provedor | SI-07, CN-08 | Sessão |

**Atenção ao item 18:** a [janela do PITR não fica disponível de imediato](https://docs.cloud.google.com/firestore/docs/pitr). Ligue antes de precisar.

---

## 13. Indicadores de acompanhamento

| Indicador | Meta proposta | Periodicidade |
|---|---|---|
| Contas de administração com chave de acesso ou token | 100% | Mensal |
| Proprietários do projeto Google | Pelo menos 2 | Trimestral |
| Testes de restauração bem-sucedidos | 1 por trimestre | Trimestral |
| Tarefas automatizadas com falha sem alerta | 0 | Semanal |
| Clique em simulação de phishing | Abaixo de 5% | Trimestral |
| Certificados de clientes guardados fora do cofre | 0 | Trimestral |
| Vulnerabilidades críticas abertas por mais de 7 dias | 0 | Mensal |
| Fornecedores críticos com cláusula de incidente | 100% | Semestral |
| Entregas fora do prazo por causa interna | 0 | Mensal |
| MTTD e MTTR | Medir desde o primeiro evento | Por evento |
| Tempo até a decisão de comunicar | Até 24 h | Por evento |

---

## 14. Não confirmado e pendente

**Jurídico e normativo:**
- Originais do DOU, seção e página da Res. 15/2024, e retificação da Res. 19/2024.
- Aplicação do Marco Civil, art. 15, ao site e ao portal. Se aplicável, os 30 dias de `_Default` podem ser insuficientes, e os logs de acesso do Hosting nem estão ligados. Exige parecer.
- Efeito da revogação do art. 171, § 5º, do CP na ação penal.
- Multas de EFD-Contribuições, EFD-ICMS/IPI e EFD-Reinf; alíquotas dos Apêndices da Res. 4/2023; texto das NBC PG 200 e 300 (R1).
- Inexistência de regulamento da ANPD sobre padrões mínimos do art. 46: só não localizei.
- Publicação do Plano Nacional de Cibersegurança.
- Regras do CRC para substituição de responsável técnico.

**Google e Firebase:**
- Aplicação de DPST e CDPA em Spark ou Blaze; qual módulo de cláusulas brasileiras cabe à ORGATEC.
- Cota gratuita do Hosting (10 GB por mês ou 360 MB por dia); retenção padrão de versões; prazo exato de retenção de IP.
- Cloud Armor com Firebase Hosting e proteção DDoS específica do Hosting.
- Mapeamento por produto do que sai do Brasil.
- Contatos de segurança do projeto (HTTP 403 em Essential Contacts).
- Data do contrato e situação de conta consumidor frente ao processamento de dados.

**Estatística:**
- Relatório completo da IBM, valores do Brasil e MTTI/MTTC.
- Totais de fraude Pix e dados de MED de 2025 (bcb.gov.br inacessível).
- Taxa de incidentes em escritórios contábeis brasileiros: **não existe em fonte localizada**.

**Interno da ORGATEC ou do cliente:** todos os itens das seções 3.3 e 3.4, além de receita, carteira, BIA, seguro, contratos e dados da LOCAR.

---

## 15. Próxima revisão

Revisar quando ocorrer qualquer destes eventos: primeiro dado real no Firestore, ativação do Blaze, decisão da D2, troca de sistema contábil, incidente relevante ou nova norma da ANPD. Na ausência deles, revisar em 6 meses.
