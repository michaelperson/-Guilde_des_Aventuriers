from .extensions import db

# Table d'association pour la relation N-N entre aventuriers et quetes.
# Un aventurier peut participer a plusieurs quetes, une quete peut
# reunir plusieurs aventuriers. Comme cette table ne porte aucune donnee
# propre (pas de colonne "role" ou "date d'ajout"), une simple
# db.Table suffit ; on eviterait ce raccourci si on avait besoin de
# stocker des informations sur la participation elle-meme.
participations = db.Table(
    "participations",
    db.Column("aventurier_id", db.Integer, db.ForeignKey("aventuriers.id"), primary_key=True),
    db.Column("quete_id", db.Integer, db.ForeignKey("quetes.id"), primary_key=True),
)


class Guilde(db.Model):
    __tablename__ = "guildes"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    reputation = db.Column(db.Integer, default=0, nullable=False)

    aventuriers = db.relationship(
        "Aventurier", back_populates="guilde", cascade="all, delete-orphan"
    )

    def to_dict(self, with_aventuriers=False):
        data = {
            "id": self.id,
            "nom": self.nom,
            "reputation": self.reputation,
        }
        if with_aventuriers:
            data["aventuriers"] = [a.to_dict() for a in self.aventuriers]
        return data


class Aventurier(db.Model):
    __tablename__ = "aventuriers"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    classe = db.Column(db.String(50), nullable=False)
    niveau = db.Column(db.Integer, default=1, nullable=False)
    guilde_id = db.Column(db.Integer, db.ForeignKey("guildes.id"), nullable=False)

    guilde = db.relationship("Guilde", back_populates="aventuriers")
    quetes = db.relationship("Quete", secondary=participations, back_populates="aventuriers")

    def to_dict(self, with_guilde=False, with_quetes=False):
        data = {
            "id": self.id,
            "nom": self.nom,
            "classe": self.classe,
            "niveau": self.niveau,
            "guilde_id": self.guilde_id,
        }
        if with_guilde and self.guilde is not None:
            data["guilde"] = {"id": self.guilde.id, "nom": self.guilde.nom}
        if with_quetes:
            data["quetes"] = [q.to_dict() for q in self.quetes]
        return data


class Quete(db.Model):
    __tablename__ = "quetes"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(120), nullable=False)
    difficulte = db.Column(db.String(20), nullable=False, default="normale")
    recompense = db.Column(db.Integer, default=0, nullable=False)
    terminee = db.Column(db.Boolean, default=False, nullable=False)

    aventuriers = db.relationship("Aventurier", secondary=participations, back_populates="quetes")
    monstres = db.relationship("Monstre", back_populates="quete", cascade="all, delete-orphan")

    def to_dict(self, with_relations=False):
        data = {
            "id": self.id,
            "titre": self.titre,
            "difficulte": self.difficulte,
            "recompense": self.recompense,
            "terminee": self.terminee,
        }
        if with_relations:
            data["aventuriers"] = [a.to_dict() for a in self.aventuriers]
            data["monstres"] = [m.to_dict() for m in self.monstres]
        return data


class Monstre(db.Model):
    __tablename__ = "monstres"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    puissance = db.Column(db.Integer, default=1, nullable=False)
    quete_id = db.Column(db.Integer, db.ForeignKey("quetes.id"), nullable=False)

    quete = db.relationship("Quete", back_populates="monstres")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "puissance": self.puissance,
            "quete_id": self.quete_id,
        }
