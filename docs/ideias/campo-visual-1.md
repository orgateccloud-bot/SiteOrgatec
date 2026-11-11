# Janela de Campo 2, V1: veredito, barra do local e cartões com faixa horária

- **Situação:** implementada em 11/11/2026 na branch `ideia/campo-visual-1`; **aguarda a sua aprovação da prévia**. Não publicada.
- **Branch:** `ideia/campo-visual-1` (parte da `desenvolvimento`)
- **Plano e mockups:** [campo-visual-2.md](campo-visual-2.md) (opção A, escolhida em 11/11/2026) e [arquivo no Figma](https://www.figma.com/design/hbSLuSGZ2Zx7gvxzpPh6vt)
- **Prévia:** a gerar com `python tools/previa.py` depois da sua aprovação para gerar.

## O que muda (só na Janela de Campo)

1. **Cabeçalho enxuto no celular.** Sem o rótulo "Setor · Agro", título menor e a fileira de atalhos (Agro, Transporte, Alertas regionais...) vira o menu "Setores ▾" no canto. Do tablet para cima nada muda.
2. **Status em uma linha:** "● Vigente · atualizado 11h00 · próxima 17h · INMET". Boletim vencido ou desatualizado mantém o aviso em âmbar.
3. **Barra do local**, colada sob o cabeçalho ao rolar: data, polo e UF. Toque abre uma **folha** (diálogo nativo, fecha com Esc) com as regiões e os polos em botões de 44 px; escolher o polo fecha. Ao grudar, a barra mostra os cinco glifos do dia.
4. **Veredito do dia**, escrito a partir dos estados que o boletim já traz, sem regra nova: "Favorável hoje: plantio e máquinas.", "Com restrição: pulverização e colheita (melhor horário 11–16h).", "Evitar: manejo de animais.", com a contagem e a fonte. Previsão parcial é dita ("previsão parcial: 10 de 16 horas").
5. **Cinco glifos do dia** (forma + ícone + cor: cheio com ✓, vazado com !, cheio com ✕, pontilhado com –). Tocar num glifo escolhe a operação.
6. **Cartões por operação** com a faixa de 16 horas (05h às 20h) do polo, a janela em número grande ("11–16h") e o motivo. A orientação de segurança abre **dentro do cartão** (tocar de novo recolhe). Sem polos (boletim manual), o cartão usa o estado da região, sem faixa.
7. **Estados honestos:** boletim vencido ou com mais de 18 horas **não tem veredito** ("Sem veredito: boletim vencido."), e os glifos ficam pontilhados.

## O que não muda

- **O formato do boletim (JSON).** Só campos que já existem (`polos[].ops[op].porHora`, `janela`, `tipoJanela`, `motivo`, `horasPrevistas`); a comparação da semana de sombra continua valendo.
- Regras e limites agronômicos (V20), satélite, abas, "Comparar as regiões" (a grade de glifos é a V2), "Minha atividade".
- Estados nunca só por cor, sem verde nem vermelho, movimento reduzido, uma só chave de `localStorage` (`orgatec.campo`).

## Diferenças em relação ao mockup (e por quê)

- **O veredito é factual, não um conselho.** O mockup dizia "Bom dia para plantar. Pulverize até as 11h."; o código diz "Favorável hoje: plantio e máquinas." e lista as restrições com a janela. Assim o texto nunca afirma mais do que os estados do boletim.
- **O cartão mostra o polo escolhido** (com a faixa hora a hora), não o estado agregado da região; a região aparece na folha e, no desktop, abaixo do título. "Comparar as regiões" continua mostrando o estado por região.

## Medição (Playwright, boletim real de 11/11/2026, 375 × 812 e 1440 × 900)

| | Antes (no ar) | V1 |
|---|---|---|
| Veredito, celular (topo) | não existe | 420 px (com a faixa de homologação de 80 px; 340 px sem ela) |
| Primeira operação, celular (topo) | 718 px (com a faixa) | 765 px (com a faixa; cerca de 685 px sem ela) |
| Altura da página, celular | 4.425 px | 4.787 px |
| Rolagem horizontal | nenhuma | nenhuma |

O primeiro cartão ficou **mais abaixo** do que antes (a decisão agora é o veredito, que vem antes, e o cartão ganhou a faixa horária). A altura da página também subiu; as metas de altura ficam para a V2 (grade das regiões) e a V3.

## Testes

- Unitários do veredito: `tests/js/campo-veredito.test.js` (12).
- E2E novos: veredito acompanha o polo, folha do local, cartão com faixa e orientação, boletim desatualizado sem veredito, barra que gruda, alvos de toque e menu de setores. Seis testes antigos foram atualizados porque a ordem da página mudou de propósito.

## Fora desta fase

Grade de glifos das regiões e estados por região (V2); linha do dia em SVG, ícones de tempo, rótulos de 13 px em toda a página e modo Ao sol (V3); cartão do WhatsApp e compartilhamento (V4).

## Pronto quando

- Suíte completa (JS, pytest, e2e) e bandit verdes.
- Prévia aberta em 375 px e 1280 px e aprovada pelo usuário.
