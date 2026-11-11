# Janela de Campo 2, V3: linha do dia, ícones de tempo, alvos de 44 px e modo Ao sol

- **Situação:** implementada em 11/11/2026; **aprovada em 11/11/2026 e junta na `desenvolvimento`**. Falta lançar (publicar com `tools/publicar.py`, com a sua autorização).
- **Branch:** `ideia/campo-visual-3` (parte da `desenvolvimento`, com V1 e V2 já juntas)
- **Plano e mockups:** [campo-visual-2.md](campo-visual-2.md) (seções 4.4, 4.5 e 4.6)
- **Prévia:** [link](https://orgatec-site--ideia-campo-visual-3-1e037t0u.web.app/rural/janela-de-campo.html) (expira em 11/12/2026). Usa o boletim real do ar.

## O que muda (só na Janela de Campo)

1. **Linha do dia em SVG** no topo da aba Horas: temperatura (linha cheia), vento (tracejada) e chuva (barras), hora a hora das 05h às 20h do polo escolhido. As **horas favoráveis da operação escolhida** ficam sombreadas (trocar de operação muda o sombreado e o título) e, no dia de hoje, uma linha pontilhada marca o **agora**. Sem biblioteca de gráfico: SVG gerado como texto, com as cores dos tokens. Para leitor de tela há um resumo ("Temperatura de 25 a 32 °C · vento até 44 km/h · chuva de 2,3 mm nas horas úteis") e uma tabela hora a hora escondida. Hora sem previsão interrompe a linha em vez de ligar os pontos.
2. **Ícones de tempo na tabela dos 7 dias** (sol, sol com nuvens, nublado, chuva, chuva forte, trovoada), **desenhados por nós** (traço de 2 px, cor do texto), sem depender de conjunto de terceiros. O texto ("Chuva moderada") continua; o ícone é só reforço.
3. **Rótulos e alvos.** Os rótulos de seção (REGIÃO, POLO, CONDIÇÃO AO LONGO DO DIA...) deixam o mono maiúsculo de 11–12 px e passam para IBM Plex Sans de 13 px em caixa normal. Chips, abas, botões do mapa e caixas de marcar da Janela passam a ter **44 px de altura mínima**. Mono fica só para números.
4. **Modo Ao sol**: botão na barra do local que liga a paleta clara (Azul flutuante) e grava na **mesma chave do botão "Cores"** (`orgatec.tema`): nenhuma chave nova. Tocar de novo volta ao padrão escuro. Só por toque (não é automático).
5. **Contraste medido nas sete paletas** (Verde, Azul, Vinho, Ciano, Noturno, Azul flutuante e Azul flutuante escuro), com teste automático (texto de selos, cartões, glifos e veredito, mínimo 4,5:1). A medição achou dois problemas, corrigidos só dentro da Janela, sem mexer nos tokens do projeto:
   - o âmbar de restrição sobre o fundo suave dava **4,22:1 (Azul flutuante), 4,30:1 (Vinho) e 4,33:1 (Azul)**: nas paletas claras a restrição passa a usar o fundo branco do cartão (a partir de 5,8:1);
   - o texto de apoio sobre os cartões favoráveis dava **4,41:1 (Azul) e 4,46:1 (Vinho)**: passa a usar a cor do texto principal.

## O que não muda

Formato do boletim (JSON), regras e limites (V20), satélite, veredito, cartões, folha do local e grade das regiões (V1 e V2). Sem verde e sem vermelho; estados nunca só por cor.

## Diferenças em relação ao mockup

- A linha do dia mostra **vento** também (o mockup só tinha temperatura e chuva), porque o vento é o motivo da maioria das restrições à pulverização. Sem escala numérica nos eixos: os valores vão no resumo escrito abaixo do gráfico.
- A tabela dos 7 dias continua com rolagem lateral dentro da própria caixa; a mudança é só o ícone.

## Medição (boletim real de 11/11/2026)

| | Antes (no ar) | V1 | V2 | V3 |
|---|---|---|---|---|
| Altura da página, celular | 4.425 px | 4.787 px | (sem mudança relevante) | **5.090 px** |
| Veredito, celular (topo, com a faixa de homologação de 80 px) | não existia | 420 px | 420 px | 440 px |
| Primeira operação, celular (topo, com a faixa) | 718 px | 765 px | 765 px | 784 px |
| Rolagem horizontal | nenhuma | nenhuma | nenhuma | nenhuma |

**A meta de altura do plano (até 4.000 px no celular) não foi atingida: a página está mais comprida a cada fase.** A linha do dia (V3) soma cerca de 300 px no topo da aba Horas. A causa provável do que sobra é a repetição: a aba Horas ainda traz as duas barras antigas ("Condição ao longo do dia na região", em 6 períodos, e "Hora a hora no polo escolhido", em 24 células), que a faixa de cada cartão e a linha do dia já cobrem. Tirá-las, ou recolhê-las, é a próxima medida para baixar a altura e fica como decisão sua (seção "Fora desta fase").

## Testes

- Unitários (`tests/js/campo-veredito.test.js`, +5): série do dia, linha do dia (marcas, resumo, tabela, interrupção da linha), ícones.
- E2E novos: linha do dia com tabela para leitor de tela, ícones nos 7 dias, Ao sol (liga, lembra, volta) e contraste nas 7 paletas; o teste de alvos de 44 px agora inclui abas e chips. Um bug real apareceu e foi corrigido: a tabela só para leitor de tela alargava a página no celular (agora fica dentro de uma caixa recortada).

## Fora desta fase

Cartão do WhatsApp e compartilhamento (V4); modo offline (V5, opcional). **Decisão pendente:** remover ou recolher as duas barras antigas da aba Horas (redundantes com a faixa dos cartões e a linha do dia) para baixar a altura da página; vários testes e2e citam `[data-campo-horaria]`.

## Pronto quando

Suíte completa e bandit verdes; prévia aberta em 375 px e 1280 px, nas paletas escura e clara, e aprovada.
