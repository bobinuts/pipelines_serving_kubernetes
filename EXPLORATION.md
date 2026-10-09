# EXPLORATION — Séance 2 (mesures 1 à 5, questions 0.1 à 1.5)

**Auteur : PELLICANO Théo** · M2 Industrialisation de l'IA dans le Cloud, YNOV Campus Montpellier · Séance 2, 09/10/2026

Source des chiffres : `sorties/01_setup.txt`, `sorties/02_kaggle.txt`, `sorties/explorer.txt` (script `explorer.py`), relevés du 09/10/2026 entre 11:24 et 11:32. Deux comptages complémentaires (croisement `iddx_1` × `target`, patients portant au moins une maligne, répartition par `attribution`) viennent d'une vérification ponctuelle sur le même fichier ; ils sont signalés comme tels.

## Question 0.1 — Pourquoi décider le rappel visé avant la première mesure

Le rappel visé est la barre que je m'engage à atteindre, et il doit exprimer le coût d'une maligne manquée, pas ce que le modèle sait faire. Si je le choisissais après avoir vu la courbe, je le fixerais là où le compromis me paraît flatteur : l'objectif serait ajusté aux résultats au lieu de les juger. Il perdrait son rôle d'engagement. Le seuil serait de plus calé sur l'ensemble de test, ce qui rend la performance annoncée optimiste. Décision prise le 09/10/2026 à 11:31 : rappel visé de 0,95, consigné dans `MESURES.md` avant toute statistique sur la cible.

## Partie 1 — Exploration et préparation des données

### Mesure 1 — versions et volumétrie du fichier

| Relevé | Votre valeur |
|---|---|
| Version de Python | 3.14.0 (environnement virtuel) |
| Version de scikit-learn | 1.9.1 |
| Version de pandas | 3.0.6 |
| Poids du fichier d'annotation | 257 543 161 octets, soit 245,6 Mio (≈ 246 Mo, comme annoncé par l'énoncé). Archive téléchargée : 89,2 Mo, en 7,2 s |

Versions utiles pour l'épinglage de la mesure 15 : numpy 2.5.3, scipy 1.18.1, joblib 1.6.0, flask 3.1.3, gunicorn 26.2.0. Liste complète du venv : `sorties/pip_freeze_venv.txt` (50 paquets).

### Mesure 2 — volumétrie et structure

| Relevé | Votre valeur |
|---|---|
| Nombre de lignes | 401 059 |
| Nombre de colonnes | 55 |
| Nombre de patients distincts | 1 042 |
| Lésions par patient : minimum / médiane / maximum | 1 / 241 / 9 184 |

Types : 37 colonnes numériques (35 en `float64`, 2 en `int64` : `target` et `tbp_lv_symm_2axis_angle`) et 18 colonnes texte. Le détail colonne par colonne figure dans `sorties/explorer.txt`.

