from typing import List, Optional, Tuple
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for

import servico
from storage import (
    Jogo,
    adicionar_jogo,
    atualizar_jogo,
    buscar_jogo,
    carregar_jogos,
    excluir_jogo,
)
from versoes import normalizar_versao, separar_versao_e_data

bp = Blueprint("jogos", __name__)

LIMITE_NOME = 100
LIMITE_VERSAO = 120
LIMITE_URL = 500


# --- Auxiliares --------------------------------------------------------------
def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _voltar(jogo_id: Optional[int] = None):
    ancora = f"jogo-{jogo_id}" if jogo_id else None
    return redirect(url_for("jogos.index", _anchor=ancora))


def _nao_encontrado():
    flash("Esse jogo não existe mais.", "aviso")
    return _voltar()


def _chave_url(url: str) -> str:
    p = urlsplit(url.strip())
    return f"{p.scheme.lower()}://{p.netloc.lower()}{p.path.rstrip('/')}" + (f"?{p.query}" if p.query else "")


def _url_valida(url: str) -> bool:
    p = urlsplit(url)
    return p.scheme in ("http", "https") and bool(p.netloc) and not any(c.isspace() for c in url)


def _ler_formulario(form) -> Tuple[dict, List[str]]:
    nome = (form.get("nome") or "").strip()
    url = (form.get("url") or "").strip()
    versao_digitada = (form.get("versao_local") or "").strip()
    erros: List[str] = []

    if url and "://" not in url:
        url = "https://" + url

    if not nome:
        erros.append("Informe o nome do jogo.")
    elif len(nome) > LIMITE_NOME:
        erros.append(f"O nome pode ter no máximo {LIMITE_NOME} caracteres.")

    if not url or not _url_valida(url):
        erros.append("Informe uma URL válida (http:// ou https://).")
    elif len(url) > LIMITE_URL:
        erros.append("A URL está longa demais.")

    # Se a pessoa colar "versão + Data da Atualização: ...", guarda só a versão.
    versao, _ = separar_versao_e_data(versao_digitada)
    if not versao:
        erros.append("Informe a versão que você tem.")
    elif len(versao) > LIMITE_VERSAO:
        erros.append(f"A versão pode ter no máximo {LIMITE_VERSAO} caracteres.")

    return {"nome": nome, "url": url, "versao_local": versao}, erros


def _erro_url_duplicada(url: str, ignorar_id: Optional[int] = None) -> List[str]:
    chave = _chave_url(url)
    for j in carregar_jogos():
        if j.id != ignorar_id and _chave_url(j.url) == chave:
            return [f"Essa URL já está cadastrada como “{j.nome}”."]
    return []


def _ordenar(jogos: List[Jogo]) -> List[Jogo]:
    def chave(j: Jogo):
        if j.tem_atualizacao:
            grupo = 0
        elif j.erro:
            grupo = 1
        elif not j.versao_site:
            grupo = 2
        else:
            grupo = 3
        return (grupo, j.nome.casefold())

    return sorted(jogos, key=chave)


def _contexto_index(valores=None, erros: Optional[List[str]] = None) -> dict:
    jogos = carregar_jogos()
    return {
        "jogos": _ordenar(jogos),
        "resumo": {
            "total": len(jogos),
            "pendentes": sum(1 for j in jogos if j.tem_atualizacao),
            "erros": sum(1 for j in jogos if j.erro),
        },
        "valores": valores or {},
        "erros": erros or [],
    }


def _avisar_resultado(jogo: Jogo) -> None:
    if jogo.erro:
        flash(f"Não foi possível verificar “{jogo.nome}”.", "erro")
    elif jogo.tem_atualizacao:
        flash(f"Atualização disponível para “{jogo.nome}”: {jogo.versao_site}.", "aviso")
    else:
        flash(f"“{jogo.nome}” está em dia.", "ok")


