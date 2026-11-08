# Bloco de confiança da Conciliação — evidências

Página: `site/solucoes/conciliacao.html#confianca`. O texto sai de `CONFIANCA_CONCILIACAO` em `tools/gerar_paginas.py`.

**Conferência:** 07/11/2026, no código do OrgConc, branch `main` (fa5f0e45, de 02/11/2026). Foi lido com `git show`/`git grep`, porque a pasta `D:\01_Projetos_Ativos\OrgConc` está em outra branch.

**Regra:** uma frase só entra no site com evidência no código. Se o OrgConc mudar, confira de novo antes de mudar o selo.

| Controle no site | Selo | Evidência | Limite (por que não é "no sistema") |
|---|---|---|---|
| Um escritório não vê o outro | em parte | `db/rls/org_isolation.sql`: ENABLE + FORCE RLS com a política `org_isolation` por `app.org_id`. A API conecta como `app_orgconc NOBYPASSRLS` (`desktop/config_store.py`) e faz `SET LOCAL` por transação (`api/db/rls_context.py`). Teste: `tests/test_rls_real_tables.py`. | `reconciliacao_datasets` (extratos, anomalias e relatório) **não tem RLS**: migration 038, "ESTA MIGRATION NAO HABILITA RLS". A separação ali é por usuário, no Python (`verify_sub`). `orgs`, `refresh_tokens` e `ai_insights_cache` usam `allow_all`. A política `superadmin_read` lê todas as orgs. |
| Trilha de auditoria encadeada | no sistema | `api/services/audit.py`: `prev_hash` mais HMAC-SHA256, cadeia por org. `audit_events` só aceita inclusão (trigger e REVOKE UPDATE/DELETE, migration 027). A conferência é `GET /audit/verificar-cadeia`. | O laudo em PDF **não** traz hash da cadeia: só um ID `LAUDO-` e `hash_linha`, sem encadeamento. Não diga que o laudo é à prova de adulteração. `docs/auditoria/ancoras.jsonl` está vazio. |
| Inteligência artificial desligada | no sistema | `api/core/config.py:221-228`: `ORGCONC_LLM_HABILITADO` vale `"0"` por padrão. A máscara está em `api/services/pii_mask.py`, chamada em `conciliacao_llm.py`. | Nomes de terceiros em texto livre (o `memo` do PIX) vão sem máscara, e o próprio código registra isso. Não há afirmação sobre treinamento de modelos, então o site não fala disso. |
| Segundo fator de login | em parte | TOTP em `api/services/mfa.py`. Passkey em `api/routers/auth_webauthn.py`. `ORGCONC_MFA_REQUIRED_ROLES` vale `admin` por padrão (`api/services/auth.py:343`). | É opcional para quem não é admin. Para o admin, só bloqueia algumas rotas (`exigir_mfa_conforme_papel`), e o superadmin do ambiente fica isento. A passkey só funciona com `ORGCONC_WEBAUTHN_RP_ID`/`ORIGIN`, que exigem domínio próprio. |
| Arquivos cifrados | no sistema | `api/services/crypto_repouso.py` (Fernet) cifra `reconciliacao_datasets.payload`, os blobs de `jobs` e os segredos TOTP. A produção recusa subir sem `ORGCONC_DATA_KEYS`. As senhas usam bcrypt. | As colunas com dados pessoais (e-mail e telefone do cliente, `transacoes.memo`) **não** são cifradas. As chaves nunca passaram por um teste de restauração. |
| Hospedagem, guarda e exclusão | a definir | A anonimização do cliente existe (`POST /clientes/{id}/anonimizar`). | A nuvem está desligada desde 02/11/2026 (`infra/nuvem/LEIA-ME.md`) e o sistema roda como aplicativo desktop. A purga de CNPJ vem desligada por padrão. Não existe exclusão completa por cliente nem prazo de guarda definido. |

## O que o site não afirma

Nada disto pode ir para o site sem nova conferência:
- certificação ISO 27001 ou SOC 2;
- hospedagem em São Paulo;
- 2FA obrigatório para todos;
- laudo com hash;
- nomes anonimizados antes da IA;
- exclusão completa a pedido;
- não uso dos dados para treino.

## Pendências relacionadas

- **T12 / Fase 0** (`docs/plano-incorporacao-produtos.md`): a troca das chaves expostas em julho de 2026 ainda não foi confirmada. O acesso ao sistema só abre depois disso.
- **Promover os selos para "no sistema":**
  - **isolamento:** RLS em `reconciliacao_datasets`;
  - **segundo fator:** 2FA exigido no login;
  - **passkey:** domínio próprio.
- **Hospedagem:** publicar a região e o prazo de guarda quando o OrgConc voltar à nuvem.
