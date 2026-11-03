# Revisão técnica antes da publicação

Data de referência do levantamento: **31/10/2026**.

## Situação atual

- Todos os itens de `site/assets/js/reforma-itens.js` saem com `revisao.status: 'pendente'`.
- Com `config.ambiente = 'producao'`, nenhum deles aparece no site, e a Central da Reforma mostra "Itens aguardando revisão técnica não aparecem".
- Em homologação, cada item aparece com o selo "em revisão técnica".

## Como aprovar um item

1. Confira o dispositivo no link da fonte (`fontes.js`).
2. Leia o `fato` e a `orientacao` do item.
3. No item, preencha `revisao: { status: 'aprovada', por: 'Nome do responsável', em: 'AAAA-MM-DD' }`. O teste `nenhum item sai aprovado sem revisão técnica` em `tests/js/conteudo.test.js` vai falhar de propósito: ajuste-o para listar os itens aprovados ou remova a verificação quando a revisão começar.
4. Para manter o item atualizado: a cada mudança, troque `consultadoEm`, acrescente uma linha em `historico` e volte a revisão para `pendente`. `conteudo.atrasados(itens, hoje, 90)` lista os itens com consulta antiga.

## Pontos que exigem atenção na revisão

| Item | O que conferir | Por quê |
|---|---|---|
| `transporte-carga` | A afirmação de que não há redução para o transporte rodoviário de cargas em geral | Conclusão por ausência: não há capítulo de redução para carga rodoviária na LC 214, e só o aéreo regional de carga tem redução de 40% (art. 287). Afirmações negativas pedem conferência humana. |
| `combustiveis` | A orientação sobre o crédito do diesel da transportadora | A lei não cita transportadoras; a leitura vem do art. 180, § 1º, combinado com o art. 57 (uso pessoal). |
| `lcdpr` | O limite de R$ 4,8 milhões e o texto vigente do art. 23-A da IN SRF nº 83/2001 | A fonte usada é o manual e a notícia da Receita (2026). O texto da IN não foi aberto, por isso a fonte está com o selo "pendente de validação". |
| `produtor-nao-contribuinte` e a calculadora do produtor | Receita **igual** a R$ 3,6 milhões | O art. 164 fala em receita "inferior" ao limite, e os §§ 2º e 3º falam em "exceder". A calculadora trata receita igual ao limite como contribuinte a partir do ano seguinte. Confirme essa leitura. |
| Calculadora do produtor | O valor do limite corrigido pelo IPCA (art. 167) | A calculadora usa o valor nominal e avisa que o valor corrigido do ano deve ser confirmado. |
| `aliquota-referencia` | A resolução do Senado sobre a CBS de 2027 | Em 31/10/2026, o TCU havia calculado 11,3468%, e o prazo do Senado varia entre as fontes (15/12 ou 22/12/2026). Atualize quando a resolução sair. |
| `imposto-seletivo` | A medida provisória das alíquotas | Foi anunciada em 29/10/2026 e não estava confirmada em 31/10/2026. |
| `split-payment` | O cronograma de obrigatoriedade | Até 31/10/2026, só havia manuais técnicos e nenhum ato com datas. |
| `comite-gestor` | A cláusula de vigência da Resolução CGIBS nº 6/2026 | Não foi lida. |
| `conformidade-2026` e a orientação de que o escritório pode ser o contador indicado | Os requisitos do Ato Conjunto nº 5/2026 | A orientação é comercial: confirme se o texto está adequado ao Código de Ética (NBC PG 01). |
| Página Escritório | "A ORGATEC atende há anos empresas do agronegócio e do transporte..." | É afirmação institucional, sem número. Os **51 anos** ficam desligados em `config.institucional` até haver documento que comprove a data de início. |
| `regulamento-cbs` | Vigência escalonada do Decreto nº 12.955/2026 | A cláusula de vigência não foi lida por completo. |

## Correção já aplicada em 31/10/2026

O alerta do simulador para o agro dizia que o produtor abaixo de R$ 3,6 milhões "pode optar por não ser contribuinte". Pela LC 214, a regra é a inversa:
- abaixo do limite, ele **não é** contribuinte (art. 164);
- ele **pode optar** por se inscrever no regime regular (art. 165).

O texto foi corrigido em `site/assets/js/regras.js`, e a fonte `lc214_produtor_opcao` foi incluída.
