/* @ds-bundle: {"format": 4, "namespace": "OrgatecUI", "components": [{"name": "Assinatura"}, {"name": "Botao"}, {"name": "Selo"}, {"name": "CitacaoFonte"}, {"name": "CartaoHub"}, {"name": "Campo"}, {"name": "Consentimento"}]} */
(function () {
  var React = window.React, h = React.createElement;
  var SIMBOLO = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 314 347\" role=\"img\" aria-label=\"ORGATEC\"><title>ORGATEC</title><defs><clipPath id=\"o-clip\"><ellipse cx=\"160.0\" cy=\"172.2\" rx=\"160.0\" ry=\"168.8\" transform=\"rotate(8.08 160.0 172.2)\"/></clipPath><linearGradient id=\"o-navy\" gradientUnits=\"userSpaceOnUse\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"347\"><stop offset=\"0\" stop-color=\"#2F5591\"/><stop offset=\"0.3\" stop-color=\"#244A86\"/><stop offset=\"0.45\" stop-color=\"#183873\"/><stop offset=\"0.6\" stop-color=\"#072563\"/><stop offset=\"1\" stop-color=\"#021D5C\"/></linearGradient><linearGradient id=\"o-azul\" gradientUnits=\"userSpaceOnUse\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"347\"><stop offset=\"0\" stop-color=\"#4A81BA\"/><stop offset=\"0.15\" stop-color=\"#4A81BA\"/><stop offset=\"0.4\" stop-color=\"#3466A3\"/><stop offset=\"0.6\" stop-color=\"#214C90\"/><stop offset=\"1\" stop-color=\"#1E4B8E\"/></linearGradient><linearGradient id=\"o-medio\" gradientUnits=\"userSpaceOnUse\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"347\"><stop offset=\"0\" stop-color=\"#1984C8\"/><stop offset=\"0.26\" stop-color=\"#3BA7D6\"/><stop offset=\"0.43\" stop-color=\"#2690CC\"/><stop offset=\"0.55\" stop-color=\"#167DBF\"/><stop offset=\"0.66\" stop-color=\"#0A70B8\"/><stop offset=\"1\" stop-color=\"#096FB7\"/></linearGradient><linearGradient id=\"o-ciano\" gradientUnits=\"userSpaceOnUse\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"347\"><stop offset=\"0\" stop-color=\"#03AEE4\"/><stop offset=\"0.26\" stop-color=\"#02C9F0\"/><stop offset=\"0.43\" stop-color=\"#03DEFA\"/><stop offset=\"0.55\" stop-color=\"#06CAF2\"/><stop offset=\"0.72\" stop-color=\"#04AEE1\"/><stop offset=\"1\" stop-color=\"#03A8DE\"/></linearGradient></defs><g clip-path=\"url(#o-clip)\"><path d=\"M-60,-30.0 L-60,377.0 L96.43,377.00 Q-1.09,173.50 46.66,-30.00 Z\" fill=\"url(#o-navy)\"/><path d=\"M75.38,-30.00 Q-9.09,173.50 130.73,377.00 L159.19,377.00 Q81.62,173.50 108.74,-30.00 Z\" fill=\"url(#o-azul)\"/><path d=\"M161.53,-30.00 Q70.99,173.50 201.08,377.00 L229.35,377.00 Q201.08,173.50 196.17,-30.00 Z\" fill=\"url(#o-medio)\"/><path d=\"M268.66,-30.00 Q192.84,173.50 251.36,377.00 L374,377.0 L374,-30.0 Z\" fill=\"url(#o-ciano)\"/></g></svg>", SIMBOLO_BRANCO = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 314 347\" role=\"img\" aria-label=\"ORGATEC\"><title>ORGATEC</title><defs><clipPath id=\"b-clip\"><ellipse cx=\"160.0\" cy=\"172.2\" rx=\"160.0\" ry=\"168.8\" transform=\"rotate(8.08 160.0 172.2)\"/></clipPath></defs><g clip-path=\"url(#b-clip)\"><path d=\"M-60,-30.0 L-60,377.0 L96.43,377.00 Q-1.09,173.50 46.66,-30.00 Z\" fill=\"#FFFFFF\"/><path d=\"M75.38,-30.00 Q-9.09,173.50 130.73,377.00 L159.19,377.00 Q81.62,173.50 108.74,-30.00 Z\" fill=\"#FFFFFF\"/><path d=\"M161.53,-30.00 Q70.99,173.50 201.08,377.00 L229.35,377.00 Q201.08,173.50 196.17,-30.00 Z\" fill=\"#FFFFFF\"/><path d=\"M268.66,-30.00 Q192.84,173.50 251.36,377.00 L374,377.0 L374,-30.0 Z\" fill=\"#FFFFFF\"/></g></svg>";
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }

  function Simbolo(p) {
    return h('span', { className: cx('og-simbolo', p.className), 'aria-hidden': 'true', style: { height: p.altura, width: p.altura * 314 / 347 },
      dangerouslySetInnerHTML: { __html: p.branco ? SIMBOLO_BRANCO : SIMBOLO } });
  }

  function Assinatura(p) {
    var variante = p.variante || 'horizontal', tom = p.tom || 'claro';
    var descritor = p.descritor !== false && variante !== 'reduzida';
    var alt = { horizontal: 64, vertical: 80, reduzida: 32 }[variante];
    return h('span', { className: cx('og-assinatura', 'og-assinatura-' + variante, 'og-tom-' + tom, p.className), role: 'img', 'aria-label': 'ORGATEC' },
      h(Simbolo, { altura: p.altura || alt, branco: tom === 'escuro' }),
      h('span', { className: 'og-assinatura-texto' },
        h('span', { className: 'og-nome' }, 'ORGATEC'),
        descritor ? h('span', { className: 'og-descritor' }, 'Inteligência Tributária') : null));
  }

  function Botao(p) {
    var r = Object.assign({}, p); delete r.variante; delete r.tamanho; delete r.className; delete r.children;
    var cls = cx('og-btn', 'og-btn-' + (p.variante || 'primario'), 'og-btn-' + (p.tamanho || 'md'), p.className);
    if (p.href) { if (/^https?:/.test(p.href)) { r.target = r.target || '_blank'; r.rel = r.rel || 'noopener'; } return h('a', Object.assign(r, { className: cls }), p.children); }
    return h('button', Object.assign({ type: 'button' }, r, { className: cls }), p.children);
  }

  var TEXTO_SELO = { pendente: 'pendente de validação', definido: 'definido', futuro: 'vigência futura', norma: '' };
  function Selo(p) {
    var tom = p.tom || 'pendente';
    return h('span', { className: cx('og-selo', 'og-selo-' + tom, p.className) }, p.children || TEXTO_SELO[tom]);
  }

  function CitacaoFonte(p) {
    return h('span', { className: cx('og-citacao', p.className) },
      p.url ? h('a', { href: p.url, target: '_blank', rel: 'noopener', className: 'og-link' }, p.rotulo) : h('span', null, p.rotulo),
      p.validado ? null : h(Selo, { tom: 'pendente' }));
  }

  function CartaoHub(p) {
    return h(p.href ? 'a' : 'div', { href: p.href, className: cx('og-cartao', p.className) },
      p.referencia ? h('span', { className: 'og-cartao-ref' }, p.referencia) : null,
      h('h3', { className: 'og-cartao-titulo' }, p.titulo, p.pendente ? h(Selo, { tom: 'pendente' }) : null),
      p.children ? h('p', { className: 'og-cartao-texto' }, p.children) : null);
  }

  function Campo(p) {
    var r = Object.assign({}, p); ['rotulo', 'ajuda', 'erro', 'tamanho', 'opcoes', 'className'].forEach(function (k) { delete r[k]; });
    var cls = cx('og-campo-controle', 'og-campo-' + (p.tamanho || 'md'), p.erro ? 'og-campo-invalido' : '');
    var desc = p.erro || p.ajuda ? p.id + '-desc' : undefined;
    var ctrl = p.opcoes
      ? h('select', Object.assign(r, { className: cls, 'aria-describedby': desc }), p.opcoes.map(function (o) { return h('option', { key: o.valor, value: o.valor }, o.rotulo); }))
      : h('input', Object.assign({ type: 'text' }, r, { className: cls, 'aria-describedby': desc, 'aria-invalid': p.erro ? 'true' : undefined }));
    return h('div', { className: cx('og-campo', p.className) },
      h('label', { htmlFor: p.id, className: 'og-campo-rotulo' }, p.rotulo), ctrl,
      p.erro ? h('p', { id: desc, className: 'og-campo-erro', role: 'alert' }, p.erro)
        : p.ajuda ? h('p', { id: desc, className: 'og-campo-ajuda' }, p.ajuda) : null);
  }

  function Consentimento(p) {
    var r = Object.assign({}, p); delete r.children; delete r.className;
    return h('label', { className: cx('og-consentimento', p.className) },
      h('input', Object.assign({ type: 'checkbox' }, r)), h('span', null, p.children));
  }

  window.OrgatecUI = Object.assign(window.OrgatecUI || {}, { Assinatura: Assinatura, Botao: Botao, Selo: Selo, CitacaoFonte: CitacaoFonte, CartaoHub: CartaoHub, Campo: Campo, Consentimento: Consentimento });
})();
