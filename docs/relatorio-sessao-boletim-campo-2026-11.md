# Relatório da sessão: boletim de campo e área rural (06 a 10/11/2026)

Escrito em 10/11/2026. Tudo o que está aqui foi conferido no repositório, no GitHub ou no site no ar nesta data; o que não foi conferido está dito.

## 1. Resumo

- Você pediu a análise do boletim de campo e da parte rural e um plano de modernização. Executei as **Fases 0 a 6**, cada uma com prévia e a sua aprovação, e todas estão **no ar desde 08/11/2026** (tag `publicado-20261108-0650`).
- Depois vieram: o pacote de decisões (D23, alerta, V20, marca, itens da reforma), a **semana de sombra no GitHub Actions** (autorizada por você), a correção do CI do GitHub e este relatório.
- **Resultado principal da sombra até agora:** o formato do boletim gerado no GitHub é igual ao do ar em todas as rodadas, mas o **agendador do GitHub não cumpre os horários**. Isso muda a recomendação sobre a virada (seção 6).

## 2. O que foi entregue, por fase

| Fase | O que mudou | Medição |
|---|---|---|
| 0. Confiabilidade | 3 tentativas por polo em erro de rede, 429 ou 5xx; previsão guardada por até 3 h; polo sem dado sai do boletim com `semDados`; `lacunas` no índice (dia sem boletim aparece desabilitado) | Entre 03/11 17h e 05/11 10h28 (cerca de 41 h) nenhum boletim saiu por MET 502/503; 4 rodadas foram geradas e não publicadas por credencial do Firebase vencida (04/11 17h, 05/11 05h, 06/11 05h, 08/11 05h) |
| 1. Qualidade | Resumos de até 90 caracteres, `horasPrevistas`, `semDados` (o painel diz quando falta previsão) | Antes, pulverização ficava em "atenção" em 98 de 100 combinações; o texto de cada operação tinha de 190 a 315 caracteres |
| 2. Hub Agro | Página Agro como hub; os cards saem | Janela 14.092 px para 9.772 px no celular |
| 3. Layout da Janela | Decisão do dia na primeira tela, seletor de região e polo, abas (Horas, 7 dias, Satélite, Como decidimos) | Celular 14.092 para 4.376 px; primeira decisão em 2.068 para 718 px; desktop 7.606 para 3.982 px |
| 4. Página Agro | O dia do produtor e os itens da reforma sob demanda, com `tema` | — |
| 5. Satélite | Divisas dos estados (IBGE), hora em cada imagem, aviso de falha da NASA com "Tentar de novo", mapa só carrega ao aparecer | 0 imagens no celular até abrir a aba; 27 no desktop |
| 6. Notícias | Histórico de 180 dias, estado vazio com a última notícia, `termos`, `acompanhe` e `descartadas` | Histórico no ar: 47 itens em 08/11 e 78 em 10/11 |

Licenças conferidas nas páginas oficiais: IBGE (CC BY 4.0, avisar que a divisa foi simplificada), Câmara (reprodução citando a fonte), Senado (sem descaracterização, citar Agência Senado e autor), gov.br (CC BY-ND 3.0), Agência Brasil/EBC (só uso não comercial, **descartada**).

Estado atual no ar, medido em 10/11/2026: Janela de Campo com **4.425 px no celular (375 px)** e **3.924 px no desktop (1440 px)**.

## 3. Publicações

| Quando | Tag | O que levou |
|---|---|---|
| 08/11, 06h50 | `publicado-20261108-0650` | Fases 0 a 6. A publicação das 06h34 foi barrada por credencial do Firebase vencida (`firebase login --reauth` é ação sua); você renovou e saiu |
| 08/11, 15h46 | `publicado-20261108-1546` | Sombra e vigia no GitHub, texto da D23 em `homologacao.js`, duas atualizações do Dependabot. A publicação foi disparada por outra sessão um minuto antes da minha; a minha foi recusada pela trava única e esperei |
| 08/11, 17h29 | `publicado-20261108-1729` | Correções dos testes do CI (ver seção 7) |

A rodada das 11h de 08/11 já saiu no formato novo (`semDados`, resumos curtos, lacuna de 04/11, notícias com histórico).

## 4. Decisões suas nesta sessão

| Assunto | Decisão |
|---|---|
| Marca Orgatec Audi Agro | Fora das páginas (`marca.exibir = false` em `tools/agro_fontes.json`); segue no rodízio do holograma por ora. Falta decidir onde ela volta |
| D23 (autor nas notícias do Senado) | Pedir confirmação à Agência Senado e manter por ora. Rascunho do pedido em `docs/decisoes-agro-2026-11.md`; **falta enviar e registrar a resposta** |
| Canal de alerta do boletim | GitHub Actions |
| Semana de sombra | Autorizada |
| Publicação de 08/11 | Autorizada (duas vezes) |

## 5. Incidentes e correções

- **Credencial do Firebase vencida** barrou a publicação (seção 3). Não contornei o 401/403.
- **Teste que pegou bug real:** a legenda de falha do satélite era sobrescrita; reordenei `atualizarLegenda()`.
- **Retenção das notícias** não era aplicada aos itens do feed; passou a valer depois da junção.
- **Prévia sem dado novo:** a prévia padrão gerava o formato antigo; usei uma prévia que roda os geradores antes.
- **Uma afirmação minha estava errada e foi corrigida:** o site está em modo `homologacao` e mostra os itens da reforma do agro com o selo "em revisão técnica"; a lista só esvazia na virada para produção.
- **Merge:** a `desenvolvimento` avançou por outra sessão (Dependabot) e o `--ff-only` falhou; fiz `--no-ff` limpo (`8923f15`).

