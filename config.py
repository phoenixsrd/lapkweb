import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "jogos.json")

HOST = "0.0.0.0"
PORT = 5000
DEBUG = False

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
REQUEST_TIMEOUT = 15

LABEL_VERSAO = "versão do jogo"
LABEL_ATUALIZADO_EM = "atualizado em"

STOP_LABELS = [
    "tradução",
    "traducao",
    "idioma",
    "plataforma",
    "censura",
    "desenvolvedor",
    "criador de",
]