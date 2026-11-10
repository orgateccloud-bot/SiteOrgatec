/* Mapa da viagem (Central e Portal). Duas partes:
   - camadas(): transforma o resultado da viagem, os lançamentos e a posição em marcadores com detalhes e fonte. É pura e testada no Node.
   - criar(): mapa real do Google (Maps JavaScript API), satélite com rótulos e alternância para ruas.
   Termos do Google Maps Platform: a rota (Routes API) e os postos (Places API) só podem aparecer em mapa Google ou sem mapa nenhum.
   Por isso não há outro mapa de fundo: sem chave, ou se o Google recusar, a tela volta ao diagrama SVG (transporte-viagem.js). */
(function (raiz) {
  'use strict';

  var TIPOS = {
    origem: { rotulo: 'Origem', cor: '#0b3d91', letra: 'A' },
    destino: { rotulo: 'Destino', cor: '#0b3d91', letra: 'B' },
    parada: { rotulo: 'Parada', cor: '#0b3d91', letra: '' },
    pedagio: { rotulo: 'Pedágio', cor: '#2563eb', letra: 'P' },
    posto: { rotulo: 'Posto', cor: '#ea580c', letra: 'C' },
    bloqueio: { rotulo: 'Bloqueio', cor: '#dc2626', letra: '!' },
    pernoite: { rotulo: 'Pernoite', cor: '#7c3aed', letra: 'N' },
    lancamento: { rotulo: 'Informado', cor: '#0f766e', letra: 'M' },
    caminhao: { rotulo: 'Caminhão', cor: '#16a34a', letra: '▲' }
  };
  /* Grupos que a legenda liga e desliga (origem, destino e paradas andam juntos). */
  var GRUPOS = [['pontos', 'Origem, destino e paradas'], ['pedagio', 'Pedágios'], ['posto', 'Postos'], ['bloqueio', 'Bloqueios'],
    ['pernoite', 'Pernoites'], ['lancamento', 'Lançamentos'], ['caminhao', 'Caminhão']];
  var ROTULO_LANC = { abastecimento: 'Abastecimento', pedagio_pago: 'Pedágio pago', parada: 'Parada', ocorrencia: 'Ocorrência', posicao_manual: 'Posição informada' };

  var brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  var num1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
  var quando = new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

  function grupo(tipo) { return tipo === 'origem' || tipo === 'destino' || tipo === 'parada' ? 'pontos' : tipo; }
  function temCoord(p) { return p && typeof p.lat === 'number' && typeof p.lon === 'number' && isFinite(p.lat) && isFinite(p.lon); }
  function km(v) { return v == null ? 'sem dado' : 'km ' + num1.format(v); }

  /* Ponto da rota a uma distância (km de estrada) da origem, proporcional ao traçado. */
  function pontoNoKm(g, total, alvoKm) {
    if (!g.length) return null;
    var acc = [0];
    for (var i = 1; i < g.length; i++) acc.push(acc[i - 1] + Math.hypot(g[i][0] - g[i - 1][0], g[i][1] - g[i - 1][1]));
    var alvo = total ? alvoKm / total * acc[acc.length - 1] : 0;
    for (var j = 1; j < acc.length; j++) if (acc[j] >= alvo) {
      var f = (alvo - acc[j - 1]) / ((acc[j] - acc[j - 1]) || 1);
      return [g[j - 1][0] + (g[j][0] - g[j - 1][0]) * f, g[j - 1][1] + (g[j][1] - g[j - 1][1]) * f];
    }
    return g[g.length - 1];
  }

  /* Posição atual: telemetria quando houver; senão a última posição informada à mão. */
  function posicaoAtual(posicao, lancamentos) {
    if (temCoord(posicao)) return { lat: posicao.lat, lon: posicao.lon, ts: posicao.ts, telemetria: true, evt: posicao };
    var manual = (lancamentos || []).filter(function (l) { return l.tipo === 'posicao_manual' && temCoord(l); })
      .sort(function (a, b) { return a.ts < b.ts ? 1 : -1; })[0];
    return manual ? { lat: manual.lat, lon: manual.lon, ts: manual.ts, telemetria: false, lanc: manual } : null;
  }

  function camadas(r, extras) {
    extras = extras || {};
    var g = (r.rota && r.rota.geometria) || [], m = [];
    function add(tipo, id, p, titulo, linhas, fonte) { if (temCoord(p)) m.push({ id: id, tipo: tipo, grupo: grupo(tipo), lat: p.lat, lon: p.lon, titulo: titulo, linhas: linhas, fonte: fonte }); }

    var n = (r.pontos || []).length;
    (r.pontos || []).forEach(function (p, i) {
      var tipo = i === 0 ? 'origem' : (i === n - 1 ? 'destino' : 'parada');
      add(tipo, 'ponto-' + i, p, TIPOS[tipo].rotulo + ': ' + p.nome + (p.uf ? '/' + p.uf : ''), [['Posição na rota', km(p.km)]],
        p.lat == null ? '' : 'informado na viagem ou localizado pelo provedor de rota');
    });
    (r.pedagios || []).forEach(function (p, i) {
      add('pedagio', 'pedagio-' + i, p, 'Pedágio: ' + p.nome, [
        ['Posição na rota', km(p.km)],
        ['Valor para ' + (p.eixos || '?') + ' eixos', p.valor != null ? brl.format(Number(p.valor)) + (p.tarifa_oficial ? '' : ' (estimado)') : 'sem dado'],
        ['Tarifa por eixo (cat. 1)', p.tarifa_cat1 != null ? brl.format(Number(p.tarifa_cat1)) : 'sem dado']
      ], p.fonte || 'ANTT, dados abertos');
    });
    (r.postos || []).forEach(function (p, i) {
      add('posto', 'posto-' + i, p, 'Posto: ' + p.nome, [
        ['Endereço', p.endereco || 'sem dado'], ['Posição na rota', km(p.km)],
        ['Diesel S10 (referência)', p.preco_diesel_referencia != null ? brl.format(Number(p.preco_diesel_referencia)) : 'não disponível'],
        ['Origem do preço', p.preco_fonte || 'não disponível']
      ], p.fonte || 'Google Places');
    });
    (r.bloqueios || []).forEach(function (b, i) {
      add('bloqueio', 'bloqueio-' + i, b, 'Bloqueio: ' + b.descricao, [['Posição na rota', km(b.km)],
        ['Passagem prevista', b.passagem_prevista ? quando.format(new Date(b.passagem_prevista)) : 'sem dado']], b.fonte);
    });
    ((r.jornada && r.jornada.eventos) || []).filter(function (e) { return e.tipo === 'pernoite'; }).forEach(function (e, i) {
      var p = pontoNoKm(g, r.rota.distancia_km, e.km_inicio);
      if (p) add('pernoite', 'pernoite-' + i, { lat: p[0], lon: p[1] }, 'Pernoite previsto', [['Posição na rota', km(e.km_inicio)],
        ['Início', quando.format(new Date(e.inicio))]], 'Plano de jornada (parâmetros da transportadora)');
    });
    (extras.lancamentos || []).forEach(function (l) {
      if (l.tipo === 'posicao_manual') return;  // a posição informada vira o caminhão quando não há telemetria
      var linhas = [['Quando', quando.format(new Date(l.ts))]];
      if (l.local) linhas.push(['Local', l.local]);
      if (l.valor != null) linhas.push(['Valor', brl.format(Number(l.valor))]);
      if (l.litros != null) linhas.push(['Litros', num1.format(Number(l.litros))]);
      if (l.preco_l != null) linhas.push(['Preço por litro', brl.format(Number(l.preco_l))]);
      if (l.observacao) linhas.push(['Observação', l.observacao]);
      add('lancamento', 'lanc-' + l.id, l, (ROTULO_LANC[l.tipo] || l.tipo) + (l.local ? ': ' + l.local : ''), linhas, 'informado manualmente');
    });
    var pos = posicaoAtual(extras.posicao, extras.lancamentos);
    if (pos) {
      var e = pos.evt || {}, linhas = [['Quando', quando.format(new Date(pos.ts))]];
      if (e.km_percorrido != null) linhas.push(['Percorrido', km(e.km_percorrido)]);
      if (e.velocidade_kmh != null) linhas.push(['Velocidade', num1.format(e.velocidade_kmh) + ' km/h']);
      if (e.fora_da_rota) linhas.push(['Desvio', num1.format(e.desvio_km) + ' km fora da rota']);
      add('caminhao', 'caminhao', pos, pos.telemetria ? 'Posição atual (telemetria)' : 'Última posição informada', linhas,
        pos.telemetria ? 'telemetria: ' + (e.sensor || 'rastreador') : 'informado manualmente');
    }
    return { rota: g, marcadores: m, posicao: pos };
  }

  /* ---------- Google Maps ---------- */
  var carregando = null, falhaAuth = [], authRecusada = false;
  function aoRecusar(f) { if (authRecusada) f(new Error('chave do mapa recusada pelo Google')); else falhaAuth.push(f); }

  function carregarGoogle(chave) {
    if (raiz.google && raiz.google.maps && raiz.google.maps.importLibrary) return Promise.resolve(raiz.google.maps);
    if (carregando) return carregando;
    carregando = new Promise(function (ok, falha) {
      var pronto = '__otMapaPronto', relogio = setTimeout(function () { falha(new Error('o mapa não respondeu')); }, 20000);
      raiz[pronto] = function () { clearTimeout(relogio); ok(raiz.google.maps); };
      /* O Google chama esta função quando recusa a chave (domínio fora da restrição, API desligada, cobrança). */
      raiz.gm_authFailure = function () {
        authRecusada = true;
        falhaAuth.forEach(function (f) { f(new Error('chave do mapa recusada pelo Google')); });
        falha(new Error('chave recusada'));
      };
      var s = document.createElement('script');
      s.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(chave) + '&v=weekly&language=pt-BR&region=BR&loading=async&callback=' + pronto;
      s.async = true;
      s.onerror = function () { clearTimeout(relogio); falha(new Error('não foi possível carregar o mapa')); };
      document.head.appendChild(s);
    });
    carregando.catch(function () { carregando = null; });
    return carregando;
  }

  function detalheNo(mk) {
    var div = document.createElement('div'), h = document.createElement('strong'), dl = document.createElement('dl'), f = document.createElement('p');
    div.className = 'ot-info';
    h.textContent = mk.titulo; div.appendChild(h);
    mk.linhas.forEach(function (l) {
      var dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = l[0]; dd.textContent = l[1]; dl.appendChild(dt); dl.appendChild(dd);
    });
    div.appendChild(dl);
    f.textContent = 'Fonte: ' + (mk.fonte || 'não informada'); div.appendChild(f);
    return div;
  }

  function pino(tipo) {
    var t = TIPOS[tipo], el = document.createElement('div');
    el.className = 'ot-pino ot-pino-' + tipo;
    el.style.background = t.cor;
    el.textContent = t.letra;
    return el;
  }

  /* cfg: { chave, map_id }. Devolve a instância quando o mapa carrega; rejeita se o Google recusar ou não responder. */
  function criar(el, cfg, aoFalhar) {
    return carregarGoogle(cfg.chave).then(function (gm) {
      return Promise.all([gm.importLibrary('maps'), gm.importLibrary('marker')]).then(function (libs) {
        var maps = libs[0], marker = libs[1], avancado = !!cfg.map_id;
        var mapa = new maps.Map(el, {
          center: { lat: -14.2, lng: -51.9 }, zoom: 4, mapTypeId: 'hybrid', mapId: cfg.map_id || undefined,
          mapTypeControl: true, mapTypeControlOptions: { mapTypeIds: ['hybrid', 'satellite', 'roadmap', 'terrain'] },
          streetViewControl: false, fullscreenControl: true, clickableIcons: false, gestureHandling: 'cooperative'
        });
        var info = new maps.InfoWindow(), linhas = [], marcas = {}, ocultos = {}, clique = null, chaveViagem = null;
        if (aoFalhar) aoRecusar(aoFalhar);  // a recusa pode chegar antes ou depois de o mapa existir
        mapa.addListener('click', function (ev) { if (clique && ev.latLng) clique(ev.latLng.lat(), ev.latLng.lng()); });

        function limpar() {
          linhas.forEach(function (l) { l.setMap(null); }); linhas = [];
          Object.keys(marcas).forEach(function (k) { marcas[k].setMap ? marcas[k].setMap(null) : (marcas[k].map = null); });
          marcas = {};
        }
        function mostrar(obj, sim) { if (obj.setMap) obj.setMap(sim ? mapa : null); else obj.map = sim ? mapa : null; }
        function marcar(mk) {
          var pos = { lat: mk.lat, lng: mk.lon }, t = TIPOS[mk.tipo], obj;
          if (avancado) {
            obj = new marker.AdvancedMarkerElement({ position: pos, map: mapa, title: mk.titulo, content: pino(mk.tipo), zIndex: mk.tipo === 'caminhao' ? 10 : 1 });
            obj.addListener('gmp-click', function () { info.setContent(detalheNo(mk)); info.open({ map: mapa, anchor: obj }); });
          } else {
            obj = new marker.Marker({ position: pos, map: mapa, title: mk.titulo, zIndex: mk.tipo === 'caminhao' ? 10 : 1,
              icon: { path: raiz.google.maps.SymbolPath.CIRCLE, scale: mk.tipo === 'caminhao' ? 10 : 8, fillColor: t.cor, fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 },
              label: t.letra ? { text: t.letra, color: '#fff', fontSize: '10px', fontWeight: '700' } : null });
            obj.addListener('click', function () { info.setContent(detalheNo(mk)); info.open({ map: mapa, anchor: obj }); });
          }
          if (ocultos[mk.grupo]) mostrar(obj, false);
          marcas[mk.id] = obj;
          obj.__dados = mk;
        }

        var inst = {
          /* Redesenha tudo. Só reenquadra quando muda a viagem (atualizações da mesma viagem mantêm o zoom do usuário). */
          desenhar: function (dados, idViagem) {
            limpar();
            if (dados.rota.length) {
              var caminho = dados.rota.map(function (p) { return { lat: p[0], lng: p[1] }; });
              linhas.push(new maps.Polyline({ path: caminho, map: mapa, strokeColor: '#0b1f3a', strokeOpacity: 0.9, strokeWeight: 8 }));
              linhas.push(new maps.Polyline({ path: caminho, map: mapa, strokeColor: '#38bdf8', strokeOpacity: 1, strokeWeight: 4 }));
            }
            dados.marcadores.forEach(marcar);
            if (idViagem !== chaveViagem) {
              chaveViagem = idViagem;
              var b = new raiz.google.maps.LatLngBounds(), vazio = true;  // LatLngBounds é da biblioteca core, não da maps
              dados.rota.forEach(function (p) { b.extend({ lat: p[0], lng: p[1] }); vazio = false; });
              dados.marcadores.forEach(function (mk) { b.extend({ lat: mk.lat, lng: mk.lon }); vazio = false; });
              if (!vazio) mapa.fitBounds(b, 40);
            }
          },
          visivel: function (grp, sim) {
            ocultos[grp] = !sim;
            Object.keys(marcas).forEach(function (k) { if (marcas[k].__dados.grupo === grp) mostrar(marcas[k], sim); });
          },
          focar: function (id) {
            var obj = marcas[id];
            if (!obj) return;
            mapa.panTo({ lat: obj.__dados.lat, lng: obj.__dados.lon });
            if (mapa.getZoom() < 12) mapa.setZoom(12);
            info.setContent(detalheNo(obj.__dados)); info.open({ map: mapa, anchor: obj });
          },
          aoClicar: function (f) { clique = f; }
        };
        return inst;
      });
    });
  }

  var api = { TIPOS: TIPOS, GRUPOS: GRUPOS, ROTULO_LANC: ROTULO_LANC, camadas: camadas, pontoNoKm: pontoNoKm, posicaoAtual: posicaoAtual, criar: criar };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else raiz.OTMapa = api;
})(typeof window !== 'undefined' ? window : globalThis);
