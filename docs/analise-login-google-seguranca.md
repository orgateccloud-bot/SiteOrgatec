# Análise: login com Google no Firebase e segurança em todos os níveis

Conferido em 02/11/2026 no projeto `orgatec-site` (conta orgatec.cloud@gmail.com), com leitura apenas: nada foi ativado nem alterado.

## 1. Situação de hoje

| Item | Estado |
|---|---|
| Firebase Authentication | **Nunca foi iniciado.** A API responde `CONFIGURATION_NOT_FOUND`. Nenhum provedor (Google, e-mail, telefone) está ligado e não há usuários. |
| Apps do Firebase | 1 app web ("ORGATEC Site Institucional"). |
| Hosting | orgatec.io e orgatec-site.web.app com CSP `script-src 'self'`, HSTS, `X-Frame-Options: DENY`, `nosniff`, `Permissions-Policy` e `noindex`. |
| Firestore | Em southamerica-east1, com regras que negam todo acesso pelo navegador. Só a API grava, com conta de serviço. |
| API (Cloud Run) | Pronta e testada, mas **não publicada**: depende do faturamento (Blaze, T1). Já tem limite por IP, IP em HMAC, CORS restrito, honeypot e trilha `audit_hash` encadeada. |
| Portal do cliente | Athenas Online (`orgatec.athenas.online`). O login dos clientes é do Athenas, não do site. |
| Área do cliente própria (D2) | Em aberto: portal do ERP ou área própria com login. |

Conclusão: o site não guarda conta de ninguém, e isso é uma vantagem de segurança. Um login novo só deve entrar onde trouxer ganho claro.

## 2. Onde o login com Google faz sentido

| Uso | Quem entra | Recomendação |
|---|---|---|
| **Painel interno da equipe** | Warley, Robson e equipe | **Sim, primeiro.** Substitui trabalho manual: aprovar a revisão técnica dos itens da reforma (V1, hoje feita editando arquivo); ler leads, contatos e opt-ins (hoje só pelo console do Google); acompanhar as pendências. Poucos usuários, todos conhecidos. |
| **Área do cliente própria** (D2) | Clientes | **Não agora.** O Athenas já é o portal. Uma área própria obrigaria o site a guardar documentos de clientes, com base legal, retenção, encarregado e resposta a incidentes (LGPD). Só faz sentido se a D2 decidir por ela. |
| **Conta de visitante** (salvar simulações, alertas) | Público | **Não.** O ganho é pequeno, e cada conta vira dado pessoal guardado. O opt-in por e-mail do calendário já atende. |

## 3. Como seria o painel interno

1. **Página própria.** O painel fica em `orgatec.io/painel/` (ou em `painel.orgatec.io`), com CSP só dela no `firebase.json`. O site público continua com `script-src 'self'`, sem nenhum script de terceiros.
2. **SDK do Firebase servido pelo próprio site.** O SDK é empacotado (npm + esbuild) num arquivo em `assets/`, sem CDN.
   - **Script do Google:** o fluxo de popup do Google carrega um script de `apis.google.com`. A CSP da página do painel precisa liberar esse endereço (`script-src`), além de `connect-src https://identitytoolkit.googleapis.com https://securetoken.googleapis.com`. A lista exata deve ser conferida no primeiro teste.
   - **Popup:** a página precisa de `Cross-Origin-Opener-Policy: same-origin-allow-popups`.
3. **`authDomain` = `orgatec.io`.** O Firebase Hosting já atende `/__/auth/handler` no domínio próprio. É o que o Google recomenda para o login funcionar em navegadores que bloqueiam armazenamento de terceiros (Safari, Firefox e Chrome com proteção).
4. **Só convidados entram.**
   - A criação de contas pelo navegador fica desligada (Authentication → Configurações → Ações do usuário; conferir a opção no console).
   - As contas da equipe são criadas pela API com o SDK de servidor.
   - O papel de cada pessoa (`revisor`, `admin`) vai em *custom claims*.
5. **A API confere tudo.** Cada chamada do painel leva o token. A FastAPI valida com `firebase_admin.auth.verify_id_token(token, check_revoked=True)` e confere o papel antes de responder. O Firestore continua fechado para o navegador.

## 4. Segurança por nível

**Situação:** ✅ já existe · ➕ adicionar sem custo · 💳 depende do faturamento (Blaze) ou de upgrade.

### 4.1 Contas e acesso ao Google Cloud

