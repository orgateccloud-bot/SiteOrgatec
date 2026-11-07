# Janela de Campo: o painel precisa discriminar e dizer quando falta dado (Fase 1)

- **Situação:** em desenvolvimento (código e testes prontos; a revisão dos limites depende de validação técnica, V20)
- **Branch:** `ideia/campo-qualidade` (parte de `ideia/campo-confiabilidade`, que ainda não foi juntada a `desenvolvimento`)
- **Prévia:** [link](https://orgatec-site--ideia-campo-qualidade-5agwgcx3.web.app/setores/janela-de-campo.html) (inclui a Fase 0; expira em 07/12/2026). O boletim da prévia foi gerado com o código desta branch, em 07/11/2026 às 19h56; o aviso de polo sem previsão não aparece nela porque a fonte respondeu a todos os polos, mas a lacuna de 04/11 aparece no seletor.

## Problema

O painel quase não muda de estado. Medido com `python tools/relatorio_campo.py` em 5 boletins (02, 03, 05, 06 e 07/11/2026), 100 combinações de polo e dia, 1.400 horas entre 05h e 20h:

| Operação | Estado do dia (polo x dia) | Horas 05h–20h | Motivo mais comum entre os não "ok" |
|---|---|---|---|
| Pulverização | atenção 98, evitar 1, ok 1 | ok 23%, atenção 67%, evitar 10% | vento forte (deriva), em 55 de 99 |
| Plantio | ok 98, atenção 2 | ok 99% | chuva moderada (2) |
| Colheita | ok 68, atenção 32 | ok 77%, atenção 23% | umidade alta (grão úmido) |
| Manejo de animais | atenção 82, evitar 15, ok 3 | evitar 45%, atenção 41%, ok 14% | estresse térmico (ITU) |
| Máquinas e insumos | ok 98, atenção 2 | ok 99% | chuva forte (2) |

Por região e dia (30 combinações), pulverização ficou em "atenção" nas 30, e plantio e máquinas em "ok" nas 30.

Dois dos cinco boletins finais (02/11 e 05/11) foram calculados com 11 das 16 horas úteis, porque as rodadas da manhã não saíram. O painel não dizia isso. Um dia sem nenhuma hora útil com previsão virava "evitar", como se fosse condição ruim.

O texto de cada operação na região tinha de 190 a 315 caracteres e listava todos os polos.

## Público

Produtor rural que decide a operação do dia pelo painel.

## O que esta branch muda (sem tocar nas regras)

`LIMITES` e `CRITERIOS` não foram alterados. Eles seguem marcados "pendente de validação" no site.

1. **Resumo curto.** O texto da operação na região passa a ter no máximo 90 caracteres: estado, janela comum aos polos, fator decisivo e os polos que fogem do padrão, por exemplo `Com restrição · janela comum 05h às 09h · vento forte (deriva) · exceção: Dourados`. Se não couber, saem primeiro a exceção, depois a janela e o fator; o estado e o aviso de previsão parcial ficam. O detalhe de cada polo já existe no painel do polo.
2. **Orientação à parte.** A recomendação de segurança que ficava na frente do texto longo (por exemplo, recolher máquinas na trovoada) agora é o terceiro item de `ops[op]`, mostrado no bloco da operação escolhida.
3. **Dado ausente separado de condição de atenção.**
   - Cada operação do polo traz `horasPrevistas` (de 16). Com menos de 16, o resumo da região diz "previsão parcial do dia" e o painel do polo diz "Previsão para N das 16 horas úteis".
   - Sem nenhuma hora útil, o estado deixa de ser "evitar": fica em "atenção" com o texto "Sem previsão para as horas úteis de hoje", e a orientação manda consultar o próximo boletim e o INMET. Esses polos não entram na agregação da região.
4. **Relatório.** `tools/relatorio_campo.py` repete a medição acima a qualquer momento (`--json` também) e aponta operações com 90% ou mais do mesmo estado e boletins finais com horas faltando.

## O que não foi mudado, e por quê

Os números abaixo são hipóteses para o responsável técnico ou o agrônomo decidirem. Nada disso entrou no código.

- **Pulverização e o vento.** O critério de 3 a 10 km/h é o das recomendações usuais de aplicação, que costumam falar do vento na altura da aplicação. A fonte entrega o vento médio previsto pelo modelo (mediana de 10,4 km/h nesta amostra, e 56% das horas acima de 10). Perguntas: o limite vale para o vento do modelo, ou é preciso converter? Se for converter, qual fator?
- **Plantio e máquinas.** As regras olham só chuva por hora (5 e 20 mm/h) e trovoada. Sem umidade do solo nem chuva acumulada, elas quase nunca saem de "ok". A fonte de previsão não traz chuva já ocorrida. Perguntas: vale acrescentar chuva acumulada dos dias anteriores, e de qual fonte com licença de uso comercial? Até lá, o texto do critério diz o que cada regra enxerga?
- **Manejo de animais.** O ITU de 72 e de 79 vem das faixas citadas pela Embrapa. Em 45% das horas úteis o ITU passa de 79. Pergunta: essas faixas servem para gado de corte e de leite, ou há faixas separadas?
- **Estado do dia.** Hoje o dia só é "ok" com pelo menos 8 horas seguidas "ok" (ou todas as horas disponíveis, se forem menos que 8). Isso explica "ok" em só 1 de 100 dias de pulverização, mesmo com 23% das horas "ok". Pergunta: 8 horas seguidas é o critério certo?

## Limites desta medição

Só 5 boletins, todos da primeira semana de novembro, no começo do período chuvoso. Antes de mexer em qualquer limite, repetir `python tools/relatorio_campo.py` com pelo menos 30 dias de arquivo, de preferência com dias de chuva.

## Fontes e validação

- Critérios e fontes de cada limite: `CRITERIOS` em `site/assets/js/campo-regras.js` (pendência V20 em `homologacao.js`). Quem aprova: o responsável técnico ou um agrônomo.
- O relatório só lê o arquivo de boletins; não consulta nenhuma fonte externa.

## Pronto quando

- Os testes novos passam: resumo de até 90 caracteres em todas as regiões e operações, fator e exceção citados, previsão parcial sinalizada, dia sem hora útil como "atenção" com texto próprio, relatório.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta no celular e aprovada pelo usuário.
- Respostas às perguntas acima, para decidir a próxima rodada de ajuste dos limites.
