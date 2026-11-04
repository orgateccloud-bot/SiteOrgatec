# Atendimento ao titular de dados

**Situação:** rascunho de 03/11/2026. **Base:** LGPD, arts. 18 e 19. O atendimento é sem custo (art. 18, § 5º).

## 1. Receber

Os pedidos chegam por:

- formulário de contato, assunto "Meus dados pessoais (LGPD)" (`contato/index.html?assunto=lgpd`);
- WhatsApp, enquanto a API não estiver no ar: hoje este é o caminho real;
- `dpo@orgatec.io`, quando ativado (C4).

Anote no controle da seção 6 no mesmo dia. **O prazo conta da data do pedido.**

## 2. Confirmar quem está pedindo

Peça o mínimo necessário. Em geral, basta responder pelo mesmo e-mail ou WhatsApp que consta no registro. Não peça documento a quem já é identificado por esse canal. Se pedir, apague a cópia depois de usar.

Pedido de terceiro exige procuração ou comprovação de representação.

## 3. Localizar os dados

**Formulários do site:** use o banco de produção, com as mesmas variáveis da API (`ORGATEC_BANCO`, `ORGATEC_SEGREDO_IP`).

```bash
python tools/lgpd.py titular --email pessoa@exemplo.com
```

```bash
python tools/lgpd.py titular --whatsapp 62999990000
```

A tela mostra só protocolos, tipos e datas.

**Fora do site:** procure também no portal Athenas, nos sistemas do escritório, no e-mail, no WhatsApp e em planilhas. Use o [registro de operações](registro-operacoes.md) como lista.

## 4. Responder

| Pedido | O que fazer | Prazo |
|---|---|---|
| Confirmar se há dados, ou acesso simples | Responder o que existe, em formato simplificado | Imediato (art. 19, I) |
| Acesso completo | Declaração clara e completa: origem dos dados, critérios usados e finalidade | Até 15 dias (art. 19, II) |
| Cópia ou portabilidade | Exportar e entregar por canal seguro (comando abaixo) | Até 15 dias, como referência |
| Correção | Nos formulários, eliminar o registro e pedir novo envio: o texto gravado não é editado, para não quebrar a trilha. Nos outros sistemas, corrigir direto | Assim que possível |
| Eliminação ou revogação do consentimento | Comandos abaixo, depois da checagem da seção 5 | Assim que possível |
| Cancelar alertas | O próprio link de cada mensagem resolve. Se não funcionar, use a eliminação | Imediato |
| Com quem compartilhamos | Usar [operadores.md](operadores.md) e a política de privacidade | Até 15 dias, como referência |
| Oposição ou revisão | Encaminhar ao responsável técnico | Avaliar caso a caso |

Na exportação, o arquivo tem dados pessoais. Grave fora do repositório e apague depois da entrega. A ferramenta recusa a pasta `site/` e não sobrescreve arquivos.

```bash
python tools/lgpd.py titular --email pessoa@exemplo.com --exportar C:/temp/resposta.json
```

Para eliminar, confira primeiro. Sem `--confirmar`, nada é apagado.

```bash
python tools/lgpd.py titular --email pessoa@exemplo.com --eliminar
```

```bash
python tools/lgpd.py titular --email pessoa@exemplo.com --eliminar --confirmar
```

Para eliminar só um registro, acrescente `--protocolo LD-20261103-ABC123`.

## 5. Antes de eliminar

Nem tudo pode ser apagado. Guarde o que tiver obrigação legal (art. 16), como documentos fiscais, contábeis, de folha e de prevenção à lavagem de dinheiro. Nesses casos, explique ao titular o que fica e por quê.

Se a ORGATEC for só operadora daquele dado (a folha de um cliente, por exemplo), encaminhe o pedido ao cliente controlador e avise o titular.

Se o pedido atingir um fornecedor, peça a ele a mesma providência (art. 18, § 6º).

## 6. Controle de pedidos

Mantenha esta tabela numa planilha interna, fora do git, porque ela identifica pessoas.

| Número | Data do pedido | Canal | Tipo | Identidade conferida | Resposta em | Responsável | Observações |
|---|---|---|---|---|---|---|---|

## 7. Modelos de resposta

**Sem dados:**

> Olá. Procuramos seus dados nos canais informados e não encontramos registros em nossos sistemas em [data]. Se quiser, envie outro e-mail ou telefone para uma nova busca.

**Eliminação feita:**

> Olá. Seus dados foram eliminados em [data]. Em nossos registros fica apenas um código de protocolo, sem dado pessoal, para a integridade da nossa trilha de auditoria.

**Guarda obrigatória:**

> Olá. Eliminamos [o que foi eliminado]. Precisamos manter [o que fica] por exigência de [norma], até [prazo]. Depois disso, esses dados também serão eliminados.

Em qualquer caso, informe que o titular pode peticionar à ANPD (art. 18, § 1º).
