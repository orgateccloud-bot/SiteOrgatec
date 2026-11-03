# Site ORGATEC — evolução conforme o Plano Diretor Digital

Base: `gemini-code-1793402547492.html` (mantido intacto na raiz como referência). A versão evoluída está em `site/`.

## Estrutura

```
site/                         ← publicar esta pasta (estático)
  index.html                  RAIZ = tela de abertura (holograma se forma, cartão surge; "Entrar no site" leva a inicio.html) — tools/gerar_paginas.py abertura()
  inicio.html                 vitrine do site ("Início" do menu, layout.INICIO) em 8 blocos: herói com painel da transição, números, "qual é o seu caso?",
                              últimas da reforma, ferramentas, perguntas e faixa de diagnóstico
  ferramentas/simulador.html  simulador + lead    ferramentas/calendario.html  calendário, .ics e opt-in
                              abertura: assets/js/abertura.js, abertura-intro.js (pré-pintura), holo-logos.js + assets/marca/holo/*.png (máscaras dos logotipos do holograma, geradas) e assets/css/abertura.css; destinos em config.abertura
  setores/janela-de-campo.html  Janela de Campo AUTOMÁTICA: tools/gerar_boletim_campo.py (agendado 05h/11h/17h no Windows) busca o MET Norway para os polos de
                              tools/campo_polos.json, monta com assets/js/campo-regras.js e grava site/dados/campo/ (atual.json, indice.json, boletim-AAAA-MM-DD.json);
                              tela em assets/js/campo.js, satélite NASA GIBS em assets/js/campo-mapa.js; boletins manuais antigos em assets/js/boletins-campo.js;
                              cartões do status/stories e do TikTok em dados/campo/cartao-status.png e cartao-tiktok.png (tools/cartao_campo.py, ver "Janela de Campo automática")
  assets/compartilhar/        imagens de compartilhamento (og:image 1200 × 630) da Central da Reforma e das páginas de público do Compliance — tools/gerar_imagens_compartilhar.py
  compliance/                 área de Compliance: visão geral, termômetro (assets/js/termometro.js + compliance.js), conformidade tributária, PLD/FT, LGPD, integridade e "Por público" (publicos.html + publico/<público>.html, destino publico-<id>)
                              (tools/paginas_compliance.py; itens em assets/js/compliance-itens.js) — plano em docs/plano-area-compliance.md
  solucoes/                   sistemas da ORGATEC (só páginas e link; situação em config.solucoes) — plano em docs/plano-incorporacao-produtos.md
  setores/regional.html       alertas GO-TO-PA    cliente/  portal + captura de XML    contato/  formulário
  tributario/ reforma/ setores/ ferramentas/ escritorio/
                              todas as páginas (inclusive a inicial) geradas por tools/gerar_paginas.py;
                              cabeçalho com grupos Setores e Ferramentas, trilha, rodapé e barra do celular em tools/layout.py
  assets/js/reforma-itens.js  ★ CONTEÚDO DA REFORMA como dados: fato, orientação, status, fontes, data de consulta, revisão técnica
  assets/js/conteudo.js       valida, filtra e renderiza os itens (puro, testável); produção só mostra itens com revisão aprovada
  assets/js/calculadoras.js   transição ano a ano e produtor rural contribuinte ou não (puro, testável)
  assets/js/paginas.js        liga as páginas aos dados (itens, notícias, alertas, calculadoras, prova de confiança)
  assets/js/tema-tailwind.js  cores do Tailwind lidas de tokens.json — gerado por tools/gerar_design_system.py
  assets/css/orgatec.css      tokens + componentes og-* do design system — gerado por tools/gerar_design_system.py
  privacidade.html            política LGPD
  marca.html                  manual da marca: símbolo, assinaturas, ícones, paleta e regras de uso
  orgatec-template2.html      design system (cores, tipografia, medidas, logotipos, componentes) — gerado
  assets/marca/               logotipo ORGATEC (SVG/PNG, favicons, og-image) — gerado por tools/gerar_logo.py
  reforma/*.html              Hub: LC 214, IBS, CBS, Split Payment, Simples Híbrido, Fontes (gerado por tools/gerar_hub.py)
  assets/js/config.js         ★ CONFIGURAÇÃO ÚNICA (pendências do Plano Diretor)
  assets/js/fontes.js         registro de fontes legais (validado / pendente de validação)
  assets/js/regras.js         motor do simulador (puro, testável)
  assets/js/calendario.js     motor do calendário fiscal (puro, testável)
  assets/js/ufs.js            27 UFs, SUDAM/SUDENE/SUDECO, ZFM/ALC, alertas regionais GO/TO/PA
  assets/js/validadores.js    CNPJ, chave de acesso NF-e/CT-e, contato
  assets/js/demo-dados.js     gerado de orgatec_io_modelos_testes.xlsx (IPs mascarados)
backend/                      API FastAPI + Pydantic V2 + SQLite (leads, opt-in, contato)
tools/gerar_demo.py           xlsx → demo-dados.js
tools/gerar_hub.py            gera site/reforma/*.html
tools/gerar_logo.py           gera site/assets/marca/* (python tools/gerar_logo.py --png para os PNGs)
tools/extrair_logo_original.py  ★ símbolo do site: PNG transparente (colorido e branco) e favicons extraídos de fontes-marca/orgatec-logo-original.jpg
site/assets/js/inicio.js      interações da página inicial: painel da transição, números, marcos e perguntas frequentes
design-system/orgatec-template2/  fonte do design system: tokens.json, tokens.css, componentes (bundle.js/css), manual
design-system/gerar_fonte.py  regenera essa fonte; tools/gerar_design_system.py gera site/orgatec-template2.html a partir dela
_legado/                      página inicial anterior (index-2026-10-31.html) e roteiro de volta (LEIA-ME.md) — fora de site/, não é publicada
design-system/orgatec-trilha/ design do projeto Trilha com o nome ORGATEC (DESIGN-SYSTEM.md, tokens.json de 7 paletas) — em teste
design-system/gerar_trilha.py gera essa pasta e site/orgatec-trilha.html (demonstração com seletor de cores); lê D:\01_Projetos_Ativos\Trilha\DESIGN-SYSTEM.md
tests/                        js (node:test), py (backend), e2e (Playwright), ROTEIRO-QA.md
site/testes/index.html        ★ PAINEL DA FASE DE TESTES (noindex): autoteste + pendências da próxima fase (dados em assets/js/homologacao.js)
docs/pendencias-proxima-fase.md  a mesma lista exportada: node tools/exportar_pendencias.js
docs/revisao-tecnica.md       o que conferir antes de publicar cada item da reforma
docs/decisao-auditoria-compliance.md  ideias além do tributário (para decisão; nada implementado)
```

