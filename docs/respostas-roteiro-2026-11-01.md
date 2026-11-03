# Roteiro até T9: respostas de 01/11/2026

Registro das respostas da direção e das respostas do desenvolvimento, conferidas no código em 01/11/2026. As decisões também estão nas pendências do painel de testes (`site/assets/js/homologacao.js`).

## Direção (respondido por Warley Veloso em 01/11/2026)

| Pergunta | Resposta | Onde ficou registrado |
|---|---|---|
| ME/EPP e tratamento em larga escala | Não avaliar agora | C4: o canal do encarregado (dpo@) continua exigido para a produção |
| Quem abre o faturamento do Google Cloud | Warley Moreira Veloso ou Robson Alain Veloso, com cartão de crédito | T1 |
| Lançar sem área do cliente e sem newsletter? | Não: lançamento completo | D2 e T2 passam a ser obrigatórias para a produção |
| Quem administra o DNS de orgatec.io | Hostinger | T5 e a nova T13 |
| O que é "validar o WhatsApp" (C5) | Migrar para o WhatsApp Business | C5 |
| Quem aprova os textos da abertura e da vitrine | Warley e Robson | D7 |

## Desenvolvimento (respondido pelo desenvolvimento, com base no código atual)

### 1. O domínio principal já aponta para o Hosting, com certificado?
- **Resposta:** não.
- **Situação:** o site responde só em `https://orgatec-site.web.app`, e `orgatec.io` ainda não aponta para o Firebase Hosting.
- **Pendência:** T13, com o caminho na seção "DNS na Hostinger" abaixo.

### 2. Qual provedor de e-mail transacional (T2), com SPF, DKIM e DMARC?
- **Resposta:** ainda não há provedor escolhido. Hoje o `/api/optin` só grava o token de confirmação no banco.
- **Decisão da ORGATEC:** escolher o provedor. Opções comuns: Amazon SES, SendGrid, Mailgun, Brevo e Postmark.
- **Requisitos para qualquer um deles:**
  - **Envio por API**, com a chave guardada no Secret Manager do Google Cloud, nunca no código.
  - **Domínio autenticado na Hostinger:**
    - SPF: registro TXT com o `include` que o provedor indicar;
    - DKIM: os registros CNAME ou TXT que o provedor gerar;
    - DMARC: registro TXT em `_dmarc.orgatec.io`. Comece com `p=none` e endureça depois de conferir os relatórios.
  - **Remetente:** um endereço do próprio domínio, por exemplo `alertas@orgatec.io`.
  - **SPF único:** se o domínio já tiver um SPF por causa do e-mail institucional (C3), o registro precisa ser um só, juntando os dois `include`. Dois registros SPF invalidam a autenticação.

### 3. Dados não validados já ficam ocultos no calendário e no simulador?
- **Resposta:** não.
- **Calendário e simulador:** mostram datas e alertas não confirmados com o selo "pendente de validação", em qualquer ambiente (`calendario.js` e `regras.js`).
- **Itens da reforma:** só eles ficam ocultos em produção quando não têm revisão aprovada.
- **Depende do responsável técnico:** se ele preferir ocultar as UFs não confirmadas (pergunta 4 do bloco dele, pendências V3 e V4), o desenvolvimento acrescenta esse filtro para produção.

### 4. Quanto tempo e quanto tráfego a T11 precisa para fixar `ORGATEC_IP_POSICAO`?
- **Resposta:** não depende de tráfego. Bastam de 3 a 5 envios de teste, feitos de redes com IP conhecido (por exemplo, a internet do escritório e um celular no 4G), logo depois de publicar a API.
- **Tempo:** cerca de 30 minutos.
- **Como fazer:** ler as linhas `diagnostico-ip` nos logs do Cloud Run, gravar a posição em `ORGATEC_IP_POSICAO` e desligar `ORGATEC_DIAGNOSTICO_IP`.
- **Pré-requisito:** a API no ar (T1, que depende do faturamento).

### 5. A página de captura de XML (C1) funciona sem ferramenta definida?
- **Resposta:** sim.
- **Situação:** a demonstração da área do cliente (`cliente/index.html`) roda com os modelos fictícios de homologação e mostra o selo "Ferramenta de captura: pendente de definição".
- **Ao definir a ferramenta:** basta preencher `capturaXml.ferramenta` em `config.js`. Nada captura documentos de verdade até a integração com a ferramenta escolhida.

### 6. Os logs do Cloud Run e a trilha `audit_hash` têm prazo de retenção, compatível com V6?
- **Resposta:** não.
- **Registros e trilha:** os do Firestore e do SQLite, com a trilha `audit_hash`, não têm exclusão automática.
- **Logs:** os do Cloud Run vão seguir a retenção do bucket de logs do projeto, que precisa ser ajustada.
- **Proposta, depois que V6 aprovar os prazos:**
  - rotina que apaga leads com mais de 24 meses e opt-ins não confirmados com mais de 30 dias;
  - retenção dos logs ajustada ao menor prazo necessário;
  - nos logs, o IP já aparece mascarado.
- **Ponto de atenção:** apagar registros quebra a cadeia `audit_hash` se for feito apagando linhas. A exclusão precisa preservar o hash, por exemplo substituindo os dados pessoais por um marcador e mantendo o registro encadeado. Isso deve ser decidido junto com V6.

## Caminhos práticos

