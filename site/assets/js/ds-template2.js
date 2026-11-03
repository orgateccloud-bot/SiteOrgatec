/* Gerado junto com a página. Não edite à mão. */
(function () {
        var ordem = ['auto', 'claro', 'escuro'], nomes = { auto: 'automático', claro: 'claro', escuro: 'escuro' };
        var btn = document.getElementById('btnTema'), atual = 'auto';
        try { atual = localStorage.getItem('og-tema') || 'auto'; } catch (e) {}
        function aplica() {
            if (atual === 'auto') document.documentElement.removeAttribute('data-theme');
            else document.documentElement.setAttribute('data-theme', atual);
            btn.textContent = 'Tema: ' + nomes[atual];
        }
        btn.addEventListener('click', function () {
            atual = ordem[(ordem.indexOf(atual) + 1) % ordem.length];
            try { localStorage.setItem('og-tema', atual); } catch (e) {}
            aplica();
        });
        aplica();
    })();
