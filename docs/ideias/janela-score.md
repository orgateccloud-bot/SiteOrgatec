# Score de compliance na Janela Empresarial

- **Situação:** em desenvolvimento
- **Branch:** `ideia/janela-score`
- **Prévia:**

## Problema

A Janela Empresarial (`empresarial/janela.html`) mostra prazos e mudanças da reforma, mas não diz à empresa como ela está nas regras de compliance. O termômetro calcula isso, só que em outra página e sem ligação com a "Minha atividade" da Janela.

## Público

Empresário, comércio e indústria, prestador de serviço, optante do Simples e transportador.

## Proposta

- Cartão "Score de compliance" no alto da Janela, com nota de 0 a 100 no geral e por frente, o selo da faixa (Em dia, Atenção, Risco), as 3 pendências mais pesadas com a fonte e o link para o termômetro.
- "Minha atividade" escolhe o perfil do termômetro (`termometro.perfilDaAtividade`). Sem atividade, vale o perfil "Qualquer empresa".
- Sem resposta, o cartão convida a responder o termômetro já no perfil certo (`termometro.html#perfil-<perfil>`). Na mesma aba, ao voltar, a nota aparece.
- O cálculo é o do termômetro (`termometro.avaliar` e `termometro.nota`): mesma nota nas duas telas. As respostas ficam só na memória da aba (`sessionStorage`). Não há requisição, formulário nem dado na URL.

## Fontes e validação

As regras são as das perguntas do termômetro, cada uma com a fonte de `fontes.js`. A nota é nível de atenção, não parecer nem probabilidade de autuação. Pesos e faixas dependem da revisão técnica (V11). Em produção, sem `REVISAO.status = aprovada`, o cartão diz "em revisão técnica" e não mostra nota.

## Pronto quando

- A nota da Janela é igual à do termômetro para as mesmas respostas, no celular e no desktop.
- Cada atividade mostra só as frentes do seu perfil.
- Nenhuma resposta vai para a rede.
- A Janela segue `noindex` e fora do menu até a decisão R3.
