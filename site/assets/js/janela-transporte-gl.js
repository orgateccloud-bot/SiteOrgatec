/* Janela do Transporte: mapa interativo (MapLibre GL JS 4.7.1, hospedado em assets/vendor/maplibre-gl-4.7.1/, versão "csp").

   Usado por janela-transporte-mapa.js quando o navegador tem WebGL; sem ele, ou se a biblioteca não carregar, fica o mapa em SVG.
   A biblioteca (~1 MB) só é baixada quando o mapa chega perto da tela. Camadas:
   - fundo NASA Blue Marble e satélite GOES-East ao vivo (cor real ou nuvens), com os últimos 12 quadros de 10 min para animar;
   - chuva estimada por satélite (NASA IMERG, dia de anteontem: o produto diário sai com cerca de 2 dias);
   - avisos do INMET, manchas e focos de fogo (NASA FIRMS), rodovias do IBGE (federais, estaduais e, a pedido, locais);
   - chuva forte prevista no Sul nas próximas 48 h (MET Norway, gravada pela rotina dos alertas; a previsão deles para o Brasil
     não traz trovoada nem rajada, então o mapa não fala em tempestade por ela);
   - toque num ponto do estado: avisos ali e a previsão do MET Norway para o ponto (pela API do site, nunca direto do navegador).
   A previsão é de modelo numérico e o mapa diz isso: não substitui o aviso oficial do INMET nem a Defesa Civil. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).janelaTransporteGL = factory();
})(this, function () {
  'use strict';
  var GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
  var QUADROS = 12, PASSO_QUADRO = 600000, ATRASO_GOES = 3600000;  // GOES-East a cada 10 min, publicado com ~50 min de atraso
  var SAT = { cor: ['GOES-East_ABI_GeoColor', 'GoogleMapsCompatible_Level7', 7, 1], ir: ['GOES-East_ABI_Band13_Clean_Infrared', 'GoogleMapsCompatible_Level6', 6, 0.8] };
  var COR = { potencial: '#facc15', perigo: '#f97316', grande_perigo: '#ef4444' };
  var COR_TEMPORAL = { forte: '#a855f7', muito_forte: '#7e22ce' };
  var NIVEL_TEMPORAL = { forte: 'Chuva forte prevista', muito_forte: 'Chuva muito forte prevista' };
  var BRASIL = [[-74.5, -34.0], [-34.5, 5.5]];  // [[oeste, sul], [leste, norte]], mesmo recorte de publico.py
  var SEMANA = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
  var CREDITO_MAPA = 'Imagens: NASA GIBS · Avisos: INMET · Focos: NASA FIRMS · Malha: IBGE · Previsão: MET Norway';
  var TEXTOS = {
    'CooperativeGesturesHandler.WindowsHelpText': 'Use Ctrl + rolagem para aproximar o mapa',
    'CooperativeGesturesHandler.MacHelpText': 'Use ⌘ + rolagem para aproximar o mapa',
    'CooperativeGesturesHandler.MobileHelpText': 'Use dois dedos para mover o mapa',
    'NavigationControl.ZoomIn': 'Aproximar', 'NavigationControl.ZoomOut': 'Afastar', 'NavigationControl.ResetBearing': 'Voltar ao norte',
    'AttributionControl.ToggleAttribution': 'Créditos do mapa', 'AttributionControl.MapFeedback': 'Corrigir o mapa', 'Popup.Close': 'Fechar',
    'Map.Title': 'Mapa', 'ScaleControl.Meters': 'm', 'ScaleControl.Kilometers': 'km'
  };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function ll(p) { return [p[1], p[0]]; }  // os arquivos guardam (lat, lon); o MapLibre quer (lon, lat)
  function colecao(features) { return { type: 'FeatureCollection', features: features }; }
  function horaBR(iso) {
    var t = Date.parse(iso);
    if (isNaN(t)) return '';
    var d = new Date(t - 3 * 3600000).toISOString();
    return d.slice(8, 10) + '/' + d.slice(5, 7) + ' ' + d.slice(11, 16);
  }
  function diaBR(t) { return new Date(t - 3 * 3600000).toISOString().slice(0, 10); }

  /* ---------- GeoJSON (funções puras, testadas em tests/js/janela-transporte-gl.test.js) ---------- */
  function geoLinhas(rodovias) {
    return colecao((rodovias || []).reduce(function (fs, r) {
      var federal = r.sigla.indexOf('BR-') === 0;
      return fs.concat(r.linhas.map(function (l) { return { type: 'Feature', properties: { sigla: r.sigla, federal: federal }, geometry: { type: 'LineString', coordinates: l.map(ll) } }; }));
    }, []));
  }
  function geoLocais(locais) {
    return colecao(((locais || {}).linhas || []).map(function (l) { return { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: l.map(ll) } }; }));
  }
  function geoAvisos(avisos) {
    return colecao((avisos || []).reduce(function (fs, a) {
      return fs.concat((a.poligonos || []).map(function (anel) {
        return { type: 'Feature', properties: { id: a.id, cor: COR[a.gravidade] || COR.perigo, vigente: a.vigente !== false }, geometry: { type: 'Polygon', coordinates: [anel.map(ll)] } };
      }));
    }, []));
  }
  /* Manchas de fogo: cada célula de 0,25° vira um ponto no centro, com o número de focos. */
  function geoCalor(nac) {
    var passo = (nac || {}).passo_calor || 0.25;
    return colecao(((nac || {}).calor || []).map(function (c) { return { type: 'Feature', properties: { n: c[2] }, geometry: { type: 'Point', coordinates: [c[1] + passo / 2, c[0] + passo / 2] } }; }));
  }
  function geoPontos(lista) { return colecao((lista || []).map(function (p) { return { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: ll(p) } }; })); }
  function geoUfs(ufs) {
    return colecao((ufs || []).reduce(function (fs, e) {
      return fs.concat(e.aneis.map(function (a) { return { type: 'Feature', properties: { uf: e.uf }, geometry: { type: 'Polygon', coordinates: [a.map(ll)] } }; }));
    }, []));
  }
  /* Chuva forte prevista no Sul: só as células com chuva forte, em quadrados de `passo` graus. */
  function geoTemporal(t) {
    if (!t || t.estado === 'indisponivel' && !(t.pontos || []).length) return colecao([]);
    var m = (t.passo || 0.75) / 2;
    return colecao((t.pontos || []).filter(function (p) { return p[3]; }).map(function (p) {
      var s = p[0] - m, n = p[0] + m, w = p[1] - m, e = p[1] + m;
      return { type: 'Feature', properties: { nivel: p[3], uf: p[2], inicio: p[4] || '' }, geometry: { type: 'Polygon', coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] } };
    }));
  }
  /* Os últimos 12 horários do GOES-East já publicados (múltiplos de 10 min, com 1 h de folga), do mais antigo ao mais novo. */
  function temposSatelite(agoraMs) {
    var fim = Math.floor((agoraMs - ATRASO_GOES) / PASSO_QUADRO) * PASSO_QUADRO, saida = [];
    for (var i = QUADROS - 1; i >= 0; i--) saida.push(new Date(fim - i * PASSO_QUADRO).toISOString().slice(0, 16) + ':00Z');
    return saida;
  }
  /* O ponto vai à API arredondado a 0,1°: vizinhos recebem a mesma resposta, que a CDN guarda. */
  function pontoArredondado(lat, lon) { return [Math.round(lat * 10) / 10, Math.round(lon * 10) / 10]; }

  function rotuloDia(chave, agoraMs) {
    var hoje = diaBR(agoraMs), amanha = diaBR(agoraMs + 86400000);
    if (chave === hoje) return 'Hoje';
    if (chave === amanha) return 'Amanhã';
    return SEMANA[new Date(chave + 'T12:00:00Z').getUTCDay()] + ' ' + chave.slice(8, 10);
  }
  /* Balão da previsão (resposta de GET /api/transporte/previsao). */
  function htmlPrevisao(p, agoraMs) {
    if (!p || !(p.dias || []).length) return '<p class="jtg-fraco">Previsão indisponível agora.</p>';
    var rot = p.rotulos || {}, hoje = diaBR(agoraMs);
    var horas = (p.horas || []).filter(function (h, i) { return i % 2 === 0; }).slice(0, 6);
    var dias = p.dias.filter(function (d) { return d.dia >= hoje; }).slice(0, 4);
    return '<p class="jtg-prev-titulo">Previsão para este ponto</p>' +
      (horas.length ? '<div class="jtg-horas">' + horas.map(function (h) {
        return '<div class="jtg-cat-' + esc(h.tempo) + '"><small>' + esc(horaBR(h.hora).slice(6)) + '</small><b>' + (h.temp == null ? '–' : Math.round(h.temp) + '°') + '</b>' +
          '<span>' + esc(rot[h.tempo] || '') + '</span>' + (h.chuva ? '<span>' + esc(String(h.chuva).replace('.', ',')) + ' mm</span>' : '') + '</div>';
      }).join('') + '</div>' : '') +
      '<ul class="jtg-dias">' + dias.map(function (d) {
        return '<li class="jtg-cat-' + esc(d.tempo) + '"><b>' + esc(rotuloDia(d.dia, agoraMs)) + '</b><span>' + esc(rot[d.tempo] || '') + (d.trovoada && d.tempo !== 'trovoada' ? ', com trovoada' : '') + '</span>' +
          '<span>' + (d.min == null ? '' : d.min + '° a ' + d.max + '°') + '</span><span>' + esc(String(d.chuva).replace('.', ',')) + ' mm' +
          (d.vento_max == null ? '' : ' · vento até ' + d.vento_max + ' km/h') + '</span></li>';
      }).join('') + '</ul>' +
      '<p class="jtg-fraco">Previsão de modelo numérico, não é aviso oficial. <a class="og-link" href="https://api.met.no/doc/License" target="_blank" rel="noopener noreferrer">Dados do MET Norway</a> (CC BY 4.0)' +
      (p.atualizado_em ? ', rodada de ' + esc(horaBR(p.atualizado_em)) : '') + '.</p>';
  }

  /* WebGL disponível (o mapa em SVG fica para quem não tem). */
  function suportado(doc) {
    try {
      var c = (doc || document).createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
    } catch (e) { return false; }
  }
  var carregando = null;
  /* Baixa a biblioteca uma vez: a folha de estilo e o script do próprio site (CSP script-src 'self'). */
  function carregar(base) {
    if (carregando) return carregando;
    var abs = new URL(base, location.href).href;
    carregando = new Promise(function (ok, falha) {
      if (window.maplibregl) { ok(window.maplibregl); return; }
      var css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = abs + 'maplibre-gl.css';
      document.head.appendChild(css);
      var s = document.createElement('script');
      s.src = abs + 'maplibre-gl-csp.js'; s.async = true;
      s.onload = function () {
        if (!window.maplibregl) { falha(new Error('maplibre')); return; }
        window.maplibregl.setWorkerUrl(abs + 'maplibre-gl-csp-worker.js');
        ok(window.maplibregl);
      };
      s.onerror = function () { falha(new Error('maplibre')); };
      document.head.appendChild(s);
    });
    return carregando;
  }

  /* Cria o mapa dentro de `caixa`. op = { previsao: URL da API ou '', aoEscolherUf(uf), aoMarcarRodovia(sigla), avisoPorId(id) }.
     Devolve { desenhar(estado), mapa }. estado = { uf, caixaUf, ufs, federais, rodovias, locais, focosPerto, nac, avisos, ocultos, rodovia }. */
  function criar(caixa, op) {
    var gl = window.maplibregl, calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    caixa.innerHTML = '<div class="jtg-mapa" data-jtg-mapa></div>' +
      '<div class="jtg-tempo">' +
        '<div class="campo-abas" role="group" aria-label="Imagem de satélite">' + [['cor', 'Satélite'], ['ir', 'Nuvens'], ['', 'Sem satélite']].map(function (s) {
          return '<button type="button" class="campo-aba" data-jtg-sat="' + s[0] + '" aria-pressed="' + (s[0] === 'cor') + '">' + s[1] + '</button>';
        }).join('') + '</div>' +
        '<button type="button" class="jtm-limpar" data-jtg-play aria-pressed="false">▶ Animar 2 h</button>' +
        '<input type="range" min="0" max="' + (QUADROS - 1) + '" step="1" value="' + (QUADROS - 1) + '" data-jtg-quadro aria-label="Horário da imagem de satélite">' +
        '<output class="jtg-fraco" data-jtg-hora></output>' +
      '</div>';
    var alvo = caixa.querySelector('[data-jtg-mapa]'), saida = caixa.querySelector('[data-jtg-hora]'), barra = caixa.querySelector('[data-jtg-quadro]'), play = caixa.querySelector('[data-jtg-play]');
    var mapa = new gl.Map({
      container: alvo, center: [-52, -15], zoom: 3.4, minZoom: 2.5, maxZoom: 12, maxBounds: [[-100, -50], [-10, 18]], cooperativeGestures: true, locale: TEXTOS,
      attributionControl: { compact: true }, fadeDuration: 0, dragRotate: false, pitchWithRotate: false, touchPitch: false,
      style: { version: 8, sources: { base: { type: 'raster', tileSize: 256, maxzoom: 8, attribution: CREDITO_MAPA,
        tiles: [GIBS + 'BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg'] } },
        layers: [{ id: 'base', type: 'raster', source: 'base' }] }
    });
    mapa.touchZoomRotate.disableRotation();
    if (window.ResizeObserver) new ResizeObserver(function () { mapa.resize(); }).observe(alvo);  // a coluna muda de largura com o painel
    mapa.addControl(new gl.NavigationControl({ showCompass: false }), 'top-right');
    mapa.addControl(new gl.ScaleControl({ unit: 'metric' }), 'bottom-left');
    var pronto = false, pendente = null, ultimo = {}, marcadores = [], popup = null, cachePrev = {};
    var sat = 'cor', quadro = QUADROS - 1, tempos = temposSatelite(Date.now()), carregados = 0, tocando = null;
    var anteontem = new Date(Date.now() - 2 * 86400000).toISOString().slice(0, 10);

    function camadaSat(i) {
      var c = SAT[sat];
      mapa.addSource('sat' + i, { type: 'raster', tileSize: 256, maxzoom: c[2], tiles: [GIBS + c[0] + '/default/' + tempos[i] + '/' + c[1] + '/{z}/{y}/{x}.png'] });
      mapa.addLayer({ id: 'sat' + i, type: 'raster', source: 'sat' + i, paint: { 'raster-opacity': i === quadro ? c[3] : 0, 'raster-fade-duration': 0 } }, 'chuva');
    }
    /* Só o quadro mais novo é baixado de início; os outros 11, quando a pessoa pede a animação. */
    function montarSatelite(todos) {
      for (var i = 0; i < QUADROS; i++) { if (mapa.getLayer('sat' + i)) mapa.removeLayer('sat' + i); if (mapa.getSource('sat' + i)) mapa.removeSource('sat' + i); }
      carregados = 0;
      if (!sat) return;
      tempos = temposSatelite(Date.now());
      for (var k = todos ? 0 : QUADROS - 1; k < QUADROS; k++) camadaSat(k);
      carregados = todos ? QUADROS : 1;
    }
    function mostrarQuadro(i) {
      quadro = i; barra.value = String(i);
      saida.textContent = sat ? 'Imagem de ' + horaBR(tempos[i]) + ' (Brasília)' : 'Sem imagem de satélite';
      for (var k = 0; k < QUADROS; k++) if (mapa.getLayer('sat' + k)) mapa.setPaintProperty('sat' + k, 'raster-opacity', k === i ? SAT[sat][3] : 0);
    }
    function parar() { if (tocando) { clearInterval(tocando); tocando = null; } play.setAttribute('aria-pressed', 'false'); play.textContent = '▶ Animar 2 h'; }
    function animar() {
      if (!sat) return;
      if (carregados < QUADROS) montarSatelite(true);
      play.setAttribute('aria-pressed', 'true'); play.textContent = '❚❚ Pausar';
      tocando = setInterval(function () { mostrarQuadro((quadro + 1) % QUADROS); }, 500);
    }
    play.addEventListener('click', function () { if (tocando) parar(); else animar(); });
    barra.addEventListener('input', function () {
      parar();
      if (sat && carregados < QUADROS) montarSatelite(true);
      mostrarQuadro(Number(barra.value));
    });
    caixa.querySelectorAll('[data-jtg-sat]').forEach(function (b) {
      b.addEventListener('click', function () {
        caixa.querySelectorAll('[data-jtg-sat]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        parar(); sat = b.getAttribute('data-jtg-sat'); quadro = QUADROS - 1;
        montarSatelite(false); mostrarQuadro(quadro);
        barra.disabled = play.disabled = !sat;
      });
    });

    mapa.on('load', function () {
      var vazio = colecao([]);
      mapa.addSource('chuva', { type: 'raster', tileSize: 256, maxzoom: 6, tiles: [GIBS + 'IMERG_Precipitation_Rate/default/' + anteontem + '/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png'] });
      mapa.addLayer({ id: 'chuva', type: 'raster', source: 'chuva', layout: { visibility: 'none' }, paint: { 'raster-opacity': 0.75 } });
      mapa.addSource('temporal', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'temporal', type: 'fill', source: 'temporal', paint: { 'fill-color': ['match', ['get', 'nivel'], 'muito_forte', COR_TEMPORAL.muito_forte, COR_TEMPORAL.forte],
        'fill-opacity': ['match', ['get', 'nivel'], 'muito_forte', 0.45, 0.25] } });
      mapa.addLayer({ id: 'temporal-linha', type: 'line', source: 'temporal', filter: ['==', ['get', 'nivel'], 'muito_forte'], paint: { 'line-color': '#e9d5ff', 'line-width': 1, 'line-opacity': 0.7 } });
      mapa.addSource('calor', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'calor', type: 'heatmap', source: 'calor', maxzoom: 10, paint: {
        'heatmap-weight': ['interpolate', ['linear'], ['get', 'n'], 0, 0, 40, 1], 'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 3, 0.8, 8, 2.2],
        'heatmap-radius': ['interpolate', ['exponential', 2], ['zoom'], 3, 5, 6, 26, 9, 150], 'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.78, 8, 0.4],
        'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(255,90,31,0)', 0.2, 'rgba(255,170,60,.55)', 0.5, 'rgba(255,90,31,.85)', 1, 'rgba(220,20,20,.95)'] } });
      mapa.addSource('avisos', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'avisos', type: 'fill', source: 'avisos', paint: { 'fill-color': ['get', 'cor'], 'fill-opacity': ['case', ['get', 'vigente'], 0.18, 0.07] } });
      mapa.addLayer({ id: 'avisos-linha', type: 'line', source: 'avisos', filter: ['get', 'vigente'], paint: { 'line-color': ['get', 'cor'], 'line-width': 1.6 } });
      mapa.addLayer({ id: 'avisos-futuro', type: 'line', source: 'avisos', filter: ['!', ['get', 'vigente']], paint: { 'line-color': ['get', 'cor'], 'line-width': 1.6, 'line-dasharray': [3, 2] } });
      mapa.addSource('ufs', { type: 'geojson', data: vazio, promoteId: 'uf' });
      mapa.addLayer({ id: 'ufs', type: 'fill', source: 'ufs', paint: { 'fill-color': '#fff', 'fill-opacity': ['case', ['boolean', ['feature-state', 'sobre'], false], 0.14, 0] } });
      mapa.addLayer({ id: 'ufs-linha', type: 'line', source: 'ufs', paint: { 'line-color': ['case', ['boolean', ['feature-state', 'marcada'], false], '#38bdf8', '#f8fafc'],
        'line-opacity': ['case', ['boolean', ['feature-state', 'marcada'], false], 1, 0.55], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, ['case', ['boolean', ['feature-state', 'marcada'], false], 2, 0.6], 8, ['case', ['boolean', ['feature-state', 'marcada'], false], 2.5, 1.4]] } });
      mapa.addSource('locais', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'locais', type: 'line', source: 'locais', paint: { 'line-color': '#cbd5e1', 'line-opacity': 0.55, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.4, 10, 1.4] } });
      mapa.addSource('rodovias', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'rodovias-borda', type: 'line', source: 'rodovias', filter: ['get', 'federal'], layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#0b1220', 'line-opacity': 0.65, 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 1.6, 9, 6] } });
      mapa.addLayer({ id: 'rodovias', type: 'line', source: 'rodovias', layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': ['case', ['get', 'federal'], '#f8fafc', '#cbd5e1'], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, ['case', ['get', 'federal'], 0.8, 0.4], 9, ['case', ['get', 'federal'], 3.2, 1.8]] } });
      mapa.addLayer({ id: 'rodovia-marcada', type: 'line', source: 'rodovias', filter: ['==', ['get', 'sigla'], ''], layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#38bdf8', 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 2.5, 9, 6] } });
      mapa.addLayer({ id: 'rodovias-alvo', type: 'line', source: 'rodovias', paint: { 'line-color': '#000', 'line-opacity': 0, 'line-width': 14 } });
      mapa.addSource('focos', { type: 'geojson', data: vazio });
      mapa.addLayer({ id: 'focos', type: 'circle', source: 'focos', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 2.2, 10, 6], 'circle-color': '#ff3d00', 'circle-stroke-color': '#fff7ed', 'circle-stroke-width': 0.8 } });
      montarSatelite(false); mostrarQuadro(quadro);
      // créditos recolhidos em tela estreita (o botão ⓘ abre): abertos, cobrem a base do mapa no celular
      var creditos = alvo.querySelector('.maplibregl-ctrl-attrib');
      if (creditos && alvo.clientWidth < 640) creditos.classList.remove('maplibregl-compact-show');
      pronto = true;
      if (pendente) desenhar(pendente);
    });
    // a imagem do GOES mais nova muda a cada 10 min: quem deixa a página aberta vê o satélite andar
    setInterval(function () { if (pronto && sat && !tocando && !document.hidden) { montarSatelite(false); quadro = QUADROS - 1; mostrarQuadro(quadro); } }, PASSO_QUADRO);

    function dados(fonte, valor, montar) {
      if (ultimo[fonte] === valor) return;  // só refaz o GeoJSON quando o dado muda
      ultimo[fonte] = valor;
      mapa.getSource(fonte).setData(montar(valor));
    }
    function ver(ids, visivel) { ids.forEach(function (id) { mapa.setLayoutProperty(id, 'visibility', visivel ? 'visible' : 'none'); }); }
    function rotulos(e) {
      marcadores.forEach(function (m) { m.remove(); });
      marcadores = [];
      var lista = [];
      if (!e.uf) lista = (e.ufs || []).map(function (u) { return [u.uf, [(u.caixa[1] + u.caixa[3]) / 2, (u.caixa[0] + u.caixa[2]) / 2], '']; });
      else if (e.rodovias && !e.ocultos.rodovias) {
        lista = e.rodovias.rodovias.filter(function (r) { return r.sigla.indexOf('BR-') === 0 || r.sigla === e.rodovia; }).slice(0, 40).map(function (r) {
          var meio = r.linhas[0][Math.floor(r.linhas[0].length / 2)];  // linhas vêm da maior para a menor
          return [r.sigla, ll(meio), r.sigla === e.rodovia ? ' jtg-rotulo-marcado' : ''];
        });
      }
      lista.forEach(function (x) {
        var el = document.createElement('div');
        el.className = 'jtg-rotulo' + x[2]; el.textContent = x[0];
        marcadores.push(new gl.Marker({ element: el }).setLngLat(x[1]).addTo(mapa));
      });
    }
    function desenhar(e) {
      if (!pronto) { pendente = e; return; }
      var o = e.ocultos || {}, mudouUf = ultimo.uf !== e.uf;
      dados('ufs', e.ufs, geoUfs);
      dados('calor', e.nac, geoCalor);
      dados('temporal', (e.nac || {}).temporal, geoTemporal);
      dados('avisos', e.avisos, geoAvisos);
      dados('rodovias', e.uf ? e.rodovias && e.rodovias.rodovias : e.federais && e.federais.rodovias, geoLinhas);
      dados('locais', e.uf && !o.locais ? e.locais : null, geoLocais);
      dados('focos', e.uf ? e.focosPerto : null, geoPontos);
      mapa.setFilter('rodovia-marcada', ['==', ['get', 'sigla'], e.rodovia || '']);
      ver(['avisos', 'avisos-linha', 'avisos-futuro'], !o.avisos);
      ver(['calor', 'focos'], !o.focos);
      ver(['rodovias', 'rodovias-borda', 'rodovia-marcada', 'rodovias-alvo'], !o.rodovias);
      ver(['locais'], !o.rodovias && !o.locais);
      ver(['chuva'], !o.chuva);
      ver(['temporal', 'temporal-linha'], !o.temporal);
      if (ultimo.marcada) mapa.setFeatureState({ source: 'ufs', id: ultimo.marcada }, { marcada: false });
      if (e.uf) mapa.setFeatureState({ source: 'ufs', id: e.uf }, { marcada: true });
      ultimo.marcada = e.uf;
      if (mudouUf || ultimo.rotulos !== (e.rodovias || e.ufs) || ultimo.marcadaSigla !== e.rodovia || ultimo.semRodovias !== !!o.rodovias) {
        rotulos(e);
        ultimo.rotulos = e.rodovias || e.ufs; ultimo.marcadaSigla = e.rodovia; ultimo.semRodovias = !!o.rodovias;
      }
      if (mudouUf) {
        ultimo.uf = e.uf;
        if (popup) popup.remove();
        var c = e.caixaUf, larga = alvo.clientWidth > 640;
        mapa.fitBounds(c ? [[c.oeste, c.sul], [c.leste, c.norte]] : BRASIL, { padding: larga ? 40 : 16, duration: calmo || ultimo.inicial === undefined ? 0 : 1200 });
        ultimo.inicial = true;
      }
      ultimo.estado = e;
    }

    /* ---------- toque e passar do mouse ---------- */
    var sobre = null;
    mapa.on('mousemove', function (ev) {
      var e = ultimo.estado || {}, f = mapa.queryRenderedFeatures(ev.point, { layers: e.uf ? ['rodovias-alvo'] : ['ufs'] })[0], uf = !e.uf && f ? f.properties.uf : null;
      if (sobre !== uf) {
        if (sobre) mapa.setFeatureState({ source: 'ufs', id: sobre }, { sobre: false });
        if (uf) mapa.setFeatureState({ source: 'ufs', id: uf }, { sobre: true });
        sobre = uf;
      }
      mapa.getCanvas().style.cursor = f ? 'pointer' : '';
    });
    mapa.on('click', function (ev) {
      var e = ultimo.estado || {};
      if (!e.uf) {
        var noUf = mapa.queryRenderedFeatures(ev.point, { layers: ['ufs'] })[0];
        if (noUf) op.aoEscolherUf(noUf.properties.uf);
        return;
      }
      var via = !(e.ocultos || {}).rodovias && mapa.queryRenderedFeatures(ev.point, { layers: ['rodovias-alvo'] })[0];
      if (via) { op.aoMarcarRodovia(via.properties.sigla); return; }
      balao(ev.lngLat, e);
    });
    function balao(lngLat, e) {
      var ids = {}, avisos = mapa.queryRenderedFeatures(mapa.project(lngLat), { layers: ['avisos'] }).map(function (f) { return f.properties.id; })
        .filter(function (id) { return !ids[id] && (ids[id] = 1); }).map(op.avisoPorId).filter(Boolean);
      var temporal = mapa.queryRenderedFeatures(mapa.project(lngLat), { layers: ['temporal'] })[0];
      var el = document.createElement('div');
      el.className = 'jtg-balao';
      el.innerHTML = (avisos.length ? avisos.map(function (a) {
        return '<p class="jtg-aviso" style="--g:' + (COR[a.gravidade] || COR.perigo) + '"><b>' + esc(op.nomeAviso(a)) + '</b><small>' +
          (a.vigente !== false ? 'Valendo agora, até ' + esc(horaBR(a.fim)) : 'De ' + esc(horaBR(a.inicio)) + ' até ' + esc(horaBR(a.fim))) + ' · INMET</small></p>';
      }).join('') : '<p class="jtg-fraco">Sem aviso do INMET neste ponto.</p>') +
        (temporal ? '<p class="jtg-aviso" style="--g:' + (COR_TEMPORAL[temporal.properties.nivel] || COR_TEMPORAL.forte) + '"><b>' + esc(NIVEL_TEMPORAL[temporal.properties.nivel] || 'Chuva forte prevista') +
          '</b><small>' + (temporal.properties.inicio ? 'a partir de ' + esc(horaBR(temporal.properties.inicio)) + ' · ' : '') + 'previsão MET Norway, próximas 48 h</small></p>' : '') +
        '<div data-jtg-prev>' + (op.previsao ? '<p class="jtg-fraco">Carregando a previsão…</p>' : '') + '</div>';
      if (popup) popup.remove();
      popup = new gl.Popup({ maxWidth: '320px', focusAfterOpen: false }).setLngLat(lngLat).setDOMContent(el).addTo(mapa);
      if (!op.previsao) return;
      var p = pontoArredondado(lngLat.lat, lngLat.lng), chave = p.join(','), alvoPrev = el.querySelector('[data-jtg-prev]');
      var pedido = cachePrev[chave] = cachePrev[chave] || fetch(op.previsao + '?lat=' + p[0] + '&lon=' + p[1]).then(function (r) {
        if (r.status === 404) return null;  // previsão desligada nesta instalação: o balão fica só com os avisos
        if (!r.ok) throw new Error(r.status);
        return r.json();
      });
      pedido.then(function (j) { alvoPrev.innerHTML = j ? htmlPrevisao(j, Date.now()) : ''; if (popup) popup.setDOMContent(el); })
        .catch(function () { delete cachePrev[chave]; alvoPrev.innerHTML = '<p class="jtg-fraco">Previsão indisponível agora. Tente de novo em instantes.</p>'; });
    }
    return { desenhar: desenhar, mapa: mapa };
  }

  return { suportado: suportado, carregar: carregar, criar: criar, geoLinhas: geoLinhas, geoLocais: geoLocais, geoAvisos: geoAvisos, geoCalor: geoCalor,
    geoPontos: geoPontos, geoUfs: geoUfs, geoTemporal: geoTemporal, temposSatelite: temposSatelite, pontoArredondado: pontoArredondado,
    htmlPrevisao: htmlPrevisao, rotuloDia: rotuloDia, QUADROS: QUADROS };
});
