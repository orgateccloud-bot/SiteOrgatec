"""Carrega entidades, itens e acessos do grupo LOCAR no banco a partir de um arquivo JSON FORA do repositório.

  python tools/locar_carregar.py --arquivo D:\\...\\SiteOrgatec-dados-privados\\locar\\carga.json --listar
  python tools/locar_carregar.py --arquivo ...                    (simulação: mostra o que faria)
  python tools/locar_carregar.py --arquivo ... --confirmar        (grava)
  python tools/locar_carregar.py --arquivo ... --confirmar --sobrescrever   (também atualiza o que já existe)

Banco: ORGATEC_LOCAR_BANCO (memoria, sqlite, firestore) e, para o Firestore, ORGATEC_FIRESTORE_PROJETO, com
`gcloud auth application-default login`. Sem a variável o banco é a memória: serve para validar o arquivo, mas nada persiste.

Regras (padrão de migração: nunca apagar, simular antes de gravar, repetir sem estragar):
  - O arquivo precisa estar fora de qualquer repositório git; dentro de um, a ferramenta recusa. Dados reais do grupo (nomes,
    CNPJ, prazos) nunca entram no git nem em `site/`.
  - Simulação por padrão. Sem --sobrescrever, o que já existe fica como está (o painel pode ter marcado um item como entregue).
  - Nada é apagado. Ids estáveis tornam a carga repetível.
  - Documento: o campo `documento` (CNPJ ou CPF) é mascarado aqui e só a versão mascarada vai para o banco.
  - A saída mostra só ids e contagens, nunca nomes.
  - Cada registro gravado entra na trilha de auditoria do grupo (usuário `carga-local`).

Formato do arquivo: ver docs/locar/modelo-carga.exemplo.json (dados fictícios).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator  # noqa: E402

from backend.locar.dominio import AcessoEntrada, EntidadeEntrada, GrupoEntrada, ItemEntrada  # noqa: E402
from backend.locar.erros import NaoEncontrado  # noqa: E402
from backend.locar.repositorio_locar import RepositorioBase, criar_repositorio  # noqa: E402

USUARIO_CARGA = "carga-local"


def mascarar_documento(bruto: str) -> str:
    """CNPJ mantém só filial e verificador; CPF sai todo mascarado. Qualquer outro tamanho é recusado."""
    d = re.sub(r"\D", "", bruto)
    if len(d) == 14:
        return f"**.***.***/{d[8:12]}-{d[12:14]}"
    if len(d) == 11:
        return "***.***.***-**"
    raise ValueError("documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos")


class EntidadeCarga(EntidadeEntrada):
    documento: str | None = None

    @model_validator(mode="after")
    def _mascarar(self) -> "EntidadeCarga":
        if self.documento is not None:
            self.documento_mascarado = mascarar_documento(self.documento)
            self.documento = None  # o dado bruto não sai deste objeto
        return self


class Carga(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    leia: str | None = Field(default=None, alias="_leia")  # comentário do modelo de exemplo; ignorado
    grupo: GrupoEntrada
    entidades: list[EntidadeCarga] = []
    itens: list[ItemEntrada] = []
    acessos: list[AcessoEntrada] = []

    @model_validator(mode="after")
    def _coerencia(self) -> "Carga":
        ids = [e.id for e in self.entidades]
        if len(ids) != len(set(ids)):
            raise ValueError("há entidades com o mesmo id")
        conhecidas = set(ids)
        for e in self.entidades:
            if e.sucessora_id and e.sucessora_id not in conhecidas:
                raise ValueError(f"sucessora_id '{e.sucessora_id}' não é uma entidade do arquivo")
        itens = [i.id for i in self.itens]
        if any(i is None for i in itens):
            raise ValueError("todo item da carga precisa de id (é o que torna a carga repetível)")
        if len(itens) != len(set(itens)):
            raise ValueError("há itens com o mesmo id")
        for i in self.itens:
            if i.entidade_id is not None and i.entidade_id not in conhecidas:
                raise ValueError(f"item '{i.id}' aponta para a entidade '{i.entidade_id}', que não está no arquivo")
        for a in self.acessos:
            faltam = [x for x in a.entidades if x not in conhecidas]
            if faltam:
                raise ValueError(f"acesso '{a.usuario_id}' cita entidade fora do arquivo: {faltam[0]}")
        return self


def dentro_de_repositorio(caminho: Path) -> bool:
    """Verdadeiro se o arquivo está dentro de qualquer repositório git (procura `.git` em todas as pastas acima)."""
    p = caminho.resolve()
    return any((pasta / ".git").exists() for pasta in [p.parent, *p.parent.parents])


def ler_carga(caminho: Path) -> Carga:
    if dentro_de_repositorio(caminho):
        raise SystemExit("Recusado: o arquivo está dentro de um repositório git. Dados reais do grupo ficam fora do git "
                         "(ex.: D:\\01_Projetos_Ativos\\SiteOrgatec-dados-privados\\locar\\).")
    try:
        return Carga.model_validate(json.loads(caminho.read_text(encoding="utf-8")))
    except (OSError, ValueError, ValidationError) as exc:
        raise SystemExit(f"Arquivo inválido: {_resumo_erro(exc)}") from None


def _resumo_erro(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        e = exc.errors()[0]
        return f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}"
    return str(exc)


@dataclass
class Plano:
    novos: dict[str, list[str]] = field(default_factory=lambda: {"entidades": [], "itens": [], "acessos": []})
    diferentes: dict[str, list[str]] = field(default_factory=lambda: {"entidades": [], "itens": [], "acessos": []})
    iguais: dict[str, list[str]] = field(default_factory=lambda: {"entidades": [], "itens": [], "acessos": []})
    grupo_novo: bool = False


def _dados(modelo: BaseModel, excluir: set[str]) -> dict[str, Any]:
    return modelo.model_dump(mode="json", exclude=excluir | {"documento"})


def _registros(carga: Carga) -> list[tuple[str, str, dict[str, Any]]]:
    saida = [("entidades", e.id, _dados(e, {"id"})) for e in carga.entidades]
    saida += [("itens", i.id, _dados(i, {"id"})) for i in carga.itens]  # type: ignore[arg-type]
    saida += [("acessos", a.usuario_id, _dados(a, {"usuario_id"})) for a in carga.acessos]
    return saida


def _normalizado(colecao: str, reg: dict[str, Any]) -> dict[str, Any]:
    """Só os campos que a carga controla: o resto (datas de criação, quem alterou) não conta como diferença."""
    ignorar = {"id", "grupo_id", "criado_em", "atualizado_em", "atualizado_por", "usuario_id"}
    r = {k: v for k, v in reg.items() if k not in ignorar}
    if colecao == "acessos":
        r["entidades"] = sorted(r.get("entidades", []))
    return r


def planejar(carga: Carga, repo: RepositorioBase) -> Plano:
    plano = Plano(grupo_novo=not repo.existe_grupo(carga.grupo.id))
    for colecao, rid, dados in _registros(carga):
        atual = None
        if not plano.grupo_novo:
            try:
                atual = repo.obter(carga.grupo.id, colecao, rid)
            except NaoEncontrado:
                atual = None
        if atual is None:
            plano.novos[colecao].append(rid)
        elif _normalizado(colecao, atual) == _normalizado(colecao, dados):
            plano.iguais[colecao].append(rid)
        else:
            plano.diferentes[colecao].append(rid)
    return plano


def aplicar(carga: Carga, repo: RepositorioBase, plano: Plano, sobrescrever: bool) -> int:
    """Grava os registros novos (e, com `sobrescrever`, os diferentes). Devolve quantos gravou."""
    gid = carga.grupo.id
    repo.criar_grupo(gid, carga.grupo.nome, carga.grupo.polos)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    gravados = 0
    for colecao, rid, dados in _registros(carga):
        if rid in plano.iguais[colecao] or (rid in plano.diferentes[colecao] and not sobrescrever):
            continue
        if colecao == "itens":
            dados = {**dados, "atualizado_em": agora, "atualizado_por": USUARIO_CARGA, **({} if rid in plano.diferentes[colecao] else {"criado_em": agora})}
        if colecao == "acessos":
            repo.salvar_acesso(gid, rid, dados["papel"], dados["entidades"])
        elif rid in plano.diferentes[colecao]:
            repo.atualizar(gid, colecao, rid, dados)
        else:
            repo.inserir(gid, colecao, rid, dados)
        repo.anexar_auditoria(gid, USUARIO_CARGA, f"carga.{colecao}", colecao, rid)
        gravados += 1
    return gravados


def descrever(carga: Carga, plano: Plano) -> list[str]:
    linhas = [f"grupo {carga.grupo.id}: {'novo' if plano.grupo_novo else 'já existe'}"]
    for colecao in ("entidades", "itens", "acessos"):
        n, d, i = len(plano.novos[colecao]), len(plano.diferentes[colecao]), len(plano.iguais[colecao])
        linhas.append(f"{colecao}: {n} novos, {d} diferentes do banco, {i} iguais")
        if plano.diferentes[colecao]:
            linhas.append("  diferentes (ids): " + ", ".join(plano.diferentes[colecao][:20]) + (" ..." if len(plano.diferentes[colecao]) > 20 else ""))
    return linhas


def main(argv: list[str] | None = None, repo: RepositorioBase | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arquivo", required=True, type=Path)
    ap.add_argument("--listar", action="store_true", help="só valida o arquivo e conta o que ele tem")
    ap.add_argument("--confirmar", action="store_true", help="grava; sem isto só mostra o que faria")
    ap.add_argument("--sobrescrever", action="store_true", help="com --confirmar, atualiza também o que já existe e é diferente")
    a = ap.parse_args(argv)
    carga = ler_carga(a.arquivo)
    if a.listar:
        print(f"arquivo válido: grupo {carga.grupo.id}, {len(carga.entidades)} entidades, {len(carga.itens)} itens, {len(carga.acessos)} acessos")
        return 0
    repo = repo or criar_repositorio(os.environ)
    plano = planejar(carga, repo)
    print("\n".join(descrever(carga, plano)))
    if not a.confirmar:
        print("[simulação] nada foi gravado; repita com --confirmar.")
        return 0
    n = aplicar(carga, repo, plano, a.sobrescrever)
    print(f"gravados: {n} registros")
    return 0


if __name__ == "__main__":
    sys.exit(main())
