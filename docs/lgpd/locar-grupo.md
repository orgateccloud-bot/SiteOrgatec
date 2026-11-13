# Painel do grupo LOCAR: rascunho de base legal e tratamento de dados

Situação: **rascunho de 12/11/2026, ainda não adotado.** O painel está pronto no código e **desligado** (`ORGATEC_LOCAR` ausente). Nenhum dado real do grupo foi carregado. Antes de ligar com dados reais, o responsável técnico e o encarregado (C4) revisam este documento.

## O que o painel trata

| Dado | Titular | Observação |
|---|---|---|
| Nome da empresa, tipo, regime tributário, situação (planejada, ativa, em incorporação, extinta) e CNPJ **mascarado** | Pessoa jurídica | CNPJ não é dado pessoal; mesmo assim só a versão mascarada vai para o banco. |
| Nome do produtor rural pessoa física, regime e situação | Sócios do grupo | **Dado pessoal.** Sem CPF, endereço, telefone ou documento: a carga mascara qualquer CPF e o banco só guarda a versão mascarada. A entidade é sempre marcada como sensível. |
| Agenda: título do item, prazo, responsável, situação, fonte legal e referência de evidência (texto ou endereço) | Pessoa jurídica; indireto, sócios | Sem upload de documento, sem valor financeiro e sem honorário. Documentos e guias continuam no portal do cliente. |
| Usuário e papel (`equipe`, `diretor`, `leitura`) | Pessoas que entram no painel | A conta (e-mail e senha) fica no Firebase Authentication. O painel guarda só o identificador do usuário. |
| Trilha de auditoria | Pessoas que entram no painel | Identificador do usuário, ação, tipo e id do recurso e hora. **O conteúdo dos campos não entra na trilha.** |

## Controlador e operador (proposta)

- O grupo é **controlador** dos dados dos próprios sócios. A ORGATEC é **operadora** do painel (contrato de prestação de serviços contábeis, com cláusula de tratamento de dados).
- Quanto aos usuários da própria equipe e à trilha de segurança, a ORGATEC é controladora.

## Base legal (candidatas, a confirmar)

- Art. 7º, V (execução de contrato de serviços contábeis, a pedido do titular), para a agenda de obrigações.
- Art. 7º, II (cumprimento de obrigação legal ou regulatória), quando o item é uma obrigação fiscal ou acessória.
- Art. 7º, IX (legítimo interesse), para a trilha de segurança, com teste de proporcionalidade registrado.
- Consentimento **não** é a base: a relação é contratual.

## Garantias já no código

- Acesso só com login individual e duas declarações próprias na conta (grupo e papel). Sem elas, a API responde 403 sem dizer o motivo. Em produção os cabeçalhos de desenvolvimento são recusados.
- Isolamento por grupo: registro de outro grupo é "não encontrado". Testado.
- Papéis: só a equipe escreve. O diretor e a leitura veem só as entidades do acesso. Entidade sensível aparece só para a equipe e para os titulares listados; a lista de titulares não é mostrada a ninguém além da equipe.
- Trilha encadeada por grupo (cada registro carrega o hash do anterior, com transação no Firestore), verificável pela equipe. Toda escrita e toda leitura de entidade sensível entram nela.
- Carga de dados por arquivo **fora do git**, com simulação por padrão, sem apagar nada e com a saída mostrando só ids e contagens.
- CSP própria da página do painel: só fala com o Firebase Authentication, sem script de terceiros e sem mapa.
- Nenhum dado do grupo no repositório: teste varre os arquivos do módulo atrás de CNPJ e CPF fora da lista fictícia.

## Pendências

1. **Revisão do responsável técnico e do encarregado (C4)** desta base legal e dos papéis.
2. **Prazo de guarda da trilha.** Hoje nada é apagado (a trilha encadeada não pode ter buraco). Propor o prazo, e como eliminar elos antigos sem quebrar a cadeia, no mesmo molde da rotina de `tools/lgpd.py`.
3. **Contrato:** cláusula de operador e divisão de responsabilidades com o grupo.
4. **Aviso aos usuários do painel** (transparência, art. 9º) e atualização da política de privacidade e de `docs/lgpd/registro-operacoes.md` quando o painel for ao ar.
5. **Produtor rural pessoa física:** confirmar por escrito, com cada titular, o tratamento e quem pode ver os dados dele.
6. **Autorização escrita do grupo** para citar o nome (confirmada oralmente em 04/11/2026, falta anexar).

## Fora do escopo da v0.1

Upload de documentos, honorários, acesso dos transportadores e sala de evidências para bancos. Cada um volta a esta análise antes de ser construído.
