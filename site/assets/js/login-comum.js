/* Login e chamadas à API do painel LOCAR (/api/locar). Firebase Authentication por e-mail e senha, direto no Identity Toolkit
   (sem biblioteca, CSP script-src 'self'). O ID token fica só na aba (sessionStorage) e vai em Authorization: Bearer.
   Os cabeçalhos X-Locar-* só valem no modo dev da API (nunca em produção). */
(function (raiz) {
  'use strict';
  var BASE = '/api/locar';
  var CHAVE_TOKEN = 'orgatec-login';
  /* A Central de Viagem guarda o token na mesma forma, com outra chave: quem entrou lá nesta aba já entra aqui (mesma conta). */
  var CHAVE_CENTRAL = 'orgatec-transporte-token';
  var CHAVE_DEV = 'orgatec-locar-dev';
  var GOOGLE_ENTRAR = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=';
  var GOOGLE_RENOVAR = 'https://securetoken.googleapis.com/v1/token?key=';
  var chaveWeb = null;

  function ler(chave) {
    try { return JSON.parse(sessionStorage.getItem(chave) || 'null'); } catch (e) { return null; }
  }
  function lerToken() { return ler(CHAVE_TOKEN) || ler(CHAVE_CENTRAL); }
  function gravarToken(t) {
    try { if (t) sessionStorage.setItem(CHAVE_TOKEN, JSON.stringify(t)); else { sessionStorage.removeItem(CHAVE_TOKEN); sessionStorage.removeItem(CHAVE_CENTRAL); } }
    catch (e) { /* armazenamento indisponível */ }
  }
  function guardar(idToken, refresh, segundos) {
    gravarToken({ id: idToken, refresh: refresh, expira: Date.now() + Number(segundos) * 1000 });
  }
  function lerDev() {
    try { return JSON.parse(localStorage.getItem(CHAVE_DEV) || '{}'); } catch (e) { return {}; }
  }
  function gravarDev(v) {
    try { localStorage.setItem(CHAVE_DEV, JSON.stringify(v)); } catch (e) { /* armazenamento indisponível */ }
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
    var h = { 'Content-Type': 'application/json' }, t = lerToken(), d = lerDev();
    if (t) { h['Authorization'] = 'Bearer ' + t.id; return h; }
    if (d.grupo) h['X-Locar-Grupo'] = d.grupo;
    if (d.papel) h['X-Locar-Papel'] = d.papel;
    if (d.usuario) h['X-Usuario-Id'] = d.usuario;
    return h;
  }

  function mensagemValidacao(d) {
    if (typeof d === 'string') return d;  // erros do módulo trazem o texto em detail
    if (!Array.isArray(d) || !d.length) return null;
    var onde = (d[0].loc || []).slice(1).join(' › '), msg = String(d[0].msg).replace(/^Value error, /, '');
    return onde ? 'Dado inválido em ' + onde + ': ' + msg : 'Dado inválido: ' + msg;
  }

  function requisitar(metodo, caminho, corpo) {
    return fetch(BASE + caminho, {
      method: metodo, headers: cabecalhos(), credentials: 'same-origin',
      body: corpo === undefined ? undefined : JSON.stringify(corpo)
    }).then(function (r) {
      return r.text().then(function (t) {
        var dados = null;
        try { dados = t ? JSON.parse(t) : null; } catch (e) { dados = null; }
        if (!r.ok) {
          var msg = (dados && dados.detail && mensagemValidacao(dados.detail)) || ('Erro ' + r.status);
          if (r.status === 403) msg = 'Sem acesso ao painel do grupo. Peça à ORGATEC para liberar o seu acesso.';
          var err = new Error(msg); err.status = r.status; throw err;
        }
        return dados;
      });
    }, function () { throw new Error('Sem conexão com o servidor. Verifique a internet e tente de novo.'); });
  }
  function api(metodo, caminho, corpo) {
    return garantirToken().then(function () { return requisitar(metodo, caminho, corpo); });
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* Modo dev (só com a API fora de produção): escolhe o grupo, o papel e o usuário pelos cabeçalhos. */
  function painelDev(alvo, aoMudar) {
    var d = lerDev();
    alvo.innerHTML = '<form class="lc-entrar" novalidate><strong>Modo desenvolvimento</strong> ' +
      '<label>Grupo <input name="grupo" size="38" placeholder="UUID do grupo"></label> ' +
      '<label>Papel <select name="papel"><option>equipe</option><option>diretor</option><option>leitura</option></select></label> ' +
      '<label>Usuário <input name="usuario" size="12"></label> <button class="lc-btn" type="submit">Aplicar</button></form>';
    var f = alvo.querySelector('form');
    f.grupo.value = d.grupo || ''; f.papel.value = d.papel || 'equipe'; f.usuario.value = d.usuario || 'u-equipe';
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      gravarDev({ grupo: f.grupo.value.trim(), papel: f.papel.value, usuario: f.usuario.value.trim() });
      aoMudar();
    });
    alvo.hidden = false;
  }

  /* Painel de acesso: formulário de login com a API em Firebase; painel de desenvolvimento com a API em dev. */
  function painelEntrada(alvo, aoMudar) {
    return fetch(BASE + '/entrada', { credentials: 'same-origin' }).then(function (r) {
      if (!r.ok) { alvo.hidden = false; alvo.textContent = 'O painel do grupo ainda não está habilitado nesta instalação.'; return; }
      return r.json().then(function (e) {
        if (e.modo === 'dev') { painelDev(alvo, aoMudar); return; }
        if (e.modo !== 'firebase' || !e.chave_web) { alvo.hidden = false; alvo.textContent = 'O login desta instalação ainda não foi configurado.'; return; }
        chaveWeb = e.chave_web;
        alvo.innerHTML = '<form class="lc-entrar" novalidate><strong>Entrar</strong> ' +
          '<label>E-mail <input name="email" type="email" autocomplete="username" required></label> ' +
          '<label>Senha <input name="senha" type="password" autocomplete="current-password" required></label> ' +
          '<button class="lc-btn" type="submit">Entrar</button> <span class="lc-erro-entrada" role="alert"></span></form>';
        var f = alvo.querySelector('form'), erro = alvo.querySelector('.lc-erro-entrada');
        f.addEventListener('submit', function (ev) {
          ev.preventDefault(); erro.textContent = '';
          entrar(f.email.value.trim(), f.senha.value).then(function () { f.senha.value = ''; alvo.hidden = true; aoMudar(); },
            function (x) { erro.textContent = x.message; });
        });
        alvo.hidden = false;
      });
    }, function () { alvo.hidden = false; alvo.textContent = 'Sem conexão. Verifique a internet e tente de novo.'; });
  }

  /* Com sessão já aberta (ou vinda da Central de Viagem), precisa da chave pública para renovar o token. */
  function prepararSessao() {
    if (!lerToken()) return Promise.resolve();
    return fetch(BASE + '/entrada', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (e) { chaveWeb = e.chave_web || null; }, function () { /* sem rede */ });
  }

  raiz.OL = { api: api, esc: esc, painelEntrada: painelEntrada, prepararSessao: prepararSessao, sair: sair,
    temSessao: function () { return !!lerToken(); }, temDev: function () { return !!lerDev().grupo; } };
})(window);
