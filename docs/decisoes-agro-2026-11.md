# Decisões e revisões que faltam na área rural (08/11/2026)

Estado: as Fases 0 a 6 da modernização do boletim de campo e da área rural estão no ar desde 08/11/2026 às 06h50 (tag `publicado-20261108-0650`). Este documento reúne o que falta e **quem** precisa agir. Nada aqui foi enviado a ninguém: os rascunhos são para você usar ou ajustar.

| # | Pendência | Quem decide ou revisa | O que destrava | Recomendação |
|---|---|---|---|---|
| 1 | D23: autor nas notícias do Senado | Você | **Decidido em 08/11/2026: pedir confirmação à Agência Senado e manter por ora.** Falta enviar o pedido (rascunho abaixo) e registrar a resposta | Enviar o pedido |
| 2 | Alerta de falha do boletim | Você | **Canal escolhido em 08/11/2026: GitHub Actions.** Plano de ativação e vigia prontos em `docs/plano-ativacao-boletim-actions.md`; nada foi ativado | Decidir os 5 pontos do plano |
| 3 | V20: limites agronômicos | Responsável técnico ou agrônomo | Revisar vento, ITU, chuva e o critério do dia "ok" | Mandar o roteiro da seção 3, com os números medidos |
| 4 | Marca Audi Agro no holograma | Você | Onde a marca volta a aparecer | Deixar como está até decidir a realocação |
| 5 | Revisão técnica dos itens da reforma | Responsável técnico | A virada do site para `ambiente: 'producao'` | Revisar com a folha da seção 5, começando pelos 10 do agro |

## Correção sobre o item 5

Em mensagens anteriores eu disse que a lista de pontos da reforma do agro "fica vazia no ar". **Isso estava errado para hoje.** O `orgatec.io` está em `ambiente: 'homologacao'` (a faixa "Ambiente de homologação" aparece no topo) e, nesse modo, a página Agro mostra os itens, cada um com o selo "em revisão técnica" (conferi no navegador: 5 de 10 à vista, e os 10 com "Ver todos"). A lista só fica vazia **depois da virada para produção**, porque em produção só aparece o que tiver revisão aprovada, e hoje são **0 de 32 itens** no site inteiro (10 deles do agro).

## 1. D23: a citação do autor nas notícias do Senado

