from flask import Blueprint, jsonify, request
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import Aventurier, Guilde

aventuriers_bp = Blueprint("aventuriers", __name__, url_prefix="/aventuriers")


@aventuriers_bp.get("")
def list_aventuriers():
    # Le parametre ?with_guilde=1 inclut la guilde de chaque aventurier
    # dans la reponse. On charge cette relation avec selectinload plutot
    # que de laisser SQLAlchemy la recuperer en lazy loading dans la
    # boucle de serialisation ci-dessous : sans ca, lister 20 aventuriers
    # avec leur guilde declencherait 1 requete pour la liste puis 1
    # requete par aventurier pour aller chercher sa guilde, soit 21
    # requetes SQL au lieu de 2 (le probleme classique du "N+1").
    with_guilde = request.args.get("with_guilde") == "1"

    query = Aventurier.query
    if with_guilde:
        query = query.options(selectinload(Aventurier.guilde))

    aventuriers = query.all()
    return jsonify([a.to_dict(with_guilde=with_guilde) for a in aventuriers])


@aventuriers_bp.get("/<int:aventurier_id>")
def get_aventurier(aventurier_id):
    aventurier = db.session.get(Aventurier, aventurier_id)
    if aventurier is None:
        return jsonify({"error": "aventurier introuvable"}), 404
    return jsonify(aventurier.to_dict(with_guilde=True, with_quetes=True))


@aventuriers_bp.post("")
def create_aventurier():
    payload = request.get_json(silent=True) or {}
    nom = payload.get("nom")
    classe = payload.get("classe")
    guilde_id = payload.get("guilde_id")

    if not nom or not classe or not guilde_id:
        return jsonify({"error": "les champs 'nom', 'classe' et 'guilde_id' sont requis"}), 400

    guilde = db.session.get(Guilde, guilde_id)
    if guilde is None:
        return jsonify({"error": "guilde_id ne correspond a aucune guilde"}), 400

    aventurier = Aventurier(
        nom=nom,
        classe=classe,
        niveau=payload.get("niveau", 1),
        guilde_id=guilde_id,
    )
    db.session.add(aventurier)
    db.session.commit()
    return jsonify(aventurier.to_dict()), 201


@aventuriers_bp.put("/<int:aventurier_id>")
def update_aventurier(aventurier_id):
    aventurier = db.session.get(Aventurier, aventurier_id)
    if aventurier is None:
        return jsonify({"error": "aventurier introuvable"}), 404

    payload = request.get_json(silent=True) or {}

    if "guilde_id" in payload:
        guilde = db.session.get(Guilde, payload["guilde_id"])
        if guilde is None:
            return jsonify({"error": "guilde_id ne correspond a aucune guilde"}), 400
        aventurier.guilde_id = payload["guilde_id"]

    for field in ("nom", "classe", "niveau"):
        if field in payload:
            setattr(aventurier, field, payload[field])

    db.session.commit()
    return jsonify(aventurier.to_dict())


@aventuriers_bp.delete("/<int:aventurier_id>")
def delete_aventurier(aventurier_id):
    aventurier = db.session.get(Aventurier, aventurier_id)
    if aventurier is None:
        return jsonify({"error": "aventurier introuvable"}), 404

    db.session.delete(aventurier)
    db.session.commit()
    return "", 204
