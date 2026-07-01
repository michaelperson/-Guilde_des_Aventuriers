from flask_sqlalchemy import SQLAlchemy

# Instance unique partagee par toute l'application. On la cree ici,
# separement de create_app(), pour eviter les imports circulaires entre
# les modeles et l'application elle-meme.
db = SQLAlchemy()
