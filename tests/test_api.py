# Tests d'integration : on passe par le client de test Flask plutot que
# par des appels directs aux fonctions des blueprints, pour verifier le
# comportement reel de l'API (codes HTTP, format JSON) et pas seulement
# la logique interne.


def creer_guilde(client, nom="Guilde Test", reputation=0):
    resp = client.post("/guildes", json={"nom": nom, "reputation": reputation})
    assert resp.status_code == 201
    return resp.get_json()


def creer_aventurier(client, guilde_id, nom="Aventurier Test", classe="Guerrier"):
    resp = client.post(
        "/aventuriers",
        json={"nom": nom, "classe": classe, "guilde_id": guilde_id},
    )
    assert resp.status_code == 201
    return resp.get_json()


def creer_quete(client, titre="Quete Test", recompense=100):
    resp = client.post("/quetes", json={"titre": titre, "recompense": recompense})
    assert resp.status_code == 201
    return resp.get_json()


def test_creation_guilde_et_aventurier(client):
    guilde = creer_guilde(client, nom="Les Aigles")
    aventurier = creer_aventurier(client, guilde["id"], nom="Rakan")

    assert aventurier["guilde_id"] == guilde["id"]

    resp = client.get("/aventuriers/{}".format(aventurier["id"]))
    assert resp.status_code == 200
    assert resp.get_json()["guilde"]["nom"] == "Les Aigles"


def test_creation_guilde_sans_nom_est_refusee(client):
    resp = client.post("/guildes", json={"reputation": 0})
    assert resp.status_code == 400


def test_aventurier_avec_guilde_id_invalide_est_refuse(client):
    resp = client.post(
        "/aventuriers",
        json={"nom": "Sans Guilde", "classe": "Mage", "guilde_id": 999},
    )
    assert resp.status_code == 400


def test_relation_n_n_entre_aventuriers_et_quetes(client):
    guilde = creer_guilde(client, nom="Guilde N-N")
    aventurier_1 = creer_aventurier(client, guilde["id"], nom="Aventurier 1")
    aventurier_2 = creer_aventurier(client, guilde["id"], nom="Aventurier 2")
    quete = creer_quete(client, titre="Quete Partagee")

    resp_1 = client.post("/quetes/{}/aventuriers/{}".format(quete["id"], aventurier_1["id"]))
    resp_2 = client.post("/quetes/{}/aventuriers/{}".format(quete["id"], aventurier_2["id"]))
    assert resp_1.status_code == 201
    assert resp_2.status_code == 201

    # Assigner deux fois le meme aventurier a la meme quete doit etre refuse.
    resp_double = client.post("/quetes/{}/aventuriers/{}".format(quete["id"], aventurier_1["id"]))
    assert resp_double.status_code == 400

    detail = client.get("/quetes/{}".format(quete["id"])).get_json()
    assert len(detail["aventuriers"]) == 2


def test_cloture_de_quete_distribue_la_reputation(client):
    guilde_a = creer_guilde(client, nom="Guilde A", reputation=0)
    guilde_b = creer_guilde(client, nom="Guilde B", reputation=0)
    aventurier_a = creer_aventurier(client, guilde_a["id"], nom="Membre A")
    aventurier_b = creer_aventurier(client, guilde_b["id"], nom="Membre B")
    quete = creer_quete(client, titre="Quete Recompensee", recompense=150)

    client.post("/quetes/{}/aventuriers/{}".format(quete["id"], aventurier_a["id"]))
    client.post("/quetes/{}/aventuriers/{}".format(quete["id"], aventurier_b["id"]))

    resp = client.post("/quetes/{}/cloturer".format(quete["id"]))
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["quete"]["terminee"] is True

    reputations = {g["nom"]: g["reputation"] for g in data["guildes_recompensees"]}
    assert reputations["Guilde A"] == 150
    assert reputations["Guilde B"] == 150

    # Une quete deja terminee ne peut pas etre cloturee une seconde fois.
    resp_double = client.post("/quetes/{}/cloturer".format(quete["id"]))
    assert resp_double.status_code == 400


def test_cloture_sans_participant_est_refusee(client):
    quete = creer_quete(client, titre="Quete Vide", recompense=50)
    resp = client.post("/quetes/{}/cloturer".format(quete["id"]))
    assert resp.status_code == 400


def test_ressource_inexistante_renvoie_404(client):
    resp = client.get("/quetes/9999")
    assert resp.status_code == 404
    resp = client.get("/aventuriers/9999")
    assert resp.status_code == 404
    resp = client.get("/guildes/9999")
    assert resp.status_code == 404


def test_suppression_guilde_supprime_ses_aventuriers(client):
    guilde = creer_guilde(client, nom="Guilde Ephemere")
    aventurier = creer_aventurier(client, guilde["id"], nom="Aventurier Ephemere")

    resp = client.delete("/guildes/{}".format(guilde["id"]))
    assert resp.status_code == 204

    resp = client.get("/aventuriers/{}".format(aventurier["id"]))
    assert resp.status_code == 404


def test_listing_aventuriers_avec_guilde(client):
    guilde = creer_guilde(client, nom="Guilde Listing")
    creer_aventurier(client, guilde["id"], nom="Aventurier Listing")

    resp = client.get("/aventuriers?with_guilde=1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["guilde"]["nom"] == "Guilde Listing"
