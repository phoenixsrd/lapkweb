"""Datas e horários: gravação em ISO 8601 e exibição amigável."""
import re
from datetime import datetime
from typing import Optional

_LEGADO_RE = re.compile(r"^(\d{2})/(\d{2}) (\d{2}):(\d{2})$")


def agora_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ler_iso(texto: Optional[str]) -> Optional[datetime]:
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def converter_legado(texto: Optional[str], referencia: Optional[datetime] = None) -> Optional[str]:
    """Converte o formato antigo 'dd/mm HH:MM' (sem ano) para ISO 8601.

    Se a data cair no futuro, assume o ano anterior. Textos que não seguem o
    formato antigo (ou já estão em ISO) voltam sem alteração.
    """
    if not texto:
        return texto
    m = _LEGADO_RE.match(texto.strip())
    if not m:
        return texto
    dia, mes, hora, minuto = (int(x) for x in m.groups())
    ref = referencia or datetime.now()
    try:
        dt = datetime(ref.year, mes, dia, hora, minuto)
        if (dt - ref.replace(tzinfo=None)).days >= 1:
            dt = dt.replace(year=ref.year - 1)
        return dt.astimezone().isoformat(timespec="seconds")
    except ValueError:
        return texto


def data_hora(texto: Optional[str]) -> str:
    dt = ler_iso(texto)
    if dt is None:
        return texto or ""
    return dt.strftime("%d/%m/%Y %H:%M")


def tempo_relativo(texto: Optional[str]) -> str:
    dt = ler_iso(texto)
    if dt is None:
        return texto or ""
    segundos = max(0, int((datetime.now(dt.tzinfo) - dt).total_seconds()))
    if segundos < 60:
        return "agora há pouco"
    if segundos < 3600:
        return f"há {segundos // 60} min"
    if segundos < 86400:
        return f"há {segundos // 3600} h"
    if segundos < 7 * 86400:
        dias = segundos // 86400
        return "há 1 dia" if dias == 1 else f"há {dias} dias"
    return dt.strftime("%d/%m/%Y")
