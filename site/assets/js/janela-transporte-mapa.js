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

  /* ---------- Dias (horário de Brasília) ---------- */
  var SEMANA = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
  function diaBR(t) { return new Date((typeof t === 'number' ? t : Date.parse(t)) - 3 * 3600000).toISOString().slice(0, 10); }
  /* Hoje, amanhã e depois: o INMET publica os avisos com até dois dias de antecedência. */
  function dias(agora) {
    return [0, 1, 2].map(function (i) {
      var t = agora.getTime() + i * 86400000, chave = diaBR(t), d = new Date(t - 3 * 3600000);
      return { chave: chave, rotulo: i === 0 ? 'Hoje' : i === 1 ? 'Amanhã' : SEMANA[d.getUTCDay()] + ' ' + chave.slice(8, 10) + '/' + chave.slice(5, 7) };
    });
  }
  function avisosDoDia(d, chave) {
    return (d.avisos || []).filter(function (a) { return diaBR(a.inicio) <= chave && chave <= diaBR(a.fim); });
  }
  function pior(avisos) {
    return avisos.reduce(function (g, a) { return (ORDEM[a.gravidade] || 0) > (ORDEM[g] || 0) ? a.gravidade : g; }, '');
  }
  function unicos(lista) { return lista.filter(function (t, i, arr) { return arr.indexOf(t) === i; }); }
  function enumerar(itens) { return itens.length < 2 ? itens.join('') : itens.slice(0, -1).join(', ') + ' e ' + itens[itens.length - 1]; }

  /* ---------- Focos: perto das rodovias viram pontos; o resto vira mancha por célula de ~27 km ---------- */
  var PASSO_CELULA = 0.25, LIMIAR_FOGO = 10;
  function distKm(p, a, b) {
    var k = Math.cos(p[0] * Math.PI / 180), ax = (a[1] - p[1]) * k, ay = a[0] - p[0], bx = (b[1] - p[1]) * k, by = b[0] - p[0];
    var dx = bx - ax, dy = by - ay, c = dx * dx + dy * dy, t = c ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / c)) : 0;
    return Math.sqrt(Math.pow(ax + t * dx, 2) + Math.pow(ay + t * dy, 2)) * 111.2;
  }
  function separarFocos(focos, rodovias, raioKm) {
    var folga = raioKm / 100 + 0.02, linhas = [];
    ((rodovias || {}).rodovias || []).forEach(function (r) {
      r.linhas.forEach(function (ln) {
        var la = ln.map(function (p) { return p[0]; }), lo = ln.map(function (p) { return p[1]; });
        linhas.push({ pts: ln, s: Math.min.apply(null, la) - folga, n: Math.max.apply(null, la) + folga, w: Math.min.apply(null, lo) - folga, e: Math.max.apply(null, lo) + folga });
      });
    });
    var perto = [], celulas = {};
    (focos || []).forEach(function (f) {
      if (!dentroDaCaixa(f[0], f[1])) return;
      var junto = linhas.some(function (l) {
        if (f[0] < l.s || f[0] > l.n || f[1] < l.w || f[1] > l.e) return false;
        for (var i = 1; i < l.pts.length; i++) if (distKm(f, l.pts[i - 1], l.pts[i]) <= raioKm) return true;
        return false;
      });
      if (junto) { perto.push([f[0], f[1]]); return; }
      var ci = Math.floor(f[0] / PASSO_CELULA), cj = Math.floor(f[1] / PASSO_CELULA), k = ci + ':' + cj;
      (celulas[k] = celulas[k] || { lat: ci * PASSO_CELULA, lon: cj * PASSO_CELULA, n: 0 }).n++;
    });
    return { perto: perto, celulas: Object.keys(celulas).map(function (k) { return celulas[k]; }) };
  }

  /* Camadas do SVG. `rodovias` é o JSON do IBGE; `ocultos` = { avisos: true, ... }; `sel` = { dia: 'AAAA-MM-DD', rodovia: 'BR-153' }.
     Sem sel.dia, mostra todos os avisos (os de agora cheios, os futuros tracejados). `focos` aceita o resultado de separarFocos já calculado. */
  function svgCamadas(d, rodovias, ocultos, sel, focos) {
    ocultos = ocultos || {}; sel = sel || {};
    var s = '';
    if (!ocultos.focos) {
      var sep = focos || separarFocos(d.focos, rodovias, d.raio_fogo_km || 5);
      sep.celulas.forEach(function (c) {
        var a = xy(c.lat + PASSO_CELULA, c.lon), b = xy(c.lat, c.lon + PASSO_CELULA);
        s += '<rect class="jtm-calor" x="' + a[0] + '" y="' + a[1] + '" width="' + r1(b[0] - a[0]) + '" height="' + r1(b[1] - a[1]) + '" rx="2" fill="#ff5a1f" fill-opacity="' +
          (Math.round((0.18 + 0.5 * Math.min(1, c.n / 20)) * 100) / 100) + '" pointer-events="none"><title>' + c.n + ' foco(s)</title></rect>';
      });
    }
    if (!ocultos.avisos) {
      // os que ainda não começaram embaixo, tracejados; entre os de agora, o mais grave por cima
      (sel.dia ? avisosDoDia(d, sel.dia) : (d.avisos || []).slice()).sort(function (a, b) {
        return (vigente(a) - vigente(b)) || ((ORDEM[a.gravidade] || 0) - (ORDEM[b.gravidade] || 0));
      }).forEach(function (a) {
        var cor = COR[a.gravidade] || COR.perigo, ja = vigente(a);
        (a.poligonos || []).forEach(function (anel) {
          s += '<polygon class="jtm-area" data-aviso="' + esc(a.id) + '" data-vigente="' + ja + '" points="' + anel.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ') +
            '" fill="' + cor + '" fill-opacity="' + (ja ? '.16' : sel.dia ? '.08' : '0') + '" stroke="' + cor + '" stroke-width="1.5" stroke-linejoin="round"' +
            (ja ? '' : ' stroke-dasharray="5 4"') + '><title>' + esc((TIPO[a.tipo] || 'Alerta') + ' · ' + (ROTULO[a.gravidade] || a.gravidade) + ' · ' +
            (ja ? 'até ' + horaBR(a.fim) : 'a partir de ' + horaBR(a.inicio))) + '</title></polygon>';
        });
      });
    }
    if (!ocultos.rodovias && rodovias) {
      rodovias.rodovias.forEach(function (r) {
        var marcada = sel.rodovia === r.sigla, apagada = sel.rodovia && !marcada;
        r.linhas.forEach(function (linha) {
          var pts = linha.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ');
          s += '<polyline points="' + pts + '" fill="none" stroke="#0b1220" stroke-width="' + (marcada ? 6 : 4) + '" stroke-linejoin="round" stroke-linecap="round" opacity=".7" pointer-events="none"/>' +
            '<polyline data-rodovia="' + esc(r.sigla) + '"' + (marcada ? ' data-marcada="1"' : '') + ' points="' + pts + '" fill="none" stroke="' + (marcada ? '#38bdf8' : '#f8fafc') +
            '" stroke-width="' + (marcada ? 3.4 : 2) + '" stroke-linejoin="round" stroke-linecap="round"' + (apagada ? ' opacity=".5"' : '') + ' pointer-events="none"/>' +
            '<polyline class="jtm-alvo" data-rodovia-alvo="' + esc(r.sigla) + '" points="' + pts + '" fill="none" stroke="transparent" stroke-width="14" pointer-events="stroke"><title>' + esc(r.sigla) + '</title></polyline>';
        });
        var maior = r.linhas.slice().sort(function (a, b) { return b.length - a.length; })[0];
        if (maior && maior.length) {
          var meio = xy(maior[Math.floor(maior.length / 2)][0], maior[Math.floor(maior.length / 2)][1]);
          s += '<g class="jtm-rotulo' + (marcada ? ' jtm-rotulo-marcado' : '') + '" transform="translate(' + meio.join(',') + ')" pointer-events="none"><rect x="-21" y="-8" width="42" height="16" rx="3"/><text text-anchor="middle" y="4">' + esc(r.sigla) + '</text></g>';
        }
      });
    }
    if (!ocultos.focos) {
      (focos || separarFocos(d.focos, rodovias, d.raio_fogo_km || 5)).perto.forEach(function (f) {
        var c = xy(f[0], f[1]);
        s += '<circle class="jtm-foco-perto" cx="' + c[0] + '" cy="' + c[1] + '" r="3" fill="#ff3d00" stroke="#fff7ed" stroke-width="1" pointer-events="none"/>';
      });
    }
    return s;
  }

  /* Por rodovia, no dia escolhido: pior aviso que cruza o traçado, se já vale, e os focos a até 5 km (sempre das últimas 24 h). */
  function resumoRodovias(d, chave) {
    var doDia = {};
    avisosDoDia(d, chave).forEach(function (a) { doDia[a.id] = a; });
    var maximo = Math.max.apply(null, [1].concat((d.rodovias || []).map(function (r) { return r.focos_5km || 0; })));
    return (d.rodovias || []).map(function (r) {
      var av = (r.avisos || []).map(function (id) { return doDia[id]; }).filter(Boolean), valendo = av.filter(function (a) { return vigente(a); });
      var base = valendo.length ? valendo : av;
      return { sigla: r.sigla, gravidade: pior(base), valendo: valendo.length > 0, tipos: unicos(base.map(function (a) { return TIPO[a.tipo] || 'Alerta'; })),
        inicio: valendo.length || !av.length ? '' : av.map(function (a) { return a.inicio; }).sort()[0], focos: r.focos_5km || 0, parte: (r.focos_5km || 0) / maximo };
    });
  }

  var ROTULO_FONTE = { inmet: 'INMET', firms: 'NASA FIRMS' };
  var ESTADO_FONTE = { ok: 'ok', indisponivel: 'indisponível', desligada: 'desligada' };
  var NIVEL = { ok: ['Sem alerta agora', '#22c55e'], atencao: ['Atenção', '#facc15'], perigo: ['Perigo', '#f97316'], grave: ['Grande perigo', '#ef4444'],
    incerto: ['Verificação incompleta', '#94a3b8'] };

  /* Avisos de fonte fora do ar e de verificação atrasada. Vazio só quando tudo está em dia. */
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

  /* A frase do topo. Com verificação incompleta, nunca diz "sem alerta". */
  function veredito(d, agora) {
    if (avisosEstado(d, agora).length) return { nivel: 'incerto', frases: ['Sem verificação em dia, a falta de alerta não quer dizer que não há risco.'] };
    var rs = d.rodovias || [], frases = [], nivel = 'ok';
    var graves = rs.filter(function (r) { return (ORDEM[r.gravidade] || 0) >= 2; }), leves = rs.filter(function (r) { return r.gravidade === 'potencial'; });
    var fogo = rs.filter(function (r) { return (r.focos_5km || 0) >= LIMIAR_FOGO; }).sort(function (a, b) { return b.focos_5km - a.focos_5km; });
    if (graves.length) {
      var g = pior(graves);
      nivel = g === 'grande_perigo' ? 'grave' : 'perigo';
      frases.push(enumerar(graves.map(function (r) { return r.sigla; })) + ' sob aviso de ' + ROTULO[g] + ' do INMET agora.');
    }
    if (fogo.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push(fogo[0].sigla + ': ' + fogo[0].focos_5km + ' focos de fogo a até ' + (d.raio_fogo_km || 5) + ' km nas últimas 24 h. Atenção à fumaça.' +
        (fogo.length > 1 ? ' Também ' + enumerar(fogo.slice(1).map(function (r) { return r.sigla + ' (' + r.focos_5km + ')'; })) + '.' : ''));
    }
    if (!graves.length && leves.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push('Aviso de perigo potencial do INMET em ' + (leves.length === rs.length ? 'todas as rodovias' : enumerar(leves.map(function (r) { return r.sigla; }))) + ', sem aviso grave agora.');
    }
    if (!frases.length) frases.push('Sem aviso do INMET e sem concentração de focos de fogo perto das rodovias agora.');
    return { nivel: nivel, frases: frases };
  }

  function etiqueta(g) {
    if (!g) return '<span class="jtm-tag jtm-tag-ok">sem aviso</span>';
    return '<span class="jtm-tag" style="--g:' + (COR[g] || COR.perigo) + '">' + esc(ROTULO[g] || g) + '</span>';
  }

  function htmlVeredito(d, agora) {
    var v = veredito(d, agora), n = NIVEL[v.nivel];
    return '<div class="jtm-veredito" style="--g:' + n[1] + '" data-nivel="' + v.nivel + '" role="status"><span class="jtm-veredito-rotulo"><i class="jtm-ponto" aria-hidden="true"></i>' + esc(n[0]) + '</span>' +
      v.frases.map(function (f) { return '<p>' + esc(f) + '</p>'; }).join('') + '</div>';
  }

  function htmlTopo(d, agora) {
    return htmlVeredito(d, agora) + avisosEstado(d, agora).map(function (t) { return '<p class="jtm-alerta" role="status">' + esc(t) + '</p>'; }).join('');
  }

  function htmlDias(d, agora, sel) {
    return '<div class="jtm-dias" role="group" aria-label="Dia dos avisos">' + dias(agora).map(function (dia) {
      var av = avisosDoDia(d, dia.chave), g = pior(av);
      return '<button type="button" class="jtm-dia" data-jtm-dia="' + dia.chave + '" aria-pressed="' + (sel.dia === dia.chave) + '">' + esc(dia.rotulo) +
        '<small>' + (av.length ? '<i class="jtm-ponto" style="--g:' + (COR[g] || COR.perigo) + '" aria-hidden="true"></i>' + av.length + (av.length === 1 ? ' aviso' : ' avisos') : 'sem aviso') + '</small></button>';
    }).join('') + '</div>';
  }

  function htmlRodovias(d, sel) {
    var linhas = resumoRodovias(d, sel.dia);
    if (!linhas.length) return '';
    return '<div class="jtm-vias" role="group" aria-label="Rodovias">' + linhas.map(function (l) {
      return '<button type="button" class="jtm-via-cartao" data-jtm-rodovia="' + esc(l.sigla) + '" aria-pressed="' + (sel.rodovia === l.sigla) + '">' +
        '<span class="jtm-via-sigla">' + esc(l.sigla) + '</span>' +
        '<span>' + etiqueta(l.gravidade) + (l.tipos.length ? ' <span class="jtm-fraco">' + esc(l.tipos.join(', ')) + '</span>' : '') + '</span>' +
        (l.inicio ? '<span class="jtm-fraco">a partir de ' + esc(horaBR(l.inicio)) + '</span>' : '') +
        '<span class="jtm-via-fogo"><b>' + l.focos + '</b> <span class="jtm-fraco">foco(s) a até ' + esc(d.raio_fogo_km || 5) + ' km em 24 h</span></span>' +
        '<span class="jtm-barra" aria-hidden="true"><i style="width:' + Math.round(l.parte * 100) + '%"></i></span></button>';
    }).join('') + '</div>';
  }

  function listaAvisos(avisos, vazio) {
    if (!avisos.length) return '<p class="jtm-fraco">' + esc(vazio) + '</p>';
    return '<ul class="jtm-avisos">' + avisos.map(function (a) {
      return '<li style="--g:' + (COR[a.gravidade] || COR.perigo) + '"><div><b>' + esc(TIPO[a.tipo] || 'Alerta') + '</b> ' + etiqueta(a.gravidade) +
        (vigente(a) ? ' <span class="jtm-tag jtm-tag-ok">valendo agora</span>' : '') + '</div>' +
        '<small>de ' + esc(horaBR(a.inicio)) + ' até ' + esc(horaBR(a.fim)) + ' (horário de Brasília)</small>' +
        ((a.riscos || a.instrucoes) ? '<details><summary>Riscos e o que fazer</summary>' + (a.riscos ? '<p>' + esc(a.riscos) + '</p>' : '') +
          (a.instrucoes ? '<p><b>' + esc(a.instrucoes) + '</b></p>' : '') + '</details>' : '') +
        (/^https:\/\//.test(a.link || '') ? '<a class="og-link" href="' + esc(a.link) + '" target="_blank" rel="noopener noreferrer">Ver no portal do INMET</a>' : '') + '</li>';
    }).join('') + '</ul>';
  }

  /* Coluna da direita: veredito, avisos de estado, dias, rodovias, avisos do dia (da rodovia marcada, se houver) e as fontes. */
  function painel(d, agora, sel, semTopo) {
    sel = sel || {};
    var dia = sel.dia || diaBR(agora.getTime()), s = { dia: dia, rodovia: sel.rodovia || null };
    var rotulo = (dias(agora).filter(function (x) { return x.chave === dia; })[0] || { rotulo: dia }).rotulo.toLowerCase();
    var lista = avisosDoDia(d, dia);
    if (s.rodovia) {
      var ids = ((d.rodovias || []).filter(function (r) { return r.sigla === s.rodovia; })[0] || {}).avisos || [];
      lista = lista.filter(function (a) { return ids.indexOf(a.id) >= 0; });
    }
    var fontes = Object.keys(d.fontes || {}).map(function (k) { return (ROTULO_FONTE[k] || k) + ' ' + (ESTADO_FONTE[d.fontes[k].estado] || d.fontes[k].estado); });
    // semTopo: na página, o veredito e os avisos de estado ficam acima do mapa (no celular, antes de tudo)
    return (semTopo ? '' : htmlTopo(d, agora)) +
      htmlDias(d, agora, s) + htmlRodovias(d, s) +
      '<h3 class="jtm-titulo">Avisos de ' + esc(rotulo) + (s.rodovia ? ' na ' + esc(s.rodovia) : '') + ' <span class="jtm-fraco">(' + lista.length + ')</span>' +
        (s.rodovia ? ' <button type="button" class="jtm-limpar" data-jtm-rodovia="' + esc(s.rodovia) + '">ver todas as rodovias</button>' : '') + '</h3>' +
      listaAvisos(lista, 'Nenhum aviso do INMET ' + (s.rodovia ? 'no traçado da ' + s.rodovia : 'na região') + ' para ' + rotulo + '.') +
      '<p class="jtm-rodape">' + esc(fontes.join(' · ')) + (d.atualizado_em ? ' · verificado em ' + esc(horaBR(d.atualizado_em)) : '') + '</p>';
  }

  var CREDITOS = 'Avisos: INMET (avisos meteorológicos, apiprevmet3.inmet.gov.br). Focos de fogo: NASA FIRMS, sensores VIIRS dos satélites NOAA-20 e NOAA-21 (dados CC0). ' +
    'Rodovias: IBGE, Base Cartográfica Contínua 1:250.000 (BC250) 2023, traçado simplificado e ilustrativo. Divisas: IBGE, Malha Municipal Digital 2025, simplificadas; o IBGE não define os limites. ' +
    'Imagem de fundo: NASA Blue Marble (NASA GIBS). Licenças do IBGE compatíveis com CC BY 4.0. ' +
    'Este mapa não substitui a Defesa Civil, a PRF nem o DNIT: interdição de rodovia não tem fonte oficial em tempo real e não aparece aqui.';

  function montar(el, op) {
    if (!el || typeof document === 'undefined') return;
    var ocultos = {}, dados = null, rodovias = null, sel = { dia: diaBR(Date.now()), rodovia: null }, focos = null, focosDe = null;
    var divisas = op.divisas ? (function () {
      var l = (px(CAIXA_DIVISAS.oeste) - X0) / LARG * 100, t = (py(CAIXA_DIVISAS.norte) - Y0) / ALT * 100;
      var w = (px(CAIXA_DIVISAS.leste) - px(CAIXA_DIVISAS.oeste)) / LARG * 100, h = (py(CAIXA_DIVISAS.sul) - py(CAIXA_DIVISAS.norte)) / ALT * 100;
      return '<img class="jtm-divisas" src="' + esc(op.divisas) + '" alt="" decoding="async" style="left:' + pct(l) + ';top:' + pct(t) + ';width:' + pct(w) + ';height:' + pct(h) + '">';
    })() : '';
    el.innerHTML =
      '<div class="jtm">' +
        '<div class="jtm-topo" data-jtm-topo></div>' +
        '<div class="jtm-mapa-col">' +
          '<div class="campo-abas" role="group" aria-label="Camadas do mapa">' + CAMADAS.map(function (c) {
            return '<button type="button" class="campo-aba" data-jtm-camada="' + c[0] + '" aria-pressed="true">' + c[1] + '</button>';
          }).join('') + '</div>' +
          '<figure class="mapa-satelite jtm-mapa" style="aspect-ratio:' + Math.round(LARG) + '/' + Math.round(ALT) + '">' +
            '<div class="mapa-palco" role="img" aria-label="Mapa de Goiás, Tocantins e Pará com os avisos do INMET, os focos de fogo e as rodovias BR-153, BR-060, BR-010 e BR-230. As mesmas informações estão nos cartões ao lado.">' +
              '<div class="mapa-camada">' + TILES.map(function (t) {
                return '<img alt="" decoding="async" referrerpolicy="no-referrer" src="' + GIBS + FUNDO.id + '/default/' + FUNDO.matriz + '/' + Z + '/' + t[1] + '/' + t[0] + '.' + FUNDO.ext + '" style="left:' +
                  pct((t[0] * TAM - X0) / LARG * 100) + ';top:' + pct((t[1] * TAM - Y0) / ALT * 100) + ';width:' + pct(TAM / LARG * 100) + ';height:' + pct(TAM / ALT * 100) + '">';
              }).join('') + '</div>' + divisas +
              '<svg class="jtm-svg" viewBox="0 0 ' + r1(LARG) + ' ' + r1(ALT) + '" preserveAspectRatio="none" aria-hidden="true" data-jtm-svg></svg>' +
            '</div>' +
            '<div class="jtm-balao" data-jtm-balao role="status" hidden></div>' +
            '<figcaption class="mapa-hora" data-jtm-hora aria-live="polite">carregando…</figcaption>' +
          '</figure>' +
          '<div class="jtm-legenda" aria-hidden="true">' + ['potencial', 'perigo', 'grande_perigo'].map(function (g) {
            return '<span><i style="background:' + COR[g] + '"></i>' + ROTULO[g] + '</span>';
          }).join('') + '<span><i class="jtm-futuro"></i>Ainda não começou</span><span><i class="jtm-foco"></i>Foco junto à rodovia</span><span><i class="jtm-mancha"></i>Focos na região</span></div>' +
          '<p class="jtm-fraco jtm-dica">Toque numa rodovia ou numa área de aviso para ver o detalhe.</p>' +
          '<details class="mapa-creditos"><summary>Créditos e fontes</summary><p>' + esc(CREDITOS) + '</p></details>' +
        '</div>' +
        '<div class="jtm-painel" data-jtm-painel><p class="jtm-fraco">Carregando os alertas…</p></div>' +
      '</div>';
    var svg = el.querySelector('[data-jtm-svg]'), alvo = el.querySelector('[data-jtm-painel]'), hora = el.querySelector('[data-jtm-hora]');
    var balao = el.querySelector('[data-jtm-balao]'), figura = el.querySelector('.jtm-mapa'), topo = el.querySelector('[data-jtm-topo]'), topoHtml = '';
    function fecharBalao() { balao.hidden = true; balao.innerHTML = ''; }
    function desenhar() {
      var d = dados || {};
      if (focosDe !== dados || !focos || focos.rodovias !== rodovias) {  // 2.000 focos × traçado: calcula uma vez por resumo
        focos = separarFocos(d.focos, rodovias, d.raio_fogo_km || 5); focos.rodovias = rodovias; focosDe = dados;
      }
      svg.innerHTML = svgCamadas(d, rodovias, ocultos, sel, focos);
      if (dados) {
        var agora = new Date(), novoTopo = htmlTopo(dados, agora);
        if (novoTopo !== topoHtml) { topo.innerHTML = topoHtml = novoTopo; }  // só muda quando os dados mudam: o leitor de tela não repete a cada toque
        alvo.innerHTML = painel(dados, agora, sel, true);
        hora.textContent = dados.atualizado_em ? 'verificado ' + horaBR(dados.atualizado_em) : 'sem verificação';
      }
    }
    function marcarRodovia(sigla) { sel.rodovia = sel.rodovia === sigla ? null : sigla; fecharBalao(); desenhar(); }
    el.querySelectorAll('[data-jtm-camada]').forEach(function (b) {
      b.addEventListener('click', function () {
        var ligada = b.getAttribute('aria-pressed') !== 'true';
        b.setAttribute('aria-pressed', String(ligada));
        ocultos[b.getAttribute('data-jtm-camada')] = !ligada;
        fecharBalao(); desenhar();
      });
    });
    alvo.addEventListener('click', function (ev) {
      var b = ev.target.closest ? ev.target.closest('[data-jtm-rodovia],[data-jtm-dia]') : null;
      if (!b) return;
      var via = b.getAttribute('data-jtm-rodovia'), dia = b.getAttribute('data-jtm-dia');
      if (via) marcarRodovia(via); else { sel.dia = dia; fecharBalao(); desenhar(); }
      var de_novo = alvo.querySelector(via ? '.jtm-via-cartao[data-jtm-rodovia="' + via + '"]' : '[data-jtm-dia="' + dia + '"]');
      if (de_novo) de_novo.focus();  // o painel é redesenhado: devolve o foco ao botão usado
    });
    svg.addEventListener('click', function (ev) {
      var t = ev.target, via = t.getAttribute && t.getAttribute('data-rodovia-alvo'), id = t.getAttribute && t.getAttribute('data-aviso');
      if (via) { marcarRodovia(via); return; }
      var a = id && dados ? (dados.avisos || []).filter(function (x) { return x.id === id; })[0] : null;
      if (!a) { fecharBalao(); return; }
      var cx = figura.getBoundingClientRect(), x = ev.clientX - cx.left, y = ev.clientY - cx.top;
      balao.style.setProperty('--g', COR[a.gravidade] || COR.perigo);
      balao.innerHTML = '<button type="button" aria-label="Fechar" data-jtm-fechar>×</button><b>' + esc(TIPO[a.tipo] || 'Alerta') + '</b> · ' + esc(ROTULO[a.gravidade] || a.gravidade) +
        '<br>' + (vigente(a) ? 'Valendo agora, até ' + esc(horaBR(a.fim)) : 'De ' + esc(horaBR(a.inicio)) + ' até ' + esc(horaBR(a.fim))) + (a.instrucoes ? '<br><span>' + esc(a.instrucoes) + '</span>' : '');
      balao.hidden = false;
      balao.style.left = Math.max(8, Math.min(x - 20, cx.width - balao.offsetWidth - 8)) + 'px';
      balao.style.top = Math.max(8, Math.min(y + 12, cx.height - balao.offsetHeight - 8)) + 'px';
    });
    balao.addEventListener('click', function (ev) { if (ev.target.hasAttribute('data-jtm-fechar')) fecharBalao(); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && !balao.hidden) fecharBalao(); });
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
  return { CAIXA: CAIXA, TILES: TILES, xy: xy, horaBR: horaBR, estadoDados: estadoDados, svgCamadas: svgCamadas, resumoRodovias: resumoRodovias, dias: dias,
    avisosDoDia: avisosDoDia, separarFocos: separarFocos, veredito: veredito, avisosEstado: avisosEstado, painel: painel, LARG: LARG, ALT: ALT };
});
