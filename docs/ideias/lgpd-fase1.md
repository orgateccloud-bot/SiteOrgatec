# LGPD no backend (Fase 1 de segurança e privacidade)

- **Situação:** aprovada (na branch `desenvolvimento`; falta lançar)
- **Branch:** `ideia/lgpd-fase1` (já integrada e removida)
- **Prévia:** sem prévia. Só muda a API, que ainda não está publicada (T1). No site, só o texto das pendências V6 e T2.

## Problema

A API prometia direitos que o código não entregava. A trilha `audit_hash` incluía o dado pessoal, então apagar um registro quebrava a trilha. Não havia descadastro, nem eliminação por prazo, nem como atender um pedido de titular.

## Público

Quem deixa contato nos formulários e a equipe que atende os pedidos de LGPD.

## Proposta

- Trilha com sal por registro: elimina os dados sem quebrar a cadeia.
- Descadastro em `/api/optin/sair`; confirmar e cancelar exigem clique.
- `tools/lgpd.py`: retenção, localizar, exportar e eliminar titular, conferir a trilha.
- API mais protegida e `starlette` atualizada.

Fazer isto antes de publicar a API evita migrar dados reais: o formato do banco mudou.

## Fontes e validação

- LGPD, arts. 8º, § 5º, 15, 16 e 18.
- Prazos em `backend/retencao.py`: ainda são proposta. Quem aprova é o responsável técnico (V6).

## Pronto quando

- Contrato passando no SQLite e no emulador do Firestore.
- Suíte completa, JS e bandit passando.

## Fora desta fase

- Agendar a retenção (depende da API no ar, T1).
- Enviar os links de confirmação e descadastro por e-mail (T2).
- Atualizar a política de privacidade (Fase 2).
