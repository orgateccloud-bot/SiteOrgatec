# Plano de incorporação dos sistemas ORGATEC ao site

**Levantamento:** 01/11/2026. Foram lidos só documentação, configuração e código-fonte; nenhum `.env`, banco, laudo, extrato ou dado de cliente foi aberto. **Situação:** Fase 1 implementada em 01/11/2026 (menu Soluções, vitrine, páginas de conciliação e de auditoria rural, selo e botão "Entrar" controlados por `config.solucoes`, nenhum link para sistema). Fases 0, 2, 3 e 4 pendentes.

## 1. Resumo

O site é **institucional e estático**: Firebase Hosting, CSP `script-src 'self'` e API própria só para formulários. Os sistemas são **aplicações com login, dados sensíveis e infraestrutura própria**. Por isso a incorporação **não é técnica, é de navegação e de conteúdo**:

- **Páginas no site:** cada sistema que vai a público ganha uma página no site, com o design do site e textos sem dado de cliente.
- **Aplicação separada:** o sistema continua no próprio endereço (subdomínio), com login, CSP e banco próprios.
- **Ligação:** o site só faz **link** para o sistema. Não embute (iframe), não importa o código e não chama as APIs dos produtos.
- **Pedido de demonstração:** vai pela API do próprio site (Cloud Run em São Paulo), com o campo `produto`. Enquanto a API não está no ar, vai pelo WhatsApp com mensagem pronta.

| Sistema | O que é | Situação hoje | Entra no site como | Quando |
|---|---|---|---|---|
| **OrgConc** | Conciliação bancária e auditoria fiscal forense; multiempresa, RLS por `org_id` | Beta em produção (Railway), nota 8,0 e 1.262 testes | Página de produto + pedido de demonstração; depois, botão "Entrar" em subdomínio | Fase 1 (página) / Fase 2 (link) |
| **OrgAudi** | Auditoria forense rural NFA-e (SEFAZ-GO), laudo PDF, Funrural/IRPF rural | Uso interno, sem produção confirmada, nota 7,6 | **Página de serviço** do escritório, com laudo de exemplo fictício. O sistema continua interno | Fase 1 |
| **Mini (MiniSaaS)** | Lançamentos, importação OFX/PDF/NFe, forense e projeção IBS/CBS para PJ | Protótipo local, sem git nem CI | Página de produto "em breve", junto com o crédito do OrgCred (D5); depois, área logada do cliente PJ | Fase 3 |
| **OrgCred** | Microcrédito da ORGATEC como ESC (LC 167/2019) | O próprio projeto diz que não opera com dinheiro real; capital R$ 0 e registradora pendente | Página institucional só depois das decisões regulatórias; depois, "Área do tomador" | Fase 4 |
| **OrgAgentDoc** | Gerador dos 21 modelos Word + agente Claude com fila de aprovação | Protótipo local (localhost) | Não entra como sistema. Fornece os dados de marca (`manifest.json`) e o catálogo de documentos para os textos de serviço | Fase 1 (dados) / Fase 4 (pedido de documento) |
| **FinancePreditiva** | Finanças pessoais com previsão (XGBoost + Claude) | Pausado ("Geladeira"), sem infraestrutura, dados planejados nos EUA | **Não entra** | — |

## 2. Antes de qualquer link público (Fase 0, nos repositórios dos sistemas)

Estes pontos **bloqueiam** a publicação de links para os sistemas. Não são trabalho do site. A troca de senhas e chaves é feita por você, no painel de cada serviço.

1. **OrgAudi: senha do banco exposta.** `docs/SUPABASE_MIGRATION_STATUS.md` traz a URL de conexão do Supabase com a senha em texto claro, além de uma credencial de teste.
   - Troque a senha no Supabase.
   - Remova o trecho do documento e do histórico do git.
   - Confira também `k8s/helm/orgaudi-chart/orgaudi-supabase-secret.yaml`, que está versionado e não foi aberto neste levantamento.
2. **OrgConc: troca de chaves pendente (P0 do próprio projeto).**
   - Chave Anthropic, senha do banco e service-role do Supabase.
   - 6 scripts locais com chave Anthropic em texto puro.
   - Confirme se `api/services/pii_mask.py` mascara CPF/CNPJ antes da Claude API, porque os documentos do projeto se contradizem.
