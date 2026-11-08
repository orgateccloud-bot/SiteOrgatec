# Plano de ativação do boletim no GitHub Actions, com alerta (08/11/2026)

Canal de alerta escolhido em 08/11/2026: **GitHub Actions**. Este plano diz o que já existe, o que falta, o que você precisa decidir e como reverter. **Nada foi ativado**: nenhum workflow novo está em `.github/workflows`, nenhuma permissão foi alterada e as tarefas do Windows continuam como estão.

## 1. Onde estamos (conferido em 08/11/2026)

| Item | Estado |
|---|---|
| Protótipo do boletim no GitHub | Pronto na branch `ideia/boletim-actions` (ainda não na `main`): gera o boletim, restaura o histórico do site no ar e guarda o resultado como artefato |
| Publicação sem chave de serviço | **Confirmada** em 07/11/2026 (execução 42306843277), por federação de identidade, num canal de prévia (`teste-actions`); reteste em 08/11 depois de dar leitura no serviço `orgatec-api` do Cloud Run |
| Federação no Google | Criada: pool `github-actions`, provedor `github-orgatec` e conta `boletim-deploy` sem chave. **O provedor aceita só a branch `ideia/boletim-actions`** |
| Publicação unificada (commit `7f0fc2b`) | O agendador do Windows só publica quando a `main` é exatamente a última tag `publicado-*`; o `publicar.py` dá push da `main` e da tag no fim. O GitHub já tem as 15 tags `publicado-*`, inclusive a última (`publicado-20261108-0916`), e a `origin/main` está igual à `main` local |
| Agendador do Windows | Funciona quando a credencial do Firebase está válida. Entre 04 e 08/11, **4 rodadas foram geradas e não publicadas por credencial vencida** (04/11 17h, 05/11 05h, 06/11 05h, 08/11 05h) |

## 2. O alerta, em camadas

1. **Falha da execução.** Se o workflow do boletim falhar (geração ou publicação), o GitHub avisa por e-mail. Pela [documentação do GitHub](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs), o aviso de execução agendada vai para quem criou o workflow, e muda para quem editar a linha do `cron` depois; o e-mail só chega se essa pessoa tiver as notificações de Actions ligadas (dá para limitar a "só falhas").
2. **Vigia de atraso** (pronto, inativo). `tools/vigiar_boletim.py`, com testes, confere o boletim que está no ar e falha quando ele passa de 14 horas, está ilegível ou o site não responde. O workflow de exemplo é `docs/ideias/boletim-vigia.yml.exemplo` (a cada 2 h, no minuto 23). Ele cobre o que a camada 1 não vê: a execução que **não rodou** (o GitHub avisa que execuções agendadas podem atrasar ou ser descartadas em horários de pico, sobretudo no começo da hora) e a publicação que falhou sem erro visível. Testado contra o boletim real: em dia (3,8 h), e alerta com limite de 1 h.
3. **O próprio site.** O visitante já vê "Boletim desatualizado" depois de 18 horas. O vigia avisa antes (14 h).

