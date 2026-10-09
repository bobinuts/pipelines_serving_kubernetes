# MESURES — Séance 2 (mesures 6 à 17, questions 2.1 à 6.1)

**Auteur : PELLICANO Théo** · M2 Industrialisation de l'IA dans le Cloud, YNOV Campus Montpellier · Séance 2, 09/10/2026

Numérotation : l'énoncé passe de la mesure 13 à la mesure 15 ; il n'existe pas de mesure 14.

## Tableau de décisions

| Décision | Votre valeur |
|---|---|
| Suffixe personnel, identique à la séance 1 | `tp42` |
| Nom du groupe portant le registre | `rg-dermascan-registre-tp42` |
| Nom du registre ACR de la séance 1 | `acrdermascantp42` |
| Rappel visé, décidé avant de voir le moindre résultat | **0,95** — décidé le 09/10/2026 à 11:31 (Europe/Paris), avant toute statistique sur les données (seul l'en-tête du CSV avait été lu) |
| Date portée par l'étiquette `a_detruire` | `2027-07-31` |

**Justification du rappel visé (0,95).** Manquer une lésion maligne peut coûter une vie, alors qu'une fausse alerte coûte un examen : je tolère donc de manquer au plus 5 malignes sur 100. Je n'exige pas 0,99, car l'ensemble de test ne contiendra que quelques dizaines de cas positifs : le gain ne serait ni mesurable ni défendable, et le nombre d'alertes deviendrait ingérable pour les dermatologues. Je n'accepte pas 0,90, qui laisserait passer une maligne sur dix.

## Contrôles de départ (vendredi 09/10/2026, ~11:08)

| Contrôle | Observation |
|---|---|
| `az group list` | 1 groupe : `rg-dermascan-registre-tp42` (germanywestcentral, Succeeded) |
| `az acr show` | `acrdermascantp42`, SKU Basic, `Succeeded` |
| Tags de `dermascan-health` | `0.1.0` |
| Étiquettes du groupe | `a_detruire=2027-07-31`, `projet=dermascan`, `proprietaire=theo.pellicano`, `role=registre` |
| Images locales `dermascan` | aucune (effet du `docker system prune` de la séance 1) |
| Python local | 3.14.0 (l'image est en 3.12 : versions des bibliothèques à épingler, cf. mesure 15) |
| Crédit restant | Pas de relevé à 11:08. Relevé fait à 12:47 : 0,28 € consommés, soit ≈ 87,72 € restants (dernier relevé précédent : 88,00 € le 06/10) |

## Journal des coûts Azure

Règle convenue le 09/10/2026 à 11:38 : toute étape qui crée, démarre ou fait varier une ressource Azure est annoncée avant, avec son coût. Extinction à la demande avec `scripts/99_extinction.ps1` (`-DetruireRegistre` pour supprimer aussi le registre).

| Date et heure | Événement | Effet sur le coût |
|---|---|---|
| 09/10/2026 11:08 | Contrôles de départ : un seul groupe, registre ACR Basic actif | Aucun changement. Registre seul facturé (≈ 0,167 $/jour d'après la fiche du TP1) |
| 09/10/2026 11:38 | Parties 1 et 2 locales : Kaggle, Python, entraînement | Aucun, rien côté Azure |
| 09/10/2026 11:41 | Contrôle `98_etat_azure.ps1` (lecture seule) | Conforme : 1 groupe, 1 ressource (le registre Basic), `dermascan-health:0.1.0` seul présent, 44 881 429 octets (44,9 Mo) utilisés sur 10 Go inclus. Aucun conteneur local |
| 09/10/2026 12:10 | Partie 4 : constructions Docker locales (`essai-libre`, `1.0.0`) | Aucun, rien côté Azure. Les images occupent 2 × 643 MB sur le disque du poste |
| 09/10/2026 12:25 | Partie 4 : `docker push` de `dermascan-api:1.0.0` dans le registre | Aucun surcoût attendu : ~147 Mo compressés ajoutés (dont 4 couches déjà présentes), dans les 10 Go inclus. Espace utilisé après push confirmé ensuite par `98_etat_azure.ps1` (12:49) : 149,1 Mo (la requête filtrée du script 09 était revenue vide). Toujours un seul groupe |
| 09/10/2026 12:47 | Relevé du crédit dans le portail (Cost Management) | 0,28 € consommés depuis le début, soit ≈ 87,72 € restants si le crédit de départ était de 88,00 € (relevé du 06/10). Cohérent avec ≈ 0,15 €/jour de registre depuis le 07/10 08:09 UTC ; la facturation Azure est différée de 8 à 48 h, donc le chiffre peut être légèrement en retard |
| 09/10/2026 14:11 | **Décision de Théo : aucune consommation pendant ≈ 2 semaines (pas d'utilisation avant la reprise des cours)** | Suppression du groupe `rg-dermascan-registre-tp42` demandée (`99_extinction.ps1 -DetruireRegistre`) : coût ramené à 0. Évité : ≈ 14 × 0,167 $ ≈ 2,3 $ (≈ 2 €). Contrepartie : les deux dépôts du registre sont effacés ; remise en route par `11_recreer_registre.ps1`, `08`, `09` (digest de `dermascan-api:1.0.0` à mettre à jour). À l'encontre de la recommandation de l'énoncé de conserver le registre ; décision assumée et tracée |
| 09/10/2026 16:44 | **Suppression exécutée** : `99_extinction.ps1 -DetruireRegistre`, confirmation `OUI` tapée à 16:42 | Groupe `rg-dermascan-registre-tp42` supprimé en 80,7 s (`sorties/99_extinction.txt`) ; `az group exists` = `false`, `az resource list` vide, `az group list` vide. Registre `acrdermascantp42`, `dermascan-health:0.1.0` et `dermascan-api:1.0.0` effacés. Coût Azure ramené à 0 ; crédit inchangé depuis le relevé de 12:47 (≈ 87,72 €) |

Note : l'étiquette `a_detruire=2027-07-31` est à 295 jours, soit environ 49 $ de registre à 0,167 $/jour. À reprendre à la question 6.1.

## Partie 2 — Pipeline

Source des chiffres : `sorties/04_entrainer.txt` (entraînement du 09/10/2026 à 11:48, graine 42) et `sorties/05_stabilite.txt` (six graines, 11:49). Configuration : régression logistique `class_weight="balanced"`, 40 variables (35 numériques, 5 catégorielles), 20 % des patients mis de côté pour le test, rappel visé 0,95.

### Mesure 6 — découpage

| Relevé | Entraînement | Test |
|---|---|---|
| Nombre de lignes | 319 514 | 81 545 |
| Nombre de patients | 833 | 209 |
| Nombre de positifs | 283 | 110 |
| Taux de positifs | 0,0886 % | 0,1349 % |

L'intersection des patients des deux côtés est vide (`assert` du script validé). Patients portant au moins une maligne : 199 en entraînement, 60 en test.

**Question 2.1.** Non, les deux taux diffèrent : 0,0886 % en entraînement contre 0,1349 % en test, soit un taux de test supérieur de plus de moitié. `GroupShuffleSplit` tire des patients au hasard sans équilibrer la classe rare, et les 393 malignes sont concentrées dans 259 patients (jusqu'à 14 malignes pour un seul patient) : quelques patients placés d'un côté ou de l'autre déplacent fortement le taux. La conséquence est que le score de test dépend de la graine. Mesuré sur six graines (`sorties/05_stabilite.txt`) :

| Graine | Positifs en test | Taux de test | PR-AUC | ROC-AUC |
|---|---|---|---|---|
| 0 | 86 | 0,097 % | 0,0336 | 0,8767 |
| 1 | 57 | 0,079 % | 0,0306 | 0,9129 |
| 2 | 100 | 0,126 % | 0,0345 | 0,9005 |
| 3 | 73 | 0,087 % | 0,0109 | 0,8760 |
| 4 | 69 | 0,086 % | 0,0212 | 0,8946 |
| 42 | 110 | 0,135 % | 0,0553 | 0,9096 |

Le nombre de patients de test est constant (209), mais le nombre de positifs va de 57 à 110 et la PR-AUC de 0,011 à 0,055, soit un facteur 5. La graine 42, retenue d'avance et non après coup, se trouve être la plus favorable des six (PR-AUC la plus haute, test le plus riche en positifs). La médiane des six est 0,032 : le chiffre à retenir pour juger le modèle est cette plage, pas la valeur de la graine 42.

### Mesure 7 — comparaison sur l'ensemble de test

| Modèle | Exactitude | ROC-AUC | PR-AUC |
|---|---|---|---|
| DummyClassifier | 0,99865 | 0,5000 | 0,00135 |
| Régression logistique | 0,84883 | 0,9096 | 0,05525 |
| Valeur du hasard pour la PR-AUC | — | — | 0,00135 |

**Question 2.2.** Avec `handle_unknown="error"`, une position anatomique jamais vue lève une exception au moment de la prédiction : l'API répond 500 et la lésion reste sans score. Avec `"ignore"`, la catégorie inconnue est encodée par des zéros et la lésion est notée à partir des 39 autres variables, avec une fiabilité réduite mais sans interruption. Je retiens `"ignore"` pour un service de tri médical : une lésion sans réponse revient à une lésion non triée, ce qui est pire qu'un score dégradé. Le prix à payer est le silence de l'erreur, donc il faut compter les catégories inconnues pour les voir en production (suivi de la séance 5).

**Question 2.3.** Faite avant le découpage, l'imputation (et la mise à l'échelle) calculerait ses médianes, moyennes et écarts-types sur tous les patients, test compris : les statistiques du jeu de test entreraient dans le modèle, et le score de test serait flatteur.

**Question 2.4.** Selon l'exactitude seule, le meilleur est le `DummyClassifier` (0,99865 contre 0,84883), alors qu'en réalité c'est la régression logistique : elle trouve 90 des 110 malignes au seuil 0,50 (rappel 0,82), le Dummy n'en trouve aucune. L'exactitude compte la part de réponses justes sans distinguer les deux sortes d'erreur ; or 99,865 % des lésions du test sont bénignes, donc répondre « bénin » partout est juste presque toujours. Elle ne compte pas ce qui importe ici : les 110 malignes, qui pèsent 0,13 % des lignes. La régression logistique perd de l'exactitude parce qu'elle signale des bénignes à tort (12 307 faux positifs à 0,50), ce qui est le prix de chercher les malignes.

**Question 2.5.** Sur mes chiffres, le taux de positifs du test est 110 / 81 545 = 0,001349, et c'est bien la PR-AUC du hasard (0,00135, celle du Dummy). La régression logistique atteint 0,0553, soit environ 41 fois le hasard. La PR-AUC est plus informative que la ROC-AUC quand la classe positive est très rare parce que la ROC-AUC rapporte les faux positifs au nombre de bénignes (81 435), énorme : 12 307 faux positifs ne représentent que 15 % de ce nombre, et la ROC-AUC affiche un correct 0,91. La PR-AUC rapporte les vrais positifs aux alertes émises (précision de 0,7 % à 0,50) et rend visible le coût réel en fausses alertes.

### Mesure 8 — compromis rappel / précision (ensemble de test)

| Seuil | Rappel | Précision | Vrais positifs | Faux positifs | Faux négatifs | Alertes pour 1000 lésions |
|---|---|---|---|---|---|---|
| 0,50 | 0,8182 | 0,00726 | 90 | 12 307 | 20 | 152,0 |
| 0,80 | 0,6091 | 0,01531 | 67 | 4 309 | 43 | 53,7 |
| 0,90 | 0,4727 | 0,02179 | 52 | 2 334 | 58 | 29,3 |
| 0,99 | 0,1818 | 0,04938 | 20 | 385 | 90 | 5,0 |

### Mesure 9 — seuil retenu et son coût

| Relevé | Votre valeur |
|---|---|
| Rappel visé, décidé en début de séance | 0,95 (09/10/2026, 11:31) |
| Seuil correspondant | 0,1714 (0,171449) |
| Précision à ce seuil | 0,002936 (0,29 %) |
| Nombre de lésions examinées par maligne trouvée | 341 |
| Faux négatifs restants | 5 (sur 110 malignes ; rappel obtenu 0,9545, soit 105 trouvées) |

À ce seuil, le service signale 35 765 lésions sur 81 545 (105 vrais positifs et 35 660 faux positifs), soit 438,6 pour 1000 lésions. Le seuil retenu est le plus élevé qui garantit le rappel visé : le rappel décroît quand le seuil monte, donc le dernier indice vérifiant `rappel >= 0,95` correspond au moins d'alertes (le commentaire de l'énoncé parle de « plus petit seuil », mais c'est bien l'indice `-1` qui minimise les alertes).

**Question 2.6.** Présentation au médecin-chef : « Pour garantir que le service retrouve 95 % des lésions malignes, un dermatologue doit examiner 341 lésions pour en trouver une maligne. Concrètement, le service signale 44 lésions sur 100, soit environ 170 lésions par patient (390 lésions en moyenne dans le test). C'est environ 2,2 fois mieux que de tout signaler au hasard, qui donnerait 741 lésions examinées par maligne trouvée. » Si le médecin-chef juge le nombre inacceptable, je ne lui réponds pas par un autre seuil présenté comme équivalent : il y a trois leviers, qui coûtent chacun quelque chose. Abaisser le rappel visé (au seuil 0,50, le service signale 15 lésions sur 100 mais laisse passer 20 malignes sur 110) : c'est une décision clinique, à consigner comme une nouvelle version et non à substituer en silence. Améliorer le modèle (un modèle non linéaire tel qu'un arbre boosté, ou un classement des lésions au sein de chaque patient) : cela suppose de refaire l'entraînement. Changer l'usage, par exemple en ne présentant que les lésions les mieux classées de chaque patient. Dans l'état actuel, ce modèle linéaire fait un tri faible à 95 % de rappel.

**Question 2.7.** Le service signale 95 lésions malignes sur 100 (mesuré sur 110 cas de test, avec une marge d'incertitude de l'ordre de quatre points, soit 90 à 98 % en intervalle de Wilson à 95 %) et laisse passer les autres ; il ne garantit pas l'absence de maligne parmi les lésions non signalées et ne pose pas de diagnostic.

Limite à connaître : le seuil est choisi sur l'ensemble de test, comme le demande l'énoncé, avec seulement 110 positifs. Le rappel mesuré (0,9545) est donc optimiste pour de nouvelles données, et une seule maligne de plus ou de moins change le rappel de près d'un point.

### Mesure 10 — paquet produit

| Relevé | Votre valeur |
|---|---|
| Taille du fichier, en Ko | 9,6 Ko (9 780 octets) |
| Nombre de colonnes attendues déclarées | 40 |
| Durée de l'entraînement, en secondes | 10,5 |

Versions ayant entraîné le modèle (champ `versions` du paquet) : Python 3.14.0, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.3, joblib 1.6.0. Prévalence d'entraînement : 0,0886 %. Version du modèle : 1.0.0.

**Question 2.8.** `prevalence_entrainement` ne sert à aucun calcul à la prédiction, mais elle garde la référence de ce que le modèle a vu : en séance 5, on comparera le taux de lésions positives (ou le taux d'alertes) du flux reçu à ce 0,0886 % pour décider si le flux ressemble encore à celui de l'entraînement. Un écart important signale une dérive, c'est-à-dire un seuil et des probabilités qui ne correspondent plus à la population servie (voir aussi la Q5.1).

**Question 2.9.** Sans `colonnes_attendues` dans le paquet, l'API ne pourrait pas, premièrement, valider la charge utile : elle ne saurait pas quelles colonnes sont requises, donc ne pourrait pas répondre 400 en nommant celles qui manquent, et une charge incomplète provoquerait une erreur interne (500) lors du `transform`. Deuxièmement, elle devrait reconstruire la liste des 40 colonnes en dur dans `app.py` (et dans `/model/info`) : à chaque réentraînement qui changerait les variables, le code et le modèle divergeraient sans que rien ne le signale.

## Partie 3 — API d'inférence

Source : `sorties/06_api_local.txt` (09/10/2026, 11:58). Serveur de développement Flask lancé en local sur le port 8000 (`python app.py`), appelé avec `curl.exe`.

### Mesure 11 — réponses de l'API

| Appel | Code HTTP | Élément relevé |
|---|---|---|
| `GET /health` | 200 | `model_loaded` : `true` (version du modèle 1.0.0) |
| `GET /model/info` | 200 | 40 colonnes attendues ; seuil 0,1714 ; rappel cible 0,95 |
| `POST /predict`, charge valide (ligne bénigne du test) | 200 | `probabilite_maligne` 0,031763, `decision` : `non_signale` |
| `POST /predict`, charge valide (ligne maligne du test) | 200 | `probabilite_maligne` 0,750524, `decision` : `a_examiner` |
| `POST /predict`, charge incomplète (5 colonnes retirées) | 400 | 5 variables manquantes signalées (`age_approx`, `clin_size_long_diam_mm`, `tbp_lv_A`, `tbp_lv_x`, `sex`) |
| `POST /predict`, corps vide | 400 | message : corps JSON absent, vide ou invalide |

La liste des manquantes est tronquée à 10 noms, comme dans l'énoncé ; le champ `nombre_manquantes` donne le total réel. Les deux lignes de test sont des lignes réelles de l'ensemble de test (`charge.json` : première ligne bénigne sans valeur manquante ; `charge_maligne.json` : première ligne maligne sans valeur manquante). Elles n'ont pas été choisies pour leur score.

### Mesure 12 — latence de dix appels successifs sur charge valide

| Minimum | Médiane | Maximum |
|---|---|---|
| 217,8 ms | 224,5 ms | 240,3 ms |

Valeurs : 217,8 – 231,6 – 233,8 – 240,3 – 228,0 – 218,5 – 221,6 – 223,4 – 225,5 – 221,3 ms, relevées par `curl.exe` (`time_total`) sur `http://localhost:8000`. Cette latence est élevée pour un modèle linéaire de 9,6 Ko, et très stable (écart de 22 ms entre minimum et maximum) : un délai fixe se cache probablement dans le chemin réseau local (par exemple une tentative d'abord en IPv6 sur `localhost`), plutôt que dans le calcul du modèle. Hypothèse non vérifiée ; les mesures du conteneur utiliseront `127.0.0.1` pour la tester.

**Question 3.1.** Le fichier fait 9,6 Ko ; un second `joblib.load` (modules déjà importés) a coûté **1,5 ms**. Rechargé à chaque requête, le modèle ajouterait donc environ 1,5 ms par appel, soit moins de 1 % des ~224 ms mesurés. L'enjeu est faible ici parce que le modèle est minuscule. Le principe reste juste, car la lecture et la désérialisation croissent avec la taille du fichier : pour un modèle de plusieurs centaines de Mo, le même défaut ajouterait un délai notable à chaque appel, et sous charge chaque requête relirait le disque et réallouerait la mémoire.

**Question 3.2.** La décision seule ne suffit pas à interpréter une réponse archivée. `decision` est le résultat de `probabilite_maligne >= seuil` ; or le seuil est un paramètre qui peut changer (variable `SEUIL`, réentraînement). Dans six mois, un dermatologue qui lit `non_signale` ne saurait pas à quel seuil, donc à quel risque, cette décision a été prise. Avec `seuil`, `rappel_cible` et `version_modele`, la réponse est auto-explicative : on peut refaire la comparaison, savoir que le service visait 95 % de rappel (donc acceptait de manquer 5 malignes sur 100) et retrouver quel modèle l'a produite.

**Question 3.3.** Avec le modèle retiré, `GET /health` renvoie **503** (`model_loaded: false`, avec le motif `FileNotFoundError: ... model/modele.joblib`), et `POST /predict` renvoie aussi 503. C'est préférable à un plantage au démarrage pour la plateforme de séance 3 : un processus qui s'arrête est redémarré en boucle, le motif se perd dans une alternance de démarrages, et l'on ne distingue plus « le processus tourne » de « le service peut répondre ». Avec un 503, le processus reste vivant, la sonde indique clairement que l'instance n'est pas prête, la plateforme ne lui envoie pas de trafic, et le corps de la réponse donne la cause.

## Partie 4 — Conteneurisation et publication

Source : `sorties/07_docker_libre.txt` (essai sans épinglage, 12:06) et `sorties/08_docker_final.txt` (image finale, 12:10). Base `python:3.12.15-slim`, Docker Desktop, plateforme `linux/amd64`. L'image finale a été construite avec `--platform linux/amd64 --provenance=false`, les options de la reconstruction du 4.4 : cette étape est donc déjà faite, il n'y a pas de seconde reconstruction.

### Mesure 13 — image de la séance 2, comparée à celle de la séance 1

| Relevé | Séance 1 | Séance 2 |
|---|---|---|
| Taille de l'image | 185 MB (44,9 MB compressés) | 643,4 MB (643 426 330 octets ; 147 MB compressés) |
| Nombre de couches | non relevé en séance 1 | 10 couches du système de fichiers (`RootFS.Layers`), 20 lignes dans `docker history` |
| Durée de construction à froid | 16,8 s | 52,8 s (`--no-cache`) ; 66,6 s pour l'essai sans épinglage |
| Nombre de paquets dans `pip freeze` | 7 | 18 |

Compléments : l'étape `pip install` dure 26,7 s à froid (4,1 s en séance 1). Pour les couches, l'image de la séance 1 comptait une instruction de copie de moins (pas de `COPY model/...`) : on peut en déduire 9 couches du système de fichiers, mais ce n'est pas une mesure. Les deux images construites (`essai-libre` et `1.0.0`) pèsent exactement la même chose à quelques octets près (643 399 592 contre 643 426 330 octets).

**Question 4.1.** L'écart de taille mesuré est de **+458 MB** sur disque (185 → 643 MB, soit un facteur 3,5) et de +102 MB une fois compressé (44,9 → 147 MB). Je n'avais pas consigné d'estimation avant la mesure ; l'ordre de grandeur attendu pour quatre bibliothèques scientifiques binaires (numpy, scipy, pandas, scikit-learn) est de plusieurs centaines de Mo, et la mesure le confirme. Cette mesure permet aussi de vérifier l'estimation de la Q3.8 de la séance 1 (« environ 1 minute perdue par build en ordre naïf ») : l'étape `pip install` dure 26,7 s, soit environ la moitié. Sur 20 itérations par jour, la perte en ordre naïf est d'environ 9 minutes, pas de 20 à 30. L'ordre « dépendances d'abord, code ensuite » reste justifié, mais l'estimation était environ deux fois trop pessimiste.

**Question 4.2.** Le modèle pèse 9,6 Ko, l'image 643 MB : ce qui coûte cher dans un artefact d'inférence, ce sont les dépendances (et l'image de base, 179 MB en séance 1), pas le modèle. Si la taille devenait un problème, il faudrait d'abord examiner la couche `pip install` (par `docker history`) et réduire les bibliothèques embarquées : se demander si `pandas` et `scipy` sont indispensables à l'inférence, ou construire en plusieurs étapes pour ne garder que l'installation finale. Réentraîner un modèle plus petit ne changerait presque rien.

Une observation à noter : gunicorn 26.2.0 crée sa socket de contrôle dans `/home/appuser/.gunicorn/gunicorn.ctl` (visible dans les journaux du conteneur). Le répertoire personnel de l'utilisateur est donc utilisé à l'exécution, ce qui justifie le passage de `--no-create-home` à `--create-home` dans le Dockerfile.

### 4.3 — l'artefact est lié à la version qui l'a produit

Premier essai avec un `requirements.txt` sans épinglage (sauf Flask 3.0.3, comme en séance 1) : l'image se construit, le conteneur démarre et `POST /predict` répond 200 avec `probabilite_maligne` = 0,031763, **la même valeur que hors conteneur**. L'erreur annoncée par l'énoncé ne s'est pas produite : à la date du 09/10/2026, `pip` a installé pour Python 3.12 la dernière version de scikit-learn, qui est justement celle du venv (1.9.1). Le risque existe, mais il n'a pas été déclenché ici ; je ne l'ai pas inventé. Les versions de Python diffèrent (3.14.0 à l'entraînement, 3.12.15 dans l'image) sans que cela gêne le rechargement.

### Mesure 15 — cohérence des versions entre l'entraînement et l'image

| Relevé | Votre valeur |
|---|---|
| Version de scikit-learn ayant entraîné le modèle — champ `versions` du paquet | 1.9.1 |
| Version de scikit-learn épinglée dans `requirements.txt` | 1.9.1 (dans l'image finale) ; essai sans épinglage : `pip` a installé 1.9.1 |
| Sont-elles identiques ? | Oui, dans les deux constructions |
| Message d'erreur exact, s'il y en a un | Aucun. Dans l'image, `python 3.12.15 / sklearn 1.9.1 / pandas 3.0.6 / numpy 2.5.3 / joblib 1.6.0` |

L'image finale épingle quand même les versions du venv (`Flask 3.1.3`, `gunicorn 26.2.0`, `scikit-learn 1.9.1`, `pandas 3.0.6`, `joblib 1.6.0`, `numpy 2.5.3`, `scipy 1.18.1`), pour que la cohérence ne dépende plus de la date de construction.

**Question 4.3.** Sans épinglage, l'image aurait cessé de fonctionner à deux moments. Le premier est la construction : si une nouvelle version de scikit-learn sort entre l'entraînement et le build, `pip` l'installe, et le modèle sérialisé par l'ancienne version ne se recharge plus correctement. Le second est n'importe quelle reconstruction ultérieure (correction de `app.py`, mise à jour de l'image de base, cache vidé), qui récupère à nouveau « la dernière version » alors que le code n'a pas changé. Le second est le plus dangereux pour un service en production : il frappe un service qui marchait, à un moment imprévu (un redéploiement de dépannage, une montée en charge qui reconstruit), sans qu'on ait touché au modèle, et le désaccord de versions peut produire un avertissement discret ou des prédictions altérées plutôt qu'un échec net. Le premier est attrapé au test avant la mise en service.

### 4.4 — publication

Source : `sorties/09_publier.txt` (09/10/2026, 12:25). Image envoyée : `acrdermascantp42.azurecr.io/dermascan-api:1.0.0`.

### Mesure 16 — publication

| Relevé | Votre valeur |
|---|---|
| Durée du push | 19,4 s |
| Digest obtenu | `sha256:81e8ae360e7ba69b8e88d7ed0d608bf90cb9fcf6fbf793cb95ed619bee2334e1` |
| Tags présents dans le registre | dépôt `dermascan-api` : `1.0.0` ; le dépôt `dermascan-health` (`0.1.0`) est inchangé |

Détail : 10 couches, dont 6 envoyées (`Pushed`) et 4 `Mounted from dermascan-health`. Ces 4 couches sont celles de l'image de base `python:3.12.15-slim`, déjà présentes dans le registre grâce à la séance 1, donc non retransférées. Le registre a été supprimé depuis (journal des coûts, 16:44) : ce digest n'est plus consultable, la capture `captures/acr_dermascan_api.png` fait foi. Le manifeste est unique (`amd64` / `linux`, type OCI, 147 443 915 octets), sans index ni attestation de provenance, grâce à `--provenance=false`. En séance 1, le premier push de l'image Flask avait pris 4,1 s (11 blobs) ; l'image actuelle est plus grosse, mais la déduplication par contenu évite de renvoyer la base.

## Partie 5 — Gouvernance

La model card est dans `MODEL_CARD.md`. Réponses aux deux questions de la partie.

**Question 5.1.** Non, le seuil ne reste pas valable tel quel. Ce qui bouge avec la prévalence est la précision, pas le rappel : avec les mêmes taux de détection (95,5 % des malignes signalées) et de fausses alertes (35 660 sur 81 435 bénignes, soit 43,8 %) qu'à l'évaluation, une prévalence de 1 sur 20 (5 %) donnerait une précision d'environ 10 % (contre 0,29 %), c'est-à-dire environ 10 lésions examinées par maligne trouvée au lieu de 341. C'est une estimation par le calcul : elle suppose que les lésions de cette consultation ressemblent à celles de l'entraînement, ce qui est précisément douteux, car des patients adressés à un spécialiste ont des lésions plus suspectes que des volontaires en pharmacie, donc des distributions différentes. De plus, `class_weight="balanced"` rend le score non calibré : `probabilite_maligne` est un score de classement, pas la probabilité réelle d'être maligne (à 0,17, la fréquence réelle observée est de 0,3 %). Il faudrait refaire : évaluer le modèle sur un échantillon représentatif de cette consultation (nouveau jeu de test avec ses patients), recalibrer les probabilités, choisir à nouveau le rappel visé et le seuil en fonction du coût local (au même seuil, le service signalerait encore environ 460 lésions sur 1000, ce qui apporte peu à un spécialiste qui ne voit déjà que des lésions suspectes), et réentraîner si les performances ont chuté.

**Question 5.2.** Les patients de moins de 18 ans. Je m'appuie sur la colonne `age_approx` : seulement 645 lésions sur 401 059 (0,16 %) concernent des patients de moins de 18 ans, et aucune n'est maligne. Le modèle n'a donc rien vu qui lui permette de reconnaître une maligne chez l'enfant, et rien ne permet de mesurer sa performance sur cette population. Deux autres angles morts, moins marqués : les femmes (30,9 % des lésions contre 66,2 % pour les hommes ; 11 517 lignes sans sexe), et les peaux foncées, que le jeu ne permet même pas de mesurer, faute de colonne de phototype.

## Nettoyage et extinction

Source : `sorties/98_etat_azure.txt` (12:49) et `sorties/99_extinction.txt` (12:50), relevés du 09/10/2026. Aucune ressource Azure n'a été créée ni supprimée pendant la séance : elle a seulement publié `dermascan-api:1.0.0` dans le registre de la séance 1.

### Mesure 17 — contrôles de nettoyage et coût de ce que je laisse actif

**Mise à jour du 09/10/2026 à 16:44.** Le tableau ci-dessous est le relevé de fin de séance (12:49-12:50), où le registre était laissé actif comme le demande l'énoncé. Je l'ai ensuite supprimé : je n'utilise pas le module pendant environ deux semaines avant la reprise des cours, et seule la suppression du groupe arrête la facturation du registre (≈ 0,167 $/jour, soit ≈ 2,3 $ sur 14 jours). Relevé après suppression (`sorties/99_extinction.txt`, 16:42-16:44) : nombre de ressources laissées actives = **0**, `az group list` vide, coût journalier = 0. C'est une entorse à la consigne de conserver le registre jusqu'à la fin du module ; elle est assumée, tracée au journal des coûts, et se rattrape avant la séance 3 (voir `11_recreer_registre.ps1`).

| Contrôle de fin de séance | Votre observation |
|---|---|
| Espace disque libéré par `docker system prune` | 932,7 MB (« Total reclaimed space », cache de build). La suppression préalable des deux images de la séance a aussi fait passer les images locales de 2,859 GB à 1,927 GB |
| Espace libéré en séance 1, pour comparaison | 29,63 MB |
| Nombre de ressources laissées actives | 1 : le registre `acrdermascantp42` (SKU Basic), seul dans le groupe `rg-dermascan-registre-tp42` ; un seul groupe dans l'abonnement |
| Coût journalier estimé du SKU Basic | ≈ 0,167 $/jour (≈ 5 $/mois, d'après la fiche du TP1) |
| Date portée par l'étiquette `a_detruire` | 2027-07-31 |
| Crédit restant, relevé dans Cost Management | 0,28 € consommés depuis le début (relevé du 09/10 à 12:47), soit ≈ 87,72 € restants sur 88,00 € |
| Écart avec le relevé de la séance précédente | −0,28 € depuis le relevé du 06/10 (88,00 €). C'est un peu moins que 0,15 €/jour × durée de fonctionnement du registre ; la facturation est différée de 8 à 48 h, donc l'écart est à re-vérifier au prochain relevé |

Espace occupé dans le registre après publication : 149 076 119 octets (149,1 Mo, 1,4 % des 10 Go inclus), contre 44 881 429 octets avant : le push de `dermascan-api` a ajouté 104,2 Mo, car les couches de l'image de base étaient déjà présentes. Le dépôt `dermascan-health` (tag `0.1.0`) est toujours là. Le coût du registre ne dépend pas de cet espace tant que les 10 Go inclus ne sont pas dépassés.

**Question 6.1 (relevé de 12:50, registre alors laissé actif).** La phrase de la séance 1 était : « Le registre ACR `acrdermascantp42` (groupe `rg-dermascan-registre-tp42`, SKU Basic, ≈ 0,17 $/jour) doit rester actif car il héberge l'image `dermascan-health` consommée par les séances 2 à 4 et le projet fil rouge ; il peut être détruit sans me consulter après le 31/07/2027. » Elle n'est plus exacte : l'image que la suite consomme n'est plus `dermascan-health:0.1.0` mais `dermascan-api:1.0.0`, que la séance 3 déploiera selon le contrat d'interface. Version corrigée : « Le registre ACR `acrdermascantp42` (groupe `rg-dermascan-registre-tp42`, SKU Basic, ≈ 0,17 $/jour) doit rester actif car il héberge `dermascan-api:1.0.0` (digest `sha256:81e8ae36…`), l'image déployée en séance 3 puis reprise en séance 4 et dans le projet fil rouge ; `dermascan-health:0.1.0` n'est plus utilisée. Il peut être détruit sans me consulter à la fin du projet fil rouge, et au plus tard le 31/07/2027 (`az group delete --name rg-dermascan-registre-tp42 --yes`) ; l'image se reconstruit à partir de `s2-dermascan/`. » Ce qui m'a fait la corriger : le contenu du registre a changé (un second dépôt) et la date de 295 jours coûterait environ 49 $, soit plus de la moitié du crédit ; elle a été écrite avant de savoir combien de séances en dépendraient, et c'est un plafond que je réduirai dès que la date de soutenance sera connue.


