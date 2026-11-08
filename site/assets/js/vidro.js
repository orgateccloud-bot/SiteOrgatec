/* Vitrine em vidro azul, com a logo ORGATEC em holograma ao fundo (o desenho está em vidro.css).
   Vale quando a paleta ativa é Azul flutuante escuro, a padrão do site. Se o visitante trocar a paleta em "Cores", o atributo
   data-vidro sai do <html> e a vitrine volta ao visual normal; ao voltar para a padrão, o vidro volta.
   Roda no <head>, depois do tema.js: data-vidro precisa estar no <html> antes da primeira pintura, para a página não piscar.
   Monta o fundo fixo, inclina a logo conforme o ponteiro e cuida do desempenho (veja vidro.css). Com movimento reduzido, fica parado. */
(function () {
  'use strict';
  var raiz = document.documentElement, PALETA = 'azul-fl-esc';
  var calmo = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var fundo = null;

  function montar() {
    if (fundo || !document.body) return;
    fundo = document.createElement('div');
    fundo.className = 'vidro-fundo';
    fundo.setAttribute('aria-hidden', 'true');
    fundo.innerHTML = '<div class="vidro-orbe o1"></div><div class="vidro-orbe o2"></div>' +
      '<div class="vidro-palco"><div class="vidro-orbita"></div>' +
      '<div class="vidro-logo"><span class="brilho"><i></i></span><i class="base"></i><i class="ciano"></i><i class="azul"></i><div class="vidro-varredura"><b></b></div></div></div>';
    document.body.insertBefore(fundo, document.body.firstChild);
    if (!calmo) animar();
  }

  function sincronizar() {
    if (raiz.getAttribute('data-tema') === PALETA) {
      raiz.setAttribute('data-vidro', '');
      montar();
    } else {
      raiz.removeAttribute('data-vidro');
    }
  }

  function animar() {
    // 1) Com a página rolada, a logo está atrás dos cartões: as animações desligam.
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

    // 3) Inclinação pelo ponteiro: uma atualização por quadro, e só enquanto ele se mexe (mouse ou dedo).
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

  sincronizar();
  if (window.MutationObserver) new MutationObserver(sincronizar).observe(raiz, { attributes: true, attributeFilter: ['data-tema'] });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', sincronizar);
})();