**Limites que continuam:**
- O vigia também roda no agendador do GitHub; se o GitHub falhar, os dois param juntos.
- Alerta só vale se alguém lê o e-mail da conta que o recebe.
- A regra de desligar execuções agendadas depois de 60 dias sem atividade vale para repositórios públicos, segundo a [documentação](https://docs.github.com/actions/managing-workflow-runs/disabling-and-enabling-a-workflow); o seu é privado.

## 3. O que falta fazer para ativar (checklist)

1. **Workflow do boletim** (`.github/workflows/boletim-campo.yml`, a partir de `docs/ideias/boletim-no-actions-publicar.yml.exemplo`), com estes ajustes que o exemplo ainda não tem:
   - **Código da última tag, não da `main`.** Fazer o checkout da tag `publicado-*` mais recente e gerar o boletim com o código dela, que já passou na suíte, para o GitHub não levar ao ar código sem suíte (mesma regra do agendador depois do commit `7f0fc2b`).
   - **Conferir a tag de novo antes de publicar.** Se uma publicação nova acontecer enquanto a execução está em andamento, abortar em vez de sobrescrever o código novo com o antigo.
   - Cron em minuto "quebrado", por exemplo `7 8,14,20 * * *` (05h, 11h e 17h de Brasília, que são 08h, 14h e 20h UTC).
2. **Restaurar também o histórico de notícias.** `tools/restaurar_dados_do_site.py` (na branch do protótipo) restaura só `agro/noticias.json` (constante `FIXOS`). Falta `agro/historico.json`, criado na Fase 6. Sem ele, cada execução no GitHub começaria sem histórico e o acúmulo de 180 dias das notícias nunca se formaria.
3. **Ampliar o provedor da federação** para aceitar a `main` (hoje só aceita `ideia/boletim-actions`). Mexe em IAM do projeto `orgatec-site`.
4. **Se a `main` ganhar outros destinos de rewrite** além do Cloud Run `orgatec-api`, dar leitura neles à conta `boletim-deploy` (o reteste de 08/11 falhou com 403 até isso ser feito para o `orgatec-api`).
5. **Vigia:** copiar `boletim-vigia.yml.exemplo` para `.github/workflows/boletim-vigia.yml` na `main`.
6. **Desligar as tarefas do Windows** só no fim da semana de sombra: `python tools/gerar_boletim_campo.py --remover-agendador`.
7. Atualizar `docs/ideias/boletim-no-actions.md` e a memória do projeto.

## 4. Semana de sombra (recomendada)

Durante 7 dias o GitHub gera o boletim e publica **só num canal de prévia**, enquanto o agendador do Windows continua publicando no ar. Assim os dois nunca disputam o `orgatec.io`. Passa para o ar se, em 7 dias (21 rodadas), não houver falha, o boletim do GitHub tiver o mesmo formato do que está no ar e o vigia ficar verde. Depois: ampliar o provedor, trocar o canal de publicação para o ao vivo e desligar o agendador do Windows no mesmo dia.

## 5. Custo (segundo `docs/github-actions-e-custos-2026-11.md`, arquivo local da outra branch)

Plano Free com cerca de 2.000 minutos por mês no Linux. O boletim, 3 execuções por dia de cerca de 1 minuto faturado, dá 90 a 100 minutos por mês. O vigia, 12 execuções por dia com mínimo de 1 minuto, dá cerca de 360. Total perto de 460 minutos (cerca de 23% da cota). Se quiser gastar menos, o vigia a cada 4 horas custa cerca de 180. Não conferi a cota no GitHub; é o número do documento.

## 6. Decisões que são suas

1. **Autorizar a semana de sombra.** Envolve criar os workflows no GitHub e, na virada, ampliar o provedor no Google. Eu só faço com a sua autorização expressa (GitHub e Google são áreas de autorização à parte).
2. **Quem recebe o alerta.** A conta do GitHub que criar o workflow ou editar o `cron` (pode ser a sua, em vez da conta `orgateccloud-bot`), com as notificações de Actions ligadas e um e-mail que você leia.
3. **Limite e frequência do vigia.** 14 horas e a cada 2 horas, ou outro valor.
4. **Quando desligar o agendador do Windows.** Sugestão: no dia da virada.
5. **Um segundo aviso** (por exemplo, no celular) além do e-mail do GitHub, ou só o e-mail.

## 7. Como reverter

- Desativar os workflows (aba Actions, "Disable workflow") ou apagar os arquivos de `.github/workflows`.
- Reativar o agendador do Windows: `python tools/gerar_boletim_campo.py --instalar-agendador`.
- Desfazer a federação: apagar a conta `boletim-deploy`, o provedor e o pool (`docs/ideias/boletim-no-actions.md`).
- O vigia não altera nada; é só leitura de um arquivo público.

## 8. O que foi criado agora

`tools/vigiar_boletim.py` e `tests/py/test_vigiar_boletim.py` (20 testes), `docs/ideias/boletim-vigia.yml.exemplo` e este plano. Nada disso roda sozinho nem vai ao ar até alguém publicar a `desenvolvimento`.
