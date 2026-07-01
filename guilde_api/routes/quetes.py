from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Aventurier, Quete

quetes_bp = Blueprint("quetes", __name__, url_prefix="/quetes")


@quetes_bp.get("")
def list_quetes():
    quetes = Quete.query.all()
    return jsonify([q.to_dict() for q in quetes])


@quetes_bp.get("/<int:quete_id>")
def get_quete(quete_id):
    quete = db.session.get(Quete, quete_id)
    if quete is None:
        return jsonify({"error": "quete introuvable"}), 404
    return jsonify(quete.to_dict(with_relations=True))


@quetes_bp.post("")
def create_quete():
    payload = request.get_json(silent=True) or {}
    titre = payload.get("titre")
    if not titre:
        return jsonify({"error": "le champ 'titre' est requis"}), 400

    quete = Quete(
        titre=titre,
        difficulte=payload.get("difficulte", "normale"),
        recompense=payload.get("recompense", 0),
    )
    db.session.add(quete)
    db.session.commit()
    return jsonify(quete.to_dict()), 201


@quetes_bp.put("/<int:quete_id>")
def update_quete(quete_id):
    quete = db.session.get(Quete, quete_id)
    if quete is None:
        return jsonify({"error": "quete introuvable"}), 404

    payload = request.get_json(silent=True) or {}
    for field in ("titre", "difficulte", "recompense"):
        if field in payload:
            setattr(quete, field, payload[field])

    db.session.commit()
    return jsonify(quete.to_dict())


@quetes_bp.delete("/<int:quete_id>")
def delete_quete(quete_id):
    quete = db.session.get(Quete, quete_id)
    if quete is None:
        return jsonify({"error": "quete introuvable"}), 404

    db.session.delete(quete)
    db.session.commit()
    return "", 204


# --- Endpoints "metier" : ce n'est pas du CRUD, ce sont les deux
# operations qui donnent son sens a la relation N-N et qui justifient
# l'existence de cette API plutot qu'un simple export de tables.


@quetes_bp.post("/<int:quete_id>/aventuriers/<int:aventurier_id>")
def assigner_aventurier(quete_id, aventurier_id):
    """Assigne un aventurier a une quete (alimente la table de jointure)."""
    quete = db.session.get(Quete, quete_id)
    aventurier = db.session.get(Aventurier, aventurier_id)

    if quete is None or aventurier is None:
        return jsonify({"error": "quete ou aventurier introuvable"}), 404

    if quete.terminee:
        return jsonify({"error": "impossible d'assigner un aventurier a une quete terminee"}), 400

    if aventurier in quete.aventuriers:
        return jsonify({"error": "cet aventurier participe deja a cette quete"}), 400

    quete.aventuriers.append(aventurier)
    db.session.commit()
    return jsonify(quete.to_dict(with_relations=True)), 201


@quetes_bp.delete("/<int:quete_id>/aventuriers/<int:aventurier_id>")
def retirer_aventurier(quete_id, aventurier_id):
    """Retire un aventurier d'une quete."""
    quete = db.session.get(Quete, quete_id)
    aventurier = db.session.get(Aventurier, aventurier_id)

    if quete is None or aventurier is None:
        return jsonify({"error": "quete ou aventurier introuvable"}), 404

    if aventurier not in quete.aventuriers:
        return jsonify({"error": "cet aventurier ne participe pas a cette quete"}), 400

    quete.aventuriers.remove(aventurier)
    db.session.commit()
    return "", 204


@quetes_bp.post("/<int:quete_id>/cloturer")
def cloturer_quete(quete_id):
    """Cloture une quete et distribue la recompense aux guildes concernees.

    Regle metier retenue : chaque guilde ayant au moins un aventurier
    ayant participe a la quete recoit un bonus de reputation egal a la
    recompense de la quete (pas une part proportionnelle : c'est un choix
    volontairement simple, a discuter si on voulait affiner la mecanique
    de jeu). Une quete deja terminee ne peut pas etre cloturee une
    seconde fois, pour ne pas distribuer la recompense en double.
    """
    quete = db.session.get(Quete, quete_id)
    if quete is None:
        return jsonify({"error": "quete introuvable"}), 404

    if quete.terminee:
        return jsonify({"error": "cette quete est deja terminee"}), 400

    if not quete.aventuriers:
        return jsonify({"error": "impossible de cloturer une quete sans participant"}), 400

    guildes_concernees = {a.guilde for a in quete.aventuriers if a.guilde is not None}
    for guilde in guildes_concernees:
        guilde.reputation += quete.recompense

    quete.terminee = True
    db.session.commit()

    return jsonify({
        "quete": quete.to_dict(),
        "guildes_recompensees": [g.to_dict() for g in guildes_concernees],
    })
