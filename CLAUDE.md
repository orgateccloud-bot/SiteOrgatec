# Site ORGATEC

O fluxo completo está em `docs/fluxo-de-desenvolvimento.md`.

- **Não trabalhe em `D:\01_Projetos_Ativos\SiteOrgatec`.** Essa pasta fica na `main`, limpa, porque o agendador publica o boletim por ela. Trabalhe em `D:\01_Projetos_Ativos\SiteOrgatec-dev` (branch `desenvolvimento`) ou em uma branch `ideia/<nome>` com pasta própria.
- **Prévia:** `python tools/previa.py`. Não usa orgatec.io.
- **Publicação:** só com `python tools/publicar.py`, na pasta principal, com autorização do usuário. Nunca rode `firebase deploy` direto.
- **Dados:** `site/dados/` fica fora do git.
- **Painel público:** `site/assets/js/homologacao.js` vai ao ar. Detalhes de segurança ficam só em `docs/`.
