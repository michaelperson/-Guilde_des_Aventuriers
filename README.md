# La Guilde des Aventuriers - API

Corrigé de l'exercice. Ceci est une implémentation de référence du cahier
des charges, pas la seule façon valable de faire : les choix
d'organisation du code, de règles métier ou de nommage pris ici sont
justifiés au fil du document, mais une autre équipe a pu faire des choix
différents et tout aussi corrects.

## Stack

Python 3, Flask, Flask-SQLAlchemy, SQLite (fichier local), pytest pour
les tests. Aucune dépendance d'authentification ou de sécurité : c'est
volontaire, voir la section "Hors scope" plus bas.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Lancer le projet

```bash
python seed.py    # cree la base et la remplit avec des donnees de demo
python run.py      # demarre le serveur de developpement sur le port 5000
```

`seed.py` vide et recrée les tables à chaque exécution : on peut le
relancer sans risque de duplication.

## Lancer les tests

```bash
pytest
```

Neuf tests couvrent le CRUD de base, la relation N-N entre aventuriers et
quêtes, la logique métier de clôture de quête, la cascade de suppression
et les cas d'erreur (400/404).

## Structure du projet

```
guilde_aventuriers_api/
  guilde_api/
    __init__.py       app factory, enregistrement des blueprints
    config.py         configuration (dev / tests)
    extensions.py     instance SQLAlchemy partagee
    models.py         Guilde, Aventurier, Quete, Monstre
    routes/
      guildes.py
      aventuriers.py
      quetes.py
      monstres.py
      docs.py
    openapi.json
  tests/
    conftest.py
    test_api.py
  seed.py
  run.py
  requirements.txt
  pytest.ini
```

Ce découpage (app factory + blueprints par ressource) est un choix parmi
d'autres. Il a été retenu ici parce qu'il isole bien la config de test de
la config de dev et qu'il garde chaque fichier de routes concentré sur
une seule ressource.

## Modèle de données

Quatre entités :

- **Guilde** : `id`, `nom` (unique), `reputation`.
- **Aventurier** : `id`, `nom`, `classe`, `niveau`, `guilde_id` (FK vers
  Guilde). Relation 1-N : une guilde a plusieurs aventuriers, chaque
  aventurier appartient à une seule guilde.
- **Quete** : `id`, `titre`, `difficulte`, `recompense`, `terminee`.
- **Monstre** : `id`, `nom`, `puissance`, `quete_id` (FK vers Quete).
  Deuxième relation 1-N : une quête a plusieurs monstres.
