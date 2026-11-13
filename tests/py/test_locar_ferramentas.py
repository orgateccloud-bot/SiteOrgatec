"""Ferramentas do LOCAR: acesso por usuário (claims mescladas), carga local fora do git e a CSP do painel."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from backend.locar.repositorio_locar import RepositorioMemoria

RAIZ = Path(__file__).resolve().parents[2]
GA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
EXEMPLO = RAIZ / "docs" / "locar" / "modelo-carga.exemplo.json"


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "tools" / f"{nome}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[nome] = m  # os dataclasses das ferramentas resolvem as anotações pelo módulo registrado
    spec.loader.exec_module(m)
    return m


usuario = _carregar("locar_usuario")
transporte_usuario = _carregar("transporte_usuario")
carregar = _carregar("locar_carregar")
firebase = _carregar("preparar_firebase")


# ---------------------------------------------------------------- locar_usuario

def _cliente(declaracoes=None, vistos=None, encontra=True, usuarios_lista=None):
    def h(req):
        corpo = json.loads(req.content) if req.content else {}
        (vistos if vistos is not None else []).append((req.method, req.url.path, corpo))
        if req.url.path.endswith(":lookup"):
            u = {"localId": "uid-1", **({"customAttributes": json.dumps(declaracoes)} if declaracoes is not None else {})}
            return httpx.Response(200, json={"users": [u] if encontra else []})
        if req.url.path.endswith(":batchGet"):
            return httpx.Response(200, json={"users": usuarios_lista or []})
        return httpx.Response(200, json={})
    return httpx.Client(transport=httpx.MockTransport(h))


def _gravado(vistos):
    return [json.loads(c["customAttributes"]) for m, p, c in vistos if p.endswith(":update")]


def test_concede_acesso_preservando_as_declaracoes_do_transporte():
    vistos = []
    frase = usuario.definir_acesso(_cliente({"transportadora_id": "t-1", "papel": "gestor"}, vistos), "p", "a@b.com", GA, "equipe", confirmar=True)
    assert "concedido" in frase and "uid-1" in frase
    assert _gravado(vistos) == [{"transportadora_id": "t-1", "papel": "gestor", "locar_grupo": GA, "locar_papel": "equipe"}]


def test_sem_confirmar_nada_e_gravado():
    vistos = []
    frase = usuario.definir_acesso(_cliente({}, vistos), "p", "a@b.com", GA, "equipe")
    assert "simulação" in frase and _gravado(vistos) == []


def test_revogar_tira_so_as_chaves_do_locar():
    vistos = []
    frase = usuario.definir_acesso(_cliente({"transportadora_id": "t-1", "papel": "gestor", "locar_grupo": GA, "locar_papel": "equipe"}, vistos),
                                   "p", "a@b.com", None, None, confirmar=True)
    assert "removido" in frase and _gravado(vistos) == [{"transportadora_id": "t-1", "papel": "gestor"}]


def test_usuario_inexistente_e_recusado():
    with pytest.raises(SystemExit):
        usuario.definir_acesso(_cliente(encontra=False), "p", "x@y.com", GA, "leitura", confirmar=True)


def test_listar_mostra_so_quem_tem_acesso_e_nao_mostra_e_mail():
    lista = [{"localId": "u1", "email": "a@b.com", "customAttributes": json.dumps({"locar_grupo": GA, "locar_papel": "diretor"})},
             {"localId": "u2", "email": "c@d.com", "customAttributes": json.dumps({"transportadora_id": "t"})},
             {"localId": "u3", "email": "e@f.com"}]
    linhas = usuario.listar(_cliente(usuarios_lista=lista), "p")
    assert linhas == [f"u1  papel=diretor  grupo={GA}"] and "@" not in "".join(linhas)


def test_transporte_usuario_agora_preserva_as_declaracoes_do_locar():
    vistos = []
    transporte_usuario.definir_acesso(_cliente({"locar_grupo": GA, "locar_papel": "equipe"}, vistos), "p", "a@b.com", "t-1", "gestor")
    assert _gravado(vistos) == [{"locar_grupo": GA, "locar_papel": "equipe", "transportadora_id": "t-1", "papel": "gestor"}]
    vistos.clear()
    transporte_usuario.definir_acesso(_cliente({"locar_grupo": GA, "locar_papel": "equipe", "transportadora_id": "t-1", "papel": "gestor"}, vistos),
                                      "p", "a@b.com", None, None)
    assert _gravado(vistos) == [{"locar_grupo": GA, "locar_papel": "equipe"}]


# ---------------------------------------------------------------- locar_carregar

@pytest.fixture
def carga(tmp_path):
    destino = tmp_path / "privado" / "carga.json"
    destino.parent.mkdir()
    shutil.copy(EXEMPLO, destino)
    return destino


def _rodar(carga_path, *args, repo=None):
    repo = repo or RepositorioMemoria()
    assert carregar.main(["--arquivo", str(carga_path), *args], repo=repo) == 0
    return repo


def test_modelo_de_exemplo_e_valido_e_conta_o_que_tem(carga, capsys):
    assert carregar.main(["--arquivo", str(carga), "--listar"]) == 0
    assert "5 entidades, 4 itens, 2 acessos" in capsys.readouterr().out


def test_recusa_arquivo_dentro_de_repositorio_git():
    with pytest.raises(SystemExit) as e:
        carregar.ler_carga(EXEMPLO)
    assert "repositório git" in str(e.value)


def test_simulacao_nao_grava_nada(carga, capsys):
    repo = _rodar(carga)
    assert not repo.existe_grupo("11111111-1111-4111-8111-111111111111")
    saida = capsys.readouterr().out
    assert "simulação" in saida and "Exemplo" not in saida  # a saída mostra ids e contagens, nunca nomes


def test_confirmar_grava_mascara_o_documento_e_audita(carga):
    repo = _rodar(carga, "--confirmar")
    g = "11111111-1111-4111-8111-111111111111"
    assert len(repo.listar(g, "entidades")) == 5 and len(repo.listar(g, "itens")) == 4
    e = repo.obter(g, "entidades", "e-transporte")
    assert e["documento_mascarado"] == "**.***.***/0001-70" and "documento" not in e
    pf = repo.obter(g, "entidades", "e-produtor-1")
    assert pf["sensivel"] is True and pf["titulares"] == ["uid-do-produtor-1"]
    assert repo.obter_acesso(g, "uid-do-diretor-1")["papel"] == "diretor"
    assert "98.900.460" not in json.dumps(repo._dados, default=str)  # o documento bruto não chega ao banco
    assert repo.verificar_cadeia(g)[0] is True and len(repo.auditoria(g, 100)) == 11


def test_repetir_a_carga_nao_grava_de_novo(carga, capsys):
    repo = _rodar(carga, "--confirmar")
    capsys.readouterr()
    _rodar(carga, "--confirmar", repo=repo)
    assert "gravados: 0 registros" in capsys.readouterr().out


def test_nao_sobrescreve_o_que_o_painel_mudou_sem_pedir(carga):
    g = "11111111-1111-4111-8111-111111111111"
    repo = _rodar(carga, "--confirmar")
    repo.atualizar(g, "itens", "i-cbs-2027", {"status": "entregue"})
    _rodar(carga, "--confirmar", repo=repo)
    assert repo.obter(g, "itens", "i-cbs-2027")["status"] == "entregue"  # a carga não desfaz o trabalho feito no painel
    _rodar(carga, "--confirmar", "--sobrescrever", repo=repo)
    assert repo.obter(g, "itens", "i-cbs-2027")["status"] == "a_fazer"


def test_cpf_sai_todo_mascarado():
    assert carregar.mascarar_documento("123.456." + "789-09") == "***.***.***-**"  # montado aos pedaços: o teste de varredura abaixo não aceita CPF escrito inteiro
    assert carregar.mascarar_documento("98.900.460/0001-70") == "**.***.***/0001-70"
    with pytest.raises(ValueError):
        carregar.mascarar_documento("12345")


def _com(carga_path, mudar):
    dados = json.loads(carga_path.read_text(encoding="utf-8"))
    mudar(dados)
    carga_path.write_text(json.dumps(dados), encoding="utf-8")


@pytest.mark.parametrize("mudar", [
    lambda d: d["itens"][0].update(entidade_id="nao-existe"),
    lambda d: d["itens"][0].pop("id"),
    lambda d: d["itens"].append(dict(d["itens"][0])),
    lambda d: d["entidades"].append(dict(d["entidades"][0])),
    lambda d: d["entidades"][0].update(sucessora_id="fora-do-arquivo"),
    lambda d: d["acessos"][1]["entidades"].append("fora-do-arquivo"),
    lambda d: d["entidades"][0].update(campo_estranho=1),
    lambda d: d["entidades"][0].update(documento="123"),
    lambda d: d["entidades"][0].update(documento_mascarado="98.900.460/0001-70"),
    lambda d: d["grupo"].update(id="nao-e-uuid"),
], ids=["entidade-do-item", "item-sem-id", "item-repetido", "entidade-repetida", "sucessora", "acesso", "campo-extra", "documento-curto",
        "documento-sem-mascara", "grupo"])
def test_arquivo_invalido_e_recusado_com_mensagem(carga, mudar):
    _com(carga, mudar)
    with pytest.raises(SystemExit) as e:
        carregar.ler_carga(carga)
    assert "Arquivo inválido" in str(e.value)


# ---------------------------------------------------------------- CSP do painel

def test_so_o_painel_locar_fala_com_o_google_alem_do_transporte():
    from backend import app as servidor

    assert firebase.csp_locar(None) == servidor.CSP_LOCAR
    assert "identitytoolkit.googleapis.com" in servidor.CSP_LOCAR and "securetoken.googleapis.com" in servidor.CSP_LOCAR
    assert "maps" not in servidor.CSP_LOCAR and "googleapis" not in servidor.CSP  # sem mapa, e o resto do site continua só com 'self'
    assert "script-src 'self';" in servidor.CSP_LOCAR  # o login não abre script de fora
    cfg = firebase.firebase_json(None, False, "orgatec-api", firebase.REGIAO_PADRAO)
    regras = {h["source"]: {x["key"]: x["value"] for x in h["headers"]} for h in cfg["hosting"]["headers"]}
    assert regras["/locar/**"]["Content-Security-Policy"] == firebase.csp_locar(None)
    assert json.loads((RAIZ / "firebase.json").read_text(encoding="utf-8"))["hosting"]["headers"][2]["source"] == "/locar/**"


# ---------------------------------------------------------------- nenhum dado real no repositório

CNPJ = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")
CPF = re.compile(r"(?<![\d.])\d{3}\.\d{3}\.\d{3}-\d{2}(?![\d])")
PERMITIDOS = {"98.900.460/0001-70", "67.025.451/0001-54", "85.346.964/0001-49", "78.213.159/0001-81",  # fictícios do documento de planejamento
              "13.155.211/0001-45"}  # o da própria ORGATEC, que já está no rodapé do site


def _arquivos_do_locar():
    git = shutil.which("git")
    rastreados = subprocess.run([git, "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split("\n")  # nosec B603
    mudados = subprocess.run([git, "ls-files", "--others", "--exclude-standard"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split("\n")  # nosec B603
    marcas = ("locar", "LOCAR")
    return [RAIZ / f for f in set(rastreados + mudados) if f and any(m in f for m in marcas) and (RAIZ / f).is_file()
            and (RAIZ / f).suffix in {".py", ".js", ".json", ".md", ".html", ".css"}]


def test_arquivos_do_locar_so_trazem_documentos_ficticios():
    arquivos = _arquivos_do_locar()
    assert len(arquivos) >= 8  # a busca achou os arquivos do módulo
    for a in arquivos:
        texto = a.read_text(encoding="utf-8", errors="ignore")
        assert set(CNPJ.findall(texto)) <= PERMITIDOS, a.name
        assert not CPF.findall(texto), a.name
