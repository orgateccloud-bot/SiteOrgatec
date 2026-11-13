/* Catálogo de itens prontos para o painel do grupo LOCAR. É público e genérico: só normas e datas que o site já conferiu
   (cada item cita ids de fontes.js). Nada daqui é dado de cliente. Prazo não conferido fica como `prazoAConfirmar`, sem data inventada.
   Para acrescentar um modelo: confira o dispositivo na fonte oficial, registre a fonte em fontes.js e só então inclua aqui.
   Todo item que a equipe adiciona ao painel mostra o selo de revisão técnica (V1) até o responsável técnico aprovar.
   perfil: transporte | rural | simples | todos (ajuda a filtrar o que sugerir para cada entidade). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else (root.Orgatec = root.Orgatec || {}).locarModelos = factory();
})(this, function () {
  'use strict';

  var MODELOS = [
    { id: 'ato_ibs_cbs_documentos', tipo: 'evento_reforma', perfil: 'transporte', prazo: '2026-08-03', prazoAConfirmar: false,
      titulo: 'Campos de IBS e CBS obrigatórios no CT-e, CT-e OS e MDF-e', fontes: ['ato_conjunto_4_2026'],
      nota: 'Vale para o Simples Nacional a partir de 01/01/2027.' },
    { id: 'ciot_obrigatorio', tipo: 'evento_reforma', perfil: 'transporte', prazo: '2026-09-18', prazoAConfirmar: false,
      titulo: 'Registro no CIOT obrigatório em toda operação remunerada de transporte', fontes: ['res_antt_6090', 'lei13703'] },
    { id: 'rntrc_revalidacao', tipo: 'obrigacao', perfil: 'transporte', prazo: null, prazoAConfirmar: true,
      titulo: 'Revalidar o RNTRC (revalidação anual)', fontes: ['lei11442', 'antt_rntrc'],
      nota: 'O dia da revalidação depende do registro de cada transportador; confirme na ANTT.' },
    { id: 'piso_frete_atualizacao', tipo: 'evento_reforma', perfil: 'transporte', prazo: '2027-01-20', prazoAConfirmar: false,
      titulo: 'ANTT atualiza os pisos mínimos de frete (até 20/01 e 20/07 de cada ano)', fontes: ['lei13703'] },
    { id: 'piscofins_escrituracao', tipo: 'obrigacao', perfil: 'todos', prazo: '2026-12-31', prazoAConfirmar: true,
      titulo: 'Registrar na escrituração os créditos de PIS e Cofins ainda não apropriados', fontes: ['lc214_saldo_piscofins', 'adct_126'],
      nota: 'Os saldos precisam estar registrados na escrituração quando PIS e Cofins forem extintos (LC 214, art. 378, II). O corte de 31/12/2026 é uma conta a partir da extinção em 2027 e precisa de confirmação.' },
    { id: 'aliquota_cbs_senado', tipo: 'evento_reforma', perfil: 'todos', prazo: null, prazoAConfirmar: true,
      titulo: 'Senado fixa a alíquota de referência da CBS de 2027 (cálculo do TCU: 11,3%)', fontes: ['lc214_aliquota_senado', 'tcu_cbs_2027', 'senado_cbs_2027'],
      nota: 'Trate os 11,3% como cenário de planejamento até a resolução. As fontes citam 15/12 e 22/12; a LC 214, art. 349, usa o cálculo do TCU se o Senado passar de 22/12.' },
    { id: 'cbs_2027', tipo: 'evento_reforma', perfil: 'todos', prazo: '2027-01-01', prazoAConfirmar: false,
      titulo: 'CBS passa a ser cobrada; PIS e Cofins são extintos', fontes: ['adct_126'] },
    { id: 'cnpj_produtor_pf_2027', tipo: 'evento_reforma', perfil: 'rural', prazo: '2027-01-01', prazoAConfirmar: false,
      titulo: 'CNPJ e documento fiscal para o produtor rural pessoa física', fontes: ['dec13075_2026'] },
    { id: 'funrural_opcao_folha', tipo: 'obrigacao', perfil: 'rural', prazo: null, prazoAConfirmar: true,
      titulo: 'Decidir a opção do Funrural pela folha (feita com o pagamento da contribuição sobre a folha de janeiro)', fontes: ['lei8212_funrural'],
      nota: 'A opção é irretratável no ano; o vencimento da contribuição de janeiro precisa de confirmação.' },
    { id: 'simples_opcao_regime_regular', tipo: 'evento_reforma', perfil: 'simples', prazo: null, prazoAConfirmar: true,
      titulo: 'Janela de opção do Simples pelo regime regular de IBS e CBS (setembro e março)', fontes: ['lc214_art41'],
      nota: 'A opção é semestral e produz efeitos a partir de 01/01/2027.' }
  ];

  var porId = {};
  MODELOS.forEach(function (m) { porId[m.id] = m; });

  /* Cópia pronta para enviar à API (POST /api/locar/itens). */
  function paraItem(modelo, entidadeId) {
    var item = { tipo: modelo.tipo, titulo: modelo.titulo, prazo: modelo.prazo, prazo_a_confirmar: !!modelo.prazoAConfirmar,
      responsavel: 'equipe', status: 'a_fazer', fonte_id: modelo.fontes[0], modelo_id: modelo.id };
    if (entidadeId) item.entidade_id = entidadeId;
    return item;
  }

  function doPerfil(perfil) {
    return MODELOS.filter(function (m) { return !perfil || perfil === 'todos' || m.perfil === perfil || m.perfil === 'todos'; });
  }

  return { MODELOS: MODELOS, porId: porId, paraItem: paraItem, doPerfil: doPerfil };
});
