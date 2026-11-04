# Plano de resposta a incidentes de segurança

**Situação:** rascunho de 03/11/2026. **Base:** LGPD, art. 48; Resolução CD/ANPD nº 15/2024.

Incidente é qualquer evento que comprometa dados pessoais: vazamento, invasão, acesso indevido, perda, alteração ou indisponibilidade.

## Prazos

Conte em dias úteis, a partir do momento em que a ORGATEC soube que o incidente **afetou dados pessoais**.

| O quê | Prazo | Se for agente de pequeno porte | Base |
|---|---|---|---|
| Comunicar a ANPD | 3 dias úteis | 6 dias úteis | Art. 6º, *caput* e § 8º |
| Comunicar os titulares | 3 dias úteis | 6 dias úteis | Art. 9º, *caput* e § 6º |
| Complementar a comunicação à ANPD | 20 dias úteis após a comunicação | 40 dias úteis | Art. 6º, §§ 3º e 8º |
| Declarar à ANPD que os titulares foram avisados | 3 dias úteis após o fim do prazo de aviso | Conferir no texto | Art. 9º, § 4º |
| Guardar o registro do incidente | 5 anos, no mínimo | Igual | Art. 10 |

Até a ORGATEC decidir se é agente de pequeno porte, use a coluna dos 3 dias.

## Quem faz o quê

Preencha com nomes e telefones antes de aprovar. Cada papel precisa de um substituto.

| Papel | Quem | Substituto | Telefone |
|---|---|---|---|
| Decide e comunica (encarregado ou representante) | a definir (C4) | a definir | a preencher |
| Avalia a parte técnica | a definir | a definir | a preencher |
| Avalia o risco jurídico e fiscal | Robson Alain Veloso | a definir | a preencher |
| Fala com clientes | a definir | a definir | a preencher |

A comunicação à ANPD é feita pelo encarregado, com comprovante de vínculo, ou por representante com procuração (art. 6º, § 5º). **Deixe esse documento pronto agora:** ele vai junto, dentro do prazo (art. 6º, § 6º).

## Passo a passo

### 1. Registrar a descoberta (na hora)

Anote em [registro-incidentes.md](registro-incidentes.md): data e hora, quem percebeu e o que foi visto. Essa data pode definir o início do prazo. Não apague nem altere nada que sirva de prova.

### 2. Conter (primeiras horas)

| Situação | Primeira ação |
|---|---|
| Conta Google ou Firebase comprometida | Trocar a senha, encerrar as sessões e conferir quem tem acesso no IAM |
| Site alterado por terceiro | Voltar a uma versão anterior no console do Firebase Hosting e trocar as credenciais antes de republicar |
| Trilha quebrada (`python tools/lgpd.py trilha`) | Tratar como possível alteração indevida do banco; copiar o banco antes de mexer |
| Senha ou chave exposta | Trocar a credencial e procurar acessos no período de exposição |
| Portal Athenas ou outro fornecedor | Avisar o fornecedor, pedir por escrito o que foi afetado e guardar a resposta |
| Celular ou computador perdido | Bloquear o aparelho, encerrar as sessões do WhatsApp e do e-mail, trocar as senhas |
| E-mail ou documento enviado à pessoa errada | Pedir a exclusão por escrito e registrar quem recebeu e o quê |
| Ransomware | Desconectar o equipamento da rede sem desligar; não pagar nem negociar sem a direção |

### 3. Avaliar o risco (até o fim do dia seguinte)

Pergunte primeiro: **dados pessoais foram afetados?** Se não, registre o evento e encerre.

Se sim, o incidente é comunicável quando as duas condições abaixo valem juntas (art. 5º):

1. **Pode afetar significativamente interesses e direitos:** impedir um direito ou serviço, causar dano material ou moral, fraude financeira, roubo de identidade, discriminação ou dano à reputação.
2. **Envolve pelo menos um destes dados:**
   - sensíveis (como saúde na folha);
   - de crianças, adolescentes ou idosos;
   - **financeiros;**
   - de autenticação em sistemas;
   - **protegidos por sigilo legal, judicial ou profissional;**
   - em larga escala.

Num escritório contábil, boa parte dos dados é financeira ou está sob sigilo profissional, então o segundo critério costuma ser atendido. A decisão fica no primeiro: o dano possível. Na dúvida, comunique.

Se a ORGATEC for só operadora daquele dado (decisão 3 do [README](README.md)), avise o cliente controlador imediatamente: a comunicação cabe a ele.

### 4. Comunicar

**À ANPD:** pelo [formulário eletrônico da ANPD](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis/comunicacao-de-incidentes-de-seguranca) (art. 6º, § 4º). Reúna (art. 6º, § 2º):

- natureza e categoria dos dados afetados;
- número de titulares afetados, separando crianças, adolescentes e idosos, e o total de titulares daquela atividade;
- medidas de segurança antes e depois do incidente;
- riscos e possíveis impactos aos titulares;
- motivo da demora, se houver;
- medidas para reverter ou reduzir os efeitos;
- data do incidente e data em que a ORGATEC soube;
- dados do encarregado ou do representante;
- identificação do controlador e, se for o caso, declaração de agente de pequeno porte;
- identificação do operador, quando houver;
- descrição do incidente e causa principal, se conhecida.

Se faltar informação, comunique no prazo e complemente depois.

**Aos titulares:** de forma direta e individual (telefone, e-mail, mensagem ou carta), em linguagem simples (art. 9º, § 1º). Se não for possível identificar ou alcançar todos, publique no site e nas redes por, no mínimo, três meses, com fácil visualização (art. 9º, § 3º). Depois, junte a declaração à ANPD.

### 5. Registrar e aprender

Complete o registro (mesmo se não houver comunicação), corrija a causa e revise este plano. Guarde o registro por pelo menos 5 anos.

## Modelo de aviso ao titular

> **Assunto: aviso de incidente de segurança com seus dados**
>
> Olá, [nome]. Em [data do conhecimento], a ORGATEC identificou um incidente de segurança que envolveu seus dados.
>
> **O que aconteceu:** [descrição simples].
> **Quais dados:** [tipos de dados].
> **Possíveis riscos:** [impactos para você].
> **O que já fizemos:** [medidas de proteção e correção].
> **O que recomendamos:** [ex.: trocar a senha, desconfiar de mensagens pedindo pagamento].
>
> [Se o aviso atrasou: motivo da demora.]
>
> Dúvidas: [contato do encarregado ou canal do titular].

Esse modelo cobre o art. 9º. Confira cada item antes de enviar e peça a revisão do responsável técnico.
