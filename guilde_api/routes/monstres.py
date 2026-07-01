from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Monstre, Quete

monstres_bp = Blueprint("monstres", __name__, url_prefix="/monstres")


@monstres_bp.get("")
def list_monstres():
    monstres = Monstre.query.all()
    return jsonify([m.to_dict() for m in monstres])


@monstres_bp.get("/<int:monstre_id>")
def get_monstre(monstre_id):
    monstre = db.session.get(Monstre, monstre_id)
    if monstre is None:
        return jsonify({"error": "monstre introuvable"}), 404
    return jsonify(monstre.to_dict())


@monstres_bp.post("")
def create_monstre():
    payload = request.get_json(silent=True) or {}
    nom = payload.get("nom")
    quete_id = payload.get("quete_id")

    if not nom or not quete_id:
        return jsonify({"error": "les champs 'nom' et 'quete_id' sont requis"}), 400

    quete = db.session.get(Quete, quete_id)
    if quete is None:
        return jsonify({"error": "quete_id ne correspond a aucune quete"}), 400

    monstre = Monstre(nom=nom, puissance=payload.get("puissance", 1), quete_id=quete_id)
    db.session.add(monstre)
    db.session.commit()
    return jsonify(monstre.to_dict()), 201


@monstres_bp.put("/<int:monstre_id>")
def update_monstre(monstre_id):
    monstre = db.session.get(Monstre, monstre_id)
    if monstre is None:
        return jsonify({"error": "monstre introuvable"}), 404

    payload = request.get_json(silent=True) or {}

    if "quete_id" in payload:
        quete = db.session.get(Quete, payload["quete_id"])
        if quete is None:
            return jsonify({"error": "quete_id ne correspond a aucune quete"}), 400
        monstre.quete_id = payload["quete_id"]

    for field in ("nom", "puissance"):
        if field in payload:
            setattr(monstre, field, payload[field])

    db.session.commit()
    return jsonify(monstre.to_dict())


@monstres_bp.delete("/<int:monstre_id>")
def delete_monstre(monstre_id):
    monstre = db.session.get(Monstre, monstre_id)
    if monstre is None:
        return jsonify({"error": "monstre introuvable"}), 404

    db.session.delete(monstre)
    db.session.commit()
    return "", 204
