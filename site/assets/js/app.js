/* Ligação da interface (DOM) com os motores puros: regras.js, calendario.js, validadores.js.
   Cada bloco só roda na página que tem o seu elemento-raiz (simulador, calendário, alertas regionais,
   demonstrações da área do cliente, contato). Links, menu e faixa de homologação ficam em paginas.js. */
(function () {
  'use strict';
  var O = window.Orgatec;
  var C = O.config, F = O.fontes, U = O.ufs, R = O.regras, CAL = O.calendario, V = O.validadores, D = O.demo;

  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, filhos) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    });
    (filhos || []).forEach(function (f) { if (f) e.appendChild(typeof f === 'string' ? document.createTextNode(f) : f); });
    return e;
  }
  var brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
  var pct = new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 2 });

  function badgePendente() {
    return el('span', { class: 'badge-pendente text-[10px] font-semibold px-2 py-0.5 rounded-full ml-2 whitespace-nowrap', text: 'pendente de validação' });
  }

  // Lista de fontes de um item: rótulo + link oficial; fonte não confirmada ganha o selo "pendente".
  function fontesNode(ids) {
    var wrap = el('span', { class: 'text-[11px] text-slate-500' }, ['Fonte: ']);
    (ids || []).forEach(function (id, i) {
      var f = typeof id === 'object' ? id : F.porId[id]; // aceita id de fontes.js ou objeto {rotulo, url, validado}
      if (i) wrap.appendChild(document.createTextNode('; '));
      if (!f) { wrap.appendChild(el('span', { text: id })); wrap.appendChild(badgePendente()); return; }
      wrap.appendChild(f.url ? el('a', { href: f.url, target: '_blank', rel: 'noopener', class: 'underline hover:text-brandBlue', text: f.rotulo }) : el('span', { text: f.rotulo }));
      if (!f.validado) wrap.appendChild(badgePendente());
    });
    return wrap;
  }

  var NIVEL = {
    critico: { cls: 'border-red-200 bg-red-50', tag: 'Crítico', tagCls: 'bg-red-600 text-white' },
    atencao: { cls: 'border-amber-200 bg-amber-50', tag: 'Atenção', tagCls: 'bg-amber-500 text-white' },
    oportunidade: { cls: 'border-emerald-200 bg-emerald-50', tag: 'Oportunidade', tagCls: 'bg-accentGreen text-white' },
    info: { cls: 'border-slate-200 bg-white', tag: 'Informação', tagCls: 'bg-slate-600 text-white' }
  };
  function alertaNode(a) {
    var n = NIVEL[a.nivel] || NIVEL.info;
    var titulo = el('p', { class: 'font-semibold text-dark text-sm' }, [
      el('span', { class: 'text-[10px] uppercase tracking-wider px-2 py-0.5 rounded mr-2 ' + n.tagCls, text: n.tag }), a.titulo]);
    if (a.pendente) titulo.appendChild(badgePendente());
    return el('li', { class: 'border rounded-xl p-4 ' + n.cls, 'data-alerta': a.id }, [
      titulo, el('p', { class: 'text-sm text-slate-700 mt-2 leading-relaxed', text: a.texto }), fontesNode(a.fontes)]);
  }

  function preencherUfs(select, selecionada) {
    U.lista.forEach(function (u) {
      var o = el('option', { value: u.sigla, text: u.nome + ' (' + u.sigla + ')' });
      if (u.sigla === selecionada) o.selected = true;
      select.appendChild(o);
    });
  }

  function linkWhats(texto) {
    return 'https://wa.me/' + C.whatsapp.numeroE164 + (texto ? '?text=' + encodeURIComponent(texto) : '');
  }

  /* ---------- Configuração refletida na interface ---------- */
  function aplicarConfig() {
    var pend = [];
    if (!C.capturaXml.ferramenta) pend.push('ferramenta de captura de XML (Sieg, Arquivei ou Omie)');
    if (!C.portal.erp) pend.push('ERP de destino do CNAME do portal');
    if (!C.emails.contato.ativo || !C.emails.dpo.ativo) pend.push('ativação de contato@ e dpo@orgatec.io');
    if (!C.whatsapp.validado) pend.push('validação do WhatsApp ' + C.whatsapp.exibicao);
    if (C.ambiente === 'homologacao' && pend.length && $('listaPendencias')) {
      $('listaPendencias').textContent = pend.join(' · ');
      $('faixaHomologacao').hidden = false;
    }

    if ($('xmlFerramenta')) {
    var xf = C.capturaXml.ferramenta && C.capturaXml.opcoes[C.capturaXml.ferramenta];
    $('xmlFerramenta').textContent = xf ? 'Integração: ' + xf.nome : 'Ferramenta de captura: pendente de definição';
    $('xmlFerramenta').className = 'text-xs px-2 py-1 rounded-full ' + (xf ? 'bg-emerald-100 text-emerald-800' : 'badge-pendente');
    var erp = C.portal.erp && C.portal.opcoes[C.portal.erp];
    $('portalErp').textContent = erp ? 'ERP: ' + erp.nome : 'ERP do portal: pendente de definição';
    $('portalErp').className = 'text-xs px-2 py-1 rounded-full ' + (erp ? 'bg-emerald-100 text-emerald-800' : 'badge-pendente');
    }

    var linha = $('contatoEmailLinha');
    if (!linha) return;
    if (C.emails.contato.ativo) {
      linha.appendChild(document.createTextNode('E-mail: '));
      linha.appendChild(el('a', { href: 'mailto:' + C.emails.contato.endereco, class: 'text-brandBlue underline', text: C.emails.contato.endereco }));
    } else {
      linha.textContent = 'Responderemos pelo WhatsApp ou pelo e-mail que você informar.';
    }
  }

  /* ---------- Hub: tabela de transição ---------- */
  function renderTransicao() {
    document.querySelectorAll('[data-fonte]').forEach(function (s) { s.replaceWith(fontesNode(s.dataset.fonte.split(','))); });
    var tb = $('tabelaTransicao').querySelector('tbody');
    R.TRANSICAO.forEach(function (l) {
      tb.appendChild(el('tr', {}, [l.ano, l.cbs, l.ibs, l.piscofins, l.ipi, l.icmsiss].map(function (c, i) {
        return el('td', { class: 'py-2 pr-4 ' + (i === 0 ? 'font-mono font-semibold text-dark' : 'text-slate-600'), text: c });
      })));
    });
  }

  /* ---------- Simulador ---------- */
  var ultimaSimulacao = null;

  function lerNumero(v) {
    if (v == null) return NaN;
    var s = String(v).trim().replace(/[R$\s]/g, '');
    if (!s) return NaN;
    if (s.indexOf(',') >= 0) s = s.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
    return Number(s);
  }

  function initSimulador() {
    var selSetor = $('simSector');
    R.SETORES.forEach(function (s) { selSetor.appendChild(el('option', { value: s.id, text: s.rotulo })); });
    // Páginas de setor chegam com ?setor=agro#simulador: pré-seleciona o setor se ele existir.
    var setorUrl = new URLSearchParams(location.search).get('setor');
    if (setorUrl && R.setor(setorUrl)) selSetor.value = setorUrl;
    preencherUfs($('simUf'), 'GO');
    function premissa() { $('simCompras').value = Math.round(R.setor(selSetor.value).comprasPadrao * 100); }
    selSetor.addEventListener('change', premissa);
    premissa();
    var regimeUrl = new URLSearchParams(location.search).get('regime');
    if (regimeUrl && R.ROTULO_REGIME[regimeUrl]) $('simRegime').value = regimeUrl;
    $('taxSimulatorForm').addEventListener('submit', function (ev) { ev.preventDefault(); runSimulation(); });
    $('leadForm').addEventListener('submit', enviarLead);
    // Simulação rápida da página inicial: o faturamento vem pela memória da aba (nunca pela URL) e é apagado ao ler
    var rapida = null;
    try { rapida = JSON.parse(sessionStorage.getItem('orgatec.simulacaoRapida') || 'null'); sessionStorage.removeItem('orgatec.simulacaoRapida'); } catch (e) { rapida = null; }
    if (rapida && rapida.faturamento) { $('simFaturamento').value = String(rapida.faturamento).slice(0, 20); runSimulation(); }
  }

  function runSimulation() {
    var entrada = {
      setor: $('simSector').value, regime: $('simRegime').value, perfil: $('simClient').value, uf: $('simUf').value,
      faturamento: lerNumero($('simFaturamento').value), comprasPct: lerNumero($('simCompras').value) / 100
    };
    var res = R.simular(entrada);
    var erro = $('simErro');
    if (res.erros.length) { erro.textContent = res.erros.join(' '); erro.hidden = false; return; }
    erro.hidden = true;
    ultimaSimulacao = res;

    $('resultText').textContent = res.resumo;
    var est = $('resultEstimativa'); est.innerHTML = '';
    if (res.estimativa) est.appendChild(estimativaNode(res.estimativa));
    var ul = $('resultAlertas'); ul.innerHTML = '';
    res.alertas.forEach(function (a) { ul.appendChild(alertaNode(a)); });

    var s = R.setor(entrada.setor), u = U.porSigla[entrada.uf];
    $('ctaWhatsSim').href = linkWhats('Olá, fiz a simulação no site da ORGATEC (' + s.rotulo + ', ' +
      R.ROTULO_REGIME[entrada.regime] + ', ' + u.sigla + ') e gostaria de uma análise completa do meu CNPJ.');
    $('simResult').classList.remove('hidden');
    $('simResult').scrollIntoView({ behavior: 'smooth' });
  }
  window.runSimulation = runSimulation; // compatibilidade com a versão anterior

  function estimativaNode(e) {
    function linha(rot, val, destaque) {
      return el('div', { class: 'flex justify-between gap-4 py-1 ' + (destaque ? 'font-semibold text-dark border-t border-slate-200 mt-1 pt-2' : '') },
        [el('span', { text: rot }), el('span', { class: 'font-mono', text: val })]);
    }
    var titulo = el('p', { class: 'font-semibold text-dark text-sm mb-2' }, [e.titulo]);
    titulo.appendChild(badgePendente());
    var box = el('div', { class: 'bg-white border border-blue-100 rounded-lg p-4 text-sm', id: 'cardEstimativa' }, [titulo,
      linha(C.simulador.rotuloEstimativa, pct.format(e.aliquotaReferencia)),
      linha('Redução setorial aplicada', e.reducao ? pct.format(e.reducao) : 'nenhuma'),
      linha('Alíquota estimada sobre as vendas', pct.format(e.aliquotaEfetiva)),
      linha('Débito estimado (ano)', brl.format(e.debito)),
      linha('(−) Créditos estimados sobre compras', brl.format(e.credito)),
      linha('IBS + CBS a recolher (ano, regime pleno 2033)', brl.format(e.liquido), true),
      linha('Carga sobre o faturamento', pct.format(e.cargaSobreFaturamento))]);
    if (e.creditoClienteB2B != null) {
      box.appendChild(el('p', { class: 'text-xs text-slate-600 mt-3', text: 'Crédito que seu cliente PJ aproveita a cada R$ 100,00 vendidos, se você apurar IBS/CBS no regime regular: ' +
        brl.format(e.creditoClienteB2B) + '. No DAS, o crédito fica limitado ao IBS/CBS efetivamente pago no Simples (depende do anexo e da faixa).' }));
    }
    box.appendChild(el('p', { class: 'text-[11px] text-slate-500 mt-3', text: 'Premissas: ' + e.premissas.join(' ') }));
    box.appendChild(fontesNode(e.fontes));
    return box;
  }

  /* ---------- Envio de formulários ---------- */
  function consentimento(finalidade) {
    return { aceito: true, versao_politica: C.lgpd.versaoPolitica, finalidade: finalidade };
  }

  function msg(alvo, texto, ok) {
    alvo.textContent = texto;
    alvo.className = 'text-sm ' + (ok ? 'text-emerald-700' : 'text-red-700');
  }

  function postar(rota, corpo) {
    if (C.api.base === null) return Promise.reject(new Error('sem-backend'));
    return fetch(C.api.base + rota, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) { var e = new Error('http-' + r.status); e.status = r.status; e.corpo = j; throw e; }
          return j;
        });
      });
  }

  function validarContato(email, whats) {
    if (!email && !whats) return 'Informe e-mail ou WhatsApp.';
    if (email && !V.emailValido(email)) return 'E-mail inválido.';
    if (whats && !V.celularValido(whats)) return 'WhatsApp inválido: use DDD + 9 dígitos.';
    return null;
  }

  function falhaEnvio(alvo, err, textoWhats) {
    if (err && err.status === 429) return msg(alvo, 'Muitas tentativas. Aguarde alguns minutos.', false);
    if (err && err.status === 422) return msg(alvo, 'Confira os campos preenchidos.', false);
    msg(alvo, 'Não foi possível enviar agora. Fale conosco pelo WhatsApp: ', false);
    alvo.appendChild(el('a', { href: linkWhats(textoWhats), target: '_blank', rel: 'noopener', class: 'underline font-semibold', text: 'abrir conversa' }));
  }

  function enviarLead(ev) {
    ev.preventDefault();
    var f = ev.target, alvo = $('leadMsg');
    var nome = $('leadNome').value.trim(), email = $('leadEmail').value.trim(), whats = $('leadWhats').value.trim();
    if (!ultimaSimulacao) return msg(alvo, 'Gere a simulação antes de enviar.', false);
    if (nome.length < 2) return msg(alvo, 'Informe seu nome.', false);
    var e = validarContato(email, whats); if (e) return msg(alvo, e, false);
    if (!$('leadConsent').checked) return msg(alvo, 'É necessário autorizar o uso dos dados (LGPD) para enviar.', false);
    var en = ultimaSimulacao.entrada;
    var corpo = {
      website: f.elements.website.value, nome: nome, email: email || null, whatsapp: whats || null,
      empresa: $('leadEmpresa').value.trim() || null,
      consentimento: consentimento('contato sobre diagnóstico tributário a partir do simulador'),
      simulacao: { setor: en.setor, regime: en.regime, perfil: en.perfil, uf: en.uf,
        faturamento_anual: isFinite(en.faturamento) ? en.faturamento : null,
        alertas: ultimaSimulacao.alertas.map(function (a) { return a.id; }) }
    };
    postar('/api/leads', corpo).then(function (r) {
      msg(alvo, 'Recebido. Protocolo ' + r.protocolo + '. Um especialista entrará em contato.', true);
      f.querySelector('button[type=submit]').disabled = true;
    }).catch(function (err) { falhaEnvio(alvo, err, 'Olá, fiz a simulação no site da ORGATEC e gostaria de uma análise completa do meu CNPJ.'); });
  }

  /* ---------- Calendário ---------- */
  var obrigacoesAtuais = [];
  function initCalendario() {
    var hoje = new Date();
    $('calMes').value = hoje.getFullYear() + '-' + String(hoje.getMonth() + 1).padStart(2, '0');
    preencherUfs($('calUf'), 'GO');
    preencherUfs($('optUfs'), 'GO');
    ['calMes', 'calUf', 'calRegime'].forEach(function (id) { $(id).addEventListener('change', renderCalendario); });
    document.querySelectorAll('input[name=calEsfera]').forEach(function (c) { c.addEventListener('change', renderCalendario); });
    $('btnIcs').addEventListener('click', baixarIcs);
    $('optinForm').addEventListener('submit', enviarOptin);
    renderCalendario();
  }

  function esferas(nome) {
    return Array.prototype.filter.call(document.querySelectorAll('input[name=' + nome + ']'), function (c) { return c.checked; })
      .map(function (c) { return c.value; });
  }

  function renderCalendario() {
    var am = ($('calMes').value || '').split('-');
    if (am.length !== 2) return;
    var uf = $('calUf').value;
    obrigacoesAtuais = CAL.obrigacoesDoMes(Number(am[0]), Number(am[1]), { uf: uf, regime: $('calRegime').value, esferas: esferas('calEsfera') });
    var ul = $('calLista'); ul.innerHTML = '';
    if (!obrigacoesAtuais.length) ul.appendChild(el('li', { class: 'py-3 text-slate-500', text: 'Nenhuma obrigação para os filtros escolhidos.' }));
    obrigacoesAtuais.forEach(function (o) {
      var data = o.data ? o.data.split('-').reverse().join('/') : o.regraVariavel ? 'conforme atividade' : 'data a confirmar';
      var cor = { federal: 'bg-blue-100 text-blue-800', trabalhista: 'bg-cyan-100 text-cyan-800', estadual: 'bg-emerald-100 text-emerald-800', compliance: 'bg-amber-100 text-amber-800' }[o.esfera];
      var t = el('div', { class: 'flex-1 min-w-0 break-words' }, [el('p', { class: 'text-dark', text: o.titulo })]);
      if (o.pendente) t.firstChild.appendChild(badgePendente());
      if (o.ajustada) t.appendChild(el('p', { class: 'text-[11px] text-slate-500', text: 'Data ajustada por fim de semana ou feriado nacional.' }));
      t.appendChild(fontesNode(o.fontes));
      if (o.link) t.appendChild(el('a', { href: o.link, target: '_blank', rel: 'noopener', class: 'block text-[11px] text-brandBlue underline', text: 'Portal da fazenda estadual' }));
      ul.appendChild(el('li', { class: 'py-3 flex gap-4 items-start', 'data-obrigacao': o.id }, [
        el('span', { class: 'font-mono text-xs w-24 shrink-0 pt-0.5 ' + (o.data ? 'text-dark font-semibold' : 'text-slate-400'), text: data }),
        t, el('span', { class: 'text-[10px] uppercase px-2 py-0.5 rounded shrink-0 ' + cor, text: o.esfera })]));
    });
    var u = U.porSigla[uf];
    $('calGuia').textContent = (u.orgao ? u.orgao + ' · ' : '') + (u.guia ? 'guia estadual: ' + u.guia + (u.guiaValidada ? '' : ' (pendente de validação)') : 'guia estadual: pendente de validação');
  }

  function baixarIcs() {
    var blob = new Blob([CAL.gerarIcs(obrigacoesAtuais)], { type: 'text/calendar;charset=utf-8' });
    var a = el('a', { href: URL.createObjectURL(blob), download: 'orgatec-calendario-' + $('calMes').value + '-' + $('calUf').value + '.ics' });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  function enviarOptin(ev) {
    ev.preventDefault();
    var f = ev.target, alvo = $('optMsg');
    alvo.className = 'text-sm';
    var email = $('optEmail').value.trim(), whats = $('optWhats').value.trim();
    var e = validarContato(email, whats); if (e) return msg(alvo, e, false);
    var ufs = Array.prototype.map.call($('optUfs').selectedOptions, function (o) { return o.value; });
    if (!ufs.length) return msg(alvo, 'Escolha ao menos uma UF.', false);
    var esf = esferas('optEsfera');
    if (!esf.length) return msg(alvo, 'Escolha ao menos uma esfera.', false);
    if (!$('optConsent').checked) return msg(alvo, 'É necessário aceitar o recebimento (LGPD).', false);
    postar('/api/optin', {
      website: f.elements.website.value, email: email || null, whatsapp: whats || null, ufs: ufs, esferas: esf,
      consentimento: consentimento('envio de alertas do calendário fiscal')
    }).then(function (r) {
      msg(alvo, 'Inscrição registrada (protocolo ' + r.protocolo + '). Confirme pelo link que enviaremos ao seu contato.', true);
      f.querySelector('button[type=submit]').disabled = true;
    }).catch(function (err) { falhaEnvio(alvo, err, 'Olá, quero receber os alertas do Calendário Fiscal da ORGATEC.'); });
  }

  /* ---------- Soluções: demonstração com os modelos de homologação ---------- */
  function renderDemos() {
    var tb = $('xmlTabela');
    D.capturaXml.forEach(function (d) {
      var an = V.analisarDocumento(d);
      var falhas = an.checks.filter(function (c) { return !c.ok; });
      var val = el('details', { class: 'text-xs' }, [
        el('summary', { class: 'cursor-pointer ' + (an.ok ? 'text-emerald-700' : 'text-amber-700'), text: an.ok ? 'Íntegro' : falhas.length + ' divergência(s)' }),
        el('ul', { class: 'mt-1 space-y-0.5' }, an.checks.map(function (c) {
          return el('li', { class: c.ok ? 'text-slate-500' : 'text-amber-800', text: (c.ok ? '✓ ' : '✗ ') + c.msg });
        }))]);
      tb.appendChild(el('tr', { 'data-doc': d.id }, [
        el('td', { class: 'py-2 pr-3 font-mono text-xs', text: d.id }),
        el('td', { class: 'py-2 pr-3' }, [el('span', { class: 'block', text: d.emitente }), el('span', { class: 'font-mono text-[11px] text-slate-500', text: d.cnpj })]),
        el('td', { class: 'py-2 pr-3', text: d.uf }),
        el('td', { class: 'py-2 pr-3', text: d.tipo }),
        el('td', { class: 'py-2 pr-3 text-right font-mono', text: brl.format(d.valor) }),
        el('td', { class: 'py-2 pr-3 font-mono text-xs', text: d.data.split('-').reverse().join('/') }),
        el('td', { class: 'py-2 pr-3 text-xs', text: d.status + ' · LGPD: ' + d.lgpd }),
        el('td', { class: 'py-2' }, [val])]));
    });

    var slaCor = function (st) { return /conclu/i.test(st) ? 'bg-emerald-100 text-emerald-800' : /andamento/i.test(st) ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'; };
    var tp = $('portalTabela');
    D.protocolos.forEach(function (p) {
      tp.appendChild(el('tr', { 'data-protocolo': p.protocolo }, [
        el('td', { class: 'py-2 pr-3 font-mono text-xs', text: p.protocolo }),
        el('td', { class: 'py-2 pr-3', text: p.uf }),
        el('td', { class: 'py-2 pr-3', text: p.departamento }),
        el('td', { class: 'py-2 pr-3' }, [el('span', { class: 'block', text: p.solicitacao }), el('span', { class: 'text-[11px] text-slate-500', text: p.acao })]),
        el('td', { class: 'py-2 pr-3 font-mono text-xs', text: p.competencia }),
        el('td', { class: 'py-2 pr-3' }, [el('span', { class: 'text-xs px-2 py-0.5 rounded-full ' + slaCor(p.status), text: p.status })]),
        el('td', { class: 'py-2 pr-3 font-mono text-xs', text: p.sla }),
        el('td', { class: 'py-2 font-mono text-[11px]' }, [el('span', { class: 'block', text: p.auditoria.ip + ' #' + p.auditoria.ipHash }),
          el('span', { class: p.auditoria.mfa ? 'text-emerald-700' : 'text-red-700', text: p.auditoria.mfa ? 'MFA verificado' : 'sem MFA' })])]));
    });
  }

  /* ---------- Alertas regionais ---------- */
  function initRegional() {
    var estado = { uf: 'GO', setor: 'agro' };
    // ?uf=GO&setor=agro (links de outras páginas, como o do agro): só valores que existem; o resto fica no padrão
    var pedido = new URLSearchParams(location.search), ufPedida = (pedido.get('uf') || '').toUpperCase(), setorPedido = pedido.get('setor');
    if (['GO', 'TO', 'PA'].indexOf(ufPedida) >= 0) estado.uf = ufPedida;
    if (R.SETORES_REGIONAIS.indexOf(setorPedido) >= 0) estado.setor = setorPedido;
    function tabs(alvo, itens, chave) {
      itens.forEach(function (it) {
        var b = el('button', { type: 'button', role: 'tab', class: 'text-sm font-medium px-4 py-2 rounded-lg border border-slate-300 bg-white transition', 'data-valor': it.v, text: it.r });
        b.addEventListener('click', function () { estado[chave] = it.v; render(); });
        alvo.appendChild(b);
      });
    }
    tabs($('tabsUf'), [{ v: 'GO', r: 'Goiás' }, { v: 'TO', r: 'Tocantins' }, { v: 'PA', r: 'Pará' }], 'uf');
    tabs($('tabsSetor'), R.SETORES_REGIONAIS.map(function (s) { return { v: s, r: R.setor(s).rotuloCurto }; }), 'setor');
    function render() {
      [['tabsUf', 'uf'], ['tabsSetor', 'setor']].forEach(function (p) {
        $(p[0]).querySelectorAll('button').forEach(function (b) {
          var on = b.dataset.valor === estado[p[1]];
          b.classList.toggle('tab-ativa', on); b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
      });
      var ul = $('listaRegional'); ul.innerHTML = '';
      R.alertasRegionais(estado.uf, estado.setor).forEach(function (a) { ul.appendChild(alertaNode(a)); });
    }
    render();
  }

  /* ---------- Contato ---------- */
  function initContato() {
    // ?assunto=lgpd (link "Exercer meus direitos"): só escolhe uma opção que já existe no formulário
    var pedido = new URLSearchParams(location.search).get('assunto'), assunto = $('ctAssunto');
    if (Array.prototype.some.call(assunto.options, function (o) { return o.value === pedido; })) assunto.value = pedido;
    $('contatoForm').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var f = ev.target, alvo = $('ctMsg');
      var nome = $('ctNome').value.trim(), email = $('ctEmail').value.trim(), whats = $('ctWhats').value.trim(), m = $('ctMensagem').value.trim();
      if (nome.length < 2) return msg(alvo, 'Informe seu nome.', false);
      var e = validarContato(email, whats); if (e) return msg(alvo, e, false);
      if (m.length < 10) return msg(alvo, 'Escreva uma mensagem com ao menos 10 caracteres.', false);
      if (!$('ctConsent').checked) return msg(alvo, 'É necessário autorizar o uso dos dados (LGPD).', false);
      postar('/api/contato', {
        website: f.elements.website.value, nome: nome, email: email || null, whatsapp: whats || null,
        assunto: $('ctAssunto').value, mensagem: m, consentimento: consentimento('resposta à mensagem de contato')
      }).then(function (r) {
        msg(alvo, 'Mensagem enviada. Protocolo ' + r.protocolo + '.', true);
        f.querySelector('button[type=submit]').disabled = true;
      }).catch(function (err) { falhaEnvio(alvo, err, 'Olá, gostaria de falar com a ORGATEC.'); });
    });
  }

  aplicarConfig();
  if ($('tabelaTransicao')) renderTransicao();
  if ($('taxSimulatorForm')) initSimulador();
  if ($('calLista')) initCalendario();
  if ($('xmlTabela')) renderDemos();
  if ($('listaRegional')) initRegional();
  if ($('contatoForm')) initContato();
})();