### DNS na Hostinger: ligar orgatec.io ao Firebase Hosting (T13)
1. **Console do Firebase.** No projeto `orgatec-site`, abra Hosting e escolha "Adicionar domínio personalizado". Informe `orgatec.io`; depois repita com `www.orgatec.io` e configure o redirecionamento para `orgatec.io`.
2. **Copiar os registros.** O console mostra um registro TXT, para provar que o domínio é seu, e os registros A de destino. Use exatamente os valores mostrados ali; eles não são fixos.
3. **Hostinger.** Entre no hPanel → Domínios → `orgatec.io` → DNS / Nameservers → Gerenciar registros DNS:
   - inclua o TXT e os registros A indicados pelo Firebase;
   - apague os registros A e AAAA antigos de `@` e de `www`, como os de estacionamento da própria Hostinger. Registros sobrando impedem a emissão do certificado;
   - não mexa nos registros MX nem nos TXT de e-mail.
4. **Certificado.** Depois da propagação, o Firebase emite o certificado HTTPS sozinho. O console mostra o andamento; pode levar algumas horas.
5. **Depois disso, no código:**
   - acrescentar `https://orgatec.io` em `ORGATEC_ORIGENS` (API);
   - rodar `python tools/preparar_firebase.py --projeto orgatec-site --cloud-run orgatec-api`;
   - conferir os links canônicos, que já usam `https://orgatec.io/`.
   - Fazer isso só quando a produção for aprovada (T9). Até lá, o domínio próprio exibiria o site em homologação. Ele continua fora do Google, mas aberto ao público.

### portal.orgatec.io (T5)
- **ERP definido (01/11/2026):** Athenas Online. A instância da ORGATEC já existe em `https://orgatec.athenas.online/Usuarios/login`, e os links do portal no site apontam para ela.
- **CNAME:** é criado na mesma tela da Hostinger (tipo CNAME, nome `portal`), com o alvo que a Athenas informar. Antes, confirmar com a Athenas se ela aceita domínio próprio e emite o certificado de `portal.orgatec.io`; sem certificado, o navegador mostra erro de segurança.
- **Depois do CNAME:** trocar `portal.url` em `site/assets/js/config.js` e `PORTAL_URL` em `tools/layout.py` para `https://portal.orgatec.io`.

### Alternativa: mover o DNS para fora da Hostinger
- **É possível**, apontando os nameservers para o Cloud DNS ou outro provedor.
- **Não é necessário:** o Firebase funciona com o DNS na Hostinger, e manter tudo lá evita migrar os registros de e-mail.

### Migrar o WhatsApp para o WhatsApp Business (C5)
1. **Backup das conversas.** No celular do número +55 62 99294-9161, faça backup das conversas pelo WhatsApp atual.
2. **Instalar e migrar.** Instale o aplicativo WhatsApp Business e informe o mesmo número. O aplicativo oferece migrar a conta e as conversas.
3. **Perfil comercial:**
   - nome ORGATEC e a categoria mais próxima de contabilidade que o aplicativo oferecer;
   - endereço da sede (Av. Ministro Alfredo Nasser, 727, Centro, Formoso-GO);
   - horário de atendimento;
   - site, quando `orgatec.io` estiver no ar.
4. **Mensagens automáticas:** configure saudação e ausência. O site já envia uma mensagem pronta ("Olá! Quero agendar um diagnóstico..."), sem dados pessoais, então a saudação pode orientar o próximo passo.
5. **Confirmar no site.** Com a migração feita, marque `whatsapp.validado: true` em `site/assets/js/config.js`. A pendência C5 fecha sozinha no painel.
6. **Links do site:** não mudam. Os links `wa.me` funcionam igual com o WhatsApp Business.
7. **Se um dia precisar de atendimento por vários atendentes ou integrações,** isso é outro produto, a WhatsApp Business Platform (API da Meta). Não é necessário para o lançamento.

### Faturamento do Google Cloud (T1)
1. **Abrir a conta de faturamento.** Warley ou Robson entra no console do Google Cloud com a conta `orgatec.cloud@gmail.com` e acessa Faturamento → Criar conta de faturamento, com o cartão de crédito. Pagamento e cartão ficam sempre com vocês; o desenvolvimento não faz essa etapa.
2. **Vincular ao projeto.** Ligue a conta de faturamento ao projeto `orgatec-site`. Isso passa o projeto para o plano Blaze.
3. **Alerta de orçamento.** Recomendo criar um em Faturamento → Orçamentos e alertas, com um valor baixo, para receber aviso de qualquer gasto fora do esperado.
4. **Avisar o desenvolvimento.** A partir daí, o desenvolvimento publica a API (passos 4 a 8 de `docs/publicacao.md`) e calibra o IP (T11).

## Ainda sem resposta: responsável técnico (Robson Alain Veloso, CRC)
1. **Ritmo de revisão:** quantos itens de V1 consegue revisar por semana?
2. **Publicação parcial:** aceita aprovar item a item, com publicação parcial? O site já funciona assim: em produção, aparece só o que tem revisão aprovada.
3. **V6 com quem cuida de LGPD:** concorda em passar os prazos de retenção para quem cuida de LGPD? A resposta afeta o item 6 acima.
4. **UFs não confirmadas:** prefere ocultá-las (V3, V4) a esperar a confirmação? A resposta afeta o item 3 acima.
