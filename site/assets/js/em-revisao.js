/* Páginas em revisão técnica: em produção, o conteúdo marcado com [data-em-revisao] dá lugar a um aviso.
   Usado pelas páginas da onda 2 do compliance moderno até o responsável técnico aprovar o texto. */
(function () {
  'use strict';
  var C = (window.Orgatec || {}).config || {};
  if (C.ambiente !== 'producao') return;
  Array.prototype.forEach.call(document.querySelectorAll('[data-em-revisao]'), function (el) {
    el.innerHTML = '<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><p class="og-cartao-texto">Esta página está em revisão técnica e volta em breve. Enquanto isso, fale com o escritório.</p></div>';
  });
})();
