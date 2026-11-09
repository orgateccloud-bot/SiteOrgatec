/* Componente único da viagem: o mesmo na Central (motorista/gestor) e no Portal (cliente). */
(function (raiz) {
  'use strict';
  var OT = raiz.OT, esc = OT.esc;
  var ROTULO_EVENTO = { direcao: 'Direção', pausa: 'Pausa obrigatória', refeicao: 'Refeição', pernoite: 'Pernoite / descanso', parada: 'Parada (carga/descarga)', chegada: 'Chegada' };
  var ROTULO_FONTE = { rota: 'Rota', combustivel: 'Combustível', pedagio: 'Pedágio', bloqueios: 'Bloqueios', clima: 'Clima' };

  function renderizar(alvo, v, opcoes) {
    opcoes = opcoes || {};
    var r = v.resultado, j = r.jornada, d = r.despesas;
    alvo.innerHTML =
      '<div class="kpis">' +
        kpi(OT.num1.format(r.rota.distancia_km) + ' km', 'distância') +
        kpi(OT.horas(j.duracao_total_h), 'tempo total (' + OT.horas(j.direcao_h) + ' dirigindo)') +
        kpi(OT.diaHora.format(new Date(j.chegada_prevista)), 'chegada prevista') +
        kpi(j.pernoites + ' / ' + j.pausas, 'pernoites / pausas') +
        kpi(OT.brl.format(Number(d.total)), 'despesa prevista') +
        kpi(OT.brl.format(Number(d.custo_por_km)), 'custo por km') +
      '</div>' +
      '<div class="duas">' +
        '<div class="cartao"><h2>Rota ' + (v.status ? '<span class="tag t-ok">' + esc(v.status.replace('_', ' ')) + '</span>' : '') + '</h2>' +
          '<svg class="mapa" data-mapa role="img" aria-label="Traçado da rota com pedágios, bloqueios e pernoites"></svg>' +
          '<div class="legenda"><span><i style="background:#003365"></i>origem/destino</span><span><i style="background:#3f88d5"></i>pedágio</span>' +
          '<span><i style="background:#c0392b"></i>bloqueio</span><span><i style="background:#8e44ad"></i>pernoite</span><span><i style="background:#1d6b3a"></i>posição atual</span></div>' +
          '<div data-vivo></div></div>' +
        '<div class="cartao"><h2>Despesas previstas</h2><div class="rolagem">' + tabelaDespesas(d, opcoes.editavel) + '</div></div>' +
      '</div>' +
      '<div class="duas">' +
        '<div class="cartao"><h2>Linha do tempo</h2><ul class="tempo">' + linhaTempo(j.eventos) + '</ul>' +
          '<p class="fonte">Limites de direção e descanso são parâmetros (CTB art. 67-C) — revisão jurídica pendente.</p></div>' +
        '<div><div class="cartao"><h2>Bloqueios e interdições</h2>' + bloqueios(r.bloqueios) + '</div>' +
          '<div class="cartao"><h2>Previsão do tempo no trajeto</h2>' + clima(r.clima) + '</div>' +
          '<div class="cartao"><h3>Fontes desta estimativa</h3>' + fontes(r) + '</div></div>' +
      '</div>';
    desenharMapa(alvo.querySelector('[data-mapa]'), r, null);
    if (opcoes.editavel && opcoes.aoAjustar) ligarAjustes(alvo, opcoes.aoAjustar);
  }

  function kpi(valor, rotulo) { return '<div class="kpi"><b>' + esc(valor) + '</b><span>' + esc(rotulo) + '</span></div>'; }

  function tabelaDespesas(d, editavel) {
    var linhas = d.itens.map(function (i) {
      var unit = i.tipo === 'reserva_imprevistos' ? (Number(i.valor_unitario) * 100).toLocaleString('pt-BR') + '%' : OT.brl.format(Number(i.valor_unitario));
      var valor = editavel
        ? '<input class="ajuste" type="number" min="0" step="0.01" data-tipo="' + esc(i.tipo) + '" value="' + esc(i.valor) + '" aria-label="Valor de ' + esc(i.rotulo) + '">'
        : OT.brl.format(Number(i.valor));
      return '<tr><td>' + esc(i.rotulo) + (i.ajustado ? ' <span class="tag t-aviso">ajustado</span>' : '') +
        '<div class="fonte">' + esc(i.fonte) + (i.estado && i.estado !== 'ok' ? ' ' + OT.tagEstado(i.estado) : '') + '</div></td>' +
        '<td class="num">' + esc(OT.num1.format(Number(i.quantidade))) + ' ' + esc(i.unidade) + '</td><td class="num">' + unit + '</td>' +
        '<td class="num">' + valor + (editavel && i.ajustado ? ' <button class="mini sec" data-limpar="' + esc(i.tipo) + '" type="button" title="Voltar ao calculado">↺</button>' : '') + '</td></tr>';
    }).join('');
    return '<table><thead><tr><th>Item</th><th class="num">Qtd.</th><th class="num">Unitário</th><th class="num">Valor</th></tr></thead><tbody>' + linhas +
      '</tbody><tfoot><tr><td colspan="3">Total previsto</td><td class="num">' + OT.brl.format(Number(d.total)) + '</td></tr></tfoot></table>' +
      (editavel ? '<p class="fonte">Altere um valor e saia do campo para salvar o ajuste. Os valores-base ficam em Parâmetros.</p>' : '');
  }

  function ligarAjustes(alvo, aoAjustar) {
    alvo.querySelectorAll('input.ajuste').forEach(function (inp) {
      var inicial = inp.value;
      inp.addEventListener('change', function () { if (inp.value !== inicial && inp.value !== '') aoAjustar(inp.dataset.tipo, inp.value); });
    });
    alvo.querySelectorAll('[data-limpar]').forEach(function (b) {
      b.addEventListener('click', function () { aoAjustar(b.dataset.limpar, null); });
    });
  }

  function linhaTempo(eventos) {
    return eventos.filter(function (e) { return e.tipo !== 'direcao' || e.duracao_h >= 0.05; }).map(function (e) {
      var desc = e.tipo === 'direcao' ? OT.horas(e.duracao_h) + ' · km ' + OT.num1.format(e.km_inicio) + ' → ' + OT.num1.format(e.km_fim)
        : (e.tipo === 'chegada' ? 'km ' + OT.num1.format(e.km_fim) : OT.horas(e.duracao_h) + ' · km ' + OT.num1.format(e.km_inicio));
      return '<li><time datetime="' + esc(e.inicio) + '">' + OT.diaHora.format(new Date(e.inicio)) + '</time><span><b>' + esc(ROTULO_EVENTO[e.tipo] || e.tipo) + '</b> · ' + esc(desc) + '</span></li>';
    }).join('');
  }

  function bloqueios(lista) {
    if (!lista.length) return '<p class="vazio">Nenhum bloqueio informado para o trajeto e o período.</p>';
    return '<table><thead><tr><th>km</th><th>Ocorrência</th><th>Passagem</th></tr></thead><tbody>' + lista.map(function (b) {
      return '<tr><td class="num">' + OT.num1.format(b.km) + '</td><td>' + esc(b.descricao) + '<div class="fonte">' + esc(b.fonte) + '</div></td><td>' + OT.diaHora.format(new Date(b.passagem_prevista)) + '</td></tr>';
    }).join('') + '</tbody></table>';
  }

  function clima(lista) {
    if (!lista.length) return '<p class="vazio">Previsão indisponível no momento.</p>';
    return '<table><thead><tr><th>km</th><th>Passagem</th><th>Condição</th><th class="num">°C</th><th class="num">Chuva</th></tr></thead><tbody>' + lista.map(function (c) {
      return '<tr><td class="num">' + OT.num1.format(c.km) + '</td><td>' + OT.diaHora.format(new Date(c.passagem)) + '</td><td>' + esc(c.condicao) + '</td>' +
        '<td class="num">' + (c.temperatura_c == null ? '—' : OT.num1.format(c.temperatura_c)) + '</td><td class="num">' + (c.chuva_mm == null ? '—' : OT.num1.format(c.chuva_mm) + ' mm') + '</td></tr>';
    }).join('') + '</tbody></table>';
  }

  function fontes(r) {
    return '<table><tbody>' + Object.keys(r.fontes).map(function (k) {
      var f = r.fontes[k];
      return '<tr><td>' + esc(ROTULO_FONTE[k] || k) + '</td><td>' + OT.tagEstado(f.estado) + '</td><td class="fonte">' + esc(f.fonte) + (f.detalhe ? ' — ' + esc(f.detalhe) : '') + '</td></tr>';
    }).join('') + '</tbody></table><p class="fonte">Parâmetros vigentes: ' + esc(r.parametros_vigencia) + ' · calculado em ' + OT.dataHora.format(new Date(r.calculado_em)) + '</p>';
  }

  /* Mapa sem imagens de fundo (CSP img-src 'self'): projeção simples do traçado em SVG. */
  function desenharMapa(svg, r, posicao) {
    if (!svg) return;
    var g = r.rota.geometria, todos = g.slice();
    if (posicao) todos.push([posicao.lat, posicao.lon]);
    var lats = todos.map(function (p) { return p[0]; }), lons = todos.map(function (p) { return p[1]; });
    var minLa = Math.min.apply(null, lats), maxLa = Math.max.apply(null, lats), minLo = Math.min.apply(null, lons), maxLo = Math.max.apply(null, lons);
    var W = 600, H = 320, m = 24, k = Math.cos((minLa + maxLa) / 2 * Math.PI / 180);
    var esc_ = Math.min((W - 2 * m) / Math.max((maxLo - minLo) * k, 1e-6), (H - 2 * m) / Math.max(maxLa - minLa, 1e-6));
    var ox = (W - (maxLo - minLo) * k * esc_) / 2, oy = (H - (maxLa - minLa) * esc_) / 2;
    function xy(la, lo) { return [(ox + (lo - minLo) * k * esc_).toFixed(1), (H - oy - (la - minLa) * esc_).toFixed(1)]; }
    function ponto(la, lo, cor, raio, titulo) { var p = xy(la, lo); return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="' + raio + '" fill="' + cor + '" stroke="#fff" stroke-width="1.5"><title>' + esc(titulo) + '</title></circle>'; }
    var linha = g.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ');
    var s = '<polyline points="' + linha + '" fill="none" stroke="#003365" stroke-width="3" stroke-linejoin="round" opacity=".85"/>';
    (r.pedagios || []).forEach(function (p) { s += ponto(p.lat, p.lon, '#3f88d5', 4, 'Pedágio: ' + p.nome); });
    (r.bloqueios || []).forEach(function (b) { s += ponto(b.lat, b.lon, '#c0392b', 6, 'Bloqueio: ' + b.descricao); });
    r.jornada.eventos.filter(function (e) { return e.tipo === 'pernoite'; }).forEach(function (e) {
      var p = pontoNoKm(g, r.rota.distancia_km, e.km_inicio); s += ponto(p[0], p[1], '#8e44ad', 5, 'Pernoite km ' + e.km_inicio);
    });
    r.pontos.forEach(function (p) { s += ponto(p.lat, p.lon, '#003365', 6, p.nome); });
    if (posicao) s += ponto(posicao.lat, posicao.lon, '#1d6b3a', 7, 'Posição atual ' + OT.diaHora.format(new Date(posicao.ts)));
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.innerHTML = s;
  }

  function pontoNoKm(g, total, km) {
    var acc = [0];
    for (var i = 1; i < g.length; i++) acc.push(acc[i - 1] + Math.hypot(g[i][0] - g[i - 1][0], g[i][1] - g[i - 1][1]));
    var alvo = km / total * acc[acc.length - 1];
    for (var j = 1; j < acc.length; j++) if (acc[j] >= alvo) {
      var f = (alvo - acc[j - 1]) / ((acc[j] - acc[j - 1]) || 1);
      return [g[j - 1][0] + (g[j][0] - g[j - 1][0]) * f, g[j - 1][1] + (g[j][1] - g[j - 1][1]) * f];
    }
    return g[g.length - 1];
  }

  function mostrarPosicao(alvo, v, evt) {
    desenharMapa(alvo.querySelector('[data-mapa]'), v.resultado, evt);
    var box = alvo.querySelector('[data-vivo]');
    if (!box || !evt) return;
    box.innerHTML = '<div class="msg ' + (evt.fora_da_rota ? 'aviso' : 'ok') + '"><span class="ao-vivo">Posição</span> ' +
      esc(OT.diaHora.format(new Date(evt.ts))) + ' · km ' + OT.num1.format(evt.km_percorrido) + ' de ' + OT.num1.format(v.resultado.rota.distancia_km) +
      (evt.velocidade_kmh != null ? ' · ' + OT.num1.format(evt.velocidade_kmh) + ' km/h' : '') +
      (evt.temperatura_c != null ? ' · baú ' + OT.num1.format(evt.temperatura_c) + ' °C' : '') +
      (evt.combustivel_pct != null ? ' · tanque ' + OT.num1.format(evt.combustivel_pct) + '%' : '') +
      (evt.fora_da_rota ? ' · <b>fora da rota (' + OT.num1.format(evt.desvio_km) + ' km)</b>' : '') + ' · ' + esc(evt.sensor) + '</div>';
  }

  raiz.ViagemView = { renderizar: renderizar, mostrarPosicao: mostrarPosicao };
})(window);
