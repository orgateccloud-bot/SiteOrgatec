# Prompt de execução: `ideia/reestruturacao-transporte`

> Cole este prompt no Claude Code aberto na pasta da ideia (`D:\01_Projetos_Ativos\SiteOrgatec-reestruturacao-transporte`). Ele resume tudo o que foi planejado nas sessões de 08 e 09/11/2026: o plano de sitemap v2, as Janelas Empresarial e do Transporte, a reanálise do site e a Central de Viagem com portal e sensores.

---

## 1. Papel e objetivo

Atue como engenheiro full-stack e arquiteto de informação com experiência em SEO técnico e em sistemas de gestão de transporte (TMS). Desenvolva, **em fases e com aprovação entre elas**, a reestruturação do site orgatec.io descrita em `docs/ideias/reestruturacao-transporte.md`. Os detalhes de cada fase estão abaixo.

Responda e escreva em português do Brasil. Seja direto. Comece pela resposta. Em cada afirmação que sustenta uma decisão, diga se é fato verificado (no código ou na fonte), inferência ou opinião, e o grau de confiança. Se não souber, diga "não sei" e como verificar; nunca invente versão, endpoint, parâmetro de API, ID ou dispositivo legal.

## 2. Regras do repositório (obrigatórias)

- Leia `CLAUDE.md`, `README.md` e `docs/fluxo-de-desenvolvimento.md` antes de tudo e siga-os.
- Trabalhe **só** nesta branch e nesta pasta. Nunca na pasta principal `D:\01_Projetos_Ativos\SiteOrgatec`.
- **Nunca publique.** Nada de `tools/publicar.py`, `firebase deploy` ou `hosting:channel:deploy` fora de `python tools/previa.py`.
- As páginas de `site/` saem de `tools/`. **Altere o gerador e rode-o de novo, nunca o HTML gerado.**
- `site/dados/` fica fora do git. `site/assets/js/homologacao.js` vai ao ar; detalhes de segurança ficam só em `docs/`.
- Um item por commit, com mensagem em português no padrão do histórico (`feat:`, `fix:`, `docs:`, `test:`). Antes de cada commit, rode:
  ```bash
  node --test tests/js/*.test.js
  python -m bandit -q -r backend tools
  python -m pytest tests/py tests/e2e -q -p no:cacheprovider
  ```
- Antes de alterar dependências do servidor, rode `pip-audit -r backend/requirements-prod.txt --no-deps --disable-pip`.
- Toda integração externa e todo recurso novo de servidor nasce **atrás de flag desligada**.
- **Pare e peça aprovação** antes de:
  - mudar `firebase.json` (redirecionamentos, cabeçalhos, `cleanUrls`);
  - mover ou renomear páginas;
  - criar coleção ou esquema de banco;
  - ligar autenticação;
  - adicionar dependência ao servidor;
  - qualquer coisa irreversível.
- **Ao fim de cada fase:**
  - gere a prévia;
  - atualize `docs/ideias/reestruturacao-transporte.md` (situação e link da prévia) e a linha da tabela em `docs/ideias/README.md`;
  - se houver pendência nova, registre-a em `homologacao.js` e rode `node tools/exportar_pendencias.js`;
  - pare e entregue o relatório da seção 8.

## 3. Fase 0: descoberta (somente leitura, sem commit)

Confirme ou corrija no código cada premissa abaixo, que hoje é inferência ou foi verificada só no site publicado:

1. **Páginas e geradores:** como `tools/gerar_paginas.py`, `gerar_hub.py`, `paginas_compliance.py` e `gerar_mapa.py` geram as páginas, o menu, o rodapé e o `sitemap.xml`. Diga onde fica a **fonte única do menu** (hoje ele se repete em todas as páginas).
2. **Conteúdo:**
   - `assets/js/conteudo.js` descarta, com `ambiente = 'producao'`, itens sem revisão `aprovada`?
   - Quantos itens de `reforma-itens.js` e `compliance-itens.js` estão aprovados?