3. **Mini: cadastro aberto põe qualquer pessoa na empresa nº 1.** `POST /api/auth/signup` (`saas/api/auth.py:138`) vincula o novo usuário ao primeiro tenant do banco, e é esse endpoint que o botão da tela usa. Além disso, a `SECRET_KEY` tem valor padrão no código. **Não publique nenhum link para o Mini antes de corrigir isso.**
4. **OrgAudi não tem multi-tenant.** Qualquer usuário logado vê todos os clientes (`api/routes/auditoria.py:46-65`). Ele **nunca** deve ter login de cliente final enquanto isso existir.
5. **Imagens dos sistemas:** só com dados fictícios. As capturas existentes nos repositórios (por exemplo, `Mini/ss_*.png`) **não** devem ser reaproveitadas, porque podem conter dados reais.
6. **Documentação:** `Mini/PLANEJAMENTO.md` cita uma empresa cliente e valores. Nenhum trecho dela vai para o site.

## 3. Estrutura do site (navegação)

- **Menu atual:** Consultoria · Reforma · Setores ▾ · Ferramentas ▾ · Escritório.
- **Proposta:** acrescentar o grupo **Soluções ▾**, no mesmo padrão de Setores e Ferramentas (`tools/layout.py`, lista `NAV`).

```
Soluções ▾
├── Todas as soluções                       solucoes/index.html          (vitrine)
├── Conciliação e auditoria bancária        solucoes/conciliacao.html    (OrgConc)
├── Auditoria forense rural (NFA-e)         solucoes/auditoria-rural.html (OrgAudi, serviço)
└── Gestão financeira para empresas         solucoes/gestao-financeira.html (Mini e crédito do OrgCred, "em breve")
```

**Área do cliente** (`cliente/index.html`) vira o ponto único de acesso, com um cartão por sistema e o selo "disponível" ou "em breve":

| Cartão | Destino | Disponível quando |
|---|---|---|
| Portal contábil (documentos, guias, relatórios) | `portal.orgatec.io` | ERP decidido (pendência C2) |
| Conciliação (para escritórios e clientes do OrgConc) | subdomínio do OrgConc | Fase 2 |
| Gestão financeira (cliente PJ, com o crédito do OrgCred) | subdomínio do Mini; o crédito, no subdomínio do OrgCred, a partir do mesmo cartão | Fases 3 e 4 |

**Outras ligações:**
- **Vitrine (`inicio.html`):** o carrossel "Ferramentas" ganha um irmão, o carrossel "Soluções", e o painel de fontes oficiais continua.
- **Tela de abertura:** ganha um quinto atalho, "Soluções", ao lado de Área do cliente, Simuladores, Central da Reforma e WhatsApp. O botão principal continua levando à área tributária.

## 4. Layout da página de produto (modelo único)

Todas as páginas de solução saem de **uma função** em `tools/gerar_paginas.py` (`solucao(dados)`), com os textos num dicionário ou JSON. Seguem o design ORGATEC Trilha, sem importar o visual de cada sistema.

1. **Herói:**
   - selo do tipo ("Produto" ou "Serviço do escritório");
   - título com o problema resolvido;
   - uma frase;
   - CTA principal "Solicitar demonstração" (ou "Falar com o escritório", no caso dos serviços);
   - CTA secundário "Entrar", só quando o subdomínio existir.
2. **Para quem:** cartões de público (escritório contábil, empresa no lucro real, produtor rural, transportadora).
3. **Como funciona:** os mesmos 3 a 4 marcos usados em `MARCOS` (componente `.marcos`).
4. **O que entrega:** grade de recursos. Usar só recursos que existem e estão testados no repositório, citando o documento do sistema como base.
5. **Segurança e LGPD:** apenas afirmações verificáveis, como isolamento por empresa (RLS), anonimização antes da IA (Protocolo @Delta) e trilha de auditoria. Cada uma precisa ser conferida no código antes de publicar.
6. **Exemplo:** imagem ou PDF **com dados fictícios** (laudo de exemplo, tela de conciliação), gerado de propósito para o site.
7. **Base legal**, quando houver regra tributária (ex.: CBS/IBS no OrgConc, Funrural no OrgAudi), com fonte de `fontes.js` e selo "pendente de validação" quando for o caso.
8. **Perguntas frequentes** e **faixa final** com o pedido de demonstração.

**Selo de situação**, lido de `config.js` (`solucoes.<id>.situacao`):

