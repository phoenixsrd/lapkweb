"""Chave secreta persistente e proteção CSRF simples (sem dependências extras)."""
import hmac
import logging
import os
import secrets
from datetime import timedelta

from flask import Flask, flash, redirect, request, session, url_for
from markupsafe import Markup

import config

log = logging.getLogger(__name__)
_METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


def carregar_secret_key() -> str:
    """Usa LAPKWEB_SECRET_KEY, ou uma chave gerada uma vez e guardada em data/.secret_key."""
    da_env = os.environ.get("LAPKWEB_SECRET_KEY")
    if da_env:
        return da_env

    caminho = config.SECRET_KEY_FILE
    for _ in range(2):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                chave = f.read().strip()
            if chave:
                return chave
        except FileNotFoundError:
            pass
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue  # outro processo criou agora: lê de novo
        except OSError:
            break
        chave = secrets.token_hex(32)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(chave)
        return chave

    log.warning("Não consegui gravar %s; usando chave temporária (as sessões somem ao reiniciar).", caminho)
    return secrets.token_hex(32)


def _token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
        session.permanent = True
    return session["csrf"]


def csrf_input() -> Markup:
    return Markup('<input type="hidden" name="csrf_token" value="%s">') % _token()


def _verificar_csrf():
    if request.method in _METODOS_SEGUROS:
        return None
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("csrf", "")
    if esperado and hmac.compare_digest(enviado, esperado):
        return None
    flash("Sua sessão expirou. Tente de novo.", "aviso")
    return redirect(url_for("jogos.index"))


def init_app(app: Flask) -> None:
    app.secret_key = carregar_secret_key()
    app.config.update(
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    )
    app.before_request(_verificar_csrf)
    app.add_template_global(csrf_input)
