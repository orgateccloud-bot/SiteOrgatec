/* Janela do Transporte: mapa público de alertas nas rodovias do Brasil (empresarial/janela.html).

   Dois modos, sem biblioteca (Web Mercator, fundo Blue Marble da NASA GIBS; CSP img-src https://gibs.earthdata.nasa.gov):
   - Brasil: contorno dos estados, rodovias federais, avisos do INMET e manchas de focos de fogo; tocar num estado aproxima nele;
   - Estado: rodovias com sigla (federais e estaduais) com cartões, focos junto a rodovias e, a pedido, as estradas locais
     (sem sigla), desenhadas num canvas.
   Geometria do IBGE no próprio site (assets/geo/ufs.json e assets/geo/rodovias/, de tools/gerar_rodovias.py). Dados de
   /api/transporte/alertas-publicos (nacional) e /alertas-publicos/<UF>, gravados pela rotina dos alertas a cada 15 min; sem
   viagem, posição ou cliente. Fonte fora do ar ou resumo atrasado aparecem como tal: o mapa nunca diz "sem risco" sem verificação. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).janelaTransporteMapa = factory();
})(this, function () {
  'use strict';
  var GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/';
  var FUNDO = { id: 'BlueMarble_ShadedRelief_Bathymetry', matriz: 'GoogleMapsCompatible_Level8', ext: 'jpeg' };
  var TAM = 256, LARGURA_TELA = 460;
  // Mesmo recorte de backend/transporte/alertas/publico.py (REGIAO): um teste confere.
  var BRASIL = { oeste: -74.5, leste: -34.5, norte: 5.5, sul: -34.0 };
  var VERIFICACAO_ATRASADA_MIN = 40;  // a rotina roda a cada 15 min
  var LIMIAR_FOGO = 10, LIMIAR_FOGO_UF = 50, MAX_CARTOES = 8;
  var COR = { potencial: '#facc15', perigo: '#f97316', grande_perigo: '#ef4444' };
  var ROTULO = { potencial: 'Perigo potencial', perigo: 'Perigo', grande_perigo: 'Grande perigo' };
  var ORDEM = { potencial: 1, perigo: 2, grande_perigo: 3 };
  var TIPO = { tempestade: 'Tempestade', chuva: 'Chuva forte', vento: 'Vento forte', geada: 'Geada', frio: 'Frio intenso', calor: 'Calor extremo',
    baixa_umidade: 'Umidade muito baixa', fogo: 'Fogo', outro: 'Alerta' };
  var CAMADAS = [['avisos', 'Avisos do INMET'], ['focos', 'Focos de fogo (24 h)'], ['rodovias', 'Rodovias'], ['locais', 'Estradas locais']];
  var NE = ' vector-effect="non-scaling-stroke"';

  /* ---------- Projeção e vistas ---------- */
  function px(lon, z) { return (lon + 180) / 360 * TAM * Math.pow(2, z); }
  function py(lat, z) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(Math.PI / 4 + r / 2)) / Math.PI) / 2 * TAM * Math.pow(2, z); }
  function r1(v) { return Math.round(v * 10) / 10; }
  function pct(v) { return (Math.round(v * 1000) / 1000) + '%'; }
  /* Vista de um retângulo { oeste, leste, norte, sul }: o maior zoom (até 8) em que o recorte cabe em 900 × 1100 px de imagem. */
  function vista(c, margem) {
    var m = margem == null ? 0.04 : margem, dl = (c.leste - c.oeste) * m, dt = (c.norte - c.sul) * m;
    var b = { oeste: c.oeste - dl, leste: c.leste + dl, norte: c.norte + dt, sul: c.sul - dt }, z = 8;
    while (z > 3 && (px(b.leste, z) - px(b.oeste, z) > 900 || py(b.sul, z) - py(b.norte, z) > 1100)) z--;
    var X0 = px(b.oeste, z), Y0 = py(b.norte, z), L = px(b.leste, z) - X0, A = py(b.sul, z) - Y0, tiles = [];
    for (var tx = Math.floor(X0 / TAM); tx <= Math.floor((X0 + L - 1) / TAM); tx++)
      for (var ty = Math.floor(Y0 / TAM); ty <= Math.floor((Y0 + A - 1) / TAM); ty++) tiles.push([tx, ty]);
    return { z: z, X0: X0, Y0: Y0, LARG: L, ALT: A, caixa: b, tiles: tiles, u: L / LARGURA_TELA };
  }
  function xy(v, lat, lon) { return [r1(px(lon, v.z) - v.X0), r1(py(lat, v.z) - v.Y0)]; }
  function pontos(v, linha) { return linha.map(function (p) { return xy(v, p[0], p[1]).join(','); }).join(' '); }
  /* caixa = [sul, oeste, norte, leste] */
  function aVista(v, cx) { return !(cx[2] < v.caixa.sul || cx[0] > v.caixa.norte || cx[3] < v.caixa.oeste || cx[1] > v.caixa.leste); }
  function caixaDe(anel) {
    var s = 90, w = 180, n = -90, e = -180;
    anel.forEach(function (p) { if (p[0] < s) s = p[0]; if (p[0] > n) n = p[0]; if (p[1] < w) w = p[1]; if (p[1] > e) e = p[1]; });
    return [s, w, n, e];
  }

  function vigente(a) { return a.vigente === false ? 0 : 1; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function num(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }

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
  /* Avisos de um dia; com `uf`, só os que cruzam rodovia daquele estado. */
  function avisosDoDia(d, chave, uf) {
    return ((d || {}).avisos || []).filter(function (a) {
      return diaBR(a.inicio) <= chave && chave <= diaBR(a.fim) && (!uf || (a.ufs || []).indexOf(uf) >= 0);
    });
  }
  function pior(itens) {
    return itens.reduce(function (g, a) { return (ORDEM[a.gravidade] || 0) > (ORDEM[g] || 0) ? a.gravidade : g; }, '');
  }
  function unicos(lista) { return lista.filter(function (t, i, arr) { return arr.indexOf(t) === i; }); }
  function enumerar(itens) { return itens.length < 2 ? itens.join('') : itens.slice(0, -1).join(', ') + ' e ' + itens[itens.length - 1]; }

  /* ---------- Camadas do SVG ---------- */
  function camadaCalor(v, nac) {
    var passo = nac.passo_calor || 0.25, s = '';
    (nac.calor || []).forEach(function (c) {
      if (!aVista(v, [c[0], c[1], c[0] + passo, c[1] + passo])) return;
      var a = xy(v, c[0] + passo, c[1]), b = xy(v, c[0], c[1] + passo);
      s += '<rect class="jtm-calor" x="' + a[0] + '" y="' + a[1] + '" width="' + r1(b[0] - a[0]) + '" height="' + r1(b[1] - a[1]) + '" fill="#ff5a1f" fill-opacity="' +
        (Math.round((0.18 + 0.5 * Math.min(1, c[2] / 20)) * 100) / 100) + '" pointer-events="none"><title>' + c[2] + ' foco(s)</title></rect>';
    });
    return s;
  }
  /* Os que ainda não começaram embaixo, tracejados; entre os de agora, o mais grave por cima. */
  function camadaAvisos(v, avisos, clicavel) {
    var s = '';
    avisos.slice().sort(function (a, b) { return (vigente(a) - vigente(b)) || ((ORDEM[a.gravidade] || 0) - (ORDEM[b.gravidade] || 0)); }).forEach(function (a) {
      var cor = COR[a.gravidade] || COR.perigo, ja = vigente(a);
      (a.poligonos || []).forEach(function (anel) {
        if (!aVista(v, caixaDe(anel))) return;
        s += '<polygon class="jtm-area" data-aviso="' + esc(a.id) + '" data-vigente="' + ja + '" points="' + pontos(v, anel) + '" fill="' + cor + '" fill-opacity="' + (ja ? '.16' : '.08') +
          '" stroke="' + cor + '" stroke-width="1.5" stroke-linejoin="round"' + NE + (ja ? '' : ' stroke-dasharray="5 4"') + (clicavel ? '' : ' pointer-events="none"') + '><title>' +
          esc((TIPO[a.tipo] || 'Alerta') + ' · ' + (ROTULO[a.gravidade] || a.gravidade) + ' · ' + (ja ? 'até ' + horaBR(a.fim) : 'a partir de ' + horaBR(a.inicio))) + '</title></polygon>';
      });
    });
    return s;
  }
  function camadaUfs(v, ufs, marcada, clicavel) {
    var s = '';
    (ufs || []).forEach(function (e) {
      if (!aVista(v, e.caixa)) return;
      var sel = e.uf === marcada;
      e.aneis.forEach(function (anel) {
        s += '<polygon class="jtm-uf" data-uf="' + esc(e.uf) + '"' + (sel ? ' data-marcada="1"' : '') + ' points="' + pontos(v, anel) + '" fill="#fff" fill-opacity="0" stroke="' +
          (sel ? '#38bdf8' : '#f8fafc') + '" stroke-opacity="' + (sel ? '1' : '.5') + '" stroke-width="' + (sel ? 1.8 : 0.8) + '" stroke-linejoin="round"' + NE +
          (clicavel ? '><title>' + esc(e.nome) + '</title></polygon>' : ' pointer-events="none"/>');
      });
    });
    return s;
  }
  function rotulo(v, lat, lon, texto, classe) {
    var c = xy(v, lat, lon), larg = texto.length * 6.2 + 8;
    return '<g class="jtm-rotulo' + (classe ? ' ' + classe : '') + '" transform="translate(' + c.join(',') + ') scale(' + r1(v.u * 10) / 10 + ')" pointer-events="none"><rect x="' + r1(-larg / 2) +
      '" y="-8" width="' + r1(larg) + '" height="16" rx="3"/><text text-anchor="middle" y="4">' + esc(texto) + '</text></g>';
  }

  /* Brasil: manchas de fogo, avisos do dia, rodovias federais e os estados (clicáveis). `geo` = { ufs: [...], federais: {rodovias} }. */
  function svgBrasil(nac, geo, ocultos, sel) {
    ocultos = ocultos || {}; sel = sel || {}; nac = nac || {};
    var v = vista(BRASIL, 0), s = '';
    if (!ocultos.focos) s += camadaCalor(v, nac);
    if (!ocultos.avisos) s += camadaAvisos(v, sel.dia ? avisosDoDia(nac, sel.dia) : (nac.avisos || []), false);
    if (!ocultos.rodovias && geo.federais) {
      geo.federais.rodovias.forEach(function (r) {
        r.linhas.forEach(function (linha) {
          s += '<polyline data-rodovia="' + esc(r.sigla) + '" points="' + pontos(v, linha) + '" fill="none" stroke="#f8fafc" stroke-opacity=".8" stroke-width="1" stroke-linejoin="round"' + NE + ' pointer-events="none"/>';
        });
      });
    }
    s += camadaUfs(v, geo.ufs, null, true);
    (geo.ufs || []).forEach(function (e) {
      s += '<text class="jtm-uf-sigla" x="' + xy(v, (e.caixa[0] + e.caixa[2]) / 2, (e.caixa[1] + e.caixa[3]) / 2).join('" y="') + '" text-anchor="middle" pointer-events="none">' + esc(e.uf) + '</text>';
    });
    return s;
  }

  /* Estado: `est` = resumo do estado (API), `geo` = { ufs, rodovias: {rodovias} } do estado, `sel` = { dia, rodovia }. */
  function svgEstado(nac, est, geo, ocultos, sel, uf) {
    ocultos = ocultos || {}; sel = sel || {}; nac = nac || {}; est = est || {};
    var e = (geo.ufs || []).filter(function (x) { return x.uf === uf; })[0];
    if (!e) return '';
    var v = vista({ sul: e.caixa[0], oeste: e.caixa[1], norte: e.caixa[2], leste: e.caixa[3] }), s = '';
    if (!ocultos.focos) s += camadaCalor(v, nac);
    if (!ocultos.avisos) s += camadaAvisos(v, sel.dia ? avisosDoDia(nac, sel.dia, uf) : (nac.avisos || []), true);
    s += camadaUfs(v, geo.ufs, uf, false);
    var rotulos = '';  // por último, para ficarem legíveis sobre os focos
    if (!ocultos.rodovias && geo.rodovias) {
      // estaduais embaixo, federais por cima
      geo.rodovias.rodovias.slice().sort(function (a, b) { return (a.sigla.indexOf('BR-') === 0) - (b.sigla.indexOf('BR-') === 0); }).forEach(function (r) {
        var federal = r.sigla.indexOf('BR-') === 0, marcada = sel.rodovia === r.sigla, apagada = sel.rodovia && !marcada;
        r.linhas.forEach(function (linha) {
          var p = pontos(v, linha);
          if (federal || marcada) s += '<polyline points="' + p + '" fill="none" stroke="#0b1220" stroke-opacity=".7" stroke-width="' + (marcada ? 6 : 4) + '" stroke-linejoin="round" stroke-linecap="round"' + NE + ' pointer-events="none"/>';
          s += '<polyline data-rodovia="' + esc(r.sigla) + '"' + (marcada ? ' data-marcada="1"' : '') + ' points="' + p + '" fill="none" stroke="' + (marcada ? '#38bdf8' : federal ? '#f8fafc' : '#cbd5e1') +
            '" stroke-width="' + (marcada ? 3.4 : federal ? 2 : 1.1) + '" stroke-linejoin="round" stroke-linecap="round"' + (apagada ? ' opacity=".45"' : '') + NE + ' pointer-events="none"/>' +
            '<polyline class="jtm-alvo" data-rodovia-alvo="' + esc(r.sigla) + '" points="' + p + '" fill="none" stroke="transparent" stroke-width="' + (federal ? 14 : 10) + '"' + NE + ' pointer-events="stroke"><title>' + esc(r.sigla) + '</title></polyline>';
        });
        if (federal || marcada) {
          var meio = r.linhas[0][Math.floor(r.linhas[0].length / 2)];  // linhas vêm da maior para a menor
          rotulos += rotulo(v, meio[0], meio[1], r.sigla, marcada ? 'jtm-rotulo-marcado' : '');
        }
      });
    }
    if (!ocultos.focos) {
      (est.focos_perto || []).forEach(function (f) {
        var c = xy(v, f[0], f[1]);
        s += '<circle class="jtm-foco-perto" cx="' + c[0] + '" cy="' + c[1] + '" r="' + r1(2.2 * v.u) + '" fill="#ff3d00" stroke="#fff7ed" stroke-width=".7"' + NE + ' pointer-events="none"/>';
      });
    }
    return s + rotulos;
  }

  /* ---------- Resumos ---------- */
  /* Por estado, no dia escolhido: pior aviso que cruza rodovia dali e os focos junto a rodovias (sempre das últimas 24 h). */
  function resumoEstados(nac, chave, nomes) {
    var ufs = (nac || {}).ufs || {}, doDia = avisosDoDia(nac, chave), linhas = Object.keys(ufs).map(function (uf) {
      var av = doDia.filter(function (a) { return (a.ufs || []).indexOf(uf) >= 0; }), valendo = av.filter(function (a) { return vigente(a); }), base = valendo.length ? valendo : av;
      return { uf: uf, nome: (nomes || {})[uf] || uf, gravidade: pior(base), valendo: valendo.length > 0, tipos: unicos(base.map(function (a) { return TIPO[a.tipo] || 'Alerta'; })),
        inicio: valendo.length || !av.length ? '' : av.map(function (a) { return a.inicio; }).sort()[0], focos: ufs[uf].focos_5km || 0 };
    });
    var maximo = Math.max.apply(null, [1].concat(linhas.map(function (l) { return l.focos; })));
    linhas.forEach(function (l) { l.parte = l.focos / maximo; });
    return linhas.sort(function (a, b) { return ((ORDEM[b.gravidade] || 0) - (ORDEM[a.gravidade] || 0)) || (b.focos - a.focos) || (a.uf < b.uf ? -1 : 1); });
  }
  /* Por rodovia do estado, no dia escolhido. `est.rodovias` só traz as que têm aviso ou foco. */
  function resumoRodovias(est, nac, chave) {
    var doDia = {};
    avisosDoDia(nac, chave).forEach(function (a) { doDia[a.id] = a; });
    var rs = (est || {}).rodovias || [], maximo = Math.max.apply(null, [1].concat(rs.map(function (r) { return r.focos_5km || 0; })));
    return rs.map(function (r) {
      var av = (r.avisos || []).map(function (id) { return doDia[id]; }).filter(Boolean), valendo = av.filter(function (a) { return vigente(a); }), base = valendo.length ? valendo : av;
      return { sigla: r.sigla, gravidade: pior(base), valendo: valendo.length > 0, tipos: unicos(base.map(function (a) { return TIPO[a.tipo] || 'Alerta'; })),
        inicio: valendo.length || !av.length ? '' : av.map(function (a) { return a.inicio; }).sort()[0], focos: r.focos_5km || 0, parte: (r.focos_5km || 0) / maximo };
    }).sort(function (a, b) { return ((ORDEM[b.gravidade] || 0) - (ORDEM[a.gravidade] || 0)) || (b.focos - a.focos) || (a.sigla < b.sigla ? -1 : 1); });
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

  var INCERTO = { nivel: 'incerto', frases: ['Sem verificação em dia, a falta de alerta não quer dizer que não há risco.'] };
  /* A frase do topo no Brasil. Com verificação incompleta, nunca diz "sem alerta". */
  function vereditoBrasil(nac, agora) {
    if (avisosEstado(nac, agora).length) return INCERTO;
    var ufs = Object.keys(nac.ufs || {}).map(function (uf) { return { uf: uf, gravidade: nac.ufs[uf].gravidade, focos: nac.ufs[uf].focos_5km || 0 }; });
    var graves = ufs.filter(function (e) { return (ORDEM[e.gravidade] || 0) >= 2; }), leves = ufs.filter(function (e) { return e.gravidade === 'potencial'; });
    var fogo = ufs.filter(function (e) { return e.focos >= LIMIAR_FOGO_UF; }).sort(function (a, b) { return b.focos - a.focos; }).slice(0, 3), frases = [], nivel = 'ok';
    if (graves.length) {
      var g = pior(graves);
      nivel = g === 'grande_perigo' ? 'grave' : 'perigo';
      frases.push('Aviso de ' + ROTULO[g] + ' do INMET sobre rodovias de ' + enumerar(graves.map(function (e) { return e.uf; })) + ' agora.');
    }
    if (fogo.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push('Mais focos de fogo junto a rodovias nas últimas 24 h: ' + enumerar(fogo.map(function (e) { return e.uf + ' (' + num(e.focos) + ')'; })) + '. Atenção à fumaça.');
    }
    if (!graves.length && leves.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push('Aviso de perigo potencial do INMET sobre rodovias de ' + leves.length + (leves.length === 1 ? ' estado' : ' estados') + ', sem aviso grave agora.');
    }
    if (!frases.length) frases.push('Sem aviso do INMET sobre rodovias e sem concentração de focos de fogo junto a elas agora.');
    return { nivel: nivel, frases: frases };
  }
  /* A frase do topo no estado, pelas rodovias com sigla. */
  function veredito(est, agora) {
    if (avisosEstado(est, agora).length) return INCERTO;
    var rs = est.rodovias || [], frases = [], nivel = 'ok', raio = est.raio_fogo_km || 5;
    var graves = rs.filter(function (r) { return (ORDEM[r.gravidade] || 0) >= 2; }), leves = rs.filter(function (r) { return r.gravidade === 'potencial'; });
    var fogo = rs.filter(function (r) { return (r.focos_5km || 0) >= LIMIAR_FOGO; }).sort(function (a, b) { return b.focos_5km - a.focos_5km; }).slice(0, 3);
    if (graves.length) {
      var g = pior(graves), nomes = graves.slice(0, 4).map(function (r) { return r.sigla; });
      nivel = g === 'grande_perigo' ? 'grave' : 'perigo';
      frases.push(enumerar(nomes) + (graves.length > 4 ? ' e mais ' + (graves.length - 4) : '') + ' sob aviso de ' + ROTULO[g] + ' do INMET agora.');
    }
    if (fogo.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push(fogo[0].sigla + ': ' + num(fogo[0].focos_5km) + ' focos de fogo a até ' + raio + ' km nas últimas 24 h. Atenção à fumaça.' +
        (fogo.length > 1 ? ' Também ' + enumerar(fogo.slice(1).map(function (r) { return r.sigla + ' (' + num(r.focos_5km) + ')'; })) + '.' : ''));
    }
    if (!graves.length && leves.length) {
      if (nivel === 'ok') nivel = 'atencao';
      frases.push('Aviso de perigo potencial do INMET em ' + leves.length + (leves.length === 1 ? ' rodovia' : ' rodovias') + ', sem aviso grave agora.');
    }
    if (!frases.length) frases.push('Sem aviso do INMET e sem concentração de focos de fogo junto às rodovias do estado agora.');
    return { nivel: nivel, frases: frases };
  }

  /* ---------- HTML do painel ---------- */
  function etiqueta(g) {
    if (!g) return '<span class="jtm-tag jtm-tag-ok">sem aviso</span>';
    return '<span class="jtm-tag" style="--g:' + (COR[g] || COR.perigo) + '">' + esc(ROTULO[g] || g) + '</span>';
  }
  function htmlTopo(v, estados) {
    var n = NIVEL[v.nivel];
    return '<div class="jtm-veredito" style="--g:' + n[1] + '" data-nivel="' + v.nivel + '" role="status"><span class="jtm-veredito-rotulo"><i class="jtm-ponto" aria-hidden="true"></i>' + esc(n[0]) + '</span>' +
      v.frases.map(function (f) { return '<p>' + esc(f) + '</p>'; }).join('') + '</div>' +
      estados.map(function (t) { return '<p class="jtm-alerta" role="status">' + esc(t) + '</p>'; }).join('');
  }
  function htmlDias(nac, agora, sel, uf) {
    return '<div class="jtm-dias" role="group" aria-label="Dia dos avisos">' + dias(agora).map(function (dia) {
      var av = avisosDoDia(nac, dia.chave, uf), g = pior(av);
      return '<button type="button" class="jtm-dia" data-jtm-dia="' + dia.chave + '" aria-pressed="' + (sel.dia === dia.chave) + '">' + esc(dia.rotulo) +
        '<small>' + (av.length ? '<i class="jtm-ponto" style="--g:' + (COR[g] || COR.perigo) + '" aria-hidden="true"></i>' + av.length + (av.length === 1 ? ' aviso' : ' avisos') : 'sem aviso') + '</small></button>';
    }).join('') + '</div>';
  }
  function cartao(atributo, titulo, sub, l, pressionado, raio) {
    return '<button type="button" class="jtm-via-cartao" ' + atributo + (pressionado == null ? '' : ' aria-pressed="' + pressionado + '"') + '>' +
      '<span class="jtm-via-sigla">' + esc(titulo) + (sub ? ' <span class="jtm-fraco">' + esc(sub) + '</span>' : '') + '</span>' +
      '<span>' + etiqueta(l.gravidade) + (l.tipos.length ? ' <span class="jtm-fraco">' + esc(l.tipos.join(', ')) + '</span>' : '') + '</span>' +
      (l.inicio ? '<span class="jtm-fraco">a partir de ' + esc(horaBR(l.inicio)) + '</span>' : '') +
      '<span class="jtm-via-fogo"><b>' + num(l.focos) + '</b> <span class="jtm-fraco">foco(s) a até ' + esc(raio) + ' km de rodovia em 24 h</span></span>' +
      '<span class="jtm-barra" aria-hidden="true"><i style="width:' + Math.round((l.parte || 0) * 100) + '%"></i></span></button>';
  }
  function htmlEstados(nac, sel, nomes) {
    var todos = resumoEstados(nac, sel.dia, nomes), com = todos.filter(function (l) { return l.gravidade || l.focos; });
    var opcoes = todos.slice().sort(function (a, b) { return a.nome < b.nome ? -1 : 1; }).map(function (l) { return '<option value="' + esc(l.uf) + '">' + esc(l.nome) + '</option>'; }).join('');
    return '<div class="jtm-linha"><h3 class="jtm-titulo">Estados</h3>' +
      '<label class="jtm-escolha"><span class="jtm-fraco">Ir para</span> <select data-jtm-estado class="og-campo-controle"><option value="">Escolha o estado</option>' + opcoes + '</select></label></div>' +
      (com.length ? '<div class="jtm-vias">' + com.slice(0, MAX_CARTOES).map(function (l) { return cartao('data-jtm-uf="' + esc(l.uf) + '"', l.uf, l.nome, l, null, nac.raio_fogo_km || 5); }).join('') + '</div>' +
        (com.length > MAX_CARTOES ? '<p class="jtm-fraco">E mais ' + (com.length - MAX_CARTOES) + ' estado(s) com aviso ou foco: escolha na lista ou toque no mapa.</p>' : '')
        : '<p class="jtm-fraco">Nenhum estado com aviso sobre rodovia ou foco junto a rodovia neste dia.</p>');
  }
  /* Cartões das rodovias do estado. `busca` filtra pela sigla em todas as rodovias do estado (`todas`), com ou sem alerta. */
  function htmlRodovias(est, nac, sel, busca, todas) {
    var linhas = resumoRodovias(est, nac, sel.dia), q = String(busca || '').toUpperCase().replace(/[^A-Z0-9]/g, ''), total = linhas.length, raio = est.raio_fogo_km || 5;
    function casa(sigla) { return sigla.replace('-', '').indexOf(q) >= 0; }
    if (q) {
      var tem = {};
      linhas = linhas.filter(function (l) { tem[l.sigla] = 1; return casa(l.sigla); });
      (todas || []).forEach(function (sigla) { if (!tem[sigla] && casa(sigla)) linhas.push({ sigla: sigla, gravidade: '', tipos: [], inicio: '', focos: 0, parte: 0 }); });
    }
    var mostradas = linhas.slice(0, q ? 12 : MAX_CARTOES);
    if (sel.rodovia && !mostradas.some(function (l) { return l.sigla === sel.rodovia; })) {
      mostradas.unshift(linhas.filter(function (l) { return l.sigla === sel.rodovia; })[0] || { sigla: sel.rodovia, gravidade: '', tipos: [], inicio: '', focos: 0, parte: 0 });
    }
    if (!mostradas.length) return '<p class="jtm-fraco">' + (q ? 'Nenhuma rodovia com essa sigla neste estado.' : 'Nenhuma rodovia do estado com aviso no traçado ou foco a até ' + esc(raio) + ' km neste dia.') + '</p>';
    return '<div class="jtm-vias">' + mostradas.map(function (l) { return cartao('data-jtm-rodovia="' + esc(l.sigla) + '"', l.sigla, '', l, sel.rodovia === l.sigla, raio); }).join('') + '</div>' +
      (!q && total > mostradas.length ? '<p class="jtm-fraco">E mais ' + (total - MAX_CARTOES) + ' rodovia(s) com aviso ou foco: busque pela sigla.</p>' : '');
  }
  function listaAvisos(avisos, vazio) {
    if (!avisos.length) return '<p class="jtm-fraco">' + esc(vazio) + '</p>';
    return '<ul class="jtm-avisos">' + avisos.map(function (a) {
      return '<li style="--g:' + (COR[a.gravidade] || COR.perigo) + '"><div><b>' + esc(TIPO[a.tipo] || 'Alerta') + '</b> ' + etiqueta(a.gravidade) +
        (vigente(a) ? ' <span class="jtm-tag jtm-tag-ok">valendo agora</span>' : '') + '</div>' +
        '<small>de ' + esc(horaBR(a.inicio)) + ' até ' + esc(horaBR(a.fim)) + ' (horário de Brasília)' + ((a.ufs || []).length ? ' · rodovias de ' + (a.ufs.length > 4 ? a.ufs.length + ' estados' : esc(a.ufs.join(', '))) : '') + '</small>' +
        ((a.riscos || a.instrucoes) ? '<details><summary>Riscos e o que fazer</summary>' + (a.riscos ? '<p>' + esc(a.riscos) + '</p>' : '') +
          (a.instrucoes ? '<p><b>' + esc(a.instrucoes) + '</b></p>' : '') + '</details>' : '') +
        (/^https:\/\//.test(a.link || '') ? '<a class="og-link" href="' + esc(a.link) + '" target="_blank" rel="noopener noreferrer">Ver no portal do INMET</a>' : '') + '</li>';
    }).join('') + '</ul>';
  }
  function rodape(d) {
    var fontes = Object.keys(d.fontes || {}).map(function (k) { return (ROTULO_FONTE[k] || k) + ' ' + (ESTADO_FONTE[d.fontes[k].estado] || d.fontes[k].estado); });
    return '<p class="jtm-rodape">' + esc(fontes.join(' · ')) + (d.atualizado_em ? ' · verificado em ' + esc(horaBR(d.atualizado_em)) : '') + '</p>';
  }
  function rotuloDia(agora, dia) { return (dias(agora).filter(function (x) { return x.chave === dia; })[0] || { rotulo: dia }).rotulo.toLowerCase(); }

  /* Brasil: veredito, dias, estados e avisos do dia. `semTopo`: na página o veredito fica acima do mapa. */
  function painelBrasil(nac, agora, sel, nomes, semTopo) {
    sel = sel || {};
    var s = { dia: sel.dia || diaBR(agora.getTime()) }, lista = avisosDoDia(nac, s.dia), rot = rotuloDia(agora, s.dia);
    return (semTopo ? '' : htmlTopo(vereditoBrasil(nac, agora), avisosEstado(nac, agora))) + htmlDias(nac, agora, s) + htmlEstados(nac, s, nomes) +
      '<h3 class="jtm-titulo">Avisos de ' + esc(rot) + ' no Brasil <span class="jtm-fraco">(' + lista.length + ')</span></h3>' +
      listaAvisos(lista, 'Nenhum aviso do INMET para ' + rot + '.') + rodape(nac);
  }
  /* Estado: voltar, veredito, dias, busca e cartões das rodovias e os avisos do dia (da rodovia marcada, se houver). */
  function painelEstado(nac, est, agora, sel, uf, nome, todas, semTopo, busca) {
    sel = sel || {};
    var s = { dia: sel.dia || diaBR(agora.getTime()), rodovia: sel.rodovia || null }, rot = rotuloDia(agora, s.dia), lista = avisosDoDia(nac, s.dia, uf);
    if (s.rodovia) {
      var ids = ((est.rodovias || []).filter(function (r) { return r.sigla === s.rodovia; })[0] || {}).avisos || [];
      lista = lista.filter(function (a) { return ids.indexOf(a.id) >= 0; });
    }
    return (semTopo ? '' : htmlTopo(veredito(est, agora), avisosEstado(est, agora))) +
      '<div class="jtm-linha"><button type="button" class="jtm-limpar" data-jtm-voltar>← Brasil</button><h3 class="jtm-titulo jtm-estado-nome">' + esc(nome || uf) + '</h3></div>' +
      htmlDias(nac, agora, s, uf) +
      '<div class="jtm-linha"><h3 class="jtm-titulo">Rodovias</h3><label class="jtm-escolha"><span class="jtm-fraco">Buscar</span> ' +
        '<input type="search" class="og-campo-controle" data-jtm-busca placeholder="sigla, ex.: BR-153" aria-label="Buscar rodovia pela sigla" autocomplete="off" value="' + esc(busca || '') + '"></label></div>' +
      '<div data-jtm-vias>' + htmlRodovias(est, nac, s, busca, todas) + '</div>' +
      '<h3 class="jtm-titulo">Avisos de ' + esc(rot) + (s.rodovia ? ' na ' + esc(s.rodovia) : ' no estado') + ' <span class="jtm-fraco">(' + lista.length + ')</span>' +
        (s.rodovia ? ' <button type="button" class="jtm-limpar" data-jtm-rodovia="' + esc(s.rodovia) + '">ver todas as rodovias</button>' : '') + '</h3>' +
      listaAvisos(lista, 'Nenhum aviso do INMET ' + (s.rodovia ? 'no traçado da ' + s.rodovia : 'sobre rodovias do estado') + ' para ' + rot + '.') + rodape(est.atualizado_em ? est : nac);
  }

  var CREDITOS = 'Avisos: INMET (avisos meteorológicos, apiprevmet3.inmet.gov.br). Focos de fogo: NASA FIRMS, sensores VIIRS dos satélites NOAA-20 e NOAA-21 (dados CC0). ' +
    'Rodovias e estradas: IBGE, Base Cartográfica Contínua 1:250.000 (BC250) 2023, traçado simplificado e ilustrativo; a malha local é incompleta e não serve de guia de rota. ' +
    'Limites dos estados: IBGE, Malha Municipal Digital 2025, simplificados; o IBGE não define os limites. Imagem de fundo: NASA Blue Marble (NASA GIBS). Licenças do IBGE compatíveis com CC BY 4.0. ' +
    'Este mapa não substitui a Defesa Civil, a PRF nem o DNIT: interdição de rodovia não tem fonte oficial em tempo real e não aparece aqui.';

  function montar(el, op) {
    if (!el || typeof document === 'undefined') return;
    var ocultos = { locais: true }, sel = { dia: diaBR(Date.now()), rodovia: null }, uf = null, busca = '';
    var nac = null, ufs = null, nomes = {}, federais = null, porUf = {}, vistaAtual = null, chaveVista = '', topoHtml = '';
    function json(url) { return fetch(url, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
    function doUf(u) { return (porUf[u] = porUf[u] || { est: null, rodovias: null, locais: null, erro: false }); }
    el.innerHTML =
      '<div class="jtm">' +
        '<div class="jtm-topo" data-jtm-topo></div>' +
        '<div class="jtm-mapa-col">' +
          '<div class="campo-abas" role="group" aria-label="Camadas do mapa">' + CAMADAS.map(function (c) {
            return '<button type="button" class="campo-aba" data-jtm-camada="' + c[0] + '" aria-pressed="' + (c[0] !== 'locais') + '"' + (c[0] === 'locais' ? ' hidden' : '') + '>' + c[1] + '</button>';
          }).join('') + '</div>' +
          '<figure class="mapa-satelite jtm-mapa">' +
            '<div class="mapa-palco" role="img" aria-label="Mapa do Brasil com os avisos do INMET, os focos de fogo e as rodovias. As mesmas informações estão nos cartões ao lado.">' +
              '<div class="mapa-camada" data-jtm-fundo></div>' +
              '<canvas class="jtm-locais" data-jtm-locais hidden></canvas>' +
              '<svg class="jtm-svg" preserveAspectRatio="none" aria-hidden="true" data-jtm-svg></svg>' +
            '</div>' +
            '<div class="jtm-balao" data-jtm-balao role="status" hidden></div>' +
            '<figcaption class="mapa-hora" data-jtm-hora aria-live="polite">carregando…</figcaption>' +
          '</figure>' +
          '<div class="jtm-legenda" aria-hidden="true">' + ['potencial', 'perigo', 'grande_perigo'].map(function (g) {
            return '<span><i style="background:' + COR[g] + '"></i>' + ROTULO[g] + '</span>';
          }).join('') + '<span><i class="jtm-futuro"></i>Ainda não começou</span><span><i class="jtm-mancha"></i>Focos na região</span><span><i class="jtm-foco"></i>Foco junto a rodovia (no estado)</span></div>' +
          '<p class="jtm-fraco jtm-dica" data-jtm-dica></p>' +
          '<details class="mapa-creditos"><summary>Créditos e fontes</summary><p>' + esc(CREDITOS) + '</p></details>' +
        '</div>' +
        '<div class="jtm-painel" data-jtm-painel><p class="jtm-fraco">Carregando os alertas…</p></div>' +
      '</div>';
    var svg = el.querySelector('[data-jtm-svg]'), alvo = el.querySelector('[data-jtm-painel]'), hora = el.querySelector('[data-jtm-hora]'), fundo = el.querySelector('[data-jtm-fundo]');
    var balao = el.querySelector('[data-jtm-balao]'), figura = el.querySelector('.jtm-mapa'), topo = el.querySelector('[data-jtm-topo]'), tela = el.querySelector('[data-jtm-locais]');
    var dica = el.querySelector('[data-jtm-dica]'), botaoLocais = el.querySelector('[data-jtm-camada="locais"]');
    function fecharBalao() { balao.hidden = true; balao.innerHTML = ''; }
    function caixaUf(u) { var e = (ufs || []).filter(function (x) { return x.uf === u; })[0]; return e ? { sul: e.caixa[0], oeste: e.caixa[1], norte: e.caixa[2], leste: e.caixa[3] } : null; }

    function trocarVista() {
      var cx = uf && caixaUf(uf), v = cx ? vista(cx) : vista(BRASIL, 0), chave = uf || 'BR';
      vistaAtual = v;
      if (chave === chaveVista) return;
      chaveVista = chave;
      figura.style.aspectRatio = Math.round(v.LARG) + '/' + Math.round(v.ALT);
      svg.setAttribute('viewBox', '0 0 ' + r1(v.LARG) + ' ' + r1(v.ALT));
      fundo.innerHTML = v.tiles.map(function (t) {
        return '<img alt="" decoding="async" referrerpolicy="no-referrer" src="' + GIBS + FUNDO.id + '/default/' + FUNDO.matriz + '/' + v.z + '/' + t[1] + '/' + t[0] + '.' + FUNDO.ext + '" style="left:' +
          pct((t[0] * TAM - v.X0) / v.LARG * 100) + ';top:' + pct((t[1] * TAM - v.Y0) / v.ALT * 100) + ';width:' + pct(TAM / v.LARG * 100) + ';height:' + pct(TAM / v.ALT * 100) + '">';
      }).join('');
      fundo.querySelectorAll('img').forEach(function (img) {
        img.addEventListener('error', function () { img.style.visibility = 'hidden'; });  // sem a imagem da NASA, as camadas seguem sobre o fundo escuro
      });
    }
    /* Estradas locais: dezenas de milhares de linhas por estado, num canvas para não pesar no celular. */
    function desenharLocais() {
      var dados = uf && !ocultos.locais && !ocultos.rodovias ? doUf(uf).locais : null;
      tela.hidden = !dados;
      if (!dados) return;
      var v = vistaAtual, dpr = Math.min(2, window.devicePixelRatio || 1), w = figura.clientWidth, h = figura.clientHeight, k = w * dpr / v.LARG, ctx = tela.getContext('2d');
      tela.width = Math.round(w * dpr); tela.height = Math.round(h * dpr);
      ctx.strokeStyle = 'rgba(226,232,240,.5)'; ctx.lineWidth = 0.7 * dpr; ctx.lineJoin = 'round';
      ctx.beginPath();
      dados.linhas.forEach(function (linha) {
        linha.forEach(function (p, i) {
          var x = (px(p[1], v.z) - v.X0) * k, y = (py(p[0], v.z) - v.Y0) * k;
          if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
        });
      });
      ctx.stroke();
    }
    function desenhar() {
      if (!ufs) return;
      trocarVista();
      var d = nac || {}, agora = new Date(), u = uf ? doUf(uf) : null, est = (u && u.est) || {};
      svg.innerHTML = uf ? svgEstado(d, est, { ufs: ufs, rodovias: u.rodovias }, ocultos, sel, uf) : svgBrasil(d, { ufs: ufs, federais: federais }, ocultos, sel);
      botaoLocais.hidden = !uf;
      dica.textContent = uf ? 'Toque numa rodovia ou numa área de aviso para ver o detalhe.' : 'Toque num estado para aproximar e ver as rodovias dele.';
      desenharLocais();
      if (!nac) return;
      var novoTopo = uf ? (u.est ? htmlTopo(veredito(est, agora), avisosEstado(est, agora)) : '') : htmlTopo(vereditoBrasil(nac, agora), avisosEstado(nac, agora));
      if (novoTopo !== topoHtml) { topo.innerHTML = topoHtml = novoTopo; }  // só muda quando os dados mudam: o leitor de tela não repete a cada toque
      if (!uf) alvo.innerHTML = painelBrasil(nac, agora, sel, nomes, true);
      else if (u.erro) alvo.innerHTML = '<div class="jtm-linha"><button type="button" class="jtm-limpar" data-jtm-voltar>← Brasil</button></div><p class="jtm-alerta" role="status">Os dados deste estado estão indisponíveis no momento. Sem verificação, a falta de alerta não quer dizer que não há risco.</p>';
      else if (!u.est) alvo.innerHTML = '<div class="jtm-linha"><button type="button" class="jtm-limpar" data-jtm-voltar>← Brasil</button></div><p class="jtm-fraco">Carregando ' + esc(nomes[uf] || uf) + '…</p>';
      else alvo.innerHTML = painelEstado(nac, est, agora, sel, uf, nomes[uf], u.rodovias ? u.rodovias.rodovias.map(function (r) { return r.sigla; }) : [], true, busca);
      hora.textContent = nac.atualizado_em ? 'verificado ' + horaBR(nac.atualizado_em) : 'sem verificação';
    }
    function carregarUf(u, forcar) {
      var reg = doUf(u);
      if (!reg.rodovias) json(op.geo + 'rodovias/' + u + '.json').then(function (j) { reg.rodovias = j; if (uf === u) desenhar(); }).catch(function () { reg.rodovias = null; });
      if (!reg.est || forcar) json(op.origem + '/' + u).then(function (j) { reg.est = j; reg.erro = false; if (uf === u) desenhar(); })
        .catch(function () { if (!reg.est) { reg.erro = true; if (uf === u) desenhar(); } });
    }
    function escolherUf(u) {
      uf = u || null; sel.rodovia = null; busca = ''; fecharBalao();
      if (uf) carregarUf(uf);
      desenhar();
      if (uf && el.scrollIntoView && window.matchMedia && window.matchMedia('(max-width: 899px)').matches) topo.scrollIntoView({ block: 'start' });
    }
    function marcarRodovia(sigla) { sel.rodovia = sel.rodovia === sigla ? null : sigla; fecharBalao(); desenhar(); }

    el.querySelectorAll('[data-jtm-camada]').forEach(function (b) {
      b.addEventListener('click', function () {
        var ligada = b.getAttribute('aria-pressed') !== 'true', camada = b.getAttribute('data-jtm-camada');
        b.setAttribute('aria-pressed', String(ligada));
        ocultos[camada] = !ligada;
        fecharBalao();
        if (camada === 'locais' && ligada && uf && !doUf(uf).locais) {
          var u = uf;
          json(op.geo + 'rodovias/' + u + '-locais.json').then(function (j) { doUf(u).locais = j; if (uf === u) desenharLocais(); }).catch(function () { b.setAttribute('aria-pressed', 'false'); ocultos.locais = true; });
        }
        desenhar();
      });
    });
    alvo.addEventListener('click', function (ev) {
      var b = ev.target.closest ? ev.target.closest('[data-jtm-rodovia],[data-jtm-dia],[data-jtm-uf],[data-jtm-voltar]') : null;
      if (!b) return;
      var via = b.getAttribute('data-jtm-rodovia'), dia = b.getAttribute('data-jtm-dia');
      if (b.hasAttribute('data-jtm-voltar')) { escolherUf(null); return; }
      if (b.hasAttribute('data-jtm-uf')) { escolherUf(b.getAttribute('data-jtm-uf')); return; }
      if (via) marcarRodovia(via); else { sel.dia = dia; fecharBalao(); desenhar(); }
      var de_novo = alvo.querySelector(via ? '.jtm-via-cartao[data-jtm-rodovia="' + via + '"]' : '[data-jtm-dia="' + dia + '"]');
      if (de_novo) de_novo.focus();  // o painel é redesenhado: devolve o foco ao botão usado
    });
    alvo.addEventListener('change', function (ev) {
      if (ev.target.hasAttribute && ev.target.hasAttribute('data-jtm-estado') && ev.target.value) escolherUf(ev.target.value);
    });
    alvo.addEventListener('input', function (ev) {
      if (!ev.target.hasAttribute || !ev.target.hasAttribute('data-jtm-busca') || !uf) return;
      busca = ev.target.value;  // só os cartões mudam: o campo mantém o foco e o cursor
      var u = doUf(uf), vias = alvo.querySelector('[data-jtm-vias]');
      if (vias && u.est) vias.innerHTML = htmlRodovias(u.est, nac || {}, sel, busca, u.rodovias ? u.rodovias.rodovias.map(function (r) { return r.sigla; }) : []);
    });
    svg.addEventListener('click', function (ev) {
      var t = ev.target, pega = function (n) { return t.getAttribute ? t.getAttribute(n) : null; };
      if (!uf && pega('data-uf')) { escolherUf(pega('data-uf')); return; }
      if (pega('data-rodovia-alvo')) { marcarRodovia(pega('data-rodovia-alvo')); return; }
      var id = pega('data-aviso'), a = id && nac ? (nac.avisos || []).filter(function (x) { return x.id === id; })[0] : null;
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
    window.addEventListener('resize', function () { if (!tela.hidden) desenharLocais(); });

    json(op.geo + 'ufs.json').then(function (j) { ufs = j.ufs; ufs.forEach(function (e) { nomes[e.uf] = e.nome; }); desenhar(); })
      .catch(function () { alvo.innerHTML = '<p class="jtm-alerta" role="status">O mapa está indisponível no momento. Confira os avisos no portal do INMET (avisos.inmet.gov.br).</p>'; });
    json(op.geo + 'rodovias/BR.json').then(function (j) { federais = j; desenhar(); }).catch(function () { federais = null; });
    function buscar() {
      json(op.origem).then(function (j) { nac = j; if (uf) carregarUf(uf, true); desenhar(); })
        .catch(function () {
          if (nac) return;  // mantém o último resumo com o carimbo de hora; o estado "atrasado" aparece sozinho
          hora.textContent = 'indisponível';
          alvo.innerHTML = '<p class="jtm-alerta" role="status">Os alertas estão indisponíveis no momento. Sem verificação, a falta de alerta não quer dizer que não há risco: confira o portal do INMET (avisos.inmet.gov.br).</p>';
        });
    }
    buscar();
    setInterval(buscar, 5 * 60000);  // a API tem cache de 5 min
  }

  function iniciar() {
    var el = document.querySelector('[data-janela-transporte-mapa]');
    if (el) montar(el, { origem: el.getAttribute('data-origem'), geo: el.getAttribute('data-geo') });
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
  }
  return { BRASIL: BRASIL, vista: vista, xy: xy, horaBR: horaBR, estadoDados: estadoDados, dias: dias, avisosDoDia: avisosDoDia, svgBrasil: svgBrasil, svgEstado: svgEstado,
    resumoEstados: resumoEstados, resumoRodovias: resumoRodovias, veredito: veredito, vereditoBrasil: vereditoBrasil, avisosEstado: avisosEstado,
    painelBrasil: painelBrasil, painelEstado: painelEstado, htmlRodovias: htmlRodovias };
});
