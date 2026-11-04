# Operadores e terceiros

**Situação:** rascunho de 03/11/2026. **Base:** LGPD, arts. 39 e 42. O operador trata dados seguindo as instruções do controlador (art. 39), e os dois podem responder por danos (art. 42).

"Contrato" indica o que foi conferido até aqui. Nenhum contrato foi lido nesta revisão.

## Quem trata dados pela ORGATEC

| Fornecedor | Serviço | Dados | Local | Contrato | Ação |
|---|---|---|---|---|---|
| Google (Firebase, Google Cloud) | Hospedagem, API, banco | Formulários e IP de acesso | Banco e API em São Paulo; site em rede global | A conferir | Aceitar os termos de tratamento de dados no console, junto com o faturamento (T1) |
| Athenas Online | Portal do cliente | Dados e documentos de clientes | A confirmar | A conferir | Enviar as perguntas abaixo |
| Provedor de e-mail transacional (T2) | Envio dos alertas | E-mail e conteúdo do alerta | A escolher | Não contratado | Avaliar com a lista de cláusulas |
| Ferramenta de captura de XML (C1) | Documentos fiscais | Notas fiscais | A escolher | Não contratado | Avaliar com a lista de cláusulas |
| Meta (WhatsApp Business) | Atendimento | Mensagens e documentos | Fora do Brasil | Termos da plataforma | Definir o que pode ser enviado por ali |

## Quem não deve receber dados pessoais

| Fornecedor | Uso | Regra |
|---|---|---|
| Hostinger | Domínio e DNS | Não recebe dados de titulares hoje. Revisar se virar provedor de e-mail |
| GitHub | Código do site | Nunca enviar `.env`, bancos ou dados reais |
| Ferramentas de IA | Desenvolvimento | Anonimizar CPF, CNPJ e nomes antes de enviar |

## Fontes externas: não são operadores

NASA (imagens de satélite) e CEPEA (cotações) recebem o IP do navegador do visitante, sem dado enviado pela ORGATEC. MET Norway e os sites de notícias são consultados pelo escritório, sem dados de visitantes. A política de privacidade informa isso.

## Cláusulas para qualquer contrato novo

- [ ] Trata dados só conforme as instruções da ORGATEC e para o serviço contratado.
- [ ] Mantém medidas de segurança adequadas, com descrição das principais.
- [ ] Avisa incidentes sem demora, a tempo do prazo de 3 dias úteis da ORGATEC, com os dados necessários à comunicação.
- [ ] Informa suboperadores e pede aceite antes de trocar.
- [ ] Informa onde os dados ficam e o enquadramento de transferências internacionais (art. 33).
- [ ] Ajuda a atender pedidos de titulares.
- [ ] Devolve ou elimina os dados ao fim do contrato.
- [ ] Permite comprovar o cumprimento dessas regras.

## Perguntas para a Athenas

Texto pronto para enviar. As respostas resolvem os selos do portal na política de privacidade (V14) e as pendências C2 e T5.

> Olá. Para atualizar nossa política de privacidade e o endereço do portal, precisamos confirmar sobre a instância orgatec.athenas.online:
>
> 1. O portal oferece autenticação em dois fatores? É obrigatória ou opcional? Como ativar?
> 2. O sistema registra os acessos (data, hora, IP e ação)? Por quanto tempo? A ORGATEC consegue consultar?
> 3. Em qual país e provedor os dados ficam hospedados? Há cópias fora do Brasil?
> 4. Há backup? Com que frequência e por quanto tempo?
> 5. Quais empresas subcontratadas têm acesso aos dados?
> 6. Em caso de incidente de segurança, em quanto tempo e por qual canal vocês avisam a ORGATEC?
> 7. O contrato tem cláusula de proteção de dados (LGPD)? Podem enviar a versão vigente?
> 8. Como os dados são devolvidos ou apagados ao fim do contrato?
> 9. Vocês aceitam domínio próprio, portal.orgatec.io? Se sim, para qual endereço apontamos o CNAME, e vocês emitem o certificado HTTPS?
