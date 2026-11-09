/* Janela Empresarial e do Transporte (empresarial/janela.html). Lê /dados/empresarial/atual.json, do próprio site
   (connect-src 'self'), gerado por tools/gerar_janela_empresarial.py. Regras: todo cartão mostra fonte, horário da coleta e
   estado (ok, atrasado, indisponível); cartão fora da validade vira "atrasado" com o carimbo; indisponível nunca mostra valor. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).janelaEmpresarial = factory();
})(this, function () {
  'use strict';
  var ROTULO = { ok: 'Em dia', atrasado: 'Atrasado', indisponivel: 'Indisponível' };
  var TRANSPORTE = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'];

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function dataBR(iso) { var p = String(iso).slice(0, 10).split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : esc(iso); }
  function horaBR(iso) { return iso ? dataBR(iso) + ' ' + String(iso).slice(11, 16) : ''; }

  /* Estado efetivo no navegador: ok vira atrasado quando a coleta passou da validade (ou a data é ilegível). */
  function estadoEfetivo(c, agora) {
    if (c.estado === 'indisponivel' || !c.coletadoEm) return 'indisponivel';
    var t = Date.parse(c.coletadoEm);
    if (isNaN(t)) return 'atrasado';
    return (agora.getTime() - t) / 3600000 > c.validadeHoras ? 'atrasado' : c.estado;
  }

  function lista(itens, vazio) {
    if (!itens.length) return '<p class="og-cartao-texto">' + vazio + '</p>';
    return '<ul class="og-lista">' + itens.map(function (i) { return '<li>' + i + '</li>'; }).join('') + '</ul>';
  }

  function corpoCartao(c, perfil) {
    var d = c.dados || {};
    if (c.id === 'E1' || c.id === 'T4') {
      var prazos = (d.porPerfil && d.porPerfil[perfil]) || [];
      return lista(prazos.map(function (p) { return '<strong>' + dataBR(p.data) + '</strong> ' + esc(p.titulo) + (p.aConfirmar ? ' <em>(data a confirmar)</em>' : ''); }),
        'Nenhum prazo nos próximos 7 dias para este perfil.');
    }
    if (c.id === 'E4') {
      return lista((d.itens || []).map(function (i) { return '<strong>' + dataBR(i.data) + '</strong> ' + esc(i.titulo) + ': ' + esc(i.nota); }),
        'Nenhuma mudança registrada nos itens da reforma nos últimos 7 dias.');
    }
    if (c.id === 'T1') {
      return '<p class="og-cartao-texto">' + esc(d.resolucao) + ', publicada em ' + dataBR(d.publicadaEm) + ', vigência em ' + dataBR(d.vigenciaEm) +
        '. Revisado por ' + esc(d.revisadoPor) + ' em ' + dataBR(d.revisadoEm) + '.</p>';
    }
    return '<p class="og-cartao-texto">' + esc(JSON.stringify(d)) + '</p>';
  }

  function htmlCartao(c, perfil, agora) {
    var est = estadoEfetivo(c, agora);
    var carimbo = c.coletadoEm ? 'Coletado em ' + horaBR(c.coletadoEm) : 'Sem coleta';
    var corpo = est === 'indisponivel'
      ? '<p class="og-cartao-texto">' + esc(c.motivo || 'Fonte indisponível no momento.') + '</p>'
      : (est === 'atrasado' ? '<p class="og-cartao-texto"><strong>Atrasado:</strong> este dado é de ' + horaBR(c.coletadoEm) + ' e pode não estar mais valendo.</p>' : '') + corpoCartao(c, perfil);
    return '<article class="og-cartao" data-cartao="' + esc(c.id) + '" data-estado="' + est + '"><span class="og-cartao-ref">' + esc(c.modulo) + ' · ' + ROTULO[est] + '</span>' +
      corpo + '<p class="text-xs text-tinta-fraca">Fonte: ' + esc(c.fonte) + '. ' + carimbo + '.</p></article>';
  }

  /* atividade 'transportador' mostra também os cartões do transporte; as demais, só os empresariais. */
  function renderizar(janela, opcoes, agora) {
    var perfil = (opcoes.regime || 'real') + '-' + (opcoes.uf || 'GO');
    var cartoes = janela.cartoes.filter(function (c) { return opcoes.atividade === 'transportador' || TRANSPORTE.indexOf(c.id) < 0; });
    var cab = '<p class="text-sm text-tinta-fraca">Gerado em ' + horaBR(janela.geradoEm) + '. Próxima atualização: ' + esc(janela.proximaAtualizacao) + '.</p>';
    return cab + '<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">' + cartoes.map(function (c) { return htmlCartao(c, perfil, agora); }).join('') + '</div>' +
      '<p class="text-sm text-tinta-fraca mt-4">' + esc(janela.aviso) + '</p>';
  }

  function iniciar() {
    var raiz = document.querySelector('[data-janela-empresarial]');
    if (!raiz) return;
    var alvo = raiz.querySelector('[data-janela-lista]'), estado = { atividade: '', regime: 'real', uf: 'GO' }, janela = null;
    function desenhar() { if (janela) alvo.innerHTML = renderizar(janela, estado, new Date()); }
    document.querySelectorAll('[data-filtro-janela]').forEach(function (s) {
      s.addEventListener('change', function () { estado[s.getAttribute('data-filtro-janela')] = s.value; desenhar(); });
    });
    fetch(raiz.getAttribute('data-origem'), { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) { janela = j; desenhar(); })
      .catch(function () { alvo.innerHTML = '<p class="og-cartao-texto">A janela está indisponível no momento. Nenhum dado antigo é exibido; fale com o escritório.</p>'; });
  }
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
  }
  return { estadoEfetivo: estadoEfetivo, renderizar: renderizar };
});
