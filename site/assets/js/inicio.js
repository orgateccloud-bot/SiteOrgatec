/* Interações da página inicial: painel da transição, números, marcos que acendem ao rolar e perguntas
   frequentes. Só DOM: as contas vêm de calculadoras.js, regras.js e conteudo.js. Todo conteúdo já aparece
   pronto ao carregar; as animações só enfeitam a chegada e são desligadas em prefers-reduced-motion. */
(function () {
  'use strict';
  var O = window.Orgatec, C = O.config, F = O.fontes, K = O.conteudo, CALC = O.calculadoras;
  var HOJE = new Date().toISOString().slice(0, 10);
  var CBS = '2027-01-01';
  var calmo = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function nf(n) { return n.toLocaleString('pt-BR'); }
  // Endereços antigos da página inicial (/#simulador, /?setor=agro#simulador...) levam às páginas próprias
  var MUDOU = { '#simulador': 'ferramentas/simulador.html', '#calendario': 'ferramentas/calendario.html', '#contato': 'contato/index.html',
    '#regional': 'setores/regional.html', '#servicos': 'cliente/index.html', '#reforma': 'reforma/index.html', '#setores': 'setores/agro.html' };
  if ($('[data-painel-transicao]') && MUDOU[location.hash]) { location.replace(MUDOU[location.hash] + location.search); return; }
  function quandoVisivel(el, fn, limiar) {
    if (calmo || !('IntersectionObserver' in window)) { fn(); return; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { fn(); io.disconnect(); } }); }, { threshold: limiar || 0.4 });
    io.observe(el);
  }

  // ---------- Painel da transição
  var painel = $('[data-painel-transicao]');
  if (painel) {
    var p = CALC.progressoTransicao(HOJE) || 0, dias = CALC.diasAte(CBS, HOJE);
    var anel = $('[data-anel]', painel), circ = 2 * Math.PI * 42;
    $('[data-progresso]', painel).textContent = Math.round(p * 100) + '%';
    requestAnimationFrame(function () { anel.style.strokeDashoffset = String(circ * (1 - p)); });
    $('[data-contagem-cbs]', painel).innerHTML = dias > 0
      ? 'Faltam <strong class="font-mono">' + nf(dias) + '</strong> dias para a CBS substituir PIS e Cofins.'
      : 'A CBS já substituiu PIS e Cofins (desde 01/01/2027).';
    var anoAtual = Math.min(2033, Math.max(2026, +HOJE.slice(0, 4)));
    var chips = $('[data-anos]', painel), dl = $('[data-linha-ano]', painel);
    chips.innerHTML = O.regras.TRANSICAO.map(function (l) {
      return '<button type="button" class="chip" data-ano="' + l.ano + '" aria-pressed="' + (+l.ano === anoAtual) + '">' + l.ano + '</button>';
    }).join('');
    var desenha = function (ano) {
      var r = CALC.transicaoAno(ano), l = r.linha, resto = Math.round(r.proporcaoIcmsIss * 100);
      dl.innerHTML =
        '<dt>CBS</dt><dd>' + K.esc(l.cbs) + '</dd>' +
        '<dt>IBS</dt><dd>' + K.esc(l.ibs) + '</dd>' +
        '<dt>PIS/Cofins</dt><dd>' + K.esc(l.piscofins) + '</dd>' +
        '<dt>IPI</dt><dd>' + K.esc(l.ipi) + '</dd>' +
        '<dt>ICMS e ISS</dt><dd>' + (resto ? resto + '% das alíquotas atuais' : 'extintos') +
        '<span class="barra" aria-hidden="true"><i style="width:' + resto + '%"></i></span></dd>';
      $$('.chip', chips).forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-ano') === String(ano))); });
    };
    chips.addEventListener('click', function (ev) { var b = ev.target.closest('[data-ano]'); if (b) desenha(+b.getAttribute('data-ano')); });
    chips.addEventListener('keydown', function (ev) {  // setas trocam o ano, como em abas
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      var bs = $$('.chip', chips), i = bs.indexOf(document.activeElement);
      if (i < 0) return;
      var j = (i + (ev.key === 'ArrowRight' ? 1 : -1) + bs.length) % bs.length;
      bs[j].focus(); bs[j].click(); ev.preventDefault();
    });
    desenha(anoAtual);
  }

  // ---------- Números (valores reais; contam a partir de zero ao entrar na tela)
  var bloco = $('[data-numeros]');
  if (bloco) {
    var pub = K.publicaveis(O.reformaItens, F.porId, C.ambiente).itens.length;
    var valores = {
      itens: pub, ufs: O.ufs.lista.length, dias: CALC.diasAte(CBS, HOJE) || 0,
      fontes: F.lista.filter(function (f) { return f.validado; }).length
    };
    var alvos = $$('[data-contador]', bloco);
    alvos.forEach(function (el) { el.textContent = nf(valores[el.getAttribute('data-contador')]); });
    if (!calmo) quandoVisivel(bloco, function () {
      var t0 = null, dur = 1100;
      var passo = function (t) {
        if (t0 === null) t0 = t;
        var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        alvos.forEach(function (el) { el.textContent = nf(Math.round(valores[el.getAttribute('data-contador')] * e)); });
        if (k < 1) requestAnimationFrame(passo);
      };
      requestAnimationFrame(passo);
    });
  }

  // ---------- Marcos que acendem ao rolar
  var marcos = $$('[data-marcos] .marco');
  marcos.forEach(function (m, i) {
    quandoVisivel(m, function () { setTimeout(function () { m.classList.add('aceso'); }, calmo ? 0 : i * 140); }, 0.6);
  });

  // ---------- Perguntas frequentes: resposta = fato do item da reforma, com status e fonte
  var PERGUNTAS = [
    ['Quando o PIS e a Cofins deixam de existir?', 'cbs-2027'],
    ['Qual será a alíquota do IBS e da CBS?', 'aliquota-referencia'],
    ['O produtor rural passa a pagar IBS e CBS?', 'produtor-nao-contribuinte'],
    ['O que muda no CT-e e na NF-e?', 'documentos-fiscais'],
    ['A empresa do Simples pode tirar IBS e CBS do DAS?', 'simples-hibrido'],
    ['O que acontece com os créditos de PIS e Cofins acumulados?', 'saldo-piscofins']
  ];
  var faq = $('[data-faq]');
  if (faq) {
    var porId = {};
    K.publicaveis(O.reformaItens, F.porId, C.ambiente).itens.forEach(function (it) { porId[it.id] = it; });
    var limite = +faq.getAttribute('data-limite') || PERGUNTAS.length;
    var html = PERGUNTAS.filter(function (q) { return porId[q[1]]; }).slice(0, limite).map(function (q) {
      var it = porId[q[1]], st = K.STATUS[it.status];
      return '<details data-item="' + it.id + '"><summary>' + K.esc(q[0]) + '</summary><div class="resposta">' +
        '<p class="og-cartao-titulo" style="margin:0"><span class="og-selo og-selo-' + st.tom + '">' + st.rotulo + '</span>' +
        (it.revisao.status === 'aprovada' ? '' : '<span class="og-selo og-selo-pendente">em revisão técnica</span>') + '</p>' +
        '<p>' + K.esc(it.fato) + '</p><div class="og-item-fontes">' + K.citacoes(it.fontes, F.porId) + '</div>' +
        '<p class="og-item-meta">Consultado em ' + K.formatarData(it.consultadoEm) + ' · <a class="og-link" href="reforma/index.html#item-' + it.id + '">ver na Central da Reforma</a></p>' +
        '</div></details>';
    }).join('');
    faq.innerHTML = html || '<p class="text-muted">As respostas aparecem aqui depois da revisão técnica.</p>';
  }

  // ---------- "Qual é o seu caso?": os cartões viram seletor e abrem os pontos da reforma de cada perfil
  // Só itens de reforma-itens.js (com fonte e status) e páginas que já existem; em produção, só itens aprovados.
  var CASOS = {
    simples: { rotulo: 'Simples Nacional', itens: ['simples-hibrido', 'teste-2026', 'split-payment'], guia: 'reforma/simples-hibrido.html', sim: '?regime=simples' },
    real: { rotulo: 'Lucro real e presumido', itens: ['cbs-2027', 'nao-cumulatividade', 'saldo-piscofins'], guia: 'reforma/cbs.html', sim: '?regime=real' },
    agro: { rotulo: 'Agro e produtor rural', itens: ['produtor-nao-contribuinte', 'agro-reducao-60', 'credito-presumido-produtor'], guia: 'setores/agro.html', sim: '?setor=agro' },
    transporte: { rotulo: 'Transporte', itens: ['transporte-carga', 'documentos-fiscais', 'tac-credito-presumido'], guia: 'empresarial/transporte.html', sim: '' }
  };
  var painelCaso = $('[data-caso-painel]'), cartoesCaso = $$('a[data-caso]');
  if (painelCaso && cartoesCaso.length) {
    var publicados = {};
    K.publicaveis(O.reformaItens, F.porId, C.ambiente).itens.forEach(function (it) { publicados[it.id] = it; });
    var dica = $('[data-caso-dica]');
    if (dica) dica.hidden = false;
    var abrirCaso = function (chave) {
      var c = CASOS[chave];
      cartoesCaso.forEach(function (a) { a.setAttribute('aria-pressed', String(a.getAttribute('data-caso') === chave)); });
      var lista = c.itens.map(function (id) { return publicados[id]; }).filter(Boolean);
      painelCaso.innerHTML =
        '<div class="flex flex-wrap items-start justify-between gap-4">' +
          '<div><p class="eyebrow">' + K.esc(c.rotulo) + '</p><h3 class="text-xl font-bold text-tinta mt-1">O que olhar primeiro</h3></div>' +
          '<div class="flex flex-wrap gap-2"><a class="og-btn og-btn-contorno og-btn-md" href="' + c.guia + '">Abrir o guia</a>' +
          '<a class="og-btn og-btn-primario og-btn-md" href="ferramentas/simulador.html' + c.sim + '">Simular este caso</a></div>' +
        '</div>' +
        (lista.length ? '<div class="lista-itens grid grid-cols-1 lg:grid-cols-3 gap-4 mt-5">' + lista.map(function (it) { return K.renderItem(it, F.porId); }).join('') + '</div>'
          : '<p class="og-cartao-texto mt-4">Os pontos deste caso aparecem aqui depois da revisão técnica.</p>');
      painelCaso.hidden = false;
      painelCaso.classList.remove('caso-painel'); void painelCaso.offsetWidth; painelCaso.classList.add('caso-painel');  // reinicia a animação
      if (dica) dica.hidden = true;
      var r = painelCaso.getBoundingClientRect();
      if (r.top > window.innerHeight - 120) painelCaso.scrollIntoView({ behavior: calmo ? 'auto' : 'smooth', block: 'start' });
    };
    cartoesCaso.forEach(function (a) {
      a.setAttribute('role', 'button');
      a.setAttribute('aria-pressed', 'false');
      a.addEventListener('click', function (ev) { ev.preventDefault(); abrirCaso(a.getAttribute('data-caso')); });
      a.addEventListener('keydown', function (ev) { if (ev.key === ' ') { ev.preventDefault(); abrirCaso(a.getAttribute('data-caso')); } });
    });
  }

  // ---------- Simulação rápida: abre o simulador já com o resultado
  var rapida = $('[data-sim-rapida]');
  if (rapida) {
    var rSetor = $('#rSetor', rapida);
    O.regras.SETORES.forEach(function (s) {
      var o = document.createElement('option'); o.value = s.id; o.textContent = s.rotuloCurto; rSetor.appendChild(o);
    });
    rapida.addEventListener('submit', function (ev) {
      var fat = $('#rFat', rapida).value.trim();
      if (!fat) return;  // sem faturamento: o formulário segue normal e abre o simulador com setor e regime
      ev.preventDefault();
      try { sessionStorage.setItem('orgatec.simulacaoRapida', JSON.stringify({ faturamento: fat })); } catch (e) { /* sem memória da aba: abre sem o valor */ }
      location.href = rapida.getAttribute('action') + '?setor=' + encodeURIComponent(rSetor.value) + '&regime=' + encodeURIComponent($('#rRegime', rapida).value);
    });
  }

  // ---------- Faixa de marcos: itens da reforma (título, status e link para a Central), rolando em laço
  var MARCOS = ['teste-2026', 'cbs-2027', 'ipi-zero-2027', 'imposto-seletivo', 'ibs-2027-2028', 'icms-iss-2029-2032', 'extincao-2033'];
  var faixa = $('[data-faixa-marcos]');
  if (faixa) {
    var noAr = {};
    K.publicaveis(O.reformaItens, F.porId, C.ambiente).itens.forEach(function (it) { noAr[it.id] = it; });
    var marcosNoAr = MARCOS.map(function (id) { return noAr[id]; }).filter(Boolean);
    if (!marcosNoAr.length) faixa.hidden = true;
    else {
      var li = function (it, copia) {
        var st = K.STATUS[it.status];
        return '<li' + (copia ? ' aria-hidden="true"' : '') + '><a href="reforma/index.html#item-' + K.esc(it.id) + '"' + (copia ? ' tabindex="-1"' : '') + '>' +
          K.esc(it.titulo) + '<span class="og-selo og-selo-' + st.tom + '">' + st.rotulo + '</span></a></li>';
      };
      // duas cópias seguidas: a animação anda metade do trilho e recomeça sem salto
      $('[data-faixa-trilho]', faixa).innerHTML = marcosNoAr.map(function (it) { return li(it, false); }).join('') +
        marcosNoAr.map(function (it) { return li(it, true); }).join('');
      var pausa = $('[data-faixa-pausa]', faixa);
      pausa.addEventListener('click', function () {
        var parada = faixa.classList.toggle('pausada');
        pausa.setAttribute('aria-pressed', String(parada));
        pausa.textContent = parada ? 'Continuar' : 'Pausar';
      });
    }
  }

  // ---------- Carrossel de ferramentas: setas rolam um cartão por vez
  var carrossel = $('[data-carrossel]');
  if (carrossel) {
    var trilho = $('[data-carrossel-trilho]', carrossel), ant = $('[data-carrossel-ant]', carrossel), prox = $('[data-carrossel-prox]', carrossel);
    var passo = function () { var c = $('.carrossel-cartao', trilho); return c ? c.getBoundingClientRect().width + 16 : 300; };
    var setas = function () {
      ant.disabled = trilho.scrollLeft <= 8;
      prox.disabled = trilho.scrollLeft + trilho.clientWidth >= trilho.scrollWidth - 8;
    };
    ant.addEventListener('click', function () { trilho.scrollBy({ left: -passo(), behavior: calmo ? 'auto' : 'smooth' }); });
    prox.addEventListener('click', function () { trilho.scrollBy({ left: passo(), behavior: calmo ? 'auto' : 'smooth' }); });
    trilho.addEventListener('scroll', setas, { passive: true });
    window.addEventListener('resize', setas);
    setas();
  }

  // ---------- Fontes oficiais: órgãos agrupados pelo endereço de cada fonte de fontes.js (contagem real)
  var ORGAOS = [
    ['Presidência da República (Planalto)', /planalto\.gov\.br/, 'Constituição, LC nº 214/2025, LC nº 227/2026 e leis federais'],
    ['Comitê Gestor do IBS', /cgibs\.gov\.br/, 'Regulamento do IBS e atos conjuntos'],
    ['Receita Federal', /receitafederal|receita\.fazenda\.gov\.br/, 'Obrigações acessórias e prazos federais'],
    ['eSocial e Ministério do Trabalho', /esocial|trabalho-e-emprego/, 'Folha e obrigações trabalhistas'],
    ['Tribunal de Contas da União', /tcu\.gov\.br/, 'Cálculo da alíquota de referência da CBS'],
    ['Senado Federal', /senado\.leg\.br/, 'Tramitação do Imposto Seletivo'],
    ['Governo de Goiás', /\.go\.gov\.br|goias\.gov\.br/, 'Incentivos e legislação estadual'],
    ['Governo do Tocantins', /\.to\.gov\.br/, 'Incentivos estaduais'],
    ['Assembleia Legislativa do Pará', /alepa\.pa\.gov\.br/, 'Legislação estadual do Pará']
  ];
  var grade = $('[data-fontes-orgaos]');
  if (grade) {
    grade.innerHTML = ORGAOS.map(function (o) {
      var n = F.lista.filter(function (f) { return f.url && o[1].test(f.url); }).length;
      if (!n) return '';
      return '<div class="og-cartao" data-orgao><span class="og-cartao-ref">' + n + (n === 1 ? ' dispositivo citado' : ' dispositivos citados') + '</span>' +
        '<h3 class="og-cartao-titulo">' + K.esc(o[0]) + '</h3><p class="og-cartao-texto">' + K.esc(o[2]) + '</p></div>';
    }).join('');
  }

  // ---------- Nome ORGATEC em holograma no topo: inclina e muda o brilho conforme o ponteiro (mouse ou dedo).
  // Leve: uma atualização por quadro, só enquanto o ponteiro está sobre o topo; nada com movimento reduzido.
  var holo = $('[data-holo-nome]');
  if (holo && !calmo) {
    var topo = holo.closest('[data-hero]'), quadro = 0, hx = 0, hy = 0;
    var mover = function () { quadro = 0; holo.style.setProperty('--hx', hx.toFixed(3)); holo.style.setProperty('--hy', hy.toFixed(3)); };
    topo.addEventListener('pointermove', function (e) {
      var r = topo.getBoundingClientRect();
      hx = Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1));
      hy = Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1));
      if (!quadro) quadro = requestAnimationFrame(mover);
    }, { passive: true });
    topo.addEventListener('pointerleave', function () { hx = 0; hy = 0; if (!quadro) quadro = requestAnimationFrame(mover); });
  }

  // ---------- Blocos surgem ao rolar (só com JS e sem movimento reduzido; sem JS tudo aparece de uma vez)
  if (!calmo && 'IntersectionObserver' in window) {
    var surgem = $$('main .og-cartao, main .numero, main .faq details').filter(function (el) { return !el.closest('[data-hero]') && !el.hasAttribute('data-caso-painel'); });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        el.classList.add('visivel');
        io.unobserve(el);
        setTimeout(function () { el.classList.remove('revelar', 'visivel'); el.style.transitionDelay = ''; }, 900);  // devolve o hover original
      });
    }, { threshold: 0.12 });
    surgem.forEach(function (el) {
      var irmaos = Array.prototype.indexOf.call(el.parentNode.children, el);
      el.style.transitionDelay = (irmaos % 4) * 70 + 'ms';
      el.classList.add('revelar');
      io.observe(el);
    });
  }
})();
