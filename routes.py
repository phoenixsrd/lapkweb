from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for

from storage import carregar_jogos, adicionar_jogo, atualizar_jogo, excluir_jogo, buscar_jogo
from scraper import verificar_versao

bp = Blueprint("jogos", __name__)


def _tem_atualizacao(jogo) -> bool:
    return bool(jogo.versao_site) and jogo.versao_site != jogo.versao_local and not jogo.erro


@bp.route("/")
def index():
    jogos = carregar_jogos()
    resumo = {
        "total": len(jogos),
        "pendentes": sum(1 for j in jogos if _tem_atualizacao(j)),
    }
    return render_template("index.html", jogos=jogos, resumo=resumo, tem_atualizacao=_tem_atualizacao)


@bp.route("/adicionar", methods=["POST"])
def adicionar():
    adicionar_jogo(
        nome=request.form["nome"].strip(),
        url=request.form["url"].strip(),
        versao_local=request.form["versao_local"].strip(),
    )
    return redirect(url_for("jogos.index"))


@bp.route("/editar/<int:jogo_id>", methods=["GET", "POST"])
def editar(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if not jogo:
        return redirect(url_for("jogos.index"))

    if request.method == "POST":
        atualizar_jogo(
            jogo_id,
            nome=request.form["nome"].strip(),
            url=request.form["url"].strip(),
            versao_local=request.form["versao_local"].strip(),
        )
        return redirect(url_for("jogos.index"))

    return render_template("edit.html", jogo=jogo)


@bp.route("/verificar/<int:jogo_id>", methods=["POST"])
def verificar(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if jogo:
        versao, atualizado_em, erro = verificar_versao(jogo.url)
        atualizar_jogo(
            jogo_id,
            versao_site=versao,
            atualizado_em=atualizado_em,
            erro=erro,
            ultima_verificacao=datetime.now().strftime("%d/%m %H:%M"),
        )
    return redirect(url_for("jogos.index"))


@bp.route("/verificar-todos", methods=["POST"])
def verificar_todos():
    agora = datetime.now().strftime("%d/%m %H:%M")
    for jogo in carregar_jogos():
        versao, atualizado_em, erro = verificar_versao(jogo.url)
        atualizar_jogo(
            jogo.id,
            versao_site=versao,
            atualizado_em=atualizado_em,
            erro=erro,
            ultima_verificacao=agora,
        )
    return redirect(url_for("jogos.index"))


@bp.route("/marcar-atualizado/<int:jogo_id>", methods=["POST"])
def marcar_atualizado(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if jogo and jogo.versao_site:
        atualizar_jogo(jogo_id, versao_local=jogo.versao_site)
    return redirect(url_for("jogos.index"))


@bp.route("/excluir/<int:jogo_id>", methods=["POST"])
def excluir(jogo_id):
    excluir_jogo(jogo_id)
    return redirect(url_for("jogos.index"))