3. **Alertas regionais:** quais setores `regras.js` e `ufs.js` cobrem, e se `transporte` aparece.
4. **Schema:** onde é gerado o JSON-LD `AccountingService` (hoje só em `/`) e se existe `BreadcrumbList`.
5. **Hospedagem:**
   - O cabeçalho `X-Robots-Tag: noindex, nofollow` vem de `firebase.json`.
   - `robots.txt` não existe (404).
   - `cleanUrls` está `false` e `trailingSlash` está `false`.
6. **Janela de Campo:** como o boletim é gerado (`tools/gerar_boletim_campo.py`, `/dados/campo/atual.json`), agendado (agendador local às 05h, 11h e 17h, e a sombra no GitHub Actions) e publicado. Esse é o modelo para as Janelas novas.
7. **Backend:** `backend/app.py` (FastAPI 0.162.0, Python 3.12) e o padrão de `backend/repositorio.py`, `repositorio_firestore.py`, `retencao.py` e `tests/py/test_repositorio_contrato.py`.

Entregue um relatório curto: premissa → confirmada, corrigida ou não encontrada, com o arquivo e a linha. Se algo mudar uma decisão da seção 4, diga qual.

## 4. Decisões já tomadas (não reabra sem fato novo)

- **Sitemap final:**
  ```
  /                          Início (a home real; /inicio.html → 301 para /)
  Central da Reforma         reforma/ + cbs, ibs, lc-214-2025, simples-hibrido, split-payment, fontes
                             + alertas-regionais (vem de setores/regional) + ferramentas (simulador, calendário, calculadoras)
  Consultoria tributária     primeiro nível (vem de tributario/), linkada nos hubs
  Compliance                 sem mudança de pasta
  Área Rural  /rural/        hub = o atual setores/agro.html (Fase 2 do agro); janela-de-campo, cotações (agro-mercado),
                             link para solucoes/auditoria-rural e compliance/publico/produtor-rural
  Área Empresarial /empresarial/  hub novo; transporte (vem de setores/transporte), janela (Fase 4), lucro-real (novo)
  Soluções                   conciliacao, auditoria-rural (a auditoria fica aqui e aparece no menu Rural)
  Cliente                    um único botão para o portal (config.portal.url)
  Rodapé                     quem-somos (vem de escritorio/), contato, privacidade, marca
  ```
- **Casa principal de cada página e links cruzados:**
  - **Transporte:** na Área Empresarial. O Rural só linka (frete do produtor).
  - **Alertas regionais:** na Central da Reforma. Rural e Empresarial linkam com `?setor=` já preenchido.
  - **Calendário fiscal:** em Ferramentas, sem mudar a URL e sem renomear para "da reforma".
- **URLs e menu mudam juntos**, numa versão só, antes da virada. O site inteiro está com `noindex`, então não há indexação a perder (fato verificado no cabeçalho HTTP).
- **Os embeds `/cotacoes/*.html` não se movem** (são do CEPEA, com `noindex` e fora do sitemap).
- **Nada some sem 301.** Mapeie direto da URL antiga para a final, sem cadeia de redirecionamentos, e cubra as duas formas de cada URL movida (com e sem `.html`).

## 5. Fases

### Fase 1: correções de virada (sem decisão pendente)

1. **`robots.txt`:** criar via gerador, com a linha `Sitemap:`. O `noindex` continua até a virada (T9).
2. **`gerar_mapa.py`:**
   - `lastmod` real por página: data do último commit que tocou a página, ou do gerador;
   - excluir páginas com `noindex`;
   - teste novo.
3. **Schema:**
   - `AccountingService` na home real;
   - `BreadcrumbList` em todas as páginas a partir da hierarquia da seção 4;
   - `Service` na Consultoria e em Soluções;
   - testes.
