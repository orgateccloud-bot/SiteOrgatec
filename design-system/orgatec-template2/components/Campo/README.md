# Campo

Rótulo, campo e linha de ajuda ou erro. `id` é obrigatório e liga o rótulo ao campo.

- `tamanho="lg"` (`raio-xl`) no simulador; `md` (`raio-lg`) nos formulários de lead, opt-in e contato.
- `opcoes` troca o input por um select (setor, regime, UF).
- `erro` diz o que corrigir ("E-mail inválido.", "Escreva pelo menos 10 caracteres.") e é anunciado ao leitor de tela.
- Valores em reais aceitam o formato brasileiro ("2.400.000"); use `inputMode="decimal"`.
