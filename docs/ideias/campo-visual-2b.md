# Janela de Campo 2, V2: grade de glifos das regiões e boletim de arquivo em cinza

- **Situação:** implementada em 11/11/2026; **aprovada em 11/11/2026 e junta na `desenvolvimento`**. Falta lançar (publicar com `tools/publicar.py`, com a sua autorização).
- **Branch:** `ideia/campo-visual-2` (parte da `desenvolvimento`, com a V1 já junta)
- **Plano e mockups:** [campo-visual-2.md](campo-visual-2.md) (seções 4.3 e 4.7)
- **Prévia:** [link](https://orgatec-site--ideia-campo-visual-2-zktkjnan.web.app/rural/janela-de-campo.html) (expira em 11/12/2026). Usa o boletim real do ar.

## O que muda (só na Janela de Campo)

1. **"Comparar as regiões" vira uma grade de glifos** (6 regiões × 5 operações). Cada célula é só o glifo de estado de 26 px (cheio com ✓, vazado com !, cheio com ✕, pontilhado com –), com texto alternativo ("Centro-Oeste, Pulverização: com restrição"). Antes era uma tabela de 680 px mínimos com selos, que rolava para o lado dentro da própria caixa.
2. **Cabe em 320, 375, 768 e 1280 px, sem rolar** (a página e a própria caixa). Os cabeçalhos de coluna têm três formas conforme a largura: abreviados ("Plant.", "Colh.") abaixo de 400 px, curtos ("Plantio", "Colheita") até o desktop; o nome completo fica para leitor de tela.
3. **"Igual em todas"**: quando as seis regiões têm o mesmo estado numa operação, o cabeçalho da coluna diz "igual em todas" (do tablet para cima) e uma frase abaixo da grade resume: "Igual em todas as regiões: pulverização (com restrição), plantio (favorável) e máquinas (favorável)." Só aparece quando há coluna igual e mais de uma região.
4. **Tocar no nome da região escolhe a região** (antes só a célula escolhia). Alvos de 48 px.
5. **Legenda com os quatro glifos**, incluindo "Sem previsão" (região sem nenhuma hora útil prevista na operação).
6. **Boletim vencido ou desatualizado fica em cinza** (cartões, glifos do dia, faixas horárias e a grade), com opacidade menor, para consulta de arquivo. O veredito já some nesses casos (V1).

## O que não muda

Formato do boletim (JSON), regras e limites (V20), satélite, abas, veredito, cartões e folha do local (V1), tabela dos 7 dias (V3), "Minha atividade". Sem verde e sem vermelho; estados nunca só por cor.

## Medição (Playwright, boletim real de 11/11/2026)

| | Antes | V2 |
|---|---|---|
| Grade das regiões, celular 375 px (altura) | tabela de 680 px que rola para o lado | 572 px, sem rolagem |
| Rolagem horizontal da página (320 / 375 / 768 / 1280 px) | nenhuma | nenhuma |
| Rolagem horizontal dentro da grade | sim, no celular | nenhuma |
| Menor alvo de toque na grade | 52 px | 48 px |

## Testes

- Unitários: `colunasIguais` e `fraseIguais` (3 testes em `tests/js/campo-veredito.test.js`).
- E2E novos: grade sem rolagem nas quatro larguras, "igual em todas" só nas colunas iguais, tocar na região ou na célula, glifo de "sem previsão" e boletim vencido em cinza.

## Fora desta fase

Linha do dia em SVG, ícones de tempo na tabela dos 7 dias, rótulos de 13 px em toda a página e modo Ao sol (V3); cartão do WhatsApp (V4).

## Pronto quando

Suíte completa e bandit verdes; prévia aberta em 375 px e 1280 px e aprovada.
