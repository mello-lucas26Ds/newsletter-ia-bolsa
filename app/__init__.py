# Factory Pattern do Flask. Permite criar multiplas instancias (util para testes).

from flask import Flask
from config import CONFIG


def criar_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(CONFIG.diretorio_templates),
        static_folder=str(CONFIG.diretorio_static),
    )
    
    app.config["SECRET_KEY"] = CONFIG.secret_key
    app.config["DEBUG"] = CONFIG.flask_debug
    
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app