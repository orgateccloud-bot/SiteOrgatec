"""Gera as páginas estáticas do Hub da Reforma Tributária (site/reforma/*.html).

Uso:  python tools/gerar_hub.py
O conteúdo de cada artigo está em ARTIGOS abaixo; o cabeçalho, os CTAs e o rodapé
regulatório são comuns. Citações usam <span data-fontes="id1,id2"></span>, que
assets/js/artigo.js preenche a partir de assets/js/fontes.js (selo "pendente" incluído).
"""

from __future__ import annotations

from pathlib import Path

import layout

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "site" / "reforma"

MODELO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} | ORGATEC</title>
    <meta name="description" content="{descricao}">
    <link rel="canonical" href="https://orgatec.io/reforma/{arquivo}">
    <meta property="og:title" content="{titulo}">
    <meta property="og:description" content="{descricao}">
    <meta property="og:type" content="article">
    <link rel="icon" href="../assets/marca/favicon-32.png" sizes="32x32" type="image/png">
    <link rel="apple-touch-icon" href="../assets/marca/apple-touch-icon.png">
    <meta name="theme-color" content="#072563">
    <meta property="og:image" content="https://orgatec.io/assets/marca/og-image.png">
{tema}
    <style>
        .badge-pendente {{ background:var(--warn-soft); color:var(--warn); border:1px solid var(--warn); }}
        .prosa h2 {{ font-weight:700; color:var(--brand); font-size:1.35rem; margin:2.25rem 0 .75rem; }}
        .prosa h3 {{ font-weight:600; color:var(--ink); margin:1.5rem 0 .5rem; }}
        .prosa p, .prosa li {{ color:var(--ink); line-height:1.75; margin-bottom:.75rem; }}
        .prosa ul {{ list-style:disc; padding-left:1.25rem; }}
        .prosa ol {{ list-style:decimal; padding-left:1.25rem; }}
        .prosa table {{ width:100%; font-size:.875rem; }}
        .prosa th, .prosa td {{ text-align:left; padding:.4rem .75rem .4rem 0; border-bottom:1px solid var(--line); }}
        .cita {{ display:block; font-size:.75rem; color:var(--muted); margin-top:-.25rem; margin-bottom:1rem; }}
    </style>
    <script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{titulo}","inLanguage":"pt-BR","dateModified":"2026-10-30","author":{{"@type":"Person","name":"Robson Alain Veloso","jobTitle":"Contador — CRC-TO 002032/O-5 T-GO"}},"publisher":{{"@type":"Organization","name":"ORGATEC"}}}}</script>
