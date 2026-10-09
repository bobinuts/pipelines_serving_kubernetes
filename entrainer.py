"""entrainer.py : decoupage par patient, pipeline scikit-learn, evaluation, choix du seuil, serialisation.
Mesures 6 a 10 (questions 2.1 a 2.9). Sortie aussi ecrite dans sorties/entrainer.txt (ASCII uniquement).

Usage :  python entrainer.py                 entrainement complet + paquet model/modele.joblib
         python entrainer.py --stabilite     effet de la graine du decoupage (aucun fichier de modele)
         python entrainer.py --echantillon N essai rapide sur N lignes (developpement, ne pas rendre)
"""
import argparse
import datetime
import json
import os
import platform
import time
import warnings

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---- decisions figees (voir MESURES.md et EXPLORATION.md) -----------------------------
RAPPEL_VISE = 0.95            # decide le 09/10/2026 a 11:31, avant toute mesure
VERSION_MODELE = "1.0.0"
SEED = 42
TEST_SIZE = 0.2               # part des PATIENTS (et non des lignes) mise de cote
CIBLE, GROUPE = "target", "patient_id"
FUITES = ["iddx_full", "iddx_1", "iddx_2", "iddx_3", "iddx_4", "iddx_5",
          "mel_thick_mm", "mel_mitotic_index", "lesion_id"]
IDENTIFIANTS = ["isic_id", "patient_id"]
CONSTANTES = ["image_type"]
ORIGINE = ["attribution", "copyright_license"]      # ecartees : identifient l'hopital
CATEGORIELLES = ["sex", "anatom_site_general", "tbp_tile_type",
                 "tbp_lv_location", "tbp_lv_location_simple"]
SEUILS_TABLEAU = [0.50, 0.80, 0.90, 0.99]

os.makedirs("sorties", exist_ok=True)
os.makedirs("model", exist_ok=True)
_f = open("sorties/entrainer.txt", "w", encoding="utf-8")


def p(*args):
    ligne = " ".join(str(a) for a in args)
    print(ligne, flush=True)
    _f.write(ligne + "\n")
    _f.flush()


def charger(echantillon=None):
    d = pd.read_csv("data/train-metadata.csv", low_memory=False)
    if echantillon:
        d = d.sample(n=echantillon, random_state=0).reset_index(drop=True)
    exclues = set(FUITES) | set(IDENTIFIANTS) | set(CONSTANTES) | set(ORIGINE) | {CIBLE}
    cat = list(CATEGORIELLES)
    num = [c for c in d.columns if c not in exclues and c not in cat]
    return d, num, cat


def construire_pipeline(num, cat):
    pre = ColumnTransformer([
        ("num", Pipeline([("imputation", SimpleImputer(strategy="median")),
                          ("echelle", StandardScaler())]), num),
        ("cat", Pipeline([("imputation", SimpleImputer(strategy="most_frequent")),
                          ("encodage", OneHotEncoder(handle_unknown="ignore"))]), cat),
    ])
    return Pipeline([("pre", pre),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])


def decouper(X, y, groupes, seed):
    decoupe = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
    train, test = next(decoupe.split(X, y, groups=groupes))
    assert not (set(groupes[train]) & set(groupes[test])), "fuite de patients"
    return train, test


def ajuster(modele, X, y):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        debut = time.perf_counter()
        modele.fit(X, y)
        duree = time.perf_counter() - debut
    return duree, sorted({f"{x.category.__name__}: {str(x.message)[:90]}" for x in w})


