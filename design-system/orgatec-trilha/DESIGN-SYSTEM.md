# ORGATEC Trilha · design system

Adaptação do design system do projeto Trilha (DESIGN-SYSTEM.md de 31/10/2026) com o nome trocado para
**ORGATEC**. Gerado por `design-system/gerar_trilha.py`; os valores das paletas vêm do código do Trilha
(`PRESETS` e `applyTheme` em `trilha.html`) e estão em `design-system/orgatec-trilha/tokens.json`.
Demonstração: `site/orgatec-trilha.html`. Este design ainda **não** está aplicado ao site: a escolha entre
ele e o `orgatec-template2` é a pendência D6 do painel de testes.

---

## 1. Conceito

O gesto de quem estuda lei seca: **marcar o trecho** (marca-texto) e **dar o visto** de concluído.
Tema gráfico: trilha, caminho e marcos. Sóbrio para concurso jurídico e OAB, com feedback de progresso
leve (anel, marcos, sequência de dias), sem gamificação barulhenta.

**Princípios**

1. **O próximo passo primeiro.** Toda tela responde "o que eu faço agora?" antes de mostrar detalhe.
2. **Cor tem papel, não decoração.** Primária orienta, marca-texto marca, âmbar alerta. Nada além disso.
3. **Funciona sem nós.** Sem login, sem internet depois da primeira visita, dados no aparelho.
4. **Texto claro, em português do dia a dia.** Rótulos dizem o que acontece; nada de jargão técnico.

---

## 2. Marca

### Nome
**ORGATEC**, sempre em maiúsculas (regra da marca de 30/10/2026). No código do modelo original, os nomes
internos `trilha.*` continuam; eles não aparecem para a pessoa.

### Símbolo
Quadrado arredondado (a página), faixa de marca-texto e visto. SVG inline, sempre com rótulo:

```html
<svg viewBox="0 0 64 64" role="img" aria-label="ORGATEC">
  <rect x="5" y="5" width="54" height="54" rx="12" fill="none" stroke="var(--brand)" stroke-width="5"/>
  <rect x="14" y="34" width="36" height="11" rx="2" fill="var(--hl)"/>
  <path d="M19 33 L28 42 L46 21" fill="none" stroke="var(--ink)" stroke-width="6"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

- Na ORGATEC já existe um símbolo oficial: a esfera de quatro faixas (`site/assets/marca/orgatec-original.png`, extraído da imagem original por `tools/extrair_logo_original.py`).
  Decisão de 31/10/2026: com este design, a ORGATEC usa o logotipo original, sempre com as cores originais,
  inclusive nas paletas escuras. O símbolo do modelo Trilha fica só como referência.
- Tamanho mínimo: **20 px**.
- Cores sempre por token (`--brand`, `--hl`, `--ink`), para seguir a paleta ativa.
- Ícone do app instalado (`pwa/icone-192.png`, `icone-512.png`): símbolo sobre `#08111F`, ocupando os
  60% centrais (zona segura para ícone adaptável).

### Assinatura
Símbolo + palavra **ORGATEC** em maiúsculas (o modelo original usava minúsculas), fonte de títulos peso 800, `letter-spacing: -.03em`.
No app, ao lado: sigla do plano e nome de quem estuda.

### Crédito
"Desenvolvido por Warley Moreira Veloso", junto da versão. Nunca creditar ferramentas de IA.
No modelo original, materiais de estudo não levavam o nome da ORGATEC; nesta adaptação o design passa a ser
da ORGATEC, e o rodapé segue a regra do site (CNPJ, responsável técnico com CRC, LGPD, NBC PG 01).

---

## 3. Cor

### Papéis

