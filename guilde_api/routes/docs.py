import json
import os

from flask import Blueprint, Response

docs_bp = Blueprint("docs", __name__)

_SPEC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.json")

_SCALAR_PAGE = """<!doctype html>
<html>
  <head>
    <title>Guilde des Aventuriers - Documentation API</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""


@docs_bp.get("/openapi.json")
def openapi_spec():
    # On lit le fichier a chaque requete plutot que de le charger une
    # fois au demarrage : ca reste triviallement rapide pour un fichier
    # de cette taille, et ca evite d'avoir a redemarrer le serveur si on
    # retouche la spec pendant le developpement.
    with open(_SPEC_PATH, encoding="utf-8") as spec_file:
        content = spec_file.read()
    # On valide que le fichier est du JSON exploitable avant de le
    # renvoyer, pour ne pas exposer une reponse cassee sans s'en rendre
    # compte si le fichier a ete modifie a la main.
    json.loads(content)
    return Response(content, mimetype="application/json")


@docs_bp.get("/docs")
def api_docs():
    return Response(_SCALAR_PAGE, mimetype="text/html")
