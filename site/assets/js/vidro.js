/* Modelos de vidro azul da vitrine (ideia/vidro-azul). Ativa só com ?vidro=a ou ?vidro=b; sem o parâmetro não faz nada.
   Roda no <head>: o atributo data-vidro precisa estar no <html> antes da primeira pintura, para a página não piscar.
   Monta o fundo fixo com a logo em holograma (o desenho está em vidro.css) e inclina a logo conforme o ponteiro.
   Com movimento reduzido, o holograma fica parado. */
(function () {
  'use strict';
  var raiz = document.documentElement, modelo = '';
  try { modelo = (new URLSearchParams(window.location.search).get('vidro') || '').toLowerCase(); } catch (e) { modelo = ''; }
  if (modelo !== 'a' && modelo !== 'b') return;
  raiz.setAttribute('data-vidro', modelo);

  // Os dois modelos partem da paleta Azul flutuante escuro; um tema salvo no navegador não pode mudar o resultado.
  function paleta() {
    try { if (window.Orgatec && window.Orgatec.tema) window.Orgatec.tema.aplicar('azul-fl-esc'); } catch (e) { /* segue com a paleta atual */ }
  }
  paleta();

  var calmo = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  function montar() {
    paleta();
    if (document.querySelector('.vidro-fundo')) return;
    var fundo = document.createElement('div');
    fundo.className = 'vidro-fundo';
    fundo.setAttribute('aria-hidden', 'true');
    fundo.innerHTML = '<div class="vidro-orbe o1"></div><div class="vidro-orbe o2"></div>' +
      '<div class="vidro-palco"><div class="vidro-feixe"></div><div class="vidro-aneis"><i></i><i></i></div><div class="vidro-orbita"></div>' +
      '<div class="vidro-logo"><span class="brilho"><i></i></span><i class="base"></i><i class="ciano"></i><i class="azul"></i><div class="vidro-varredura"><b></b></div></div></div>';
    document.body.insertBefore(fundo, document.body.firstChild);

    // Chave para comparar com a página original e entre os modelos (prévia: sai quando um modelo for escolhido)
    var caminho = window.location.pathname;
    var troca = document.createElement('nav');
    troca.className = 'vidro-troca';
    troca.setAttribute('aria-label', 'Modelos de vidro');
    troca.innerHTML = '<span>Modelo</span><a href="' + caminho + '">Original</a>' +
      '<a href="' + caminho + '?vidro=a"' + (modelo === 'a' ? ' aria-current="true"' : '') + '>A</a>' +
      '<a href="' + caminho + '?vidro=b"' + (modelo === 'b' ? ' aria-current="true"' : '') + '>B</a>';
    document.body.appendChild(troca);
    if (calmo) return;

    // Desempenho. O vidro é barato; o que pesa é o fundo mudar a cada quadro, porque todo cartão refaz o desfoque.
    // 1) Com a página rolada, a logo está atrás dos cartões: as animações pausam.
    var pausado = false, rolando = 0;
    function conferirRolagem() {
      rolando = 0;
      var pausar = window.scrollY > window.innerHeight * 0.5;
      if (pausar !== pausado) { pausado = pausar; raiz.classList.toggle('vidro-pausa', pausar); }
    }
    window.addEventListener('scroll', function () { if (!rolando) rolando = window.requestAnimationFrame(conferirRolagem); }, { passive: true });
    conferirRolagem();

    // 2) Aparelho lento: mede o tempo de quadro com tudo animado e, se ficar abaixo de cerca de 30 quadros por segundo
    //    duas vezes seguidas, desliga as animações (a inclinação pelo ponteiro continua).
    function sonda(ms, depois) {
      var t0 = window.performance.now(), ultimo = t0, quadros = [];
      function passo(t) {
        quadros.push(t - ultimo); ultimo = t;
        if (t - t0 < ms) { window.requestAnimationFrame(passo); return; }
        quadros.shift(); quadros.sort(function (a, b) { return a - b; });
        depois(quadros[Math.floor(quadros.length / 2)]);
      }
      window.requestAnimationFrame(passo);
    }
    function conferirAparelho(vez) {
      if (window.__vidroSemSonda || raiz.classList.contains('vidro-leve') || pausado) return;
      sonda(1500, function (mediana) {
        if (mediana <= 34) return;
        if (vez >= 2) raiz.classList.add('vidro-leve'); else conferirAparelho(vez + 1);
      });
    }
    window.setTimeout(function () { conferirAparelho(1); }, 1500);

    // Uma atualização por quadro, e só enquanto o ponteiro se mexe (mouse ou dedo).
    var quadro = 0, hx = 0, hy = 0;
    function desenhar() {
      quadro = 0;
      fundo.style.setProperty('--hx', hx.toFixed(3));
      fundo.style.setProperty('--hy', hy.toFixed(3));
    }
    window.addEventListener('pointermove', function (e) {
      hx = (e.clientX / window.innerWidth) * 2 - 1;
      hy = (e.clientY / window.innerHeight) * 2 - 1;
      if (!quadro) quadro = window.requestAnimationFrame(desenhar);
    }, { passive: true });
    document.addEventListener('pointerleave', function () {
      hx = 0; hy = 0;
      if (!quadro) quadro = window.requestAnimationFrame(desenhar);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', montar); else montar();
})();
