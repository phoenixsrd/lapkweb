import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

import config


@dataclass
class Jogo:
    id: int
    nome: str
    url: str
    versao_local: str
    versao_site: Optional[str] = None
    atualizado_em: Optional[str] = None
    ultima_verificacao: Optional[str] = None
    erro: Optional[str] = None


def _garantir_arquivo() -> None:
    os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
    if not os.path.exists(config.DATA_FILE):
        with open(config.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def carregar_jogos() -> list[Jogo]:
    _garantir_arquivo()
    with open(config.DATA_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return [Jogo(**d) for d in dados]


def salvar_jogos(jogos: list[Jogo]) -> None:
    _garantir_arquivo()
    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(j) for j in jogos], f, ensure_ascii=False, indent=2)


def adicionar_jogo(nome: str, url: str, versao_local: str) -> Jogo:
    jogos = carregar_jogos()
    novo_id = max([j.id for j in jogos], default=0) + 1
    jogo = Jogo(id=novo_id, nome=nome, url=url, versao_local=versao_local)
    jogos.append(jogo)
    salvar_jogos(jogos)
    return jogo


def buscar_jogo(jogo_id: int) -> Optional[Jogo]:
    for j in carregar_jogos():
        if j.id == jogo_id:
            return j
    return None


def atualizar_jogo(jogo_id: int, **campos) -> Optional[Jogo]:
    jogos = carregar_jogos()
    alvo = None
    for j in jogos:
        if j.id == jogo_id:
            for chave, valor in campos.items():
                setattr(j, chave, valor)
            alvo = j
            break
    if alvo:
        salvar_jogos(jogos)
    return alvo


def excluir_jogo(jogo_id: int) -> None:
    jogos = [j for j in carregar_jogos() if j.id != jogo_id]
    salvar_jogos(jogos)