| Token | Papel | Regra |
|---|---|---|
| `--bg` | Fundo da página | — |
| `--surface` / `--surface2` | Cartões e áreas internas | — |
| `--ink` | Texto principal | contraste ≥ 4,5:1 sobre `--bg` e `--surface` |
| `--muted` | Texto secundário, legendas | — |
| `--line` | Bordas de 1 px | — |
| `--brand` | Títulos, links, aba ativa, bloco de teoria | — |
| `--brand-soft` | Etiquetas neutras, fundo de ícone | — |
| `--hl` (marca-texto) | Hoje, meta, concluído, botão principal | **só marca**: nunca texto corrido, nunca área grande |
| `--hl-soft` | Fundo de bloco concluído e do dia de hoje | — |
| `--warn` (âmbar prazo) | Alerta, questões, desatualizado | só alerta |
| `--warn-soft` | Fundo de aviso | — |
| `--focus` | Anel de foco; bloco de áudio | — |

### Paletas do seletor de cores (8)

Chaves: **p** primária · **h** marca-texto · **ink** texto · **a** alerta · **s** etiquetas · **bg** fundo.

| id | Nome | Tipo | p | h | ink | a | s | bg |
|---|---|---|---|---|---|---|---|---|
| `auto` | Automático | segue o sistema | Verde (claro) ou Noturno (escuro) | | | | | |
| `verde` | Verde Toga | claro · **padrão** | `#1F4D40` | `#F2C14E` | `#18211E` | `#9A5212` | `#DCE7E1` | `#F3F5F2` |
| `azul` | Azul Tribunal | claro | `#1D3F6E` | `#F5C451` | `#131A26` | `#A4471C` | `#DDE5F0` | `#F2F4F7` |
| `vinho` | Vinho Toga | claro | `#6B1E2E` | `#F0C04A` | `#1E1416` | `#8A5A10` | `#EEDFE2` | `#F6F2F2` |
| `ciano` | Grafite e Ciano | claro | `#155E6B` | `#F4D35E` | `#161B1E` | `#9B4A12` | `#D9ECEF` | `#F2F5F6` |
| `noite` | Noturno | escuro | `#8FC7B2` | `#F2C14E` | `#E6ECE8` | `#E3A961` | `#22322C` | `#111916` |
| `azul-fl` | Azul flutuante | claro · flutuante | `#1D5FD6` | `#4B8FE0` | `#0C1A33` | `#B03A0A` | `#E3ECFB` | `#EAF1FB` |
| `azul-fl-esc` | **Azul flutuante escuro** | escuro · flutuante · **padrão da página inicial e de quem entra por ela** | `#6EA8FF` | `#9CC3FF` | `#E6EEFB` | `#FF8A4C` | `#12233F` | `#08111F` |

A escolha fica em `localStorage` (`trilha.tema`) e é aplicada por variáveis inline em `<html>`.
Quem entra pelo botão "Começar" da página inicial abre o app em `azul-fl-esc`, se ainda não escolheu outra.

### Derivação do resto da paleta

- Escuro quando a luminância de `bg` < 0,2.
- `surface` = branco no claro; `bg` + 6% de branco no escuro.
- `muted` = mistura `ink`→`bg` a 36%. `line` = mistura `bg`→`ink` a 16%.
- `hl-soft` = mistura `bg`/`h` a 30% (claro) ou 22% (escuro). `warn-soft` = `bg`/`a` a 16%.
- Texto sobre `--hl`: `#18211E` se a luminância de `h` > 0,3; nas paletas flutuantes, `#06142B`.
- Texto sobre `--brand`: branco ou `#18211E`, o de maior contraste.

### Tokens completos

**Verde Toga (claro, padrão do app)**

```css
:root{
  --bg:#F3F5F2;--surface:#FFFFFF;--surface2:#E9EEEA;--ink:#18211E;--muted:#4F5C56;--line:#D5DDD8;
  --brand:#1F4D40;--brand-ink:#F3F5F2;--brand-soft:#DCE7E1;
  --hl:#F2C14E;--hl-ink:#18211E;--hl-soft:#FBEFC9;
  --warn:#9A5212;--warn-soft:#F6E6D3;
  --focus:#2B6CB0;--shadow:0 6px 18px rgba(20,30,25,.10);--r:10px;
}
```

**Noturno (escuro automático do app)**

