# Janela do score da empresa (gráficos e alertas)

- **Situação:** em desenvolvimento
- **Branch:** `ideia/score-empresa`
- **Prévia:**

## Problema

O score de compliance da Janela Empresarial mostra a nota do momento, mas não mostra a evolução nem avisa o que tem prazo ou o que está em risco.

## Público

Empresário, comércio e indústria, prestador de serviço, optante do Simples e transportador.

## Proposta

- Página própria, `empresarial/score.html`, aberta pelo botão "Abrir a janela do score" do cartão da Janela. Fica `noindex` e fora do menu, como a Janela (decisão R3).
- **Medidor da nota geral:** meio arco de 0 a 100, com as marcas de 60 e 85 e a faixa escrita por extenso.
- **Evolução no tempo:** linha com as notas registradas do perfil, com as linhas de 60 e 85, dica em cada ponto e a opção "Ver em tabela". O visitante registra com "Registrar a nota de hoje" e apaga com "Apagar histórico".
- **Alertas:**
  - prazo de pendência chegando, com "faltam N dias", a fonte e o arquivo `.ics` para a agenda;
  - frente em Risco (nota abaixo de 60), com o número de pendências e o link para a regra.
- **Cálculo:** é o do termômetro (`termometro.avaliar`, `nota`, `planoDeAcao`, `FAIXAS`), em `site/assets/js/score-empresa.js`, sem biblioteca e sem CDN.

## Fontes e validação

- **Regras:** as das perguntas do termômetro, cada uma com a fonte de `fontes.js`. Os prazos vêm do campo `prazo` dos itens. A nota é nível de atenção, não parecer nem probabilidade de autuação.
- **Revisão técnica (V11):** pesos e faixas dependem dela. Em produção, sem a revisão, a página diz "em revisão técnica" e não mostra nota.
- **Privacidade:** as respostas ficam na memória da aba. O histórico guarda só as notas, em `localStorage` (`orgatec.score.historico`), e só quando o visitante registra. A chave entrou na seção 3 da política, ainda pendente da aprovação V14. Nada vai para a rede.

## Pronto quando

- A nota é igual no termômetro, na Janela e na janela do score.
- O histórico sobrevive ao recarregar, guarda só as notas e pode ser apagado.
- Os alertas de prazo e de risco aparecem com fonte e link.
- A página funciona sem rolagem lateral no celular e no desktop, nos temas claro e escuro.
