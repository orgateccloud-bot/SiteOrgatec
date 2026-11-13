# Modelo: mapa interativo de alertas (para aprovação)

Pedido do usuário em 13/11/2026: mapas realistas, previsão do tempo, tornados no Sul, dinamismo e interatividade; "gere um modelo primeiro".

`modelo.html` é um protótipo, não é código de produção.

- **Abrir:** `python -m http.server 8430` na raiz desta pasta de trabalho e `http://localhost:8430/docs/ideias/mapa-interativo/modelo.html`.
- **De verdade no modelo:**
  - zoom e arrastar (MapLibre GL JS 4.7.1, aqui por CDN);
  - fundo de satélite e imagens GOES-East ao vivo, com animação de 2 h (NASA GIBS);
  - chuva estimada IMERG;
  - avisos reais do INMET de 12/11/2026;
  - malha do IBGE por estado, inclusive as estradas locais.
- **De teste:** os focos de fogo (`dados/`, copiados da prévia local).
- **Exemplo de tela, sem fonte ligada:** a previsão por ponto no balão e a camada "Tempo severo no Sul".
- **Telas:** pasta `telas/` (Brasil, estado, balão de previsão, Sul e celular).

Antes de virar código de produção:

- conferir os termos das fontes novas (previsão, radar e índice de tempo severo);
- hospedar o MapLibre no próprio site e ajustar a CSP (script, worker e imagens);
- no celular, o painel de camadas precisa recolher: hoje cobre boa parte do mapa.