</head>
<body class="text-ink font-sans antialiased com-barra-movel" data-layout="paginas">
{cabecalho}
{trilha}
    <main class="max-w-3xl mx-auto px-4 sm:px-6 py-12">
        <p class="font-mono text-xs text-brandBlue mb-2">{selo}</p>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-dark tracking-tight mb-4">{titulo}</h1>
        <p class="text-xs text-slate-500 mb-8">Atualizado em 30/10/2026 · Responsável técnico: Robson Alain Veloso, <span class="font-mono">CRC-TO 002032/O-5 T-GO</span></p>
        <article class="prosa">
{corpo}
            <h2>Base legal</h2>
            <p class="text-sm"><span data-fontes="{fontes}"></span></p>
        </article>
        <div class="mt-10 bg-white border border-blue-100 rounded-lg p-4 text-xs text-slate-500 font-mono">
            ⚠️ Aviso Legal: Conteúdo orientativo baseado na EC nº 132/2023 e na LC nº 214/2025. Não substitui parecer técnico emitido pelo contador responsável. Itens marcados como "pendente de validação" ainda não foram conferidos na fonte primária.
        </div>
        <div class="mt-8 flex flex-col sm:flex-row gap-3">
            <a href="../ferramentas/simulador.html" class="og-btn og-btn-primario og-btn-lg">Testar Simulador Tributário</a>
            <a href="https://wa.me/5562992949161" data-link="whatsapp" target="_blank" rel="noopener" class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>
        </div>
        <nav class="mt-12 border-t border-slate-200 pt-6 text-sm grid grid-cols-1 sm:grid-cols-2 gap-2" aria-label="Outros artigos">
{outros}
        </nav>
    </main>
{rodape}
{barra}
{scripts}
</body>
</html>
"""


def cita(ids: str) -> str:
    return f'<span class="cita">Fonte: <span data-fontes="{ids}"></span></span>'


ARTIGOS = [
    {
        "arquivo": "lc-214-2025.html",
        "selo": "LC nº 214/2025",
        "titulo": "LC 214/2025: a lei do IBS, da CBS e do Imposto Seletivo",
        "descricao": "Estrutura da Lei Complementar 214/2025, cronograma de transição 2026-2033, reduções de alíquota e o que já vale em 2026.",
        "fontes": "adct_125_133,lc214_2026,lc214_art127,lc214_saude,lc214_cesta,lc214_zfm,cfg_aliquota_ref",
        "corpo": f"""
            <p>A Lei Complementar nº 214, de 16 de janeiro de 2025, regulamenta a Reforma Tributária do consumo aprovada pela Emenda Constitucional nº 132/2023. Ela institui o Imposto sobre Bens e Serviços (IBS), de estados e municípios, a Contribuição Social sobre Bens e Serviços (CBS), federal, e o Imposto Seletivo (IS). Em 13/01/2026, a LC nº 227/2026 alterou vários dispositivos da LC 214; este conteúdo já considera o texto compilado.</p>
            <h2>Cronograma de transição</h2>
            <table>
                <thead><tr><th>Ano</th><th>O que acontece</th></tr></thead>
                <tbody>
                    <tr><td class="font-mono">2026</td><td>Teste: CBS 0,9% e IBS 0,1%, compensáveis com PIS/Cofins.</td></tr>
                    <tr><td class="font-mono">2027–2028</td><td>CBS em vigor (PIS/Cofins extintos); IPI zerado, exceto produtos com industrialização incentivada na ZFM; IBS a 0,1% (0,05% estadual + 0,05% municipal) e CBS reduzida em 0,1 ponto percentual.</td></tr>
                    <tr><td class="font-mono">2029–2032</td><td>ICMS e ISS caem para 9/10, 8/10, 7/10 e 6/10 das alíquotas; o IBS sobe na mesma proporção.</td></tr>
                    <tr><td class="font-mono">2033</td><td>ICMS e ISS extintos; IBS e CBS integrais.</td></tr>
                </tbody>
            </table>
            {cita("adct_125_133")}
            <h2>O que vale em 2026</h2>
            <p>As notas fiscais de contribuintes do regime regular já destacam CBS e IBS com as alíquotas de teste. O valor é compensado com PIS/Cofins; quem cumpre as obrigações acessórias fica dispensado do recolhimento. O optante do Simples Nacional não está sujeito a esse teste.</p>
            {cita("lc214_2026")}
            <h2>Alíquotas reduzidas e alíquota zero</h2>
            <ul>
                <li><strong>Redução de 30%</strong> para 18 profissões intelectuais fiscalizadas por conselho profissional (contabilidade, advocacia, engenharia, arquitetura, entre outras), com requisitos para sociedades.</li>
                <li><strong>Redução de 60%</strong> para os itens do art. 128, como educação, saúde, dispositivos médicos, medicamentos, produtos agropecuários in natura e insumos agropecuários.</li>
                <li><strong>Alíquota zero</strong> para a Cesta Básica Nacional e para hortícolas, frutas e ovos listados na lei.</li>
            </ul>
            {cita("lc214_art127,lc214_saude,lc214_educacao,lc214_agro,lc214_cesta")}
            <h2>Zona Franca de Manaus e Áreas de Livre Comércio</h2>
            <p>A lei traz regimes próprios para a ZFM e para as Áreas de Livre Comércio de Tabatinga (AM), Guajará-Mirim (RO), Boa Vista e Bonfim (RR), Macapá e Santana (AP), Brasiléia com Epitaciolândia e Cruzeiro do Sul (AC).</p>
            {cita("lc214_zfm")}
            <h2>Qual será a alíquota?</h2>
            <p>As alíquotas de referência ainda não estão fixadas. As estimativas oficiais da Secretaria Extraordinária da Reforma Tributária ficaram em 26,47% (nota de julho de 2024), com acréscimo estimado de 1,47 ponto pelas mudanças feitas na Câmara. A LC 214 prevê avaliações periódicas e, se a soma estimada para 2033 passar de 26,5%, o Executivo deve propor redução dos benefícios. Os 26,5% não são, portanto, um teto automático.</p>
            {cita("cfg_aliquota_ref")}
            <h2>O que fazer agora</h2>
            <ol>
                <li>Revisar NCM, NBS e classificação tributária de produtos e serviços.</li>
                <li>Mapear fornecedores por regime (Simples, regular, produtor não contribuinte), pois isso define o crédito.</li>
                <li>Simular preço e margem no regime pleno e no período de convivência 2029–2032.</li>
                <li>Preparar o caixa para o split payment.</li>
            </ol>
