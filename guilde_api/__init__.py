from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    """Cree et configure l'application Flask.

    On utilise le pattern app factory plutot qu'une instance Flask
    globale : ca permet de creer plusieurs instances de l'app avec des
    configurations differentes (developpement, tests) sans effets de
    bord entre elles, ce qui est precisement ce dont on a besoin pour
    faire tourner les tests avec une base en memoire.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .routes.guildes import guildes_bp
    from .routes.aventuriers import aventuriers_bp
    from .routes.quetes import quetes_bp
    from .routes.monstres import monstres_bp

    app.register_blueprint(guildes_bp)
    app.register_blueprint(aventuriers_bp)
    app.register_blueprint(quetes_bp)
    app.register_blueprint(monstres_bp)

    @app.route("/")
    def index():
        return {"message": "API de la Guilde des Aventuriers", "status": "ok"}

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "ressource introuvable"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return {"error": "methode non autorisee sur cette route"}, 405

    with app.app_context():
        # create_all() suffit pour cet exercice. Sur un vrai projet en
        # production on passerait par des migrations (Alembic) pour ne
        # pas ecraser le schema a chaque redemarrage.
        db.create_all()

    return app
