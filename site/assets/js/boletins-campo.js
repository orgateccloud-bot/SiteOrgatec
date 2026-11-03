/* Janela de Campo: boletins agrometeorológicos para o produtor rural (renderizados por campo.js em
   site/setores/janela-de-campo.html). Um registro por boletim; o mais recente vai primeiro.

   Campos de cada boletim:
   - id (AAAA-MM-DD do dia previsto), dia (o mesmo), emitidoEm (AAAA-MM-DD), resumo.
   - alerta: { titulo, itens[] } ou null.
   - regioes[]: { id, nome, uf, ceu, temp, chuva, vento, alertas: [[estado, texto]], dia: [6 estados],
     nota, ops: { pulv|plantio|colheita|animais|maquinas: [estado, recomendação] } }.
     estado = 'ok' (favorável) | 'atencao' (com restrição) | 'evitar'.
     dia = períodos 00–06h, 06–10h, 10–12h, 12–15h, 15–18h, 18–24h (horário de Brasília).
   - tendencia[]: { quando, titulo, texto }; confianca[]: { rotulo, texto }; fontes[]: { rotulo, url } (obrigatório).

   Como publicar um boletim novo: copie o bloco mais recente, troque datas e textos, coloque-o no topo da
   lista e rode `node --test tests/js/campo.test.js` (confere a estrutura). Depois do dia previsto, o boletim
   continua no ar como arquivo, marcado como vencido. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).boletinsCampo = factory();
})(this, function () {
  'use strict';
  return [
    {
      id: '2026-10-28', dia: '2026-10-28', emitidoEm: '2026-10-27',
      resumo: 'Previsão geral para o país, sem localidade específica. Escolha a região e a operação no painel para ver a janela do dia e a recomendação de campo.',
      alerta: {
        titulo: 'Atenção · temporais à tarde',
        itens: [
          'Centro-Oeste, interior do Sudeste e Norte: pancadas fortes com raios a partir do fim da manhã. Em MT, avisos de ventos até 60 km/h, granizo e até 80 mm em um dia em pontos isolados.',
          'Calor de 28 a 38 °C no Centro-Oeste, podendo chegar a 40 °C na divisa MT/GO.',
          'Regra do dia nas áreas de risco: operações de campo concentradas na manhã.'
        ]
      },
      regioes: [
        { id: 'co', nome: 'Centro-Oeste', uf: 'MT · GO · DF · MS',
          ceu: 'Sol e nuvens pela manhã; pancadas fortes com raios à tarde',
          temp: 'Máx. 28–38 °C; até 40 °C na divisa MT/GO',
          chuva: 'Moderada a forte à tarde; até 80 mm/dia em pontos de MT',
          vento: 'Rajadas até 60 km/h nos temporais (avisos em MT)',
          alertas: [['evitar', 'Temporal'], ['evitar', 'Granizo (MT)'], ['atencao', 'Calor forte']],
          dia: ['ok', 'ok', 'atencao', 'evitar', 'evitar', 'atencao'],
          nota: 'Melhor janela: 06h às 10h. Instabilidade ganha força a partir do fim da manhã.',
          ops: {
            pulv: ['atencao', 'Aplicar só no início da manhã e encerrar até cerca de 10h. Depois, o calor aumenta a deriva e a evaporação, e a chuva da tarde pode lavar o produto.'],
            plantio: ['ok', 'A umidade que volta favorece a semeadura da soja. Evite semear em área declivosa ou recém-preparada onde a enxurrada da tarde pode arrastar sementes e solo.'],
            colheita: ['atencao', 'Se houver colheita em curso, concentre de manhã e encerre antes das pancadas. Grão molhado à tarde exige secagem.'],
            animais: ['atencao', 'Garanta sombra e água no pico de calor. Recolha os animais de pastos abertos e de perto de cercas de arame antes das pancadas, por risco de raios.'],
            maquinas: ['evitar', 'Recolha máquinas, sementes, adubo e defensivos para galpão antes do meio-dia. Granizo e vento podem danificar equipamentos e embalagens expostas.']
          } },
        { id: 'sei', nome: 'Sudeste interior', uf: 'Norte de SP · Triângulo · noroeste de MG',
          ceu: 'Instabilidade crescendo do fim da manhã à tarde',
          temp: 'Calor moderado',
          chuva: 'Moderada a forte à tarde, com risco de enxurrada',
          vento: 'Rajadas nos temporais; sem dado regional confiável',
          alertas: [['evitar', 'Temporal'], ['atencao', 'Raios'], ['atencao', 'Enxurrada']],
          dia: ['ok', 'ok', 'atencao', 'evitar', 'evitar', 'atencao'],
          nota: 'Melhor janela: 06h às 10h. Pancadas mais prováveis entre 12h e 18h.',
          ops: {
            pulv: ['atencao', 'Aplicar até o fim da manhã. À tarde, risco de chuva logo após a aplicação.'],
            plantio: ['ok', 'Umidade favorável ao plantio. Atenção a áreas com risco de enxurrada.'],
            colheita: ['atencao', 'Operar pela manhã e encerrar antes das pancadas.'],
            animais: ['atencao', 'Recolher o gado de áreas expostas a raios antes da tarde.'],
            maquinas: ['atencao', 'Deixar máquinas e insumos cobertos a partir do meio-dia.']
          } },
        { id: 'sel', nome: 'Sudeste leste', uf: 'RJ · ES · centro-sul e leste de SP',
          ceu: 'Pouca nebulosidade de chuva; tempo mais firme',
          temp: 'Mínimas baixas para outubro (ex.: 11 °C previstos em Campos dos Goytacazes)',
          chuva: 'Fraca ou ausente; chuva fraca no litoral paulista',
          vento: 'Sem dado regional confiável',
          alertas: [['ok', 'Sem alerta relevante']],
          dia: ['ok', 'ok', 'ok', 'ok', 'ok', 'ok'],
          nota: 'Dia todo operável. É a melhor janela do país para trabalho de campo na quarta.',
          ops: {
            pulv: ['ok', 'Boa janela. Prefira manhã e fim de tarde para menor deriva.'],
            plantio: ['ok', 'Condição boa para operar; verifique a umidade do solo, pois a chuva foi pouca.'],
            colheita: ['ok', 'Dia favorável para colher e transportar.'],
            animais: ['ok', 'Manejo normal. Madrugada mais fria para outubro.'],
            maquinas: ['ok', 'Sem necessidade de recolhimento especial.']
          } },
        { id: 'sul', nome: 'Sul', uf: 'RS · SC · PR',
          ceu: 'Pancadas passageiras no RS, oeste de SC e norte/centro do PR',
          temp: 'Mínimas de 6–9 °C nas serras de SC e RS; aquecimento gradual',
          chuva: 'Acumulados baixos na quarta; chuva aumenta na quinta',
          vento: 'Sem dado regional confiável',
          alertas: [['atencao', 'Geada residual nas serras (madrugada)'], ['atencao', 'Chuva aumenta na quinta']],
          dia: ['atencao', 'ok', 'ok', 'atencao', 'atencao', 'ok'],
          nota: 'Madrugada fria nas serras. Pancadas passageiras possíveis à tarde.',
          ops: {
            pulv: ['ok', 'Janela boa pela manhã. Evite aplicar se houver pancada prevista para a sua área à tarde.'],
            plantio: ['ok', 'Quarta ainda permite plantio. Antecipe o que der antes da chuva de quinta.'],
            colheita: ['ok', 'Antecipe a colheita de trigo e cereais de inverno: a chuva ganha força na quinta e os maiores volumes da semana vêm para o Sul.'],
            animais: ['atencao', 'Madrugada fria nas serras: abrigo para animais jovens e recém-tosquiados.'],
            maquinas: ['ok', 'Sem risco relevante na quarta. Planeje cobertura de grãos e insumos para quinta em diante.']
          } },
        { id: 'norte', nome: 'Norte', uf: 'RO · AC · AM · TO · centro-sul do PA',
          ceu: 'Chuva moderada a forte, temporais principalmente à tarde',
          temp: 'Quente',
          chuva: 'Moderada a forte; oeste do AM pode passar de 100 mm na semana',
          vento: 'Rajadas nos temporais; sem dado regional confiável',
          alertas: [['evitar', 'Temporal à tarde'], ['atencao', 'Raios']],
          dia: ['ok', 'ok', 'atencao', 'evitar', 'evitar', 'atencao'],
          nota: 'Melhor janela: manhã. Temporais mais prováveis à tarde.',
          ops: {
            pulv: ['atencao', 'Só pela manhã; alto risco de lavagem à tarde.'],
            plantio: ['ok', 'Umidade favorável; evite áreas sujeitas a encharcamento.'],
            colheita: ['atencao', 'Operar de manhã.'],
            animais: ['atencao', 'Recolher animais de áreas abertas antes da tarde.'],
            maquinas: ['atencao', 'Cobrir máquinas e insumos a partir do meio-dia.']
          } },
        { id: 'ne', nome: 'Nordeste', uf: 'BA · centro-sul de MA e PI · oeste de PE (chuva) · demais áreas secas',
          ceu: 'Chuva moderada a forte na faixa oeste e na BA; pouca chuva no restante',
          temp: 'Quente',
          chuva: 'Moderada a forte no Matopiba e na BA; baixa no interior e no norte de MA e PI',
          vento: 'Sem dado regional confiável',
          alertas: [['atencao', 'Pancadas fortes no Matopiba/BA'], ['atencao', 'Seca no sertão']],
          dia: ['ok', 'ok', 'ok', 'atencao', 'atencao', 'ok'],
          nota: 'Na faixa com chuva, pancadas mais prováveis à tarde. No sertão, dia seco.',
          ops: {
            pulv: ['atencao', 'Matopiba/BA: aplicar pela manhã. Sertão: atenção à baixa umidade e à deriva nas horas quentes.'],
            plantio: ['ok', 'Matopiba: a chuva favorece o início do plantio. Sertão: sem umidade para plantar.'],
            colheita: ['ok', 'Sem restrição relevante pela manhã.'],
            animais: ['atencao', 'Sertão: reforçar água e sombra para o rebanho.'],
            maquinas: ['ok', 'Cobrir insumos onde houver previsão de pancada.']
          } }
      ],
      tendencia: [
        { quando: 'Qua 28/10', titulo: 'Temporais à tarde no interior', texto: 'Centro-Oeste, norte de SP, Triângulo e noroeste de MG, Norte. Sul com pancadas passageiras.' },
        { quando: 'Qui 29/10', titulo: 'Chuva se espalha', texto: 'Área maior de chuva entre São Paulo e Minas Gerais. No Sul, a chuva ganha força.' },
        { quando: 'Sex 30/10 → Seg 02/11', titulo: 'Maiores volumes no Sul', texto: 'RS, SC e PR com pontos acima de 100 mm na semana. MT com 20 a 60 mm, pontos acima de 80 mm. Interior do Nordeste segue seco.' }
      ],
      confianca: [
        { rotulo: 'Padrão geral: razoavelmente seguro.', texto: 'INMET (Informativo nº 43/2026) e fontes secundárias concordam.' },
        { rotulo: 'Local e volume de cada temporal: baixa confiança.', texto: 'Pancadas de calor são irregulares; uma fazenda pode receber 50 mm e a vizinha ficar seca.' },
        { rotulo: 'Pode mudar se:', texto: 'a instabilidade atrasar (mais calor, menos chuva no Centro-Oeste) ou se organizar mais (mais risco de granizo).' },
        { rotulo: 'Lacunas:', texto: 'sem dado confiável de direção do vento e umidade por região. Horários da linha do dia são estimativa do padrão de pancadas da tarde.' }
      ],
      fontes: [
        { rotulo: 'INMET · previsão 26/10 a 02/11/2026', url: 'https://portal.inmet.gov.br/noticias/inmet-divulga-previs%C3%A3o-para-semana-de-26-de-outubro-a-02-de-novembro-de-2026' },
        { rotulo: 'Canal Rural · chuva forte em várias regiões', url: 'https://canalrural.com.br/previsao-do-tempo/chuva-forte-atinge-varias-regioes-do-brasil-saiba-ate-quando-vai-chover' },
        { rotulo: 'Climatempo · temporais no norte de SP e Triângulo', url: 'https://www.climatempo.com.br/noticia/temporal/temporais-voltam-a-ganhar-forca-no-norte-de-sp-e-no-triangulo-mineiro-nesta-quarta-feira' },
        { rotulo: 'VG Notícias · temporais em MT', url: 'https://vgnoticias.com.br/cidades/temporais-ameacam-69-cidades-de-mt-com-ventania-e-granizo/154154' },
        { rotulo: 'O Tempo · mínimas previstas pelo INMET', url: 'https://otempo.com.br/tempo/2026/10/27/frio-fora-de-epoca-derruba-a-minima-a-11c-nesta-quarta-feira' },
        { rotulo: 'Mix Vale · frio e geada no Sul', url: 'https://mixvale.com.br/2026/10/27/geada-na-serra-gaucha-e-minimas-podendo-chegar-a-10-c-no-sul' }
      ]
    }
  ];
});
