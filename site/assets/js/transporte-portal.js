/* Portal do cliente: mesmas informações da Central (somente leitura), sensores via API e acompanhamento ao vivo. */
(function () {
  'use strict';
  var OT = window.OT, View = window.ViagemView, $ = function (s) { return document.querySelector(s); };
  var ctx = null, atual = null, fonte = null, sensores = [];

  /* Tempo real da v1: consulta /posicoes a cada 15 s (o Cloud Run escala em várias instâncias, então não há canal aberto). */
  var INTERVALO_MS = 15000;
  function fecharStream() { if (fonte) { clearInterval(fonte); fonte = null; } }

  function abrirStream(v) {
    fecharStream();
    fonte = setInterval(function () {
      if (!atual || atual.id !== v.id || document.hidden) return;
      OT.api('GET', '/viagens/' + v.id + '/posicoes').then(function (ps) {
        if (ps.length) View.mostrarPosicao($('#detalhe'), atual, ps[0]);
      }).catch(function () { /* sem atualização: a tela mantém a última posição */ });
    }, INTERVALO_MS);
  }

  function abrir(id) {
    fecharStream();
    $('#detalhe').innerHTML = '<div class="cartao carregando">Carregando viagem…</div>';
    OT.api('GET', '/viagens/' + id).then(function (v) {
      atual = v;
      View.renderizar($('#detalhe'), v, { editavel: false });
      marcarLista();
      if (!ctx.flags.sensores_ativo) return;
      acoesSensor(v);
      OT.api('GET', '/viagens/' + v.id + '/posicoes').then(function (ps) { if (ps.length) View.mostrarPosicao($('#detalhe'), v, ps[0]); });
      abrirStream(v);
    }).catch(function (e) { OT.mensagem($('#aviso'), e.message); });
  }

  function acoesSensor(v) {
    var box = $('#detalhe [data-vivo]');
    if (!box) return;
    var doVeiculo = sensores.filter(function (s) { return s.veiculo_id === v.veiculo_id && s.ativo; });
    var extra = document.createElement('div');
    extra.className = 'fonte';
    if (ctx.papel !== 'gestor') {
      extra.innerHTML = '<span class="ao-vivo">Acompanhamento ao vivo</span> · a posição aparece assim que um sensor do veículo enviar dados.';
    } else if (!doVeiculo.length) {
      extra.textContent = 'Nenhum sensor conectado a este veículo.';
    } else {
      extra.innerHTML = '<span class="ao-vivo">Acompanhamento ao vivo</span> · ' + doVeiculo.map(function (s) { return OT.esc(s.nome); }).join(', ');
      if (ctx.papel === 'gestor' && ctx.ambiente !== 'producao') {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'mini sec'; b.textContent = 'Simular leituras do sensor';
        b.style.marginLeft = '8px';
        b.addEventListener('click', function () {
          b.disabled = true;
          OT.api('POST', '/viagens/' + v.id + '/simular-sensor', { sensor_id: doVeiculo[0].id, leituras: 3 })
            .catch(function (e) { OT.mensagem($('#aviso'), e.message); }).then(function () { b.disabled = false; });
        });
        extra.appendChild(b);
      }
    }
    box.parentNode.insertBefore(extra, box);
  }

  function marcarLista() {
    document.querySelectorAll('#lista li[data-id]').forEach(function (li) { li.setAttribute('aria-selected', String(atual && li.dataset.id === atual.id)); });
  }

  function carregarLista() {
    return OT.api('GET', '/viagens').then(function (vs) {
      $('#lista').innerHTML = vs.length ? vs.map(function (v) {
        return '<li tabindex="0" data-id="' + OT.esc(v.id) + '"><b>' + OT.esc(v.origem) + ' → ' + OT.esc(v.destino) + '</b> <span class="tag t-ok">' + OT.esc(v.status.replace('_', ' ')) + '</span>' +
          '<small>Partida ' + OT.dataHora.format(new Date(v.partida_prevista)) + ' · chegada ' + OT.diaHora.format(new Date(v.chegada_prevista)) + '</small>' +
          '<small>' + OT.num1.format(v.distancia_km) + ' km · ' + OT.brl.format(Number(v.total_despesas)) + (v.alertas ? ' · ' + v.alertas + ' alerta(s)' : '') + '</small></li>';
      }).join('') : '<li class="vazio">Nenhuma viagem lançada.</li>';
      document.querySelectorAll('#lista li[data-id]').forEach(function (li) {
        li.addEventListener('click', function () { abrir(li.dataset.id); });
        li.addEventListener('keydown', function (e) { if (e.key === 'Enter') abrir(li.dataset.id); });
      });
    });
  }

  function carregarSensores() {
    return Promise.all([OT.api('GET', '/sensores'), OT.api('GET', '/veiculos')]).then(function (r) {
      sensores = r[0];
      var placas = {};
      r[1].forEach(function (v) { placas[v.id] = v.placa; });
      $('#sVeiculo').innerHTML = r[1].map(function (v) { return '<option value="' + OT.esc(v.id) + '">' + OT.esc(v.placa) + '</option>'; }).join('');
      $('#listaSensores').innerHTML = sensores.length ? '<table><thead><tr><th>Sensor</th><th>Veículo</th><th>Último sinal</th></tr></thead><tbody>' + sensores.map(function (s) {
        return '<tr><td>' + OT.esc(s.nome) + (s.ativo ? '' : ' <span class="tag t-erro">inativo</span>') + '<div class="fonte">' + OT.esc(s.tipo) + ' · ' + OT.esc(s.fornecedor) + '</div></td>' +
          '<td>' + OT.esc(placas[s.veiculo_id] || '—') + '</td><td>' + (s.ultimo_sinal_em ? OT.diaHora.format(new Date(s.ultimo_sinal_em)) : 'nunca') + '</td></tr>';
      }).join('') + '</tbody></table>' : '<p class="vazio">Nenhum sensor conectado.</p>';
    });
  }

  $('#formSensor').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var msg = $('#msgSensor');
    OT.api('POST', '/sensores', { veiculo_id: $('#sVeiculo').value, nome: $('#sNome').value.trim(), tipo: $('#sTipo').value, fornecedor: $('#sForn').value })
      .then(function (s) {
        msg.innerHTML = '<div class="msg ok" role="status">Sensor criado. ' + OT.esc(s.aviso) + '</div>' +
          '<label>Endpoint</label><div class="segredo">POST ' + OT.esc(location.origin + s.endpoint) + '</div>' +
          '<label>Segredo (HMAC-SHA256)</label><div class="segredo">' + OT.esc(s.segredo) + '</div>' +
          '<p class="fonte">Cabeçalhos: X-Timestamp (segundos Unix) e X-Assinatura = HMAC-SHA256(segredo, "timestamp." + corpo). Detalhes no README.</p>';
        return carregarSensores().then(function () { if (atual) abrir(atual.id); });
      }).catch(function (e) { OT.mensagem(msg, e.message); });
  });

  function iniciar() {
    OT.mensagem($('#aviso'), '');
    OT.api('GET', '/contexto').then(function (c) {
      ctx = c;
      if (c.ambiente !== 'producao' && c.entrada === 'dev') OT.painelDev($('#dev'), iniciar);
      $('#boxSensores').hidden = !(c.flags.sensores_ativo && c.papel === 'gestor');
      if (!c.flags.sensores_ativo) OT.mensagem($('#aviso'), 'Acompanhamento em tempo real desligado nesta instalação (ORGATEC_TRANSPORTE_SENSORES).', 'aviso');
      return Promise.all([carregarLista(), $('#boxSensores').hidden ? null : carregarSensores()]);
    }).catch(function (e) {
      if (e.status === 403) {
        OT.sair();
        OT.painelEntrada($('#dev'), iniciar);
        OT.mensagem($('#aviso'), 'Identifique-se para continuar: entre com o e-mail e a senha do seu acesso (em desenvolvimento, informe a transportadora no painel acima).', 'aviso');
      } else { OT.mensagem($('#aviso'), e.message); }
    });
  }

  window.addEventListener('beforeunload', fecharStream);
  OT.prepararSessao().then(iniciar);
})();
