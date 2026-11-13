# MapLibre GL JS 4.7.1

Biblioteca de mapas do mapa interativo da Janela do Transporte (`assets/js/janela-transporte-gl.js`). Licença BSD-3-Clause (`LICENSE.txt`).

- Origem: pacote `maplibre-gl@4.7.1` do npm (`https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-4.7.1.tgz`), integridade
  conferida em 13/11/2026: `sha512-lgL7XpIwsgICiL82ITplfS7IGwrB1OJIw/pCvprDp2dhmSSEBgmPzYRvwYYYvJGJD7fxUv1Tvpih4nZ6VrLuaA==`.
- Arquivos copiados sem alteração de `dist/`: `maplibre-gl-csp.js` e `maplibre-gl-csp-worker.js` (versão sem `eval` e sem
  worker em `blob:`, que roda com `script-src 'self'`) e `maplibre-gl.css`.
- A pasta leva a versão no nome e é servida com cache longo (`tools/preparar_firebase.py`): para atualizar, crie uma pasta nova.