""",
    },
    {
        "arquivo": "ibs.html",
        "selo": "IBS",
        "titulo": "IBS: o imposto que substitui o ICMS e o ISS",
        "descricao": "Como funciona o Imposto sobre Bens e Serviços: cobrança no destino, transição 2029-2032, fim dos benefícios de ICMS e Fundo de Compensação.",
        "fontes": "cf_156a_destino,adct_125_133,adct_12_fundo,lc214_nao_cumulatividade",
        "corpo": f"""
            <p>O Imposto sobre Bens e Serviços (IBS) é de competência compartilhada entre estados, Distrito Federal e municípios e substituirá o ICMS e o ISS. A alíquota total de cada operação é a soma da alíquota do estado com a do município.</p>
            <h2>Cobrança no destino</h2>
            <p>O IBS é cobrado pelo somatório das alíquotas do estado e do município de destino da operação. A arrecadação passa a acompanhar o consumo, e não a localização do estabelecimento vendedor.</p>
            {cita("cf_156a_destino")}
            <h2>Transição</h2>
            <p>Em 2026, o IBS é cobrado a 0,1% como teste; em 2027 e 2028, a 0,1% (0,05% estadual e 0,05% municipal). De 2029 a 2032, o ICMS e o ISS são reduzidos a 9/10, 8/10, 7/10 e 6/10, e o IBS cresce na mesma medida até a extinção dos dois impostos em 2033.</p>
            {cita("adct_125_133")}
            <h2>Fim dos benefícios de ICMS</h2>
            <p>Incentivos de ICMS perdem efeito à medida que o imposto é reduzido. Para benefícios onerosos concedidos regularmente, a EC nº 132/2023 criou o Fundo de Compensação de Benefícios Fiscais, que compensa os titulares de 1º/01/2029 a 31/12/2032. Em Goiás, no Tocantins e no Pará, onde programas estaduais de ICMS sustentam decisões de investimento na indústria, no atacado e no agro, esse mapeamento deve começar já.</p>
            {cita("adct_12_fundo")}
            <h2>Não cumulatividade</h2>
            <p>Diferentemente do ICMS, o crédito de IBS é amplo: alcança as aquisições de bens e serviços, exceto as de uso ou consumo pessoal, condicionado ao pagamento do tributo na etapa anterior.</p>
            {cita("lc214_nao_cumulatividade")}
""",
    },
    {
        "arquivo": "cbs.html",
        "selo": "CBS",
        "titulo": "CBS: a contribuição federal que substitui PIS e Cofins",
        "descricao": "A Contribuição Social sobre Bens e Serviços a partir de 2027: fim do PIS/Cofins, IPI zerado, crédito amplo e impacto no Lucro Presumido e no Lucro Real.",
        "fontes": "adct_125_133,lc214_nao_cumulatividade,lei9718_cumulativo,lei10637_10833",
        "corpo": f"""
            <p>A Contribuição Social sobre Bens e Serviços (CBS) é o tributo federal sobre o consumo. Ela entra em vigor de forma plena em 2027, quando PIS e Cofins deixam de existir e o IPI passa a ter alíquota zero, exceto para produtos com industrialização incentivada na Zona Franca de Manaus.</p>
            {cita("adct_125_133")}
            <h2>Cronograma</h2>
            <ul>
                <li><strong>2026:</strong> alíquota de teste de 0,9%, compensável com PIS/Cofins.</li>
                <li><strong>2027 e 2028:</strong> alíquota de referência reduzida em 0,1 ponto percentual (para acomodar o IBS de 0,1%).</li>
                <li><strong>A partir de 2029:</strong> alíquota de referência integral.</li>
            </ul>
            <h2>O que muda por regime</h2>
            <h3>Lucro Presumido</h3>
            <p>PIS e Cofins cumulativos (0,65% e 3%, sem crédito) dão lugar à CBS não cumulativa. Para empresas com muitas compras de fornecedores do regime regular, o crédito pode compensar a alíquota maior; para prestadores de serviço com custo concentrado em folha, a carga tende a subir. O IRPJ e a CSLL continuam apurados pelo Presumido.</p>
            {cita("lei9718_cumulativo,lc214_nao_cumulatividade")}
            <h3>Lucro Real</h3>
            <p>PIS e Cofins não cumulativos (1,65% e 7,6%) têm créditos limitados por lista legal. Na CBS, o crédito é amplo, alcançando as aquisições em geral, exceto as de uso ou consumo pessoal, condicionado ao pagamento do tributo na etapa anterior.</p>
            {cita("lei10637_10833,lc214_nao_cumulatividade")}
            <h3>Simples Nacional</h3>
            <p>A parcela de PIS/Cofins do DAS é substituída pela CBS. O optante pode escolher apurar CBS e IBS no regime regular (o "Simples Híbrido"), opção que interessa principalmente a quem vende para outras empresas.</p>
            <p><a href="simples-hibrido.html" class="text-brandBlue underline">Entenda o Simples Híbrido →</a></p>
