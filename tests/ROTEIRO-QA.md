# Roteiro de QA — Site ORGATEC

## 1. Testes automatizados

| Suíte | Comando | O que cobre |
|---|---|---|
| Fase de testes (Node 18+) | `node --test tests/js/homologacao.test.js` | 8 testes: lista de pendências íntegra; modo teste sem liberação para produção; status automático acompanha `config.js`; pendência marcada à mão; erro de verificação não derruba a avaliação; exportação em Markdown; autoteste passando e acusando falha quando falta módulo ou o ambiente não é de teste. No navegador, o mesmo autoteste roda em `site/testes/index.html`. |
| Conteúdo da reforma e calculadoras (Node 18+) | `node --test tests/js/conteudo.test.js tests/js/calculadoras.test.js` | 23 testes. **Itens:** todos válidos e com fonte existente; cobertura mínima de tributos, setores, status e destinos; nenhum aprovado sem revisão; recusa de item sem fonte, com fonte inexistente, status ou data inválidos; produção esconde itens pendentes; filtros; itens atrasados (90 dias); notícias ordenadas; HTML escapado; anos de atuação só com comprovação. **Calculadoras:** transição de 2026 a 2033 e fora da faixa; produtor rural no limite exato, excesso de 20%, mês do excesso, início de atividade, integrado, opção e entradas inválidas. |
| Regras / calendário / validadores (Node 18+) | `node --test tests/js/regras.test.js tests/js/calendario.test.js tests/js/validadores.test.js` | 35 testes: 7.776 combinações setor × regime × perfil × UF × faixa de faturamento; 27 UFs; limites (4,8 mi, 3,6 mi, 78 mi, produtor 3,6 mi); SUDAM/SUDENE/SUDECO/ZFM/ALC; janela de opção do Simples Híbrido; calendário (12 meses × 27 UFs × 3 regimes sem data em dia não útil); .ics; validação de NF-e/CT-e/NFS-e dos modelos de homologação |
| Backend | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/py -q` | Lead, opt-in com double opt-in, contato, consentimento obrigatório, honeypot, campos extras, UF inválida, IP só em HMAC, trilha `audit_hash` que detecta adulteração, limite de requisições (429) |
| Ponta a ponta (Chromium) | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/e2e -q` | 375 / 768 / 1440 px sem rolagem horizontal, menu móvel, CTAs preservados, simulador nas 27 UFs pela interface, fluxo de lead, opt-in, contato, fallback para WhatsApp com API fora do ar, calendário + download .ics, demos e pendências. Páginas novas em 375 e 1440 px (objetivo declarado, logo, WhatsApp, rodapé, menu); Central da Reforma com filtros, fontes e datas; produção sem itens pendentes; anos de atuação só com comprovação; calculadoras pela interface; alertas GO/TO/PA do agro; simulador pré-selecionado por `?setor=` |
| Contrato SQLite × Firestore | `firebase emulators:exec --only firestore --project demo-orgatec "python -m pytest tests/py/test_repositorio_contrato.py"` | As mesmas 6 regras nos dois bancos: protocolo e hash, cadeia íntegra, adulteração detectada, IP só em HMAC, opt-in confirmado uma única vez, contagem e 12 envios simultâneos. Sem o emulador, os casos do Firestore são pulados. |
| Segurança estática | `python -m bandit -q -r backend tools design-system` | Sem achados |

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` só é necessário nesta máquina, onde um plugin global (logfire) quebra na inicialização do pytest.

## 2. Roteiro manual (o que a automação não cobre)

| # | Passo | Resultado esperado |
|---|---|---|
| M1 | Abrir o site em iPhone (Safari) e Android (Chrome) reais | Sem rolagem lateral; menu ☰ abre e fecha; selects nativos funcionam |
| M2 | Clicar em cada botão de WhatsApp (cabeçalho, hero, simulador, contato, artigos) | Abre conversa com +55 62 99294-9161 e mensagem pré-preenchida, **sem** nome, e-mail ou telefone do visitante na URL |
| M3 | Opt-in com e-mail real → abrir o link de confirmação | Depende do disparo de e-mail (pendência 3). Hoje o token fica só no banco; confirmar via `GET /api/optin/confirmar?token=` |
| M4 | Acessar `https://portal.orgatec.io` | Depende do CNAME/ERP (pendência 2) |
| M5 | Importar o .ics no Google Agenda e no Outlook | Eventos de dia inteiro nas datas exibidas |
| M6 | Leitor de tela (NVDA/VoiceOver) no simulador | Rótulos lidos; resultado anunciado (`aria-live`) |
| M7 | Trocar `ambiente` para `'producao'` em `config.js` | Faixa de homologação some |
| M8 | Preencher `capturaXml.ferramenta`, `portal.erp`, `emails.*.ativo` | Selos "pendente de definição" viram nome do fornecedor; e-mails passam a aparecer no contato e no rodapé |

## 3. Não testado

- Navegadores Safari/Firefox e dispositivos reais (somente Chromium headless).
- Envio real de e-mail/WhatsApp e confirmação de opt-in pelo usuário final.
- DNS/CNAME, TLS e MFA do portal (dependem do ERP escolhido).
- Integração real com Sieg/Arquivei/Omie (a demo usa a planilha de homologação).
- Carga/desempenho do backend e comportamento atrás de proxy reverso.
