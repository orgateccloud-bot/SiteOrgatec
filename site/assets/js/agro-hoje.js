/* Resumo do dia na página Agro: lê o boletim publicado da Janela de Campo (mesma origem) e mostra o estado das 5 operações
   na região escolhida. A região é a mesma da Janela (chave orgatec.campo, só neste navegador). Sem boletim válido ou com ele
   desatualizado, fica o texto fixo com o link da Janela, sem número nenhum. */
(function () {
  'use strict';
  var alvo = document.querySelector('[data-agro-hoje]');
  var C = window.Orgatec && window.Orgatec.campo;
  if (!alvo || !C) return;
  var corpo = alvo.querySelector('[data-agro-hoje-corpo]'), titulo = alvo.querySelector('[data-agro-hoje-regiao]');
  var BASE = alvo.getAttribute('data-campo-dados') || '../dados/campo/';
  var HOJE = new Date(Date.now() - 3 * 3600000).toISOString().slice(0, 10);  // dia em Brasília
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };

  function pref() { try { return JSON.parse(localStorage.getItem('orgatec.campo') || '{}') || {}; } catch (e) { return {}; } }
  function gravarRegiao(id) {
    var p = pref(); p.r = id; p.p = null;  // a Janela escolhe o primeiro polo da região
    try { localStorage.setItem('orgatec.campo', JSON.stringify(p)); } catch (e) { /* sem memória: só nesta visita */ }
  }
  function selo(s) {
    var e = C.ESTADOS[s];
    return e ? '<span class="campo-selo campo-' + s + '"><i aria-hidden="true">' + e.icone + '</i>' + esc(e.rotulo) + '</span>' : '';
  }

  fetch(BASE + 'atual.json', { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); }).then(function (b) {
    if (C.validar(b).length || !b.automatico) return;
    var horas = C.horasDesde(b, Date.now());
    if (C.situacao(b, HOJE) !== 'vigente' || (horas != null && horas > C.LIMITE_HORAS)) return;
    var escolhida = pref().r, r = b.regioes.filter(function (x) { return x.id === escolhida; })[0] || b.regioes[0];
    var hora = b.geradoEm ? b.geradoEm.slice(11, 16).replace(':', 'h') : '';
    corpo.innerHTML =
      '<div class="og-campo max-w-xs"><label class="og-campo-rotulo" for="agroHojeRegiao">Região</label>' +
        '<select id="agroHojeRegiao" class="og-campo-controle og-campo-md">' + b.regioes.map(function (x) { return '<option value="' + esc(x.id) + '"' + (x.id === r.id ? ' selected' : '') + '>' + esc(x.nome) + '</option>'; }).join('') + '</select></div>' +
      '<ul class="campo-hoje-mini" data-agro-hoje-lista></ul>' +
      '<p class="text-sm text-tinta-suave">Boletim de ' + esc(C.dataCurta(b.dia)) + (hora ? ', atualizado às ' + esc(hora) : '') + '.</p>';
    function desenhar(x) {
      titulo.textContent = x.nome;
      corpo.querySelector('[data-agro-hoje-lista]').innerHTML = C.OPERACOES.map(function (o) {
        return '<li><span>' + esc(o.nome) + '</span>' + selo(x.ops[o.id][0]) + '</li>';
      }).join('');
    }
    desenhar(r);
    corpo.querySelector('select').addEventListener('change', function (ev) {
      var x = b.regioes.filter(function (y) { return y.id === ev.target.value; })[0];
      if (x) { gravarRegiao(x.id); desenhar(x); }
    });
  }).catch(function () { /* fica o texto fixo */ });
})();
