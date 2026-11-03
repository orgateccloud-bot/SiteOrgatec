/* Tela de abertura: carregado no <head>, antes da primeira pintura. Na primeira visita da aba, com animação,
   marca html.abertura-intro para o holograma se formar antes de o cartão surgir (abertura.css e abertura.js).
   Movimento reduzido (sistema ou botão) ou abertura já vista na aba: nada muda e a tela abre pronta. */
(function () {
  'use strict';
  try {
    var pref = localStorage.getItem('orgatec.abertura.movimento');
    var reduzido = pref ? pref === 'reduzido' : !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    if (!reduzido && !sessionStorage.getItem('orgatec.abertura.vista')) document.documentElement.classList.add('abertura-intro');
  } catch (e) { /* sem armazenamento do navegador: abre pronta */ }
})();