4. **Descrições:** as `meta description` acima de 160 caracteres, hoje as 8 de `compliance/publico/` (de 189 a 265), passam a ter até cerca de 155. O sentido não muda; o texto novo vai para revisão (V1) se mudar algum conteúdo técnico.
5. **Beco sem saída do transporte:** tire o link "alertas regionais" da página de transporte até existirem alertas do setor. Incluir `transporte` em `regras.js` exige itens com fonte e revisão técnica: **não crie itens de alerta sem fonte oficial**; liste os candidatos para o responsável técnico.
6. **Pré-renderização:** proponha, sem implementar ainda, como o gerador pode escrever no HTML os itens da reforma, dos alertas e do compliance (hoje só aparecem via JavaScript; a página de alertas regionais tem 114 palavras no HTML). Diga o impacto nos testes.

### Fase 2: sitemap e áreas (depende de R1)

- **Se R1 = `cleanUrls: true`:** os redirecionamentos de `.html` passam a ser automáticos e só as mudanças de pasta precisam de 301 manual. **Teste na prévia** como o Firebase trata `index.html`, `/pasta` e `/pasta/`.
- **Se R1 = manter `.html`:** as URLs novas ficam em `rural/index.html`, `empresarial/transporte.html` e assim por diante.
- **Mapeamento de 301 (destino final, conforme R1):**

  | Atual | Destino |
  |---|---|
  | `/inicio.html` | `/` |
  | `/setores/agro.html` | `/rural/` |
  | `/setores/janela-de-campo.html` | `/rural/janela-de-campo` |
  | `/setores/agro-mercado.html` | `/rural/cotacoes` |
  | `/setores/transporte.html` | `/empresarial/transporte` |
  | `/setores/regional.html` | `/reforma/alertas-regionais` (preservando `?setor=` e `?uf=`) |
  | `/tributario/index.html` | `/consultoria-tributaria` |
  | `/escritorio/index.html` | `/quem-somos` |
  | `/compliance/publico/*.html` | `/compliance/publicos/*` (opcional, uma regra com curinga) |

- **Menu enxuto, com fonte única no gerador:** Reforma · Rural · Empresarial · Compliance · Soluções · Consultoria · Cliente, mais o WhatsApp.
- **Home com duas portas:** "Sou produtor rural" e "Tenho empresa ou transportadora".
- **Testes e2e:**
  - cada URL antiga responde 301 para o destino final;
  - nenhum link interno aponta para URL antiga;
  - as âncoras usadas em links internos (`#noticias`, `#transicao`, `#produtor`, `#item-…`) existem no destino.

### Fase 3: conteúdo da Área Empresarial

1. **`/empresarial/`:** quem atende e quatro cartões (Transporte, Lucro real e presumido, Simples, Janela Empresarial quando existir), mais a chamada para diagnóstico. Sem página "em breve" no menu.
2. **Transporte:**
   - preencher a seção "Pontos da reforma para transporte", se estiver vazia no HTML;
   - frente de compliance do transportador com a tabela 3.6 de `docs/relatorio-publicos-reforma-compliance.md` (RNTRC com revalidação anual, CIOT, piso de frete, vale-pedágio), cada ponto com fonte e status de revisão.
3. **`/empresarial/lucro-real`:** CBS no lugar de PIS/Cofins, créditos e transição. Usa itens existentes com etiqueta de setor.
4. **Etiquetas de setor em `reforma-itens.js`:** hoje existem só `agro`, `transporte` e `todos`. Criar `comercio`, `industria` e `servicos` para o hub se preencher pelos dados. A etiqueta não muda o conteúdo jurídico, mas o item continua na revisão V1.

### Fase 4: Janela Empresarial e Janela do Transporte (depende de R3)

- **Arquitetura:** a mesma da Janela de Campo.
  - Um gerador `tools/gerar_janela_empresarial.py` grava `/dados/empresarial/atual.json`, com `geradoEm` e `proximaAtualizacao`, no padrão de `/dados/campo/atual.json`.
  - A página lê o arquivo do próprio site (a política de segurança tem `connect-src 'self'`) e traz um instantâneo pré-renderizado.
  - O agendamento segue o modelo do boletim: primeiro uma semana de sombra no GitHub Actions, sem publicar.