| Medida | Situação | Por quê |
|---|---|---|
| Verificação em duas etapas (de preferência chave de acesso/passkey) na conta orgatec.cloud@gmail.com | ➕ | É a conta dona do projeto, do Hosting e do DNS de produção. Quem entra nela publica qualquer coisa em orgatec.io. |
| Warley e Robson como proprietários individuais no IAM, cada um com a própria conta Google e 2 etapas, em vez de senha compartilhada | ➕ | Quem fez o quê fica rastreável, e a saída de uma pessoa não exige trocar a senha de todos. |
| Alertas de orçamento no faturamento | 💳 | Junto com a abertura do Blaze (T1): avisam se o uso disparar, por ataque ou erro. |
| Publicação feita a partir de uma cópia limpa (git + build), e não da pasta compartilhada | ➕ | Hoje `firebase deploy` leva o que estiver na pasta, inclusive trabalho pela metade de outra sessão. A pasta nem é um repositório git. |

### 4.2 Autenticação (login)

| Medida | Situação | Por quê |
|---|---|---|
| Ligar só o provedor Google | ➕ | Sem senha guardada pelo site, não há senha para vazar ou para tentar adivinhar. |
| Domínios autorizados mínimos: orgatec.io e o domínio do painel; `localhost` só em desenvolvimento | ➕ | Impede usar o projeto em outros sites. |
| Criação de contas desligada e lista de permitidos | ➕ | Uma conta Google qualquer não consegue entrar. |
| Revogar sessões na saída de alguém (`revoke_refresh_tokens`) e checar a revogação na API | ➕ | O token dura 1 hora. Com a checagem, o acesso cai na hora. |
| Exigir 2 etapas nas contas Google da equipe | ➕ | Com login pelo Google, a segunda etapa é a do Google. Com Google Workspace no domínio orgatec.io, isso pode ser **obrigatório por política**, e a API pode aceitar só e-mails `@orgatec.io` (campo `hd` do token). O Workspace também resolve os e-mails `contato@` e `dpo@` (C3, T2). |
| *Blocking functions* (barrar o login fora da lista, registrar cada entrada) | 💳 | Exigem o upgrade para Identity Platform e uma função no Cloud Run. |
| MFA dentro do Firebase (TOTP ou SMS) | 💳 | Também exige o upgrade. Para login com Google, as 2 etapas do próprio Google costumam bastar. |

### 4.3 Aplicação (navegador)

| Medida | Situação | Por quê |
|---|---|---|
| CSP restrita, HSTS, `X-Frame-Options`, `nosniff`, `Permissions-Policy` | ✅ | Já publicados no `firebase.json`. |
| CSP separada para o painel e COOP para o popup | ➕ | O site público não precisa abrir nada para o login existir. |
| **App Check** com reCAPTCHA Enterprise nos formulários e no login | 💳 | Confirma que o pedido vem do site verdadeiro, e não de um robô. Soma-se ao honeypot e ao limite por IP. A FastAPI valida o cabeçalho `X-Firebase-AppCheck`. |
| HSTS com `preload` | ➕ | Depois que `www.orgatec.io` tiver certificado (pendência aberta). Força HTTPS desde a primeira visita. |

### 4.4 API (Cloud Run)

| Medida | Situação | Por quê |
|---|---|---|
| Limite por IP, HMAC do IP, CORS restrito, validação Pydantic, honeypot | ✅ | Já no código (`backend/app.py`). |
| Segredo do HMAC no Secret Manager, não em variável solta | 💳 | O segredo não aparece no console nem nos logs de publicação. |
| Conta de serviço própria com permissão mínima (só `roles/datastore.user`) | 💳 | Se a API for invadida, o estrago fica limitado ao banco dos formulários. |
| Limite por IP compartilhado entre instâncias, ou número máximo de instâncias baixo | 💳 | O limite atual fica na memória de cada instância. Com várias instâncias, ele se multiplica. |
| Validação do token do painel e do App Check | 💳 | Detalhado nas seções 3 e 4.3. |

### 4.5 Dados (Firestore)

