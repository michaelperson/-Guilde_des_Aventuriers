from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Guilde

guildes_bp = Blueprint("guildes", __name__, url_prefix="/guildes")


@guildes_bp.get("")
def list_guildes():
    guildes = Guilde.query.all()
    return jsonify([g.to_dict() for g in guildes])


@guildes_bp.get("/<int:guilde_id>")
def get_guilde(guilde_id):
    guilde = db.session.get(Guilde, guilde_id)
    if guilde is None:
        return jsonify({"error": "guilde introuvable"}), 404
    return jsonify(guilde.to_dict(with_aventuriers=True))


@guildes_bp.post("")
def create_guilde():
    payload = request.get_json(silent=True) or {}
    nom = payload.get("nom")
    if not nom:
        return jsonify({"error": "le champ 'nom' est requis"}), 400

    if Guilde.query.filter_by(nom=nom).first() is not None:
        return jsonify({"error": "une guilde avec ce nom existe deja"}), 400

    guilde = Guilde(nom=nom, reputation=payload.get("reputation", 0))
    db.session.add(guilde)
    db.session.commit()
    return jsonify(guilde.to_dict()), 201


@guildes_bp.put("/<int:guilde_id>")
def update_guilde(guilde_id):
    guilde = db.session.get(Guilde, guilde_id)
    if guilde is None:
        return jsonify({"error": "guilde introuvable"}), 404

    payload = request.get_json(silent=True) or {}
    if "nom" in payload:
        guilde.nom = payload["nom"]
    if "reputation" in payload:
        guilde.reputation = payload["reputation"]

    db.session.commit()
    return jsonify(guilde.to_dict())


@guildes_bp.delete("/<int:guilde_id>")
def delete_guilde(guilde_id):
    guilde = db.session.get(Guilde, guilde_id)
    if guilde is None:
        return jsonify({"error": "guilde introuvable"}), 404

    db.session.delete(guilde)
    db.session.commit()
    return "", 204
