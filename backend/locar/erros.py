"""Exceções do módulo LOCAR. A API traduz cada uma em resposta HTTP sem expor detalhe interno."""

from __future__ import annotations


class ErroLocar(Exception):
    codigo_http = 500
    mensagem_publica = "Erro interno no módulo LOCAR."


class NaoEncontrado(ErroLocar):
    codigo_http = 404
    mensagem_publica = "Registro não encontrado."


class EntradaInvalida(ErroLocar):
    codigo_http = 422

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem_publica = mensagem


class AcessoNegado(ErroLocar):
    codigo_http = 403
    mensagem_publica = "Acesso negado."


class RecursoDesligado(ErroLocar):
    codigo_http = 404
    mensagem_publica = "Recurso não habilitado nesta instalação."

    def __init__(self, detalhe: str = "") -> None:
        super().__init__(detalhe)


class LimiteExcedido(ErroLocar):
    codigo_http = 429
    mensagem_publica = "Muitas requisições. Aguarde um instante."