| Medida | Situação | Por quê |
|---|---|---|
| Regras que negam o navegador | ✅ | `firestore.rules`. |
| Trilha `audit_hash` encadeada | ✅ | Mostra se algum registro foi alterado ou apagado. |
| **Política de TTL** (apagar leads e contatos após o prazo definido) | ➕ | Resolve a pendência V6, que hoje não tem retenção nenhuma, e cumpre a minimização da LGPD (art. 15 e 16). O prazo é decisão da ORGATEC. |
| Backups agendados ou recuperação a um ponto no tempo (PITR) | 💳 | Permitem voltar o banco depois de um erro ou ataque. |
| Cópia diária da trilha num bucket com retenção travada (*Bucket Lock*) | 💳 | Ninguém, nem um administrador, consegue apagar a trilha antes do prazo: é a cadeia de custódia. |

### 4.6 Registro e monitoramento

| Medida | Situação | Por quê |
|---|---|---|
| Cloud Audit Logs de leitura de dados para Firestore e Identity Toolkit | ➕ | Mostram quem leu o quê, inclusive pelo console. |
| Alertas sobre os logs: muitos 429, conta nova criada, erro 5xx em série | 💳 | A ORGATEC fica sabendo do ataque na hora, e não depois. |
| Registro de atividade dos usuários (Identity Platform) | 💳 | Exige o upgrade. |

### 4.7 Domínio e e-mail (Hostinger)

| Medida | Situação | Por quê |
|---|---|---|
| 2 etapas e bloqueio de transferência (*registrar lock*) na conta da Hostinger | ➕ | Quem controla o DNS controla o site, o e-mail e o login. |
| DNSSEC em orgatec.io | ➕ | Impede respostas de DNS falsificadas. |
| Registro CAA limitando quem emite certificado | ➕ | Conferir antes quais autoridades o Firebase Hosting usa, para não bloquear a renovação. |
| SPF, DKIM e DMARC | ➕ | Já previstos em T2. Sem eles, qualquer um envia e-mail se passando pela ORGATEC. Hoje não há MX nem DMARC. |

### 4.8 Desenvolvimento

| Medida | Situação | Por quê |
|---|---|---|
| Bandit, testes e CSP testada em todas as páginas | ✅ | Rodam antes de cada publicação. |
| Repositório git privado, com histórico e revisão | ➕ | Hoje não há histórico nem como voltar uma publicação errada. |
| `pip-audit` e `npm audit` nas dependências | ➕ | Pegam bibliotecas com falha conhecida. |

### 4.9 LGPD

| Medida | Situação | Por quê |
|---|---|---|
| Política de privacidade cobrindo o login do painel (dados tratados, base legal, prazo dos registros) | ➕ | O registro de login também é dado pessoal. |
| Prazo de retenção definido (V6) e canal do encarregado ativo (`dpo@`, C3) | ➕ | Já são pendências. O painel e o TTL dependem delas. |

## 5. Ordem sugerida

1. **Agora, sem custo:**
   - 2 etapas nas contas Google e na Hostinger;
   - Warley e Robson no IAM;
   - bloqueio de transferência e DNSSEC;
   - git para o projeto;
   - decidir o prazo de retenção (V6).
2. **Com o Blaze (T1):**
   - API no Cloud Run com Secret Manager e conta de serviço mínima;
   - App Check nos formulários;
   - TTL;
   - backups;
   - alertas de orçamento e de logs.
3. **Painel interno com login Google:**
   - iniciar o Authentication só com Google;
   - criação de contas desligada;
   - papéis em *custom claims*;
   - revisão técnica (V1) e leitura de leads no painel;
   - upgrade para Identity Platform só se precisarem de *blocking functions* ou de log de atividade.
4. **Área do cliente própria:** só se a D2 decidir por ela, com plano de LGPD próprio.

## 6. Decisões da ORGATEC

1. Fazer o painel interno com login Google?
2. Contratar Google Workspace para o domínio orgatec.io? Ele permite exigir 2 etapas e aceitar só `@orgatec.io`, e já resolve `contato@` e `dpo@`.
3. Quem é administrador e quem é revisor no painel?
4. Prazo de guarda de leads, contatos e opt-ins (V6).

## Fontes

- Firebase Authentication: https://firebase.google.com/docs/auth
- Login com redirecionamento em navegadores que bloqueiam armazenamento de terceiros: https://firebase.google.com/docs/auth/web/redirect-best-practices
- Novidades do Firebase Auth (upgrade para Identity Platform: MFA, *blocking functions*, auditoria): https://goo.gle/3BCrqoY
- Preços e limites: conferir na página de preços do Firebase e do Identity Platform antes do upgrade. Os valores de terceiros consultados divergem entre si.
