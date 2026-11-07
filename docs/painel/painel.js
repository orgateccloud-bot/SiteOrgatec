/* Dados e interação dos modelos do painel de compliance moderno (docs/estudo-compliance-moderno.md). */
(function(){
  var FRENTES = [
    {t:'1. Eficácia', c:'A', r:'Separar existe, funciona e como sabe.', site:'Termômetro em três camadas; o resultado mostra o que é só declaração.', serv:'Diagnóstico pede amostra de registros (canal, cadastros, CIOT emitidos).', f:'DOJ ECCP (set/2024): "o programa funciona na prática?"'},
    {t:'2. Risco e proporcionalidade', c:'A', r:'Pesos por perfil, porte e histórico, revistos.', site:'Pesos do termômetro por perfil, com justificativa e fonte (V11).', serv:'Matriz de risco anual do cliente, curta para MEI e Simples.', f:'Decreto 11.129/2022, art. 57 (porte); ECCP (avaliação de risco).'},
    {t:'3. Cultura e relatos', c:'C', r:'Valores e segurança para relatar pesam mais que regra.', site:'Perguntas de cultura e de tratamento de relatos na frente de integridade.', serv:'Canal com prazo de resposta e registro de apuração.', f:'Weaver e Treviño (1999); Stubben e Welch (2020).'},
    {t:'4. Monitoramento', c:'C', r:'Toda a base, não amostra.', site:'Explicar o cruzamento como serviço, sem dados no site.', serv:'Conciliação e auditoria rural já cruzam notas, extratos e escrituração.', f:'Jans, Alles e Vasarhelyi (2014).'},
    {t:'5. Conformidade embutida', c:'A', r:'O controle mora no emissor, no ERP e na rotina.', site:'Plano de ação em .ics e lembretes no calendário (pendência antiga).', serv:'Revisão do cadastro de produtos e do emissor (campos de IBS e CBS).', f:'OCDE, Tax Administration 3.0 (via relatório de 2023).'},
    {t:'6. Comportamento', c:'B', r:'Lembretes ajudam pouco, mas ajudam.', site:'Lembretes simples e no momento certo; nada de norma social inventada.', serv:'Avisos de prazo para os clientes.', f:'Antinyan e Asatryan (2025); Hallsworth et al. (2017).'},
    {t:'7. Treinamento', c:'B', r:'Comunicar o código não garantiu entendimento.', site:'Não prometer que treinamento reduz desvios.', serv:'Treinar em pequenos grupos e medir entendimento.', f:'Gómez-Alatorre et al. (2022), RCT nulo.'},
    {t:'8. Mudança regulatória', c:'A', r:'Fonte primária primeiro, revalidação periódica.', site:'Rotina de 90 dias com conteudo.atrasados(); casos CIOT, 30% e MEI.', serv:'Boletim de mudanças para os clientes por público.', f:'Lições do próprio projeto (relatório de públicos).'},
    {t:'9. IA e analytics', c:'A', r:'Governança, precisão e recall, falsos positivos.', site:'Nenhuma IA no site; dizer como os sistemas medem acerto.', serv:'Relatar falsos positivos dos cruzamentos; Benford só como triagem.', f:'DOJ ECCP; FATF (2021); ISO/IEC 42001:2023.'}
  ];
  var EVID = [
    ['DOJ, ECCP (set/2024)','A','Três perguntas: desenho, recursos, funciona na prática; pede dados, analytics e medir precisão e recall.','EUA; verificar versão mais nova.'],
    ['ISO 37301:2021 · ISO 37001:2025 · ISO/IEC 42001:2023','A','Sistemas de gestão de compliance, antissuborno e IA.','Texto pago: citar só escopo.'],
    ['CGU, Pró-Ética 2025-2026','A','Dez áreas; aprovação com 70% e mínimo em cada área.','Pensado para empresas maiores.'],
    ['Antinyan e Asatryan (EJ, 2025)','B','Lembrete +2,7 p.p.; dissuasão +3,2; moral +1,4 (base de cerca de 25%).','Efeitos pequenos; viés de publicação.'],
    ['Hallsworth et al. (JPubE, 2017)','B','Norma descritiva em cartas elevou pagamento de impostos em atraso.','Reino Unido; pessoa física.'],
    ['Gómez-Alatorre et al. (2022)','B','E-mail semanal sobre o código não melhorou o entendimento.','Um varejista no México.'],
    ['Stubben e Welch (JAR, 2020)','C','Mais relatos no canal, menos multas e processos.','Correlação; dados de fornecedor.'],
    ['Jans, Alles e Vasarhelyi (TAR, 2014)','C','Mineração de processos achou falhas de aprovação que a auditoria não viu.','Um banco.'],
    ['Weaver e Treviño (1999)','C','Orientação por valores pesa mais que por regra.','Uma empresa, pesquisa de opinião.'],
    ['Batrancea et al. (44 países)','C','Confiança e poder da autoridade elevam a intenção de cumprir.','Cenário, não comportamento.'],
    ['Shu et al. (PNAS, 2012)','X','Retratado em 2021. Não usar.','Dados questionados.']
  ];
  var COBERTURA = [['Desenho (existe)',43,43],['Recursos e responsáveis',4,43],['Funciona na prática',0,43],['Risco e terceiros',3,43],['Cultura e relatos',1,43],['Medição e prova',0,43]];
  var ONDAS = [
    ['Onda 1 · rápida','Termômetro com a camada "como sabe" em 5 perguntas; aviso de que o resultado é declaração; rotina de revalidação de 90 dias; plano de ação em .ics.'],
    ['Onda 2 · média','Pesos por perfil com justificativa (V11); perguntas de cultura e de relatos; página explicando o monitoramento do escritório; boletim de mudanças por público.'],
    ['Onda 3 · estrutural','Página de revisão do responsável técnico; diagnóstico de eficácia como serviço; mapa dos cruzamentos com precisão e falsos positivos medidos.']
  ];
  var NAO = [
    ['Probabilidade de autuação no termômetro','Não há base de dados para isso; seria opinião apresentada como fato.'],
    ['Assinar no topo do formulário para induzir honestidade','O estudo foi retratado em 2021.'],
    ['Mensagem do tipo "9 em cada 10 já cumprem"','Só com dado real; inventar a norma social é enganoso.'],
    ['Prometer que treinamento reduz desvios','Evidência fraca ou nula.'],
    ['Benford como prova de fraude','Falha com poucos dados e alarma à toa perto de limites de aprovação.'],
    ['Copiar o texto das normas ISO','Conteúdo pago e protegido.'],
    ['IA no site analisando dados de clientes','Fora do escopo do site estático; LGPD e CSP.']
  ];
  function $(s){return document.querySelector(s)}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function desenharFrentes(classe){
    $('#frentes').innerHTML = FRENTES.filter(function(f){return classe==='todas'||f.c===classe}).map(function(f){
      return '<article class="cartao" tabindex="0"><span class="selo c'+f.c+'">Classe '+f.c+'</span><h3>'+esc(f.t)+'</h3><p>'+esc(f.r)+'</p>'+
        '<div class="det"><p><b>No site:</b> '+esc(f.site)+'</p><p><b>No serviço:</b> '+esc(f.serv)+'</p><p><b>Base:</b> '+esc(f.f)+'</p></div></article>';
    }).join('');
  }
  desenharFrentes('todas');
  $('#frentes').addEventListener('click',function(e){var c=e.target.closest('.cartao'); if(c) c.classList.toggle('aberto')});
  $('#frentes').addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){var c=e.target.closest('.cartao'); if(c){e.preventDefault();c.classList.toggle('aberto')}}});
  $('#filtroClasse').addEventListener('click',function(e){var b=e.target.closest('button'); if(!b) return;
    document.querySelectorAll('#filtroClasse button').forEach(function(x){x.setAttribute('aria-pressed',x===b)}); desenharFrentes(b.dataset.classe)});
  document.querySelectorAll('nav.abas button').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('nav.abas button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});
    document.querySelectorAll('[data-painel]').forEach(function(s){s.hidden = s.dataset.painel!==b.dataset.aba});
    if(b.dataset.aba==='termometro') animarBarras();
  })});
  $('#cobertura').innerHTML = COBERTURA.map(function(c){return '<div class="linha-barra"><span>'+esc(c[0])+'</span><div class="barra"><i style="width:0" data-w="'+(c[1]/c[2]*100)+'"></i></div><span>'+c[1]+'/'+c[2]+'</span></div>'}).join('');
  function animarBarras(){requestAnimationFrame(function(){document.querySelectorAll('#cobertura i').forEach(function(i){i.style.width=i.dataset.w+'%'})})}
  $('#tabelaEvidencia').innerHTML = EVID.map(function(e){return '<tr><td>'+esc(e[0])+'</td><td><span class="selo c'+e[1]+'">'+(e[1]==='X'?'retratado':e[1])+'</span></td><td>'+esc(e[2])+'</td><td>'+esc(e[3])+'</td></tr>'}).join('');
  $('#ondas').innerHTML = ONDAS.map(function(o){return '<div class="vidro"><h3 style="margin:0 0 6px">'+esc(o[0])+'</h3><p style="margin:0">'+esc(o[1])+'</p></div>'}).join('');
  $('#tabelaNao').innerHTML = NAO.map(function(n){return '<tr><td>'+esc(n[0])+'</td><td>'+esc(n[1])+'</td></tr>'}).join('');
  var bt=$('#tema'); if(bt) bt.addEventListener('click',function(){var r=document.documentElement; r.dataset.tema = r.dataset.tema==='claro'?'escuro':'claro'});
  var abaInicial=document.querySelector('nav.abas button[aria-pressed="true"]'); if(abaInicial&&abaInicial.dataset.aba==='termometro') animarBarras();
})();
