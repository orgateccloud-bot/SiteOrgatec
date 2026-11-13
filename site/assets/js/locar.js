/* Painel do grupo LOCAR (site/locar/painel.html): login, agenda por mês, entidades com ciclo de vida, marcos da reforma e trilha.
   Toda a conversa com o servidor passa por OL.api (login-comum.js); as regras de prazo ficam em locar-agenda.js (testadas no Node).
   Nenhum dado do grupo mora neste arquivo nem na página: tudo chega pela API depois do login. */
(function () {
  'use strict';
  var O = window.Orgatec, OL = window.OL, A = O.locarAgenda, M = O.locarModelos, F = O.fontes;
  var esc = OL.esc;
  function $(s, r) { return (r || document).querySelector(s); }

  var el = { acesso: $('#lcAcesso'), painel: $('#lcPainel'), msg: $('#lcMsg'), cabeca: $('#lcCabeca'), kpis: $('#lcKpis'), filtros: $('#lcFiltros'),
    agenda: $('#lcAgenda'), entidades: $('#lcEntidades'), marcos: $('#lcMarcos'), adicionar: $('#lcAdicionar'), auditoria: $('#lcAuditoria') };
  var estado = { ctx: null, hoje: '', entidades: [], itens: [], filtro: { entidade: '', status: 'abertos', janela: 'todos', busca: '', kpi: '' } };

  function mensagem(texto, tipo) {
    el.msg.innerHTML = texto ? '<div class="lc-msg lc-msg-' + (tipo || 'erro') + '" role="' + (tipo === 'ok' ? 'status' : 'alert') + '">' + esc(texto) + '</div>' : '';
  }
  function equipe() { return !!estado.ctx && estado.ctx.papel === 'equipe'; }
  function entidadePorId(id) {
    for (var i = 0; i < estado.entidades.length; i++) if (estado.entidades[i].id === id) return estado.entidades[i];
    return null;
  }
  function seguro(url) { return /^https:\/\/[^\s"'<>]+$/.test(String(url || '')); }
  function dataHora(iso) {
    try { return new Date(iso).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); }
    catch (e) { return String(iso || ''); }
  }

  function fonteHtml(id) {
    var f = id && F.porId[id];
    if (!f) return '';
    var nome = seguro(f.url) ? '<a href="' + esc(f.url) + '" target="_blank" rel="noopener noreferrer">' + esc(f.rotulo) + '</a>' : esc(f.rotulo);
    return '<span class="lc-fonte">Fonte: ' + nome + (f.validado ? '' : ' <span class="og-selo og-selo-pendente">pendente de validação</span>') + '</span>';
  }
  function selo(tom, texto) { return '<span class="og-selo og-selo-' + tom + '">' + esc(texto) + '</span>'; }

  // ---------------------------------------------------------------- cabeçalho e números
  function cabeca() {
    var papel = { equipe: 'Equipe ORGATEC', diretor: 'Diretoria', leitura: 'Leitura' }[estado.ctx.papel] || estado.ctx.papel;
    el.cabeca.innerHTML = '<div><p class="eyebrow">Acesso restrito</p><h1>' + esc(estado.ctx.grupo.nome || 'Painel do grupo') + '</h1>' +
      '<p class="lc-sub">' + selo('norma', papel) + ' <span>Hoje: ' + esc(A.dataCurta(estado.hoje)) + '</span></p></div>' +
      '<div class="lc-topo-acoes"><button class="lc-btn lc-btn-sec" type="button" data-acao-topo="atualizar">Atualizar</button>' +
      '<button class="lc-btn lc-btn-sec" type="button" data-acao-topo="sair">Sair</button></div>';
  }
  function kpis() {
    var r = A.resumo(estado.itens, estado.hoje), k = estado.filtro.kpi;
    function cartao(chave, numero, rotulo, tom) {
      return '<button type="button" class="lc-kpi lc-kpi-' + tom + '" data-kpi="' + chave + '" aria-pressed="' + (k === chave) + '"><b>' + numero + '</b><span>' + rotulo + '</span></button>';
    }
    el.kpis.innerHTML = cartao('atrasadas', r.atrasadas, 'Atrasadas', 'erro') + cartao('proximas', r.proximas30, 'Vencem em 30 dias', 'aviso') +
      cartao('andamento', r.andamento, 'Em andamento', 'info') + cartao('entregues', r.entreguesMes, 'Entregues neste mês', 'ok');
  }

  // ---------------------------------------------------------------- filtros
  function filtros() {
    var f = estado.filtro, opcoes = '<option value="">Todas as entidades</option><option value="__grupo"' + (f.entidade === '__grupo' ? ' selected' : '') + '>Do grupo (sem entidade)</option>' +
      estado.entidades.map(function (e) { return '<option value="' + esc(e.id) + '"' + (f.entidade === e.id ? ' selected' : '') + '>' + esc(e.nome) + '</option>'; }).join('');
    function radio(v, rotulo) { return '<label class="lc-chip"><input type="radio" name="lcStatus" value="' + v + '"' + (f.status === v ? ' checked' : '') + '><span>' + rotulo + '</span></label>'; }
    el.filtros.innerHTML = '<label class="lc-campo">Entidade <select id="lcEnt">' + opcoes + '</select></label>' +
      '<fieldset class="lc-chips"><legend>Situação</legend>' + radio('abertos', 'Abertos') + radio('entregues', 'Entregues') + radio('todos', 'Todos') + '</fieldset>' +
      '<label class="lc-campo">Período <select id="lcJanela"><option value="todos"' + (f.janela === 'todos' ? ' selected' : '') + '>Todos</option><option value="30"' + (f.janela === '30' ? ' selected' : '') +
      '>Até 30 dias</option><option value="90"' + (f.janela === '90' ? ' selected' : '') + '>Até 90 dias</option></select></label>' +
      '<label class="lc-campo lc-busca">Buscar <input id="lcBusca" type="search" placeholder="título ou evidência" value="' + esc(f.busca) + '"></label>' +
      (f.kpi ? '<button type="button" class="lc-limpar" data-limpar-kpi>Filtro ativo: ' + esc({ atrasadas: 'atrasadas', proximas: 'vencem em 30 dias', andamento: 'em andamento', entregues: 'entregues' }[f.kpi]) + ' ✕</button>' : '');
  }

  // ---------------------------------------------------------------- agenda
  function acoesDoItem(i) {
    if (!equipe() || A.informativo(i)) return '';
    var b = function (acao, rotulo, sec) { return '<button type="button" class="lc-btn lc-btn-mini' + (sec ? ' lc-btn-sec' : '') + '" data-acao="' + acao + '" data-id="' + esc(i.id) + '">' + rotulo + '</button>'; };
    if (i.status === 'entregue' || i.status === 'nao_se_aplica') return b('reabrir', 'Reabrir', true);
    return b('entregar', 'Marcar como entregue') + (i.status === 'a_fazer' ? b('andamento', 'Em andamento', true) : '');
  }
  function linhaItem(i) {
    var classe = A.classificar(i, estado.hoje), ent = i.entidade_id ? entidadePorId(i.entidade_id) : null;
    var prazo = i.prazo && !i.prazo_a_confirmar ? '<strong>' + esc(A.dataCurta(i.prazo)) + '</strong><small>' + esc(A.relativo(estado.hoje, i.prazo)) + '</small>' :
      '<strong>' + (i.prazo ? esc(A.dataCurta(i.prazo)) : '—') + '</strong><small>a confirmar</small>';
    var evid = i.evidencia_ref ? '<p class="lc-evid">Evidência: ' + (seguro(i.evidencia_ref) ? '<a href="' + esc(i.evidencia_ref) + '" target="_blank" rel="noopener noreferrer">' + esc(i.evidencia_ref) + '</a>' : esc(i.evidencia_ref)) + '</p>' : '';
    var revisao = i.tipo === 'evento_reforma' || i.fonte_id ? selo('pendente', 'em revisão técnica') : '';
    var nota = i.modelo_id && M.porId[i.modelo_id] && M.porId[i.modelo_id].nota ? '<p class="lc-nota">' + esc(M.porId[i.modelo_id].nota) + '</p>' : '';
    var estadoRotulo = classe === 'atrasada' ? selo('pendente', 'Atrasada') : selo(i.status === 'entregue' ? 'definido' : 'norma', A.ROTULO_STATUS[i.status] || i.status);
    return '<li class="lc-item lc-' + classe + '" data-id="' + esc(i.id) + '"><div class="lc-prazo">' + prazo + '</div><div class="lc-corpo"><p class="lc-titulo">' + esc(i.titulo) + '</p>' +
      '<p class="lc-meta">' + esc(ent ? ent.nome : 'Grupo') + ' · ' + esc(A.ROTULO_TIPO[i.tipo] || i.tipo) + ' · ' + (i.responsavel === 'grupo' ? 'Responsável: grupo' : 'Responsável: ORGATEC') + '</p>' +
      nota + fonteHtml(i.fonte_id) + evid + '</div><div class="lc-lado">' + (A.informativo(i) ? selo('futuro', 'Marco') : estadoRotulo) + ' ' + revisao + '<div class="lc-acoes">' + acoesDoItem(i) + '</div></div></li>';
  }
  function agenda() {
    var lista = A.filtrar(estado.itens, estado.filtro, estado.hoje), grupos = A.porMes(lista);
    if (!estado.itens.length) {
      el.agenda.innerHTML = '<div class="lc-vazio"><p><strong>Ainda não há itens neste painel.</strong></p><p>' +
        (equipe() ? 'Use “Adicionar do catálogo” ou a carga de dados (tools/locar_carregar.py) para começar.' : 'A equipe da ORGATEC está preparando a agenda do grupo.') + '</p></div>';
      return;
    }
    if (!lista.length) { el.agenda.innerHTML = '<div class="lc-vazio"><p>Nenhum item com estes filtros.</p></div>'; return; }
    el.agenda.innerHTML = grupos.map(function (g) {
      return '<section class="lc-mes"><h3>' + esc(g.rotulo) + ' <small>' + g.itens.length + '</small></h3><ul class="lc-itens">' + g.itens.map(linhaItem).join('') + '</ul></section>';
    }).join('');
  }

  // ---------------------------------------------------------------- entidades
  function entidades() {
    var contagem = A.porEntidade(estado.itens, estado.hoje);
    if (!estado.entidades.length) { el.entidades.innerHTML = '<p class="lc-nota">Nenhuma entidade liberada para o seu acesso.</p>'; return; }
    el.entidades.innerHTML = estado.entidades.map(function (e) {
      var c = contagem[e.id] || { abertos: 0, atrasados: 0 }, passos = A.cicloDeVida(e).map(function (p) {
        return '<li class="' + (p.atual ? 'atual' : p.passado ? 'passado' : '') + '"' + (p.atual ? ' aria-current="step"' : '') + '>' + esc(p.rotulo) + '</li>';
      }).join('');
      var suc = e.status === 'em_incorporacao' && e.sucessora_id && entidadePorId(e.sucessora_id) ? '<p class="lc-nota">Incorporação por <strong>' + esc(entidadePorId(e.sucessora_id).nome) + '</strong></p>' : '';
      var regime = (A.ROTULO_REGIME[e.regime] || e.regime) + (e.regime_vigencia ? ' (desde ' + A.dataCurta(e.regime_vigencia) + ')' : '');
      var editar = equipe() ? '<details class="lc-editar"><summary>Alterar situação</summary><form data-form-entidade="' + esc(e.id) + '"><label class="lc-campo">Situação <select name="status">' +
        A.CICLO.map(function (s) { return '<option value="' + s + '"' + (e.status === s ? ' selected' : '') + '>' + esc(A.ROTULO_SITUACAO[s]) + '</option>'; }).join('') + '</select></label>' +
        '<label class="lc-campo">Sucessora <select name="sucessora"><option value="">—</option>' + estado.entidades.filter(function (o) { return o.id !== e.id; }).map(function (o) {
          return '<option value="' + esc(o.id) + '"' + (e.sucessora_id === o.id ? ' selected' : '') + '>' + esc(o.nome) + '</option>'; }).join('') + '</select></label>' +
        '<button class="lc-btn lc-btn-mini" type="submit">Salvar</button></form></details>' : '';
      return '<article class="lc-ent"><h3>' + esc(e.nome) + (e.sensivel ? ' ' + selo('pendente', 'dado sensível') : '') + '</h3><p class="lc-meta">' + esc(e.tipo === 'produtor_pf' ? 'Produtor rural (pessoa física)' : 'Empresa') +
        ' · ' + esc(regime) + (e.documento_mascarado ? ' · ' + esc(e.documento_mascarado) : '') + '</p><ol class="lc-ciclo" aria-label="Situação">' + passos + '</ol>' + suc +
        '<p class="lc-num">' + c.abertos + ' em aberto' + (c.atrasados ? ' · <b class="lc-alerta">' + c.atrasados + ' atrasado' + (c.atrasados > 1 ? 's' : '') + '</b>' : '') + '</p>' + editar + '</article>';
    }).join('');
  }

  // ---------------------------------------------------------------- marcos da reforma (catálogo público)
  function marcos() {
    var lista = M.MODELOS.filter(function (m) { return m.tipo === 'evento_reforma'; }).sort(function (a, b) { return String(a.prazo || '9999') < String(b.prazo || '9999') ? -1 : 1; });
    el.marcos.innerHTML = lista.map(function (m) {
      var passou = m.prazo && A.diasEntre(estado.hoje, m.prazo) < 0;
      return '<li class="lc-marco' + (passou ? ' passou' : '') + '"><time>' + (m.prazo && !m.prazoAConfirmar ? esc(A.dataCurta(m.prazo)) : 'a confirmar') + '</time><div><p>' + esc(m.titulo) + '</p>' +
        (m.nota ? '<p class="lc-nota">' + esc(m.nota) + '</p>' : '') + fonteHtml(m.fontes[0]) + '</div></li>';
    }).join('');
  }

  // ---------------------------------------------------------------- adicionar do catálogo (equipe)
  function adicionar() {
    if (!equipe()) { el.adicionar.hidden = true; return; }
    el.adicionar.hidden = false;
    var ents = estado.entidades.map(function (e) { return '<option value="' + esc(e.id) + '">' + esc(e.nome) + '</option>'; }).join('');
    el.adicionar.innerHTML = '<summary>Adicionar do catálogo</summary><form id="lcFormAdd"><label class="lc-campo">Perfil <select name="perfil"><option value="todos">Todos</option>' +
      '<option value="transporte">Transporte</option><option value="rural">Rural</option><option value="simples">Simples Nacional</option></select></label>' +
      '<label class="lc-campo lc-largo">Modelo <select name="modelo"></select></label><label class="lc-campo">Entidade <select name="entidade"><option value="">Do grupo (sem entidade)</option>' + ents + '</select></label>' +
      '<button class="lc-btn" type="submit">Adicionar ao painel</button></form><p class="lc-nota">Os modelos citam fonte oficial e entram com o selo “em revisão técnica”. Prazo não confirmado fica como “a confirmar”.</p>';
    var f = $('#lcFormAdd');
    function modelos() {
      f.modelo.innerHTML = M.doPerfil(f.perfil.value).map(function (m) { return '<option value="' + esc(m.id) + '">' + esc(m.titulo) + '</option>'; }).join('');
    }
    modelos();
    f.perfil.addEventListener('change', modelos);
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var m = M.porId[f.modelo.value], ent = f.entidade.value || null;
      if (!m) return;
      if (estado.itens.some(function (i) { return i.modelo_id === m.id && (i.entidade_id || null) === ent; })) { mensagem('Este modelo já está no painel para essa entidade.', 'erro'); return; }
      OL.api('POST', '/itens', M.paraItem(m, ent)).then(function (novo) { estado.itens.push(novo); desenhar(); mensagem('Item adicionado ao painel.', 'ok'); }, function (e) { mensagem(e.message, 'erro'); });
    });
  }

  // ---------------------------------------------------------------- trilha (equipe)
  function auditoria() {
    if (!equipe()) { el.auditoria.hidden = true; return; }
    el.auditoria.hidden = false;
    el.auditoria.innerHTML = '<summary>Trilha de auditoria</summary><div class="lc-aud"><p class="lc-nota">Quem fez o quê e quando. O conteúdo dos campos não é gravado na trilha.</p>' +
      '<p><button class="lc-btn lc-btn-mini lc-btn-sec" type="button" data-verificar>Verificar integridade</button></p><ol id="lcAudLista" class="lc-aud-lista"></ol></div>';
  }
  function carregarTrilha() {
    return OL.api('GET', '/auditoria?limite=30').then(function (elos) {
      $('#lcAudLista').innerHTML = elos.length ? elos.map(function (e) {
        return '<li><time>' + esc(dataHora(e.quando)) + '</time> <code>' + esc(e.usuario_id) + '</code> ' + esc(e.acao) + ' <small>' + esc(e.recurso_id) + '</small></li>';
      }).join('') : '<li>Nenhum registro ainda.</li>';
    }, function (e) { mensagem(e.message, 'erro'); });
  }

  // ---------------------------------------------------------------- operação: Janela de Campo e alertas (dados públicos do próprio site)
  var POLOS_PADRAO_UF = ['GO', 'TO', 'PA'];
  var CEU = { sol: 'Sol', nublado: 'Nublado', chuva: 'Chuva fraca', 'chuva-forte': 'Chuva forte', trovoada: 'Trovoada' };
  function lerJson(url) {
    return fetch(url, { credentials: 'same-origin' }).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
  }
  function plural(n, um, varios) { return n + ' ' + (n === 1 ? um : varios); }
  function tempo() {
    var alvo = $('#lcTempo');
    lerJson('/dados/campo/atual.json').then(function (b) {
      var escolhidos = estado.ctx.grupo.polos || [], polos = (b.polos || []).filter(function (p) {
        return escolhidos.length ? escolhidos.indexOf(p.id) >= 0 : POLOS_PADRAO_UF.indexOf(p.uf) >= 0;
      }).slice(0, 6);
      if (!polos.length) { alvo.innerHTML = '<p class="lc-nota">Sem polo da Janela de Campo para as regiões do grupo.</p>'; return; }
      var velho = b.dia && b.dia !== estado.hoje ? ' <span class="og-selo og-selo-pendente">boletim de ' + esc(A.dataCurta(b.dia)) + '</span>' : '';
      var fonte = (b.fontes || [])[0];
      alvo.innerHTML = '<ul class="lc-polos">' + polos.map(function (p) {
        var hoje = (p.dias || [])[0] || {}, prox = (p.dias || []).slice(1, 4);
        var pulv = p.ops && p.ops.pulv ? '<small>Pulverização: ' + esc(p.ops.pulv.janela || '—') + (p.ops.pulv.motivo ? ' · ' + esc(p.ops.pulv.motivo) : '') + '</small>' : '';
        return '<li class="lc-polo" data-polo="' + esc(p.id) + '"><strong>' + esc(p.nome) + ' <small>' + esc(p.uf) + '</small></strong>' +
          '<span class="lc-polo-hoje">' + esc(CEU[hoje.familia] || hoje.familia || '') + (hoje.trovoada ? ' · trovoada' : '') + ' · ' + esc(hoje.min) + '° a ' + esc(hoje.max) + '° · ' + esc(hoje.chuva) + ' mm</span>' + pulv +
          '<span class="lc-polo-prox">' + prox.map(function (d) { return '<span>' + esc(A.dataCurta(d.dia).slice(0, 5)) + ' ' + esc(d.chuva) + ' mm</span>'; }).join('') + '</span></li>';
      }).join('') + '</ul><p class="lc-nota">Boletim de ' + esc(A.dataCurta(b.dia)) + velho + (b.proximaAtualizacao ? ' · próxima atualização ' + esc(b.proximaAtualizacao) : '') +
        (fonte ? ' · Fonte: ' + (seguro(fonte.url) ? '<a href="' + esc(fonte.url) + '" target="_blank" rel="noopener noreferrer">' + esc(fonte.rotulo) + '</a>' : esc(fonte.rotulo)) : '') + '. Previsão por município, não por fazenda.</p>';
    }, function () { alvo.innerHTML = '<p class="lc-nota">Boletim da Janela de Campo indisponível agora. Tente de novo mais tarde.</p>'; });
  }
  function alertas() {
    var alvo = $('#lcAlertas');
    lerJson('/api/transporte/alertas-publicos').then(function (a) {
      var vigentes = (a.avisos || []).filter(function (x) { return x.vigente; }), focos = (a.focos || []).length;
      var creditos = Object.keys(a.fontes || {}).map(function (k) { return a.fontes[k].credito; }).filter(Boolean);
      alvo.innerHTML = '<p class="lc-op-num"><b>' + vigentes.length + '</b> ' + esc(plural(vigentes.length, 'aviso meteorológico vigente', 'avisos meteorológicos vigentes').replace(/^\d+ /, '')) + '</p>' +
        '<p class="lc-op-num"><b>' + focos + '</b> ' + esc(plural(focos, 'foco de fogo na região', 'focos de fogo na região').replace(/^\d+ /, '')) + '</p>' +
        (vigentes.length ? '<ul class="lc-avisos">' + vigentes.slice(0, 3).map(function (x) { return '<li>' + esc(x.titulo) + '</li>'; }).join('') + '</ul>' : '') +
        '<p class="lc-nota">Atualizado em ' + esc(dataHora(a.atualizado_em)) + (creditos.length ? ' · ' + esc(creditos.join(' · ')) : '') + '</p>';
    }, function () { alvo.innerHTML = '<p class="lc-nota">Alertas indisponíveis agora. O mapa público continua na Janela Empresarial.</p>'; });
  }

  function desenhar() { kpis(); filtros(); agenda(); entidades(); }  // o formulário do catálogo é desenhado só ao carregar: não perde o que a equipe escolheu

  // ---------------------------------------------------------------- carga e eventos
  function mostrarLogin(aviso) {
    el.painel.hidden = true;
    el.acesso.hidden = false;
    OL.painelEntrada(el.acesso, carregar);
    if (aviso) mensagem(aviso, 'erro');
  }

  function carregar() {
    mensagem('');
    return OL.prepararSessao().then(function () { return OL.api('GET', '/contexto'); }).then(function (ctx) {
      return OL.api('GET', '/agenda').then(function (a) {
        estado.ctx = ctx; estado.hoje = a.hoje; estado.itens = a.itens;
        estado.entidades = a.entidades.slice().sort(function (x, y) { return x.nome.localeCompare(y.nome, 'pt-BR'); });
        el.acesso.hidden = true; el.painel.hidden = false;
        cabeca(); desenhar(); marcos(); adicionar(); auditoria(); tempo(); alertas();
      });
    }).catch(function (e) { mostrarLogin(e.status ? e.message : null); if (!e.status) mensagem(e.message, 'erro'); });
  }

  document.addEventListener('click', function (ev) {
    var t = ev.target.closest('[data-kpi],[data-limpar-kpi],[data-acao],[data-acao-topo],[data-verificar]');
    if (!t) return;
    if (t.hasAttribute('data-kpi')) { var k = t.getAttribute('data-kpi'); estado.filtro.kpi = estado.filtro.kpi === k ? '' : k; kpis(); filtros(); agenda(); return; }
    if (t.hasAttribute('data-limpar-kpi')) { estado.filtro.kpi = ''; kpis(); filtros(); agenda(); return; }
    var topo = t.getAttribute('data-acao-topo');
    if (topo === 'sair') { OL.sair(); estado.ctx = null; mostrarLogin(); return; }
    if (topo === 'atualizar') { carregar().then(function () { if (estado.ctx) mensagem('Painel atualizado.', 'ok'); }); return; }
    if (t.hasAttribute('data-verificar')) {
      OL.api('GET', '/auditoria/verificar').then(function (r) {
        mensagem(r.integra ? 'Trilha íntegra: ' + r.elos + ' registros conferidos.' : 'Atenção: a trilha tem uma inconsistência. Avise o responsável técnico.', r.integra ? 'ok' : 'erro');
      }, function (e) { mensagem(e.message, 'erro'); });
      return;
    }
    var acao = t.getAttribute('data-acao'), id = t.getAttribute('data-id');
    var status = { entregar: 'entregue', andamento: 'em_andamento', reabrir: 'a_fazer' }[acao];
    if (!status) return;
    t.disabled = true;
    OL.api('PATCH', '/itens/' + encodeURIComponent(id), { status: status }).then(function (novo) {
      estado.itens = estado.itens.map(function (i) { return i.id === id ? novo : i; });
      desenhar(); mensagem('Item atualizado.', 'ok');
    }, function (e) { t.disabled = false; mensagem(e.message, 'erro'); });
  });

  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (t.id === 'lcEnt') estado.filtro.entidade = t.value;
    else if (t.name === 'lcStatus') { estado.filtro.status = t.value; estado.filtro.kpi = ''; }
    else if (t.id === 'lcJanela') { estado.filtro.janela = t.value; estado.filtro.kpi = ''; }
    else return;
    kpis(); filtros(); agenda();
  });
  document.addEventListener('input', function (ev) {
    if (ev.target.id !== 'lcBusca') return;
    estado.filtro.busca = ev.target.value;
    agenda();  // sem refazer a barra de filtros: o campo de busca mantém o foco
  });
  document.addEventListener('submit', function (ev) {
    var f = ev.target.closest('[data-form-entidade]');
    if (!f) return;
    ev.preventDefault();
    var id = f.getAttribute('data-form-entidade'), corpo = { status: f.status.value };
    if (f.sucessora.value) corpo.sucessora_id = f.sucessora.value;
    OL.api('PATCH', '/entidades/' + encodeURIComponent(id), corpo).then(function (novo) {
      estado.entidades = estado.entidades.map(function (e) { return e.id === id ? Object.assign({}, e, novo) : e; });
      desenhar(); mensagem('Situação da entidade atualizada.', 'ok');
    }, function (e) { mensagem(e.message, 'erro'); });
  });
  document.addEventListener('toggle', function (ev) {
    if (ev.target === el.auditoria && el.auditoria.open) carregarTrilha();
  }, true);

  if (OL.temSessao() || OL.temDev()) carregar(); else mostrarLogin();
})();
