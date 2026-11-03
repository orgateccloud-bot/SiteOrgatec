ORGATEC é um escritório de contabilidade consultiva e inteligência tributária, com responsável técnico com CRC ativo e atuação no eixo GO, TO e PA. O site vende diagnóstico tributário da Reforma (EC 132/2023, LC 214/2025). Cada número exibido carrega a fonte legal.

## Voz e conteúdo

- Escreva em português do Brasil, direto e técnico, falando com o empresário por "você" e "sua empresa". A ORGATEC fala de si como "nós" ("Preparamos sua empresa...").
- O nome é sempre **ORGATEC**, em maiúsculas. Nunca "Orgatec.IO" nem "Orgatec". Os domínios continuam `orgatec.io` e `portal.orgatec.io`.
- Toda regra, alíquota, percentual de incentivo ou prazo cita a norma e o dispositivo ("LC 214/2025, art. 41, §§ 3º e 4º") com `CitacaoFonte`. O que não foi confirmado leva o `Selo` "pendente de validação". Nunca apresente suposição como fato.
- Use normas como sobretítulo, no formato "EC 132/2023 • LC 214/2025 • Split Payment".
- Os CTAs são fixos: "Testar Simulador Tributário", "Agendar Diagnóstico com Especialista", "Falar no WhatsApp" ("WhatsApp" no celular).
- Todo resultado de simulação traz o aviso: "Simulação orientativa baseada na EC nº 132/2023 e LC nº 214/2025. Não substitui parecer técnico emitido pelo contador responsável."
- Emoji: nenhum, salvo o 🔒 de "Portal do Cliente" e o ⚠️ do aviso legal, que já existem no site.

## Cor

- Página em `fundo` e blocos em `superficie`, com borda `linha`. Títulos em `tinta`, texto em `tinta-texto`, apoio em `tinta-suave` e metadados em `tinta-fraca`.
- O hero e o rodapé são `palco` nos dois temas, com texto `marca-branco` e parágrafo `palco-texto`. A grade de pontos do hero usa `palco-ponto` a 16 px de passo (`espaco-4`) e 10% de opacidade.
- `acao` preenche o botão primário e a aba ativa e desenha o foco. Texto clicável, sobretítulos e referências legais usam `link`, que no escuro vira ciano.
- `contato` (verde) é exclusivo dos botões de WhatsApp e telefone.
- As cinco cores `marca-*` são as faixas do símbolo, do navy ao ciano. Use-as em peças de marca e capas, não em texto corrido. `marca-ciano` nunca vai como texto sobre claro.
- Estados: `pendente-*` para o que falta validar ou definir, `definido-*` para o que foi confirmado, `aviso-*` para a faixa de homologação.

## Tipografia

- Inter para tudo, JetBrains Mono para normas, registros, protocolos e valores (`referencia`, `dado`).
- O nome usa `nome-marca` (ExtraBold, +4%) e o descritor `descritor` (SemiBold, caixa-alta, +32%).
- Hierarquia: `titulo-hero` só no H1 do hero; `titulo-secao` em cada H2, com `sobretitulo` acima em `link`; `titulo-cartao` em cartões; `lead`, `corpo`, `pequeno` para texto; `rotulo` em campos; `selo` nos selos.
- Carregue as duas famílias do Google Fonts (pesos 400, 600, 700, 800 e 400, 600). Em produção, sirva os arquivos localmente.

## Espaço, forma e sombra

- Escala de 4 px: `espaco-4` entre cartões, `espaco-5` dentro do cartão do Hub, `espaco-20` no padding vertical de cada seção. Margem lateral: `espaco-4` no celular, `espaco-6` no tablet, `espaco-8` no desktop. Largura máxima de 1280 px.
- Cantos: `raio-lg` em campos pequenos e botões do cabeçalho, `raio-xl` em CTAs e campos do simulador, `raio-2xl` em cartões, `raio-pilula` só em selos.
- Sombra só em hover de cartão e no CTA do hero (`sombra-lg`) e no botão de contato (`sombra-sm`). O foco de teclado é `foco`, anel sólido de 2 px.
- O cabeçalho é fixo, branco a 90% com desfoque e borda `linha`. A navegação completa aparece a partir de 1280 px; abaixo, menu ☰.

## Marca

- Use `Assinatura` ou os arquivos dos grupos Símbolo, Assinaturas e Ícones. Não redesenhe o símbolo.
- Use o símbolo sempre com as cores originais, em fundo claro ou escuro (decisão da ORGATEC de 31/10/2026). A versão branca fica só para usos em uma cor, como carimbo ou gravação.
- Respiro: metade da altura do símbolo. Mínimo: 16 px ou 6 mm de símbolo, 160 px ou 40 mm de assinatura com descritor.
- Não distorça, não gire, não troque as cores, não aplique sombra ou efeito.

## Iconografia

O site não tem biblioteca de ícones: usa texto e dois glifos (🔒 no Portal do Cliente, ☰ no menu móvel). Ao precisar de ícones, escolha um conjunto de traço simples e registre aqui antes de usar.

## Acessibilidade

- Texto em `tinta`, `tinta-texto`, `tinta-suave` e `tinta-fraca` passa de 4,5:1 sobre `fundo` e `superficie` nos dois temas.
- Dois pares vêm do site e ficam abaixo do mínimo, mantidos por serem a identidade atual: branco sobre `contato` (2,5:1) e a borda `linha-campo` sobre branco (1,5:1). Se quiser corrigir, troque `contato` por #047857 (5,5:1) e `linha-campo` por #64748b (4,8:1).
- Todo campo tem rótulo visível; erros saem com `role="alert"`; o resultado do simulador é anunciado com `aria-live`.

## Rodapé obrigatório

Toda página termina com: CNPJ 13.155.211/0001-45; responsável técnico Robson Alain Veloso, `CRC-TO 002032/O-5 T-GO` em `dado` e `link`; sede na Av. Ministro Alfredo Nasser, nº 727, Centro, Formoso-GO; links para a Política de Privacidade (LGPD), as Fontes legais e a Marca; e a linha "Em conformidade com a LGPD e o Código de Ética do CFC (NBC PG 01)."
