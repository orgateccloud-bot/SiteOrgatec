"""Aplica no site as aprovações de um registro da revisão técnica (gerado por docs/revisao/revisao-tecnica.html).

O responsável técnico decide na tela e baixa o registro (JSON com audit_hash). Esta ferramenta:
  1. confere a integridade do registro (tools/conferir_revisao.py);
  2. só aceita uma aprovação se o texto atual do site tem o mesmo hash do texto que foi revisado;
  3. grava as aprovações nos arquivos de dados (reforma-itens.js, compliance-itens.js e termometro.js);
  4. revoga a aprovação de um texto que mudou depois da revisão: ele volta a "em revisão técnica";
  5. guarda uma cópia do registro em docs/revisao/registros/ (rastro de quem aprovou o quê e quando).
Pontos marcados "ajustar" continuam pendentes e saem listados com a nota do responsável.
As perguntas do termômetro e os pesos por perfil são aprovados em conjunto: só valem com todos aprovados.

Uso: python tools/aplicar_revisao.py registro.json            (simula: mostra o que mudaria)
     python tools/aplicar_revisao.py registro.json --aplicar  (grava no site)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess  # nosec B404 — só executa node com argumentos fixos
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conferir_revisao  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "site" / "assets" / "js"
REGISTROS = RAIZ / "docs" / "revisao" / "registros"
ARQUIVOS = {"reforma": "reforma-itens.js", "compliance": "compliance-itens.js"}
BLOCO = re.compile(r"(  /\* REVISOES:INICIO \*/\r?\n)(.*?)(\r?\n  /\* REVISOES:FIM \*/)", re.S)
REVISAO = re.compile(r"var REVISAO = (\{[^}\n]*\});")
PESOS = re.compile(r"(var PESOS_PERFIL = \{\r?\n    )(status: [^\n]*?)(\r?\n)")
PENDENTE_REVISAO = "{ status: 'pendente', por: null, em: null }"
PENDENTE_PESOS = "status: 'proposta', por: null, em: null,"


def hashes_atuais(js: Path = JS) -> dict:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node não encontrado no PATH")
    r = subprocess.run([node, str(RAIZ / "tools" / "revisao_hashes.js"), str(js)],  # nosec B603
                       capture_output=True, text=True, encoding="utf-8", check=False)
    if r.returncode != 0:
        raise RuntimeError(f"não consegui calcular os hashes do site: {r.stderr.strip()}")
    return json.loads(r.stdout)


def ler_aprovados(texto: str) -> dict:
    m = BLOCO.search(texto)
    if not m:
        raise RuntimeError("marcadores REVISOES:INICIO/FIM não encontrados")
    corpo = m.group(2).strip()
    return json.loads(corpo[len("var APROVADOS = "):].rstrip(";"))


def ler_revisao_termometro(texto: str) -> dict:
    m = REVISAO.search(texto)
    try:
        return json.loads(m.group(1)) if m else {}
    except ValueError:  # ainda no formato original, pendente
        return {"status": "pendente"}


def ler_pesos(texto: str) -> dict:
    m = PESOS.search(texto)
    h = re.search(r'status: "aprovada".*?hash: "([0-9a-f]{64})"', m.group(2)) if m else None
    return {"status": "aprovada", "hash": h.group(1)} if h else {"status": "proposta"}


def _grupo_aprovado(prefixo: str, atuais: dict, decisoes: dict) -> bool:
    ids = atuais[prefixo]["ids"]
    return bool(ids) and all(
        decisoes.get(i, {}).get("decisao") == "aprovada" and decisoes[i].get("conteudoHash") == atuais["itens"][i]["hash"] for i in ids)


def planejar(registro: dict, atuais: dict, gravados: dict, revisao_t: dict, pesos: dict) -> dict:
    por, em = registro["responsavel"], registro["data"]
    decisoes = {d["id"]: d for d in registro.get("decisoes", [])}
    final, revogados, ajustar, divergentes, inexistentes = {}, [], [], [], []
    for id_, g in gravados.items():  # o que já estava aprovado continua, se o texto não mudou
        atual = atuais["itens"].get(id_)
        if atual and atual["hash"] == g["hash"]:
            final[id_] = {**g, "origem": atual["origem"]}
        else:
            revogados.append(id_)
    for id_, d in decisoes.items():
        if not id_.startswith("item:"):
            continue
        atual = atuais["itens"].get(id_)
        if not atual:
            inexistentes.append(id_)
        elif d["decisao"] == "ajustar":
            ajustar.append((id_, d.get("nota", "")))
            if final.pop(id_, None) is not None:
                revogados.append(id_)
        elif d["conteudoHash"] != atual["hash"]:
            divergentes.append(id_)
        else:
            final[id_] = {"por": por, "em": em, "hash": atual["hash"], "origem": atual["origem"]}
    termometro = {}
    for nome, prefixo, atual_gravado in (("perguntas", "perguntas", revisao_t), ("pesos", "pesos", pesos)):
        ag = atuais[prefixo]["agregado"]
        if _grupo_aprovado(prefixo, atuais, decisoes):
            termometro[nome] = {"status": "aprovada", "por": por, "em": em, "hash": ag}
        elif atual_gravado.get("status") == "aprovada" and atual_gravado.get("hash") == ag and atual_gravado.get("por"):
            termometro[nome] = None  # continua como está
        elif atual_gravado.get("status") == "aprovada":
            termometro[nome] = {"status": "pendente"}  # o conjunto mudou depois da revisão
        else:
            termometro[nome] = None
    return {"final": final, "revogados": revogados, "ajustar": ajustar, "divergentes": divergentes,
            "inexistentes": inexistentes, "termometro": termometro}


def _js_obj(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False)


def escrever(plano: dict, js: Path = JS) -> None:
    for origem, nome in ARQUIVOS.items():
        arq = js / nome
        t = arq.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in t else "\n"
        mine = {i: {k: v for k, v in a.items() if k != "origem"} for i, a in sorted(plano["final"].items()) if a["origem"] == origem}
        corpo = "var APROVADOS = " + json.dumps(mine, ensure_ascii=False, indent=2, sort_keys=True) + ";"
        corpo = nl.join("  " + linha for linha in corpo.split("\n"))
        t = BLOCO.sub(lambda m: m.group(1) + corpo + m.group(3), t, count=1)
        arq.write_bytes(t.encode("utf-8"))
    arq = js / "termometro.js"
    t = arq.read_bytes().decode("utf-8")
    perg, pesos = plano["termometro"].get("perguntas"), plano["termometro"].get("pesos")
    if perg:
        novo = _js_obj(perg) if perg["status"] == "aprovada" else PENDENTE_REVISAO
        t = REVISAO.sub(lambda m: "var REVISAO = " + novo + ";", t, count=1)
    if pesos:
        linha = (f'status: "aprovada", por: {json.dumps(pesos["por"], ensure_ascii=False)}, em: "{pesos["em"]}", hash: "{pesos["hash"]}",'
                 if pesos["status"] == "aprovada" else PENDENTE_PESOS)
        t = PESOS.sub(lambda m: m.group(1) + linha + m.group(3), t, count=1)
    arq.write_bytes(t.encode("utf-8"))


def aplicar(registro: dict, js: Path = JS, registros: Path = REGISTROS, gravar: bool = False) -> dict:
    erros = conferir_revisao.conferir(registro)
    if erros:
        raise ValueError("registro inválido: " + "; ".join(erros))
    atuais = hashes_atuais(js)
    gravados = {}
    for nome in ARQUIVOS.values():
        gravados.update(ler_aprovados((js / nome).read_bytes().decode("utf-8")))
    t = (js / "termometro.js").read_bytes().decode("utf-8")
    plano = planejar(registro, atuais, gravados, ler_revisao_termometro(t), ler_pesos(t))
    plano["total_itens"] = sum(1 for i in atuais["itens"] if i.startswith("item:"))
    if gravar:
        escrever(plano, js)
        registros.mkdir(parents=True, exist_ok=True)
        (registros / f"revisao-{registro['data']}-{registro['audit_hash'][:8]}.json").write_text(
            json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return plano


def resumo(plano: dict) -> list[str]:
    linhas = [f"pontos aprovados no site: {len(plano['final'])} de {plano['total_itens']}"]
    for nome, rotulo in (("perguntas", "perguntas do termômetro"), ("pesos", "pesos por perfil")):
        t = plano["termometro"].get(nome)
        if t:
            linhas.append(f"{rotulo}: " + ("aprovados" if t["status"] == "aprovada" else "voltam a pendente (o conjunto mudou)"))
    for id_ in plano["revogados"]:
        linhas.append(f"REVOGADO (o texto mudou depois da revisão ou voltou para ajuste): {id_}")
    for id_ in plano["divergentes"]:
        linhas.append(f"NÃO APROVADO (o texto mudou depois da revisão): {id_}")
    for id_ in plano["inexistentes"]:
        linhas.append(f"IGNORADO (já não existe no site): {id_}")
    for id_, nota in plano["ajustar"]:
        linhas.append(f"AJUSTAR {id_}: {nota}")
    return linhas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("registro", type=Path)
    ap.add_argument("--aplicar", action="store_true", help="grava no site (sem isso, só simula)")
    a = ap.parse_args(argv)
    try:
        plano = aplicar(json.loads(a.registro.read_text(encoding="utf-8")), gravar=a.aplicar)
    except (ValueError, RuntimeError) as erro:
        print(erro)
        return 1
    print("\n".join(resumo(plano)))
    print("gravado no site." if a.aplicar else "simulação: nada foi gravado. Rode de novo com --aplicar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
