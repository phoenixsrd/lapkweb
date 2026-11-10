import os


def _env_texto(nome: str, padrao: str) -> str:
    valor = os.environ.get(nome)
    return valor if valor not in (None, "") else padrao


def _env_numero(nome: str, padrao, tipo=int):
    try:
        return tipo(os.environ[nome])
    except (KeyError, ValueError):
        return padrao


def _env_bool(nome: str, padrao: bool) -> bool:
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


# --- Armazenamento -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = _env_texto("LAPKWEB_DATA_DIR", os.path.join(BASE_DIR, "data"))
DATA_FILE = os.path.join(DATA_DIR, "jogos.json")
SECRET_KEY_FILE = os.path.join(DATA_DIR, ".secret_key")

# --- Servidor ----------------------------------------------------------------
HOST = _env_texto("LAPKWEB_HOST", "0.0.0.0")
PORT = _env_numero("LAPKWEB_PORT", 5000)
DEBUG = _env_bool("LAPKWEB_DEBUG", False)

# Verificação automática em segundo plano (em horas). 0 = desligada.
VERIFICAR_A_CADA_HORAS = _env_numero("LAPKWEB_VERIFICAR_A_CADA_HORAS", 0.0, float)

# --- Requisições de scraping -------------------------------------------------
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
REQUEST_TIMEOUT = 15          # segundos
REQUEST_RETRIES = 2           # novas tentativas em erros 5xx / falhas de conexão
MAX_WORKERS = 3               # páginas verificadas em paralelo
MAX_BYTES = 3 * 1024 * 1024   # só lê o começo de páginas gigantes

# --- Rótulos usados para achar as informações no texto da página ---------------
# Maiúsculas e acentos não importam. O primeiro rótulo de cada lista é o principal.
LABELS_VERSAO = ["versão do jogo", "versão atual", "game version"]
LABELS_DATA = ["data da atualização", "atualizado em", "última atualização"]

# Rótulos que marcam o FIM do valor capturado (além dos de versão e data acima).
STOP_LABELS = [
    "tradução",
    "idioma",
    "plataforma",
    "censura",
    "desenvolvedor",
    "criador de",
]
