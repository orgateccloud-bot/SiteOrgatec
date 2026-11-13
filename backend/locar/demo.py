"""Grupo fictício para experimentar a tela e rodar os testes de navegador (ORGATEC_LOCAR_DEMO=1, nunca em produção).

Tudo aqui é inventado: nomes, regimes e prazos. Os prazos são relativos à data de hoje, para a tela sempre ter atrasadas,
próximas e entregues. Nenhum dado de cliente real entra neste arquivo nem em qualquer arquivo do repositório.
"""

from __future__ import annotations

from datetime import date, timedelta

from backend.locar.repositorio_locar import RepositorioBase

GRUPO_DEMO = "00000000-0000-4000-8000-0000000000a1"


def carregar(repo: RepositorioBase, hoje: date | None = None) -> str:
    hoje = hoje or date.today()
    d = lambda dias: (hoje + timedelta(days=dias)).isoformat()  # noqa: E731
    repo.criar_grupo(GRUPO_DEMO, "Grupo Exemplo")
    repo.inserir(GRUPO_DEMO, "entidades", "e-transp", {"nome": "Exemplo Transporte Ltda", "tipo": "pj", "status": "em_incorporacao",
                 "sucessora_id": "e-matriz", "regime": "lucro_real", "regime_vigencia": None, "documento_mascarado": "**.***.***/0001-70",
                 "sensivel": False, "titulares": []})
    repo.inserir(GRUPO_DEMO, "entidades", "e-matriz", {"nome": "Exemplo Matriz Ltda", "tipo": "pj", "status": "ativa", "sucessora_id": None,
                 "regime": "lucro_real", "regime_vigencia": None, "documento_mascarado": "**.***.***/0001-54", "sensivel": False, "titulares": []})
    repo.inserir(GRUPO_DEMO, "entidades", "e-maq", {"nome": "Exemplo Máquinas Ltda", "tipo": "pj", "status": "ativa", "sucessora_id": None,
                 "regime": "lucro_presumido", "regime_vigencia": None, "documento_mascarado": "**.***.***/0001-49", "sensivel": False, "titulares": []})
    repo.inserir(GRUPO_DEMO, "entidades", "e-pf", {"nome": "Produtor Exemplo (pessoa física)", "tipo": "produtor_pf", "status": "ativa", "sucessora_id": None,
                 "regime": "produtor_rural_pf", "regime_vigencia": None, "documento_mascarado": None, "sensivel": True, "titulares": ["u-titular"]})
    itens = [
        ("i1", "e-matriz", "obrigacao", "Entregar a escrituração do mês", d(-6), False, "equipe", "a_fazer", None),
        ("i2", "e-matriz", "obrigacao", "Conferir créditos de PIS e Cofins", d(12), False, "equipe", "em_andamento", "lc214_saldo_piscofins"),
        ("i3", "e-maq", "obrigacao", "Enviar contratos de locação para revisão", d(25), False, "grupo", "a_fazer", None),
        ("i4", "e-maq", "obrigacao", "Fechamento mensal", d(-2), False, "equipe", "entregue", None),
        ("i5", "e-transp", "marco_societario", "Alteração contratual da incorporação", d(40), True, "equipe", "a_fazer", None),
        ("i6", None, "evento_reforma", "CBS no lugar de PIS e Cofins", "2027-01-01", False, "equipe", "a_fazer", "adct_126"),
        ("i7", None, "evento_reforma", "Resolução do Senado sobre a alíquota da CBS", None, True, "equipe", "a_fazer", "senado_cbs_2027"),
        ("i8", "e-pf", "obrigacao", "Entregar o livro caixa digital", d(18), False, "equipe", "a_fazer", None),
    ]
    for rid, ent, tipo, titulo, prazo, a_confirmar, resp, status, fonte in itens:
        repo.inserir(GRUPO_DEMO, "itens", rid, {"entidade_id": ent, "tipo": tipo, "titulo": titulo, "prazo": prazo, "prazo_a_confirmar": a_confirmar,
                     "responsavel": resp, "status": status, "fonte_id": fonte, "modelo_id": None, "evidencia_ref": None})
    repo.salvar_acesso(GRUPO_DEMO, "u-diretor", "diretor", ["e-matriz", "e-maq"])
    return GRUPO_DEMO
