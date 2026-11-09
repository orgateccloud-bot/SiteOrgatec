/* Utilidades compartilhadas da Central e do Portal: API, formatação e painel de desenvolvimento. */
(function (raiz) {
  'use strict';
  var FUSO = 'America/Sao_Paulo';
  var CHAVE_DEV = 'orgatec-transporte-dev';

  function lerDev() {
    try { return JSON.parse(localStorage.getItem(CHAVE_DEV) || '{}'); } catch (e) { return {}; }
  }
  function gravarDev(v) {
    try { localStorage.setItem(CHAVE_DEV, JSON.stringify(v)); } catch (e) { /* armazenamento indisponível */ }
  }

  /* Em produção o login do sistema hospedeiro autentica a sessão; estes cabeçalhos só valem no modo dev. */
  function cabecalhos() {
    var d = lerDev(), h = { 'Content-Type': 'application/json' };
    if (d.transportadora) h['X-Transportadora-Id'] = d.transportadora;
    if (d.papel) h['X-Usuario-Papel'] = d.papel;
    if (d.usuario) h['X-Usuario-Id'] = d.usuario;
    return h;
  }

  function api(metodo, caminho, corpo) {
    return fetch('/api/transporte' + caminho, {
      method: metodo, headers: cabecalhos(), credentials: 'same-origin',
      body: corpo === undefined ? undefined : JSON.stringify(corpo)
    }).then(function (r) {
      return r.text().then(function (t) {
        var dados = null;
        try { dados = t ? JSON.parse(t) : null; } catch (e) { dados = null; }
        if (!r.ok) {
          var msg = (dados && (dados.erro || (dados.detail && mensagemValidacao(dados.detail)))) || ('Erro ' + r.status);
          var err = new Error(msg); err.status = r.status; err.estado = dados && dados.estado; throw err;
        }
        return dados;
      });
    }, function () { throw new Error('Sem conexão com o servidor. Verifique a internet e tente de novo.'); });
  }

  function mensagemValidacao(d) {
    if (!Array.isArray(d) || !d.length) return null;
    return 'Dado inválido em ' + d[0].loc.slice(1).join(' › ') + ': ' + d[0].msg;
  }

  var brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  var num1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
  var dataHora = new Intl.DateTimeFormat('pt-BR', { timeZone: FUSO, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  var diaHora = new Intl.DateTimeFormat('pt-BR', { timeZone: FUSO, day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function horas(h) {
    var t = Math.round(Number(h) * 60), d = Math.floor(t / 1440), hh = Math.floor((t % 1440) / 60), mm = t % 60;
    return (d ? d + 'd ' : '') + hh + 'h' + (mm ? String(mm).padStart(2, '0') : '');
  }
  function tagEstado(estado) {
    var classe = { ok: 't-ok', simulado: 't-simulado', parametro: 't-parametro' }[estado] || 't-erro';
    var rotulo = { ok: 'oficial', simulado: 'simulado', parametro: 'parâmetro', timeout: 'sem resposta',
      limite_excedido: 'limite de uso', indisponivel: 'indisponível', resposta_invalida: 'resposta inválida' }[estado] || estado;
    return '<span class="tag ' + classe + '">' + esc(rotulo) + '</span>';
  }
  function mensagem(alvo, texto, tipo) {
    alvo.innerHTML = texto ? '<div class="msg ' + (tipo || 'erro') + '" role="' + (tipo === 'ok' ? 'status' : 'alert') + '">' + esc(texto) + '</div>' : '';
  }

  /* Painel de desenvolvimento: só aparece quando a API não está em produção. */
  function painelDev(alvo, aoMudar) {
    var d = lerDev();
    alvo.innerHTML = '<strong>Modo desenvolvimento</strong> Transportadora <input id="devT" size="38" placeholder="id da transportadora"> ' +
      'Papel <select id="devP"><option>gestor</option><option>motorista</option><option>leitura</option></select> ' +
      'Usuário <input id="devU" size="12"> <button class="mini" id="devOk" type="button">Aplicar</button>';
    alvo.querySelector('#devT').value = d.transportadora || '';
    alvo.querySelector('#devP').value = d.papel || 'gestor';
    alvo.querySelector('#devU').value = d.usuario || 'u-gestor';
    alvo.querySelector('#devOk').addEventListener('click', function () {
      gravarDev({ transportadora: alvo.querySelector('#devT').value.trim(), papel: alvo.querySelector('#devP').value, usuario: alvo.querySelector('#devU').value.trim() });
      aoMudar();
    });
    alvo.hidden = false;
  }

  raiz.OT = { api: api, brl: brl, num1: num1, dataHora: dataHora, diaHora: diaHora, esc: esc, horas: horas,
    tagEstado: tagEstado, mensagem: mensagem, painelDev: painelDev, lerDev: lerDev };
})(window);
