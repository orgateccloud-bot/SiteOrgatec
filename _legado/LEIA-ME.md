# _legado — versões aposentadas do site

Esta pasta fica **fora de `site/`**, para que nada aqui seja publicado.

## `index-2026-10-31.html`: a página inicial antes da nova arquitetura

- **Data:** em 31/10/2026, a página inicial escrita à mão (13 seções, cerca de 17.100 px no celular) foi substituída por uma página gerada por `tools/gerar_paginas.py` (`inicio()`), com 7 blocos.
- **Para onde foi cada seção:**

| Seção antiga | Onde está agora |
|---|---|
| Simulador e captação do lead | `site/ferramentas/simulador.html` |
| Calendário fiscal, `.ics` e opt-in | `site/ferramentas/calendario.html` |
| Alertas regionais GO/TO/PA | `site/setores/regional.html` |
| Captura de XML e portal (demonstração) | `site/cliente/index.html` |
| Formulário de contato | `site/contato/index.html` |
| Hub da LC 214 e tabela de transição | `site/reforma/index.html` (guias e linha do tempo) |
| Como funciona (marcos) | `site/tributario/index.html` |
| Setores | bloco "Qual é o seu caso?" da página inicial |

- **IDs:** os elementos mantêm os IDs antigos (`simSector`, `calLista`, `contatoForm`...), e o `site/assets/js/app.js` continua o mesmo. Cada bloco só roda na página que tem o seu elemento.
- **Links antigos:** endereços já compartilhados, como `/#simulador` e `/?setor=agro#simulador`, são levados à página nova pelo `site/assets/js/abertura.js` (a raiz agora é a tela de abertura).

## Como voltar à versão anterior

1. **Restaurar a página antiga:** copie `_legado/index-2026-10-31.html` para `site/index.html`. Desde 31/10/2026, a raiz é a tela de abertura (`abertura()` no gerador), e a vitrine que substituiu a página antiga está em `site/inicio.html` (`inicio()`); `layout.INICIO` define para onde aponta o "Início" do menu.
2. **Manter a página antiga ao gerar o site:** em `tools/gerar_paginas.py`, comente a chamada `abertura()` em `main()` (ela grava `site/index.html`). Sem isso, a próxima geração sobrescreve a página restaurada. Se a vitrine também deve sair, comente `inicio()` e troque `INICIO` em `tools/layout.py` para `index.html`.
3. **Recolocar o menu e o rodapé que a página antiga usava.** A página antiga não tem `data-layout`, então o `paginas.js` não liga o menu nem os links dela. Em `site/assets/js/app.js`, recoloque os trechos abaixo, que existiam antes de 31/10/2026:

   ```js
   // no início de aplicarConfig()
   document.querySelectorAll('[data-link="portal"]').forEach(function (a) { a.href = C.portal.url; });
   document.querySelectorAll('[data-link^="whatsapp"]').forEach(function (a) {
     a.href = linkWhats(a.dataset.link === 'whatsapp-diagnostico'
       ? 'Olá, gostaria de agendar um diagnóstico tributário com a ORGATEC.' : '');
   });
   document.querySelectorAll('[data-texto="whatsapp"]').forEach(function (s) { s.textContent = C.whatsapp.exibicao; });

   // no fim de aplicarConfig(): e-mail do encarregado de dados no rodapé
   var rod = $('rodapeEmails');
   rod.appendChild(document.createTextNode('Encarregado de dados (DPO): '));
   if (C.emails.dpo.ativo) rod.appendChild(el('a', { href: 'mailto:' + C.emails.dpo.endereco, class: 'text-brandCyan hover:underline', text: C.emails.dpo.endereco }));
   else rod.appendChild(el('a', { href: '#contato', class: 'hover:underline', text: 'solicitações pelo formulário de contato (assunto LGPD)' }));

   // menu móvel (chamar initMenu() logo depois de aplicarConfig())
   function initMenu() {
     var b = $('btnMenu'), m = $('menuMobile');
     b.addEventListener('click', function () { m.hidden = !m.hidden; b.setAttribute('aria-expanded', String(!m.hidden)); });
     m.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { m.hidden = true; b.setAttribute('aria-expanded', 'false'); }); });
   }
   ```

   Se o opt-in voltar a ficar no cartão escuro, recoloque também, no sucesso de `enviarOptin`, a linha `alvo.classList.replace('text-emerald-700', 'text-emerald-300');`.
4. **Recompilar o CSS:** rode `python tools/compilar_css.py`. A página antiga usa classes (`slate`, `brandBlue`...) que saíram do CSS compilado quando ela deixou de existir.
5. **Conferir:** rode `node --test tests/js/*.test.js` e a suíte e2e. Os testes da nova arquitetura, no fim de `tests/e2e/test_e2e.py`, vão falhar de propósito.
