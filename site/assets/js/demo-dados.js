/* GERADO por tools/gerar_demo.py a partir de orgatec_io_modelos_testes.xlsx — não edite à mão.
   Dados FICTÍCIOS de homologação; IPs mascarados (LGPD). */
(function (root) {
  var dados = {
    "origem": "orgatec_io_modelos_testes.xlsx",
    "capturaXml": [
      {
        "id": "TRX-2026-001",
        "cnpj": "07.346.512/0001-90",
        "emitente": "Comércio Atacadista Brasil S/A",
        "uf": "GO",
        "chave": "52261007346512000190550010000254121102548912",
        "tipo": "NF-e",
        "valor": 45890.5,
        "data": "2026-10-28",
        "status": "Sincronizado SEFAZ-GO",
        "lgpd": "Conforme"
      },
      {
        "id": "TRX-2026-002",
        "cnpj": "12.456.789/0001-44",
        "emitente": "Logística Tocantins Transportes Ltda",
        "uf": "TO",
        "chave": "17261012456789000144570020000124581014785236",
        "tipo": "CT-e",
        "valor": 12450.0,
        "data": "2026-10-29",
        "status": "Sincronizado SEFAZ-TO",
        "lgpd": "Conforme"
      },
      {
        "id": "TRX-2026-003",
        "cnpj": "33.987.123/0001-88",
        "emitente": "Indústria Paraense de Metais S/A",
        "uf": "PA",
        "chave": "15261033987123000188550030000895621123457891",
        "tipo": "NF-e",
        "valor": 128900.0,
        "data": "2026-10-29",
        "status": "Sincronizado SEFAZ-PA",
        "lgpd": "Conforme"
      },
      {
        "id": "TRX-2026-004",
        "cnpj": "45.123.789/0001-10",
        "emitente": "Tech Solutions SP Ltda",
        "uf": "SP",
        "chave": "35261045123789000110550010000045121098765432",
        "tipo": "NFS-e",
        "valor": 8500.0,
        "data": "2026-10-30",
        "status": "Sincronizado SEFAZ-SP",
        "lgpd": "Conforme"
      }
    ],
    "protocolos": [
      {
        "protocolo": "PRT-8801",
        "cnpj": "12.345.678/0001-99",
        "uf": "GO",
        "departamento": "Fiscal",
        "solicitacao": "Emissão Guia DAS (Simples Nacional)",
        "competencia": "10/2026",
        "status": "Concluído",
        "sla": "2h",
        "acao": "Download efetuado pelo cliente",
        "auditoria": {
          "ip": "177.18.***.***",
          "ipHash": "3b7ad708",
          "mfa": true
        }
      },
      {
        "protocolo": "PRT-8802",
        "cnpj": "98.765.432/0001-11",
        "uf": "TO",
        "departamento": "Departamento Pessoal",
        "solicitacao": "Envio Folha de Pagamento e Encargos",
        "competencia": "10/2026",
        "status": "Em Andamento",
        "sla": "24h",
        "acao": "Aguardando validação de rubricas",
        "auditoria": {
          "ip": "187.120.***.***",
          "ipHash": "dec04495",
          "mfa": true
        }
      },
      {
        "protocolo": "PRT-8803",
        "cnpj": "44.555.666/0001-22",
        "uf": "PA",
        "departamento": "Contábil",
        "solicitacao": "Balancete Periódico e Relatório Gerencial",
        "competencia": "Q3/2026",
        "status": "Concluído",
        "sla": "12h",
        "acao": "Visualizado com log de segurança",
        "auditoria": {
          "ip": "200.150.***.***",
          "ipHash": "b51f9b6e",
          "mfa": true
        }
      },
      {
        "protocolo": "PRT-8804",
        "cnpj": "11.222.333/0001-44",
        "uf": "SP",
        "departamento": "Societário",
        "solicitacao": "Alteração Contratual / DBE Receita Federal",
        "competencia": "Atual",
        "status": "Em Análise",
        "sla": "48h",
        "acao": "Protocolado na Junta Comercial",
        "auditoria": {
          "ip": "201.88.***.***",
          "ipHash": "18ddc83d",
          "mfa": true
        }
      }
    ]
  };
  if (typeof module === 'object' && module.exports) module.exports = dados;
  else (root.Orgatec = root.Orgatec || {}).demo = dados;
})(this);
