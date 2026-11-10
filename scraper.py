"""Baixa a página do jogo e extrai versão e data de atualização."""
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, Optional, Union

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from versoes import ValorInvalido, extrair_campo, extrair_data, separar_versao_e_data

log = logging.getLogger(__name__)


@dataclass
class Resultado:
    versao: Optional[str] = None
    atualizado_em: Optional[str] = None
    erro: Optional[str] = None


class ConteudoInesperado(Exception):
    """A URL respondeu, mas não com uma página de texto/HTML."""


def _criar_sessao() -> requests.Session:
    retry = Retry(
        total=config.REQUEST_RETRIES,
        backoff_factor=0.6,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=False,
        raise_on_status=False,
    )
    adaptador = HTTPAdapter(max_retries=retry)
    sessao = requests.Session()
    sessao.mount("http://", adaptador)
    sessao.mount("https://", adaptador)
    sessao.headers.update(config.REQUEST_HEADERS)
    return sessao


def _baixar(url: str) -> bytes:
    with _criar_sessao() as sessao:
        with sessao.get(url, timeout=config.REQUEST_TIMEOUT, stream=True) as resposta:
            resposta.raise_for_status()
            tipo = resposta.headers.get("Content-Type", "").lower()
            if tipo and "html" not in tipo and not tipo.startswith("text/"):
                raise ConteudoInesperado(f"A URL não devolveu uma página (tipo: {tipo.split(';')[0]})")
            partes, total = [], 0
            for pedaco in resposta.iter_content(65536):
                partes.append(pedaco)
                total += len(pedaco)
                if total >= config.MAX_BYTES:
                    break
            return b"".join(partes)


def _mensagem_erro(exc: Exception) -> str:
    if isinstance(exc, requests.exceptions.Timeout):
        return "Tempo esgotado ao acessar a página"
    if isinstance(exc, requests.exceptions.SSLError):
        return "Falha de segurança (SSL) ao acessar a página"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "Não consegui conectar ao site (confira a internet e a URL)"
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else "?"
        dica = " (pode ser bloqueio anti-robô)" if status in (403, 429, 503) else ""
        return f"O site respondeu com erro HTTP {status}{dica}"
    if isinstance(exc, (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema,
                        requests.exceptions.InvalidSchema)):
        return "URL inválida"
    if isinstance(exc, ConteudoInesperado):
        return str(exc)
    return f"Erro ao acessar a página: {exc}"


def extrair_dados(conteudo: Union[bytes, str]) -> Resultado:
    """Extrai versão e data do HTML (função pura, fácil de testar)."""
    soup = BeautifulSoup(conteudo, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    texto = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    paradas = config.LABELS_VERSAO + config.LABELS_DATA + config.STOP_LABELS
    try:
        versao_bruta = extrair_campo(texto, config.LABELS_VERSAO, paradas)
    except ValorInvalido as e:
        return Resultado(erro=str(e))
    if versao_bruta is None:
        return Resultado(erro=f"Não encontrei '{config.LABELS_VERSAO[0]}:' na página")

    versao, data_embutida = separar_versao_e_data(versao_bruta)
    if not versao:
        return Resultado(erro=f"O campo '{config.LABELS_VERSAO[0]}' está vazio na página")

    try:
        data = extrair_data(extrair_campo(texto, config.LABELS_DATA, paradas)) or data_embutida
    except ValorInvalido:
        data = data_embutida
    return Resultado(versao=versao, atualizado_em=data)


def verificar_versao(url: str) -> Resultado:
    try:
        conteudo = _baixar(url)
    except (requests.RequestException, ConteudoInesperado) as e:
        return Resultado(erro=_mensagem_erro(e))
    return extrair_dados(conteudo)


def _verificar_sem_excecao(url: str) -> Resultado:
    try:
        return verificar_versao(url)
    except Exception as e:  # uma página problemática não pode derrubar o lote
        log.exception("Erro inesperado ao verificar %s", url)
        return Resultado(erro=f"Erro inesperado: {e}")


def verificar_varios(urls: Dict[int, str]) -> Dict[int, Resultado]:
    """Verifica várias páginas em paralelo. Chave = id do jogo."""
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=max(1, min(config.MAX_WORKERS, len(urls)))) as pool:
        futuros = {jid: pool.submit(_verificar_sem_excecao, url) for jid, url in urls.items()}
        return {jid: f.result() for jid, f in futuros.items()}