```css
--bg:#111916;--surface:#18221E;--surface2:#1F2B26;--ink:#E6ECE8;--muted:#9AA8A1;--line:#2C3833;
--brand:#8FC7B2;--brand-ink:#111916;--brand-soft:#1F3029;
--hl:#F2C14E;--hl-ink:#18211E;--hl-soft:#3A3218;
--warn:#E3A961;--warn-soft:#33281A;--focus:#7FB3F2;
```

**Azul flutuante escuro (página inicial e privacidade)**

```css
--bg:#08111F;--surface:#171F2C;--surface2:#1D2737;--ink:#E6EEFB;--muted:#969EAC;--line:#2B3442;
--brand:#6EA8FF;--brand-ink:#08111F;--brand-soft:#12233F;
--hl:#9CC3FF;--hl-ink:#06142B;--hl-soft:#293850;
--warn:#FF8A4C;--warn-soft:#302426;--focus:#9CC3FF;--r:14px;
```

**Tema escuro no CSS.** Tokens em `:root`; escuro em `@media (prefers-color-scheme: dark)` com
`:root:not([data-theme="light"])` e repetido em `:root[data-theme="dark"]`, sempre com
`color-scheme: dark`. Componentes usam só tokens, nunca cor literal.

---

## 4. Estilo flutuante

Ligado pelas paletas "flutuante" (`data-float` em `<html>`): todos os efeitos abaixo entram juntos.

| Efeito | Valor |
|---|---|
| Sombra (claro) | `0 1px 2px rgba(15,40,90,.06), 0 8px 24px -8px rgba(15,40,90,.16)` |
| Sombra elevada (claro) | `0 2px 4px rgba(15,40,90,.08), 0 18px 40px -12px rgba(<primária>,.32)` |
| Sombra (escuro) | `0 1px 2px rgba(0,0,0,.4), 0 10px 28px -10px rgba(0,0,0,.6)` |
| Sombra elevada (escuro) | `0 2px 6px rgba(0,0,0,.45), 0 20px 44px -12px rgba(<primária>,.35)` |
| Subir no hover | `translateY(-3px)`, transição `.2s`; desligado em `prefers-reduced-motion` |
| Brilho de fundo | `radial-gradient(900px 520px at 8% -6%, rgba(p,.18–.22), transparent 60%)` + `radial-gradient(760px 480px at 100% 30%, rgba(h,.12–.16), transparent 60%)` |
| Abas e cabeçalho em vidro | pílula, `rgba(255,255,255,.72)` (escuro `rgba(23,31,44,.62)`), borda `--line`, `backdrop-filter: blur(14px) saturate(1.4)` |
| Cantos | 14 px (clássico: 10 px) |
| Fontes | Sora + IBM Plex Sans |

---

## 5. Tipografia

| Papel | Clássico | Flutuante | Uso |
|---|---|---|---|
| Títulos (`--f-display`) | Bricolage Grotesque 700/800 | Sora 600–800 | títulos, números de destaque, assinatura |
| Texto (`--f-body`) | Source Sans 3 400/600/700 | IBM Plex Sans 400–600 | corpo, botões, formulários |
| Dados (`--f-mono`) | IBM Plex Mono 400/500 | IBM Plex Mono | artigos de lei, datas, horários, rótulos em CAIXA ALTA |

- Corpo: **16 px** na tela, 11 pt impresso; linha 1,5–1,55; largura de leitura ~65–70 caracteres.
- Rótulo de seção ("eyebrow"): mono, 12 px, caixa alta, `letter-spacing: .08em`, cor `--hl` (flutuante)
  ou `--muted`.
- Títulos com `text-wrap: balance`; títulos grandes com `letter-spacing` negativo (-.03 a -.035em).
- Números alinhados em colunas: `font-variant-numeric: tabular-nums`.
- Google Fonts, sempre com fallback de sistema (`"Segoe UI", system-ui, sans-serif`;
  `ui-monospace, Consolas, monospace`).

---

## 6. Forma, espaço e movimento

- **Cantos:** 6–10 px no clássico, 14 px no flutuante; pílula (999 px) em botões da página inicial e no
  cabeçalho de vidro.