| Situação | Efeito na página |
|---|---|
| `disponivel` | Mostra o botão "Entrar". |
| `demonstracao` | Mostra só o pedido de demonstração. |
| `em_breve` | Mostra a lista de interesse. |
| `rascunho` | A página não vai para o menu e fica com `noindex`. |

Assim, ligar ou desligar um sistema no site é mudar uma linha.

## 5. Integração técnica

| Tema | Decisão |
|---|---|
| Embutir o sistema no site (iframe) | **Não.** O OrgConc já envia `X-Frame-Options: DENY`; os outros não têm CSP adequada para isso. |
| Site chamando a API dos sistemas | **Não.** A CSP do site continua `connect-src 'self'`. Nada de status ao vivo nem contagens. |
| Código dos sistemas no site | **Não.** Nenhum bundle, nenhuma fonte do Google além das que o site já usa. |
| Link para o login | **Sim**, só depois da Fase 0 e com domínio próprio. As passkeys do OrgConc exigem domínio próprio (`*.up.railway.app` é recusado). |
| Pedido de demonstração | API do site. O modelo `LeadIn` (`backend/schemas.py`) ganha `produto: Literal['conciliacao','auditoria_rural','gestao_financeira','credito','documentos']`. A trilha `audit_hash` e o consentimento LGPD continuam iguais. Enquanto o Cloud Run não está no ar (pendência T1), usar WhatsApp com a mensagem do produto. |
| Login único (SSO) | Fora do escopo. Cada sistema tem o próprio: JWT próprio no OrgConc e no OrgAudi, Supabase Auth no OrgCred. Unificar exigiria um provedor OIDC; fica registrado como ideia. |
| Domínios | **Decisão D3.** Hoje coexistem `orgatec.io` (site), `app.orgatec.cloud` (exemplo no OrgConc) e `app.orgatec.com.br` (comentário na landing do OrgConc). Sugestão: `orgatec.io` + subdomínios `conciliacao.`, `app.` (Mini), `credito.` e `portal.` (ERP). |
| Identidade visual | Hoje há cinco paletas (Atlas Hidrográfico no OrgConc, Aurora no OrgAudi e no Mini, "oc" no OrgCred, Neon/Aurora no OrgAgentDoc). O site **não** adota nenhuma. Ideia: publicar `design-system/orgatec-trilha/tokens.json` como fonte para os sistemas convergirem. É um trabalho separado, em cada repositório. |
| Dados de marca | O site já tem CNPJ, endereço e responsável técnico. `OrgAgentDoc/sistema-modelos-orgatec/manifest.json` traz tagline, contatos e signatário. Confira antes de usar: o e-mail aparece como "orgatefmo@gmail.com", o que parece erro de digitação. |

## 6. Fases

### Fase 0: segurança nos sistemas (bloqueia os links; feita por você e nos repositórios de cada sistema)
Itens 1 a 4 da seção 2.

### Fase 1: páginas estáticas no site (sem link para sistema nenhum)
1. Criar o grupo "Soluções" no `NAV`, gerar `solucao()` e o `config.solucoes`.
2. Criar a vitrine `solucoes/index.html` e as páginas `conciliacao` (situação `demonstracao`) e `auditoria-rural` (serviço).
3. Pedido de demonstração pelo WhatsApp com mensagem por produto.
4. Montar o laudo de exemplo do OrgAudi com dados fictícios (PDF estático ou imagem).
5. Registrar as pendências no painel de testes (`homologacao.js`) e atualizar o mapa de páginas (`MAPA`).
6. Testes:
   - menu e rodapé iguais;
   - nenhuma página de solução com script ou fonte externa;
   - selo de situação obedecendo ao `config.js`;
   - nenhum link para subdomínio de sistema enquanto a situação não for `disponivel`.

### Fase 2: OrgConc com acesso (depois da Fase 0 e da decisão D3)
1. Configurar o domínio próprio do OrgConc.
2. Passar a situação para `disponivel`; o botão "Entrar" aparece na página e na área do cliente.
3. Pedido de demonstração pela API do site, com o campo `produto` (depende do faturamento Blaze, pendência T1).

### Fase 3: Mini (depois do item 3 da Fase 0)
1. No repositório do Mini:
   - corrigir o cadastro e tornar a `SECRET_KEY` obrigatória;
   - passar para Postgres com migrations;
   - pôr o projeto no git com CI;
   - trocar os CDNs, o Tailwind Play e os scripts embutidos por arquivos próprios (CSP).
