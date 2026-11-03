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

1. Copie `docs/ideias/_modelo.md` para `docs/ideias/<nome>.md` e preencha.
2. Crie a branch e a pasta, a partir da pasta `SiteOrgatec-dev`:
   ```bash
   git worktree add -b ideia/<nome> ../SiteOrgatec-<nome> desenvolvimento
   ```
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

Na pasta `SiteOrgatec`:

```bash
git merge desenvolvimento
python tools/publicar.py
```

O `publicar.py` só publica da `main`, sem alterações pendentes e com JS, bandit e pytest passando. Depois marca a versão com uma tag `publicado-AAAAMMDD-HHMM` e envia ao GitHub.

## Conflitos em páginas geradas

As páginas de `site/` saem de `tools/`. Em conflito num HTML gerado, resolva o gerador e rode de novo a ordem do README, em vez de editar o HTML.

## Dados fora do git

`site/dados/` é regravado três vezes por dia e não entra no git. Ele chega ao ar pela pasta principal, e o `previa.py` copia os dados de lá. Os testes usam amostras próprias.

## Cuidados

- A prévia usa os mesmos cabeçalhos do site. Quando a API estiver no ar, ela também apontará para a API de produção: rever antes de testar formulários em prévia.
- Com o ambiente em produção (T9), confira se as prévias continuam fora do Google.
