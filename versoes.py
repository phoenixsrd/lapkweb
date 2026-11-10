"""Funções puras para lidar com textos de versão e data (sem I/O)."""
import re
import unicodedata
from typing import Iterable, Optional, Tuple

import config

LIMITE_VALOR = 120
_DATA_RE = re.compile(r"(?<!\d)\d{1,2}/\d{1,2}/\d{2,4}(?!\d)")
_APARAR = " -–—"


class ValorInvalido(ValueError):
    """O rótulo foi encontrado, mas o valor capturado não parece confiável."""


def dobrar(texto: str) -> str:
    """Minúsculas e sem acentos, mantendo o MESMO comprimento do original.

    Isso permite procurar rótulos ignorando acento/caixa e depois recortar o
    valor do texto original usando os mesmos índices.
    """
    saida = []
    for c in texto:
        base = "".join(x for x in unicodedata.normalize("NFD", c) if not unicodedata.combining(x)).lower()
        saida.append(base if len(base) == 1 else c)
    return "".join(saida)


def _colapsar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _padrao_rotulo(rotulo: str) -> str:
    return r"\s+".join(re.escape(p) for p in dobrar(rotulo).split())


def extrair_campo(
    texto: str,
    rotulos: Iterable[str],
    paradas: Iterable[str],
    limite: int = LIMITE_VALOR,
) -> Optional[str]:
    """Devolve o valor que vem depois de 'rótulo:' até o próximo rótulo conhecido.

    Tenta cada rótulo em ordem. Retorna None se nenhum for encontrado e levanta
    ValorInvalido se o valor capturado passar de `limite` caracteres (sinal de
    que nenhum rótulo de parada foi achado).
    """
    texto = _colapsar(texto)
    norm = dobrar(texto)
    parada = "|".join(_padrao_rotulo(r) for r in paradas)
    for rotulo in rotulos:
        padrao = re.compile(
            rf"(?<!\w){_padrao_rotulo(rotulo)}\s*:\s*(.*?)\s*(?=(?<!\w)(?:{parada})(?!\w)|$)"
        )
        for m in padrao.finditer(norm):
            valor = texto[m.start(1):m.end(1)].strip(_APARAR)
            if not valor:
                continue
            if len(valor) > limite:
                raise ValorInvalido(
                    f"O valor depois de '{rotulo}:' ficou longo demais; "
                    "confira STOP_LABELS em config.py"
                )
            return valor
    return None


def extrair_data(valor: Optional[str]) -> Optional[str]:
    """Pega só a data (dd/mm/aaaa) de um trecho; sem data, aceita textos curtos."""
    valor = _colapsar(valor or "")
    if not valor:
        return None
    m = _DATA_RE.search(valor[:60])
    if m:
        return m.group(0)
    return valor if len(valor) <= 40 else None


def separar_versao_e_data(texto: str) -> Tuple[str, Optional[str]]:
    """'0.2.9b + DLC Data da Atualização: 08/08/2026' -> ('0.2.9b + DLC', '08/08/2026')."""
    texto = _colapsar(texto)
    rotulos = "|".join(_padrao_rotulo(r) for r in config.LABELS_DATA)
    m = re.search(rf"(?<!\w)(?:{rotulos})\s*:?\s*", dobrar(texto))
    if not m:
        return texto.strip(_APARAR), None
    return texto[: m.start()].strip(_APARAR), extrair_data(texto[m.end():])


def normalizar_versao(texto: Optional[str]) -> str:
    """Forma canônica para comparar versões: sem caixa/acento e sem 'v' inicial."""
    norm = _colapsar(dobrar(texto or "")).strip(_APARAR)
    return re.sub(r"(?<!\w)v(?=\d)", "", norm)


def houve_atualizacao(versao_local: Optional[str], versao_site: Optional[str]) -> bool:
    if not versao_site:
        return False
    return normalizar_versao(versao_site) != normalizar_versao(versao_local)
