# Virada para produção (T9)

Hoje `site/assets/js/config.js` está com `ambiente: 'homologacao'`. Virar é trocar essa linha para `'producao'`, mas só depois de fechar os bloqueios. Este roteiro mostra o que a virada faz, o que fecha cada bloqueio e como voltar atrás.

## O que muda ao virar (medido em 10/11/2026)

Servi o site inteiro com `ambiente: 'producao'` e comparei com a homologação, nas 62 páginas.

- **Não aparece nenhum erro novo.** Os três avisos de 404 já existem em homologação (páginas do transporte, em reestruturação).
- **O aviso "Ambiente de homologação" some** da abertura e das demais páginas.
- **O painel de testes e as entradas de desenvolvimento do transporte** deixam de aparecer.
- **Vinte páginas perdem conteúdo,** porque só pontos aprovados pelo responsável técnico aparecem. Hoje são 70 de 70 pendentes (32 da reforma e 38 do compliance) e o termômetro todo também:

| Página | Texto visível hoje | Texto visível em produção |
|---|---|---|
| `reforma/index.html` | 29.478 caracteres | 3.416 |
| `compliance/termometro.html` | 9.400 | 1.301 |
| `compliance/index.html` | 12.771 | 3.953 |
| `compliance/publico/*` (8 páginas) | 5.992 a 17.201 | cerca de 3.600 |
| demais de compliance, `cliente/`, `consultoria-tributaria`, `empresarial/transporte`, `inicio` | — | só o esqueleto |

Por isso o V1 bloqueia a produção: sem a revisão, a parte central do site fica vazia.

## Os 10 bloqueios e como fechar cada um

| ID | O que falta | Quem | Como fechar |
|---|---|---|---|
| V1 | Aprovar os 70 pontos (e, se quiser o termômetro, as 47 perguntas) | Responsável técnico | Abrir `docs/revisao/revisao-tecnica.html`, decidir "Aprovar" ou "Ajustar" em cada ponto, baixar o registro. Depois: `python tools/aplicar_revisao.py registro.json` (simula) e `--aplicar` (grava). |
| V6 | Aprovar os prazos de retenção (24 meses e 30 dias) | Responsável técnico | Aprovar no texto de `site/privacidade.html`. A rotina já roda todo dia às 4h. |
| V12 | Confirmar que as rotinas do bloco "Como a ORGATEC cumpre as próprias obrigações" existem no escritório | Responsável técnico | Confirmar por escrito e marcar na lista de pendências. |
| V14 | Aprovar a política de privacidade 2026-11 | Responsável técnico | Resolver os trechos com o selo "pendente de validação". |
| V15 | Aprovar os documentos internos de proteção de dados | Responsável técnico | `docs/lgpd/README.md`. A equipe preenche, o responsável aprova. |
| D2 | Área do cliente: só o portal do ERP ou área própria | Direção | Decidir. Muda C2 e T5. |
| C2 | Alvo do CNAME de `portal.orgatec.io` | Direção, com a Athenas Online | Pedir o endereço à Athenas. |
| C5 | Validar o WhatsApp +55 62 99294-9161 | Direção | Confirmar que o número é o oficial e marcar `whatsapp.validado`. |
| T2 | Envio real do e-mail de confirmação do opt-in | Desenvolvimento, depende de escolha | Escolher o serviço de envio; depois implementar em `backend/app.py`. |
| T5 | DNS e certificado de `portal.orgatec.io` | Desenvolvimento, depende de C2 | Criar o CNAME quando a Athenas informar o alvo. |

O que o desenvolvimento faz sozinho já está pronto: a ferramenta que aplica a revisão, a trava da virada e este roteiro. As duas únicas pendências técnicas bloqueantes (T2 e T5) esperam decisões da direção.

## A trava

`tests/js/homologacao.test.js` falha se `ambiente` for `'producao'` com qualquer pendência que bloqueia ainda aberta. Como `tools/publicar.py` roda a suíte, **não dá para publicar a produção com bloqueio aberto**, mesmo por engano.

Um segundo teste, `tests/js/revisao-aplicada.test.js`, falha se o texto de um ponto aprovado mudar depois da revisão. O ponto tem de voltar para a revisão: rode `python tools/aplicar_revisao.py` com um registro novo, que revoga a aprovação do texto alterado.

## Passo a passo da virada

Quando o painel (`/testes/`) mostrar **0 bloqueios**:

1. Na `SiteOrgatec-dev`, trocar `ambiente: 'homologacao'` por `'producao'` em `config.js`.
2. `node tools/exportar_pendencias.js` para regerar `docs/pendencias-proxima-fase.md`.
3. Rodar a suíte e fazer o commit na `desenvolvimento`.
4. Na pasta principal, com autorização da direção: `python tools/publicar.py --com-desenvolvimento`.
5. Conferir no ar:
   - `reforma/` e `compliance/` com os pontos aprovados;
   - o aviso de homologação ausente;
   - o `robots` e o mapa do site;
   - o formulário de contato, se tiver sido ligado (`api.publica`).
6. Marcar o T9 como resolvido no painel.

## Voltar atrás

Trocar `ambiente` de volta para `'homologacao'` em `config.js` e publicar de novo. O site volta a mostrar a faixa de aviso e os pontos em revisão, sem perder nenhum dado.

## Decisão da direção: lançar com revisão parcial?

A virada esconde só o que não foi aprovado. Dá para lançar com parte dos pontos aprovados, mas o V1 hoje exige todos, e a página da reforma ficaria quase vazia no início. Para lançar assim, a direção decide **quais pontos são o mínimo** e o V1 passa a exigir só esses. Sem essa decisão, o caminho acima vale.