2. Publicar o Mini em subdomínio e ligar a página e a área do cliente.

### Fase 4: Crédito ESC e documentos
1. **Crédito em Gestão financeira:** o cartão já avisa que o crédito entra ali e que não há oferta. Detalhes, condições e o botão "Entrar" só depois das decisões regulatórias do OrgCred (capital, entidade registradora, IOF e parecer COAF) e de rever a publicidade de crédito com o responsável técnico.
2. **Pedido de documento:** um endpoint restrito na API do site põe o pedido na fila de aprovação humana do OrgAgentDoc, sem chamar o LLM direto do site.

### Fora do plano
FinancePreditiva. Se for retomado, vira no máximo uma página "Labs" com link para um subdomínio, e só com os dados no Brasil e acordo de tratamento de dados (DPA) com o fornecedor da IA.

## 7. Decisões que dependem da ORGATEC

| # | Decisão | Por que importa |
|---|---|---|
| D1 | O OrgConc será **vendido a outros escritórios** (SaaS) ou só mostrado como diferencial do serviço ORGATEC? | Muda o público e o texto da página. A landing atual do OrgConc fala com escritórios, e o site fala com empresas e produtores. |
| D2 | **Nomes públicos:** OrgConc, OrgAudi, Mini e OrgCred, ou nomes descritivos ("Conciliação ORGATEC")? | Marca e SEO. |
| D3 | **Domínio:** `orgatec.io`, `orgatec.cloud` ou `orgatec.com.br`, e quais subdomínios? | Passkeys, cookies e certificados. |
| D4 | **Preços do Mini** (a landing do Mini tem planos Gratuito, Pro a R$ 97 e Enterprise): publicar ou não? | Compromisso comercial público. |
| D5 | **Crédito ESC no site:** decidido em 04/11/2026: entra em **Gestão financeira**, não em página própria. Falta definir quando e com que texto de oferta. | Atividade regulada (LC 167/2019). Anunciar antes de operar é risco; por isso o cartão diz que ainda não há oferta. |
| D6 | **Quem aprova** os textos de cada página de solução (responsável técnico e responsável pelo produto)? | Mesma regra da reforma: nada vai a público sem revisão. |

## 8. Coordenação com a outra sessão

Uma sessão vinculada está evoluindo o site em paralelo (por exemplo, a página "Janela de Campo" em Setores). As fases 1 em diante mexem em `tools/layout.py` (`NAV`), `tools/gerar_paginas.py` e `site/assets/js/config.js`, que essa sessão também usa. A implementação deve começar **depois** que ela terminar, ou numa branch combinada, para que uma não sobrescreva a outra.

## 9. Fontes do levantamento (por sistema)

- **OrgConc:** `README.md`, `CLAUDE.md`, `PROJETO_MAPEAMENTO_COMPLETO.md`, `DEPLOY.md`, `api/main.py`, `api/core/config.py`, `api/core/bootstrap.py`, `orgconc-react/src/pages/LandingPage.tsx`, `design-system/MASTER.md`.
- **OrgCredV1:** `README.md`, `DECISOES_PENDENTES.md`, `MAPEAMENTO_E_PLANO_DE_COMBATE.md`, `RELATORIO_FINAL.md`, `app/core/security.py`, `app/main.py`, `frontend/src/index.css`.
- **OrgAudi:** `README.md`, `CLAUDE.md`, `MAPEAMENTO_2026-08-11.md`, `docs/SUPABASE_MIGRATION_STATUS.md`, `api/routes/auth.py`, `api/routes/auditoria.py`, `frontend/frontend/src/index.css`, `pdf_engine/orgaudi_v240/styles.py`.
- **OrgAgentDoc:** `sistema-modelos-orgatec/README.md`, `agente/README.md`, `agente/web/api.py`, `agente/web/servidor.py`, `manifest.json`.
- **Mini:** `PLANEJAMENTO.md`, `saas/main.py`, `saas/api/auth.py`, `saas/core/security.py`, `saas/static/index.html`, `saas/static/landing.html`.
- **FinancePreditiva:** `docs/auditoria/relatorio-executivo.md`, `docs/adr/0008-deploy-render-vercel.md`, `docs/conformidade/lgpd.md`, `backend-api/package.json`, `frontend-web/package.json`.
