# Monitoramento de veículos e motoristas (Central de Viagem): rascunho de base legal

Situação: **adotada como proposta de trabalho pelo escritório em 09/11/2026 ("sim" à base legal sugerida).** Continua sem parecer jurídico: antes de qualquer cliente real usar o módulo, o responsável técnico e o encarregado (DPO) precisam revisar o teste de proporcionalidade e o aviso ao motorista (itens 1 e 3 das pendências abaixo). Nada aqui é parecer jurídico.

**Adotado até a revisão:** base legal principal, execução de contrato (art. 7º, V) com legítimo interesse (art. 7º, IX) de apoio e teste de proporcionalidade por escrito; consentimento não é a base. Controladora: a transportadora cliente; operadora: a ORGATEC. Prazo de guarda das leituras: 30 dias.

## O que o módulo trata

- **Posição, velocidade, ignição, temperatura e combustível** enviados por sensores do veículo. A posição de um caminhão, ligada a uma viagem e a um motorista, é dado pessoal do motorista.
- **Motorista:** só nome e vínculo ao usuário. Sem CPF, CNH, telefone ou endereço.
- **Coordenadas em log:** nenhuma. O log registra só o tipo do erro.
- **APIs estrangeiras:** só coordenadas de origem e destino (nunca nome nem placa), e apenas quando os provedores reais existirem.

## Controlador e operador (proposta)

- A transportadora cliente é a **controladora** dos dados dos próprios motoristas. A ORGATEC é **operadora** do módulo. Isso muda o contrato e o registro de operações (`docs/lgpd/registro-operacoes.md`).

## Base legal (candidatas, a confirmar)

- LGPD art. 7º, V (execução de contrato), se o monitoramento estiver previsto no contrato de trabalho ou de transporte.
- LGPD art. 7º, IX (legítimo interesse), com teste de proporcionalidade (finalidade, necessidade e balanceamento), registrado por escrito.
- Consentimento **não** é recomendado como base única: a relação de trabalho torna o consentimento frágil.

## Garantias já no código

- Acesso restrito à transportadora (isolamento por `transportadora_id`; outro cliente recebe 404).
- Motorista só vê as próprias viagens. O papel `leitura` não escreve.
- Prazo de guarda das leituras: **30 dias (proposta)**, em `backend/retencao.py` (`telemetria_dias`, variável `ORGATEC_RETENCAO_TELEMETRIA_DIAS`). A eliminação automática por `tools/lgpd.py` só passa a valer quando houver persistência (hoje os dados ficam em memória e somem ao reiniciar).
- Credencial de sensor exibida uma vez; assinatura HMAC com janela de relógio de 5 minutos; 403 sem dizer o motivo.

## Pendências

1. Escolher e registrar a base legal e o teste de proporcionalidade.
2. Definir o prazo de guarda definitivo.
3. Aviso ao motorista (transparência, art. 9º): o que é coletado, para quê e por quanto tempo.
4. Atualizar `docs/lgpd/registro-operacoes.md` e a política de privacidade quando o módulo for ao ar.
