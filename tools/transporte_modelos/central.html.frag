<div class="dev" id="dev" hidden></div>
  <div id="aviso"></div>
  <div class="grade">
    <div>
      <form class="cartao" id="form" novalidate>
        <h2>Lançar rota</h2>
        <label for="veiculo">Veículo</label>
        <select id="veiculo" required></select>
        <div id="pontos"></div>
        <div class="acoes"><button type="button" class="sec mini" id="addParada">+ parada intermediária</button></div>
        <div class="linha">
          <div><label for="partida">Partida prevista (horário de Brasília)</label><input id="partida" type="datetime-local" required></div>
        </div>
        <label><input type="checkbox" id="carregado" checked style="width:auto"> Veículo carregado</label>
        <label for="descricao">Descrição (opcional)</label><input id="descricao" maxlength="160">
        <div id="msgForm"></div>
        <div class="acoes"><button type="submit" id="lancar">Calcular viagem</button></div>
      </form>
      <details class="cartao" id="boxVeiculo"><summary>Cadastrar veículo</summary>
        <form id="formVeiculo" novalidate>
          <div class="linha"><div><label for="vPlaca">Placa</label><input id="vPlaca" required placeholder="ABC1D23"></div><div class="estreito"><label for="vEixos">Eixos</label><input id="vEixos" type="number" min="2" max="9" value="6"></div></div>
          <label for="vDesc">Descrição</label><input id="vDesc" placeholder="Cavalo 6x2 + carreta">
          <div class="linha"><div><label for="vCc">km/l carregado</label><input id="vCc" type="number" step="0.01" value="2.3"></div><div><label for="vCv">km/l vazio</label><input id="vCv" type="number" step="0.01" value="2.9"></div><div><label for="vT">Tanque (l)</label><input id="vT" type="number" value="700"></div></div>
          <div id="msgVeiculo"></div>
          <div class="acoes"><button type="submit">Salvar veículo</button></div>
        </form>
      </details>
      <details class="cartao" id="boxParametros"><summary>Parâmetros de custo e jornada</summary>
        <form id="formParametros" novalidate><div id="camposParametros" class="carregando">Carregando…</div><div id="msgParametros"></div>
          <div class="acoes"><button type="submit">Salvar parâmetros</button></div></form>
      </details>
      <div class="cartao"><h2>Viagens recentes</h2><ul class="lista-viagens" id="lista"></ul></div>
    </div>
    <section id="resultado" aria-live="polite"><div class="cartao vazio">Lance uma rota para ver despesas, tempo, bloqueios e clima.</div></section>
  </div>
