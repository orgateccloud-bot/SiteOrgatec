/* Componente único da viagem: o mesmo na Central (motorista/gestor) e no Portal (cliente). O mapa vem de transporte-mapa.js. */
(function (raiz) {
  'use strict';
  var OT = raiz.OT, esc = OT.esc, Mapa = raiz.OTMapa;
  var ROTULO_EVENTO = { direcao: 'Direção', pausa: 'Pausa obrigatória', refeicao: 'Refeição', pernoite: 'Pernoite / descanso', parada: 'Parada (carga/descarga)', chegada: 'Chegada' };
  var ROTULO_FONTE = { rota: 'Rota', combustivel: 'Combustível', pedagio: 'Pedágio', postos: 'Postos', bloqueios: 'Bloqueios', clima: 'Clima', tempo: 'Tempo de direção' };

  /* O mapa do Google é criado uma vez por página (cada criação conta como um carregamento cobrado) e reaproveitado a cada redesenho. */
  var mapa = { el: null, inst: null, falhou: false, chave: null, carregando: null };
  var ultimo = { alvo: null, v: null, opcoes: null };

  /* opcoes: editavel, aoAjustar, aoRecalcular, mapa {chave, map_id}, lancamentos, posicao (telemetria), telemetria (bool),
     aoLancar(corpo) -> Promise, aoRemoverLancamento(id), papel, usuario. */
  function renderizar(alvo, v, opcoes) {
    opcoes = opcoes || {};
    ultimo = { alvo: alvo, v: v, opcoes: opcoes };
    var r = v.resultado, j = r.jornada, d = r.despesas, expirado = !!r.coordenadas_expiradas;
    alvo.innerHTML =
      '<div class="kpis">' +
        kpi(OT.num1.format(r.rota.distancia_km) + ' km', 'distância') +
        kpi(OT.horas(j.duracao_total_h), 'tempo total (' + OT.horas(j.direcao_h) + ' dirigindo)') +
        kpi(OT.diaHora.format(new Date(j.chegada_prevista)), 'chegada prevista') +
        kpi(j.pernoites + ' / ' + j.pausas, 'pernoites / pausas') +
        kpi(OT.brl.format(Number(d.total)), 'despesa prevista') +
        kpi(OT.brl.format(Number(d.custo_por_km)), 'custo por km') +
      '</div>' + cartaoAlertas(opcoes) +
      '<div class="cartao mapa-cartao">' +
        '<div class="mapa-topo"><h2>Mapa da viagem ' + (v.status ? '<span class="tag t-ok">' + esc(v.status.replace('_', ' ')) + '</span>' : '') + '</h2>' +
          '<span class="fonte" data-mapa-fonte></span></div>' +
        (expirado ? '<div class="msg aviso">O traçado e as coordenadas do Google foram apagados 30 dias após o cálculo, como exigem os termos do Google Maps. ' +
          (opcoes.aoRecalcular ? 'Use “Recalcular viagem” para ver o mapa de novo.' : 'Peça ao gestor para recalcular a viagem.') + '</div>' : '') +
        '<div class="mapa-grade">' +
          '<div class="mapa-area"><div class="mapa-slot" data-mapa></div><div class="legenda" data-legenda>' + legenda() + '</div></div>' +
          '<aside class="mapa-lado">' +
            '<div data-vivo>' + caixaPosicao(v, opcoes) + '</div>' +
            listaPedagios(r.pedagios || []) + listaPostos(r.postos || [], r.fontes.postos) + listaLancamentos(opcoes) +
            (opcoes.aoRecalcular ? '<div class="acoes"><button type="button" class="mini sec" data-recalcular>Recalcular viagem</button></div>' : '') +
          '</aside>' +
        '</div>' +
      '</div>' +
      '<div class="duas">' +
        '<div class="cartao"><h2>Despesas previstas</h2><div class="rolagem">' + tabelaDespesas(d, opcoes.editavel) + '</div></div>' +
        '<div class="cartao"><h2>Linha do tempo</h2><ul class="tempo">' + linhaTempo(j.eventos) + '</ul>' +
          '<p class="fonte">Limites de direção e descanso são parâmetros (CTB art. 67-C) — revisão jurídica pendente.</p></div>' +
      '</div>' +
      '<div class="duas">' +
        '<div><div class="cartao"><h2>Bloqueios e interdições</h2>' + bloqueios(r.bloqueios) + '</div>' +
          '<div class="cartao"><h2>Previsão do tempo no trajeto</h2>' + clima(r.clima) + '</div></div>' +
        '<div class="cartao"><h3>Fontes desta estimativa</h3>' + fontes(r) + '</div>' +
      '</div>';
    montarMapa(alvo, v, opcoes);
    ligarPainel(alvo, v, opcoes);
    if (opcoes.editavel && opcoes.aoAjustar) ligarAjustes(alvo, opcoes.aoAjustar);
  }

  /* ---------- Alertas de clima e desastres na rota (só com ORGATEC_TRANSPORTE_ALERTAS) ---------- */
  var ROTULO_ORIGEM = { inmet: 'INMET', firms: 'NASA FIRMS', inpe: 'INPE Queimadas' };
  var ESTADO_FONTE = { ok: ['t-ok', 'ok'], indisponivel: ['t-erro', 'indisponível'], desligada: ['t-simulado', 'desligada'] };
  var ESTADO_ENVIO = { enviada: 'enviada', entregue: 'entregue', lida: 'lida', falhou: 'falhou', sem_consentimento: 'sem consentimento',
    bloqueada_teto: 'bloqueada pelo teto', canal_desligado: 'canal desligado' };
  var VERIFICACAO_ATRASADA_MIN = 40;  // o job roda a cada 15 min

  function linhaFontes(d) {
    var chaves = Object.keys(d.fontes || {});
    if (!d.atualizado_em || !chaves.length) {
      return '<div class="msg aviso">A verificação automática ainda não rodou para esta transportadora. Sem verificação, a falta de alerta não quer dizer que não há risco.</div>';
    }
    var chips = chaves.map(function (k) {
      var f = d.fontes[k], e = ESTADO_FONTE[f.estado] || ['t-aviso', f.estado];
      return '<span class="fonte-chip" title="' + esc(f.credito + (f.detalhe ? ' — ' + f.detalhe : '')) + '">' + esc(ROTULO_ORIGEM[k] || k) + ' <span class="tag ' + e[0] + '">' + esc(e[1]) + '</span></span>';
    }).join('');
    var min = Math.round((Date.now() - new Date(d.atualizado_em).getTime()) / 60000), avisos = [];
    var fora = chaves.filter(function (k) { return d.fontes[k].estado === 'indisponivel'; }).map(function (k) { return ROTULO_ORIGEM[k] || k; });
    if (fora.length) avisos.push(fora.join(' e ') + ' sem resposta na última verificação: a falta de alerta dessa fonte não quer dizer que não há risco.');
    if (min > VERIFICACAO_ATRASADA_MIN) avisos.push('A última verificação foi há ' + min + ' min (o normal é a cada 15 min).');
    return '<div class="fontes-alerta">' + chips + '<span class="fonte">verificado em ' + esc(OT.diaHora.format(new Date(d.atualizado_em))) + '</span></div>' +
      avisos.map(function (t) { return '<div class="msg aviso">' + esc(t) + '</div>'; }).join('');
  }

  function itemAlerta(a, opcoes) {
    var al = a.alerta, t = Mapa.TIPO_ALERTA[al.tipo] || Mapa.TIPO_ALERTA.outro, ativo = a.estado === 'ativo';
    var cor = Mapa.COR_GRAVIDADE[al.gravidade] || '#ea580c';
    var quando = a.chegada_prevista ? OT.diaHora.format(new Date(a.chegada_prevista)) : 'sem dado';
    return '<li class="alerta-item' + (ativo ? '' : ' encerrado') + '" style="--g:' + cor + '">' +
      '<div class="alerta-topo"><span class="alerta-icone" aria-hidden="true">' + esc(t[1]) + '</span><b>' + esc(t[0]) + '</b>' +
        '<span class="tag tag-g">' + esc(Mapa.ROTULO_GRAVIDADE[al.gravidade] || al.gravidade) + '</span>' +
        (ativo ? '' : ' <span class="tag t-simulado">' + esc(a.estado) + '</span>') + (a.visto ? ' <span class="tag t-ok">visto</span>' : '') + '</div>' +
      '<div>' + esc(al.titulo) + '</div>' +
      '<small>km ' + OT.num1.format(a.km_ini) + (a.km_fim > a.km_ini ? ' a ' + OT.num1.format(a.km_fim) : '') + ' · chega por volta de ' + esc(quando) +
        ' (' + (a.posicao_fonte === 'telemetria' ? 'pela telemetria' : 'pelo plano') + ') · vale até ' + esc(OT.diaHora.format(new Date(al.fim))) + '</small>' +
      ((al.riscos || al.instrucoes) ? '<details><summary class="fonte">riscos e o que fazer</summary><p>' + esc(al.riscos || '') + '</p><p><b>' + esc(al.instrucoes || '') + '</b></p></details>' : '') +
      '<div class="fonte">Fonte: ' + (al.link ? '<a href="' + esc(al.link) + '" target="_blank" rel="noopener noreferrer">' + esc(al.fonte) + '</a>' : esc(al.fonte)) + '</div>' +
      '<div class="acoes">' + (a.lat != null ? '<button type="button" class="mini sec" data-focar="alerta-' + esc(a.id) + '">ver no mapa</button>' : '') +
        (ativo && !a.visto && opcoes.aoMarcarVisto ? '<button type="button" class="mini" data-visto="' + esc(a.id) + '">marcar como visto</button>' : '') + '</div></li>';
  }

  function tabelaEnvios(coms) {
    if (!coms || !coms.length) return '';
    return '<details><summary>Avisos ao motorista <span class="fonte">(' + coms.length + ')</span></summary><div class="rolagem"><table><thead><tr><th>Quando</th><th>Canal</th><th>Situação</th><th>Destino</th></tr></thead><tbody>' +
      coms.map(function (c) {
        var ruim = ['falhou', 'sem_consentimento', 'bloqueada_teto', 'canal_desligado'].indexOf(c.estado) >= 0;
        return '<tr><td>' + esc(OT.diaHora.format(new Date(c.enviada_em))) + '</td><td>' + esc(c.canal === 'sms' ? 'SMS' : 'WhatsApp') + '</td>' +
          '<td><span class="tag ' + (ruim ? 't-erro' : 't-ok') + '">' + esc(ESTADO_ENVIO[c.estado] || c.estado) + '</span>' + (c.detalhe ? '<div class="fonte">' + esc(c.detalhe) + '</div>' : '') + '</td>' +
          '<td class="fonte">' + esc(c.destino || '—') + '</td></tr>';
      }).join('') + '</tbody></table></div></details>';
  }

  function cartaoAlertas(opcoes) {
    var d = opcoes.alertas;
    if (!d) return '';
    var ativos = (d.alertas || []).filter(function (a) { return a.estado === 'ativo'; });
    var outros = (d.alertas || []).filter(function (a) { return a.estado !== 'ativo'; }).slice(0, 5);
    var corpo = ativos.length ? '<ul class="lista-alertas">' + ativos.map(function (a) { return itemAlerta(a, opcoes); }).join('') + '</ul>'
      : '<p class="vazio-curto">Nenhum alerta ativo no trecho que falta' + (d.atualizado_em ? '' : ' (sem verificação ainda)') + '.</p>';
    return '<div class="cartao cartao-alertas"><div class="mapa-topo"><h2>Alertas de clima e desastres no trajeto ' +
        (ativos.length ? '<span class="tag t-erro">' + ativos.length + ' ativo(s)</span>' : '') + '</h2></div>' +
      linhaFontes(d) + corpo +
      (outros.length ? '<details><summary class="fonte">Encerrados recentes (' + outros.length + ')</summary><ul class="lista-alertas">' +
        outros.map(function (a) { return itemAlerta(a, opcoes); }).join('') + '</ul></details>' : '') +
      tabelaEnvios(opcoes.comunicacoes) +
      '<p class="fonte">Interdição de rodovia não tem fonte oficial em tempo real (PRF, DNIT e ANTT não publicam): registre em Bloqueios. Deslizamento e enchente aparecem só pelo aviso de chuva do INMET.</p></div>';
  }

  function kpi(valor, rotulo) { return '<div class="kpi"><b>' + esc(valor) + '</b><span>' + esc(rotulo) + '</span></div>'; }

  function legenda() {
    return Mapa.GRUPOS.map(function (g) {
      var t = Mapa.TIPOS[g[0] === 'pontos' ? 'origem' : g[0]];
      return '<label><input type="checkbox" data-grupo="' + g[0] + '" checked><i style="background:' + t.cor + '"></i>' + esc(g[1]) + '</label>';
    }).join('');
  }

  function caixaPosicao(v, opcoes) {
    var pos = Mapa.posicaoAtual(opcoes.posicao, opcoes.lancamentos);
    if (pos && pos.telemetria) return linhaPosicao(v, pos.evt);
    var sem = opcoes.telemetria ? 'Sem dado de telemetria para esta viagem ainda.' : 'Sem telemetria: nenhum rastreador conectado nesta instalação.';
    if (pos) return '<div class="msg aviso">' + esc(sem) + ' Última posição informada à mão em ' + esc(OT.diaHora.format(new Date(pos.ts))) + '.</div>';
    return '<div class="msg aviso">' + esc(sem) + '</div>';
  }

  function linhaPosicao(v, evt) {
    return '<div class="msg ' + (evt.fora_da_rota ? 'aviso' : 'ok') + '"><span class="ao-vivo">Posição</span> ' +
      esc(OT.diaHora.format(new Date(evt.ts))) +
      (evt.km_percorrido != null ? ' · km ' + OT.num1.format(evt.km_percorrido) + ' de ' + OT.num1.format(v.resultado.rota.distancia_km) : '') +
      (evt.velocidade_kmh != null ? ' · ' + OT.num1.format(evt.velocidade_kmh) + ' km/h' : '') +
      (evt.temperatura_c != null ? ' · baú ' + OT.num1.format(evt.temperatura_c) + ' °C' : '') +
      (evt.combustivel_pct != null ? ' · tanque ' + OT.num1.format(evt.combustivel_pct) + '%' : '') +
      (evt.fora_da_rota ? ' · <b>fora da rota (' + OT.num1.format(evt.desvio_km) + ' km)</b>' : '') + ' · telemetria: ' + esc(evt.sensor) + '</div>';
  }

  function itemLista(id, titulo, detalhe) {
    return '<li><button type="button" class="link" data-focar="' + esc(id) + '">' + esc(titulo) + '</button><small>' + detalhe + '</small></li>';
  }

  function listaPedagios(ps) {
    var total = ps.reduce(function (s, p) { return s + Number(p.valor || 0); }, 0);
    var corpo = ps.length ? '<ul class="lista-mapa">' + ps.map(function (p, i) {
      return itemLista('pedagio-' + i, p.nome, 'km ' + OT.num1.format(p.km) + ' · ' + (p.valor != null ? OT.brl.format(Number(p.valor)) : 'sem valor') +
        (p.tarifa_oficial ? '' : ' <span class="tag t-parametro">estimado</span>') + '<span class="fonte"> · ' + esc(p.fonte || '') + '</span>');
    }).join('') + '</ul>' : '<p class="vazio">Nenhuma praça de pedágio na rota.</p>';
    return '<details open><summary>Pedágios <span class="fonte">(' + ps.length + ' · ' + OT.brl.format(total) + ')</span></summary>' + corpo + '</details>';
  }

  function listaPostos(ps, fonte) {
    var corpo;
    if (!ps.length && fonte && fonte.estado !== 'ok') {
      corpo = '<p class="vazio">' + esc(fonte.fonte) + (fonte.detalhe ? ' — ' + esc(fonte.detalhe) : '') + '.</p>';
    } else if (!ps.length) {
      corpo = '<p class="vazio">' + (fonte ? 'Nenhum posto encontrado a até 3 km da rota.' : 'Busca de postos não feita nesta viagem (recalcule).') + '</p>';
    } else {
      corpo = '<ul class="lista-mapa">' + ps.map(function (p, i) {
        return itemLista('posto-' + i, p.nome, 'km ' + OT.num1.format(p.km) + (p.municipio ? ' · ' + esc(p.municipio) + (p.uf ? '/' + esc(p.uf) : '') : '') +
          ' · diesel ' + (p.preco_diesel_referencia ? OT.brl.format(Number(p.preco_diesel_referencia)) + ' <span class="fonte">(média ANP)</span>' : '<span class="fonte">preço não disponível</span>'));
      }).join('') + '</ul><p class="fonte">Postos: Google Places. Preço: média da ANP no município (ou na UF), não é o preço do posto.</p>';
    }
    return '<details' + (ps.length ? '' : ' open') + '><summary>Postos <span class="fonte">(' + ps.length + ')</span></summary>' + corpo + '</details>';
  }

  function listaLancamentos(opcoes) {
    var ls = opcoes.lancamentos || [];
    var corpo = ls.length ? '<ul class="lista-mapa">' + ls.map(function (l) {
      var det = esc(OT.diaHora.format(new Date(l.ts))) + (l.valor != null ? ' · ' + OT.brl.format(Number(l.valor)) : '') +
        (l.litros != null ? ' · ' + OT.num1.format(Number(l.litros)) + ' l' : '') + (l.observacao ? ' · ' + esc(l.observacao) : '') +
        '<span class="fonte"> · informado manualmente</span>' +
        (opcoes.aoRemoverLancamento && (opcoes.papel === 'gestor' || l.autor_id === opcoes.usuario)
          ? ' <button type="button" class="mini sec" data-remover="' + esc(l.id) + '" title="Remover lançamento">remover</button>' : '');
      var titulo = (Mapa.ROTULO_LANC[l.tipo] || l.tipo) + (l.local ? ': ' + l.local : '');
      return l.lat != null ? itemLista(l.tipo === 'posicao_manual' ? 'caminhao' : 'lanc-' + l.id, titulo, det) : '<li><b>' + esc(titulo) + '</b><small>' + det + '</small></li>';
    }).join('') + '</ul>' : '<p class="vazio">Nenhum lançamento.</p>';
    return '<details' + (ls.length ? ' open' : '') + '><summary>Lançamentos <span class="fonte">(' + ls.length + ')</span></summary>' + corpo +
      (opcoes.aoLancar ? formLancamento() : '') + '</details>';
  }

  function formLancamento() {
    var tipos = Object.keys(Mapa.ROTULO_LANC).map(function (k) { return '<option value="' + k + '">' + esc(Mapa.ROTULO_LANC[k]) + '</option>'; }).join('');
    return '<form class="form-lanc" data-form-lanc novalidate><h3>Novo lançamento</h3>' +
      '<div class="linha"><div><label>Tipo</label><select name="tipo">' + tipos + '</select></div><div><label>Quando</label><input name="ts" type="datetime-local" required></div></div>' +
      '<label>Local</label><input name="local" maxlength="120" placeholder="Posto, cidade ou km">' +
      '<div class="linha"><div><label>Valor (R$)</label><input name="valor" type="number" min="0" step="0.01"></div>' +
      '<div data-so-abastecimento><label>Litros</label><input name="litros" type="number" min="0" step="0.01"></div>' +
      '<div data-so-abastecimento><label>R$/l</label><input name="preco_l" type="number" min="0" step="0.001"></div></div>' +
      '<div class="linha"><div><label>Latitude</label><input name="lat" type="number" step="any"></div><div><label>Longitude</label><input name="lon" type="number" step="any"></div></div>' +
      '<p class="fonte" data-dica-mapa hidden>Clique no mapa para preencher a posição.</p>' +
      '<label>Observação</label><input name="observacao" maxlength="300">' +
      '<div data-msg-lanc></div><div class="acoes"><button type="submit" class="mini">Salvar lançamento</button></div></form>';
  }

  function agoraLocal() {
    return new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      .format(new Date()).replace(' ', 'T');
  }

  function mapaAtivo() { return mapa.inst && !mapa.falhou; }

  function ligarClique(alvo) {
    var f = alvo.querySelector('[data-form-lanc]');
    if (!f || !mapaAtivo()) return;
    mapa.inst.aoClicar(function (la, lo) { f.lat.value = la.toFixed(5); f.lon.value = lo.toFixed(5); });
    f.querySelector('[data-dica-mapa]').hidden = false;
  }

  function ligarPainel(alvo, v, opcoes) {
    alvo.querySelectorAll('[data-grupo]').forEach(function (cb) {
      cb.addEventListener('change', function () { if (mapaAtivo()) mapa.inst.visivel(cb.dataset.grupo, cb.checked); else desenharSvg(alvo, v, opcoes); });
    });
    alvo.querySelectorAll('[data-focar]').forEach(function (b) {
      b.addEventListener('click', function () { if (mapaAtivo()) mapa.inst.focar(b.dataset.focar); });
    });
    alvo.querySelectorAll('[data-visto]').forEach(function (b) {
      b.addEventListener('click', function () { b.disabled = true; opcoes.aoMarcarVisto(b.dataset.visto); });
    });
    var rec = alvo.querySelector('[data-recalcular]');
    if (rec) rec.addEventListener('click', function () { rec.disabled = true; rec.textContent = 'Recalculando…'; opcoes.aoRecalcular(); });
    alvo.querySelectorAll('[data-remover]').forEach(function (b) {
      b.addEventListener('click', function () { b.disabled = true; opcoes.aoRemoverLancamento(b.dataset.remover); });
    });
    var f = alvo.querySelector('[data-form-lanc]');
    if (!f) return;
    f.ts.value = agoraLocal();
    function ajustarTipo() { f.querySelectorAll('[data-so-abastecimento]').forEach(function (d) { d.hidden = f.tipo.value !== 'abastecimento'; }); }
    f.tipo.addEventListener('change', ajustarTipo);
    ajustarTipo();
    ligarClique(alvo);
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = f.querySelector('[data-msg-lanc]'), botao = f.querySelector('button[type=submit]');
      if (!f.ts.value) return OT.mensagem(msg, 'Informe quando aconteceu.');
      var corpo = { tipo: f.tipo.value, ts: f.ts.value + ':00-03:00', local: f.local.value.trim(), observacao: f.observacao.value.trim() };
      ['valor', 'litros', 'preco_l'].forEach(function (k) { if (f[k].value !== '' && !f[k].closest('[hidden]')) corpo[k] = f[k].value; });
      if (f.lat.value !== '' || f.lon.value !== '') { corpo.lat = Number(f.lat.value); corpo.lon = Number(f.lon.value); }
      botao.disabled = true;
      Promise.resolve(opcoes.aoLancar(corpo)).catch(function (e) { OT.mensagem(msg, e.message); botao.disabled = false; });
    });
  }

  function dadosMapa(v, opcoes) {
    return Mapa.camadas(v.resultado, { lancamentos: opcoes.lancamentos, posicao: opcoes.posicao, alertas: opcoes.alertas ? opcoes.alertas.alertas : [] });
  }

  /* Google Maps quando há chave e ele carregou; senão o diagrama SVG (permitido: os termos aceitam uso sem mapa). */
  function montarMapa(alvo, v, opcoes) {
    var slot = alvo.querySelector('[data-mapa]'), fonte = alvo.querySelector('[data-mapa-fonte]'), cfg = opcoes.mapa;
    if (!cfg || !cfg.chave || mapa.falhou) {
      fonte.textContent = cfg && cfg.chave ? 'Mapa do Google indisponível: diagrama do traçado.' : 'Diagrama do traçado (mapa real não configurado nesta instalação).';
      desenharSvg(alvo, v, opcoes);
      return;
    }
    fonte.textContent = 'Imagens: Google Maps · rota: ' + v.resultado.fontes.rota.fonte;
    if (!mapa.el || mapa.chave !== cfg.chave) {
      mapa.el = document.createElement('div');
      mapa.el.className = 'mapa mapa-google';
      mapa.inst = null;
      mapa.chave = cfg.chave;
      mapa.carregando = Mapa.criar(mapa.el, cfg, falhar).then(function (inst) { mapa.inst = inst; return inst; }, function () { falhar(); return null; });
    }
    slot.appendChild(mapa.el);
    mapa.carregando.then(function (inst) {
      if (!inst || ultimo.v !== v || mapa.falhou) return;
      inst.desenhar(dadosMapa(v, opcoes), v.id);
      alvo.querySelectorAll('[data-grupo]').forEach(function (cb) { if (!cb.checked) inst.visivel(cb.dataset.grupo, false); });
      ligarClique(alvo);
    });
  }

  function falhar() {
    if (mapa.falhou) return;
    mapa.falhou = true;
    if (mapa.el && mapa.el.parentNode) mapa.el.parentNode.removeChild(mapa.el);
    if (!ultimo.alvo || !ultimo.v) return;
    var f = ultimo.alvo.querySelector('[data-mapa-fonte]');
    if (f) f.textContent = 'Mapa do Google indisponível: diagrama do traçado.';
    desenharSvg(ultimo.alvo, ultimo.v, ultimo.opcoes);
  }

  /* Diagrama SVG do traçado (sem imagem de fundo): usado quando o mapa do Google não está configurado ou não carregou. */
  function desenharSvg(alvo, v, opcoes) {
    var slot = alvo.querySelector('[data-mapa]');
    if (!slot) return;
    var dados = dadosMapa(v, opcoes), g = dados.rota, ocultos = {};
    alvo.querySelectorAll('[data-grupo]').forEach(function (cb) { ocultos[cb.dataset.grupo] = !cb.checked; });
    var marc = dados.marcadores.filter(function (mk) { return !ocultos[mk.grupo]; });
    var todos = g.concat(marc.map(function (mk) { return [mk.lat, mk.lon]; }));
    if (!todos.length) { slot.innerHTML = '<div class="mapa vazio">Sem coordenadas para desenhar.</div>'; return; }
    var lats = todos.map(function (p) { return p[0]; }), lons = todos.map(function (p) { return p[1]; });
    var minLa = Math.min.apply(null, lats), maxLa = Math.max.apply(null, lats), minLo = Math.min.apply(null, lons), maxLo = Math.max.apply(null, lons);
    var W = 600, H = 360, m = 24, k = Math.cos((minLa + maxLa) / 2 * Math.PI / 180);
    var e = Math.min((W - 2 * m) / Math.max((maxLo - minLo) * k, 1e-6), (H - 2 * m) / Math.max(maxLa - minLa, 1e-6));
    var ox = (W - (maxLo - minLo) * k * e) / 2, oy = (H - (maxLa - minLa) * e) / 2;
    function xy(la, lo) { return [(ox + (lo - minLo) * k * e).toFixed(1), (H - oy - (la - minLa) * e).toFixed(1)]; }
    var s = (dados.areas || []).filter(function (ar) { return !ocultos[ar.grupo]; }).map(function (ar) {
      return '<polygon points="' + ar.pontos.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ') + '" fill="' + ar.cor + '" fill-opacity=".14" stroke="' + ar.cor + '" stroke-width="1.5"/>';
    }).join('');
    s += g.length ? '<polyline points="' + g.map(function (p) { return xy(p[0], p[1]).join(','); }).join(' ') + '" fill="none" stroke="#003365" stroke-width="3" stroke-linejoin="round" opacity=".85"/>' : '';
    marc.forEach(function (mk) {
      var p = xy(mk.lat, mk.lon), raio = mk.tipo === 'caminhao' ? 7 : (mk.grupo === 'pontos' ? 6 : 4.5);
      s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="' + raio + '" fill="' + (mk.cor || Mapa.TIPOS[mk.tipo].cor) + '" stroke="#fff" stroke-width="1.5"><title>' +
        esc(mk.titulo + ' — ' + mk.linhas.map(function (l) { return l[0] + ': ' + l[1]; }).join(' · ') + ' — fonte: ' + (mk.fonte || 'não informada')) + '</title></circle>';
    });
    slot.innerHTML = '<svg class="mapa" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Traçado da rota com pedágios, postos, bloqueios, pernoites e posição">' + s + '</svg>';
  }

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
    }).join('') + '<tr><td>Lançamentos</td><td><span class="tag t-parametro">manual</span></td><td class="fonte">informado manualmente</td></tr>' +
      '</tbody></table><p class="fonte">Parâmetros vigentes: ' + esc(r.parametros_vigencia) + ' · calculado em ' + OT.dataHora.format(new Date(r.calculado_em)) + '</p>';
  }

  /* Nova posição de telemetria: atualiza o caminhão e a caixa de posição sem recriar a tela. */
  function mostrarPosicao(alvo, v, evt) {
    if (!ultimo.v || ultimo.v.id !== v.id) return;
    ultimo.opcoes.posicao = evt;
    var box = alvo.querySelector('[data-vivo]');
    if (box) box.innerHTML = caixaPosicao(v, ultimo.opcoes);
    if (mapaAtivo()) mapa.inst.desenhar(dadosMapa(v, ultimo.opcoes), v.id);
    else desenharSvg(alvo, v, ultimo.opcoes);
  }

  raiz.ViagemView = { renderizar: renderizar, mostrarPosicao: mostrarPosicao };
})(window);
