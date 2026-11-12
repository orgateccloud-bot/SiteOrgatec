/* Central de Viagem: lançar rota, ver previsão, ajustar despesas e parâmetros. */
(function () {
  'use strict';
  var OT = window.OT, View = window.ViagemView, $ = function (s) { return document.querySelector(s); };
  var ctx = null, atual = null, lancamentos = [], posicao = null, relogio = null, assinatura = '';
  var alertas = null, comunicacoes = [], voltas = 0;
  var INTERVALO_MS = 15000;
  var VOLTAS_ALERTAS = 4;  /* alertas a cada 60 s: a rotina que os grava roda a cada 15 min */  /* o Cloud Run escala em várias instâncias: a tela consulta em vez de manter canal aberto */

  function blocoPonto(rotulo, removivel) {
    var div = document.createElement('div');
    div.className = 'ponto';
    div.innerHTML = '<div class="linha"><div><label>' + OT.esc(rotulo) + '</label><input class="pNome" required placeholder="Cidade"></div>' +
      '<div class="estreito"><label>UF</label><input class="pUf" maxlength="2" placeholder="GO"></div></div>' +
      '<details><summary class="fonte">coordenadas (opcional)</summary><div class="linha"><div><label>Latitude</label><input class="pLat" type="number" step="any"></div>' +
      '<div><label>Longitude</label><input class="pLon" type="number" step="any"></div></div></details>' +
      (removivel ? '<button type="button" class="mini sec pRem">remover parada</button>' : '');
    if (removivel) div.querySelector('.pRem').addEventListener('click', function () { div.remove(); });
    return div;
  }

  function montarPontos() {
    var box = $('#pontos');
    box.innerHTML = '';
    box.appendChild(blocoPonto('Origem', false));
    box.appendChild(blocoPonto('Destino', false));
  }

  function lerPontos() {
    return Array.prototype.map.call(document.querySelectorAll('.ponto'), function (p) {
      var o = { nome: p.querySelector('.pNome').value.trim() }, uf = p.querySelector('.pUf').value.trim().toUpperCase();
      var lat = p.querySelector('.pLat').value, lon = p.querySelector('.pLon').value;
      if (uf) o.uf = uf;
      if (lat !== '') o.lat = Number(lat);
      if (lon !== '') o.lon = Number(lon);
      return o;
    });
  }

  function partidaPadrao() {
    var d = new Date(Date.now() + 3600e3), f = new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    return f.format(d).replace(' ', 'T').slice(0, 14) + '00';
  }

  function carregarVeiculos() {
    return OT.api('GET', '/veiculos').then(function (vs) {
      $('#veiculo').innerHTML = vs.length ? vs.map(function (v) {
        return '<option value="' + OT.esc(v.id) + '">' + OT.esc(v.placa + ' · ' + v.eixos + ' eixos' + (v.descricao ? ' · ' + v.descricao : '')) + '</option>';
      }).join('') : '<option value="">Cadastre um veículo</option>';
    });
  }

  function carregarLista() {
    return OT.api('GET', '/viagens').then(function (vs) {
      $('#lista').innerHTML = vs.length ? vs.map(function (v) {
        return '<li tabindex="0" data-id="' + OT.esc(v.id) + '" aria-selected="' + (atual && atual.id === v.id) + '"><b>' + OT.esc(v.origem) + ' → ' + OT.esc(v.destino) + '</b>' +
          '<small>' + OT.dataHora.format(new Date(v.partida_prevista)) + ' · ' + OT.num1.format(v.distancia_km) + ' km · ' + OT.brl.format(Number(v.total_despesas)) + (v.alertas ? ' · ' + v.alertas + ' alerta(s)' : '') + '</small></li>';
      }).join('') : '<li class="vazio">Nenhuma viagem ainda.</li>';
      document.querySelectorAll('#lista li[data-id]').forEach(function (li) {
        function abrir() { OT.api('GET', '/viagens/' + li.dataset.id).then(mostrar).catch(erroGeral); }
        li.addEventListener('click', abrir);
        li.addEventListener('keydown', function (e) { if (e.key === 'Enter') abrir(); });
      });
    });
  }

  function marca(v, ls) {
    var al = alertas ? [alertas.atualizado_em, (alertas.alertas || []).map(function (a) { return [a.id, a.estado, a.alerta.gravidade, a.visto, a.chegada_prevista]; })] : null;
    return JSON.stringify([v.status, v.resultado.calculado_em, v.resultado.coordenadas_expiradas || '', v.ajustes, ls.map(function (l) { return l.id; }), al,
      comunicacoes.map(function (c) { return [c.id, c.estado]; })]);
  }

  /* Alertas da viagem e, para o gestor, os avisos enviados ao motorista. Falha aqui não derruba a tela: o cartão diz que não verificou. */
  function buscarAlertas(id) {
    if (!ctx.flags.alertas_ativo) return Promise.resolve([null, []]);
    return Promise.all([
      OT.api('GET', '/alertas-rota?viagem_id=' + encodeURIComponent(id)).catch(function () { return { fontes: {}, atualizado_em: null, alertas: [] }; }),
      ctx.papel === 'gestor' ? OT.api('GET', '/comunicacoes?viagem_id=' + encodeURIComponent(id)).catch(function () { return []; }) : Promise.resolve([])
    ]);
  }

  /* Abre uma viagem: busca os lançamentos e a última posição, desenha e passa a acompanhar as mudanças. */
  function mostrar(v) {
    var trocou = !atual || atual.id !== v.id;
    atual = v;
    if (trocou) { lancamentos = []; posicao = null; alertas = null; comunicacoes = []; }
    return Promise.all([
      OT.api('GET', '/viagens/' + v.id + '/lancamentos').catch(function () { return []; }),
      ctx.flags.sensores_ativo ? OT.api('GET', '/viagens/' + v.id + '/posicoes').catch(function () { return []; }) : Promise.resolve([]),
      buscarAlertas(v.id)
    ]).then(function (r) {
      lancamentos = r[0]; posicao = r[1][0] || null; alertas = r[2][0]; comunicacoes = r[2][1];
      desenhar();
      acompanhar();
      carregarLista();
    });
  }

  function desenhar() {
    var gestor = ctx.papel === 'gestor', lanca = gestor || ctx.papel === 'motorista';
    assinatura = marca(atual, lancamentos);
    View.renderizar($('#resultado'), atual, {
      editavel: gestor, aoAjustar: ajustar, aoRecalcular: gestor ? recalcular : null,
      mapa: ctx.mapa, lancamentos: lancamentos, posicao: posicao, telemetria: ctx.flags.sensores_ativo,
      aoLancar: lanca ? lancar : null, aoRemoverLancamento: lanca ? removerLancamento : null, papel: ctx.papel, usuario: ctx.usuario_id,
      alertas: alertas, comunicacoes: comunicacoes, aoMarcarVisto: gestor && alertas ? marcarVisto : null
    });
  }

  /* A cada 15 s (com a aba visível): viagem, lançamentos e posição. Redesenha só o que mudou e nunca enquanto alguém digita. */
  function acompanhar() {
    if (relogio) clearInterval(relogio);
    relogio = setInterval(function () {
      if (!atual || document.hidden) return;
      var id = atual.id, comAlertas = ++voltas % VOLTAS_ALERTAS === 0;
      Promise.all([
        OT.api('GET', '/viagens/' + id),
        OT.api('GET', '/viagens/' + id + '/lancamentos'),
        ctx.flags.sensores_ativo ? OT.api('GET', '/viagens/' + id + '/posicoes') : Promise.resolve([]),
        comAlertas ? buscarAlertas(id) : Promise.resolve(null)
      ]).then(function (r) {
        if (!atual || atual.id !== id) return;
        if (r[3]) { alertas = r[3][0]; comunicacoes = r[3][1]; }
        var nova = r[2][0] || null, digitando = document.activeElement && $('#resultado').contains(document.activeElement) &&
          /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName);
        if (marca(r[0], r[1]) !== assinatura && !digitando) {
          atual = r[0]; lancamentos = r[1]; posicao = nova;
          desenhar();
        } else if (nova && (!posicao || nova.ts !== posicao.ts)) {
          posicao = nova;
          View.mostrarPosicao($('#resultado'), atual, nova);
        }
      }).catch(function () { /* sem atualização: a tela mantém o último estado */ });
    }, INTERVALO_MS);
  }

  function marcarVisto(alertaId) {
    OT.api('POST', '/alertas-rota/' + encodeURIComponent(alertaId) + '/visto').then(function () { return mostrar(atual); }).catch(erroGeral);
  }

  /* ---------- Telefone do motorista para os alertas (só gestor; só com o consentimento do motorista) ---------- */
  function carregarContatos() {
    if (!ctx.flags.alertas_ativo || ctx.papel !== 'gestor') return null;
    $('#boxAlertas').hidden = false;
    return Promise.all([OT.api('GET', '/motoristas'), OT.api('GET', '/alertas-termo')]).then(function (r) {
      var ms = r[0], termo = r[1];
      $('#termoAlertas').textContent = termo.texto;
      $('#termoAlertas').dataset.versao = termo.versao;
      $('#aMotorista').innerHTML = ms.length ? ms.map(function (m) { return '<option value="' + OT.esc(m.id) + '">' + OT.esc(m.nome) + '</option>'; }).join('')
        : '<option value="">Nenhum motorista cadastrado</option>';
      $('#listaContatos').innerHTML = ms.length ? ms.map(function (m) {
        var c = m.alertas_canais || [];
        return '<li><b>' + OT.esc(m.nome) + '</b><small>' + (c.length ? 'recebe por ' + OT.esc(c.join(' e ').replace('whatsapp', 'WhatsApp').replace('sms', 'SMS')) +
          ' <button type="button" class="mini sec" data-revogar="' + OT.esc(m.id) + '">cancelar</button>' : 'não recebe alertas') + '</small></li>';
      }).join('') : '<li class="vazio">Nenhum motorista.</li>';
      document.querySelectorAll('#listaContatos [data-revogar]').forEach(function (b) {
        b.addEventListener('click', function () {
          b.disabled = true;
          OT.api('DELETE', '/motoristas/' + b.dataset.revogar + '/contato').then(carregarContatos).catch(function (e) { OT.mensagem($('#msgAlertas'), e.message); });
        });
      });
    }).catch(function (e) { OT.mensagem($('#msgAlertas'), e.message); });
  }

  $('#formAlertas').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var canais = ['whatsapp', 'sms'].filter(function (c) { return $('#aCanal-' + c).checked; }), msg = $('#msgAlertas');
    if (!$('#aMotorista').value) return OT.mensagem(msg, 'Cadastre o motorista primeiro.');
    if (!canais.length) return OT.mensagem(msg, 'Marque ao menos um canal.');
    if (!$('#aConsentimento').checked) return OT.mensagem(msg, 'Sem o aceite do motorista, o telefone não pode ser cadastrado.');
    OT.api('PUT', '/motoristas/' + $('#aMotorista').value + '/contato', {
      telefone: $('#aTelefone').value, canais: canais, consentimento_do_motorista: true, versao_termo: $('#termoAlertas').dataset.versao
    }).then(function () {
      OT.mensagem(msg, 'Telefone salvo. O motorista recebe os alertas de "Perigo" e "Grande perigo" das viagens dele.', 'ok');
      $('#aTelefone').value = ''; $('#aConsentimento').checked = false;
      return carregarContatos();
    }).catch(function (e) { OT.mensagem(msg, e.message); });
  });

  function ajustar(tipo, valor) {
    OT.api('PUT', '/viagens/' + atual.id + '/despesas/' + tipo, { valor: valor === null ? null : String(valor) }).then(mostrar).catch(erroGeral);
  }

  function recalcular() {
    OT.api('POST', '/viagens/' + atual.id + '/recalcular').then(mostrar).catch(erroGeral);
  }

  function lancar(corpo) {
    return OT.api('POST', '/viagens/' + atual.id + '/lancamentos', corpo).then(function () { return mostrar(atual); });
  }

  function removerLancamento(id) {
    OT.api('DELETE', '/viagens/' + atual.id + '/lancamentos/' + id).then(function () { return mostrar(atual); }).catch(erroGeral);
  }

  function erroGeral(e) { OT.mensagem($('#aviso'), e.message); }

  $('#form').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var btn = $('#lancar'), msg = $('#msgForm');
    OT.mensagem(msg, '');
    var pontos = lerPontos();
    if (!$('#veiculo').value) return OT.mensagem(msg, 'Escolha ou cadastre um veículo.');
    if (pontos.some(function (p) { return p.nome.length < 2; })) return OT.mensagem(msg, 'Preencha o nome de todos os pontos.');
    if (!$('#partida').value) return OT.mensagem(msg, 'Informe a partida prevista.');
    btn.disabled = true; btn.textContent = 'Calculando…';
    $('#resultado').innerHTML = '<div class="cartao carregando">Calculando rota, jornada, despesas, bloqueios e clima…</div>';
    OT.api('POST', '/viagens', {
      veiculo_id: $('#veiculo').value, pontos: pontos, carregado: $('#carregado').checked,
      descricao: $('#descricao').value.trim(), partida_prevista: $('#partida').value + ':00-03:00'
    }).then(mostrar).catch(function (e) {
      $('#resultado').innerHTML = '<div class="cartao vazio">Não foi possível calcular a viagem.</div>';
      OT.mensagem(msg, e.message + (e.estado ? ' (fonte: ' + e.estado + ')' : ''));
    }).then(function () { btn.disabled = false; btn.textContent = 'Calcular viagem'; });
  });

  $('#addParada').addEventListener('click', function () {
    var box = $('#pontos');
    box.insertBefore(blocoPonto('Parada intermediária', true), box.lastElementChild);
  });

  $('#formVeiculo').addEventListener('submit', function (ev) {
    ev.preventDefault();
    OT.api('POST', '/veiculos', {
      placa: $('#vPlaca').value, descricao: $('#vDesc').value, eixos: Number($('#vEixos').value),
      consumo_km_l_carregado: $('#vCc').value, consumo_km_l_vazio: $('#vCv').value, tanque_l: $('#vT').value
    }).then(function () { OT.mensagem($('#msgVeiculo'), 'Veículo salvo.', 'ok'); return carregarVeiculos(); })
      .catch(function (e) { OT.mensagem($('#msgVeiculo'), e.message); });
  });

  function carregarParametros() {
    return OT.api('GET', '/parametros').then(function (p) {
      var html = '<p class="fonte">Vigência: ' + OT.esc(p.vigencia) + '</p>' + Object.keys(p.valores).map(function (k) {
        var meta = p.meta[k] || { rotulo: k, fonte: '' }, v = p.valores[k];
        var campo = typeof v === 'boolean'
          ? '<input type="checkbox" data-k="' + k + '"' + (v ? ' checked' : '') + ' style="width:auto">'
          : '<input type="number" step="any" min="0" data-k="' + k + '" value="' + (v == null ? '' : OT.esc(v)) + '"' + (v == null ? ' placeholder="em branco"' : '') + '>';
        return '<label>' + OT.esc(meta.rotulo) + '</label>' + campo + '<div class="fonte">' + OT.esc(meta.fonte) + '</div>';
      }).join('');
      $('#camposParametros').className = '';
      $('#camposParametros').innerHTML = html;
    });
  }

  $('#formParametros').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var valores = {};
    document.querySelectorAll('#camposParametros [data-k]').forEach(function (i) {
      valores[i.dataset.k] = i.type === 'checkbox' ? i.checked : i.value === '' ? null : (/_min$/.test(i.dataset.k) ? parseInt(i.value, 10) : i.value);
    });
    OT.api('PUT', '/parametros', valores).then(function () {
      OT.mensagem($('#msgParametros'), 'Parâmetros salvos. Use “Recalcular” ou lance a rota de novo para aplicar.', 'ok');
    }).catch(function (e) { OT.mensagem($('#msgParametros'), e.message); });
  });

  function iniciar() {
    OT.mensagem($('#aviso'), '');
    OT.api('GET', '/contexto').then(function (c) {
      ctx = c;
      if (c.ambiente !== 'producao' && c.entrada === 'dev') OT.painelDev($('#dev'), iniciar);
      var gestor = c.papel === 'gestor';
      $('#boxVeiculo').hidden = !gestor; $('#boxParametros').hidden = !gestor;
      if (c.papel === 'leitura') { $('#form').hidden = true; OT.mensagem($('#aviso'), 'Perfil de leitura: use o Portal do cliente.', 'aviso'); }
      var simulados = ['rota', 'combustivel', 'pedagio', 'clima'].filter(function (k) { return (c.flags.provedores_reais || []).indexOf(k) < 0; });
      if (simulados.length) OT.mensagem($('#aviso'), 'Fontes em modo simulado: ' + simulados.join(', ').replace(/_/g, ' ') + '. Os valores servem para demonstração.', 'aviso');
      return Promise.all([carregarVeiculos(), carregarLista(), gestor ? carregarParametros() : null, carregarContatos()]);
    }).catch(function (e) {
      if (e.status === 403) {
        OT.sair();
        OT.painelEntrada($('#dev'), iniciar);
        OT.mensagem($('#aviso'), 'Identifique-se para continuar: entre com o e-mail e a senha do seu acesso (em desenvolvimento, informe a transportadora no painel acima).', 'aviso');
      } else { erroGeral(e); }
    });
  }

  window.addEventListener('beforeunload', function () { if (relogio) clearInterval(relogio); });
  montarPontos();
  $('#partida').value = partidaPadrao();
  OT.prepararSessao().then(iniciar);
})();