- **Bordas:** 1 px `--line`. Sem sombra no tema clássico.
- **Espaço:** grid/flex com `gap`, nunca margem por elemento. Gutter lateral
  `max(16px, env(safe-area-inset-*))`.
- **Responsivo:** grades caem para 1 coluna; tabelas em caixa com `overflow-x: auto`; a página nunca
  rola na horizontal.
- **Movimento:** curto e com propósito (bloco concluído, anel de progresso, marca-texto que risca o título
  da página inicial, marcos que acendem ao rolar). Tudo desligado em `prefers-reduced-motion`.
  Conteúdo nunca fica invisível esperando animação.

---

## 7. Ícones

Sprite SVG inline (`<symbol id="i-…">`), traço 2 px, pontas arredondadas, `currentColor`, 20 px.
**Nunca emoji.**

`book` `pen` `flag` `check` `ext` `cal` `chart` `lib` `user` `gear` `palette` `map` `fire` `trash` `plus`
`left` `right` `target` `mountain` `lock` `unlock` `star` `audio` `video` `list` `clock` `sun` `refresh`

---

## 8. Componentes

### Cabeçalho
Assinatura à esquerda; botões **Cores** e **Cadastro** à direita; borda inferior 2 px `--ink` (clássico)
ou barra de vidro em pílula (flutuante, página inicial).

### Botões
- Padrão: borda `--line`, fundo `--surface`, altura mínima 44 px.
- Principal: fundo `--hl`, texto `--hl-ink` (app) · fundo `--brand`, texto `--brand-ink` (página inicial).
- Rótulo diz o que acontece: "Salvar e ir para o cronograma", "Importar e ativar", "Gerar token".
- Ação destrutiva pede confirmação **na própria página** (o 1º clique arma o botão por 6 s e muda o
  rótulo para "Confirmar: …"). Nunca `confirm()` do navegador.

### Cartão de indicador (KPI)
Rótulo mono em caixa alta com ícone, valor grande na fonte de títulos (~30 px), subtítulo `--muted`.
Cartão "Hoje" com fundo `--hl-soft`. Anel de progresso SVG com traço `--hl`.

### Bloco do cronograma
O componente central. Borda esquerda de 4 px pela natureza do bloco; topo com tipo + caixa "Feito?";
horário em mono; disciplina em negrito; tópico; link "Abrir: material ↗"; campo de acertos nas questões.

| Tipo | Classe | Borda esquerda | Ícone |
|---|---|---|---|
| Teoria / Lei seca | `t` | `--brand` | `book` |
| Leitura | `l` | `--muted` | `list` |
| Questões / Prática | `q` | `--warn` | `pen` |
| Áudio | `a` | `--focus` | `audio` |
| Videoaula | `x` | `--brand`, dupla, 5 px | `video` |
| Revisão / Escrita / Avaliação | `v` `r` `s` | `--hl` | `refresh` `pen` `target` |
| Dia-alvo (prova) | `p` | `--hl` + fundo `--hl-soft` | `flag` |
| Dia livre | `off` | tracejada, fundo `--bg` | — |
| Concluído | `.done` | fundo `--hl-soft`, borda `--hl` | visto |

Com horários próprios, os blocos do dia saem em ordem de horário. Contador "x de y blocos" e % da semana
atualizam juntos.

### Trilha das fases
Marcos circulares ligados por linha tracejada. Concluída: `--brand` com visto. Atual: `--hl` com halo.
A seguir: neutro. No celular vira lista vertical.

### Etiquetas e marcadores
- `.tag` (mono, 11,5 px, fundo `--brand-soft`, texto `--brand`) · `.tag.w` para aviso (`--warn-soft`).
- Prioridade: quadrado 24 px; A = `--brand` cheio, B = contorno `--brand`, C = contorno neutro.
- Confiança: fato / fonte secundária (`--brand-soft`) · inferência / divergente (`--warn-soft`).
- Guia: 2× 3× (fundo `--hl`) · Armadilha, Desatualizado (`--warn-soft`) · Novo (`--brand-soft`).