def stabilite(d, num, cat):
    X, y, groupes = d[num + cat], d[CIBLE].to_numpy(), d[GROUPE].to_numpy()
    p("=== STABILITE : EFFET DE LA GRAINE DU DECOUPAGE (question 2.1) ===")
    p(f"{'graine':>6} {'patients test':>14} {'positifs test':>14} {'taux test %':>12} {'PR-AUC':>8} {'ROC-AUC':>8}")
    for seed in [0, 1, 2, 3, 4, 42]:
        train, test = decouper(X, y, groupes, seed)
        m = construire_pipeline(num, cat)
        ajuster(m, X.iloc[train], y[train])
        proba = m.predict_proba(X.iloc[test])[:, 1]
        p(f"{seed:>6} {len(set(groupes[test])):>14} {int(y[test].sum()):>14} "
          f"{100 * y[test].mean():>12.3f} {average_precision_score(y[test], proba):>8.4f} "
          f"{roc_auc_score(y[test], proba):>8.4f}")
    p("=== FIN ===")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stabilite", action="store_true")
    ap.add_argument("--echantillon", type=int, default=None)
    a = ap.parse_args()

    d, num, cat = charger(a.echantillon)
    if a.stabilite:
        stabilite(d, num, cat)
        return

    colonnes = num + cat
    X, y, groupes = d[colonnes], d[CIBLE].to_numpy(), d[GROUPE].to_numpy()
    p("=== CONFIGURATION ===")
    p("date :", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    p("lignes :", len(d), "| variables :", len(colonnes), f"({len(num)} numeriques, {len(cat)} categorielles)")
    p("graine :", SEED, "| part de patients en test :", TEST_SIZE, "| rappel vise :", RAPPEL_VISE)

    # ------------------------------------------------------------------ MESURE 6
    train, test = decouper(X, y, groupes, SEED)
    y_train, y_test = y[train], y[test]
    p("")
    p("=== MESURE 6 : DECOUPAGE PAR PATIENT ===")
    p("intersection des patients (doit etre vide) :", len(set(groupes[train]) & set(groupes[test])))
    p(f"{'':<22}{'Entrainement':>14}{'Test':>12}")
    p(f"{'lignes':<22}{len(train):>14}{len(test):>12}")
    p(f"{'patients':<22}{len(set(groupes[train])):>14}{len(set(groupes[test])):>12}")
    p(f"{'positifs':<22}{int(y_train.sum()):>14}{int(y_test.sum()):>12}")
    p(f"{'taux de positifs %':<22}{100 * y_train.mean():>14.4f}{100 * y_test.mean():>12.4f}")
    p("patients avec au moins une maligne :",
      len(set(groupes[train][y_train == 1])), "(train),", len(set(groupes[test][y_test == 1])), "(test)")

    # ------------------------------------------------------------------ MESURE 7
    reference = DummyClassifier(strategy="most_frequent").fit(X.iloc[train], y_train)
    modele = construire_pipeline(num, cat)
    duree_fit, avertissements = ajuster(modele, X.iloc[train], y_train)
    proba = modele.predict_proba(X.iloc[test])[:, 1]
    proba_ref = reference.predict_proba(X.iloc[test])[:, 1]
    p("")
    p("=== MESURE 7 : COMPARAISON SUR L'ENSEMBLE DE TEST ===")
    p(f"{'Modele':<24}{'Exactitude':>12}{'ROC-AUC':>10}{'PR-AUC':>10}")
    p(f"{'DummyClassifier':<24}{accuracy_score(y_test, reference.predict(X.iloc[test])):>12.5f}"
      f"{roc_auc_score(y_test, proba_ref):>10.4f}{average_precision_score(y_test, proba_ref):>10.5f}")
    p(f"{'Regression logistique':<24}{accuracy_score(y_test, modele.predict(X.iloc[test])):>12.5f}"
      f"{roc_auc_score(y_test, proba):>10.4f}{average_precision_score(y_test, proba):>10.5f}")
    p(f"{'Hasard (taux de positifs)':<24}{'-':>12}{'-':>10}{y_test.mean():>10.5f}")
    p("duree de l'entrainement (s) :", round(duree_fit, 1))
    p("avertissements a l'entrainement :", avertissements if avertissements else "aucun")

    # ------------------------------------------------------------------ MESURE 8
    p("")
    p("=== MESURE 8 : COMPROMIS RAPPEL / PRECISION (ensemble de test) ===")
    p(f"{'Seuil':>6}{'Rappel':>9}{'Precision':>11}{'VP':>7}{'FP':>9}{'FN':>6}{'Alertes/1000':>14}")
    for s in SEUILS_TABLEAU:
        pred = proba >= s
        vp = int((pred & (y_test == 1)).sum())
        fp = int((pred & (y_test == 0)).sum())
        fn = int((~pred & (y_test == 1)).sum())
        rap = vp / (vp + fn) if (vp + fn) else float("nan")
        pre_s = vp / (vp + fp) if (vp + fp) else float("nan")
        p(f"{s:>6.2f}{rap:>9.4f}{pre_s:>11.5f}{vp:>7}{fp:>9}{fn:>6}{1000 * (vp + fp) / len(y_test):>14.1f}")

    # ------------------------------------------------------------------ MESURE 9
    precision, rappel, seuils = precision_recall_curve(y_test, proba)
    # rappel decroit quand le seuil monte : le DERNIER indice qui tient le rappel vise
    # est le seuil le plus eleve, donc celui qui declenche le moins d'alertes.
    i = np.where(rappel >= RAPPEL_VISE)[0][-1]
    seuil = float(seuils[min(i, len(seuils) - 1)])
    pred = proba >= seuil
    vp = int((pred & (y_test == 1)).sum())
    fp = int((pred & (y_test == 0)).sum())
    fn = int((~pred & (y_test == 1)).sum())
    precision_s = vp / (vp + fp)
    rappel_s = vp / (vp + fn)
    p("")
    p("=== MESURE 9 : SEUIL RETENU ET SON COUT ===")
    p("rappel vise :", RAPPEL_VISE)
    p("seuil correspondant :", round(seuil, 6))
    p("rappel obtenu sur le test :", round(rappel_s, 4))
    p("precision a ce seuil :", round(precision_s, 6))
    p("lesions examinees par maligne trouvee :", round(1 / precision_s))
    p("vrais positifs / faux positifs / faux negatifs :", vp, fp, fn)
    p("alertes pour 1000 lesions :", round(1000 * (vp + fp) / len(y_test), 1))

    # ------------------------------------------------------------------ MESURE 10
    metriques = {
        "pr_auc_test": float(average_precision_score(y_test, proba)),
        "roc_auc_test": float(roc_auc_score(y_test, proba)),
        "hasard_pr_auc": float(y_test.mean()),
        "rappel_test_au_seuil": float(rappel_s),
        "precision_test_au_seuil": float(precision_s),
        "lesions_examinees_par_maligne": int(round(1 / precision_s)),
        "faux_negatifs_test": fn,
        "positifs_test": int(y_test.sum()),
        "lignes_test": int(len(test)),
        "patients_test": int(len(set(groupes[test]))),
    }
    paquet = {
        "pipeline": modele,
        "version": VERSION_MODELE,
        "colonnes_attendues": colonnes,
        "colonnes_numeriques": num,
        "colonnes_categorielles": cat,
        "seuil": seuil,
        "rappel_cible": RAPPEL_VISE,
        "metriques": metriques,
        "prevalence_entrainement": float(y_train.mean()),
        "entraine_le": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
    }
    joblib.dump(paquet, "model/modele.joblib")
    taille = os.path.getsize("model/modele.joblib")
    p("")
    p("=== MESURE 10 : PAQUET PRODUIT ===")
    p("taille du fichier (Ko) :", round(taille / 1024, 1), f"({taille} octets)")
    p("nombre de colonnes attendues declarees :", len(colonnes))
    p("duree de l'entrainement (s) :", round(duree_fit, 1))
    p("versions ayant entraine le modele :", json.dumps(paquet["versions"]))
    p("prevalence d'entrainement :", round(paquet["prevalence_entrainement"], 6))

    # ---- charges d'essai pour l'API : lignes reelles du jeu de test, sans valeur manquante
    test_X = X.iloc[test].reset_index(drop=True)
    complet = test_X.notna().all(axis=1).to_numpy()
    cibles = {"charge.json": complet & (y_test == 0), "charge_maligne.json": complet & (y_test == 1)}
    for nom, masque in cibles.items():
        if masque.any():
            ligne = test_X.loc[[int(np.argmax(masque))]]
            with open(nom, "w", encoding="utf-8") as g:
                json.dump(json.loads(ligne.to_json(orient="records"))[0], g, indent=1)
            p("ecrit :", nom)
    with open("sorties/metriques.json", "w", encoding="utf-8") as g:
        json.dump({"seuil": seuil, **metriques}, g, indent=1)
    p("")
    p("=== FIN ===")


main()
_f.close()