- **Regras de cada cartão:**
  - mostra fonte, horário da coleta e estado (ok, atrasado, indisponível);
  - falha da fonte nunca exibe valor antigo sem carimbo;
  - piso de frete e alertas normativos só entram depois da revisão humana;
  - avisos: não substitui SEFAZ, ANTT nem parecer do contador.
- **Seletor "Minha atividade"** com os públicos de `compliance/publicos.html`.
- **Fontes:** registre cada uma num JSON no padrão de `tools/agro_fontes.json`, com os termos de uso conferidos e a data da conferência. **Não entra no ar fonte com termos não conferidos.**

| ID | Módulo | Fonte | Situação | Prioridade |
|---|---|---|---|---|
| E1 | Prazos dos próximos 7 dias por regime e UF | calendário do próprio site | sem fonte nova | P0 |
| E2 | Selic, IPCA e dólar | API SGS do Banco Central (séries 11/432, 433, 1) | licença confirmada só em fonte secundária: conferir | P1 (fase 1) |
| E3 | Radar normativo | feeds de Câmara, Senado e Receita já usados nas Cotações; DOU via INLABS | só título, data e link; revisão antes de virar alerta | P1 |
| E4 | "Mudou esta semana" na reforma | histórico de `reforma-itens.js` | verificado | P1 |
| E5 | Disponibilidade da SEFAZ | Portal Nacional da NF-e | sem API conhecida: conferir termos antes | P2 |
| T1 | Piso mínimo de frete vigente | ANTT | **não calcular**: mostrar resolução, data e vigência por revisão humana e linkar a calculadora oficial | P0 |
| T2 | Diesel S10 e S500 em GO, TO e PA | ANP, levantamento de preços (CSV, dados abertos) | oficial; formato do levantamento pode mudar | P0 |
| T3 | Status de CT-e e MDF-e | Portal Nacional CT-e/MDF-e | sem API conhecida: viabilidade e termos | P1 |
| T4 | Prazos do transportador | compliance do transportador + calendário | lacuna de datas hoje | P0 |
| T5 | Clima nos corredores | MET Norway (já usado) + avisos do INMET | confirmar URL e licença atuais do INMET | P1 |
| T6 | Interdições de rodovia | PRF | sem feed em tempo real confirmado: só link | fora da v1 |

### Fase 5: Central de Viagem e portal com sensores (no ar só depois de R4 e R5)

**Referência:** `docs/ideias/anexos/central-viagem-v0.1/`. É o módulo completo escrito fora do repositório, com 56 testes, telas, README e fontes de dados. **Reaproveite a lógica, não a infraestrutura:**

- **Reaproveitar quase como está:**
  - `servicos/jornada.py`, `servicos/despesas.py` (casos de referência conferidos à mão), `servicos/viagem.py`, `geo.py`;
  - `provedores/` (interfaces, simulados, OpenRouteService, MET Norway, ANP e ANTT por CSV, cliente HTTP resiliente, cache);
  - `telemetria/` (HMAC, adaptadores, ingestão idempotente, limitador);
  - as telas `web/transporte/` (o componente da viagem é o mesmo na Central e no Portal).
- **Trocar:**
  - **Banco:** SQLAlchemy, Alembic e PostgreSQL saem. A persistência passa para um repositório no padrão de `backend/repositorio.py` (SQLite) e `backend/repositorio_firestore.py` (Firestore), com teste de contrato no padrão de `tests/py/test_repositorio_contrato.py`, usando o emulador. **Proponha as coleções e espere aprovação.**
  - **API:** um `APIRouter` em `backend/transporte/` incluído em `backend/app.py`, com documentação automática desligada (como o app atual), o mesmo middleware de limite e o mesmo tratamento de IP.
  - **Tempo real:** o Cloud Run escala em várias instâncias, então o distribuidor em memória não serve. A v1 consulta `/posicoes` a cada 15 segundos. SSE só com Firestore ou Pub/Sub como distribuidor, em fase posterior.
  - **Telas:** passam ao design system do site (`orgatec.css`, tokens, `tema.js`, Tailwind compilado), são geradas por `tools/` e ficam com `noindex` e fora do menu até R4.
  - **LGPD:**
    - prazo de guarda das leituras de telemetria em `backend/retencao.py`, eliminado por `tools/lgpd.py`;
    - motorista só com nome e vínculo de usuário;
    - sem coordenadas em log;
    - só coordenadas vão para APIs estrangeiras;
    - base legal do monitoramento registrada em `docs/lgpd/`.
  - **Autenticação:** a interface de autenticador continua; o modo `dev` é recusado em produção. O login real depende de R4. Não ative o Firebase Authentication sem aprovação.
