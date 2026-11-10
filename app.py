import logging
import os

from flask import Flask

import agendador
import config
import erros
import seguranca
import storage
from routes import bp


def criar_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    seguranca.init_app(app)
    erros.registrar(app)
    app.register_blueprint(bp)
    try:
        storage.migrar_arquivo()
    except storage.ArmazenamentoCorrompido as e:
        # Sobe mesmo assim: o navegador mostra a mensagem em vez de o servidor cair.
        app.logger.error("%s", e)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = criar_app()
    # Com o recarregador do modo debug há dois processos; só o filho liga o agendador.
    if not config.DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        agendador.iniciar()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
