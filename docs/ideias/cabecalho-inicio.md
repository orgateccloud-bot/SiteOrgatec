# Cabeçalho: o ícone "Início" cobria o nome ORGATEC no desktop

- **Situação:** implementada em 12/11/2026 na branch `ideia/cabecalho-inicio`; suíte e bandit verdes; **aguarda a sua aprovação da prévia**. Não publicada.
- **Branch:** `ideia/cabecalho-inicio` (parte da `desenvolvimento`)
- **Prévia:** [link](https://orgatec-site--ideia-cabecalho-inicio-8qc7n6xz.web.app/inicio.html) (expira em 12/12/2026)

## Problema

Em 1280 px (notebook comum) o ícone de casa do "Início" aparecia por cima da palavra ORGATEC, em todas as páginas. Em 1536 px e acima o cabeçalho passava da caixa de 1280 px e o botão do WhatsApp ia até a borda da tela.

## Causa

O cabeçalho vive em `tools/layout.py` e vale para as 49 páginas. A caixa tem no máximo 1280 px (`max-w-7xl`), com 32 px de margem em cada lado, mas o menu, o logotipo e os três botões da direita somavam cerca de 1.340 px em 1280 px e 1.380 px em 1536 px (com o texto de "Início", "Cores" e "Falar no WhatsApp" aparecendo a partir de 2xl). O logotipo tinha `min-w-0`, então encolhia até o tamanho da imagem e o texto ORGATEC passava para fora da própria caixa, por baixo do menu.

## O que muda

1. O logotipo não encolhe mais (`shrink-0`).
2. Espaço entre os itens do menu de 24 para 16 px (`gap-4`) a partir de 1280 px.
3. A partir de 1280 px, "Início" é só o ícone (o texto fica para leitor de tela e no `title`), "Cores" é só o ícone e o botão verde diz "WhatsApp" (abaixo de 1280 px, com o menu ☰, nada muda).

A medida é a mesma em todas as larguras de desktop; antes a versão larga (2xl) era a que estourava a caixa.

## O que não muda

Itens, ordem e destinos do menu, o menu ☰ do celular e do tablet, a área do cliente e os links de WhatsApp (continuam `wa.me/5562992949161`).

## Testes

- E2E novo (7 larguras: 1024, 1279, 1280, 1366, 1440, 1536 e 1920 px, na Home e na Janela de Campo): o logotipo cabe inteiro, o menu não o cobre, os botões não cobrem o menu, a caixa não tem sobra e a página não rola para o lado.
- O teste que compara o menu de todas as páginas continua verde.
- Suíte completa: 678 testes pytest/e2e passados, 205 JS e bandit sem achados.

## Pronto quando

Prévia aberta em 1280 px e em 1536 px, ou mais, e aprovada.