# --- Rotas -------------------------------------------------------------------
@bp.route("/")
def index():
    return render_template("index.html", **_contexto_index())


@bp.route("/adicionar", methods=["POST"])
def adicionar():
    dados, erros = _ler_formulario(request.form)
    if not erros:
        erros = _erro_url_duplicada(dados["url"])
    if erros:
        return render_template("index.html", **_contexto_index(request.form, erros)), 400

    jogo = adicionar_jogo(**dados)
    servico.verificar([jogo.id])  # já mostra o status logo depois de cadastrar
    atual = buscar_jogo(jogo.id) or jogo
    if atual.erro:
        flash(f"“{atual.nome}” adicionado, mas não consegui verificar agora.", "aviso")
    elif atual.tem_atualizacao:
        flash(f"“{atual.nome}” adicionado — o site já tem uma versão mais nova.", "aviso")
    else:
        flash(f"“{atual.nome}” adicionado e em dia.", "ok")
    return _voltar(jogo.id)


@bp.route("/editar/<int:jogo_id>", methods=["GET", "POST"])
def editar(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if not jogo:
        return _nao_encontrado()

    if request.method == "POST":
        dados, erros = _ler_formulario(request.form)
        if not erros:
            erros = _erro_url_duplicada(dados["url"], ignorar_id=jogo_id)
        if erros:
            return render_template("edit.html", jogo=jogo, valores=request.form, erros=erros), 400

        campos = dict(dados)
        if _chave_url(dados["url"]) != _chave_url(jogo.url):
            # URL nova: o que foi lido da página antiga não vale mais.
            campos.update(versao_site=None, atualizado_em=None, ultima_verificacao=None,
                          detectado_em=None, erro=None)
        elif normalizar_versao(dados["versao_local"]) != normalizar_versao(jogo.versao_local):
            campos["detectado_em"] = None
        atualizar_jogo(jogo_id, **campos)
        flash(f"“{dados['nome']}” salvo.", "ok")
        return _voltar(jogo_id)

    valores = {"nome": jogo.nome, "url": jogo.url, "versao_local": jogo.versao_local}
    return render_template("edit.html", jogo=jogo, valores=valores, erros=[])


@bp.route("/verificar/<int:jogo_id>", methods=["POST"])
def verificar(jogo_id):
    if not buscar_jogo(jogo_id):
        return _nao_encontrado()
    servico.verificar([jogo_id])
    atual = buscar_jogo(jogo_id)
    if atual:
        _avisar_resultado(atual)
    return _voltar(jogo_id)


@bp.route("/verificar-todos", methods=["POST"])
def verificar_todos():
    r = servico.verificar()
    if not r.verificados:
        flash("Nenhum jogo cadastrado para verificar.", "aviso")
    else:
        partes = [f"{_plural(r.verificados, 'jogo verificado', 'jogos verificados')}"]
        partes.append(f"{r.pendentes} com atualização" if r.pendentes else "nenhuma atualização")
        if r.erros:
            partes.append(_plural(r.erros, "erro", "erros"))
        flash(" · ".join(partes) + ".", "aviso" if (r.pendentes or r.erros) else "ok")
    return _voltar()


@bp.route("/marcar-atualizado/<int:jogo_id>", methods=["POST"])
def marcar_atualizado(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if not jogo:
        return _nao_encontrado()
    if jogo.versao_site:
        atualizar_jogo(jogo_id, versao_local=jogo.versao_site, detectado_em=None)
        flash(f"“{jogo.nome}” marcado como atualizado.", "ok")
    return _voltar(jogo_id)


@bp.route("/excluir/<int:jogo_id>", methods=["POST"])
def excluir(jogo_id):
    jogo = buscar_jogo(jogo_id)
    if jogo and excluir_jogo(jogo_id):
        flash(f"“{jogo.nome}” excluído.", "ok")
    else:
        flash("Esse jogo não existe mais.", "aviso")
    return _voltar()
