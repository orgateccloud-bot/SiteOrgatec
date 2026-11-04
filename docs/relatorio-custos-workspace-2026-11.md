# Relatório de custos: Google Workspace com 10 usuários

| Ficha | |
|---|---|
| Classificação | **Uso interno.** Trata de custos e de decisões da direção. Não publicar |
| Data de referência | 04/11/2026 |
| Fontes | [Página de preços do Google Workspace](https://workspace.google.com/pricing?hl=pt-BR), lida em 04/11/2026; e-mail de configuração do Workspace recebido em 03/11/2026 |
| Elaboração | Claude (sessão responsável por Firebase e Google). Sem revisão financeira |
| Limite | Não acessei o Admin Console nem a fatura. O plano e o preço realmente cobrados precisam ser conferidos lá |

Marcas: **[V]** li na fonte indicada · **[I]** inferência minha · **[INT]** depende de informação interna da ORGATEC.

---

## 1. Resumo

- **A ORGATEC está no plano mais caro.** O e-mail do Google de 03/11/2026 diz "Google Workspace Business Plus". Na página de preços de hoje, o plano equivalente chama-se **Plus**. A equivalência de nomes é inferência minha. [V/I]
- **Com 10 usuários, o Plus custa R$ 1.284,00 por mês no contrato anual, ou R$ 1.540,00 sem compromisso.** Em 12 meses: R$ 15.408,00 ou R$ 18.480,00. [V]
- **Cada usuário a mais custa R$ 128,40 por mês no anual**, ou R$ 154,00 sem compromisso. [V]
- **A diferença entre planos é grande.** Com 10 usuários no anual, o Starter custa R$ 10.500,00 por ano a menos que o Plus, e o Standard, R$ 5.592,00 a menos. [V]
- **A segurança básica que a ORGATEC usa está em todos os planos**, segundo a página: verificação em duas etapas, políticas por grupo e Programa de Proteção Avançada. [V]
- **A decisão mais importante é o plano e o tipo de contrato, antes de 16/11/2026**, data em que anotei o fim do teste gratuito de 14 dias. Essa data veio das notas do projeto, e não a vi no Admin Console. [INT]

---

## 2. Premissas

1. **10 usuários, cada um com licença.** Um "e-mail" só exige licença se for uma pessoa com caixa própria.
2. **Endereços compartilhados não precisam de licença.** `contato@` e `dpo@` já são grupos, e não entram na conta. Um grupo também pode receber o e-mail dos clientes em uma caixa colaborativa. Quanto mais endereços forem grupos ou apelidos, menor o custo. [INT]
3. **Preços da página, em R$, por usuário por mês, sem confirmar impostos.** A página afirma que o valor final aparece antes da assinatura. Confira se o imposto está incluído. [V/INT]
4. **Duas formas de cobrança**, ambas cobradas mensalmente:
   - **Flexível**, sem compromisso.
   - **Anual**, com compromisso de 12 meses. A página anuncia 16% de economia, e os números dela dão de 16,5% a 16,7%. [V]
5. **Não sei qual das duas a ORGATEC contratou.** [INT]

---

## 3. Preços da página (04/11/2026)

| Plano | Flexível (mensal) | Anual (por mês) | Armazenamento por pessoa, em pool |
|---|---|---|---|
| Base | R$ 24,00 | R$ 20,00 | 20 GB |
| Starter | R$ 49,00 | R$ 40,90 | 30 GB |
| Standard | R$ 98,00 | R$ 81,80 | 2 TB |
| Plus | R$ 154,00 | R$ 128,40 | 5 TB |
| Enterprise | Sob consulta | Sob consulta | 5 TB ou mais |

**Oferta de lançamento do Starter:** 20% de desconto por 12 meses, a R$ 39,20 (flexível) ou R$ 32,72 (anual). A página limita a oferta a **novos clientes** e aos **20 primeiros usuários**, durante 12 meses. Como a ORGATEC já assinou o Plus, não sei se continuaria elegível ao trocar de plano. [V/INT]

---

## 4. Custo com 10 usuários

### 4.1 Por mês e por ano

| Plano | Flexível, por mês | Flexível, por ano | Anual, por mês | Anual, por ano |
|---|---|---|---|---|
| Base | R$ 240,00 | R$ 2.880,00 | R$ 200,00 | R$ 2.400,00 |
| Starter | R$ 490,00 | R$ 5.880,00 | R$ 409,00 | R$ 4.908,00 |
| Standard | R$ 980,00 | R$ 11.760,00 | R$ 818,00 | R$ 9.816,00 |
| **Plus (contratado)** | **R$ 1.540,00** | **R$ 18.480,00** | **R$ 1.284,00** | **R$ 15.408,00** |
| Starter com oferta | R$ 392,00 | R$ 4.704,00 | R$ 327,20 | R$ 3.926,40 |

### 4.2 Diferença entre planos (anual, 10 usuários)

| Comparação | Por mês | Por ano |
|---|---|---|
| Plus em vez de Standard | R$ 466,00 | R$ 5.592,00 |
| Plus em vez de Starter | R$ 875,00 | R$ 10.500,00 |
| Plus em vez de Base | R$ 1.084,00 | R$ 13.008,00 |
| Standard em vez de Starter | R$ 409,00 | R$ 4.908,00 |

### 4.3 Compromisso anual em vez de flexível

Com 10 usuários, o anual economiza **R$ 3.072,00 por ano** no Plus, R$ 1.944,00 no Standard e R$ 972,00 no Starter. O preço dessa economia é o compromisso de 12 meses.

### 4.4 Outros tamanhos de equipe (anual, por mês)

| Plano | 2 usuários | 5 usuários | 10 usuários |
|---|---|---|---|
| Base | R$ 40,00 | R$ 100,00 | R$ 200,00 |
| Starter | R$ 81,80 | R$ 204,50 | R$ 409,00 |
| Standard | R$ 163,60 | R$ 409,00 | R$ 818,00 |
| Plus | R$ 256,80 | R$ 642,00 | R$ 1.284,00 |

Sei de 2 usuários: `orgatec@` e `administrador@`. O total atual, e portanto quantos faltam para chegar a 10, precisa ser conferido no Admin Console. [INT]

---

## 5. O que cada plano entrega (para decidir)

| Item | Base | Starter | Standard | Plus |
|---|---|---|---|---|
| E-mail personalizado `@orgatec.io`, Calendar, Meet, Drive, Docs | Sim | Sim | Sim | Sim |
| Verificação em duas etapas | Sim | Sim | Sim | Sim |
| Controles de política por grupos | Sim | Sim | Sim | Sim |
| Programa de Proteção Avançada | Sim | Sim | Sim | Sim |
| "Segurança e privacidade empresariais" (linha da página) | **Não** | Sim | Sim | Sim |
| Gemini no Gmail | Não | Sim | Sim | Sim |
| Gemini em Docs, Planilhas, Drive e Meet | Não | Não | Sim | Sim |
| E-discovery | Não | Não | Não | **Sim** |
| Videochamada com até 500 participantes | Limite menor, não conferido | Limite menor, não conferido | Limite menor, não conferido | Sim |

Todos os dados da tabela são da página de preços, e a coluna de Enterprise foi omitida. [V]

**O que não confirmei:** a lista completa de recursos de segurança por plano, a página mostra só alguns itens. O e-mail do Google associa ao Business Plus a proteção avançada contra phishing e malware, a prevenção contra vazamento de dados (DLP) e os Insights de segurança. A página não mostra em qual plano mais baixo cada um deles começa. **Antes de rebaixar de plano, confirme isso no Admin Console ou com o Google.** [V/INT]

---

## 6. Recomendação

1. **Não assine o compromisso anual antes de fechar a lista de 10 usuários e o plano.** A economia de 16% desaparece se o plano estiver acima do necessário. Confira no Admin Console se o contrato anual permite reduzir usuários ou mudar de plano. [INT]
2. **Avalie sair do Plus.** Para o uso descrito até aqui (e-mail do domínio, grupos, duas etapas e administração), o Standard ou o Starter parecem suficientes. O Plus se justifica por:
   - e-discovery, por exemplo para reter e pesquisar e-mails por exigência jurídica;
   - 5 TB por pessoa;
   - reuniões grandes.
   Esses pontos dependem de uma decisão da direção e do jurídico. [I]
3. **Se a ORGATEC guarda e-mails por dever legal ou por contrato com clientes,** confirme se o e-discovery é necessário antes de dispensá-lo. [INT]
4. **Reduza o número de licenças.** Transforme em grupo ou apelido todo endereço que não seja uma pessoa. Cada licença Plus a menos economiza R$ 1.540,80 por ano no anual. [V]
5. **Conta `administrador@`:** a licença dela custa o mesmo que a de qualquer usuário. O Workspace oferece contas gratuitas do Cloud Identity para quem só administra. Não conferi os limites atuais dessa opção. Pergunte ao Google antes de contar com ela. [I]
6. **Conta de plano pago exige um responsável pela fatura.** Defina quem acompanha a cobrança e o e-mail de cobrança. [INT]

---

## 7. Custos fora da licença

Nenhum destes valores foi cotado. Preencha antes de aprovar o orçamento.

| Item | Observação | Valor |
|---|---|---|
| Imposto | Não sei se a página inclui | [INT] |
| Registro do domínio `orgatec.io` | Renovação anual na Hostinger | [INT] |
| Chaves de segurança físicas para as contas administradoras | Recomendadas para o proprietário; pelo menos duas por pessoa, uma de reserva | [INT] |
| Backup de terceiros para e-mail e Drive | O Workspace não substitui um backup independente. A decisão é a mesma do risco CN-02 do relatório de riscos | [INT] |
| Créditos de IA adicionais | O Admin Console recebeu em 04/11/2026 um pedido de um usuário por créditos extras de IA. Não sei se há custo | [INT] |
| Armazenamento acima do limite | Provavelmente fora do alcance com 10 usuários, mas o limite do pool deve ser conferido | [INT] |
| Pré-pagamento | O Google registrou um pagamento de R$ 50,00 em 03/11/2026. Não sei se vira crédito na fatura | [V/INT] |
| Tempo da equipe | Criar contas, treinar e migrar e-mails antigos | [INT] |

---

## 8. Itens a confirmar no Admin Console

1. Plano exato e tipo de cobrança (flexível ou anual).
2. Preço por usuário que aparece na fatura, com impostos.
3. Data do fim do teste e da primeira cobrança.
4. Se é possível trocar de plano, e quando a troca vale.
5. Se o contrato anual permite reduzir a quantidade de usuários.
6. Quais recursos de segurança e retenção existem em cada plano, em especial DLP, Insights de segurança e e-discovery.
7. Se a ORGATEC ainda é elegível à oferta de 20% do Starter.
8. Quem recebe os e-mails de cobrança e de segurança do Google.

---

## 9. Próximos passos

| # | Ação | Quem |
|---|---|---|
| 1 | Listar os 10 endereços e separar pessoas de grupos e apelidos | Direção |
| 2 | Conferir no Admin Console os 8 itens da seção 8 | Direção |
| 3 | Decidir plano e tipo de contrato antes de 16/11/2026 | Direção |
| 4 | Registrar a decisão e atualizar o relatório de riscos, no item de conta administradora e backup | Sessão |
| 5 | Criar os usuários restantes com segunda etapa obrigatória desde o primeiro acesso, depois de decidir o plano | Direção; Sessão orienta |
