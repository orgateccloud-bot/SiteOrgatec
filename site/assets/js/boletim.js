/* Boletim de mudanças por público (compliance/boletim.html; estudo do compliance moderno, frente 3.8).
   Puro: monta, para cada público, as mudanças registradas no `historico` dos itens e a data em que cada item
   foi conferido pela última vez. Nada é inventado: só o que já está nos itens, com as fontes do próprio item.
   Em produção, conteudo.publicaveis já tira os itens sem revisão técnica. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).boletim = factory();
})(this, function () {
  'use strict';

  /* itens: lista já validada; publicos: { chave: rótulo }; desde (AAAA-MM-DD, opcional): corte das mudanças.
     Devolve [{ publico, rotulo, mudancas: [{ data, id, titulo, nota }], conferidos: [{ id, titulo, consultadoEm }] }]. */
  function montar(itens, publicos, desde) {
    return Object.keys(publicos).map(function (k) {
      var destino = 'publico-' + k;
      var doPublico = (itens || []).filter(function (it) { return (it.destinos || []).indexOf(destino) >= 0; });
      var mudancas = [];
      doPublico.forEach(function (it) {
        (it.historico || []).forEach(function (h) {
          if (!desde || h.data >= desde) mudancas.push({ data: h.data, id: it.id, titulo: it.titulo, nota: h.nota });
        });
      });
      mudancas.sort(function (a, b) { return a.data < b.data ? 1 : a.data > b.data ? -1 : 0; });
      var conferidos = doPublico.map(function (it) { return { id: it.id, titulo: it.titulo, consultadoEm: it.consultadoEm }; })
        .sort(function (a, b) { return a.consultadoEm < b.consultadoEm ? 1 : a.consultadoEm > b.consultadoEm ? -1 : 0; });
      return { publico: k, rotulo: publicos[k], mudancas: mudancas, conferidos: conferidos };
    });
  }

  return { montar: montar };
});