### Sugestão e aviso
Borda esquerda 4 px `--warn` sobre `--warn-soft`; versão positiva `.ok` com `--brand`/`--brand-soft`.

### Toast
Pílula `--ink` com texto `--bg`, no rodapé, `aria-live="polite"`, ~1,8 s. Frase curta e afirmativa
("Bloco feito", "Sincronizado", "Plano recebido de outro aparelho").

### Seletor de cores
As 8 paletas aparecem em três lugares: botão **Cores** do cabeçalho, passo 2 do Cadastro e
Configurações. Cada opção mostra 4 amostras (p, h, ink, bg) e o nome; a escolha vale na hora e mostra
um toast "Cores: <nome>".

A identidade Trilha prevê ainda um **painel de cores completo** (arrastável, com chaves por efeito
flutuante, troca de fonte, régua de cantos 2–22 px, ajuste de cada cor, códigos para copiar e contraste
WCAG ao vivo). Ele **ainda não existe no ORGATEC**; quando for feito, segue a skill `trilha-design-estudos`.

---

## 9. Página inicial

- Herói com título curto e uma palavra marcada pelo marca-texto animado; subtítulo; dois botões
  (principal leva ao cadastro).
- Demonstração interativa à direita (estudo do dia com anel de progresso), marcada como exemplo.
- Seções: Como funciona (4 marcos reais: cadastro → plano → cronograma → prova), Recursos (6 cartões),
  Calculadora de horas, Perguntas (details/summary), chamada final, rodapé com crédito e Privacidade.
- Atalho "Continuar de onde parou" só aparece para quem já tem cadastro no aparelho.

---

## 10. Acessibilidade

- Contraste de texto ≥ 4,5:1 em todas as paletas (conferir ao criar uma paleta nova).
- Todo controle com rótulo (`<label>` ou `aria-label`); ícones decorativos com `aria-hidden`.
- Foco visível de 2–3 px em `--focus`; navegação completa por teclado; abas com setas.
- Alvos de toque ≥ 44 px.
- `prefers-reduced-motion` respeitado; `prefers-color-scheme` respeitado no modo Automático.

---

## 11. Voz e texto

- Português do Brasil, direto, frases curtas, voz ativa.
- Nomear pelo que a pessoa reconhece: "Sincronização", "Apagar meus dados do servidor", não "endpoint
  RPC" (termos técnicos só na área avançada de Configurações).
- Erro diz o que houve e como resolver: "O token precisa de pelo menos 32 caracteres. Use "Gerar token"
  ou cole o de outro aparelho."
- Sem exclamação, sem emoji, sem promessa que o app não cumpre.

---

## 12. Regras técnicas que afetam o design

- **Arquivo único** no código-fonte (HTML + CSS + JS embutidos); a publicação separa o script em
  `app.js`/`inicio.js` para a CSP (`script-src 'self'`). Nenhum `on…=` em HTML; eventos só por script.
- **Conteúdo de plano é dado de terceiros.** HTML de plano passa por lista de tags permitidas:
  `b strong i em u s small sub sup code br span a ul ol li p mark abbr`; atributos só `class`, `title`
  e `href` http(s). Estilos inline de plano são removidos: a aparência vem só dos tokens.
- **Sem dependência externa** além do Google Fonts. Ícones e gráficos em SVG inline.
- **App instalável:** `theme_color` e `background_color` `#08111F`; abre em `/app`.
- **Dados do usuário** só em `localStorage` (com `try/catch`) e, se ligada, na sincronização.

---

## 13. Onde está no código

| O quê | Arquivo |
|---|---|
| Paletas, tokens e documento adaptado | `design-system/orgatec-trilha/` (gerado por `design-system/gerar_trilha.py`) |
| Demonstração com seletor de cores | `site/orgatec-trilha.html` |
| Código de origem (referência) | `D:\01_Projetos_Ativos\Trilha\trilha.html` (`PRESETS`, `applyTheme`) e `inicio.html` |
| Design atual do site, para comparar | `design-system/orgatec-template2/` e `site/orgatec-template2.html` |
