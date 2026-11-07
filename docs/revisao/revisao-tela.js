/* Tela da revisão técnica: só DOM. A lógica e o hash são de revisao.js. */
(function () {
  'use strict';
  var O = window.Orgatec, R = O.revisao;
  var itens = R.pendentes(O), decisoes = {};
  var lista = document.getElementById('lista'), filtro = document.getElementById('filtro');
  document.getElementById('data').value = new Date().toISOString().slice(0, 10);
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function resumo() {
    var n = Object.keys(decisoes).length;
    document.getElementById('resumo').textContent = n + ' de ' + itens.length + ' decididos';
  }
  function desenhar() {
    lista.innerHTML = itens.filter(function (it) { return !filtro.value || it.tipo === filtro.value; }).map(function (it) {
      var d = decisoes[it.id] || {};
      return '<article class="linha" data-id="' + esc(it.id) + '"><div><span class="tipo">' + esc(it.tipo) + '</span><p>' + esc(it.titulo) + '</p>' +
        '<details><summary>Conteúdo revisado</summary><pre>' + esc(JSON.stringify(it.conteudo, null, 2)) + '</pre></details>' +
        '<textarea placeholder="Nota (obrigatória para ajustar)" data-nota>' + esc(d.nota || '') + '</textarea></div>' +
        '<div><label><input type="radio" name="d-' + esc(it.id) + '" value="aprovada"' + (d.decisao === 'aprovada' ? ' checked' : '') + '> Aprovar</label><br>' +
        '<label><input type="radio" name="d-' + esc(it.id) + '" value="ajustar"' + (d.decisao === 'ajustar' ? ' checked' : '') + '> Ajustar</label></div></article>';
    }).join('');
  }
  lista.addEventListener('change', function (e) {
    var art = e.target.closest('[data-id]'); if (!art) return;
    var id = art.getAttribute('data-id'), d = decisoes[id] || { id: id };
    if (e.target.type === 'radio') d.decisao = e.target.value;
    if (e.target.hasAttribute('data-nota')) d.nota = e.target.value;
    if (d.decisao) decisoes[id] = d;
    resumo();
  });
  filtro.addEventListener('change', desenhar);
  document.getElementById('baixar').addEventListener('click', function () {
    var lst = Object.keys(decisoes).map(function (k) { return decisoes[k]; });
    var falta = lst.filter(function (d) { return d.decisao === 'ajustar' && !d.nota; });
    if (falta.length) { alert('Escreva a nota dos itens marcados para ajustar.'); return; }
    R.registro(document.getElementById('responsavel').value.trim(), document.getElementById('data').value, lst, itens).then(function (reg) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(reg, null, 2)], { type: 'application/json' }));
      a.download = 'revisao-' + reg.data + '-' + reg.audit_hash.slice(0, 8) + '.json';
      a.click();
    }).catch(function (e) { alert(e.message); });
  });
  desenhar(); resumo();
})();
