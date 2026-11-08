# Janela de Campo: o boletim não pode parar sem ninguém saber (Fase 0)

- **Situação:** aprovada em 07/11/2026 e junta em `desenvolvimento`; falta lançar (publicar com `tools/publicar.py`, com a sua autorização)
- **Branch:** `ideia/campo-confiabilidade`
- **Prévia:** [link](https://orgatec-site--ideia-campo-qualidade-5agwgcx3.web.app/setores/janela-de-campo.html) (a mesma das Fases 0 e 1; expira em 07/12/2026)

## Problema

Entre 03/11 às 17h e 05/11 às 10h28 (cerca de 41 horas) nenhum boletim novo saiu, e o de 04/11 nunca foi arquivado. Causas no log (`tools/logs/campo.log`):

- O MET Norway respondeu 502 e 503 em 04/11 (05h, 11h, 17h) e 05/11 (05h). Um único polo com erro derrubava o boletim inteiro, e o gerador não tentava de novo.
- A publicação falhou três vezes por credencial do Firebase vencida (04/11 17h, 05/11 05h, 06/11 05h). A causa é a validade curta da credencial da CLI (cerca de 16 horas), já documentada em `boletim-actions` e tratada lá.
- Ninguém foi avisado e o índice não registrava o dia perdido.

## Público

Produtor rural que consulta a Janela de Campo, e a equipe interna que mantém o boletim.

## Proposta

Mudanças desta branch (só gerador, montagem e a tela da Janela; nada de layout novo):

1. **Retentativas.** Cada polo tem 3 tentativas (espera de 2 s e 6 s) em erro de rede, 429 ou 5xx, respeitando `Retry-After` com teto de 30 s. Erro 4xx diferente de 429 não insiste.
2. **Previsão guardada.** Se a fonte continuar falhando, vale a previsão guardada há até 3 horas.
3. **Polo sem dado.** O polo sem previsão sai do boletim, que traz `semDados`. A tela mostra "Sem previsão neste horário: X, Y" no status, o resumo cita quantos polos faltaram e a seção "Confiança" lista quais. Cada região precisa manter pelo menos metade dos polos; abaixo disso, ou com 3 polos seguidos sem previsão (fonte fora do ar), nada é gravado e continua o boletim anterior.
4. **Dias sem boletim.** `indice.json` ganha `lacunas` (dias entre o mais antigo e o mais recente do arquivo sem boletim). O seletor da tela mostra "04/11/2026 (sem boletim)", desabilitado. Nenhum dado retroativo é inventado.
5. **Boletim atrasado.** Já existia: a tela marca "Boletim desatualizado" depois de 18 horas (`LIMITE_HORAS` em `campo.js`). Não mudou.

Já resolvido fora desta branch:

- **USER_AGENT.** O gerador de boletim e o de notícias já usam `orgatec.io contato@orgatec.io`, sem o e-mail pessoal. Falta confirmar que a caixa `contato@orgatec.io` existe e é lida, porque o MET Norway usa esse contato para falar com quem abusa da API.
- **Agendador fora do PC (T20) e credencial do Firebase.** Estão na ideia `boletim-no-actions` (branch `ideia/boletim-actions`), em protótipo. Esta branch não mexe nisso.

## Escolhas minhas, fáceis de mudar

Os números abaixo não vêm de norma nem da fonte; foram escolhidos aqui e ficam como constantes no topo de `tools/gerar_boletim_campo.py`: `ESPERAS = (2, 6)`, `ESPERA_MAXIMA = 30`, `CACHE_VELHO_HORAS = 3`, `FALHAS_SEGUIDAS = 3`, e a regra de "metade dos polos por região" em `conferir_cobertura`.

## Decisão que é do usuário: canal do alerta

Nada foi implementado para o alerta, como combinado. Opções:

| Canal | Como funciona | Limite |
|---|---|---|
| **GitHub Actions** (recomendada) | Quando o boletim passar para o Actions (`boletim-actions`), uma execução com erro ou um boletim com mais de 18 h abre um alerta pelo próprio GitHub (e-mail do dono do repositório, sem chave nem senha) | Depende de ativar o T20 e da decisão sobre Blaze descrita lá |
| E-mail pelo conector Gmail | Um script manda mensagem quando a coleta falha | Envia em nome do usuário; precisa de autorização e continua dependendo do PC ligado |
| Aviso do Windows no PC | Notificação local quando a execução falhar | Só adianta com o usuário na frente do PC |

Até lá, o aviso existente na tela (boletim desatualizado depois de 18 h) é a única proteção para o visitante.

## Fontes e validação

- Termos do MET Norway (identificação por User-Agent, cache por `Expires`, sem rajadas): conferidos em 02/11/2026, ver o topo de `tools/gerar_boletim_campo.py`. As retentativas esperam entre pedidos e não aumentam a frequência normal de consulta.
- Não há regra agronômica nem afirmação legal nesta fase; `LIMITES` e `CRITERIOS` não foram alterados (V20 continua pendente).

## Pronto quando

- Os testes novos passam: 3 tentativas, `Retry-After`, 4xx sem insistir, previsão guardada de 1 h serve e de 5 h não, polo sem dado, regiões com menos da metade, 3 falhas seguidas, lacunas no índice, `semDados` no JS.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta no celular mostrando o aviso e a lacuna, e aprovada pelo usuário.
