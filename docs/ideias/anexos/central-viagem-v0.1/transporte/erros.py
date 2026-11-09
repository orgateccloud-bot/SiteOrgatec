"""Hierarquia de exceções do módulo. A API traduz cada uma em resposta HTTP sem expor detalhe interno."""

from __future__ import annotations


class ErroTransporte(Exception):
    codigo_http = 500
    mensagem_publica = "Erro interno na Central de Viagem."


class NaoEncontrado(ErroTransporte):
    codigo_http = 404
    mensagem_publica = "Registro não encontrado."


class EntradaInvalida(ErroTransporte):
    codigo_http = 422

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem_publica = mensagem


class AcessoNegado(ErroTransporte):
    codigo_http = 403
    mensagem_publica = "Acesso negado."


class RecursoDesligado(ErroTransporte):
    codigo_http = 404
    mensagem_publica = "Recurso não habilitado nesta instalação."


class ErroProvedor(ErroTransporte):
    """Falha numa integração externa. `estado` vai para a tela ao lado do dado afetado."""

    codigo_http = 503
    estado = "indisponivel"
    mensagem_publica = "Fonte de dados indisponível no momento."

    def __init__(self, provedor: str, detalhe: str = "") -> None:
        super().__init__(f"{provedor}: {detalhe}")
        self.provedor = provedor


class ProvedorTimeout(ErroProvedor):
    estado = "timeout"
    mensagem_publica = "A fonte de dados não respondeu a tempo."


class ProvedorLimiteExcedido(ErroProvedor):
    estado = "limite_excedido"
    codigo_http = 429
    mensagem_publica = "Limite de uso da fonte de dados atingido. Tente mais tarde."


class ProvedorRespostaInvalida(ErroProvedor):
    estado = "resposta_invalida"
    mensagem_publica = "A fonte de dados devolveu uma resposta inesperada."
