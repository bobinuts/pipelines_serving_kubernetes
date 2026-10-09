"""app.py : API d'inference DermaScan.
Contrat : PORT (defaut 8000), MODEL_PATH (defaut model/modele.joblib), SEUIL (optionnel).
Endpoints : GET /health, GET /model/info, POST /predict.
Les charges utiles (donnees de sante) ne sont jamais journalisees."""
import os

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

# Chargement au demarrage, PAS dans la fonction de vue.
# Un modele absent ou illisible n'empeche pas le processus de demarrer : /health repond 503.
PAQUET = None
PIPELINE = None
SEUIL = None
ERREUR = None
try:
    PAQUET = joblib.load(os.environ.get("MODEL_PATH", "model/modele.joblib"))
    PIPELINE = PAQUET["pipeline"]
    SEUIL = float(os.environ.get("SEUIL", PAQUET["seuil"]))
except Exception as exc:
    PAQUET = None
    PIPELINE = None
    ERREUR = f"{type(exc).__name__}: {exc}"

COLONNES = PAQUET["colonnes_attendues"] if PAQUET else []
NUMERIQUES = set(PAQUET["colonnes_numeriques"]) if PAQUET else set()


def indisponible():
    return jsonify({"status": "indisponible", "model_loaded": False, "erreur": ERREUR}), 503


@app.get("/health")
def health():
    if PIPELINE is None:
        return indisponible()
    return jsonify({"status": "ok", "model_loaded": True, "version_modele": PAQUET["version"]}), 200


@app.get("/model/info")
def model_info():
    if PAQUET is None:
        return indisponible()
    return jsonify({
        "version_modele": PAQUET["version"],
        "seuil": SEUIL,
        "rappel_cible": PAQUET["rappel_cible"],
        "metriques": PAQUET["metriques"],
        "prevalence_entrainement": PAQUET["prevalence_entrainement"],
        "entraine_le": PAQUET["entraine_le"],
        "versions_bibliotheques": PAQUET["versions"],
        "nombre_colonnes_attendues": len(COLONNES),
        "colonnes_attendues": COLONNES,
    })


@app.post("/predict")
def predict():
    if PIPELINE is None:
        return indisponible()
    charge = request.get_json(silent=True)
    if not isinstance(charge, dict) or not charge:
        return jsonify({"error": "corps JSON absent, vide ou invalide : un objet {colonne: valeur} est attendu"}), 400

    # Validation AVANT prediction : une charge incomplete donne un 400, jamais un 500.
    manquantes = [c for c in COLONNES if c not in charge]
    if manquantes:
        return jsonify({"error": "colonnes manquantes", "nombre_manquantes": len(manquantes),
                        "manquantes": manquantes[:10]}), 400

    ligne = {c: (np.nan if charge[c] is None else charge[c]) for c in COLONNES}
    X = pd.DataFrame([ligne], columns=COLONNES)
    invalides = []
    for c in NUMERIQUES:
        convertie = pd.to_numeric(X[c], errors="coerce")
        if X[c].notna().iloc[0] and convertie.isna().iloc[0]:
            invalides.append(c)
        X[c] = convertie
    if invalides:
        return jsonify({"error": "valeurs non numeriques", "invalides": invalides[:10]}), 400

    proba = float(PIPELINE.predict_proba(X)[0, 1])
    return jsonify({
        "probabilite_maligne": round(proba, 6),
        "seuil": SEUIL,
        "decision": "a_examiner" if proba >= SEUIL else "non_signale",
        "version_modele": PAQUET["version"],
        "rappel_cible": PAQUET["rappel_cible"],
    })


if __name__ == "__main__":
    # Serveur de developpement, pour les tests locaux uniquement : le conteneur utilise gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
