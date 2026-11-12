/* Janela do Transporte: mapa público de alertas nas rodovias de GO, TO e PA (empresarial/janela.html).

   Sem biblioteca, como o mapa da Janela de Campo (campo-mapa.js): recorte fixo em Web Mercator (zoom 6), fundo Blue Marble
   da NASA GIBS (CSP img-src https://gibs.earthdata.nasa.gov), divisas do IBGE (divisas-ufs.svg, do próprio site) e, por cima,
   um SVG com as camadas:
   - avisos do INMET (área colorida pela gravidade, como no portal do INMET);
   - focos de fogo do NASA FIRMS das últimas 24 h;
   - traçado das rodovias BR-153, BR-060, BR-010 e BR-230 (IBGE BC250, assets/geo/rodovias-corredores.json).
   Os dados vêm de /api/transporte/alertas-publicos (resumo gravado pela rotina dos alertas a cada 15 min; sem viagem,
   posição ou cliente). Fonte fora do ar ou resumo atrasado aparecem como tal: o mapa nunca diz "sem risco" sem verificação. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).janelaTransporteMapa = factory();
})(this, function () {
  'use strict';
  var GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
  var FUNDO = { id: 'BlueMarble_ShadedRelief_Bathymetry', matriz: 'GoogleMapsCompatible_Level8', ext: 'jpeg' };
  var Z = 6, N = Math.pow(2, Z), TAM = 256;
  // Mesma região de backend/transporte/alertas/publico.py (REGIAO) e tools/gerar_rodovias.py: um teste confere.
  var CAIXA = { oeste: -56.5, leste: -45.5, norte: -1.0, sul: -19.6 };
  // Recorte do divisas-ufs.svg (campo-mapa.js CAIXA): a imagem do Brasil inteiro é posicionada sobre este recorte.
  var CAIXA_DIVISAS = { oeste: -75, leste: -33, norte: 6, sul: -34 };
  var VERIFICACAO_ATRASADA_MIN = 40;  // a rotina roda a cada 15 min
  var COR = { potencial: '#facc15', perigo: '#f97316', grande_perigo: '#ef4444' };
  var ROTULO = { potencial: 'Perigo potencial', perigo: 'Perigo', grande_perigo: 'Grande perigo' };
  var ORDEM = { potencial: 1, perigo: 2, grande_perigo: 3 };
  var TIPO = { tempestade: 'Tempestade', chuva: 'Chuva forte', vento: 'Vento forte', geada: 'Geada', frio: 'Frio intenso', calor: 'Calor extremo',
    baixa_umidade: 'Umidade muito baixa', fogo: 'Fogo', outro: 'Alerta' };
  var CAMADAS = [['avisos', 'Avisos do INMET'], ['focos', 'Focos de fogo (24 h)'], ['rodovias', 'Rodovias']];

  function px(lon) { return (lon + 180) / 360 * TAM * N; }
  function py(lat) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(Math.PI / 4 + r / 2)) / Math.PI) / 2 * TAM * N; }
  var X0 = px(CAIXA.oeste), X1 = px(CAIXA.leste), Y0 = py(CAIXA.norte), Y1 = py(CAIXA.sul), LARG = X1 - X0, ALT = Y1 - Y0;
  var TILES = [];
  for (var tx = Math.floor(X0 / TAM); tx <= Math.floor((X1 - 1) / TAM); tx++)
    for (var ty = Math.floor(Y0 / TAM); ty <= Math.floor((Y1 - 1) / TAM); ty++) TILES.push([tx, ty]);

  function vigente(a) { return a.vigente === false ? 0 : 1; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function pct(v) { return (Math.round(v * 1000) / 1000) + '%'; }
  function r1(v) { return Math.round(v * 10) / 10; }
  /* (lat, lon) → coordenadas do SVG (viewBox 0 0 LARG ALT). */
  function xy(lat, lon) { return [r1(px(lon) - X0), r1(py(lat) - Y0)]; }
  function dentroDaCaixa(lat, lon) { return lat <= CAIXA.norte && lat >= CAIXA.sul && lon >= CAIXA.oeste && lon <= CAIXA.leste; }

  /* Hora de Brasília (UTC−3, sem horário de verão desde 2019), 'dd/mm hh:mm'. */
  function horaBR(iso) {
    var t = Date.parse(iso);
    if (isNaN(t)) return '';
    var d = new Date(t - 3 * 3600000).toISOString();
    return d.slice(8, 10) + '/' + d.slice(5, 7) + ' ' + d.slice(11, 16);
  }

  /* ok | atrasado | sem_dados. Atrasado quando a última verificação passou de 40 min. */
  function estadoDados(d, agora) {
    if (!d || !d.atualizado_em) return 'sem_dados';
    var t = Date.parse(d.atualizado_em);
    if (isNaN(t)) return 'sem_dados';
    return (agora.getTime() - t) / 60000 > VERIFICACAO_ATRASADA_MIN ? 'atrasado' : 'ok';
  }

  /* Camadas do SVG. `rodovias` é o JSON do IBGE; `ocultos` = { avisos: true, ... }. */
  function svgCamadas(d, rodovias, ocultos) {
    ocultos = ocultos || {};
    var s = '';
    if (!ocultos.avisos) {
      // os dos próximos dias embaixo, tracejados; entre os de agora, o mais grave por cima
      (d.avisos || []).slice().sort(function (a, b) {
        return (vigente(a) - vigente(b)) || ((ORDEM[a.gravidade] || 0) - (ORDEM[b.gravidade] || 0));
      }).forEach(function (a) {
        var cor = COR[a.gravidade] || COR.perigo, ja = vigente(a);
        (a.poligonos || []).forEach(function (anel) {
          s += '<polygon data-aviso="' + esc(a.id) + '" data-vigente="' + ja + '" points="' + anel.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ') +
            '" fill="' + cor + '" fill-opacity="' + (ja ? '.16' : '0') + '" stroke="' + cor + '" stroke-width="1.5" stroke-linejoin="round"' +
            (ja ? '' : ' stroke-dasharray="5 4"') + '><title>' + esc((TIPO[a.tipo] || 'Alerta') + ' · ' + (ROTULO[a.gravidade] || a.gravidade) + ' · ' +
            (ja ? 'até ' + horaBR(a.fim) : 'a partir de ' + horaBR(a.inicio))) + '</title></polygon>';
        });
      });
    }
    if (!ocultos.rodovias && rodovias) {
      rodovias.rodovias.forEach(function (r) {
        r.linhas.forEach(function (linha) {
          var pts = linha.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ');
          s += '<polyline points="' + pts + '" fill="none" stroke="#0b1220" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" opacity=".7"/>' +
            '<polyline data-rodovia="' + esc(r.sigla) + '" points="' + pts + '" fill="none" stroke="#f8fafc" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><title>' + esc(r.sigla) + '</title></polyline>';
        });
        var maior = r.linhas.slice().sort(function (a, b) { return b.length - a.length; })[0];
        if (maior && maior.length) {
          var meio = xy(maior[Math.floor(maior.length / 2)][0], maior[Math.floor(maior.length / 2)][1]);
          s += '<g class="jtm-rotulo" transform="translate(' + meio.join(',') + ')"><rect x="-21" y="-8" width="42" height="16" rx="3"/><text text-anchor="middle" y="4">' + esc(r.sigla) + '</text></g>';
        }
      });
    }
    if (!ocultos.focos) {
      (d.focos || []).forEach(function (f) {
        if (!dentroDaCaixa(f[0], f[1])) return;
        var c = xy(f[0], f[1]);
        s += '<circle cx="' + c[0] + '" cy="' + c[1] + '" r="2.6" fill="#ff3d00" stroke="#fff7ed" stroke-width=".8"/>';
      });
    }
    return s;
  }

  /* Linhas da tabela por rodovia: maior gravidade dos avisos que cruzam o traçado e focos a até 5 km. */
  function linhasRodovias(d) {
    var porId = {};
    (d.avisos || []).forEach(function (a) { porId[a.id] = a; });
    return (d.rodovias || []).map(function (r) {
      var avisos = (r.avisos || []).map(function (id) { return porId[id]; }).filter(Boolean);
      return { sigla: r.sigla, gravidade: r.gravidade || '', proxima: r.gravidade_proxima || '', proximoInicio: r.proximo_inicio || '',
        avisos: avisos.filter(function (a) { return vigente(a); }), focos: r.focos_5km || 0 };
    });
  }

  function etiqueta(g) {
    if (!g) return '<span class="jtm-tag jtm-tag-ok">sem aviso</span>';
    return '<span class="jtm-tag" style="--g:' + (COR[g] || COR.perigo) + '">' + esc(ROTULO[g] || g) + '</span>';
  }

  function tabelaRodovias(d) {
    var linhas = linhasRodovias(d);
    if (!linhas.length) return '';
    return '<div class="jtm-rolagem"><table class="jtm-tabela"><thead><tr><th>Rodovia</th><th>Aviso do INMET no traçado</th><th>Focos a até ' +
      esc(d.raio_fogo_km || 5) + ' km (24 h)</th></tr></thead><tbody>' + linhas.map(function (l) {
        var tipos = l.avisos.map(function (a) { return TIPO[a.tipo] || 'Alerta'; }).filter(function (t, i, arr) { return arr.indexOf(t) === i; });
        return '<tr><th scope="row">' + esc(l.sigla) + '</th><td>' + etiqueta(l.gravidade) + (tipos.length ? ' <span class="jtm-fraco">' + esc(tipos.join(', ')) + '</span>' : '') +
          (l.proxima ? '<div class="jtm-fraco">' + esc(ROTULO[l.proxima] || l.proxima) + ' a partir de ' + esc(horaBR(l.proximoInicio)) + '</div>' : '') + '</td><td>' + (l.focos ? '<b>' + l.focos + '</b>' : '0') + '</td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  function listaAvisos(avisos, vazio) {
    if (!avisos.length) return '<p class="jtm-fraco">' + vazio + '</p>';
    return '<ul class="jtm-avisos">' + avisos.map(function (a) {
      return '<li style="--g:' + (COR[a.gravidade] || COR.perigo) + '"><div><b>' + esc(TIPO[a.tipo] || 'Alerta') + '</b> ' + etiqueta(a.gravidade) + '</div>' +
        '<small>de ' + esc(horaBR(a.inicio)) + ' até ' + esc(horaBR(a.fim)) + ' (horário de Brasília)</small>' +
        ((a.riscos || a.instrucoes) ? '<details><summary>Riscos e o que fazer</summary>' + (a.riscos ? '<p>' + esc(a.riscos) + '</p>' : '') +
          (a.instrucoes ? '<p><b>' + esc(a.instrucoes) + '</b></p>' : '') + '</details>' : '') +
        (/^https:\/\//.test(a.link || '') ? '<a class="og-link" href="' + esc(a.link) + '" target="_blank" rel="noopener noreferrer">Ver no portal do INMET</a>' : '') + '</li>';
    }).join('') + '</ul>';
  }

  var ROTULO_FONTE = { inmet: 'INMET', firms: 'NASA FIRMS' };
  var ESTADO_FONTE = { ok: 'ok', indisponivel: 'indisponível', desligada: 'desligada' };

  /* Cabeçalho: estado de cada fonte e da verificação. Devolve '' só quando tudo está em dia. */
  function avisosEstado(d, agora) {
    var est = estadoDados(d, agora), saida = [];
    if (est === 'sem_dados') return ['A verificação automática ainda não rodou. Sem verificação, a falta de alerta não quer dizer que não há risco.'];
    if (est === 'atrasado') saida.push('A última verificação foi em ' + horaBR(d.atualizado_em) + ' (o normal é a cada 15 min).');
    Object.keys(d.fontes || {}).forEach(function (k) {
      var e = d.fontes[k].estado;
      if (e !== 'ok') saida.push((ROTULO_FONTE[k] || k) + ' ' + (ESTADO_FONTE[e] || e) + ' na última verificação: a falta de ' +
        (k === 'firms' ? 'focos' : 'avisos') + ' no mapa não quer dizer que não há risco.');
    });
    return saida;
  }

  function painel(d, agora) {
    var ja = (d.avisos || []).filter(function (a) { return vigente(a); }), depois = (d.avisos || []).filter(function (a) { return !vigente(a); });
    var chips = Object.keys(d.fontes || {}).map(function (k) {
      var e = d.fontes[k].estado;
      return '<span class="jtm-fonte">' + esc(ROTULO_FONTE[k] || k) + ' <span class="jtm-tag ' + (e === 'ok' ? 'jtm-tag-ok' : 'jtm-tag-erro') + '">' + esc(ESTADO_FONTE[e] || e) + '</span></span>';
    }).join('');
    var avisos = avisosEstado(d, agora).map(function (t) { return '<p class="jtm-alerta" role="status">' + esc(t) + '</p>'; }).join('');
    return '<div class="jtm-fontes">' + chips + (d.atualizado_em ? '<span class="jtm-fraco">verificado em ' + esc(horaBR(d.atualizado_em)) + '</span>' : '') + '</div>' + avisos +
      '<h3 class="jtm-titulo">Por rodovia</h3>' + tabelaRodovias(d) +
      '<h3 class="jtm-titulo">Avisos do INMET valendo agora <span class="jtm-fraco">(' + ja.length + ')</span></h3>' +
        listaAvisos(ja, 'Nenhum aviso do INMET valendo agora na região.') +
      (depois.length ? '<h3 class="jtm-titulo">Próximos dias <span class="jtm-fraco">(' + depois.length + '; tracejados no mapa)</span></h3>' +
        listaAvisos(depois, '') : '');
  }

  var CREDITOS = 'Avisos: INMET (avisos meteorológicos, apiprevmet3.inmet.gov.br). Focos de fogo: NASA FIRMS, sensores VIIRS dos satélites NOAA-20 e NOAA-21 (dados CC0). ' +
    'Rodovias: IBGE, Base Cartográfica Contínua 1:250.000 (BC250) 2023, traçado simplificado e ilustrativo. Divisas: IBGE, Malha Municipal Digital 2025, simplificadas; o IBGE não define os limites. ' +
    'Imagem de fundo: NASA Blue Marble (NASA GIBS). Licenças do IBGE compatíveis com CC BY 4.0. ' +
    'Este mapa não substitui a Defesa Civil, a PRF nem o DNIT: interdição de rodovia não tem fonte oficial em tempo real e não aparece aqui.';

  function montar(el, op) {
    if (!el || typeof document === 'undefined') return;
    var ocultos = {}, dados = null, rodovias = null;
    var divisas = op.divisas ? (function () {
      var l = (px(CAIXA_DIVISAS.oeste) - X0) / LARG * 100, t = (py(CAIXA_DIVISAS.norte) - Y0) / ALT * 100;
      var w = (px(CAIXA_DIVISAS.leste) - px(CAIXA_DIVISAS.oeste)) / LARG * 100, h = (py(CAIXA_DIVISAS.sul) - py(CAIXA_DIVISAS.norte)) / ALT * 100;
      return '<img class="jtm-divisas" src="' + esc(op.divisas) + '" alt="" decoding="async" style="left:' + pct(l) + ';top:' + pct(t) + ';width:' + pct(w) + ';height:' + pct(h) + '">';
    })() : '';
    el.innerHTML =
      '<div class="jtm">' +
        '<div class="jtm-mapa-col">' +
          '<div class="mapa-opcoes" role="group" aria-label="Camadas do mapa">' + CAMADAS.map(function (c) {
            return '<label class="og-consentimento"><input type="checkbox" data-jtm-camada="' + c[0] + '" checked><span>' + c[1] + '</span></label>';
          }).join('') + '</div>' +
          '<figure class="mapa-satelite jtm-mapa" style="aspect-ratio:' + Math.round(LARG) + '/' + Math.round(ALT) + '">' +
            '<div class="mapa-palco" role="img" aria-label="Mapa de Goiás, Tocantins e Pará com os avisos do INMET, os focos de fogo e as rodovias BR-153, BR-060, BR-010 e BR-230">' +
              '<div class="mapa-camada">' + TILES.map(function (t) {
                return '<img alt="" decoding="async" referrerpolicy="no-referrer" src="' + GIBS + FUNDO.id + '/default/' + FUNDO.matriz + '/' + Z + '/' + t[1] + '/' + t[0] + '.' + FUNDO.ext + '" style="left:' +
                  pct((t[0] * TAM - X0) / LARG * 100) + ';top:' + pct((t[1] * TAM - Y0) / ALT * 100) + ';width:' + pct(TAM / LARG * 100) + ';height:' + pct(TAM / ALT * 100) + '">';
              }).join('') + '</div>' + divisas +
              '<svg class="jtm-svg" viewBox="0 0 ' + r1(LARG) + ' ' + r1(ALT) + '" preserveAspectRatio="none" aria-hidden="true" data-jtm-svg></svg>' +
            '</div>' +
            '<figcaption class="mapa-hora" data-jtm-hora aria-live="polite">carregando…</figcaption>' +
          '</figure>' +
          '<div class="jtm-legenda" aria-hidden="true">' + ['potencial', 'perigo', 'grande_perigo'].map(function (g) {
            return '<span><i style="background:' + COR[g] + '"></i>' + ROTULO[g] + '</span>';
          }).join('') + '<span><i class="jtm-futuro"></i>Próximos dias</span><span><i class="jtm-foco"></i>Foco de fogo</span><span><i class="jtm-via"></i>Rodovia</span></div>' +
          '<details class="mapa-creditos"><summary>Créditos e fontes</summary><p>' + esc(CREDITOS) + '</p></details>' +
        '</div>' +
        '<div class="jtm-painel" data-jtm-painel aria-live="polite"><p class="jtm-fraco">Carregando os alertas…</p></div>' +
      '</div>';
    var svg = el.querySelector('[data-jtm-svg]'), alvo = el.querySelector('[data-jtm-painel]'), hora = el.querySelector('[data-jtm-hora]');
    function desenhar() {
      svg.innerHTML = svgCamadas(dados || {}, rodovias, ocultos);
      if (dados) {
        alvo.innerHTML = painel(dados, new Date());
        hora.textContent = dados.atualizado_em ? 'verificado ' + horaBR(dados.atualizado_em) : 'sem verificação';
      }
    }
    el.querySelectorAll('[data-jtm-camada]').forEach(function (c) {
      c.addEventListener('change', function () { ocultos[c.getAttribute('data-jtm-camada')] = !c.checked; desenhar(); });
    });
    var imgDiv = el.querySelector('.jtm-divisas');
    if (imgDiv) imgDiv.addEventListener('error', function () { imgDiv.hidden = true; });
    el.querySelectorAll('.mapa-camada img').forEach(function (img) {
      img.addEventListener('error', function () { img.style.visibility = 'hidden'; });  // sem a imagem da NASA, as camadas seguem sobre o fundo escuro
    });
    if (op.rodovias) {
      fetch(op.rodovias).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (j) { rodovias = j; desenhar(); }).catch(function () { rodovias = null; });
    }
    function buscar() {
      fetch(op.origem, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (j) { dados = j; desenhar(); })
        .catch(function () {
          if (dados) return;  // mantém o último resumo com o carimbo de hora; o estado "atrasado" aparece sozinho
          hora.textContent = 'indisponível';
          alvo.innerHTML = '<p class="jtm-alerta" role="status">Os alertas estão indisponíveis no momento. Sem verificação, a falta de alerta não quer dizer que não há risco: confira o portal do INMET (avisos.inmet.gov.br).</p>';
        });
    }
    buscar();
    setInterval(buscar, 5 * 60000);  // a API tem cache de 5 min
  }

  function iniciar() {
    var el = document.querySelector('[data-janela-transporte-mapa]');
    if (el) montar(el, { origem: el.getAttribute('data-origem'), rodovias: el.getAttribute('data-rodovias'), divisas: el.getAttribute('data-divisas') });
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
  }
  return { CAIXA: CAIXA, TILES: TILES, xy: xy, horaBR: horaBR, estadoDados: estadoDados, svgCamadas: svgCamadas, linhasRodovias: linhasRodovias,
    avisosEstado: avisosEstado, painel: painel, LARG: LARG, ALT: ALT };
});
