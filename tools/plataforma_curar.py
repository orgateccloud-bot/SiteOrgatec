"""Reduz o grafo de código do Graphify ao nível de módulo, para a página solucoes/plataforma.html.

Uso:  python tools/plataforma_curar.py --orgconc <graph.json do OrgConc>
      (--orgaudi <graph.json do OrgAudi> só quando o OrgAudi voltar a ser público; ver "publico" em SISTEMAS)

Gere cada graph.json no repositório do sistema, só com código e sem nenhum modelo de IA:
    GRAPHIFY_BACKEND=none GRAPHIFY_QUERY_LOG_DISABLE=1 graphify extract . --code-only --no-viz

O que sai em tools/plataforma_grafo.json é o que vai a público, e só isto: nome público de cada módulo, quantos arquivos e
símbolos ele tem e quantas ligações de código vão de um módulo a outro. Nomes de arquivo, de função e de classe, caminhos,
comentários e trechos de código ficam de fora. Arquivo fora de MODULOS também fica de fora (é o filtro de entrada:
o que não está listado aqui não aparece, mesmo que entre no grafo).
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "plataforma_grafo.json"
LIGACAO_MINIMA = 3  # ligações abaixo disso são ruído no desenho
IGNORAR = {"contains", "method", "rationale_for"}  # estrutura interna de um mesmo arquivo, não ligação entre módulos

# (prefixo do caminho no repositório, id público). O primeiro prefixo que casar vence: do mais específico ao mais geral.
# "publico": só os sistemas marcados como públicos vão para o JSON e para a página.
SISTEMAS = {
    "orgconc": {
        "publico": True,
        "nome": "Conciliação bancária",
        "pagina": "solucoes/conciliacao.html",
        "modulos": {
            "entrada": ("Rotas da API", 0, "Recebem os pedidos da tela: envio de extrato, conferência, laudo, login."),
            "app": ("Aplicação e contratos", 0, "Inicialização do sistema e formato dos dados trocados com a tela."),
            "casos": ("Casos de uso", 1, "Fluxos de negócio, como cadastrar um cliente ou listar conciliações."),
            "servicos": ("Serviços", 1, "Laudo, planilha, fila de tarefas, mascaramento de dados e trilha de auditoria."),
            "motores": ("Motores de conferência", 2, "Cruzam banco e contabilidade e apontam divergências por severidade."),
            "leitura": ("Leitura de extratos", 2, "Interpretam OFX, PDF, CSV e XML de diferentes bancos."),
            "dominio": ("Domínio", 2, "Conceitos do negócio: conta, lançamento, valor, período."),
            "nucleo": ("Núcleo", 3, "Configuração, limites de uso e métricas de funcionamento."),
            "dados": ("Banco de dados", 3, "Tabelas com separação por escritório e registro de auditoria."),
        },
        "prefixos": [("api/routers/", "entrada"), ("api/usecases/", "casos"), ("api/services/", "servicos"),
                     ("api/matchers/", "motores"), ("api/parsers/", "leitura"), ("api/domain/", "dominio"),
                     ("api/core/", "nucleo"), ("api/db/", "dados"), ("api/infra/", "dados"), ("api/", "app")],
    },
    "orgaudi": {
        # Fora da página por decisão do usuário em 13/11/2026: o OrgAudi é de uso interno. O mapeamento fica aqui para,
        # quando ele puder aparecer, bastar trocar para True e rodar o curador com --orgaudi.
        "publico": False,
        "nome": "Auditoria forense rural",
        "pagina": "solucoes/auditoria-rural.html",
        "modulos": {
            "entrada": ("Rotas da API", 0, "Recebem os pedidos da equipe: envio do relatório, auditoria, laudo."),
            "app": ("Aplicação", 0, "Inicialização do sistema e dependências comuns."),
            "acesso": ("Acesso e controle", 1, "Login, limites de uso e métricas."),
            "contratos": ("Contratos de dados", 1, "Formato dos dados de auditoria, clientes e laudos."),
            "servicos": ("Serviços de auditoria", 1, "Testes de risco, cruzamentos e montagem dos achados."),
            "orquestra": ("Orquestração da leitura", 2, "Coordena a leitura das notas e a análise."),
            "leitura": ("Leitura de NFA-e", 2, "Interpreta o relatório da SEFAZ, com regras por estado."),
            "laudo": ("Motor do laudo PDF", 3, "Gera o laudo com achados por severidade e apurações."),
            "infra": ("Banco e integração com IA", 3, "Gravação dos resultados e cliente do modelo de IA."),
        },
        "prefixos": [("api/routes/", "entrada"), ("api/auth/", "acesso"), ("api/middleware/", "acesso"),
                     ("api/observability/", "acesso"), ("api/schemas/", "contratos"), ("api/services/", "servicos"),
                     ("api/", "app"), ("nfa_extractor/application/", "orquestra"), ("nfa_extractor/infrastructure/", "infra"),
                     ("nfa_extractor/", "leitura"), ("pdf_engine/", "laudo")],
    },
}


def _modulo(caminho: str, prefixos: list[tuple[str, str]]) -> str | None:
    caminho = caminho.replace("\\", "/")
    if "/_legacy/" in caminho or caminho.startswith("_legacy/"):
        return None
    for prefixo, mod in prefixos:
        if caminho.startswith(prefixo):
            return mod
    return None


def curar(grafo: dict, cfg: dict) -> dict:
    arquivo = {n["id"]: n.get("source_file") or "" for n in grafo["nodes"]}
    mod_no = {i: _modulo(f, cfg["prefixos"]) for i, f in arquivo.items()}
    arquivos = {m: set() for m in cfg["modulos"]}
    simbolos = Counter()
    for i, m in mod_no.items():
        if m:
            arquivos[m].add(arquivo[i])
            simbolos[m] += 1
    ligacoes, confianca = Counter(), Counter()
    for e in grafo["links"]:
        if e.get("relation") in IGNORAR:
            continue
        a, b = mod_no.get(e["source"]), mod_no.get(e["target"])
        if a and b and a != b:
            ligacoes[(a, b)] += 1
            confianca[(a, b, e.get("confidence") == "EXTRACTED")] += 1
    return {
        "nome": cfg["nome"],
        "pagina": cfg["pagina"],
        "modulos": [{"id": m, "nome": n, "camada": c, "texto": t, "arquivos": len(arquivos[m]), "simbolos": simbolos[m]}
                    for m, (n, c, t) in cfg["modulos"].items() if arquivos[m]],
        "ligacoes": [{"de": a, "para": b, "total": t, "lidas": confianca[(a, b, True)]}
                     for (a, b), t in sorted(ligacoes.items(), key=lambda x: -x[1]) if t >= LIGACAO_MINIMA],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    publicos = [chave for chave, cfg in SISTEMAS.items() if cfg["publico"]]
    for chave in SISTEMAS:
        ap.add_argument(f"--{chave}", required=chave in publicos, type=Path,
                        help=None if chave in publicos else "ignorado enquanto o sistema não for público")
    ap.add_argument("--versao", default="", help="versão do Graphify usada (graphify --version)")
    args = ap.parse_args()
    saida = {"gerado": date.today().isoformat(), "graphify": args.versao, "sistemas": {}}
    for chave in publicos:
        grafo = json.loads(getattr(args, chave).read_text(encoding="utf-8"))
        saida["graphify"] = saida["graphify"] or (grafo.get("graph") or {}).get("graphify_version", "")
        saida["sistemas"][chave] = curar(grafo, SISTEMAS[chave])
    DESTINO.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("OK", DESTINO)


if __name__ == "__main__":
    main()
