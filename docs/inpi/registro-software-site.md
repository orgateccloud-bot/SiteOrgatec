# Registro do programa de computador do site e da API no INPI (e-Software)

- **Data:** 14/11/2026
- **Situação:** pacote e hash gerados; falta o protocolo pela empresa (exige certificado digital ICP-Brasil e pagamento).
- **Base legal:** Lei 9.609/1998. A proteção existe sem registro (art. 2º, § 3º); o registro prova autoria e data.
  Prazo de 50 anos, contados de 1º de janeiro do ano seguinte ao da publicação (art. 2º, § 2º).

## O que foi gerado

| Item | Valor |
|---|---|
| Programa | ORGATEC.IO — site e API (simulador tributário, gerador de páginas, Janela de Campo, Central de Viagem, painel LOCAR, rotinas de alertas e publicação) |
| Versão registrada | tag `publicado-20261114-1114` (a que está em orgatec.io em 14/11/2026) |
| Pacote | `D:\01_Projetos_Ativos\SiteOrgatec-dados-privados\inpi\orgatec-io-site-api-publicado-20261114-1114.tar` (164 arquivos, cerca de 2 MB) |
| **Resumo hash (SHA-512)** | `91cf162e3d9e50946fe09102c7e1a9e9545964c7eec3c60fac5e26b82e2df99bcfbe1ad942b67a04a1682e6d9ce576bb8b7df0fef0e4ad52d2ab00e3a6cd3c8e` |
| Manifesto | `.manifesto.csv` na mesma pasta: cada arquivo com tamanho e SHA-256 |

O pacote é montado por `tools/inpi_software.py` a partir da tag, com ordem, datas e permissões fixas. Rodar de novo na
mesma tag dá o mesmo hash:

```bash
python tools/inpi_software.py --ref publicado-20261114-1114
```

**Entra no pacote (código próprio):** `backend/`, `tools/`, `site/assets/js/`, `site/assets/css/` (menos o CSS gerado
pelo Tailwind), `Dockerfile`, `.dockerignore`, `firebase.json`, `firestore.rules`, `firestore.indexes.json` e
`tailwind.config.js`.

**Fica de fora (terceiros ou gerado):** MapLibre GL (`site/assets/vendor/`, licença BSD), fontes tipográficas
(`site/assets/fontes/`), `tailwind.css` (gerado pelo Tailwind, MIT), páginas HTML geradas, dados públicos de terceiros
(`site/assets/geo/`, IBGE), documentos e testes. Bibliotecas Python instaladas pelo `requirements.txt` não estão no
pacote.

## Guarda do pacote (obrigatório)

O INPI só guarda o hash. Se o arquivo se perder ou mudar um byte, não há como provar o que foi registrado.

1. Copiar a pasta `SiteOrgatec-dados-privados\inpi\` para dois lugares fora deste computador (por exemplo, o Drive da
   empresa e um disco externo).
2. Não abrir o `.tar` para editar. Para conferir, recalcular o hash (comando acima) e comparar com o `.sha512`.
3. A tag `publicado-20261114-1114` está no GitHub e também permite remontar o pacote.

## Dados para o formulário do e-Software

| Campo | Preencher com |
|---|---|
| Titular | RAV LTDA, CNPJ 13.155.211/0001-45, Av. Ministro Alfredo Nasser, 727, Centro, Formoso-GO, CEP 76470-000 |
| Título do programa | ORGATEC.IO — Plataforma de Inteligência Tributária (site e API) |
| Data de criação | a data mais antiga que a empresa puder provar; o histórico do git começa em 03/11/2026 (`de31368`) |
| Data de publicação | 03/11/2026 (primeira publicação registrada, tag `publicado-20261103-2054`), salvo prova de publicação anterior |
| Linguagens | Python, JavaScript, HTML, CSS |
| Campo de aplicação | escolher na tabela do formulário as opções de administração e finanças, contabilidade e tributação; se houver, também transporte e agropecuária |
| Tipo de programa | escolher na tabela do formulário as opções de aplicativo e de aplicação na internet; se houver, também banco de dados e comunicação de dados |
| Algoritmo do hash | SHA-512 |
| Resumo hash | o valor da tabela acima |
| Derivação | não (primeiro registro); versões novas importantes podem ser registradas depois como programa derivado |
| Autores | **a preencher pela empresa:** nome, CPF, nacionalidade e endereço de cada pessoa que criou o programa |

**Autores e titularidade.** O titular é a empresa: o programa feito por empregado ou contratado no exercício do contrato
pertence ao empregador (Lei 9.609/1998, art. 4º). Para quem não é empregado (sócio, prestador), ter um termo de cessão
dos direitos à RAV LTDA. O código foi escrito com apoio de ferramenta de IA (Claude, da Anthropic), sob direção,
revisão e aprovação da equipe: os autores a declarar são as pessoas que definiram, revisaram e aprovaram o programa.
Os commits ficam em nome da conta ORGATEC; alguns trazem a linha "Co-Authored-By" da ferramenta.

## Passo a passo do protocolo

1. Entrar no e-INPI com o login da empresa.
2. Emitir e pagar a GRU do serviço de pedido de registro de programa de computador (com o desconto de microempresa, se o
   sistema oferecer).
3. Preencher o formulário do e-Software com os dados acima.
4. Baixar a **Declaração de Veracidade** gerada pelo sistema, assinar com certificado digital ICP-Brasil (e-CNPJ da
   empresa ou e-CPF do representante ou procurador) e anexar.
5. Protocolar. Pelo que o INPI informa, o certificado de registro sai em poucos dias úteis e é publicado na RPI.

## Próximos registros com a mesma ferramenta

- **Versões novas do site:** quando houver mudança grande, gerar o pacote da nova tag e registrar como derivação.
- **OrgConc e os demais sistemas:** copiar `tools/inpi_software.py` para o repositório de cada um e ajustar as listas
  `INCLUIR` e `EXCLUIR`.
