# Modelo C: a ferramenta que vira proposta

- **Situação:** em desenvolvimento
- **Branch:** `ideia/modelo-c`
- **Prévia:** `python tools/previa.py` na pasta `SiteOrgatec-modelo-c`

## Problema

O site já abre com o simulador e entrega um relatório preliminar, mas o passo seguinte não fecha: o diagnóstico não tem
escopo, prazo nem preço, o formulário do resultado não qualifica o contato e o menu tem 7 grupos. O estudo de 03/11/2026
(quatro modelos de site das grandes auditorias) apontou esta como a maior lacuna comercial.

## Público

Empresário, produtor rural e transportador que simulou o impacto da reforma e quer saber o que contratar.

## Proposta

- **Menu com 6 grupos:** Simular · Diagnóstico · Reforma · Setores · Compliance · Serviços. Empresarial se dissolve em
  Setores (com a Central de Viagem, ao lado de Transporte); o score vai para Compliance. Nenhum endereço atual muda.
- **Botão "Solicitar diagnóstico"** no cabeçalho (a partir de 1280 px) e na barra do celular, no lugar do WhatsApp, que
  continua no cabeçalho.
- **Página nova `diagnostico-reforma.html`:** o que se levanta, o que se entrega, prazo e investimento.
- **Página nova `proposta/index.html`:** o mesmo pedido, para quem chega pelo menu ou pela página do diagnóstico. O
  cenário vem da simulação feita na aba (`sessionStorage`, nunca pela URL) ou é escolhido na página.
- **Formulário do resultado do simulador:** fica onde está e vira o pedido de proposta do diagnóstico, com porte e
  origem (opcionais). Dois caminhos: formulário (`/api/leads`) e WhatsApp com a mensagem pronta.
- **Faixa "Comece pelo diagnóstico":** mantém os dois botões e ganha o link para a página do diagnóstico.
- **API:** `LeadIn` aceita `porte` e `origem`. O registro é gravado como JSON; não há migração de banco.
- **Política de privacidade:** o item do simulador passa a citar porte e origem, e a lista do navegador ganha `orgatec.cenario`.

## Decisões da direção (12/11/2026)

| Ponto | Decisão |
|---|---|
| Prazo do diagnóstico | 5 dias |
| Preço | A ser estabelecido; a página diz que o valor segue na proposta |
| Formulário ou WhatsApp | Os dois |
| Compliance | Grupo próprio no menu |
| Formulário do simulador | Unificado com o pedido de proposta |

## Fontes e validação

- Não há regra, alíquota nem prazo legal novo nesta ideia.
- **Responsável técnico precisa aprovar** o escopo descrito na página do diagnóstico (o que se levanta, o que se entrega
  e a linha "Quem assina").
- **Direção precisa definir:** se os 5 dias são úteis e a partir de quando contam; o preço ou a faixa; se a mudança no
  item do simulador pede nova versão da política (`config.lgpd.versaoPolitica`).

## Ordem de publicação

1. A API nova (que aceita `porte` e `origem`) vai ao Cloud Run **antes** do site. O `LeadIn` recusa campo desconhecido:
   com a API antiga, um pedido com porte ou origem escolhidos volta com erro 422. O site só envia os dois campos quando
   escolhidos, então o pedido sem eles continua aceito mesmo pela API antiga.
2. Depois o site, com `python tools/publicar.py`.

## Pronto quando

- As suítes de `tests/ROTEIRO-QA.md` passam, com o e2e do menu novo, da página de proposta e do pedido pelo simulador.
- O cabeçalho cabe em 1280 px sem encostar no logotipo (conferido pelo e2e `test_modelo_c_menu_e_botao_do_diagnostico`).
- A página do diagnóstico está aprovada pelo responsável técnico.

## Limites conhecidos

- As trilhas das páginas continuam com os nomes antigos de grupo (Ferramentas, Empresarial, Soluções).
- O caminho do formulário só funciona com a API no ar (`config.api.base`); sem ela, cai no WhatsApp, como hoje.
- A mensagem do WhatsApp não leva o faturamento.
