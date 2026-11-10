"""Regras de negócio da verificação (usadas pelas rotas e pelo agendador)."""
from dataclasses import dataclass, replace
from typing import Iterable, Optional

import scraper
import tempo
from storage import Jogo, atualizar_varios, carregar_jogos


@dataclass
class Resumo:
    verificados: int = 0
    pendentes: int = 0
    erros: int = 0


def _campos_apos_verificacao(jogo: Jogo, resultado: scraper.Resultado, agora: str) -> dict:
    campos = {"ultima_verificacao": agora, "erro": resultado.erro}

    if resultado.erro:
        # Falha temporária não apaga o que já se sabia sobre a versão do site.
        return campos

    campos["versao_site"] = resultado.versao
    campos["atualizado_em"] = resultado.atualizado_em

    if replace(jogo, **campos).tem_atualizacao:
        mesma_novidade = (
            jogo.detectado_em
            and jogo.versao_site == resultado.versao
            and jogo.atualizado_em == resultado.atualizado_em
        )
        campos["detectado_em"] = jogo.detectado_em if mesma_novidade else agora
    else:
        campos["detectado_em"] = None
    return campos


def verificar(ids: Optional[Iterable[int]] = None) -> Resumo:
    """Verifica os jogos indicados (ou todos, se `ids` for None) e grava tudo de uma vez."""
    alvo = None if ids is None else set(ids)
    jogos = [j for j in carregar_jogos() if alvo is None or j.id in alvo]
    if not jogos:
        return Resumo()

    resultados = scraper.verificar_varios({j.id: j.url for j in jogos})
    agora = tempo.agora_iso()
    mudancas = {j.id: _campos_apos_verificacao(j, resultados[j.id], agora) for j in jogos}
    atualizados = atualizar_varios(mudancas)

    return Resumo(
        verificados=len(jogos),
        pendentes=sum(1 for j in atualizados if j.tem_atualizacao),
        erros=sum(1 for j in atualizados if j.erro),
    )
