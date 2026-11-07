/* Liga as páginas geradas por tools/gerar_paginas.py aos dados: itens da reforma, notícias,
   alertas por setor, calculadoras, prova de confiança e links de WhatsApp/portal (config.js).
   A lógica fica nos módulos puros (conteudo.js, calculadoras.js, regras.js); aqui só há DOM. */
(function () {
  'use strict';
  var O = window.Orgatec, C = O.config, F = O.fontes, K = O.conteudo;
  var HOJE = new Date().toISOString().slice(0, 10);
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function brl(v) { return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }); }

  // Links, menu e faixa: só nas páginas do layout comum (na página inicial, app.js já faz isso).
  if (document.body.hasAttribute('data-layout')) {
    $$('[data-link="portal"]').forEach(function (a) { a.href = C.portal.url; });
    $$('[data-link^="whatsapp"]').forEach(function (a) {
      var msg = a.getAttribute('data-msg') || 'Olá! Vim pelo site da ORGATEC e gostaria de falar sobre a reforma tributária.';
      a.href = 'https://wa.me/' + C.whatsapp.numeroE164 + '?text=' + encodeURIComponent(msg);
    });
    $$('[data-texto="whatsapp"]').forEach(function (s) { s.textContent = C.whatsapp.exibicao; });
    var btn = $('#btnMenu'), menu = $('#menuMobile');
    if (btn && menu) {
      btn.addEventListener('click', function () { menu.hidden = !menu.hidden; btn.setAttribute('aria-expanded', String(!menu.hidden)); });
      $$('a', menu).forEach(function (a) { a.addEventListener('click', function () { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); }); });
    }
    var faixa = $('#faixaHomologacao');
    if (faixa) faixa.hidden = C.ambiente !== 'homologacao';

    // Grupos do menu (Setores, Ferramentas): um aberto por vez; fecham com clique fora ou Esc
    var grupos = $$('[data-nav-grupo]');
    grupos.forEach(function (g) {
      g.addEventListener('toggle', function () { if (g.open) grupos.forEach(function (o) { if (o !== g) o.open = false; }); });
    });
    document.addEventListener('click', function (ev) { grupos.forEach(function (g) { if (!g.contains(ev.target)) g.open = false; }); });
    document.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Escape') return;
      grupos.forEach(function (g) { if (g.open) { g.open = false; $('summary', g).focus(); } });
    });

    // Encarregado de dados (DPO) no rodapé: e-mail só depois de ativado em config.js
    var rod = $('#rodapeEmails');
    if (rod) {
      rod.textContent = 'Encarregado de dados (DPO): ';
      var a = document.createElement('a');
      a.className = 'hover:underline';
      if (C.emails.dpo.ativo) { a.href = 'mailto:' + C.emails.dpo.endereco; a.textContent = C.emails.dpo.endereco; }
      else { a.href = rod.getAttribute('data-contato') || 'contato/index.html'; a.textContent = 'solicitações pelo formulário de contato (assunto LGPD)'; }
      rod.appendChild(a);
    }

    // Canal do encarregado na página Escritório: troca o aviso pelo e-mail só depois de ativado em config.js
    $$('[data-dpo]').forEach(function (p) {
      if (!C.emails.dpo.ativo) return;
      p.textContent = 'E-mail do encarregado de dados (DPO): ';
      var a = document.createElement('a');
      a.className = 'og-link'; a.href = 'mailto:' + C.emails.dpo.endereco; a.textContent = C.emails.dpo.endereco;
      p.appendChild(a);
    });

    // Barra fixa do celular: recolhida enquanto o herói (que já tem os mesmos botões) está na tela
    var barra = $('[data-barra-movel]'), heroi = $('[data-hero]');
    if (barra && heroi && 'IntersectionObserver' in window) {
      barra.classList.add('recolhida');
      new IntersectionObserver(function (es) { barra.classList.toggle('recolhida', es[0].isIntersecting); }).observe(heroi);
    }
  }

  // Prova de confiança: o número de anos só aparece com data e comprovação em config.institucional
  var anos = K.anosAtuacao(C.institucional, HOJE);
  $$('[data-prova-anos]').forEach(function (el) {
    if (anos) { el.textContent = anos + ' anos de atuação'; el.hidden = false; } else el.hidden = true;
  });

  // Itens da reforma
  // Itens da reforma + itens de compliance (compliance-itens.js, carregado só nas páginas da área)
  var base = K.publicaveis(O.reformaItens.concat(O.complianceItens || []), F.porId, C.ambiente);
  if (base.rejeitados.length && window.console) console.warn('Itens da reforma fora da tela:', base.rejeitados);
  $$('[data-itens]').forEach(function (alvo) {
    var fixo = { destino: alvo.getAttribute('data-destino') || null, setor: alvo.getAttribute('data-setor') || null };
    var limite = +alvo.getAttribute('data-limite') || 0;
    var lista = $('.lista-itens', alvo) || alvo;
    function desenha() {
      var f = Object.assign({}, fixo);
      $$('select[data-filtro]', alvo).forEach(function (s) { if (s.value) f[s.getAttribute('data-filtro')] = s.value; });
      var itens = K.filtrar(base.itens, f);
      if (limite) itens = itens.slice(0, limite);
      lista.innerHTML = itens.length ? itens.map(function (it) { return K.renderItem(it, F.porId); }).join('')
        : '<p class="og-cartao-texto">Nenhum item com esses filtros.' + (C.ambiente === 'producao' ? ' Itens aguardando revisão técnica não aparecem.' : '') + '</p>';
      var n = $('[data-contagem]', alvo);
      if (n) n.textContent = itens.length + (itens.length === 1 ? ' item' : ' itens');
    }
    $$('select[data-filtro]', alvo).forEach(function (s) { s.addEventListener('change', desenha); });
    desenha();
  });

  // Datas que pedem atenção (itens com `prazo`, de hoje em diante), com a fonte de cada uma
  $$('[data-prazos]').forEach(function (alvo) {
    var lista = K.proximosPrazos(base.itens.filter(function (it) { return it.destinos.indexOf(alvo.getAttribute('data-prazos')) >= 0; }), HOJE);
    alvo.innerHTML = lista.length ? lista.map(function (it) {
      return '<li class="og-cartao og-item"><span class="og-item-meta">' + K.formatarData(it.prazo) + '</span>' +
        '<p class="og-cartao-titulo">' + K.esc(it.titulo) + '</p><div class="og-item-fontes">' + K.citacoes(it.fontes, F.porId) + '</div>' +
        '<a class="og-link text-sm" href="#item-' + K.esc(it.id) + '">Ver o ponto completo</a></li>';
    }).join('') : '<li class="og-cartao-texto">Nenhuma data próxima publicada.' + (C.ambiente === 'producao' ? ' Itens aguardando revisão técnica não aparecem.' : '') + '</li>';
  });

  // Perguntas frequentes da área de Compliance: itens com `pergunta`; a resposta é o fato do item, com fonte e status
  $$('[data-faq-itens]').forEach(function (alvo) {
    var destino = alvo.getAttribute('data-faq-itens');
    var lista = base.itens.filter(function (it) { return it.pergunta && it.destinos.indexOf(destino) >= 0; });
    alvo.innerHTML = lista.length ? lista.map(function (it) {
      var st = K.STATUS[it.status];
      return '<details data-item="' + K.esc(it.id) + '"><summary>' + K.esc(it.pergunta) + '</summary><div class="resposta">' +
        '<p class="og-cartao-titulo" style="margin:0"><span class="og-selo og-selo-' + st.tom + '">' + st.rotulo + '</span>' +
        (it.revisao.status === 'aprovada' ? '' : '<span class="og-selo og-selo-pendente">em revisão técnica</span>') + '</p>' +
        '<p>' + K.esc(it.fato) + '</p><div class="og-item-fontes">' + K.citacoes(it.fontes, F.porId) + '</div>' +
        '<p class="og-item-meta">Consultado em ' + K.formatarData(it.consultadoEm) + ' · <a class="og-link" href="#item-' + K.esc(it.id) + '">ver o ponto completo</a></p></div></details>';
    }).join('') : '<p class="text-muted">As respostas aparecem aqui depois da revisão técnica.</p>';
  });

  // Central de notícias
  $$('[data-noticias]').forEach(function (alvo) {
    var lista = K.noticias(base.itens, +alvo.getAttribute('data-noticias') || 0);
    alvo.innerHTML = lista.length ? lista.map(function (n) {
      return '<li class="og-cartao og-item"><span class="og-item-meta">' + K.formatarData(n.data) + '</span>' +
        '<p class="og-cartao-texto"><strong class="text-tinta">' + K.esc(n.nota) + '</strong></p>' +
        '<a class="og-link text-sm" href="' + (alvo.getAttribute('data-base') || '') + 'reforma/index.html#item-' + K.esc(n.id) + '">' + K.esc(n.titulo) + '</a></li>';
    }).join('') : '<li class="og-cartao-texto">Sem atualizações publicadas.</li>';
  });

  // Alertas regionais por setor (GO, TO, PA), reaproveitando regras.alertasRegionais
  $$('[data-alertas]').forEach(function (alvo) {
    var setor = alvo.getAttribute('data-alertas'), sel = $('select', alvo), lista = $('.lista-alertas', alvo);
    function desenha() {
      var al = O.regras.alertasRegionais(sel.value, setor);
      lista.innerHTML = al.map(function (a) {
        return '<li class="og-cartao og-item"><h3 class="og-cartao-titulo">' + K.esc(a.titulo) + '</h3><p class="og-cartao-texto">' + K.esc(a.texto) + '</p>' +
          '<div class="og-item-fontes">' + K.citacoes(a.fontes.filter(function (id) { return F.porId[id]; }), F.porId) + '</div></li>';
      }).join('');
    }
    sel.addEventListener('change', desenha);
    desenha();
  });

  // Linha do tempo 2026–2033 a partir de regras.TRANSICAO (mesma tabela do simulador)
  $$('[data-linha-tempo]').forEach(function (alvo) {
    alvo.innerHTML = O.regras.TRANSICAO.map(function (l) {
      return '<tr class="border-b border-linha"><td class="py-2 pr-4 font-mono">' + l.ano + '</td><td class="py-2 pr-4">' + K.esc(l.cbs) + '</td><td class="py-2 pr-4">' + K.esc(l.ibs) +
        '</td><td class="py-2 pr-4">' + K.esc(l.piscofins) + '</td><td class="py-2 pr-4">' + K.esc(l.ipi) + '</td><td class="py-2">' + K.esc(l.icmsiss) + '</td></tr>';
    }).join('');
  });

  // Soluções: selo de situação e botão "Entrar" a partir de config.solucoes. O site só faz LINK para o sistema
  // (subdomínio próprio); o botão só aparece com situacao 'disponivel' e endereço https.
  var SITUACAO = { disponivel: ['definido', 'Disponível'], demonstracao: ['futuro', 'Demonstração com a equipe'],
    servico: ['norma', 'Serviço do escritório'], em_breve: ['pendente', 'Em breve'], rascunho: ['pendente', 'Em preparação'] };
  $$('[data-solucao]').forEach(function (el) {
    var s = (C.solucoes || {})[el.getAttribute('data-solucao')] || {}, st = SITUACAO[s.situacao] || SITUACAO.rascunho;
    var selo = $('[data-solucao-selo]', el);
    if (selo) { selo.className = 'og-selo og-selo-' + st[0]; selo.textContent = st[1]; }
    var lugar = $('[data-solucao-entrar]', el);
    if (lugar && s.situacao === 'disponivel' && /^https:\/\/[^\s"'<>]+$/.test(s.url || '')) {
      var a = document.createElement('a');
      a.href = s.url; a.rel = 'noopener'; a.className = lugar.getAttribute('data-classe') || 'og-btn og-btn-contorno og-btn-lg';
      a.textContent = 'Entrar';
      lugar.appendChild(a); lugar.hidden = false;
    }
  });

  // Situação do portal (ERP ainda não definido em config.js)
  $$('[data-portal-erp]').forEach(function (el) {
    var erp = C.portal.erp && C.portal.opcoes[C.portal.erp];
    el.className = 'og-selo ' + (erp ? 'og-selo-definido' : 'og-selo-pendente');
    el.textContent = erp ? 'ERP: ' + erp.nome : 'ERP do portal: pendente de definição';
  });

  // Painel de testes: autoteste e pendências da próxima fase (homologacao.js)
  var H = O.homologacao;
  if (H && $('[data-pendencias]')) {
    var casos = H.autoteste(O, HOJE);
    var okN = casos.filter(function (c) { return c.ok; }).length;
    $('[data-autoteste]').innerHTML = casos.map(function (c) {
      return '<li class="og-cartao flex items-start gap-3" data-ok="' + c.ok + '"><span class="og-selo og-selo-' + (c.ok ? 'definido' : 'pendente') + '">' + (c.ok ? 'passou' : 'falhou') + '</span>' +
        '<div class="min-w-0"><p class="font-semibold text-tinta text-sm">' + K.esc(c.nome) + '</p><p class="og-item-meta">' + K.esc(c.detalhe) + '</p></div></li>';
    }).join('');
    var av = H.avaliar({ config: C, fontes: F, itens: O.reformaItens, complianceItens: O.complianceItens || [], ufs: O.ufs, conteudo: K, hoje: HOJE });
    var res = { ambiente: C.ambiente === 'homologacao' ? 'Homologação' : 'Produção', abertas: av.resumo.abertas + ' / ' + av.resumo.total,
      bloqueios: String(av.resumo.bloqueios), autoteste: okN + ' / ' + casos.length };
    Object.keys(res).forEach(function (k) { var el = $('[data-resumo="' + k + '"]'); if (el) el.textContent = res[k]; });
    var alvo = $('[data-pendencias]');
    var desenhaPend = function () {
      var st = $('#pdStatus').value, rp = $('#pdResp').value, bl = $('#pdBloqueia').checked;
      var vis = av.itens.filter(function (i) { return (!st || i.status === st) && (!rp || i.responsavel === rp) && (!bl || i.bloqueia); });
      $('#pdContagem').textContent = vis.length + (vis.length === 1 ? ' pendência' : ' pendências');
      alvo.innerHTML = Object.keys(H.CATEGORIAS).map(function (cat) {
        var g = vis.filter(function (i) { return i.categoria === cat; });
        if (!g.length) return '';
        return '<div><h3 class="text-lg font-bold text-tinta mb-3">' + K.esc(H.CATEGORIAS[cat]) + '</h3><div class="grid grid-cols-1 lg:grid-cols-2 gap-4">' + g.map(function (i) {
          return '<article class="og-cartao og-item" id="pendencia-' + i.id + '" data-status="' + i.status + '" data-bloqueia="' + i.bloqueia + '">' +
            '<span class="og-cartao-ref">' + i.id + ' · ' + K.esc(H.RESPONSAVEL[i.responsavel]) + (i.automatica ? ' · verificação automática' : '') + '</span>' +
            '<h4 class="og-cartao-titulo">' + K.esc(i.titulo) + '<span class="og-selo og-selo-' + (i.status === 'resolvida' ? 'definido' : 'pendente') + '">' + i.status + '</span>' +
            (i.bloqueia ? '<span class="og-selo og-selo-futuro">bloqueia produção</span>' : '') + '</h4>' +
            (i.descricao ? '<p class="og-cartao-texto">' + K.esc(i.descricao) + '</p>' : '') +
            (i.detalhe ? '<p class="text-sm text-tinta-texto"><strong>Situação:</strong> ' + K.esc(i.detalhe) + '</p>' : '') +
            '<p class="og-item-meta">Onde resolver: ' + K.esc(i.onde) + (i.depende && i.depende.length ? ' · Depende de: ' + K.esc(i.depende.join(', ')) : '') + '</p></article>';
        }).join('') + '</div></div>';
      }).join('') || '<p class="og-cartao-texto">Nenhuma pendência com esses filtros.</p>';
    };
    ['#pdStatus', '#pdResp', '#pdBloqueia'].forEach(function (s) { $(s).addEventListener('change', desenhaPend); });
    desenhaPend();
    $('#btnCopiarPendencias').addEventListener('click', function () {
      var texto = H.comoTexto(av, HOJE), b = this;
      var aviso = function (m) { b.textContent = m; setTimeout(function () { b.textContent = 'Copiar lista (Markdown)'; }, 2500); };
      var selecionar = function () { var t = $('#pdTexto'); t.value = texto; t.select(); try { document.execCommand('copy'); aviso('Lista copiada'); } catch (e) { aviso('Selecione e copie manualmente'); } };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texto).then(function () { aviso('Lista copiada'); }, selecionar);
      else selecionar();
    });
  }

  // Calculadora 1: transição ano a ano
  var ft = $('#formTransicao');
  if (ft) ft.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var r = O.calculadoras.transicaoAno($('#tAno').value, $('#tIcms').value), out = $('#tResultado');
    out.hidden = false;
    if (r.erro) { out.innerHTML = '<p class="og-campo-erro" role="alert">' + K.esc(r.erro) + '</p>'; return; }
    if (r.fase === 'anterior') { out.innerHTML = '<p class="og-cartao-texto">' + K.esc(r.texto) + '</p>'; return; }
    var l = r.linha;
    out.innerHTML = '<dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">' +
      '<dt class="text-tinta-suave">CBS</dt><dd class="font-semibold">' + K.esc(l.cbs) + '</dd>' +
      '<dt class="text-tinta-suave">IBS</dt><dd class="font-semibold">' + K.esc(l.ibs) + '</dd>' +
      '<dt class="text-tinta-suave">PIS/Cofins</dt><dd class="font-semibold">' + K.esc(l.piscofins) + '</dd>' +
      '<dt class="text-tinta-suave">IPI</dt><dd class="font-semibold">' + K.esc(l.ipi) + '</dd>' +
      '<dt class="text-tinta-suave">ICMS e ISS</dt><dd class="font-semibold">' + K.esc(l.icmsiss) + ' das alíquotas atuais</dd></dl>' +
      (r.icmsIssRestante != null ? '<p class="mt-3 text-sm">ICMS/ISS estimado em ' + r.ano + ': <strong class="font-mono">' + brl(r.icmsIssRestante) + '</strong> (proporção aplicada sobre o valor informado, sem considerar mudança de preço ou de legislação local).</p>' : '') +
      (r.texto ? '<p class="mt-3 text-sm">' + K.esc(r.texto) + '</p>' : '') +
      '<div class="og-item-fontes mt-3">' + K.citacoes(r.fontes, F.porId) + '</div>';
  });

  // Calculadora 3: pessoa física com imóveis (página Compliance por público: imóveis)
  var fi = $('#formImoveisPF');
  if (fi) fi.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var r = O.calculadoras.imoveisPessoaFisica({ receitaAnterior: $('#iReceitaAnt').value, locadosAnterior: $('#iLocadosAnt').value,
      vendidosAnterior: $('#iVendidosAnt').value, construidosAnterior: $('#iConstruidosAnt').value,
      receitaAtual: $('#iReceitaAtual').value, vendidosAtual: $('#iVendidosAtual').value, construidosAtual: $('#iConstruidosAtual').value });
    var out = $('#iResultado');
    out.hidden = false;
    if (r.erro) { out.innerHTML = '<p class="og-campo-erro" role="alert">' + K.esc(r.erro) + '</p>'; return; }
    out.innerHTML = '<p class="og-cartao-titulo" data-imoveis-resultado="' + (r.contribuinte ? 'contribuinte' : 'nao') + '">' +
      (r.contribuinte ? 'Pelas informações dadas, você passa a ser contribuinte de IBS e CBS nas operações com imóveis.' : 'Pelas informações dadas, você não passa a ser contribuinte de IBS e CBS por causa dos imóveis.') + '</p>' +
      (r.motivos.length ? '<ul class="list-disc pl-5 mt-2 text-sm">' + r.motivos.map(function (m) { return '<li>' + K.esc(m.texto) + ' <span class="text-tinta-fraca">(' + K.esc(m.regra) + ')</span></li>'; }).join('') + '</ul>' : '') +
      '<p class="text-xs text-tinta-fraca mt-3">' + K.esc(r.aviso) + '</p><div class="og-item-fontes mt-2">' + K.citacoes(r.fontes, F.porId) + '</div>';
  });

  // Calculadora 2: produtor rural contribuinte ou não
  var fp = $('#formProdutor');
  if (fp) fp.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var r = O.calculadoras.produtorRural({ receita: $('#pReceita').value, mesesAtividade: $('#pMeses').value,
      mesExcesso: $('#pMesExcesso').value, integrado: $('#pIntegrado').checked, optou: $('#pOptou').checked });
    var out = $('#pResultado');
    out.hidden = false;
    if (r.erro) { out.innerHTML = '<p class="og-campo-erro" role="alert">' + K.esc(r.erro) + '</p>'; return; }
    out.innerHTML = '<p class="og-cartao-titulo">' + (r.contribuinte ? 'Contribuinte de IBS e CBS' : 'Não contribuinte de IBS e CBS') +
      '<span class="og-selo og-selo-' + (r.contribuinte ? 'futuro' : 'definido') + '">' + (r.contribuinte ? 'regime regular' : 'fora do regime regular') + '</span></p>' +
      '<p class="og-cartao-texto">' + K.esc(r.texto) + '</p>' +
      (r.consequencias ? '<ul class="list-disc pl-5 mt-3 text-sm space-y-1">' + r.consequencias.map(function (c) { return '<li>' + K.esc(c) + '</li>'; }).join('') + '</ul>' : '') +
      '<p class="mt-3 text-xs text-tinta-fraca">Limite considerado: <span class="font-mono">' + brl(r.limite) + '</span>. ' + K.esc(r.avisos.join(' ')) + '</p>' +
      '<div class="og-item-fontes mt-3">' + K.citacoes(r.fontes, F.porId) + '</div>';
  });
})();