## Arquitetura das páginas (31/10/2026)

- **Página inicial:** é só vitrine. Distribui o visitante para a consultoria, a reforma, os setores e as ferramentas, sem formulários.
- **Uma página por ferramenta ou assunto:** simulador, calendário, alertas regionais, área do cliente e contato. Os IDs dos elementos são os mesmos da página inicial antiga, e o `app.js` só liga o bloco que existe na página.
- **Layout único:** menu, trilha de navegação, rodapé e barra fixa do celular vêm de `tools/layout.py`. O teste `test_menu_e_rodape_iguais_em_todas_as_paginas` garante que nenhuma página diverge.
- **Links antigos:** `/#simulador`, `/#calendario` e similares levam à página nova (`inicio.js`).

## Design do site

Desde 31/10/2026, o site usa o design **ORGATEC Trilha**. Ele vem do projeto Trilha, com o nome trocado para ORGATEC.

- **Cores:** saem de `design-system/orgatec-trilha/tokens.json`, que tem 7 paletas.
- **Seletor "Cores":** fica no cabeçalho de todas as páginas. A escolha é salva no navegador e vale em todo o site.
- **Paleta padrão:** Azul flutuante escuro (escolha da ORGATEC em 02/11/2026; antes, Azul flutuante). O visitante troca no botão "Cores".
- **Componentes:** os `og-*` e as medidas continuam do `orgatec-template2`, agora lendo as cores do Trilha.
- **Classes antigas do Tailwind:** `white`, `slate`, `brandBlue` e similares ficaram ligadas às variáveis da paleta.
- **Exceções:**
  - o botão de WhatsApp continua verde;
  - o manual do logotipo (`marca.html`) mantém as cores fixas da marca.

## Ordem de geração

O design system é a fonte única da identidade visual:

```bash
python design-system/gerar_fonte.py
python design-system/gerar_trilha.py
python tools/gerar_design_system.py
python tools/gerar_holo_logos.py   # só quando mudar um logotipo em fontes-marca/projecao/
python tools/gerar_imagens_compartilhar.py   # og:image por página; antes das páginas, que só apontam para imagem já gerada
python tools/gerar_paginas.py
python tools/gerar_hub.py
python tools/compilar_css.py
```

O primeiro gera `tokens.json`, o CSS e os componentes. O segundo gera o ORGATEC Trilha. O terceiro gera `orgatec.css`, `tema.js` (as paletas e o seletor), `tailwind.config.js` e a página do design system. O último compila o Tailwind em `site/assets/css/tailwind.css`; o site não usa o CDN. Os dois últimos geram as páginas do site.

