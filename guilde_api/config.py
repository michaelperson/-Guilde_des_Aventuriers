import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "guilde.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Mettre SQL_ECHO=1 dans l'environnement pour voir passer les requetes
    # SQL generees par SQLAlchemy - utile pour reperer un probleme de N+1.
    SQLALCHEMY_ECHO = os.environ.get("SQL_ECHO", "0") == "1"


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    SQLALCHEMY_ECHO = False
