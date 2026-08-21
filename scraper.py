import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config


def _montar_padrao_parada() -> str:
    rotulos = list(config.STOP_LABELS) + [config.LABEL_ATUALIZADO_EM]
    alternativas = [re.escape(r) for r in rotulos]
    return "(?:" + "|".join(alternativas) + r"|$)"


def _extrair_campo(texto: str, rotulo: str, padrao_parada: str) -> Optional[str]:
    padrao = re.escape(rotulo) + r"\s*:\s*(.*?)\s*" + padrao_parada
    m = re.search(padrao, texto, re.IGNORECASE)
    if not m:
        return None
    valor = m.group(1).strip(" -–—")
    return valor or None


def verificar_versao(url: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Busca a página e extrai (versao, atualizado_em, erro)."""
    try:
        resposta = requests.get(url, headers=config.REQUEST_HEADERS, timeout=config.REQUEST_TIMEOUT)
        resposta.raise_for_status()
    except requests.RequestException as e:
        return None, None, f"Erro ao acessar a página: {e}"

    texto = BeautifulSoup(resposta.content, "html.parser").get_text(" ", strip=True)
    texto = re.sub(r"\s+", " ", texto)

    padrao_parada = _montar_padrao_parada()
    versao = _extrair_campo(texto, config.LABEL_VERSAO, padrao_parada)
    atualizado_em = _extrair_campo(texto, config.LABEL_ATUALIZADO_EM, padrao_parada)

    if versao is None:
        return None, None, f"Não encontrei '{config.LABEL_VERSAO}:' na página"

    return versao, atualizado_em, None