## Fase de testes

- O site está em modo teste (`config.ambiente = 'homologacao'`).
- O painel `testes/index.html` roda o autoteste e lista as pendências da próxima fase. Ele aparece pela faixa amarela no topo das páginas.
- As pendências com verificação automática mudam de status sozinhas quando `config.js`, `fontes.js`, `ufs.js` ou `reforma-itens.js` são atualizados.
- As demais pendências são marcadas como resolvidas em `site/assets/js/homologacao.js`.
- Para atualizar o documento: `node tools/exportar_pendencias.js`.

## Conteúdo da reforma

- Edite `site/assets/js/reforma-itens.js`. Cada item precisa de pelo menos uma fonte de `fontes.js`, da data de consulta e de um status.
- Toda mudança volta o item para `revisao.status: 'pendente'`.
- Com `config.ambiente = 'producao'`, só aparecem itens com revisão aprovada.
- Roteiro de revisão: `docs/revisao-tecnica.md`.

## Executar

```bash
pip install -r backend/requirements.txt
python -m playwright install chromium
ORGATEC_SEGREDO_IP=<segredo> uvicorn backend.app:app --port 8410   # site + API em http://localhost:8410
```

Sem backend, o site funciona aberto direto do disco; para isso, defina `api.base: null` em `config.js` e os formulários passam a oferecer o WhatsApp.

## Pendências configuráveis (`site/assets/js/config.js`)

| Pendência (Plano Diretor, item 4) | Chave | Padrão |
|---|---|---|
| 1. Ferramenta de captura de XML | `capturaXml.ferramenta`: `'sieg'`, `'arquivei'`, `'omie'` | `null` |
| 2. ERP do CNAME de `portal.orgatec.io` | `portal.erp`: `'athenas'`, `'onvio'`, `'alterdata'`, `'acessorias'`; `portal.cnameAlvo` | `'athenas'` (01/11/2026); alvo `null` |
| 3. E-mails institucionais | `emails.contato.ativo`, `emails.dpo.ativo` | `false` |
| 4. WhatsApp oficial | `whatsapp.validado` | `false` |

Enquanto `ambiente: 'homologacao'`, uma faixa no topo lista o que falta.

## Validar uma fonte legal

Em `site/assets/js/fontes.js`, confira o dispositivo, marque `validado: true` e preencha `conferido`. O selo "pendente de validação" some em todo o site: simulador, calendário, alertas e artigos.

## Publicação

- **Pacote pronto:** `Dockerfile`, `.env.example` e `backend/requirements-prod.txt`.
- **Roteiro e checklist:** `docs/publicacao.md`.
- **Modelo escolhido:** Firebase Hosting (site), Cloud Run (API) e Firestore (banco), em São Paulo. A API escolhe o banco por `ORGATEC_BANCO=sqlite|firestore` (`backend/repositorio.py` ou `backend/repositorio_firestore.py`).
- **Comandos:**

```bash
docker build -t orgatec-site .
docker run -p 8000:8000 --env-file .env -v orgatec-dados:/dados orgatec-site
```

## Produção

- Tailwind compilado (T3) e fontes servidas pelo próprio site (T4, `python tools/baixar_fontes.py` → `site/assets/fontes/`): o navegador do visitante não contata o Google nem CDNs.
- Atrás de proxy: `uvicorn ... --proxy-headers --forwarded-allow-ips=<IP do proxy>` para o limite de requisições usar o IP real.
- Definir `ORGATEC_ORIGENS` com o domínio do site e `ORGATEC_SEGREDO_IP` fixo.

## Janela de Campo automática

```bash
python tools/gerar_boletim_campo.py                       # gera o boletim de agora em site/dados/campo/
python tools/gerar_boletim_campo.py --publicar            # gera e publica no Firebase Hosting
python tools/gerar_boletim_campo.py --instalar-agendador  # tarefas 05h, 11h e 17h no Agendador do Windows (--simular para só ver)
python tools/gerar_boletim_campo.py --remover-agendador
```

- Previsão: MET Norway (CC BY 4.0, uso comercial permitido). O User-Agent identifica o site, e o cache respeita o `Expires`.
- Não usados: CPTEC/INPE (termos proíbem uso comercial sem autorização) e a API do INMET (protegida contra robôs, sem documentação para terceiros). O site leva aos avisos oficiais do INMET.
- Se a previsão de um polo falhar, nada é gravado nem publicado; o log fica em `tools/logs/campo.log`.
- Critérios por operação em `site/assets/js/campo-regras.js`, marcados como pendentes de validação (V10).