## 6. Boletim no GitHub Actions: o que a sombra mostrou

Workflows na `main`: `boletim-campo-sombra.yml` (05h, 11h e 17h de Brasília, sem publicar e sem entrar no Google) e `boletim-vigia.yml` (a cada 2 h, limite de 14 h).

**Formato:** em todas as 4 execuções agendadas, "mesmo formato do que está no ar" e 0 de 30 estados diferentes. O histórico de notícias não encolhe (47, 64, 71, 80 itens).

**Horário (a parte ruim).** Entre a ativação (08/11, 15h46) e 10/11 às 13h22, o cron da sombra tinha **6 horários programados**; rodaram **4**, e nenhuma perto das 05h:

| Rodou em (Brasília) | Horário programado mais próximo | Atraso |
|---|---|---|
| 08/11 20h37 | 17h | 3h37 |
| 09/11 15h41 | 11h | 4h41 |
| 09/11 23h39 | 17h | 6h39 |
| 10/11 13h22 | 11h | 2h22 |

O vigia, programado a cada 2 h (cerca de 22 horários no mesmo período), executou **5 vezes**, todas verdes.

**O que isso significa:**
- A própria documentação do GitHub avisa que execuções agendadas podem atrasar ou ser descartadas; na prática foi bem pior do que eu previ. São 4 dias de dados, então a amostra é pequena, mas o padrão é consistente.
- O **vigia não serve como único alerta**: se ele não roda, ele não avisa. Hoje ele só prova que o GitHub andou.
- O critério de passar para o ar que eu escrevi no plano ("as rodadas começam perto das 05h, 11h e 17h") **não está sendo cumprido**.
- **Recomendação:** não virar a publicação do boletim para o GitHub nos horários do cron. Manter o agendador do Windows como publicador. Para o alerta, escolher entre (a) manter a sombra e o vigia só como observação, (b) um agendador com horário confiável (por exemplo, Cloud Scheduler no projeto do Google, que exige a sua autorização por envolver Google e faturamento), ou (c) um aviso gerado pelo próprio agendador do Windows quando a publicação falhar. A decisão é sua; não mexi em nada.

Registro: o GitHub também executa a sombra em pushes na branch `ideia/boletim-actions` (o arquivo está lá); é inofensivo, só lê.

## 7. CI do GitHub ("Testes")

Estava falhando em dois testes, antes desta sessão. Corrigidos nos commits `bee3237` e `c7767d8`, já no ar na tag `publicado-20261108-1729`; as últimas execuções na `main` e na `desenvolvimento` (10/11) estão verdes.

- `test_credencial_vencida_para_antes_da_suite`: dependia do git do ambiente (a `main` local fica atrás no GitHub).
- `test_vidro_aparelho_lento_desliga_as_animacoes`: no runner, a CPU limitada 25 vezes ainda dava quadros de 33 ms, abaixo do corte de 34 ms da sonda. Agora o teste simula quadros de 80 ms. Diagnóstico feito numa branch temporária, já apagada.
- Não alterei o `vidro.js`. A sonda mede uma vez, 1,5 s depois do carregamento; aparelho que só fica lento depois nunca é detectado. Decisão de produto, em aberto.

## 8. Estado do git (10/11/2026)

- No ar: `publicado-20261110-1602`. A `main` e a `desenvolvimento` estão iguais.
- A pasta `SiteOrgatec-dev` tem 5 arquivos sem commit, do trabalho de transporte de outra sessão; não são meus.
- Branches de fase mantidas até o lançamento definitivo: `ideia/campo-confiabilidade`, `campo-qualidade`, `agro-hub`, `campo-layout`, `agro-pagina`, `campo-satelite`, `agro-noticias`, `boletim-actions` (2 commits fora da `main`, de outra sessão) e `boletim-sombra`.
- Os arquivos `docs/ideias/README.md` listavam as fases como "falta lançar"; corrigi nesta sessão.

## 9. Pendências

**Suas:**
1. Enviar o pedido da D23 à Agência Senado e registrar a resposta.
2. Decidir o canal de alerta de verdade, à luz da seção 6 (e quem recebe: a conta que criou o workflow).
3. Responder às 4 perguntas dos limites agronômicos (V20) ao responsável técnico. Enquanto isso, pulverização quase sempre aparece "com restrição" e plantio e máquinas quase sempre "favorável".
4. Aprovar a revisão dos 32 itens da reforma (0 aprovados hoje), que é o que bloqueia a virada do site para produção.
5. Decidir onde a marca Audi Agro volta.
6. `firebase login --reauth` quando a credencial vencer (cerca de 16 h de validade).
7. D21 e D22 (CEPEA fora do widget, B3): precisam de autorização ou contrato.

**Minhas, dependendo de você:** planejamento visual do boletim (documento `docs/ideias/campo-visual-2.md`, esta entrega), aguardando o seu "execute".

## 10. Fora do escopo, mas visto

No desktop (1280 e 1440 px), o ícone de "Início" do cabeçalho fica **sobre a palavra ORGATEC** e "Consultoria" encosta nela. Confirmei em `inicio.html`, na Janela de Campo e na Central da Reforma. Afeta a primeira impressão de todas as páginas. É um defeito do cabeçalho (provavelmente da barra de navegação), não do boletim. Não corrigi.