""",
    },
    {
        "arquivo": "split-payment.html",
        "selo": "Split Payment",
        "titulo": "Split Payment: o tributo separado no momento do pagamento",
        "descricao": "Como funciona o recolhimento de IBS e CBS na liquidação financeira (arts. 31 a 35 da LC 214/2025), a implantação gradual e o impacto no capital de giro.",
        "fontes": "lc214_split",
        "corpo": f"""
            <p>O split payment é o recolhimento do IBS e da CBS na liquidação financeira da operação. Quando o cliente paga por meio eletrônico, o prestador do serviço de pagamento separa a parcela dos tributos e a destina ao Fisco, e a empresa recebe o valor líquido.</p>
            {cita("lc214_split")}
            <h2>Procedimentos previstos</h2>
            <ul>
                <li><strong>Padrão:</strong> o valor segregado considera o débito da operação e os créditos já apropriados pelo fornecedor, consultados no momento do pagamento.</li>
                <li><strong>Simplificado:</strong> segregação por percentual fixo, com ajuste posterior; após a LC nº 227/2026, a adoção do procedimento simplificado é opcional.</li>
            </ul>
            <h2>Implantação gradual</h2>
            <p>A lei determina que ato conjunto do Comitê Gestor do IBS e da Receita Federal estabeleça a implementação gradual do split payment e permite prever hipóteses em que a adoção será facultativa. Os primeiros meios a receber o mecanismo tendem a ser os eletrônicos de alto volume, como cartões e Pix.</p>
            <h2>Efeitos práticos</h2>
            <ol>
                <li><strong>Capital de giro:</strong> o tributo deixa de transitar pelo caixa da empresa até o vencimento da guia.</li>
                <li><strong>Conciliação:</strong> é preciso casar vendas, recebimentos líquidos, créditos e valores retidos.</li>
                <li><strong>Precificação:</strong> descontos e parcelamentos passam a ser analisados sobre o valor líquido.</li>
                <li><strong>Cadastros:</strong> erros de classificação geram retenção indevida no ato do pagamento.</li>
            </ol>
