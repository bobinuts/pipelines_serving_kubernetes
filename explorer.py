"""explorer.py : exploration de data/train-metadata.csv (mesures 2 a 5, questions 1.1 a 1.5).
Aucun modele. La sortie est aussi ecrite dans sorties/explorer.txt (ASCII uniquement)."""
import os
import pandas as pd

os.makedirs("sorties", exist_ok=True)
_f = open("sorties/explorer.txt", "w", encoding="utf-8")


def p(*args):
    ligne = " ".join(str(a) for a in args)
    print(ligne)
    _f.write(ligne + "\n")


d = pd.read_csv("data/train-metadata.csv", low_memory=False)

# ---------------------------------------------------------------- MESURE 2
p("=== MESURE 2 : VOLUMETRIE ET STRUCTURE ===")
p("lignes, colonnes :", d.shape)
p("patients distincts :", d["patient_id"].nunique())
tailles = d.groupby("patient_id").size()
p("lesions par patient (min / mediane / max) :", tailles.min(), int(tailles.median()), tailles.max())
p("")
p("--- type de chaque colonne ---")
for c, t in d.dtypes.items():
    p(f"{c:<32} {t}")

# ---------------------------------------------------------------- MESURE 3
LEAKS = ["iddx_full", "iddx_1", "iddx_2", "iddx_3", "iddx_4", "iddx_5",
         "mel_thick_mm", "mel_mitotic_index", "lesion_id"]
p("")
p("=== MESURE 3 : COLONNES SUSPECTES (renseignees / dont malignes) ===")
p(f"total de lesions malignes : {int(d['target'].sum())}")
for c in LEAKS:
    rempli = d[c].notna().sum()
    malignes = d.loc[d[c].notna(), "target"].sum()
    p(f"{c:<22} rempli {rempli:>7} dont malignes {int(malignes):>4}")

# A examiner (non classees d'office comme fuites) : meme comptage
A_EXAMINER = ["tbp_lv_dnn_lesion_confidence", "attribution", "copyright_license"]
p("--- a examiner, pas encore tranchees ---")
for c in A_EXAMINER:
    rempli = d[c].notna().sum()
    malignes = d.loc[d[c].notna(), "target"].sum()
    p(f"{c:<32} rempli {rempli:>7} dont malignes {int(malignes):>4} modalites {d[c].nunique()}")

# ---------------------------------------------------------------- MESURE 4
IDENTIFIANTS = ["isic_id", "patient_id"]
p("")
p("=== MESURE 4 : VALEURS MANQUANTES ET CONSTANTES ===")
hors_fuite = [c for c in d.columns if c not in LEAKS]
na = d[hors_fuite].isna().sum()
na = na[na > 0].sort_values(ascending=False)
p("colonnes hors fuites avec au moins une valeur manquante :", len(na))
for c, n in na.items():
    p(f"{c:<32} {int(n):>8}  {100 * n / len(d):7.3f} %")
constantes = [c for c in d.columns if d[c].nunique(dropna=True) <= 1]
p("colonnes constantes :", constantes)
retirees = set(LEAKS) | set(IDENTIFIANTS) | set(constantes) | {"target"}
restantes = [c for c in d.columns if c not in retirees]
p("variables restantes apres retrait des fuites, identifiants et constantes (cible exclue) :", len(restantes))
p("liste :", restantes)

# ---------------------------------------------------------------- MESURE 5
p("")
p("=== MESURE 5 : DESEQUILIBRE DE LA CIBLE ===")
n1 = int(d["target"].sum())
n0 = int((d["target"] == 0).sum())
p("target = 1 :", n1)
p("target = 0 :", n0)
p("taux de positifs (%) :", round(100 * n1 / len(d), 4))
p("une maligne pour N benignes : N =", round(n0 / n1, 1))
p("exactitude du classifieur 'tout benin' :", round(n0 / len(d), 6))
p("")
p("=== FIN ===")
_f.close()
