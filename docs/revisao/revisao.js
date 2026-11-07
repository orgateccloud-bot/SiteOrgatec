/* Revisão técnica (onda 3 do compliance moderno). Ferramenta local, fora do site: abre no navegador a partir de docs/.
   Lista o que espera o responsável técnico (pontos da reforma e do compliance, perguntas do termômetro, camadas e
   pesos por perfil). Cada decisão fica presa ao texto revisado pelo hash SHA-256 do conteúdo, e o registro inteiro
   ganha um audit_hash. Nada sai do navegador: o registro é baixado como JSON e conferido com tools/conferir_revisao.py. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).revisao = factory();
})(this, function () {
  'use strict';

  /* JSON canônico: chaves em ordem, sem espaços. Igual a json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False). */
  function canonico(v) {
    if (v === null || typeof v !== 'object') return JSON.stringify(v);
    if (Array.isArray(v)) return '[' + v.map(canonico).join(',') + ']';
    return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + canonico(v[k]); }).join(',') + '}';
  }

  /* O que vai à revisão: [{ id, tipo, titulo, conteudo }], com `conteudo` = o texto que o responsável aprova. */
  function pendentes(O) {
    var lista = [];
    (O.reformaItens || []).concat(O.complianceItens || []).forEach(function (it) {
      if (it.revisao && it.revisao.status === 'aprovada') return;
      lista.push({ id: 'item:' + it.id, tipo: 'Ponto', titulo: it.titulo,
        conteudo: { fato: it.fato, orientacao: it.orientacao || '', fontes: it.fontes, status: it.status } });
    });
    var T = O.termometro;
    if (T && T.REVISAO.status !== 'aprovada') {
      T.PERGUNTAS.forEach(function (p) {
        lista.push({ id: 'pergunta:' + p.id, tipo: 'Pergunta', titulo: p.texto,
          conteudo: { texto: p.texto, corrigir: p.corrigir, peso: p.peso, fontes: p.fontes, camadas: T.CAMADAS[p.id] || null } });
      });
    }
    if (T && T.PESOS_PERFIL && T.PESOS_PERFIL.status !== 'aprovada') {
      Object.keys(T.PESOS_PERFIL.ajustes).forEach(function (perfil) {
        Object.keys(T.PESOS_PERFIL.ajustes[perfil]).forEach(function (id) {
          var a = T.PESOS_PERFIL.ajustes[perfil][id];
          lista.push({ id: 'peso:' + perfil + ':' + id, tipo: 'Peso por perfil', titulo: perfil + ' · ' + id + ' → peso ' + a.peso,
            conteudo: a });
        });
      });
    }
    return lista;
  }

  /* hash(texto) → Promise<hex>. No navegador usa crypto.subtle; nos testes, o crypto do Node. */
  function sha256(texto) {
    var g = typeof globalThis !== 'undefined' ? globalThis : {};
    if (g.crypto && g.crypto.subtle) {
      return g.crypto.subtle.digest('SHA-256', new TextEncoder().encode(texto)).then(function (b) {
        return Array.prototype.map.call(new Uint8Array(b), function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
      });
    }
    return Promise.resolve(require('crypto').createHash('sha256').update(texto, 'utf8').digest('hex'));
  }

  /* decisoes: [{ id, decisao: 'aprovada'|'ajustar', nota }]; itens: saída de pendentes().
     Devolve Promise<registro> com conteudoHash em cada decisão e audit_hash do registro sem ele. */
  function registro(responsavel, data, decisoes, itens) {
    var porId = {};
    itens.forEach(function (it) { porId[it.id] = it; });
    return Promise.all(decisoes.map(function (d) {
      if (!porId[d.id]) return Promise.reject(new Error('decisão sem item: ' + d.id));
      if (d.decisao !== 'aprovada' && d.decisao !== 'ajustar') return Promise.reject(new Error('decisão inválida: ' + d.id));
      return sha256(canonico(porId[d.id].conteudo)).then(function (h) {
        return { id: d.id, tipo: porId[d.id].tipo, decisao: d.decisao, nota: d.nota || '', conteudoHash: h };
      });
    })).then(function (lista) {
      var corpo = { versao: 1, responsavel: responsavel, data: data, decisoes: lista };
      if (!responsavel || !/^\d{4}-\d{2}-\d{2}$/.test(data || '')) throw new Error('responsável e data são obrigatórios');
      return sha256(canonico(corpo)).then(function (h) { corpo.audit_hash = h; return corpo; });
    });
  }

  return { canonico: canonico, pendentes: pendentes, registro: registro, sha256: sha256 };
});
