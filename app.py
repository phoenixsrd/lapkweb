from flask import Flask

import config
from routes import bp


def criar_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    criar_app().run(host=config.HOST, port=config.PORT, debug=config.DEBUG)