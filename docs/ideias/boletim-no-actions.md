# Boletim da Janela de Campo no GitHub Actions

- **Situação:** em desenvolvimento (protótipo que só gera, sem publicar)
- **Branch:** `ideia/boletim-actions`
- **Prévia:** não se aplica (o protótipo não publica; o resultado fica como artefato da execução, por 7 dias)

## Problema

O boletim é gerado três vezes ao dia (05h, 11h e 17h) por tarefas do Windows e só roda com o computador ligado e o usuário conectado. Além disso, a credencial da CLI do Google expira em cerca de 16 horas, e a publicação falha até alguém refazer o login (ver `docs/relatorio-riscos-seguranca-continuidade-2026-11.md`, que fica no repositório, e o log do boletim).

## Público

Equipe interna (continuidade da publicação). O visitante não nota diferença.

## Proposta

Rodar o mesmo gerador num runner do GitHub, com a publicação feita sem chave de serviço (federação de identidade). Em duas etapas:

1. **Protótipo (esta branch):** `.github/workflows/boletim-campo-prototipo.yml`. Só dispara à mão (`workflow_dispatch`), não tem `cron`, não publica e não usa credencial do Google. Restaura o histórico que está no ar (`tools/restaurar_dados_do_site.py`), gera o boletim e o cartão do status, confere o resultado e guarda `site/dados` como artefato.
2. **Ativação (depende de autorização do usuário):** agendar, ligar a federação com o Google e publicar. O arquivo `boletim-no-actions-publicar.yml.exemplo` mostra o esqueleto; ele não roda (extensão `.exemplo`, fora de `.github/workflows`).

### Por que o histórico precisa ser restaurado

`site/dados/` fica fora do git e o deploy do Hosting troca o site inteiro. Um runner novo começa sem esses arquivos: publicar assim apagaria os boletins anteriores e o gerador perderia o boletim do dia que ele compara para marcar o que mudou. O protótipo baixa do site no ar o índice, os boletins que ele lista (até 30 dias), o `atual.json` e as notícias do agro. Boletins mais antigos que os 30 do índice não têm como ser listados pela web e não voltariam; para guardá-los de forma definitiva é preciso decidir onde fica `site/dados/` (ver decisões abaixo).

### O que o protótipo não prova

- **Publicação sem chave:** a ação `FirebaseExtended/action-hosting-deploy` só documenta chave JSON. Usar `firebase-tools` com credencial da federação (ADC), sem chave, **não foi confirmado** na documentação oficial; precisa de um teste real antes de qualquer ativação.
- **Faturamento:** não se sabe se o Hosting exige o plano Blaze para a federação funcionar. A conta de faturamento do projeto está fechada (ver o estudo de custos).
- **Horário:** o `schedule` do GitHub roda em UTC, pode atrasar e só vale na branch padrão. Os horários de Brasília (05h, 11h, 17h) são 08h, 14h e 20h UTC (sem horário de verão desde 2019).
- **Rede:** as fontes do boletim e do cartão precisam responder a partir dos IPs do GitHub; só uma execução real mostra.

## Fontes e validação

- Cota e preço do Actions: `docs/github-actions-e-custos-2026-11.md` (arquivo local, fora do git). Em resumo: o plano Free tem US$ 12/mês de computação (cerca de 2.000 min no Linux); 3 execuções por dia de cerca de 4 min dão perto de 360 min/mês, dentro da cota.
- Federação Google: documentação do `google-github-actions/auth` (versão 3) e do Workload Identity Federation. Quem aprova: o usuário, por mexer em IAM do projeto `orgatec-site`.

## Decisões que são do usuário

1. Ativar ou não o `cron` e quando desligar as tarefas do Windows (só depois de uma semana de execuções boas).
2. Criar a federação (pool, provedor restrito a este repositório e à branch `main`, conta de serviço só com Hosting).
3. Onde guardar `site/dados/`: restaurar do site no ar (como no protótipo), branch `dados` ou bucket.
4. Plano Blaze, se a federação exigir.

## Pronto quando

- O workflow roda sem erro num runner limpo e o artefato traz o boletim do dia, o índice com histórico e o cartão do status.
- O teste `tests/py/test_restaurar_dados_do_site.py` passa e a suíte completa segue verde.
- O deploy sem chave foi testado numa prévia (`hosting:channel:deploy`), nunca direto no canal ao vivo, e o resultado está registrado aqui.
