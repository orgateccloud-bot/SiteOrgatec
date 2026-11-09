# Reestruturação do site: áreas Rural e Empresarial, Janelas do Transporte e Empresarial e Central de Viagem

- **Situação:** ideia (plano aprovado para desenvolvimento em fases; cada fase vai à prévia antes de seguir)
- **Branch:** `ideia/reestruturacao-transporte`
- **Prévia:**
- **Autoria:** Warley Moreira Veloso
- **Prompt de execução:** [reestruturacao-transporte-prompt.md](reestruturacao-transporte-prompt.md)

## Problema

- **Menu sem porta por público.** O site atende principalmente agro e transporte, mas o menu é organizado por tipo de conteúdo. O produtor já tem entrada própria (`setores/agro.html`, Fase 2 do agro), mas não tem uma área. A empresa e a transportadora não têm nenhuma das duas.
- **Transporte sem destino.** A página de transporte linka os alertas regionais, que não cobrem esse setor (beco sem saída).
- **Janela só para o agro.** A Janela de Campo traz o produtor de volta todo dia; a empresa e a transportadora não têm equivalente.
- **Previsão de viagem fora do site.** A transportadora calcula despesas e tempo de viagem à mão e não tem onde acompanhar o veículo.

## Público

Transportadora (ETC, CTC e TAC), empresa do Simples, do lucro presumido e do lucro real, produtor rural e a equipe da ORGATEC.

## Proposta

Em fases, cada uma com prévia e aprovação:

1. **Correções de virada** que não dependem de decisão: schema, descrições, gerador do sitemap e beco sem saída do transporte.
2. **Reestruturação do sitemap:**
   - áreas `/rural/` (o hub do agro muda de endereço) e `/empresarial/` (nova);
   - Consultoria tributária no primeiro nível;
   - alertas regionais na Central da Reforma;
   - redirecionamentos 301.
3. **Área Empresarial:** página do hub, Transporte movido para ela, página de lucro real e prazos do transportador.
4. **Janela Empresarial e Janela do Transporte:** boletim gerado no servidor, no padrão da Janela de Campo.
5. **Central de Viagem e portal do cliente com sensores via API.** Depende das decisões de login e de área do cliente (ver abaixo).

## Fontes e validação

- **Normas do transportador** (Lei nº 15.485/2026, CIOT obrigatório desde 18/09/2026 pela Res. ANTT nº 6.090/2026, vale-pedágio pela Lei nº 10.209/2001):
  - já conferidas em `docs/relatorio-publicos-reforma-compliance.md`, seção 3.6;
  - todo item novo entra na revisão técnica (V1) do responsável técnico.
- **Fontes de dados das Janelas e da Central:** status de cada uma na seção 6 do prompt. Nenhuma entra no ar sem os termos de uso conferidos, no padrão de `tools/agro_fontes.json`.
- **Limites de jornada do motorista** (CTB art. 67-C): ficam como parâmetro. Revisão jurídica pendente (STF, ADI 5322).

## Pronto quando

- Cada fase passa na suíte (JS, bandit, pytest, e2e) e vai à prévia aprovada.
- Nenhum endereço antigo dá 404: os 301 foram testados na prévia.
- As Janelas mostram fonte, horário da coleta e estado de cada cartão. Uma fonte com falha não exibe dado velho sem aviso.
- Ao lançar uma rota de teste, a Central mostra despesas, tempo, bloqueios e clima; o portal mostra o mesmo; um sensor simulado, falando pela API, atualiza a posição.

## Decisões pendentes (do escritório)

| # | Decisão | Bloqueia |
|---|---|---|
| R1 | Formato das URLs: ligar `cleanUrls` (endereços sem `.html`) ou manter `.html` | Fase 2 |
| R2 | O painel `/testes/` continua público depois da virada para produção (T9)? | Checklist de virada |
| R3 | O que é a Janela Empresarial (proposta: prazos e mudanças da semana por perfil) e se Transporte é um perfil dela ou uma janela separada | Fase 4 |
| R4 | Login (Firebase Authentication) e área do cliente própria (D2) | Fase 5 no ar |
| R5 | Faturamento Blaze (T1) para publicar a API no Cloud Run | Fases 4 (se usar a API) e 5 |
