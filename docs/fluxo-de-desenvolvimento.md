# Fluxo de desenvolvimento do site

O histórico fica no git e no GitHub (`orgateccloud-bot/SiteOrgatec`, privado).

## Branches e pastas

| Branch | Para quê | Pasta | Onde aparece |
|---|---|---|---|
| `main` | O que está em orgatec.io | `D:\01_Projetos_Ativos\SiteOrgatec` | orgatec.io |
| `desenvolvimento` | Junta as ideias aprovadas | `D:\01_Projetos_Ativos\SiteOrgatec-dev` | prévia `dev` |
| `ideia/<nome>` | Uma ideia ou projeto, de vida curta | uma pasta por ideia | prévia própria ou só local |

**A pasta principal não recebe trabalho.** O agendador do boletim roda nela às 05h, 11h e 17h. Com alteração pendente, o boletim é gerado, mas não vai ao ar.

## Uma ideia, do começo ao fim

1. Crie a branch e a pasta, a partir da pasta `SiteOrgatec-dev`:
   ```bash
   git worktree add -b ideia/<nome> ../SiteOrgatec-<nome> desenvolvimento
   ```
2. Na pasta nova, copie `docs/ideias/_modelo.md` para `docs/ideias/<nome>.md` e preencha.
3. Desenvolva e faça commits em português.
4. Gere o link de prévia:
   ```bash
   python tools/previa.py
   ```
5. Aprovada, faça o merge na `desenvolvimento` e apague a branch e a pasta:
   ```bash
   git merge ideia/<nome>
   git worktree remove ../SiteOrgatec-<nome>
   git branch -d ideia/<nome>
   ```

## Lançar no site

Primeiro, confira o que falta publicar e se há outra publicação rodando:

```bash
python tools/publicar.py --estado
```

Depois, na pasta `SiteOrgatec`, um comando só:

```bash
python tools/publicar.py --com-desenvolvimento
```

O que o comando faz, nesta ordem:

1. **Confere a pasta:** só publica da `main` e sem alterações pendentes.
2. **Confere o GitHub:** para se a `main` local estiver atrás de `origin/main`.
3. **Confere o Firebase:** para logo se a credencial estiver vencida.
4. **Pega a trava** `.publicando.lock`. Se outra sessão ou o agendador estiver publicando, recusa e mostra quem é.
5. **Avança a `main` até a `desenvolvimento`** por avanço direto. Se não der, para e manda integrar na `desenvolvimento` primeiro.
6. **Roda JS, bandit e pytest.**
7. **Confere se a `main` mudou** durante a suíte. Se mudou, não publica.
8. **Publica,** marca a tag `publicado-AAAAMMDD-HHMM` e envia `main` e tag ao GitHub.

### Regras para várias sessões

- **Ideias:** só entram na `main` passando pela `desenvolvimento`.
- **Pasta principal:** nunca faça `git merge` à mão nela. Use `--com-desenvolvimento`, que faz o avanço já com a trava.
- **Agendador do boletim** (05h, 11h e 17h):
  - usa a mesma trava;
  - **só publica quando a `main` é exatamente a última tag `publicado-*`**, porque não roda a suíte. Assim, código que ainda não passou pela suíte nunca vai ao ar por ele;
  - enquanto houver commit novo sem publicação, ele gera o boletim e não publica. A próxima publicação leva os dados mais recentes.
- **Suíte falhou:** nada vai ao ar e a trava é liberada. Corrija na `desenvolvimento` e rode de novo.

## Conflitos em páginas geradas

As páginas de `site/` saem de `tools/`. Em conflito num HTML gerado, resolva o gerador e rode de novo a ordem do README, em vez de editar o HTML.

## Dados fora do git

`site/dados/` é regravado três vezes por dia e não entra no git. Ele chega ao ar pela pasta principal, e o `previa.py` copia os dados de lá. Os testes usam amostras próprias.

## Cuidados

- A prévia usa os mesmos cabeçalhos do site. Quando a API estiver no ar, ela também apontará para a API de produção: rever antes de testar formulários em prévia.
- Com o ambiente em produção (T9), confira se as prévias continuam fora do Google.