### Cartão para o status do WhatsApp, os stories e o TikTok

A cada boletim gravado, `tools/cartao_campo.py` faz imagens PNG 1080 × 1920 com o estado de cada operação por região, a data, a hora de emissão e até quando o boletim vale (paleta Azul flutuante escuro, fontes do site, logotipo original, crédito MET Norway / CC BY 4.0). Um arquivo por formato (`FORMATOS`): o mesmo cartão, encaixado na área que cada rede deixa livre.

| Formato | Para | No PC | No site |
|---|---|---|---|
| `status` | status do WhatsApp e stories do Instagram/Facebook (livre: 140 px no alto, 210 px embaixo) | `cartoes-status/janela-de-campo.png` | `https://orgatec.io/dados/campo/cartao-status.png` |
| `tiktok` | modo foto do TikTok (livre: 130 px no alto, 480 px embaixo, 150 px à direita; o TikTok não publica as medidas, ficaram as mais conservadoras dos guias consultados em 03/11/2026) | `cartoes-status/janela-de-campo-tiktok.png` | `https://orgatec.io/dados/campo/cartao-tiktok.png` |

- `cartoes-status/` fica fora de `site/` e não é publicado; cópias datadas dos últimos 7 dias em `cartoes-status/arquivo/`.
- Os do site saem com o boletim, para abrir e salvar no celular. O Hosting revalida `/dados/**` a cada acesso (`no-cache`), então o link fixo traz sempre o cartão da última emissão.
- **Falha no cartão** (Playwright, fonte, disco) só vai para `tools/logs/campo.log`: o boletim é publicado do mesmo jeito.
- **Boletim vencido** (dia anterior ou gerado há mais de 18 horas) não gera cartão. Se o boletim do dia não sair, os cartões do dia anterior saem dos caminhos fixos; as cópias datadas ficam.
- Refazer os cartões do boletim atual, sem publicar: `python tools/cartao_campo.py`.

## Cards por atividade (Orgatec Audi Agro)

Ficam na Janela de Campo, depois do boletim. A configuração única está em `tools/agro_fontes.json`: atividades, códigos do widget do CEPEA, palavras-chave e feeds.

- **Cotações:** vêm do widget oficial do CEPEA, em `site/cotacoes/<atividade>.html`, gerado por `tools/gerar_paginas.py`. A página abre num iframe com `sandbox="allow-scripts"`, e a CSP só libera o script do CEPEA em `/cotacoes/`.
  - O site não copia nem guarda os valores: a política do CEPEA só libera o widget sem autorização (pendência D21).
  - A pasta não se chama `widgets/` porque bloqueadores de anúncio barram endereços com essa palavra.
- **Notícias:** `python tools/gerar_noticias_agro.py` grava `site/dados/agro/noticias.json`. Roda junto com o boletim às 05h, 11h e 17h, e se um feed cair, ficam os itens válidos anteriores.
- **Logo:** `python tools/extrair_logo_audi_agro.py` gera `site/assets/marca/orgatec-audi-agro.png` a partir de `fontes-marca/orgatec-audi-agro-original.jpg`. As cores da marca (#028227 e #000000) valem só na seção `.audi-agro`.

## Modelos do Instagram (marketing)

`python tools/modelos_instagram.py` desenha as peças do Instagram com a identidade do site: tokens, fontes do site e logotipo original, pela mesma base do cartão (`tools/imagem_marca.py`).

- **Fonte do texto:** a ferramenta só lê a pasta do marketing (`D:\01_Projetos_Ativos\Marketing`): o calendário do mês, os rascunhos das peças (`## Conteúdo`), o kit do Instagram (nome, bio, endereço, destaques) e o link "Vim pelo Instagram" do kit do WhatsApp. Quando o marketing muda um rascunho, basta rodar de novo.
- **Saída** em `modelos-redes/instagram/`, fora de `site/`, então não é publicada:
  - `perfil/foto-perfil.png` (1080 × 1080);
  - `destaques/*.png` (capas, 1080 × 1920);
  - `feed/pNN-MM.png` (lâminas 1080 × 1350; `pNN-capa.png` para peça ainda "a escrever");
  - `stories/DD-MM.png` (véspera de prazo, 1080 × 1920);
  - `simulacao-perfil.html` (simulação local do perfil, abre do disco).
- **Regras das peças:** etiqueta RASCUNHO até o status `aprovado`; verde só no botão do WhatsApp; sem o endereço do site enquanto `config.ambiente` não for `producao` (vale também para o cartão da Janela de Campo); fontes e CRC do responsável técnico na última lâmina.