- Relation N-N entre **Aventurier** et **Quete**, portée par la table
  `participations` (aucune colonne propre, donc une simple `db.Table`
  suffit plutôt qu'un modèle dédié).

## Endpoints

CRUD standard sur les quatre ressources (`GET`, `POST`, `PUT`, `DELETE`
sur `/guildes`, `/aventuriers`, `/quetes`, `/monstres`), plus les
endpoints métier suivants :

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/quetes/<id>/aventuriers/<id>` | Assigne un aventurier à une quête |
| DELETE | `/quetes/<id>/aventuriers/<id>` | Retire un aventurier d'une quête |
| POST | `/quetes/<id>/cloturer` | Clôture la quête et distribue la réputation |
| GET | `/aventuriers?with_guilde=1` | Liste les aventuriers avec leur guilde, sans N+1 |

### Règle métier de clôture

Quand une quête est clôturée (`POST /quetes/<id>/cloturer`), chaque
guilde ayant au moins un aventurier participant reçoit un bonus de
réputation égal à la récompense de la quête (montant fixe, pas une part
proportionnelle au nombre de participants). Une quête déjà terminée ne
peut pas être clôturée à nouveau, pour ne pas distribuer la récompense
en double. Une quête sans participant ne peut pas être clôturée.

## Documentation interactive (Scalar)

La spécification OpenAPI 3.0 complète de l'API est servie brute sur
`GET /openapi.json`, et une documentation interactive construite avec
[Scalar](https://scalar.com) est disponible sur `GET /docs` une fois le
serveur lancé (`http://localhost:5000/docs`).

L'intégration ne demande aucune dépendance Python supplémentaire :
`docs.py` expose la spec statique, et la page `/docs` charge le
composant Scalar directement depuis un CDN dans le navigateur :

```html
<script id="api-reference" data-url="/openapi.json"></script>
<script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
```

La spec (`guilde_api/openapi.json`) couvre les dix routes de l'API, les
schémas de requête et de réponse pour chaque ressource, ainsi que les
cas d'erreur (400/404). Elle a été validée avec
`openapi-spec-validator` avant livraison. Si un endpoint est ajouté ou
modifié, il faut mettre à jour ce fichier à la main : il n'y a pas de
génération automatique depuis le code des routes dans cette version.

## Exemples curl

```bash
# Créer une guilde
curl -X POST http://localhost:5000/guildes \
  -H "Content-Type: application/json" \
  -d '{"nom": "Les Aigles d'\''Acier"}'

# Créer un aventurier dans cette guilde (guilde_id=1)
curl -X POST http://localhost:5000/aventuriers \
  -H "Content-Type: application/json" \
  -d '{"nom": "Rakan", "classe": "Guerrier", "guilde_id": 1}'

# Créer une quête
curl -X POST http://localhost:5000/quetes \
  -H "Content-Type: application/json" \
  -d '{"titre": "Nettoyer la mine", "recompense": 100}'

# Assigner l'aventurier 1 a la quete 1
curl -X POST http://localhost:5000/quetes/1/aventuriers/1

# Cloturer la quete et distribuer la recompense
curl -X POST http://localhost:5000/quetes/1/cloturer

# Lister les aventuriers avec leur guilde (chargement optimise)
curl "http://localhost:5000/aventuriers?with_guilde=1"

# Cas d'erreur : ressource inexistante
curl -i http://localhost:5000/quetes/9999
```

## Bonus résolu : le problème du N+1

L'endpoint `GET /aventuriers?with_guilde=1` illustre la résolution du
défi bonus de l'énoncé. Sans précaution, accéder à `aventurier.guilde`
pour chaque élément d'une liste déclenche une requête SQL par aventurier
dont la guilde n'a pas déjà été chargée dans la session (chargement
paresseux, comportement par défaut de SQLAlchemy). Mesuré directement
sur ce projet : pour 10 aventuriers répartis dans 10 guildes distinctes,
la version naïve génère 11 requêtes SQL (1 pour la liste + 1 par
aventurier), contre 2 requêtes avec un chargement `selectinload`.

Le correctif, visible dans `guilde_api/routes/aventuriers.py` :

```python
from sqlalchemy.orm import selectinload

query = Aventurier.query
if with_guilde:
    query = query.options(selectinload(Aventurier.guilde))
```

`selectinload` charge en une seule requête additionnelle toutes les
guildes nécessaires à la liste d'aventuriers déjà récupérée, plutôt que
d'aller chercher chaque guilde une par une. `joinedload` aurait aussi été
une option valable (une seule requête avec `JOIN` au lieu de deux) ; le
choix entre les deux dépend surtout de la volumétrie et du nombre de
colonnes ramenées par la jointure.

Note : dans une relation many-to-one comme celle-ci, SQLAlchemy évite
déjà de requêter en base une guilde qui a été chargée plus tôt dans la
même session. Le problème est donc surtout visible quand les objets
liés sont nombreux et distincts (ce qui est le cas courant en
production, où chaque requête HTTP démarre avec une session neuve).

## Hors scope (volontaire)

Aucune authentification, aucune autorisation. Cet exercice porte sur
Flask, SQLAlchemy et la construction d'une API REST ; la sécurité des
accès (JWT, OAuth2, gestion des rôles) fait l'objet d'une session à
part. Ne pas déployer ce projet tel quel sur une machine accessible
publiquement.

Autres limites connues, assumées pour un exercice de cette portée : pas
de migrations de schéma (Alembic serait la suite logique dès qu'on
modifie un modèle en production), pas de pagination sur les listes, pas
de validation de schéma poussée (les erreurs 400 couvrent les champs
requis et les références invalides, pas plus).