""",
    },
    {
        "arquivo": "simples-hibrido.html",
        "selo": "LC 214/2025, art. 41",
        "titulo": "Simples Híbrido: IBS e CBS fora do DAS",
        "descricao": "Quando vale ao Simples Nacional apurar IBS e CBS no regime regular (LC 214/2025, art. 41): crédito ao cliente, janelas de opção em setembro e março e riscos.",
        "fontes": "lc214_art41,lc214_credito_simples,cf_146_simples,lc123_sublimite,cgsn_opcao",
        "corpo": f"""
            <p>"Simples Híbrido" é o nome dado no mercado à faculdade que a LC nº 214/2025 dá ao optante do Simples Nacional: continuar recolhendo IRPJ, CSLL, contribuição previdenciária e demais tributos pelo DAS, mas apurar IBS e CBS pelo regime regular, com débitos e créditos. A expressão não está na lei.</p>
            {cita("lc214_art41,cf_146_simples")}
            <h2>Por que isso importa para quem vende a empresas</h2>
            <p>Quem compra de uma empresa do Simples que mantém IBS e CBS no DAS só se credita do valor devido por meio do Simples, em geral bem inferior ao de um fornecedor do regime regular. Para o cliente PJ, o fornecedor do Simples fica mais caro. Ao optar pelo regime regular de IBS/CBS, a empresa passa a transferir crédito integral.</p>
            {cita("lc214_credito_simples")}
            <h2>Regras da opção</h2>
            <ul>
                <li>Vale por semestre (semestres iniciados em janeiro e em julho) e é irretratável dentro dele.</li>
                <li>É exercida em <strong>setembro</strong> (para o semestre iniciado em janeiro) e em <strong>março</strong> (para o semestre iniciado em julho), conforme a redação dada pela LC nº 227/2026. O texto original da LC 214 previa abril.</li>
                <li>Produz efeitos a partir de 1º/01/2027. A primeira janela foi setembro de 2026.</li>
                <li>Para empresas em início de atividade, segue ato do Comitê Gestor do Simples Nacional, cuja regulamentação ainda não foi conferida.</li>
            </ul>
            <p class="bg-white border border-slate-200 rounded-lg p-3 font-semibold text-dark" data-janela-simples></p>
            {cita("lc214_art41,cgsn_opcao")}
            <h2>Quando tende a valer a pena</h2>
            <ul>
                <li>Clientes predominantemente pessoas jurídicas do regime regular.</li>
                <li>Compras relevantes de fornecedores do regime regular, cujo crédito a empresa passa a aproveitar.</li>
                <li>Margem suficiente para absorver uma alíquota nominal maior que a parcela de IBS/CBS do DAS.</li>
            </ul>
            <h2>Quando tende a não valer</h2>
            <ul>
                <li>Venda majoritária a consumidor final, que não aproveita crédito.</li>
                <li>Custo concentrado em folha de salários, que não gera crédito de IBS/CBS.</li>
            </ul>
            <h2>Sublimite</h2>
            <p>Empresas acima do sublimite de R$ 3,6 milhões já recolhem ICMS e ISS fora do DAS; a partir de 2027, o IBS também fica fora do DAS nessa situação.</p>
            {cita("lc123_sublimite")}
            <p>A decisão exige reconstrução do PGDAS-D, levantamento dos créditos por fornecedor e simulação de preço. <a href="../ferramentas/simulador.html" class="text-brandBlue underline">Faça a simulação inicial →</a></p>
""",
    },
]

FONTES_PAGINA = {
    "arquivo": "fontes.html",
    "selo": "Transparência",
    "titulo": "Fontes legais citadas no site",
    "descricao": "Lista dos dispositivos legais citados pela ORGATEC no simulador, no calendário e no Hub da Reforma, com o status de conferência.",
    "fontes": "adct_125_133",
    "corpo": """
            <p>Todo dispositivo citado no site está nesta lista. Os itens marcados como "pendente de validação" ainda não foram conferidos na fonte primária pelo responsável técnico; os demais foram conferidos nos textos compilados do Planalto e no portal de normas da Receita Federal na data indicada.</p>
            <table><thead><tr><th>Dispositivo</th><th>Status</th></tr></thead><tbody data-lista-fontes></tbody></table>
""",
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    paginas = ARTIGOS + [FONTES_PAGINA]
    for p in paginas:
        outros = "\n".join(
            f'            <a href="{o["arquivo"]}" class="text-brandBlue hover:underline">{o["titulo"]}</a>'
            for o in ARTIGOS if o["arquivo"] != p["arquivo"]
        )
        html = MODELO.format(outros=outros, tema=layout.tema("../") + layout.breadcrumb([("Reforma", "reforma/index.html"), (p["titulo"], None)], "reforma/" + p["arquivo"]), cabecalho=layout.cabecalho("../", "reforma", "reforma/" + p["arquivo"]), rodape=layout.rodape("../"),
                             trilha=layout.trilha("../", [("Reforma", "reforma/index.html"), (p["titulo"], None)], "max-w-3xl"), barra=layout.barra_movel("../"),
                             scripts=layout.scripts("../", ["artigo.js"]), **p)
        (DESTINO / p["arquivo"]).write_text(html, encoding="utf-8", newline="\n")
        print("OK", p["arquivo"])


if __name__ == "__main__":
    main()
