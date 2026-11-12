/* Janela de Campo: mapa de satélite do Brasil com as imagens públicas da NASA GIBS (GOES-East da NOAA e IMERG),
   sem biblioteca. Recorte fixo em Web Mercator, zoom 4 (3 × 3 imagens de 256 px por camada), animação das últimas
   2 horas do infravermelho, divisas dos estados (SVG do próprio site, de tools/gerar_divisas_ufs.py) e os polos como
   botões. As imagens vêm direto da NASA para o navegador do visitante (CSP img-src https://gibs.earthdata.nasa.gov; a
   política de privacidade cita).

   Cada imagem tem a hora ou a data à vista; quando a NASA falha, um aviso diz isso e oferece "Tentar de novo"; a camada
   de chuva só é pedida quando o visitante a liga.

   Visual (12/11/2026): um cartão só, com a camada em controle segmentado, chuva e divisas em chaves, os polos com os mesmos
   glifos da página (cheio com ✓, vazado com !, cheio com ✕, pontilhado com –), o polo escolhido em destaque, a contagem dos
   polos por estado sobre a imagem, transição suave entre os quadros e linha do tempo com botão redondo. */
(function (root) {
  'use strict';
  var GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
  var Z = 4, N = Math.pow(2, Z), TAM = 256;
  var CAIXA = { oeste: -75, leste: -33, norte: 6, sul: -34 };  // Brasil com folga
  var CAMADAS = {
    infravermelho: { rotulo: 'Nuvens (infravermelho)', curto: 'Nuvens', id: 'GOES-East_ABI_Band13_Clean_Infrared', matriz: 'GoogleMapsCompatible_Level6', anima: true },
    cor: { rotulo: 'Cor real', curto: 'Cor real', id: 'GOES-East_ABI_GeoColor', matriz: 'GoogleMapsCompatible_Level7', anima: false }
  };
  /* Glifos de estado: o mesmo desenho da página (campo.js, glifoSvg), para o mapa e os cartões falarem a mesma língua. */
  var GLIFOS = {
    ok: '<circle cx="12" cy="12" r="11"/><path d="M7 12.5l3.2 3.2L17 8.8"/>',
    atencao: '<circle cx="12" cy="12" r="10"/><path d="M12 7v6"/><circle class="ponto" cx="12" cy="16.6" r="1.4"/>',
    evitar: '<circle cx="12" cy="12" r="11"/><path d="M8 8l8 8M16 8l-8 8"/>',
    sem: '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/>'
  };
  var ORDEM_ESTADOS = ['ok', 'atencao', 'evitar', 'sem'];
  var IC = {
    play: '<svg class="mapa-ic mapa-ic-play" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M8 5.5v13l11-6.5z"/></svg>',
    pausa: '<svg class="mapa-ic mapa-ic-pausa" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>'
  };
  function glifo(e) {
    var k = GLIFOS[e] ? e : 'sem';
    return '<svg class="glifo glifo-' + k + '" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + GLIFOS[k] + '</svg>';
  }
  /* Contagem dos polos por estado, na ordem favorável, com restrição, evitar e sem previsão; estado desconhecido conta como
     sem previsão e quem tem zero fica de fora. */
  function resumoDosPolos(estados) {
    var n = { ok: 0, atencao: 0, evitar: 0, sem: 0 };
    (estados || []).forEach(function (e) { n[GLIFOS[e] ? e : 'sem']++; });
    var texto = {
      ok: function (q) { return q === 1 ? '1 favorável' : q + ' favoráveis'; },
      atencao: function (q) { return q + ' com restrição'; },
      evitar: function (q) { return q + ' a evitar'; },
      sem: function (q) { return q + ' sem previsão'; }
    };
    return ORDEM_ESTADOS.filter(function (e) { return n[e] > 0; }).map(function (e) { return { estado: e, n: n[e], texto: texto[e](n[e]) }; });
  }
  var CHUVA = { id: 'IMERG_Precipitation_Rate', matriz: 'GoogleMapsCompatible_Level6' };
  // Litoral transparente. (Reference_Features_15m, com fronteiras, vem preto e opaco neste zoom: conferido em 02/11/2026.
  // A NASA GIBS não tem as divisas dos estados brasileiros: elas vêm do IBGE, em divisas-ufs.svg.)
  var FRONTEIRAS = { id: 'Coastlines_15m', matriz: 'GoogleMapsCompatible_Level13' };
  var QUADROS = 12, PASSO_MIN = 10;

  /* Escalas de cor das legendas, tiradas dos colormaps oficiais da NASA GIBS (consultados em 07/11/2026):
     gibs.earthdata.nasa.gov/colormaps/v1.3/Clean_Longwave_Infrared_Window_Band.xml (temperatura de brilho, °C) e
     .../GPM_Precipitation_Rate.xml (taxa de chuva, mm/h). No infravermelho: cinza para o quente (nuvens baixas e superfície);
     do ciano ao vermelho, topos cada vez mais frios. */
  var ESCALA_IR = { de: -90, ate: 50,
    paradas: [[-90, '#8c0d87'], [-80, '#e6e6e6'], [-70, '#1a0000'], [-60, '#ff1a00'], [-50, '#e6ff00'], [-40, '#00ea0a'], [-30, '#000073'],
      [-20, '#00f2f8'], [-10, '#aeaeae'], [0, '#949494'], [10, '#777777'], [20, '#606060'], [30, '#464646'], [40, '#2c2c2c'], [50, '#131313']],
    marcas: [-80, -60, -40, -20, 0, 40] };
  var ESCALA_CHUVA = [['#00991a', '0,2'], ['#4ec300', '0,5'], ['#e6ec00', '1,2'], ['#ff8117', '2,8'], ['#ff1313', '6,7'], ['#b50000', '16'], ['#580000', '38']];

  function px(lon) { return (lon + 180) / 360 * TAM * N; }
  function py(lat) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(Math.PI / 4 + r / 2)) / Math.PI) / 2 * TAM * N; }
  var X0 = px(CAIXA.oeste), X1 = px(CAIXA.leste), Y0 = py(CAIXA.norte), Y1 = py(CAIXA.sul), LARG = X1 - X0, ALT = Y1 - Y0;
  var TILES = [];
  for (var tx = Math.floor(X0 / TAM); tx <= Math.floor((X1 - 1) / TAM); tx++)
    for (var ty = Math.floor(Y0 / TAM); ty <= Math.floor((Y1 - 1) / TAM); ty++) TILES.push([tx, ty]);

  function pct(v) { return (Math.round(v * 1000) / 1000) + '%'; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function url(camada, tempo, x, y) {
    return GIBS + camada.id + '/default/' + (tempo ? tempo + '/' : '') + camada.matriz + '/' + Z + '/' + y + '/' + x + '.png';
  }
  /* Uma camada = 3 × 3 imagens. aoFalhar roda uma vez por imagem que não veio nem na segunda tentativa; aoCarregar, a cada
     imagem que chega (o mapa usa para tirar o brilho de carregamento). */
  function grade(camada, tempo, classe, aoFalhar, aoCarregar) {
    var d = document.createElement('div');
    d.className = 'mapa-camada ' + (classe || '');
    TILES.forEach(function (t) {
      var img = document.createElement('img');
      img.alt = ''; img.decoding = 'async'; img.referrerPolicy = 'no-referrer';
      img.src = url(camada, tempo, t[0], t[1]);
      img.style.left = pct((t[0] * TAM - X0) / LARG * 100); img.style.top = pct((t[1] * TAM - Y0) / ALT * 100);
      img.style.width = pct(TAM / LARG * 100); img.style.height = pct(TAM / ALT * 100);
      if (aoCarregar) img.onload = aoCarregar;
      img.onerror = function () {  // a NASA às vezes falha uma imagem isolada: tenta mais uma vez antes de esconder e avisar
        if (!img.dataset.retentou) { img.dataset.retentou = '1'; img.src = img.src + '?r=1'; }
        else { img.style.visibility = 'hidden'; if (aoFalhar) aoFalhar(); }
      };
      d.appendChild(img);
    });
    return d;
  }
  function isoMin(ms) { return new Date(ms).toISOString().slice(0, 16) + ':00Z'; }
  function horaBrasilia(iso) { var d = new Date(Date.parse(iso) - 3 * 3600000); return d.toISOString().slice(11, 16).replace(':', 'h'); }
  function dataCurta(iso) { var p = iso.slice(0, 10).split('-'); return p[2] + '/' + p[1]; }

  /* Primeiro horário (ou dia) da lista de candidatos, do mais recente ao mais antigo, para o qual a NASA já tem a imagem:
     ela responde 404 para o que ainda não foi processado. cb(null) se nenhum servir (NASA fora do ar ou sem rede). */
  function sondar(camada, candidatos, cb) {
    var i = 0;
    (function tenta() {
      if (i >= candidatos.length) { cb(null); return; }
      var t = candidatos[i++], img = new Image();
      img.referrerPolicy = 'no-referrer';
      img.onload = function () { cb(t); };
      img.onerror = tenta;
      img.src = url(camada, t, TILES[4][0], TILES[4][1]);
    })();
  }
  function horariosDe(fimMs, n) {
    var lista = [];
    for (var k = 0; k < n; k++) lista.push(isoMin(fimMs - k * PASSO_MIN * 60000));
    return lista;
  }
  function diasAnteriores(n) {
    var agora = new Date(), hoje = Date.UTC(agora.getUTCFullYear(), agora.getUTCMonth(), agora.getUTCDate()), lista = [];
    for (var k = 1; k <= n; k++) lista.push(new Date(hoje - k * 86400000).toISOString().slice(0, 10));
    return lista;
  }

  function gradiente(paradas) { return 'linear-gradient(to right,' + paradas.map(function (p) { return p[0] + ' ' + p[1] + '%'; }).join(',') + ')'; }
  /* Legenda de cores da camada de nuvens: barra de temperatura com as marcas e uma frase. */
  function escalaIR() {
    var span = ESCALA_IR.ate - ESCALA_IR.de, pos = function (t) { return (t - ESCALA_IR.de) / span * 100; };
    var barra = gradiente(ESCALA_IR.paradas.map(function (p) { return [p[1], Math.round(pos(p[0]) * 10) / 10]; }));
    return '<div class="mapa-escala-bloco"><p class="mapa-escala-titulo">Temperatura do topo da nuvem (°C)</p>' +
      '<div class="mapa-escala-barra" style="background:' + barra + '"></div>' +
      '<div class="mapa-escala-marcas" aria-hidden="true">' + ESCALA_IR.marcas.map(function (t) { return '<span style="left:' + pct(pos(t)) + '">' + String(t).replace('-', '−') + '</span>'; }).join('') + '</div>' +
      '<p class="mapa-escala-texto mapa-escala-pontas"><span>Do ciano ao vermelho: topos mais frios e altos, nuvens de grande desenvolvimento</span>' +
      '<span>Cinza: nuvens baixas e a superfície</span></p></div>';
  }
  function escalaChuva(data) {
    var n = ESCALA_CHUVA.length;
    var barra = gradiente(ESCALA_CHUVA.map(function (p, i) { return [p[0], Math.round(i / (n - 1) * 1000) / 10]; }));
    return '<div class="mapa-escala-bloco"><p class="mapa-escala-titulo">Chuva estimada (IMERG), em mm/h' + (data ? ' · dia ' + esc(dataCurta(data)) : '') + '</p>' +
      '<div class="mapa-escala-barra" style="background:' + barra + '"></div>' +
      '<div class="mapa-escala-marcas" aria-hidden="true">' + ESCALA_CHUVA.map(function (p, i) { return '<span style="left:' + pct(i / (n - 1) * 100) + '">' + p[1] + '</span>'; }).join('') + '</div></div>';
  }

  var estadoMapa = null;

  function montar(el, op) {
    if (!el) return;
    var calmo = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.innerHTML =
      '<div class="mapa-cartao">' +
        '<div class="mapa-controles">' +
          '<div class="mapa-seg" role="group" aria-label="Camada do satélite">' + Object.keys(CAMADAS).map(function (k) {
            return '<button type="button" data-camada="' + k + '" aria-pressed="' + (k === 'infravermelho') + '" title="' + CAMADAS[k].rotulo + '">' + CAMADAS[k].curto +
              (CAMADAS[k].curto !== CAMADAS[k].rotulo ? '<span class="sr-only"> (infravermelho)</span>' : '') + '</button>';
          }).join('') + '</div>' +
          '<div class="mapa-opcoes">' +
            '<label class="mapa-chave" title="Chuva estimada (NASA IMERG), uma imagem por dia"><input type="checkbox" data-mapa-chuva><span><i aria-hidden="true"></i>Chuva estimada</span></label>' +
            (op.divisas ? '<label class="mapa-chave" title="Divisas dos estados (IBGE)"><input type="checkbox" data-mapa-divisas-chave checked><span><i aria-hidden="true"></i>Divisas</span></label>' : '') +
          '</div>' +
        '</div>' +
        '<div class="mapa-aviso" data-mapa-aviso role="status" hidden>' +
          '<p data-mapa-aviso-txt></p><button type="button" class="og-btn og-btn-contorno og-btn-md" data-mapa-tentar>Tentar de novo</button>' +
        '</div>' +
        '<figure class="mapa-satelite" data-mapa-figura data-carregando style="aspect-ratio:' + Math.round(LARG) + '/' + Math.round(ALT) + '">' +
          '<div class="mapa-palco" data-mapa-palco role="img" aria-label="Imagem de satélite do Brasil com os polos agrícolas da Janela de Campo"></div>' +
          (op.divisas ? '<img class="mapa-divisas" data-mapa-divisas src="' + esc(op.divisas) + '" alt="" decoding="async">' : '') +
          '<div class="mapa-pontos" data-mapa-pontos></div>' +
          '<p class="mapa-resumo" data-mapa-resumo role="status"></p>' +
          '<figcaption class="mapa-hora" data-mapa-hora aria-live="polite">carregando imagem…</figcaption>' +
        '</figure>' +
        '<div class="mapa-tempo" data-mapa-tempo hidden>' +
          '<button type="button" class="mapa-play" data-mapa-play aria-pressed="false" aria-label="Animar as últimas 2 horas" title="Animar as últimas 2 horas">' + IC.play + IC.pausa + '</button>' +
          '<div class="mapa-faixa">' +
            '<input type="range" min="0" max="' + (QUADROS - 1) + '" value="' + (QUADROS - 1) + '" step="1" data-mapa-quadro aria-label="Horário da imagem">' +
            '<div class="mapa-faixa-marcas" aria-hidden="true"></div>' +
            '<div class="mapa-faixa-rotulos"><span data-mapa-inicio></span><output data-mapa-faixa-hora></output><span data-mapa-fim></span></div>' +
          '</div>' +
        '</div>' +
        '<div class="mapa-escala" data-mapa-escala></div>' +
      '</div>' +
      '<details class="mapa-creditos"><summary>Créditos e fontes das imagens</summary>' +
        '<p>Imagens: NASA GIBS · NOAA GOES-East (infravermelho e cor real, a cada 10 min, com cerca de 1 h de atraso) · NASA IMERG (chuva estimada, uma imagem por dia). Litoral: NASA GIBS.' +
        (op.divisas ? ' Divisas dos estados: IBGE, Malha Municipal Digital e Áreas Territoriais 2025 (licença compatível com CC BY 4.0), simplificadas para este mapa; o IBGE não define os limites, e o desenho é ilustrativo.' : '') + '</p></details>';
    var figura = el.querySelector('[data-mapa-figura]');
    function pronto() { figura.removeAttribute('data-carregando'); }
    var palco = el.querySelector('[data-mapa-palco]'), pontos = el.querySelector('[data-mapa-pontos]'), hora = el.querySelector('[data-mapa-hora]');
    var tempo = el.querySelector('[data-mapa-tempo]'), play = el.querySelector('[data-mapa-play]'), faixa = el.querySelector('[data-mapa-quadro]');
    var aviso = el.querySelector('[data-mapa-aviso]'), avisoTxt = el.querySelector('[data-mapa-aviso-txt]'), escala = el.querySelector('[data-mapa-escala]');
    var saidaHora = el.querySelector('[data-mapa-faixa-hora]');
    var s = estadoMapa = { el: el, op: op, camada: 'infravermelho', horarios: [], horaCor: null, dataChuva: null, chuvaPedida: false, quadros: {},
      atual: QUADROS - 1, timer: null, falhas: 0, rodada: 0 };
    var chuvaCamada = null, fronteiras = grade(FRONTEIRAS, null, 'mapa-fronteiras');

    function avisar(texto) { avisoTxt.textContent = texto; aviso.hidden = false; }
    function limparAviso() { aviso.hidden = true; avisoTxt.textContent = ''; s.falhas = 0; }
    function aoFalhar() {
      s.falhas++; pronto();
      avisar(s.falhas >= TILES.length
        ? 'A imagem de satélite não carregou: a NASA (GIBS) não respondeu agora. A previsão e os polos continuam valendo.'
        : 'Parte da imagem de satélite não carregou (NASA GIBS). A previsão e os polos continuam valendo.');
    }
    function visivelChuva() { return chuvaCamada && !chuvaCamada.hidden; }
    function textoHora() {
      var base;
      if (s.camada === 'cor') base = s.horaCor ? 'Cor real · ' + horaBrasilia(s.horaCor) + ' (Brasília)' : 'Cor real · imagem mais recente';
      else base = s.horarios[s.atual] ? 'Infravermelho · ' + horaBrasilia(s.horarios[s.atual]) + ' (Brasília)' : 'Infravermelho';
      return base + (visivelChuva() && s.dataChuva ? ' · chuva IMERG de ' + dataCurta(s.dataChuva) : '');
    }
    function atualizarLegenda() {
      escala.innerHTML = (s.camada === 'infravermelho' ? escalaIR() : '<p class="mapa-escala-texto">Imagem em cores naturais de dia; à noite, a NOAA usa o infravermelho no lugar.</p>') +
        (visivelChuva() ? escalaChuva(s.dataChuva) : '');
      hora.textContent = textoHora();
    }
    function mostrar(i) {
      s.atual = i; faixa.value = String(i);
      faixa.style.setProperty('--p', (i / (QUADROS - 1) * 100) + '%');  // trecho já percorrido da linha do tempo
      // Os quadros ficam empilhados: o da vez sobe com transição de opacidade (CSS), o anterior some depois dela
      Object.keys(s.quadros).forEach(function (k) { s.quadros[k].classList.toggle('on', Number(k) === i); });
      if (s.horarios[i]) {
        var h = horaBrasilia(s.horarios[i]);
        saidaHora.textContent = h; faixa.setAttribute('aria-valuetext', h + ' (Brasília)');
      }
      hora.textContent = textoHora();
    }
    function quadro(i) {
      if (!s.quadros[i]) { s.quadros[i] = grade(CAMADAS.infravermelho, s.horarios[i], 'mapa-quadro', aoFalhar, pronto); palco.insertBefore(s.quadros[i], fronteiras); }
      return s.quadros[i];
    }
    function rotuloPlay(t) { play.setAttribute('aria-label', t); play.title = t; }
    function parar() { if (s.timer) { clearInterval(s.timer); s.timer = null; } play.setAttribute('aria-pressed', 'false'); rotuloPlay('Animar as últimas 2 horas'); }
    function animar() {
      for (var i = 0; i < QUADROS; i++) quadro(i);  // pré-carrega todos os quadros antes de girar
      play.setAttribute('aria-pressed', 'true'); rotuloPlay('Pausar a animação');
      s.timer = setInterval(function () { mostrar((s.atual + 1) % QUADROS); }, 700);
    }
    function limparBase() {
      Array.prototype.forEach.call(palco.querySelectorAll('.mapa-camada:not(.mapa-chuva):not(.mapa-fronteiras)'), function (d) { d.remove(); });
      s.quadros = {};
    }
    function desenharBase() {
      if (s.camada === 'cor') {
        palco.insertBefore(grade(CAMADAS.cor, s.horaCor || 'default', 'mapa-quadro on', aoFalhar, pronto), fronteiras);
        tempo.hidden = true;
      } else if (s.horarios.length) {
        quadro(QUADROS - 1); mostrar(QUADROS - 1); tempo.hidden = false;
      }
      atualizarLegenda();
    }
    function trocarCamada(k) {
      parar(); s.camada = k; s.falhas = 0; aviso.hidden = true;
      Array.prototype.forEach.call(el.querySelectorAll('[data-camada]'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-camada') === k)); });
      limparBase();
      desenharBase();
    }

    /* Descobre as horas: o último infravermelho publicado, os 12 quadros até 2 h antes, e a hora da cor real (mesmo
       horário, ou até 1 h antes). Sem nenhum horário, avisa que a NASA não respondeu. */
    function iniciar() {
      var rodada = ++s.rodada;
      parar(); limparAviso(); limparBase();
      s.horarios = []; s.horaCor = null;
      figura.setAttribute('data-carregando', '');
      tempo.hidden = true; hora.textContent = 'carregando imagem…';
      var fimIR = Math.floor((Date.now() - 30 * 60000) / (PASSO_MIN * 60000)) * PASSO_MIN * 60000;
      sondar(CAMADAS.infravermelho, horariosDe(fimIR, 18), function (ultimo) {
        if (rodada !== s.rodada) return;
        if (!ultimo) {
          pronto();
          atualizarLegenda();  // antes do texto da hora: ele reescreve a legenda da imagem
          hora.textContent = 'Imagem de satélite indisponível agora';
          avisar('Não foi possível carregar a imagem de satélite: a NASA (GIBS) não respondeu agora. A previsão e os polos continuam valendo; tente de novo em alguns minutos.');
          return;
        }
        var fim = Date.parse(ultimo);
        for (var i = QUADROS - 1; i >= 0; i--) s.horarios[i] = isoMin(fim - (QUADROS - 1 - i) * PASSO_MIN * 60000);
        el.querySelector('[data-mapa-inicio]').textContent = horaBrasilia(s.horarios[0]);
        el.querySelector('[data-mapa-fim]').textContent = horaBrasilia(s.horarios[QUADROS - 1]);
        desenharBase();
        sondar(CAMADAS.cor, horariosDe(fim, 7), function (t) {  // só dá nome à hora; a cor real é desenhada ao escolher a camada
          if (rodada !== s.rodada) return;
          s.horaCor = t;
          if (s.camada === 'cor') { limparBase(); desenharBase(); }
        });
      });
    }

    /* Chuva: só é pedida quando o visitante liga a camada. Descobre o dia mais recente que a NASA já tem (IMERG é diário). */
    function ligarChuva(ligada) {
      if (!ligada) { if (chuvaCamada) chuvaCamada.hidden = true; atualizarLegenda(); return; }
      if (chuvaCamada) { chuvaCamada.hidden = false; atualizarLegenda(); return; }
      if (s.chuvaPedida) return;
      s.chuvaPedida = true;
      sondar(CHUVA, diasAnteriores(4), function (dia) {
        s.chuvaPedida = false;
        var chave = el.querySelector('[data-mapa-chuva]');
        if (!dia) {
          chave.checked = false;
          avisar('A camada de chuva (NASA IMERG) não respondeu agora. Tente de novo em alguns minutos.');
          return;
        }
        s.dataChuva = dia;
        chuvaCamada = grade(CHUVA, dia, 'mapa-chuva', function () { avisar('Parte da camada de chuva (NASA IMERG) não carregou.'); });
        chuvaCamada.hidden = !chave.checked;
        palco.insertBefore(chuvaCamada, fronteiras);
        atualizarLegenda();
      });
    }

    palco.appendChild(fronteiras);
    iniciar();
    el.addEventListener('click', function (ev) {
      var c = ev.target.closest('[data-camada]');
      if (c) trocarCamada(c.getAttribute('data-camada'));
      if (ev.target.closest('[data-mapa-play]')) { if (s.timer) parar(); else animar(); }
      if (ev.target.closest('[data-mapa-tentar]')) {
        if (chuvaCamada) { chuvaCamada.remove(); chuvaCamada = null; }
        iniciar();
        if (el.querySelector('[data-mapa-chuva]').checked) ligarChuva(true);
      }
      var p = ev.target.closest('[data-polo]');
      if (p && s.op.aoEscolher) s.op.aoEscolher(s.op.polos.filter(function (x) { return x.id === p.getAttribute('data-polo'); })[0]);
    });
    faixa.addEventListener('input', function () { parar(); quadro(Number(faixa.value)); mostrar(Number(faixa.value)); });
    el.querySelector('[data-mapa-chuva]').addEventListener('change', function (ev) { ligarChuva(ev.target.checked); });
    var chaveDivisas = el.querySelector('[data-mapa-divisas-chave]'), imgDivisas = el.querySelector('[data-mapa-divisas]');
    if (chaveDivisas && imgDivisas) {
      chaveDivisas.addEventListener('change', function () { imgDivisas.hidden = !chaveDivisas.checked; });
      imgDivisas.addEventListener('error', function () { imgDivisas.hidden = true; chaveDivisas.closest('label').hidden = true; });  // arquivo do próprio site: sem ele, só some a opção
    }
    if (calmo) play.title = 'Animação desligada pela preferência de movimento reduzido; use o controle de horário.';
    if (calmo) play.hidden = true;

    pontos.innerHTML = op.polos.map(function (p) {
      var x = (px(p.lon) - X0) / LARG * 100, y = (py(p.lat) - Y0) / ALT * 100;
      // o nome abre para a esquerda nos polos da metade direita, para não sair do mapa
      return '<button type="button" class="mapa-polo" data-polo="' + p.id + '"' + (x > 62 ? ' data-lado="esq"' : '') + ' style="left:' + pct(x) + ';top:' + pct(y) + '">' +
        '<span class="mapa-polo-glifo" data-mapa-glifo></span><span class="mapa-polo-nome">' + esc(p.nome) + (p.uf ? ' · ' + esc(p.uf) : '') + '</span></button>';
    }).join('');
    atualizar();
  }

  /* Recolore os polos com o estado da operação escolhida, destaca o polo escolhido na página e refaz a contagem por estado
     (chamado pelo campo.js a cada troca). */
  function atualizar() {
    var s = estadoMapa;
    if (!s) return;
    var escolhido = s.op.atual ? s.op.atual() : null, estados = [];
    s.op.polos.forEach(function (p) {
      var b = s.el.querySelector('[data-polo="' + p.id + '"]');
      if (!b) return;
      var est = s.op.estado(p), atual = p.id === escolhido;
      estados.push(est);
      b.className = 'mapa-polo mapa-polo-' + est + (atual ? ' mapa-polo-atual' : '');
      b.querySelector('[data-mapa-glifo]').innerHTML = glifo(est);
      b.setAttribute('aria-label', s.op.rotulo(p));
      if (atual) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
      b.title = s.op.rotulo(p);
    });
    var resumo = s.el.querySelector('[data-mapa-resumo]');
    if (resumo) resumo.innerHTML = resumoDosPolos(estados).map(function (r) {
      return '<span class="mapa-resumo-item">' + glifo(r.estado) + '<b>' + r.n + '</b><span class="mapa-resumo-txt">' + esc(r.texto.replace(/^\d+\s*/, '')) + '</span></span>';
    }).join('');
  }

  (root.Orgatec = root.Orgatec || {}).campoMapa = { montar: montar, atualizar: atualizar, resumoDosPolos: resumoDosPolos, CAIXA: CAIXA, TILES: TILES, ESCALA_IR: ESCALA_IR, ESCALA_CHUVA: ESCALA_CHUVA };
})(typeof window !== 'undefined' ? window : this);
