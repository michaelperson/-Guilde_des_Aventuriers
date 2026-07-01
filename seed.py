"""Peuple la base de donnees avec des donnees de demonstration.

Ce script vide les tables avant de les repeupler (db.drop_all suivi de
db.create_all) : on peut donc le relancer autant de fois que necessaire
sans dupliquer les donnees ni tomber sur une contrainte d'unicite.
"""
from guilde_api import create_app
from guilde_api.extensions import db
from guilde_api.models import Aventurier, Guilde, Monstre, Quete


def seed():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        guilde_aigles = Guilde(nom="Les Aigles d'Acier", reputation=10)
        guilde_ombres = Guilde(nom="La Confrerie des Ombres", reputation=5)
        db.session.add_all([guilde_aigles, guilde_ombres])
        db.session.flush()  # attribue les id sans attendre le commit final

        rakan = Aventurier(nom="Rakan", classe="Guerrier", niveau=5, guilde_id=guilde_aigles.id)
        yseult = Aventurier(nom="Yseult", classe="Mage", niveau=7, guilde_id=guilde_aigles.id)
        korran = Aventurier(nom="Korran", classe="Voleur", niveau=4, guilde_id=guilde_ombres.id)
        elowen = Aventurier(nom="Elowen", classe="Archere", niveau=6, guilde_id=guilde_ombres.id)
        db.session.add_all([rakan, yseult, korran, elowen])
        db.session.flush()

        quete_mine = Quete(titre="Nettoyer la mine abandonnee", difficulte="moyenne", recompense=100)
        quete_foret = Quete(titre="Escorter la caravane en foret noire", difficulte="difficile", recompense=250)
        db.session.add_all([quete_mine, quete_foret])
        db.session.flush()

        quete_mine.aventuriers.extend([rakan, korran])
        quete_foret.aventuriers.extend([yseult, elowen])

        db.session.add_all([
            Monstre(nom="Rat geant", puissance=2, quete_id=quete_mine.id),
            Monstre(nom="Gobelin des tunnels", puissance=4, quete_id=quete_mine.id),
            Monstre(nom="Loup de l'ombre", puissance=6, quete_id=quete_foret.id),
        ])

        db.session.commit()

        print(
            "Base peuplee : {} guildes, {} aventuriers, {} quetes, {} monstres".format(
                Guilde.query.count(),
                Aventurier.query.count(),
                Quete.query.count(),
                Monstre.query.count(),
            )
        )


if __name__ == "__main__":
    seed()
