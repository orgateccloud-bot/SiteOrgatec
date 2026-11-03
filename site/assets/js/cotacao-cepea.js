/* Roda dentro de site/cotacoes/*.html (iframe com sandbox="allow-scripts", origem opaca), logo depois do
   script oficial do CEPEA. Não lê nem copia os valores: só avisa a página que o abriu se a tabela do widget
   apareceu e qual altura ela ocupa, e faz o link do CEPEA abrir em outra aba (dentro do card ele não cabe). */
(function () {
  'use strict';
  var tabela = document.querySelector('.imagenet-widget-tabela') || document.querySelector('table');
  var ok = !!(tabela && tabela.querySelectorAll('tr').length > 2);
  Array.prototype.forEach.call(document.querySelectorAll('a[href]'), function (a) { a.target = '_blank'; a.rel = 'noopener'; });
  function avisar() {
    parent.postMessage({ tipo: 'orgatec-widget-cepea', atividade: document.body.getAttribute('data-atividade'), ok: ok,
      altura: Math.ceil(document.documentElement.scrollHeight) }, '*');
  }
  avisar();
  window.addEventListener('load', avisar);
  if (window.ResizeObserver) new ResizeObserver(avisar).observe(document.body);
})();