- **O que a fonte diz** ([política de uso do Senado](https://www12.senado.leg.br/noticias/politica-de-uso), lida em 07/11/2026): "A reprodução de matérias e fotografias é livre, desde que não haja descaracterização de conteúdo e mediante a citação da Agência Senado e do autor."
- **O que o site faz:** lista o título sem alteração, a data e o link para a matéria, com o nome "Agência Senado".
- **O que falta:** o feed do Senado não informa o autor (conferido: o item traz só título, descrição, data e `guid`). A matéria original traz.
- **Decisão (08/11/2026): opção B.** As opções que estavam em aberto:
  - **A.** Manter como está. Barato, mas o autor não é citado na lista.
  - **B (recomendada).** Manter por ora e pedir confirmação à Agência Senado de que título e link para a matéria bastam. Se disserem que não, passa para C.
  - **C.** Tirar o Senado dos cards. É uma linha em `tools/agro_fontes.json`. Custo: o Senado hoje contribui com pouca coisa (1 notícia de cana e 1 de arroz na medição de 07/11), e o histórico das demais fontes continua.
- **Rascunho do pedido** (o contato da Agência Senado deve ser procurado na página de política de uso ou no portal da agência; eu não o verifiquei nem o inventei):

  > Assunto: Uso de títulos e links do feed RSS da Agência Senado
  >
  > Olá. A ORGATEC (orgatec.io) lista, em páginas de informação para produtores rurais, apenas o título, a data e o link das matérias publicadas no feed RSS da Agência Senado, sempre com a indicação "Agência Senado" e o link para a matéria original. O feed não informa o autor; a matéria original o informa. A política de uso pede a citação da Agência Senado e do autor. Essa forma de listagem atende à política, ou prefere que incluamos o autor de outra maneira ou deixemos de listar? Obrigado.

## 2. Alerta de falha do boletim

- **Por que importa:** no log do agendador (`tools/logs/campo.log`), entre 04 e 08/11 houve **4 rodadas em que o boletim foi gerado e não foi publicado por credencial do Firebase vencida** (04/11 17h, 05/11 05h, 06/11 05h e 08/11 05h) e 4 falhas do MET Norway (04/11 ×3, 05/11 ×1). Ninguém foi avisado; o site só mostrou "Boletim desatualizado" depois de 18 horas.
- **O que o alerta deve cobrir:** (a) publicação falhou; (b) boletim no ar com mais de 18 h; (c) fonte fora do ar (MET Norway). A Fase 0 já reduziu (c), com tentativas e polo sem previsão.

| Canal | Como funciona | Limite |
|---|---|---|
| **GitHub Actions (recomendada)** | O boletim passa a rodar no GitHub (protótipo em `ideia/boletim-actions`); uma execução com erro, ou um boletim com mais de 18 h, avisa pelo e-mail do próprio GitHub, sem chave nem senha. Resolve também a credencial que vence em cerca de 16 horas (segundo `docs/ideias/boletim-no-actions.md`), que é a causa das 4 falhas acima | Depende de ativar o T20: criar a federação com o Google (IAM do projeto) e decidir sobre o plano Blaze, conforme `docs/ideias/boletim-no-actions.md` |
| E-mail pelo conector do Gmail | Um script manda mensagem quando a coleta falha | Envia em nome do usuário; precisa da sua autorização e continua dependendo do PC ligado |
| Aviso do Windows no PC | Notificação local | Só adianta com você na frente do PC |

Enquanto isso, o `--simular` do publicador já acusa a credencial vencida antes de rodar a suíte (foi o que aconteceu hoje às 06h34).

## 3. V20: roteiro para o responsável técnico (limites agronômicos)

Os critérios de cada operação seguem "pendentes de validação" no site. Os números abaixo vêm de 5 boletins de 02 a 07/11/2026 (100 combinações de polo e dia, 1.400 horas entre 05h e 20h). Repetir com `python tools/relatorio_campo.py` quando houver 30 dias de arquivo.

| Operação | Estado do dia (polo x dia) | Horas 05h a 20h |
|---|---|---|
| Pulverização | atenção em 98, evitar em 1, ok em 1 | ok 23%, atenção 67%, evitar 10% |
| Plantio | ok em 98 | ok 99% |
| Colheita | ok em 68, atenção em 32 | ok 77% |
| Manejo de animais | atenção em 82, evitar em 15 | evitar 45% |
| Máquinas e insumos | ok em 98 | ok 99% |

**Perguntas** (responder no próprio documento):

1. **Vento na pulverização.** O critério de 3 a 10 km/h é o das recomendações usuais de aplicação, que costumam falar do vento na altura da aplicação. A fonte entrega o vento médio previsto pelo modelo (mediana de 10,4 km/h na amostra; 56% das horas acima de 10 km/h). O limite vale para o vento do modelo ou precisa de conversão? Se precisa, qual fator?
   Resposta: ______
2. **Plantio e máquinas.** As regras só olham chuva por hora (5 e 20 mm/h) e trovoada, então quase nunca saem de "ok". Vale acrescentar chuva acumulada dos dias anteriores? De qual fonte com licença de uso comercial (a previsão não traz chuva já ocorrida)?
   Resposta: ______
3. **Manejo de animais.** ITU de 72 (restrição) e 79 (evitar), faixas citadas pela Embrapa. Em 45% das horas úteis o ITU passa de 79. Servem para gado de corte e de leite, ou há faixas separadas?
   Resposta: ______
4. **Estado do dia.** Hoje o dia só é "ok" com 8 horas seguidas "ok" (ou todas as disponíveis, se forem menos de 8). Oito horas seguidas é o critério certo? Para pulverização isso dá "ok" em 1 de 100 dias, com 23% das horas "ok".
   Resposta: ______

Para cada resposta, o ajuste é uma linha em `site/assets/js/campo-regras.js` (`LIMITES` e `CRITERIOS`), com teste; só depois o critério sai de "pendente de validação".

## 4. Marca Audi Agro no rodízio do holograma

Decisão de 07/11/2026: a marca saiu das páginas ("deixar por ora" no holograma). O rodízio da abertura ainda mostra o logotipo dela (`tools/gerar_holo_logos.py` e `holo-logos.js`; o teste e2e confere a sequência `simbolo servicos ia parceiro audi-agro trilhum assinatura`). Para tirar: remover a entrada, regenerar e ajustar a sequência esperada no teste. Para a marca voltar às páginas: `marca.exibir = true` em `tools/agro_fontes.json`. Sem ação até você decidir onde ela volta.

## 5. Folha de revisão dos 10 itens do agro (para o responsável técnico)

Para aprovar um item, o responsável técnico confere o fato contra a fonte citada e o `status`; eu então registro `revisao: { status: 'aprovada', por, em }` no item e rodo a suíte. Todos têm `consultadoEm` de 31/10/2026 (passam de 90 dias em 29/01/2027). O agrupamento por tema (`tema`) é editorial e também precisa da sua aprovação.

| Item | Status | Fonte | O que conferir |
|---|---|---|---|
| `agro-reducao-60` | em vigor | LC 214/2025, arts. 137 e 138 e Anexo IX | Redução de 60% para in natura e insumos do Anexo IX |
| `cesta-basica` | em vigor | LC 214/2025, art. 125 e Anexo I; art. 148 e Anexo XV | Alíquota zero: cesta básica, hortícolas, frutas e ovos |
| `maquinas-agro` | em vigor | LC 214/2025, art. 110 | Alíquota zero para máquinas destinadas ao produtor não contribuinte |
| `combustiveis` | em vigor | LC 214/2025, arts. 172 a 180 | Incidência única e crédito de quem não revende; tem orientação ORGATEC |
| `produtor-nao-contribuinte` | em vigor | LC 214/2025, arts. 164 e 167; Decreto 12.955/2026, arts. 239 a 249, e Decreto 13.075/2026 | Limite de R$ 3,6 milhões, corrigido pelo IPCA; receita de 2024; tem orientação ORGATEC |
| `produtor-opcao` | em vigor | LC 214/2025, arts. 165 e 166 | Opção pelo regime regular, irretratável no ano-calendário; tem orientação ORGATEC |
| `credito-presumido-produtor` | **pendente de regulamentação** | LC 214/2025, arts. 168 e 544 (redação da LC 227/2026) | Efeitos a partir de 01/01/2027 |
| `diferimento-insumos` | em vigor | LC 214/2025, art. 138, § 2º | Diferimento nos insumos do Anexo IX |
| `lcdpr` | em vigor | IN SRF 83/2001, art. 23-A (IN RFB 1.848/2018); manual IRPF Atividade Rural (gov.br) | **A fonte `rfb_lcdpr` está marcada como não validada**: o texto vigente da IN não foi conferido. Resolver antes de aprovar; tem orientação ORGATEC |
| `icms-iss-2029-2032` | vigência futura | ADCT, arts. 128 e 129; EC 132/2023, art. 12 | Escada de ICMS e ISS de 2029 a 2032 e extinção em 2033; tem orientação ORGATEC |

**Alcance da virada para produção:** os 32 itens da reforma do site estão sem revisão aprovada, não só os 10 do agro. Virar `ambiente` para `'producao'` hoje esvaziaria também a Central da reforma, os setores e o compliance. A revisão do agro é um pedaço desse trabalho, não o todo.
