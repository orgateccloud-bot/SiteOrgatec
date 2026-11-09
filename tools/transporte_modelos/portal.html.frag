<div class="dev" id="dev" hidden></div>
  <div id="aviso"></div>
  <div class="grade">
    <div>
      <div class="cartao"><h2>Viagens</h2><ul class="lista-viagens" id="lista"><li class="carregando">Carregando…</li></ul></div>
      <div class="cartao" id="boxSensores" hidden>
        <h2>Sensores e rastreadores</h2>
        <div id="listaSensores"></div>
        <details><summary>Conectar sensor via API</summary>
          <form id="formSensor" novalidate>
            <label for="sVeiculo">Veículo</label><select id="sVeiculo"></select>
            <label for="sNome">Nome</label><input id="sNome" placeholder="Rastreador cavalo" required>
            <div class="linha"><div><label for="sTipo">Tipo</label><select id="sTipo"><option value="rastreador">Rastreador</option><option value="telemetria">Telemetria</option><option value="temperatura">Temperatura</option><option value="outro">Outro</option></select></div>
            <div><label for="sForn">Formato</label><select id="sForn"><option value="generico">Genérico (JSON da Central)</option></select></div></div>
            <div id="msgSensor"></div>
            <div class="acoes"><button type="submit">Gerar credencial</button></div>
          </form>
        </details>
      </div>
    </div>
    <section id="detalhe" aria-live="polite"><div class="cartao vazio">Escolha uma viagem para ver previsão, alertas e posição em tempo real.</div></section>
  </div>
