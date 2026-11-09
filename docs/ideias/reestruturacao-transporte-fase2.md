# Fase 2: sitemap e áreas (preparada, não executada)

Situação: **não executada.** Toda a fase exige aprovação do escritório (mover páginas, mudar `firebase.json`, decidir R1 e o destino da tela de abertura). O que já foi feito sem mover nada: a Área Empresarial existe com endereços novos (`empresarial/`) e o menu já tem o grupo **Empresarial** ao lado de Setores.

## Decisões que travam a fase

1. **R1, formato de URL.** `cleanUrls: true` (endereços sem `.html`) ou manter `.html`.
2. **Destino da tela de abertura.** Hoje `/` é a abertura (`abertura()` em `tools/gerar_paginas.py`) e a vitrine é `inicio.html`. O plano manda `/inicio.html` → `/`. Opções: (a) a vitrine passa a ser `/` e a abertura vira outra página; (b) a abertura é aposentada em `_legado/` com plano de retorno; (c) manter as duas e não mexer.
3. **Aprovar o `firebase.json`.** Ele é gerado por `tools/preparar_firebase.py`: os redirecionamentos entram no gerador, e o arquivo é regerado. Não editar à mão.

## Tabela de 301 (destino conforme R1)

| Atual | Se `cleanUrls: true` | Se manter `.html` |
|---|---|---|
| `/inicio.html` | `/` | `/` |
| `/setores/agro.html` | `/rural/` | `/rural/index.html` |
| `/setores/janela-de-campo.html` | `/rural/janela-de-campo` | `/rural/janela-de-campo.html` |
| `/setores/agro-mercado.html` | `/rural/cotacoes` | `/rural/cotacoes.html` |
| `/setores/transporte.html` | `/empresarial/transporte` | `/empresarial/transporte.html` |
| `/setores/regional.html` | `/reforma/alertas-regionais` (com `?setor=` e `?uf=`) | `/reforma/alertas-regionais.html` (idem) |
| `/tributario/index.html` | `/consultoria-tributaria` | `/consultoria-tributaria.html` |
| `/escritorio/index.html` | `/quem-somos` | `/quem-somos.html` |
| `/compliance/publico/*.html` | `/compliance/publicos/*` (opcional, curinga) | idem, com `.html` |

Regras: mapear direto para o destino final, sem cadeia; cobrir as duas formas de cada URL movida (com e sem `.html`); os embeds `/cotacoes/*.html` não se movem.

## O que fica pronto para quando houver aprovação

- Menu final (fonte única em `tools/layout.py`): Reforma, Rural, Empresarial, Compliance, Soluções, Consultoria, Cliente e WhatsApp.
- `/empresarial/` (feito), `/empresarial/lucro-real` (feito), `/empresarial/transporte` (a página existe em `setores/transporte.html`; falta mover).
- Home com duas portas ("Sou produtor rural" e "Tenho empresa ou transportadora").
- Testes e2e a escrever junto da mudança: cada URL antiga responde 301 para o destino final; nenhum link interno aponta para URL antiga; as âncoras usadas em links internos (`#noticias`, `#transicao`, `#produtor`, `#item-…`) existem no destino. Teste de `cleanUrls` na prévia: como o Firebase trata `index.html`, `/pasta` e `/pasta/`.

## Risco

O site inteiro está com `noindex`, então não há indexação a perder agora. O risco é de links externos e do WhatsApp já divulgados: por isso "nada some sem 301".
