# MODEL CARD — DermaScan, modèle de tri de lésions cutanées

**Auteur : PELLICANO Théo** · M2 Industrialisation de l'IA dans le Cloud, YNOV Campus Montpellier · Séance 2, 09/10/2026

Version du modèle 1.0.0, entraîné le 09/10/2026. Rédigée le 09/10/2026 à partir des mesures de `EXPLORATION.md` et `MESURES.md`.

## Usage prévu

Aide au **tri** : parmi les lésions détectées par une cabine de photographie corporelle totale, signaler celles qui méritent un examen humain, pour qu'un dermatologue concentre son temps sur elles. Le service renvoie un score, un seuil et une décision `a_examiner` ou `non_signale`. Un dermatologue reste le seul à poser un diagnostic.

## Usage explicitement exclu

- Poser un diagnostic, ou conclure qu'une lésion est bénigne : `non_signale` signifie « non prioritaire pour ce service », jamais « sans danger ».
- Décider seul, sans relecture humaine, d'un traitement ou d'une absence de consultation.
- Utiliser le modèle sur des photographies hors cabine (téléphone, dermoscope) ou sur des mesures produites par un autre appareil.
- Utiliser le modèle chez des patients de moins de 18 ans : le jeu n'en contient presque pas (voir « Populations »).
- Le déployer dans une consultation spécialisée, où la prévalence des lésions malignes est bien plus élevée, sans l'évaluer à nouveau (voir `MESURES.md`, question 5.1).
- Lire `probabilite_maligne` comme une probabilité : c'est un score de classement, non calibré.

## Données d'entraînement

