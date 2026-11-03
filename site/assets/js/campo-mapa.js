/* Janela de Campo: mapa de satélite do Brasil com as imagens públicas da NASA GIBS (GOES-East da NOAA e IMERG),
   sem biblioteca. Recorte fixo em Web Mercator, zoom 4 (3 × 3 imagens de 256 px por camada), animação das últimas
   2 horas do infravermelho e os polos como botões. As imagens vêm direto da NASA para o navegador do visitante
   (CSP img-src https://gibs.earthdata.nasa.gov; a política de privacidade cita). */
(function (root) {
  'use strict';
  var GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
  var Z = 4, N = Math.pow(2, Z), TAM = 256;
  var CAIXA = { oeste: -75, leste: -33, norte: 6, sul: -34 };  // Brasil com folga
  var CAMADAS = {
    infravermelho: { rotulo: 'Nuvens (infravermelho)', id: 'GOES-East_ABI_Band13_Clean_Infrared', matriz: 'GoogleMapsCompatible_Level6', anima: true,
      legenda: 'Quanto mais branca a nuvem, mais fria e alta: nuvens brancas e densas indicam tempestade.' },
    cor: { rotulo: 'Cor real', id: 'GOES-East_ABI_GeoColor', matriz: 'GoogleMapsCompatible_Level7', anima: false,
      legenda: 'Imagem em cores naturais de dia; à noite, a NOAA usa o infravermelho no lugar.' }
  };
  var CHUVA = { id: 'IMERG_Precipitation_Rate', matriz: 'GoogleMapsCompatible_Level6' };
  // Litoral transparente. (Reference_Features_15m, com fronteiras, vem preto e opaco neste zoom: conferido em 02/11/2026.)
  var FRONTEIRAS = { id: 'Coastlines_15m', matriz: 'GoogleMapsCompatible_Level13' };
  var QUADROS = 12, PASSO_MIN = 10;

  function px(lon) { return (lon + 180) / 360 * TAM * N; }
  function py(lat) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(Math.PI / 4 + r / 2)) / Math.PI) / 2 * TAM * N; }
  var X0 = px(CAIXA.oeste), X1 = px(CAIXA.leste), Y0 = py(CAIXA.norte), Y1 = py(CAIXA.sul), LARG = X1 - X0, ALT = Y1 - Y0;
  var TILES = [];
  for (var tx = Math.floor(X0 / TAM); tx <= Math.floor((X1 - 1) / TAM); tx++)
    for (var ty = Math.floor(Y0 / TAM); ty <= Math.floor((Y1 - 1) / TAM); ty++) TILES.push([tx, ty]);

  function pct(v) { return (Math.round(v * 1000) / 1000) + '%'; }
  function url(camada, tempo, x, y) {
    return GIBS + camada.id + '/default/' + (tempo ? tempo + '/' : '') + camada.matriz + '/' + Z + '/' + y + '/' + x + '.png';
  }
  function grade(camada, tempo, classe) {
    var d = document.createElement('div');
    d.className = 'mapa-camada ' + (classe || '');
    TILES.forEach(function (t) {
      var img = document.createElement('img');
      img.alt = ''; img.decoding = 'async'; img.referrerPolicy = 'no-referrer';
      img.src = url(camada, tempo, t[0], t[1]);
      img.style.left = pct((t[0] * TAM - X0) / LARG * 100); img.style.top = pct((t[1] * TAM - Y0) / ALT * 100);
      img.style.width = pct(TAM / LARG * 100); img.style.height = pct(TAM / ALT * 100);
      img.onerror = function () {  // a NASA às vezes falha uma imagem isolada: tenta mais uma vez antes de esconder
        if (!img.dataset.retentou) { img.dataset.retentou = '1'; img.src = img.src + '?r=1'; } else img.style.visibility = 'hidden';
      };
      d.appendChild(img);
    });
    return d;
  }
  function isoMin(ms) { return new Date(ms).toISOString().slice(0, 16) + ':00Z'; }
  function horaBrasilia(iso) { var d = new Date(Date.parse(iso) - 3 * 3600000); return d.toISOString().slice(11, 16).replace(':', 'h'); }

  /* Último horário do infravermelho já publicado: a NASA responde 404 para horários ainda não processados. */
  function ultimoHorario(cb) {
    var base = Math.floor((Date.now() - 30 * 60000) / (PASSO_MIN * 60000)) * PASSO_MIN * 60000, tentativa = 0;
    (function testa() {
      var t = isoMin(base - tentativa * PASSO_MIN * 60000), img = new Image();
      img.referrerPolicy = 'no-referrer';
      img.onload = function () { cb(t); };
      img.onerror = function () { if (++tentativa < 18) testa(); else cb(null); };
      img.src = url(CAMADAS.infravermelho, t, TILES[4][0], TILES[4][1]);
    })();
  }

  var estadoMapa = null;

  function montar(el, op) {
    if (!el) return;
    var calmo = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.innerHTML =
      '<div class="mapa-controles">' +
        '<div class="campo-abas" role="group" aria-label="Camada do satélite">' + Object.keys(CAMADAS).map(function (k) {
          return '<button type="button" class="campo-aba" data-camada="' + k + '" aria-pressed="' + (k === 'infravermelho') + '">' + CAMADAS[k].rotulo + '</button>';
        }).join('') + '</div>' +
        '<label class="og-consentimento"><input type="checkbox" data-mapa-chuva><span>Chuva estimada de ontem (IMERG)</span></label>' +
      '</div>' +
      '<figure class="mapa-satelite" style="aspect-ratio:' + Math.round(LARG) + '/' + Math.round(ALT) + '">' +
        '<div class="mapa-palco" data-mapa-palco role="img" aria-label="Imagem de satélite do Brasil com os polos agrícolas da Janela de Campo"></div>' +
        '<div class="mapa-pontos" data-mapa-pontos></div>' +
        '<figcaption class="mapa-hora" data-mapa-hora aria-live="polite">carregando imagem…</figcaption>' +
      '</figure>' +
      '<div class="mapa-tempo" data-mapa-tempo hidden>' +
        '<button type="button" class="og-btn og-btn-contorno og-btn-md" data-mapa-play aria-pressed="false">Animar 2 h</button>' +
        '<input type="range" min="0" max="' + (QUADROS - 1) + '" value="' + (QUADROS - 1) + '" step="1" data-mapa-quadro aria-label="Horário da imagem">' +
      '</div>' +
      '<p class="text-xs text-tinta-fraca" data-mapa-legenda></p>' +
      '<p class="text-xs text-tinta-fraca">Imagens: NASA GIBS · NOAA GOES-East (infravermelho e cor real, atualizadas a cada 10 min, com cerca de 1 h de atraso) · NASA IMERG (chuva estimada, dia anterior). Litoral: NASA GIBS.</p>';
    var palco = el.querySelector('[data-mapa-palco]'), pontos = el.querySelector('[data-mapa-pontos]'), hora = el.querySelector('[data-mapa-hora]');
    var tempo = el.querySelector('[data-mapa-tempo]'), play = el.querySelector('[data-mapa-play]'), faixa = el.querySelector('[data-mapa-quadro]');
    var s = estadoMapa = { el: el, op: op, camada: 'infravermelho', horarios: [], quadros: {}, atual: QUADROS - 1, timer: null };

    var chuvaCamada = grade(CHUVA, 'default', 'mapa-chuva'); chuvaCamada.hidden = true;
    var fronteiras = grade(FRONTEIRAS, null, 'mapa-fronteiras');

    function mostrar(i) {
      s.atual = i; faixa.value = String(i);
      Object.keys(s.quadros).forEach(function (k) { s.quadros[k].hidden = Number(k) !== i; });
      if (s.camada === 'infravermelho' && s.horarios[i]) hora.textContent = 'Infravermelho · ' + horaBrasilia(s.horarios[i]) + ' (Brasília)';
    }
    function quadro(i) {
      if (!s.quadros[i]) { s.quadros[i] = grade(CAMADAS.infravermelho, s.horarios[i]); palco.insertBefore(s.quadros[i], chuvaCamada); }
      return s.quadros[i];
    }
    function parar() { if (s.timer) { clearInterval(s.timer); s.timer = null; } play.setAttribute('aria-pressed', 'false'); play.textContent = 'Animar 2 h'; }
    function animar() {
      for (var i = 0; i < QUADROS; i++) quadro(i);  // pré-carrega todos os quadros antes de girar
      play.setAttribute('aria-pressed', 'true'); play.textContent = 'Pausar';
      s.timer = setInterval(function () { mostrar((s.atual + 1) % QUADROS); }, 700);
    }
    function trocarCamada(k) {
      parar(); s.camada = k;
      Array.prototype.forEach.call(el.querySelectorAll('[data-camada]'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-camada') === k)); });
      Array.prototype.forEach.call(palco.querySelectorAll('.mapa-camada:not(.mapa-chuva):not(.mapa-fronteiras)'), function (d) { d.remove(); });
      s.quadros = {};
      el.querySelector('[data-mapa-legenda]').textContent = CAMADAS[k].legenda;
      if (k === 'cor') {
        palco.insertBefore(grade(CAMADAS.cor, 'default'), chuvaCamada);
        hora.textContent = 'Cor real · imagem mais recente';
        tempo.hidden = true;
      } else if (s.horarios.length) {
        quadro(QUADROS - 1); mostrar(QUADROS - 1); tempo.hidden = false;
      }
    }

    palco.appendChild(chuvaCamada); palco.appendChild(fronteiras);
    el.querySelector('[data-mapa-legenda]').textContent = CAMADAS.infravermelho.legenda;
    ultimoHorario(function (ultimo) {
      if (!ultimo) { hora.textContent = 'Imagem de satélite indisponível agora'; return; }
      var fim = Date.parse(ultimo);
      for (var i = QUADROS - 1; i >= 0; i--) s.horarios[i] = isoMin(fim - (QUADROS - 1 - i) * PASSO_MIN * 60000);
      if (s.camada === 'infravermelho') { quadro(QUADROS - 1); mostrar(QUADROS - 1); tempo.hidden = false; }
    });
    el.addEventListener('click', function (ev) {
      var c = ev.target.closest('[data-camada]');
      if (c) trocarCamada(c.getAttribute('data-camada'));
      if (ev.target.closest('[data-mapa-play]')) { if (s.timer) parar(); else animar(); }
      var p = ev.target.closest('[data-polo]');
      if (p && s.op.aoEscolher) s.op.aoEscolher(s.op.polos.filter(function (x) { return x.id === p.getAttribute('data-polo'); })[0]);
    });
    faixa.addEventListener('input', function () { parar(); quadro(Number(faixa.value)); mostrar(Number(faixa.value)); });
    el.querySelector('[data-mapa-chuva]').addEventListener('change', function (ev) { chuvaCamada.hidden = !ev.target.checked; });
    if (calmo) play.title = 'Animação desligada pela preferência de movimento reduzido; use o controle de horário.';
    if (calmo) play.hidden = true;

    pontos.innerHTML = op.polos.map(function (p) {
      var x = (px(p.lon) - X0) / LARG * 100, y = (py(p.lat) - Y0) / ALT * 100;
      return '<button type="button" class="mapa-polo" data-polo="' + p.id + '" style="left:' + pct(x) + ';top:' + pct(y) + '"><i aria-hidden="true"></i><span class="mapa-polo-nome">' + p.nome + '</span></button>';
    }).join('');
    atualizar();
  }

  /* Recolore os polos com o estado da operação escolhida (chamado pelo campo.js a cada troca). */
  function atualizar() {
    var s = estadoMapa;
    if (!s) return;
    s.op.polos.forEach(function (p) {
      var b = s.el.querySelector('[data-polo="' + p.id + '"]');
      if (!b) return;
      var est = s.op.estado(p);
      b.className = 'mapa-polo mapa-polo-' + est;
      b.querySelector('i').textContent = { ok: '✓', atencao: '!', evitar: '✕' }[est] || '';
      b.setAttribute('aria-label', s.op.rotulo(p));
      b.title = s.op.rotulo(p);
    });
  }

  (root.Orgatec = root.Orgatec || {}).campoMapa = { montar: montar, atualizar: atualizar, CAIXA: CAIXA, TILES: TILES };
})(typeof window !== 'undefined' ? window : this);
