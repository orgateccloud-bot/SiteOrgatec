/* Política de privacidade: mostra o canal do encarregado de dados conforme config.js (sem script embutido na página, para a CSP). */
(function () {
    var d = window.Orgatec.config.emails.dpo;
    if (d.ativo) {
        var p = document.getElementById('dpoLinha');
        p.textContent = 'E-mail do encarregado: ';
        var a = document.createElement('a'); a.href = 'mailto:' + d.endereco; a.className = 'text-brandBlue underline'; a.textContent = d.endereco;
        p.appendChild(a);
    }
})();
