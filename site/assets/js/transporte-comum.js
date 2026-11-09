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

  /* Login (Firebase Authentication, e-mail e senha): o ID token fica só na aba (sessionStorage) e vai em Authorization.
     Os cabeçalhos X-* abaixo só valem no modo dev. */
  var CHAVE_TOKEN = 'orgatec-transporte-token';
  var GOOGLE_ENTRAR = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=';
  var GOOGLE_RENOVAR = 'https://securetoken.googleapis.com/v1/token?key=';
  var chaveWeb = null;

  function lerToken() {
    try { return JSON.parse(sessionStorage.getItem(CHAVE_TOKEN) || 'null'); } catch (e) { return null; }
  }
  function gravarToken(t) {
    try { if (t) sessionStorage.setItem(CHAVE_TOKEN, JSON.stringify(t)); else sessionStorage.removeItem(CHAVE_TOKEN); } catch (e) { /* armazenamento indisponível */ }
  }
  function guardar(idToken, refresh, segundos) {
    gravarToken({ id: idToken, refresh: refresh, expira: Date.now() + Number(segundos) * 1000 });
  }
  /* Renova o token quando faltam menos de 2 minutos; se não der, apaga e a tela pede o login de novo. */
  function garantirToken() {
    var t = lerToken();
    if (!t || !chaveWeb || t.expira - Date.now() > 120000) return Promise.resolve();
    return fetch(GOOGLE_RENOVAR + encodeURIComponent(chaveWeb), {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'grant_type=refresh_token&refresh_token=' + encodeURIComponent(t.refresh)
    }).then(function (r) { return r.json().then(function (d) {
      if (!r.ok || !d.id_token) { gravarToken(null); return; }
      guardar(d.id_token, d.refresh_token, d.expires_in);
    }); }, function () { /* sem rede: a chamada seguinte mostra o erro */ });
  }
  function entrar(email, senha) {
    return fetch(GOOGLE_ENTRAR + encodeURIComponent(chaveWeb), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: senha, returnSecureToken: true })
    }).then(function (r) { return r.json().then(function (d) {
      if (!r.ok || !d.idToken) throw new Error('E-mail ou senha incorretos.');
      guardar(d.idToken, d.refreshToken, d.expiresIn);
    }); }, function () { throw new Error('Sem conexão. Verifique a internet e tente de novo.'); });
  }
  function sair() { gravarToken(null); }

  function cabecalhos() {
    var d = lerDev(), h = { 'Content-Type': 'application/json' }, t = lerToken();
    if (t) { h['Authorization'] = 'Bearer ' + t.id; return h; }
    if (d.transportadora) h['X-Transportadora-Id'] = d.transportadora;
    if (d.papel) h['X-Usuario-Papel'] = d.papel;
    if (d.usuario) h['X-Usuario-Id'] = d.usuario;
    return h;
  }

  function api(metodo, caminho, corpo) {
    return garantirToken().then(function () { return requisitar(metodo, caminho, corpo); });
  }

  function requisitar(metodo, caminho, corpo) {
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

  /* Painel de acesso: formulário de login quando a API usa Firebase; painel de desenvolvimento quando usa cabeçalhos. */
  function painelEntrada(alvo, aoMudar) {
    fetch('/api/transporte/entrada', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : {}; }).then(function (e) {
      if (e.modo === 'dev') { painelDev(alvo, aoMudar); return; }
      if (e.modo !== 'firebase' || !e.chave_web) { alvo.hidden = false; alvo.textContent = 'O login desta instalação ainda não foi configurado.'; return; }
      chaveWeb = e.chave_web;
      alvo.innerHTML = '<form class="entrar" novalidate><strong>Entrar</strong> ' +
        '<label>E-mail <input name="email" type="email" autocomplete="username" required></label> ' +
        '<label>Senha <input name="senha" type="password" autocomplete="current-password" required></label> ' +
        '<button class="mini" type="submit">Entrar</button> <span class="erro-entrada" role="alert"></span></form>';
      var f = alvo.querySelector('form'), erro = alvo.querySelector('.erro-entrada');
      f.addEventListener('submit', function (ev) {
        ev.preventDefault(); erro.textContent = '';
        entrar(f.email.value.trim(), f.senha.value).then(function () { f.senha.value = ''; alvo.hidden = true; aoMudar(); },
          function (x) { erro.textContent = x.message; });
      });
      alvo.hidden = false;
    }, function () { /* sem rede */ });
  }
  /* Chamado quando a página já tem sessão: precisa da chave para renovar o token. */
  function prepararSessao() {
    if (!lerToken()) return Promise.resolve();
    return fetch('/api/transporte/entrada', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (e) { chaveWeb = e.chave_web || null; }, function () { /* sem rede */ });
  }

  raiz.OT = { api: api, brl: brl, num1: num1, dataHora: dataHora, diaHora: diaHora, esc: esc, horas: horas,
    tagEstado: tagEstado, mensagem: mensagem, painelDev: painelDev, painelEntrada: painelEntrada, prepararSessao: prepararSessao, sair: sair,
    lerDev: lerDev, temSessao: function () { return !!lerToken(); } };
})(window);
