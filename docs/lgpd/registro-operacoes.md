# Registro das operações de tratamento (LGPD, art. 37)

**Situação:** rascunho de 03/11/2026. O bloco A foi conferido no código do site. O bloco B foi montado com o que o site diz sobre o escritório e precisa ser preenchido pela equipe.

**Controlador:** ORGATEC, CNPJ 13.155.211/0001-45, Av. Ministro Alfredo Nasser, nº 727, Centro, Formoso-GO.
**Encarregado:** a definir (C4).

## A. Site orgatec.io (conferido no código)

A API dos formulários ainda não está publicada (T1). Hoje esses registros não existem: o visitante é levado ao WhatsApp.

| Operação | Titulares | Dados | Finalidade | Base legal | Guarda | Onde fica | Quem recebe |
|---|---|---|---|---|---|---|---|
| Pedido de análise no simulador (lead) | Interessados | Nome, empresa (opcional), e-mail e/ou WhatsApp, setor, regime, perfil, UF, faturamento, alertas | Retorno sobre o diagnóstico | Art. 7º, I e V | 24 meses (V6) | Firestore, São Paulo | Google (operador) |
| Alertas do Calendário Fiscal (opt-in) | Interessados | E-mail e/ou WhatsApp, UFs, esferas | Enviar alertas | Art. 7º, I, com double opt-in | Não confirmado: 30 dias (V6). Confirmado: até cancelar | Firestore, São Paulo | Google; provedor de e-mail (T2) |
| Contato | Interessados, clientes, titulares | Nome, e-mail e/ou WhatsApp, assunto, mensagem | Responder | Art. 7º, V, ou II (direitos do titular) | 24 meses (V6) | Firestore, São Paulo | Google |
| Registro técnico dos formulários | Quem envia | IP em HMAC, contatos em HMAC, versão da política, finalidade aceita | Segurança, prevenção de abuso, prova do consentimento | Art. 7º, IX | Junto com o registro | Firestore, São Paulo | Google |
| Acesso às páginas | Visitantes | IP, navegador, página | Entregar o site | A definir pelo responsável técnico | Definida pela hospedagem; a ajustar (V6, V14) | Firebase Hosting (rede global) | Google; NASA e CEPEA, nas páginas que usam |
| Preferências no navegador | Visitantes | Cores, animação, região da Janela de Campo, respostas do termômetro | Funcionamento | Não saem do navegador | Até o visitante apagar ou fechar a aba | Navegador | Ninguém |

**Eliminação:** `python tools/lgpd.py retencao --confirmar` apaga os dados vencidos e mantém só protocolo, tipo, datas e hashes. A rotina ainda precisa ser agendada com a API (T1).

**Medidas de segurança:** HTTPS, CSP restrita, banco fechado ao navegador, IP e contatos pseudonimizados, tokens guardados só como hash, trilha `audit_hash`.

## B. Atividades do escritório (a preencher)

"Papel" é controlador ou operador. Cada linha precisa da confirmação do responsável técnico (decisão 3 do [README](README.md)).

| Operação | Titulares | Dados (exemplos) | Papel | Base legal (proposta) | Guarda | Sistema | Compartilha com |
|---|---|---|---|---|---|---|---|
| Cadastro de clientes | Sócios e representantes | Nome, CPF, contato, documentos | a preencher | Art. 7º, V e II | a preencher | a preencher | a preencher |
| Escrituração e obrigações fiscais | Clientes, sócios, fornecedores pessoa física | Notas, valores, CPF | a preencher | Art. 7º, II e V | Prazo da legislação tributária e societária | a preencher | Receita Federal, Sefaz |
| Folha de pagamento e eSocial | Empregados dos clientes e dependentes | CPF, salário, afastamentos, saúde ocupacional | a preencher | Art. 7º, II; dados de saúde: art. 11 | Prazo da legislação trabalhista e previdenciária | a preencher | eSocial, FGTS |
| Portal do cliente | Usuários das empresas clientes | Login, documentos | a preencher | Art. 7º, V e II | a preencher | Athenas Online | Athenas (operador) |
| Prevenção à lavagem de dinheiro | Contratantes e beneficiários | Dados cadastrais, operações | a preencher | Art. 7º, II (Res. CFC nº 1.721/2024) | a preencher | a preencher | COAF, quando cabível |
| Atendimento por WhatsApp e e-mail | Clientes e interessados | Mensagens e documentos enviados | a preencher | Art. 7º, V | a preencher | WhatsApp Business (C5) | Meta |
| Equipe do escritório | Empregados e colaboradores | Dados de contrato e folha | Controlador | Art. 7º, II e V | a preencher | a preencher | a preencher |
| Fornecedores | Pessoas físicas contratadas | Nome, CPF, pagamento | Controlador | Art. 7º, V e II | a preencher | a preencher | a preencher |

**Atenção na folha:** dados de saúde são sensíveis. Incidentes com esses dados, com dados financeiros ou com dados sob sigilo profissional entram nos critérios de risco do [plano de incidentes](plano-incidentes.md).

## C. Sistemas próprios fora do site

OrgConc, OrgAudi e Mini tratam dados de clientes e têm documentação própria. Antes de ligar qualquer um ao site (T12), acrescente uma linha aqui.
