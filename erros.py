"""Páginas de erro amigáveis e filtros de template."""
from flask import Flask, render_template

import tempo
from storage import ArmazenamentoCorrompido


def _pagina(titulo: str, mensagem: str, status: int):
    return render_template("erro.html", titulo=titulo, mensagem=mensagem), status


def registrar(app: Flask) -> None:
    app.add_template_filter(tempo.tempo_relativo, "tempo_relativo")
    app.add_template_filter(tempo.data_hora, "data_hora")

    @app.errorhandler(404)
    def _404(_e):
        return _pagina("Página não encontrada", "Esse endereço não existe.", 404)

    @app.errorhandler(405)
    def _405(_e):
        return _pagina("Ação não permitida", "Essa página não aceita esse tipo de acesso.", 405)

    @app.errorhandler(413)
    def _413(_e):
        return _pagina("Dados demais", "O formulário enviado é grande demais.", 413)

    @app.errorhandler(ArmazenamentoCorrompido)
    def _corrompido(e):
        return _pagina("Problema nos dados salvos", str(e), 500)

    @app.errorhandler(500)
    def _500(_e):
        return _pagina("Algo deu errado", "Ocorreu um erro inesperado. Veja o terminal para detalhes.", 500)
