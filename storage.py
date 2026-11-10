"""Persistência dos jogos em JSON, com escrita atômica e trava entre threads."""
import json
import logging
import os
import shutil
import tempfile
import threading
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import Dict, List, Optional

import config
import tempo
from versoes import houve_atualizacao, separar_versao_e_data

log = logging.getLogger(__name__)
_lock = threading.RLock()


class ArmazenamentoCorrompido(RuntimeError):
    """O arquivo de dados existe, mas não é um JSON válido."""


@dataclass
class Jogo:
    id: int
    nome: str
    url: str
    versao_local: str
    versao_site: Optional[str] = None
    atualizado_em: Optional[str] = None
    ultima_verificacao: Optional[str] = None
    detectado_em: Optional[str] = None
    erro: Optional[str] = None

    @property
    def tem_atualizacao(self) -> bool:
        return houve_atualizacao(self.versao_local, self.versao_site)

    @property
    def status(self) -> str:
        if self.erro:
            return "erro"
        if self.tem_atualizacao:
            return "stale"
        if self.versao_site:
            return "ok"
        return "pendente"

    @property
    def url_segura(self) -> bool:
        return self.url.lower().startswith(("http://", "https://"))


_CAMPOS = {f.name for f in fields(Jogo)}


# --- Leitura / escrita -------------------------------------------------------
def _garantir_arquivo() -> None:
    os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
    if not os.path.exists(config.DATA_FILE):
        _gravar_bruto([])


def _ler_bruto() -> list:
    _garantir_arquivo()
    try:
        with open(config.DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as e:
        raise ArmazenamentoCorrompido(
            f"O arquivo {config.DATA_FILE} não é um JSON válido ({e}). "
            "Corrija ou restaure um backup; nada foi sobrescrito."
        ) from e
    if not isinstance(dados, list):
        raise ArmazenamentoCorrompido(f"O arquivo {config.DATA_FILE} deveria conter uma lista de jogos.")
    return dados


def _gravar_bruto(dados: list) -> None:
    pasta = os.path.dirname(config.DATA_FILE)
    os.makedirs(pasta, exist_ok=True)
    fd, caminho_tmp = tempfile.mkstemp(dir=pasta, prefix=".jogos-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(caminho_tmp, config.DATA_FILE)
    except BaseException:
        try:
            os.unlink(caminho_tmp)
        except OSError:
            pass
        raise


def _migrar_registro(d: dict, referencia: Optional[datetime] = None) -> Jogo:
    """Aceita registros do formato antigo e descarta campos desconhecidos.

    - 'versao_local'/'versao_site' com 'Data da Atualização: ...' embutida são separadas;
    - 'ultima_verificacao' no formato 'dd/mm HH:MM' vira ISO 8601.
    """
    d = {k: v for k, v in d.items() if k in _CAMPOS}

    versao_local, _ = separar_versao_e_data(d.get("versao_local") or "")
    d["versao_local"] = versao_local

    if d.get("versao_site"):
        versao_site, data_site = separar_versao_e_data(d["versao_site"])
        d["versao_site"] = versao_site or None
        if not d.get("atualizado_em"):
            d["atualizado_em"] = data_site

    d["ultima_verificacao"] = tempo.converter_legado(d.get("ultima_verificacao"), referencia)
    return Jogo(**d)


def _salvar(jogos: List[Jogo]) -> None:
    _gravar_bruto([asdict(j) for j in jogos])


def carregar_jogos() -> List[Jogo]:
    with _lock:
        return [_migrar_registro(d) for d in _ler_bruto()]


def salvar_jogos(jogos: List[Jogo]) -> None:
    with _lock:
        _salvar(jogos)


def migrar_arquivo() -> bool:
    """Atualiza o arquivo para o formato atual, guardando um backup do original.

    Devolve True se houve mudança. É seguro chamar a cada inicialização.
    """
    with _lock:
        bruto = _ler_bruto()
        migrado = [asdict(_migrar_registro(d)) for d in bruto]
        if migrado == bruto:
            return False
        backup = f"{config.DATA_FILE}.bak-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copy2(config.DATA_FILE, backup)
        _gravar_bruto(migrado)
        log.info("Dados migrados para o formato novo. Backup em %s", backup)
        return True


# --- Operações ---------------------------------------------------------------
def adicionar_jogo(nome: str, url: str, versao_local: str) -> Jogo:
    with _lock:
        jogos = carregar_jogos()
        novo_id = max([j.id for j in jogos], default=0) + 1
        jogo = Jogo(id=novo_id, nome=nome, url=url, versao_local=versao_local)
        jogos.append(jogo)
        _salvar(jogos)
        return jogo


def buscar_jogo(jogo_id: int) -> Optional[Jogo]:
    for j in carregar_jogos():
        if j.id == jogo_id:
            return j
    return None


def atualizar_varios(mudancas: Dict[int, dict]) -> List[Jogo]:
    """Aplica várias alterações com uma única leitura e uma única gravação."""
    with _lock:
        jogos = carregar_jogos()
        alterados = []
        for j in jogos:
            campos = mudancas.get(j.id)
            if campos is None:
                continue
            desconhecidos = set(campos) - _CAMPOS
            if desconhecidos:
                raise TypeError(f"Campos desconhecidos: {sorted(desconhecidos)}")
            for chave, valor in campos.items():
                setattr(j, chave, valor)
            alterados.append(j)
        if alterados:
            _salvar(jogos)
        return alterados


def atualizar_jogo(jogo_id: int, **campos) -> Optional[Jogo]:
    alterados = atualizar_varios({jogo_id: campos})
    return alterados[0] if alterados else None


def excluir_jogo(jogo_id: int) -> bool:
    with _lock:
        jogos = carregar_jogos()
        restantes = [j for j in jogos if j.id != jogo_id]
        if len(restantes) == len(jogos):
            return False
        _salvar(restantes)
        return True
