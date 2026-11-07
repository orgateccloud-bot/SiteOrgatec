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
      '<div class="vidro-logo"><i class="base"></i><i class="ciano"></i><i class="azul"></i><div class="vidro-varredura"><b></b></div></div></div>';
    document.body.insertBefore(fundo, document.body.firstChild);
    if (calmo) return;

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
