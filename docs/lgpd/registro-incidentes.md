# Registro de incidentes de segurança

Guarde cada registro por, no mínimo, 5 anos, inclusive os não comunicados (Res. CD/ANPD nº 15/2024, art. 10). Não escreva aqui nomes ou dados de titulares: use quantidades e categorias.

## Modelo

```text
Número:
Data e hora do conhecimento:
Quem percebeu:
Descrição geral das circunstâncias:
Natureza e categoria dos dados afetados:
Número de titulares afetados:
Avaliação do risco e possíveis danos:
Medidas de correção e mitigação:
Comunicado à ANPD e aos titulares? Quando, como e com qual conteúdo:
Motivos de não comunicar (se for o caso):
Aprovado por:
```

## Registros

### 2026-001: painel público descrevia fragilidades de sistemas internos

**Situação:** aberto, para avaliação do responsável técnico.

- **Conhecimento:** 03/11/2026, na revisão de segurança do site.
- **Circunstâncias:** o arquivo público `homologacao.js`, base do painel de testes de orgatec.io, descreveu pontos fracos de sistemas internos (OrgAudi e Mini), incluindo o arquivo onde havia uma senha em texto claro. A senha em si não aparecia no site. O texto foi removido e o site, republicado em 03/11/2026. O início da exposição não foi apurado.
- **Dados afetados:** nenhum dado pessoal identificado no texto publicado. Não foi verificado se alguém usou essa informação.
- **Titulares afetados:** nenhum identificado até aqui.
- **Risco:** o site tem `noindex`, mas ficou aberto a quem acessasse o endereço.
- **Falta fazer:**
  1. Trocar a senha citada e confirmar aqui a data.
  2. Conferir nos registros do serviço se houve acesso estranho no período.
  3. Corrigir os demais pontos da pendência T12.
- **Comunicação:** só depois da conferência acima. Se houver indício de acesso a dados pessoais, siga o [plano de incidentes](plano-incidentes.md): o prazo conta a partir de quando a ORGATEC souber que dados pessoais foram afetados.
- **Prevenção:** detalhes de segurança agora ficam só em `docs/`, regra registrada no `CLAUDE.md` do projeto.