**Question 1.1.** On compte 401 059 lignes pour 1 042 patients, soit environ 385 lésions par patient en moyenne (médiane 241, jusqu'à 9 184 pour un seul patient). Une ligne n'est donc pas une observation indépendante : les lésions d'un même patient partagent la peau, l'âge, le sexe, la séance de photographie et la cabine, et se ressemblent plus entre elles qu'avec celles d'un autre patient. La grandeur qui détermine la taille réelle de l'échantillon est le **nombre de patients** (1 042), et plus finement les 259 patients qui portent au moins une lésion maligne (vérification ponctuelle : les 393 malignes se répartissent entre ces 259 patients, 1 maligne en médiane par patient, 14 au maximum). Le découpage de la partie 2.1 doit donc se faire par patient, sans quoi les lésions d'un même patient se retrouveraient des deux côtés.

### Mesure 3 — colonnes à écarter pour cause de fuite

Total de lésions malignes dans le jeu : 393.

| Colonne | Valeurs renseignées | Dont malignes | Écartée ? |
|---|---|---|---|
| `iddx_1` | 401 059 | 393 | Oui |
| `iddx_full` | 401 059 | 393 | Oui |
| `mel_thick_mm` | 63 | 63 | Oui |
| `mel_mitotic_index` | 53 | 53 | Oui |
| `lesion_id` | 22 058 | 393 | Oui |
| `iddx_2` | 1 068 | 393 | Oui |
| `iddx_3` | 1 065 | 393 | Oui |
| `iddx_4` | 551 | 242 | Oui |
| `iddx_5` | 1 | 0 | Oui (et constante) |

Les neuf colonnes écartées sont celles de la liste de l'annexe C. Lecture des chiffres :
- `iddx_1` et `iddx_full` sont renseignées partout, mais `iddx_1` **est** la cible : le croisement avec `target` (vérification ponctuelle) donne `Malignant` = 393 lignes, toutes à `target = 1`, `Benign` = 400 552 et `Indeterminate` = 114, toutes à `target = 0`.
- `mel_thick_mm` et `mel_mitotic_index` : toutes les lignes renseignées sont malignes (63 sur 63, 53 sur 53). Être renseigné suffit à désigner une maligne.
- `iddx_2` à `iddx_4` ne sont renseignées que pour environ 1 000 lignes, qui contiennent toutes les 393 malignes (36,8 % de malignes parmi les renseignées contre 0,098 % sur l'ensemble).
- `lesion_id` : voir Q1.2.

Pour mémoire, trois autres colonnes sont renseignées partout et n'ont pas été classées comme fuites : `tbp_lv_dnn_lesion_confidence`, `attribution` et `copyright_license`. Leur sort est traité dans la section « Décision complémentaire » plus bas.

**Question 1.2.** `lesion_id` est renseigné pour 22 058 lésions seulement (5,5 %), mais pour les 393 malignes sans exception : parmi les lésions qui en ont un, 1,78 % sont malignes (environ 18 fois la prévalence), et parmi les 379 001 qui n'en ont pas, aucune ne l'est. Sa seule présence révèle donc que la lésion a déjà été distinguée du reste. Cet identifiant n'est pas attribué à la prise de vue : d'après la description du jeu (à vérifier sur la page Data de la compétition), il est donné aux lésions qu'un clinicien a repérées comme préoccupantes, donc en aval de la décision qu'on demande au modèle de prendre. En production, une lésion qui arrive de la cabine n'a pas encore cet identifiant.

**Question 1.3.** `iddx_1` donne 100 % de bonnes réponses parce que c'est le diagnostic lui-même (`Malignant` coïncide exactement avec `target = 1`) : le modèle apprend à recopier la réponse, pas à reconnaître une lésion maligne. Le jour où une nouvelle lésion arrive, ce diagnostic n'existe pas encore, puisque c'est précisément ce qu'on cherche, et le modèle n'a plus rien à lire : sa performance réelle s'effondre alors que sa validation affichait un score parfait.

### Mesure 4 — valeurs manquantes et colonnes constantes

| Relevé | Votre valeur |
|---|---|
| Colonnes avec au moins une valeur manquante, hors fuites | 3 : `sex`, `anatom_site_general`, `age_approx` |
| Taux de valeurs manquantes | `sex` : 11 517 (2,872 %) ; `anatom_site_general` : 5 756 (1,435 %) ; `age_approx` : 2 798 (0,698 %) |
| Colonnes constantes | `image_type` (unique modalité : `TBP tile: close-up`). `iddx_5` l'est aussi, mais elle est déjà écartée comme fuite |
| Variables restantes après retrait des fuites, identifiants et constantes | **42** = 55 − 9 fuites − 2 identifiants (`isic_id`, `patient_id`) − 1 constante (`image_type`) − 1 cible. Dont 7 catégorielles (`sex`, `anatom_site_general`, `tbp_tile_type`, `tbp_lv_location`, `tbp_lv_location_simple`, `attribution`, `copyright_license`) et 35 numériques |

**Question 1.4.** Raison de la retirer explicitement : une constante n'apporte aucune information, mais elle alourdit le pipeline, figurerait dans `colonnes_attendues` et obligerait l'API à exiger un champ qui ne sert à rien. Raison de consigner son existence : elle décrit le domaine dans lequel le modèle a été entraîné. Ici, toutes les images sont des vignettes `TBP tile: close-up`. Si une cabine remontait un autre type d'image, on sortirait du domaine d'entraînement, et c'est une information à mettre dans la model card et à surveiller en séance 5.

### Mesure 5 — déséquilibre de la cible

| Relevé | Votre valeur |
|---|---|
| Nombre de lésions `target = 1` | 393 |
| Nombre de lésions `target = 0` | 400 666 |
| Taux de positifs, en pourcentage | 0,098 % |
| Rapport « une maligne pour N bénignes » | 1 pour 1 020 (N = 1 019,5) |

**Question 1.5.** Un classifieur qui répond « bénin » à toutes les lésions atteint 400 666 / 401 059 = **99,902 %** d'exactitude. Ce chiffre ne dit rien du service : le classifieur ne trouve aucun cancer, donc ne sert à rien, et il paraît pourtant excellent. L'exactitude est dominée par la classe majoritaire : sur un jeu où une lésion sur mille est maligne, elle ne peut pas servir de critère de choix. Il faut des mesures centrées sur la classe rare (rappel, précision, PR-AUC).

## Décision complémentaire — colonnes d'origine et score du réseau de neurones

Décision du 09/10/2026, après la Mesure 4. Elle ne modifie pas les relevés ci-dessus (42 variables restantes après retrait des fuites, identifiants et constantes) : elle précise lesquelles entrent dans le modèle.

| Colonne | Décision | Motif |
|---|---|---|
| `attribution` | Écartée | Identifie l'établissement d'origine, pas la lésion. Le taux de malignes varie d'un facteur 8 selon l'établissement (de 0,020 % pour Bâle à 0,156 % pour Frazer Institute ; comptage ponctuel sur le même fichier) : le modèle pourrait apprendre l'hôpital. Une cabine ne produit pas ce champ. |
| `copyright_license` | Écartée | Reflète la même information (`CC-0` correspond exactement à ACEMID MIA, 28 665 lignes). |
| `tbp_lv_dnn_lesion_confidence` | Conservée | Sortie de la cabine, disponible à l'arrivée d'une lésion. À signaler dans la model card comme dépendance à un autre modèle dont l'entraînement n'est pas connu. |

**Variables utilisées par le modèle : 40**, soit 35 numériques et 5 catégorielles (`sex`, `anatom_site_general`, `tbp_tile_type`, `tbp_lv_location`, `tbp_lv_location_simple`).

