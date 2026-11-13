# Painel do grupo LOCAR (v0.1)

- **Situação:** aprovada e junta na `desenvolvimento` em 12/11/2026; **desligado por padrão** e sem dado real. Falta lançar e, depois, ligar (T30).
- **Branch:** `ideia/locar-painel` (já integrada e removida)
- **Prévia:** ainda não gerada (`python tools/previa.py`, só com autorização para criar o canal). A prévia do Hosting não liga a API de produção com o painel, então o funcionamento se vê localmente com `ORGATEC_LOCAR=1 ORGATEC_LOCAR_DEMO=1`.

## Problema

O módulo LOCAR (03/11/2026) é só uma porta de entrada. O grupo e a equipe da ORGATEC precisam ver e atualizar, num lugar só, prazos, obrigações e marcos da reforma por empresa, com acesso por login, permissão por pessoa e trilha de auditoria.

## Público

Equipe da ORGATEC (primeiro) e, depois, a diretoria do grupo. Transportadores e bancos ficam para fases seguintes.

## Proposta

- **Reuso do que existe:** login Firebase e API do Cloud Run (`orgatec-api`) da Central de Viagem, com declarações próprias (`locar_grupo`, `locar_papel`): a mesma conta pode ter os dois módulos.
- **Backend** `backend/locar/`: grupos, entidades (empresa ou produtor pessoa física, com ciclo de vida e sucessora), itens (obrigação, marco da reforma, marco societário), acessos, trilha encadeada e API `/api/locar`, atrás de `ORGATEC_LOCAR=1`.
- **Página** `locar/painel.html` (`noindex`, fora do menu e do mapa), em `/locar/` para ter a própria CSP, que só deixa falar com o Firebase Authentication. A página pública `cliente/locar.html` continua sem dado e ganhou o botão de entrada.
- **Ferramentas:** `tools/locar_usuario.py` (acesso por usuário, mescla as declarações) e `tools/locar_carregar.py` (carga de arquivo **fora do git**, simulação por padrão, nunca apaga). Correção em `tools/transporte_usuario.py`, que sobrescrevia todas as declarações.
- **Catálogo** `site/assets/js/locar-modelos.js`: só itens já conferidos, com fonte; prazo não confirmado fica "a confirmar".

## Fontes e validação

Os itens do catálogo citam ids de `fontes.js` (LC 214/2025, ADCT, Ato Conjunto RFB/CGIBS 4/2026, Res. ANTT 6.090/2026, Leis 11.442/2007, 13.703/2018 e 8.212/1991, Decreto 13.075/2026, TCU). Todos entram com o selo "em revisão técnica" até a revisão (V1). Base legal e retenção da trilha: `docs/lgpd/locar-grupo.md` (V30). Nenhum dado do grupo (nomes, CNPJ, valores, honorários) entra no repositório.

## Pronto quando

- Testes de isolamento entre grupos, papéis, entidade sensível e trilha passam, e o contrato dos três repositórios também (Firestore no emulador).
- Painel confere em computador e celular, nas paletas escura e clara, e nos três navegadores de teste.
- **Para ligar com dado real (Fase 2, fora desta ideia):** aprovação do usuário, V30 e D30 resolvidas, provedor E-mail/senha do Authentication conferido, carga a partir do arquivo privado e acesso da equipe concedido.

## Atualização de 13/11/2026: Operação do grupo (`ideia/locar-operacao`)

- Seção **Operação do grupo** no painel, com três cartões:
  - **Tempo nas regiões do grupo:** os polos da Janela de Campo onde o grupo opera (`polos` gravados no grupo pela carga; sem eles, os polos de GO, TO e PA). Mostra o dia, a janela de pulverização, os próximos 3 dias e o crédito do MET Norway (CC BY 4.0). Boletim de outro dia aparece com selo.
  - **Alertas nas rodovias:** avisos meteorológicos vigentes do INMET e focos de fogo da NASA FIRMS, do resumo público `/api/transporte/alertas-publicos`, com link para o mapa.
  - **Central de Viagem:** atalhos para a Central e o portal de viagens.
- O login do painel grava o token também na chave da Central: a mesma conta abre a Central sem novo login. A Central continua exigindo as próprias permissões (`transportadora_id` e `papel`), dadas por `tools/transporte_usuario.py`.
- Sem dado novo do grupo no repositório: os polos são ids públicos da Janela de Campo.
