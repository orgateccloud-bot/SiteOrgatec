# Cotações e notícias do agro: fontes com termos conferidos e card que nunca fica mudo (Fase 6)

- **Situação:** em desenvolvimento (código e testes prontos; falta a prévia e a sua aprovação)
- **Branch:** `ideia/agro-noticias` (parte de `desenvolvimento`, que já tem as Fases 0 a 4)
- **Prévia:** [link](https://orgatec-site--ideia-agro-noticias-lmm935s0.web.app/setores/agro-mercado.html) (expira em 07/12/2026). Conferida em 375 px e 1280 px com dados reais em 07/11/2026 às 23h: 11 cards, 5 com notícia, 6 sem notícia e com os links oficiais, leite sem cotação, 10 de 10 widgets do CEPEA respondendo, sem erro nem rolagem lateral.

## Problema

Dos 11 cards por atividade, só 4 tinham notícia quando medi (07/11/2026): corte, cana, leite e arroz. A causa não era o limite de 90 dias, e sim a profundidade dos feeds:

| Feed | Itens | Período que cobre |
|---|---|---|
| Agência Câmara · Agropecuária | 10 | 27/10 a 06/11 |
| Agência Senado | 15 | só 06/11 |
| Receita Federal | 10 | 28/06/2022 a 22/07/2026, esparsos |

Os termos de reprodução da Câmara e do Senado também nunca tinham sido conferidos (pendência D23), e o estado vazio era só "sem notícia".

## O que esta branch muda

1. **Histórico acumulado.** Cada rodada (05h, 11h e 17h) guarda o que já coletou em `site/dados/agro/historico.json`, por 180 dias, e o card mostra o que for dos últimos 90 dias. O que sai do feed continua valendo. O `noticias.json` que o visitante baixa ficou com 5 KB (antes levava os itens brutos).
2. **Duas fontes a mais**, as mesmas da Agência Câmara e com os mesmos termos: Economia e Meio ambiente. Efeito imediato: milho passou a ter notícia (5 de 11 hoje). A cobertura sobe com o tempo, conforme o histórico se forma; hoje as seis atividades restantes simplesmente não têm nenhuma notícia casando nas fontes.
3. **Estado vazio útil.** O card sem notícia dos últimos 90 dias mostra: o aviso; a última notícia que o histórico tiver sobre o tema, com a data completa (porque pode ser antiga), quando houver; e os links das fontes oficiais (Ministério da Agricultura, Conab, Embrapa e IBGE). Nada é inventado: sem última notícia, só o aviso e os links. Se o `noticias.json` falhar, uma linha fixa no rodapé mantém os links das fontes oficiais, sem depender de JavaScript.
4. **Registro do que cada fonte permite**, em `tools/agro_fontes.json` (chaves `termos`, `acompanhe` e `descartadas`), com a página onde cada termo foi lido, o texto, o que o site faz e a data da conferência. Um teste (`tests/py/test_agro_fontes_termos.py`) exige esse registro para toda fonte coletada.
5. **Crédito dos cards:** o nome de cada fonte leva ao portal dela (antes levava ao arquivo do feed), com o link dos termos e a data da conferência.
6. **Título inteiro.** O título de uma notícia nunca é cortado, porque o gov.br usa licença sem derivações e o Senado pede que não se descaracterize o conteúdo. Título com mais de 300 caracteres deixa de ser listado.

## Fontes e termos (lidos nas páginas oficiais em 07/11/2026)

| Fonte | O que permite | O que o site faz | Ressalva |
|---|---|---|---|
| Agência Câmara | "As notícias disponíveis no portal e nas mídias digitais da Câmara podem ser reproduzidas pelos meios de comunicação, desde que citada a fonte" ([guia da Câmara](https://www2.camara.leg.br/comunicacao/assessoria-de-imprensa/guia-para-jornalistas/noticias-e-fotografias)) | título, data e link, com a fonte | a regra fala em meios de comunicação; a lista só aponta para a matéria |
| Agência Senado | "A reprodução de matérias e fotografias é livre, desde que não haja descaracterização de conteúdo e mediante a citação da Agência Senado e do autor" ([política de uso](https://www12.senado.leg.br/noticias/politica-de-uso)) | título sem alteração, data e link, com a fonte | **o feed não traz o autor**, então o item não o mostra |
| Receita Federal (gov.br) | CC BY-ND 3.0, "Atribuição-SemDerivações", declarada no rodapé do [portal](https://www.gov.br/receitafederal/pt-br/assuntos/noticias) | título sem alteração, data e link, com a fonte | sem derivações: o título não é cortado |

**Descartadas, com o motivo:**

- **Agência Brasil (EBC):** a licença é Creative Commons, mas a [sala de imprensa](https://www.ebc.com.br/sobre/sala-de-imprensa) diz que a reprodução gratuita vale para fins não comerciais, e o uso comercial exige contato com o licenciamento da EBC. O site da ORGATEC é comercial.
- **Feeds que não existem ou não dão para coletar:** o MAPA e a Conab (no portal gov.br) não oferecem feed (404); o site antigo da Conab, `www.conab.gov.br`, tem certificado inválido (erro também no Chromium), então não é linkado; o IBGE bloqueia robôs (403, verificação anti-robô). Nenhuma dessas proteções foi contornada. O Ministério da Agricultura, a Conab, a Embrapa e o IBGE entram só como links para o visitante.
- **CEPEA fora do widget** (valores guardados, RSS, indicador mensal do leite): continua exigindo autorização formal, pendência D21.
- **B3:** continua exigindo contrato, pendência D22.

O leite segue sem cotação: o indicador do CEPEA é mensal e não está no widget.

## Decisão que é sua (D23)

O Senado pede que se cite a Agência Senado **e o autor**, e o feed dele não informa o autor. A lista mostra título sem alteração, data, link para a matéria (que traz o autor) e o nome "Agência Senado". Basta ou vale pedir confirmação à Agência Senado? A pendência D23 no painel de testes ficou aberta com esse texto.

## Para quem cuida da publicação automática

`gerar_noticias_agro.py` agora lê e grava `site/dados/agro/historico.json`. Quem restaurar `site/dados` num ambiente limpo (como o protótipo em `ideia/boletim-actions`, `tools/restaurar_dados_do_site.py`) precisa restaurar esse arquivo também, senão o histórico recomeça do zero; o `noticias.json` antigo, na primeira rodada depois da mudança, vale como histórico.

## Pronto quando

- Os testes novos passam: histórico acumulado e sem duplicar, última notícia de tema sem notícia recente (e não além de 180 dias), título inteiro, registro dos termos, estado vazio na tela e com o arquivo fora do ar.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta em 375 px e 1280 px e aprovada pelo usuário.
