"""tools/aplicar_revisao.py: aplica no site as aprovações da revisão técnica, só se o texto não mudou depois."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import aplicar_revisao as ar  # noqa: E402
import conferir_revisao as cr  # noqa: E402

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node ausente")


@pytest.fixture
def js(tmp_path):
    destino = tmp_path / "js"
    shutil.copytree(RAIZ / "site" / "assets" / "js", destino)
    return destino


def _registro(atuais, aprovar, ajustar=(), responsavel="Responsável Teste", data="2026-11-10", hash_errado=()):
    decisoes = []
    for i in aprovar:
        h = "0" * 64 if i in hash_errado else atuais["itens"][i]["hash"]
        decisoes.append({"id": i, "tipo": atuais["itens"][i]["tipo"], "decisao": "aprovada", "nota": "", "conteudoHash": h})
    for i in ajustar:
        decisoes.append({"id": i, "tipo": atuais["itens"][i]["tipo"], "decisao": "ajustar", "nota": "revisar o prazo",
                         "conteudoHash": atuais["itens"][i]["hash"]})
    corpo = {"versao": 1, "responsavel": responsavel, "data": data, "decisoes": decisoes}
    corpo["audit_hash"] = hashlib.sha256(cr.canonico(corpo).encode("utf-8")).hexdigest()
    return corpo


def _ids(atuais, origem, n):
    return [i for i, v in atuais["itens"].items() if v["origem"] == origem][:n]


def _node(js, codigo):
    r = subprocess.run([shutil.which("node"), "-e", codigo, str(js)], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(r.stdout)


def _revisao_no_site(js, origem, id_):
    arquivo = "reforma-itens.js" if origem == "reforma" else "compliance-itens.js"
    return _node(js, f"const l=require(require('path').join(process.argv[1],'{arquivo}'));"
                     f"console.log(JSON.stringify(l.find(i=>i.id==='{id_[5:]}').revisao))")


def test_simulacao_nao_grava(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    antes = {n: (js / n).read_bytes() for n in ("reforma-itens.js", "compliance-itens.js", "termometro.js")}
    reg = _registro(atuais, _ids(atuais, "reforma", 2))
    plano = ar.aplicar(reg, js, tmp_path / "reg", gravar=False)
    assert len(plano["final"]) == 2
    assert antes == {n: (js / n).read_bytes() for n in antes}
    assert not (tmp_path / "reg").exists()


def test_aplicar_grava_e_o_site_le_a_aprovacao(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    r1, c1 = _ids(atuais, "reforma", 1)[0], _ids(atuais, "compliance", 1)[0]
    reg = _registro(atuais, [r1, c1])
    ar.aplicar(reg, js, tmp_path / "reg", gravar=True)
    for origem, id_ in (("reforma", r1), ("compliance", c1)):
        rev = _revisao_no_site(js, origem, id_)
        assert rev["status"] == "aprovada" and rev["por"] == "Responsável Teste" and rev["em"] == "2026-11-10"
        assert rev["hash"] == atuais["itens"][id_]["hash"]
    outro = _ids(atuais, "reforma", 2)[1]
    assert _revisao_no_site(js, "reforma", outro)["status"] == "pendente"
    assert len(list((tmp_path / "reg").glob("revisao-2026-11-10-*.json"))) == 1
    assert ar.hashes_atuais(js)["itens"] == atuais["itens"]  # aprovar não muda o texto revisado


def test_aplicar_duas_vezes_da_o_mesmo_arquivo(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    reg = _registro(atuais, _ids(atuais, "reforma", 2))
    ar.aplicar(reg, js, tmp_path / "reg", gravar=True)
    primeira = (js / "reforma-itens.js").read_bytes()
    ar.aplicar(reg, js, tmp_path / "reg", gravar=True)
    assert (js / "reforma-itens.js").read_bytes() == primeira


def test_texto_que_mudou_depois_da_revisao_nao_e_aprovado(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    i = _ids(atuais, "reforma", 1)[0]
    plano = ar.aplicar(_registro(atuais, [i], hash_errado=[i]), js, tmp_path / "reg", gravar=True)
    assert plano["divergentes"] == [i] and i not in plano["final"]
    assert _revisao_no_site(js, "reforma", i)["status"] == "pendente"


def test_ajustar_continua_pendente_e_traz_a_nota(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    a, b = _ids(atuais, "reforma", 2)
    plano = ar.aplicar(_registro(atuais, [a], ajustar=[b]), js, tmp_path / "reg", gravar=True)
    assert plano["ajustar"] == [(b, "revisar o prazo")]
    assert any("AJUSTAR" in linha and "revisar o prazo" in linha for linha in ar.resumo(plano))
    assert _revisao_no_site(js, "reforma", b)["status"] == "pendente"


def test_aprovado_que_muda_de_texto_e_revogado(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    i = "item:cbs-2027"
    assert i in atuais["itens"]
    ar.aplicar(_registro(atuais, [i]), js, tmp_path / "reg", gravar=True)
    assert _revisao_no_site(js, "reforma", i)["status"] == "aprovada"
    t = (js / "reforma-itens.js").read_text(encoding="utf-8")
    novo, n = re.subn(r"(id: 'cbs-2027'.*?fato: ')", r"\1ALTERADO. ", t, count=1, flags=re.S)
    assert n == 1
    (js / "reforma-itens.js").write_text(novo, encoding="utf-8")
    plano = ar.aplicar(_registro(atuais, []), js, tmp_path / "reg", gravar=True)
    assert plano["revogados"] == [i]
    assert _revisao_no_site(js, "reforma", i)["status"] == "pendente"


def test_termometro_so_aprova_com_o_conjunto_inteiro(js, tmp_path):
    termo = js / "termometro.js"  # o site já tem a V11 aprovada (12/11/2026): o teste parte do estado pendente
    texto = ar.REVISAO.sub("var REVISAO = " + ar.PENDENTE_REVISAO + ";", termo.read_text(encoding="utf-8"))
    termo.write_text(ar.PESOS.sub(lambda m: m.group(1) + ar.PENDENTE_PESOS + m.group(3), texto), encoding="utf-8")
    atuais = ar.hashes_atuais(js)
    perguntas = atuais["perguntas"]["ids"]
    ar.aplicar(_registro(atuais, perguntas[:-1]), js, tmp_path / "reg", gravar=True)  # falta uma
    assert _node(js, "console.log(JSON.stringify(require(require('path').join(process.argv[1],'termometro.js')).REVISAO))")["status"] == "pendente"
    ar.aplicar(_registro(atuais, perguntas), js, tmp_path / "reg", gravar=True)
    rev = _node(js, "console.log(JSON.stringify(require(require('path').join(process.argv[1],'termometro.js')).REVISAO))")
    assert rev["status"] == "aprovada" and rev["hash"] == atuais["perguntas"]["agregado"] and rev["por"] == "Responsável Teste"
    pesos = _node(js, "console.log(JSON.stringify(require(require('path').join(process.argv[1],'termometro.js')).PESOS_PERFIL.status))")
    assert pesos == "proposta"  # os pesos por perfil são revisados à parte
    ar.aplicar(_registro(atuais, atuais["pesos"]["ids"]), js, tmp_path / "reg", gravar=True)
    assert _node(js, "console.log(JSON.stringify(require(require('path').join(process.argv[1],'termometro.js')).PESOS_PERFIL.status))") == "aprovada"
    assert _node(js, "console.log(JSON.stringify(require(require('path').join(process.argv[1],'termometro.js')).REVISAO.status))") == "aprovada"


def test_registro_adulterado_e_recusado(js, tmp_path):
    atuais = ar.hashes_atuais(js)
    reg = _registro(atuais, _ids(atuais, "reforma", 1))
    reg["decisoes"][0]["decisao"] = "ajustar"
    with pytest.raises(ValueError, match="audit_hash"):
        ar.aplicar(reg, js, tmp_path / "reg", gravar=True)
