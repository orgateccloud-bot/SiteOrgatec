/* Tela de abertura (site/index.html), no modelo do trilhum.io: texto à esquerda, direto no fundo, e a projeção
   holográfica à direita em canvas 2D — projetor, feixe e os logotipos da ORGATEC em pontos, com volume (camadas em
   profundidade) e giro em Y, em rodízio, terminando em "By Warley Veloso". Máscaras em assets/marca/holo/ (holo-logos.js,
   gerado por tools/gerar_holo_logos.py); destinos editáveis em config.abertura. Sem bibliotecas: a CSP só aceita
   scripts próprios. Movimento reduzido (preferência do sistema ou botão): quadro estático do símbolo, sem rodízio.
   Primeira visita da aba (html.abertura-intro, posta por abertura-intro.js): a projeção acende e o texto surge depois
   (abertura.css); clique, toque, tecla, rolagem ou foco pulam direto para a tela pronta. */
(function () {
  'use strict';
  var O = window.Orgatec, C = O.config, K = O.conteudo;
  var HOJE = new Date().toISOString().slice(0, 10);
  var raiz = document.documentElement;
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  // ---------- Endereços antigos da raiz (/#simulador, /?setor=agro#simulador...): a raiz agora é esta tela,
  // então cada seção que mudou de lugar leva à página própria; as da vitrine, a inicio.html
  var MUDOU = { '#simulador': 'ferramentas/simulador.html', '#calendario': 'ferramentas/calendario.html', '#contato': 'contato/index.html',
    '#regional': 'setores/regional.html', '#servicos': 'cliente/index.html', '#reforma': 'reforma/index.html', '#setores': 'setores/agro.html' };
  var VITRINE = ['#agora', '#casos', '#ultimas', '#ferramentas', '#fontes', '#perguntas', '#como-funciona'];
  if (MUDOU[location.hash]) { location.replace(MUDOU[location.hash] + location.search); return; }
  if (VITRINE.indexOf(location.hash) >= 0) { location.replace('inicio.html' + location.hash); return; }

  // ---------- Destinos (config.abertura) e WhatsApp (config.whatsapp)
  var A = C.abertura || {};
  $$('[data-destino]').forEach(function (a) { var d = A[a.getAttribute('data-destino')]; if (d) a.href = d; });
  $$('[data-link="whatsapp"]').forEach(function (a) {
    a.href = 'https://wa.me/' + C.whatsapp.numeroE164 + '?text=' + encodeURIComponent(a.getAttribute('data-msg') || '');
  });
  var faixa = $('[data-homologacao]');
  if (faixa) faixa.hidden = C.ambiente !== 'homologacao';

  // ---------- Anos de atuação: só com data e comprovação em config.institucional
  var anos = K.anosAtuacao(C.institucional, HOJE), trajetoria = $('[data-prova-anos]');
  if (trajetoria && anos) { trajetoria.textContent = anos + ' anos de atuação'; trajetoria.hidden = false; }

  // ---------- Movimento: preferência do sistema, que o botão pode trocar (lembrado no navegador)
  var CHAVE = 'orgatec.abertura.movimento';
  var lerPref = function () { try { return localStorage.getItem(CHAVE); } catch (e) { return null; } };
  var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var reduzido = lerPref() ? lerPref() === 'reduzido' : !!(mq && mq.matches);
  // Aparelho mais fraco (poucos núcleos ou pouca memória): menos camadas, menos resolução e 30 quadros/s
  var fraco = (navigator.hardwareConcurrency || 4) <= 4 || (navigator.deviceMemory || 4) <= 4;
  raiz.classList.toggle('aparelho-fraco', fraco);

  // ---------- Sequência de entrada: só na primeira visita da aba; termina sozinha depois da cascata do texto
  var intro = raiz.classList.contains('abertura-intro'), FORMACAO = fraco ? 700 : 1300;
  function pularIntro() {
    if (!intro) return;
    intro = false;
    raiz.classList.remove('abertura-intro');
    try { sessionStorage.setItem('orgatec.abertura.vista', '1'); } catch (e) { /* repete na próxima visita */ }
    ['pointerdown', 'keydown', 'wheel', 'touchstart', 'focusin'].forEach(function (ev) { window.removeEventListener(ev, pularIntro, true); });
  }
  if (intro) {
    ['pointerdown', 'keydown', 'wheel', 'touchstart', 'focusin'].forEach(function (ev) { window.addEventListener(ev, pularIntro, { capture: true, passive: true }); });
    setTimeout(pularIntro, fraco ? 1900 : 2600);  // depois do rodapé (abertura.css: --intro + 0,7 s + 0,55 s)
  }
  var botaoMov = $('[data-movimento]');
  var aplicarMovimento = function () {
    raiz.classList.toggle('movimento-reduzido', reduzido);
    if (reduzido) pularIntro();
    if (botaoMov) {
      botaoMov.setAttribute('aria-pressed', String(reduzido));
      botaoMov.textContent = reduzido ? 'Ativar animação' : 'Reduzir animação';
    }
    iniciar();
  };

  // ---------- Holograma: projetor no chão, feixe de luz e logotipo em pontos com volume, em rodízio.
  // Cada logotipo fica PERMANENCIA ms; na troca ele gira até ficar de perfil, troca nesse instante e volta (TROCA ms).
  var cv = $('[data-holo]'), ctx = cv && cv.getContext ? cv.getContext('2d') : null;
  var W = 0, H = 0, dpr = 1, cx = 0, logoY = 0, S = 0, baseY = 0, rx = 0, cores = {};
  var ponteiro = { x: 0.5, y: 0.5 }, desvio = 0, t0 = performance.now(), ultimo = 0, quadroId = 0;
  var PERMANENCIA = 5000, TROCA = 900;
  var legenda = $('[data-holo-legenda]');
  // "50 anos" só com os anos de atuação comprovados em config.institucional (mesma regra de [data-prova-anos]);
  // a assinatura fecha o rodízio e é escrita com a fonte do site, não é imagem
  var logos = (O.holoLogos || []).filter(function (lg) { return lg.exige !== 'anos50' || (anos && anos >= 50); })
    .concat([{ id: 'assinatura', nome: 'By Warley Veloso', texto: ['By', 'Warley Veloso'] }]);
  var sprites = [], atual = 0, proximo = 0, trocaDesde = -1, proximaTroca = 0;
  if (legenda) legenda.setAttribute('data-rodizio', logos.map(function (lg) { return lg.id; }).join(' '));

  // fonte de cada quadro: a máscara PNG (mesma origem, liberada pela CSP img-src 'self') ou a assinatura desenhada
  logos.forEach(function (lg, i) {
    if (lg.texto) return;
    var im = new Image();
    im.onload = function () { lg.fonte = im; lg.fw = im.naturalWidth; lg.fh = im.naturalHeight; sprites[i] = null; iniciar(); };
    im.src = lg.arquivo;
  });
  function montarAssinatura(lg) {
    var familia = (getComputedStyle(document.body).getPropertyValue('--f-display') || 'sans-serif').trim();
    var c = document.createElement('canvas'), g = c.getContext('2d');
    c.width = 900; c.height = 380;
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    g.font = '600 92px ' + familia; g.fillText(lg.texto[0], 450, 120);
    g.font = '800 132px ' + familia; g.fillText(lg.texto[1], 450, 290, 880);
    lg.fonte = c; lg.fw = c.width; lg.fh = c.height;
  }
  var assinatura = logos[logos.length - 1];
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { montarAssinatura(assinatura); sprites[logos.length - 1] = null; });
  else montarAssinatura(assinatura);

  // pontilhar: a máscara vira pontos em linhas (varredura), já na cor do tema; uma versão clara (frente) e uma
  // escura (camadas de trás). Feito uma vez por quadro do rodízio e refeito ao mudar o tamanho ou o tema.
  function pontilhar(lg) {
    if (!lg.fonte) return null;
    var escala = 2 * S / Math.max(lg.fw, lg.fh), w = Math.max(2, Math.round(lg.fw * escala * dpr)), h = Math.max(2, Math.round(lg.fh * escala * dpr));
    var tmp = document.createElement('canvas'); tmp.width = w; tmp.height = h;
    var tg = tmp.getContext('2d'); tg.drawImage(lg.fonte, 0, 0, w, h);
    var src = tg.getImageData(0, 0, w, h).data, passo = Math.max(2, Math.round(2.4 * dpr)), ponto = Math.max(1, Math.round(1.25 * dpr));
    function camada(c, forca) {
      var out = document.createElement('canvas'); out.width = w; out.height = h;
      var og = out.getContext('2d'), img = og.createImageData(w, h), d = img.data;
      for (var y = 0; y < h; y += passo) {
        var linha = (y / passo) % 3 === 0 ? 1 : 0.68;  // uma linha em três mais acesa: o efeito de varredura
        for (var x = 0; x < w; x += passo) {
          var a = src[(y * w + x) * 4 + 3];
          if (a < 28) continue;
          // borda acesa, miolo mais apagado: o contorno define a forma, como num holograma
          var borda = x < passo || y < passo || x + passo >= w || y + passo >= h ||
            src[(y * w + x - passo) * 4 + 3] < 28 || src[(y * w + x + passo) * 4 + 3] < 28 ||
            src[((y - passo) * w + x) * 4 + 3] < 28 || src[((y + passo) * w + x) * 4 + 3] < 28;
          var alfa = Math.min(255, a * linha * forca * (borda ? 1.35 : 0.62));
          for (var dy = 0; dy < ponto && y + dy < h; dy++) for (var dx = 0; dx < ponto && x + dx < w; dx++) {
            var k = ((y + dy) * w + x + dx) * 4;
            d[k] = c[0]; d[k + 1] = c[1]; d[k + 2] = c[2]; d[k + 3] = alfa;
          }
        }
      }
      og.putImageData(img, 0, 0);
      return out;
    }
    return { frente: camada(cores.a, 1.15), tras: camada(cores.b, 0.9), w: w / dpr, h: h / dpr };
  }
  function sprite(i) {
    if (!sprites[i]) sprites[i] = pontilhar(logos[i]);
    return sprites[i];
  }

  function medir() {
    if (!ctx) return;
    dpr = Math.min(window.devicePixelRatio || 1, fraco ? 1.25 : 1.75);
    W = innerWidth; H = innerHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    cv.style.width = W + 'px'; cv.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // a projeção ocupa o espaço reservado no layout (.holo-ancora): à direita do texto no desktop, acima dele no celular
    var ancora = $('[data-holo-ancora]'), r = ancora ? ancora.getBoundingClientRect() : null;
    if (!r || !r.width) r = { left: W * 0.25, top: 0, width: W * 0.5, height: H * 0.4 };
    cx = r.left + r.width / 2;  // canvas fixo: coordenadas da tela no carregamento
    // de baixo para cima: o anel de fora do projetor (1,65 × rx de largura, 0,4 × rx abaixo do centro) acaba acima
    // da legenda de baixo (no celular ela fica no alto); o logotipo ocupa o que sobra, com o feixe à mostra
    var lr = legenda ? legenda.getBoundingClientRect() : null;
    var limite = lr && lr.height && lr.top > r.top + r.height / 2 ? lr.top - 6 : r.top + r.height - 8;
    rx = Math.min(r.width * 0.34, (r.width / 2 - 14) / 1.65, r.height * 0.42);
    baseY = limite - rx * 0.4;
    var inicio = r.top + 28, livre = Math.max(40, baseY - rx * 0.35 - inicio);
    S = Math.min(r.width * 0.36, livre * 0.47);
    logoY = inicio + livre / 2;
    sprites = [];
  }

  function rgb(cor) {
    cor = (cor || '').trim();
    var m = /^#([0-9a-f]{6})$/i.exec(cor);
    if (m) { var v = parseInt(m[1], 16); return [v >> 16 & 255, v >> 8 & 255, v & 255]; }
    m = /rgba?\((\d+)[ ,]+(\d+)[ ,]+(\d+)/.exec(cor);
    return m ? [+m[1], +m[2], +m[3]] : [75, 143, 224];
  }
  function lerCores() {
    var s = getComputedStyle(document.body);
    cores = { a: rgb(s.getPropertyValue('--holo-1')), b: rgb(s.getPropertyValue('--holo-2')), c: rgb(s.getPropertyValue('--holo-3')) };
    sprites = [];
  }
  function cor(c, alfa) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + alfa + ')'; }
  function suave(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }

  function mostrarLegenda(i) {
    var lg = logos[i];
    if (!legenda || !lg) return;
    legenda.textContent = lg.nome;
    legenda.setAttribute('data-logo', lg.id);
  }

  // rodízio: a troca começa quando acaba a permanência; devolve o giro extra (0 → 90° → 0) e troca no perfil
  function rodizio(agora) {
    if (reduzido || logos.length < 2 || intro) return 0;
    if (trocaDesde < 0 && agora >= proximaTroca) { proximo = (atual + 1) % logos.length; trocaDesde = agora; }
    if (trocaDesde < 0) return 0;
    var m = Math.min(1, (agora - trocaDesde) / TROCA);
    if (m >= 0.5 && atual !== proximo) { atual = proximo; mostrarLegenda(atual); }
    if (m >= 1) { trocaDesde = -1; proximaTroca = agora + PERMANENCIA; return 0; }
    return m < 0.5 ? suave(m * 2) : 1 - suave((m - 0.5) * 2);
  }

  function desenhar(agora) {
    var t = reduzido ? 0 : (agora - t0) / 1000;
    // entrada (0 → 1): o projetor acende, o feixe sobe e a varredura revela o logotipo de baixo para cima
    var f = intro && !reduzido ? Math.min(1, (agora - t0) / FORMACAO) : 1, forma = suave(f);
    var giro = rodizio(agora);
    desvio = reduzido ? 0 : desvio + ((ponteiro.x - 0.5) * 0.5 - desvio) * 0.05;
    var lado = Math.sin(t * 0.55) >= 0 ? 1 : -1;
    var ang = reduzido ? 0.32 : Math.sin(t * 0.55) * 0.5 + desvio + lado * giro * (Math.PI / 2 - 0.2);
    var ly = logoY + (reduzido ? 0 : Math.sin(t * 1.1) * S * 0.04);
    ctx.clearRect(0, 0, W, H);

    // projetor: brilho achatado, dois contornos e dois anéis de pontos girando
    ctx.globalAlpha = Math.min(1, forma * 1.6);
    var ry = rx * 0.24, gl = ctx.createRadialGradient(cx, baseY, 0, cx, baseY, rx * 1.1);
    gl.addColorStop(0, cor(cores.a, 0.85)); gl.addColorStop(0.18, cor(cores.a, 0.35)); gl.addColorStop(1, cor(cores.b, 0));
    ctx.save(); ctx.translate(cx, baseY); ctx.scale(1, 0.24); ctx.translate(-cx, -baseY);
    ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(cx, baseY, rx * 1.1, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = cor(cores.a, 0.55);
    ctx.beginPath(); ctx.ellipse(cx, baseY, rx * 0.62, ry * 0.62, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = cor(cores.b, 0.3);
    ctx.beginPath(); ctx.ellipse(cx, baseY, rx * 0.9, ry * 0.9, 0, 0, Math.PI * 2); ctx.stroke();
    [[1.25, 54, 0.12], [1.65, 72, -0.08]].forEach(function (anel) {
      for (var k = 0; k < anel[1]; k++) {
        var a = k / anel[1] * Math.PI * 2 + t * anel[2], frente = (Math.sin(a) + 1) / 2;
        ctx.fillStyle = cor(cores.a, 0.15 + 0.55 * frente);
        ctx.fillRect(cx + Math.cos(a) * rx * anel[0] - 1, baseY + Math.sin(a) * ry * anel[0] - 1, 2, 2);
      }
    });

    // feixe: cone estreito no projetor e largo no logotipo, com uma faixa de varredura subindo
    var topo = ly - S * 0.2, larg = S * 1.05, bocal = rx * 0.32;
    var fe = ctx.createLinearGradient(0, baseY, 0, topo);
    fe.addColorStop(0, cor(cores.a, 0.5)); fe.addColorStop(0.55, cor(cores.b, 0.16)); fe.addColorStop(1, cor(cores.b, 0));
    ctx.globalAlpha = forma;
    ctx.fillStyle = fe;
    ctx.beginPath(); ctx.moveTo(cx - bocal, baseY); ctx.lineTo(cx - larg, topo); ctx.lineTo(cx + larg, topo); ctx.lineTo(cx + bocal, baseY); ctx.closePath(); ctx.fill();
    if (!reduzido) {
      var sv = (t * 0.35) % 1, vy = baseY + (topo - baseY) * sv, vw = bocal + (larg - bocal) * sv;
      ctx.strokeStyle = cor(cores.a, 0.35 * (1 - sv)); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx - vw, vy); ctx.lineTo(cx + vw, vy); ctx.stroke();
    }

    // logotipo com volume: o mesmo desenho em camadas de trás para a frente; a largura segue cos(giro) e cada camada
    // se desloca sin(giro) × profundidade, o que mostra a lateral quando ele gira
    var sp = sprite(atual);
    if (sp) {
      var camadas = fraco ? 4 : 8, prof = S * 0.3, ca = Math.cos(ang), sa = Math.sin(ang);
      var pisca = giro > 0 ? 0.75 + 0.25 * Math.abs(Math.sin(t * 47)) : 1;
      ctx.save();
      if (forma < 1) { ctx.beginPath(); ctx.rect(0, ly + sp.h / 2 - sp.h * forma, W, sp.h * forma + 2); ctx.clip(); }
      for (var j = camadas - 1; j >= 0; j--) {
        var z = (j / (camadas - 1) - 0.5) * prof, frenteCamada = j === 0;
        ctx.globalAlpha = forma * pisca * (frenteCamada ? 1 : 0.28 + 0.4 * (1 - j / (camadas - 1)));
        ctx.globalCompositeOperation = frenteCamada ? 'lighter' : 'source-over';
        ctx.setTransform(dpr * ca, 0, 0, dpr, dpr * (cx + sa * z), dpr * ly);
        ctx.drawImage(frenteCamada ? sp.frente : sp.tras, -sp.w / 2, -sp.h / 2, sp.w, sp.h);
      }
      ctx.restore();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = 'source-over';
    }
    ctx.globalAlpha = 1;
  }

  function laco(agora) {
    quadroId = requestAnimationFrame(laco);
    if (fraco && agora - ultimo < 32) return;  // ~30 quadros/s em aparelho fraco
    ultimo = agora;
    desenhar(agora);
  }
  function iniciar() {
    if (!ctx) return;
    cancelAnimationFrame(quadroId);
    if (reduzido || document.hidden) desenhar(performance.now());
    else quadroId = requestAnimationFrame(laco);
  }

  // ---------- Ponteiro: o logotipo vira um pouco para o lado do mouse
  window.addEventListener('pointermove', function (ev) { ponteiro.x = ev.clientX / (W || innerWidth); ponteiro.y = ev.clientY / (H || innerHeight); }, { passive: true });
  document.addEventListener('pointerleave', function () { ponteiro.x = 0.5; ponteiro.y = 0.5; });

  // ---------- Botão de entrada sempre ao alcance: cópia fixa aparece quando o original sai da tela
  var entrar = $('[data-entrar]:not([data-entrar-fixo])'), fixo = $('[data-entrar-fixo]');
  if (entrar && fixo && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      var fora = !es[0].isIntersecting;
      fixo.classList.toggle('visivel', fora);
      fixo.setAttribute('aria-hidden', String(!fora));
      fixo.tabIndex = fora ? 0 : -1;
    }).observe(entrar);
  }
  // Saída: o palco se aproxima e some antes de abrir o site (sem animação, abre na hora)
  $$('[data-entrar]').forEach(function (a) {
    a.addEventListener('click', function (ev) {
      if (reduzido || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button) return;
      ev.preventDefault();
      raiz.classList.add('saindo');
      setTimeout(function () { location.href = a.href; }, 420);
    });
  });
  window.addEventListener('pageshow', function () { raiz.classList.remove('saindo'); });  // voltar pelo histórico

  // ---------- Início
  if (botaoMov) botaoMov.addEventListener('click', function () {
    reduzido = !reduzido;
    try { localStorage.setItem(CHAVE, reduzido ? 'reduzido' : 'normal'); } catch (e) { /* preferência só nesta visita */ }
    aplicarMovimento();
  });
  if (mq && mq.addEventListener) mq.addEventListener('change', function (e) { if (!lerPref()) { reduzido = e.matches; aplicarMovimento(); } });
  document.addEventListener('visibilitychange', iniciar);
  var redimensionar = 0;
  window.addEventListener('resize', function () {
    clearTimeout(redimensionar);
    redimensionar = setTimeout(function () { medir(); iniciar(); }, 120);
  });
  if (window.MutationObserver) new MutationObserver(function () { lerCores(); iniciar(); }).observe(raiz, { attributes: true, attributeFilter: ['data-tema'] });
  medir(); lerCores(); mostrarLegenda(0);
  proximaTroca = performance.now() + (intro ? FORMACAO : 0) + PERMANENCIA;
  aplicarMovimento();
})();