- **Origine** : jeu ISIC 2024 (*Skin Cancer Detection with 3D-TBP*), publié par l'International Skin Imaging Collaboration et récupéré sur Kaggle (`train-metadata.csv`, 257 543 161 octets). Données de santé, collectées auprès de volontaires dans plusieurs établissements : le champ `attribution` en compte 7 valeurs distinctes, alors que l'énoncé du TP parle de neuf institutions.
- **Volumétrie** : 401 059 lésions, 1 042 patients (de 1 à 9 184 lésions par patient, médiane 241), 393 lésions malignes portées par 259 patients.
- **Prévalence** : 0,098 % sur l'ensemble (1 maligne pour 1 020 bénignes) ; 0,0886 % sur le jeu d'entraînement (283 malignes sur 319 514 lésions). Cette prévalence est celle d'un échantillon de volontaires photographiés dans des centres hospitaliers, avec des lésions repérées automatiquement : elle diffère de la prévalence d'une consultation spécialisée (de l'ordre de 1 lésion sur 20) et de celle d'une population générale.
- **Découpage** : par patient (`GroupShuffleSplit`, graine 42, 20 % des patients en test), sans patient commun entre entraînement et test : 833 patients en entraînement, 209 en test.
- **Licences** : le champ `copyright_license` indique trois licences. Une part importante des lésions (183 582 sur 401 059) est sous licence CC-BY-NC, c'est-à-dire d'usage non commercial. **À faire valider juridiquement avant tout usage commercial du modèle.**

## Variables utilisées

40 variables, soit 35 numériques et 5 catégorielles, toutes produites par la cabine ou connues à l'arrivée d'une lésion. Regroupement indicatif :
- patient : âge approximatif, sexe ;
- localisation : site anatomique général, localisation et localisation simplifiée, coordonnées x, y, z sur le corps ;
- taille et forme : diamètre, aire, périmètre, axe mineur, rapport aire / périmètre, excentricité, symétrie et son angle, régularité du contour ;
- couleur : composantes L, A, B, C, H de la lésion et de la peau voisine, écarts entre elles, écart-type et homogénéité de la couleur ;
- scores de la cabine : confiance « naevus » et `tbp_lv_dnn_lesion_confidence`, **sortie d'un autre réseau de neurones dont l'entraînement n'est pas connu** ;
- type de vignette (`tbp_tile_type`).

## Variables écartées, avec le motif

| Colonne(s) | Motif |
|---|---|
| `iddx_1`, `iddx_full` | Diagnostic lui-même : `Malignant` coïncide exactement avec la cible (393 lignes). Fuite directe. |
| `iddx_2`, `iddx_3`, `iddx_4`, `iddx_5` | Sous-catégories du diagnostic, renseignées pour un millier de lignes qui contiennent toutes les 393 malignes. |
| `mel_thick_mm`, `mel_mitotic_index` | Mesures histologiques : renseignées uniquement pour des lésions malignes (63 sur 63, 53 sur 53). |
| `lesion_id` | Présent pour 5,5 % des lésions, mais pour les 393 malignes : révèle qu'un clinicien a déjà distingué la lésion. |
| `isic_id`, `patient_id` | Identifiants. `patient_id` sert seulement à découper sans fuite. |
| `image_type` | Constante (une seule modalité). |
| `attribution`, `copyright_license` | Identifient l'établissement d'origine : le taux de malignes varie d'un facteur 8 selon l'établissement, et une cabine ne produit pas ce champ. |

## Performance

Sur l'ensemble de test (209 patients, 81 545 lésions, **110 malignes**) :

| Mesure | Valeur | Valeur du hasard |
|---|---|---|
| PR-AUC | 0,0553 | 0,00135 |
| ROC-AUC | 0,9096 | 0,5 |

Ces valeurs sont celles de la graine 42. Sur six graines de découpage, la PR-AUC varie de 0,011 à 0,055 (médiane 0,032) et la ROC-AUC de 0,876 à 0,913 : la graine retenue est la plus favorable des six. Il faut lire la performance comme cette plage. L'exactitude (0,849) n'est pas un critère : un classifieur qui répond « bénin » partout atteint 0,9987. Le modèle est une régression logistique (`class_weight="balanced"`), un choix simple qui donne un tri faible à haut rappel.

## Seuil et compromis

- **Rappel visé** : 0,95, décidé le 09/10/2026 à 11:31 avant toute mesure sur la cible.
- **Seuil** : 0,1714, le plus élevé qui atteint ce rappel sur le test.
- **Rappel obtenu** : 0,9545 (105 malignes signalées sur 110 ; 5 manquées). Intervalle de Wilson à 95 % : environ 0,90 à 0,98, car le test ne contient que 110 positifs. Le seuil ayant été choisi sur ce même ensemble de test, le rappel mesuré est optimiste pour de nouvelles données.
- **Coût** : **341 lésions examinées par maligne trouvée** (précision 0,29 %), 438,6 alertes pour 1000 lésions, soit environ 170 lésions par patient. Signaler les lésions au hasard à ce même rappel demanderait 741 lésions par maligne trouvée.
- À 0,50, le service signale 152 lésions sur 1000 et laisse passer 20 malignes sur 110 (rappel 0,82).

## Populations et angles morts

Le jeu vient d'établissements d'Australie, d'Europe et des États-Unis. Ce qui est mesurable dans le fichier :
- **Âge** : 0,16 % des lésions (645) concernent des patients de moins de 18 ans, aucune n'est maligne ; la tranche de 60 à 74 ans porte à elle seule 202 des 393 malignes. Les performances chez l'enfant ne sont pas garanties.
- **Sexe** : 66,2 % d'hommes, 30,9 % de femmes, 2,9 % sans valeur. Les femmes sont sous-représentées.
- **Localisation** : la tête et le cou ne représentent que 3,0 % des lésions mais 78 malignes ; 5 756 lésions n'ont pas de site anatomique.
- **Phototype** : aucune colonne ne renseigne la couleur de peau ; on ne peut donc pas mesurer la performance selon le phototype. Le jeu étant issu de ces établissements, il est probable que les peaux foncées soient sous-représentées, mais ce point n'est pas vérifiable avec ce fichier.
- **Établissements** : le taux de malignes va de 0,020 % (Bâle) à 0,156 % (Frazer Institute). Un nouveau site n'est pas couvert par l'évaluation.

## Versions

| Élément | Valeur |
|---|---|
| Modèle | 1.0.0, entraîné le 2026-10-09 à 09:48 UTC |
| Image | `dermascan-api:1.0.0`, base `python:3.12.15-slim`, plateforme `linux/amd64` |
| Registre | `acrdermascantp42.azurecr.io/dermascan-api:1.0.0` |
| Digest | `sha256:81e8ae360e7ba69b8e88d7ed0d608bf90cb9fcf6fbf793cb95ed619bee2334e1` (publié le 09/10/2026 à 12:25 ; registre supprimé le 09/10/2026 à 16:44, voir `MESURES.md`. Une nouvelle publication donnera un autre digest, à reporter ici) |
| Bibliothèques | scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.3, scipy 1.18.1, joblib 1.6.0, Flask 3.1.3, gunicorn 26.2.0 |
| Entraînement | Python 3.14.0 ; image en Python 3.12.15 |

Un modèle sérialisé ne se recharge de façon fiable qu'avec les versions de bibliothèques qui l'ont produit : elles sont épinglées dans `requirements.txt`.