- **Requisitos do briefing original** (Central de Viagem):
  - **Ao lançar a rota:** despesas (combustível, pedágio, hotel e pernoite, borracharia, alimentação, pneus, manutenção, ARLA, outros e reserva), tempo (duração, paradas, pernoites), bloqueios e clima no trajeto.
  - **Parâmetros:** todos ajustáveis pela transportadora (consumo, diárias, custos).
  - **Escala:** serve para frota pequena, média e grande.
  - **Portal do cliente:**
    - mostra tudo isso em modo leitura;
    - cadastra sensores com credencial HMAC exibida uma vez só;
    - aceita qualquer fornecedor por adaptador;
    - recebe leituras idempotentes e acompanha a viagem em tempo real.
  - **Aceite:**
    - a rota de teste mostra despesas, tempo, bloqueios e clima;
    - o portal mostra o mesmo;
    - um sensor simulado, pela API, atualiza posição e status;
    - há testes automatizados de falha, timeout e limite de uso nas integrações;
    - documentação de uso e configuração.
- **Ao terminar a Fase 5,** apague `docs/ideias/anexos/central-viagem-v0.1/` num commit próprio.

## 6. Fontes de dados: situação em 09/11/2026

| Dado | Padrão | Situação |
|---|---|---|
| Rota | OpenRouteService, perfil `driving-hgv` | Plano gratuito de 2.000 rotas/dia e 40/min (openrouteservice.org/plans); sem SLA; precisa de chave. Alternativa: servidor próprio do ORS ou do OSRM. O servidor de demonstração do OSRM é proibido para uso comercial |
| Clima | MET Norway Locationforecast 2.0 | Exige User-Agent identificado; uso comercial a confirmar nos termos oficiais. Open-Meteo não é padrão: o plano gratuito é só para uso não comercial |
| Diesel | ANP, levantamento semanal | Oficial; falta o conversor do arquivo oficial para o CSV normalizado |
| Pedágio | ANTT, dados abertos "Praças de Pedágio" | Localização sim; tarifa em formato aberto **não confirmada** (há só painel). Sem tarifa, usa o parâmetro × eixos |
| Bloqueios | sem API aberta confirmada (DNIT, PRF, ANTT) | Cadastro manual pela transportadora, com raio, validade e fonte |
| Jornada | CTB art. 67-C | Parâmetros; revisão jurídica pendente (ADI 5322) |

Para cada fonte: confirme disponibilidade, custo, limites e termos antes de ligar a flag. Não apresente como disponível o que não confirmou. Sem fonte confiável, use entrada manual, média histórica ou parâmetro configurável.

## 7. Decisões que só o escritório toma (pergunte; não presuma)

R1 formato de URL · R2 `/testes/` público após a virada · R3 definição da Janela Empresarial e se Transporte é perfil ou janela separada · R4 login e área do cliente · R5 faturamento Blaze. Enquanto uma decisão estiver aberta, desenvolva o que não depende dela e deixe o resto atrás de flag ou fora do menu.

## 8. Relatório ao fim de cada fase

1. **O que foi feito:** uma ou duas linhas.
2. **Commits e arquivos principais.**
3. **Link da prévia.**
4. **Verificado / não verificado:** com o motivo.
5. **Pendências e riscos:** até 3 linhas.
6. **Decisão que preciso do escritório para seguir,** se houver.
