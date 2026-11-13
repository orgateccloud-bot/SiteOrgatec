# Janela de Campo: barra do local com fundo próprio e página mais curta no celular

- **Situação:** implementada em 13/11/2026 na branch `ideia/campo-barra-altura`; **aguarda a sua aprovação da prévia**. Não publicada.
- **Branch:** `ideia/campo-barra-altura` (parte da `desenvolvimento`)
- **Prévia:** ver o índice em [README.md](README.md)

## Problema

Dois pontos ficaram pendentes depois da Janela de Campo 2 (V1 a V4) e do mapa novo:

1. **Barra do local.** Ao rolar, a barra ("Sorriso · MT", os cinco glifos e "Ao sol") gruda sob o cabeçalho, mas não tinha fundo: o texto que passava por trás aparecia nos vãos entre o botão, os glifos e o "Ao sol". Acontecia no desktop e no celular.
2. **Altura no celular.** A página tinha 4.899 px em 375 x 812 (com a faixa de homologação), acima dos 4.425 px de antes da Janela de Campo 2 e da meta de 4.000 px do plano. A primeira operação estava a 766 px do topo (antes: 718 px).

## O que muda

1. **Barra grudada com fundo de vidro.** Só quando gruda, a barra ganha uma moldura de 6 px com fundo (92% da cor da página), desfoque e sombra. O conteúdo continua na mesma posição, logo abaixo do cabeçalho; solta, a barra fica como era.
2. **Botão "Compartilhar no WhatsApp" depois dos cartões.** Continua levando o veredito, mas sai do meio do caminho entre o veredito e as operações.
3. **Fatos do dia em duas colunas no celular** (céu e temperatura, chuva e vento). Antes era uma coluna só abaixo de 480 px; agora só abaixo de 340 px.
4. **Seções de fechamento compactas no celular** ("Minha atividade" e "O clima também mexe no caixa"): metade do espaço vertical em cima e embaixo, usando a opção `compacto` que as funções já tinham. No desktop não muda.

## Medição (celular, 375 x 812, boletim real de 13/11/2026, com a faixa de homologação de 81 px)

| | Antes da Janela 2 | Antes deste ajuste | Depois |
|---|---|---|---|
| Altura da página | 4.425 px | 4.899 px | **4.693 px** |
| Primeira operação (topo) | 718 px | 766 px | **714 px** |
| Rolagem horizontal | nenhuma | nenhuma | nenhuma |

**A meta de 4.000 px continua sem ser atingida.** O que sobra não está no boletim:

| Bloco | Altura no celular |
|---|---|
| Cabeçalho, faixa de homologação (só fora de produção), trilha e título | 271 px |
| Boletim (situação, barra, veredito, glifos, cartões, abas, painel e aviso das fontes) | 2.327 px |
| Seção "Minha atividade" (leva às cotações) | 392 px |
| Seção "O clima também mexe no caixa" (chamada e aviso legal) | 545 px |
| Rodapé do site | 1.086 px |
| Espaço reservado para a barra fixa de baixo | 72 px |

Para chegar aos 4.000 px seria preciso mexer fora do boletim. Duas decisões suas, não tomadas aqui:

- **Rodapé em sanfona no celular** (as duas listas de links recolhidas): por estimativa, cerca de 330 px a menos, mas muda as 49 páginas do site.
- **Tirar a seção "Minha atividade" da Janela de Campo** (o menu "Setores" já leva às cotações): 392 px a menos, mas a escolha da atividade deixa de aparecer nesta página.

As duas juntas levariam a página a cerca de 3.970 px (estimativa, não medida).

## O que não muda

Formato do boletim, regras e limites, veredito, cartões (no formato de antes), mapa de satélite e o modelo 3D dele, as duas barras antigas da aba Horas (continuam recolhidas em "Detalhes por período e por hora": a de hora em hora cobre as 24 horas, e a faixa dos cartões só as horas úteis, então tirá-las de vez perderia informação e não baixaria a altura).

## Testes

- E2E novos (+2): a barra grudada tem fundo (opacidade de 0,9 ou mais) e desfoque, no desktop e no celular, sem sair da tela; o botão de compartilhar fica depois dos cartões e os fatos do dia ficam dois por linha no celular.
- Limites mais apertados no teste que já existia: primeira operação até 760 px (era 812) e página até 4.800 px (era 5.000), com o boletim de teste.
- O teste antigo da barra grudada passou a medir o botão da barra (o conteúdo), não a moldura.

## Pronto quando

Suíte completa e bandit verdes; prévia vista no celular e no desktop (rolar a página e olhar a barra) e aprovada.
