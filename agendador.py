"""Verificação periódica em segundo plano (opcional)."""
import logging
import threading
from typing import Optional

import config
import servico

log = logging.getLogger(__name__)
ATRASO_INICIAL = 10  # segundos entre subir o servidor e a primeira verificação


def _loop(intervalo_s: float, parar: threading.Event) -> None:
    espera = ATRASO_INICIAL
    while not parar.wait(espera):
        try:
            r = servico.verificar()
            log.info("Verificação automática: %d jogos, %d com atualização, %d com erro",
                     r.verificados, r.pendentes, r.erros)
        except Exception:
            log.exception("Falha na verificação automática")
        espera = intervalo_s


def iniciar() -> Optional[threading.Event]:
    """Liga a thread se LAPKWEB_VERIFICAR_A_CADA_HORAS > 0. Devolve o evento para parar."""
    horas = config.VERIFICAR_A_CADA_HORAS
    if horas <= 0:
        return None
    parar = threading.Event()
    threading.Thread(target=_loop, args=(horas * 3600, parar), daemon=True, name="lapkweb-agendador").start()
    log.info("Verificação automática ligada: a cada %g h", horas)
    return parar
