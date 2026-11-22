# API d'analyse de sentiment

> Dépôt de départ du mini-projet **« Mettre en production une API de machine learning »**
> Module *Big data et architecture d'externalisation*, Master IA & Data Computing, INSA Hauts-de-France / UPHF.

L'équipe data de votre entreprise a développé une petite application : on lui donne un **avis de film en français**, elle répond s'il est **positif** ou **négatif**, avec un **score de confiance**.

```
« Un film magnifique, je le recommande ! »   →   positif (confiance 0,97)
```

L'application fonctionne sur le PC du data scientist. Mais elle **n'est pas prête pour la production** : pas de conteneur, pas de pipeline, pas de déploiement, pas de supervision.

**Votre mission, en tant qu'équipe cloud : la mettre en production.** Vous n'avez pas à modifier l'application ni à entraîner le modèle.

---

## Sommaire

1. [Les 5 étapes du projet](#1-les-5-étapes-du-projet)
2. [Récupérer le dépôt pour votre groupe](#2-récupérer-le-dépôt-pour-votre-groupe)
3. [Comprendre l'application](#3-comprendre-lapplication)
4. [Lancer l'application sur votre PC](#4-lancer-lapplication-sur-votre-pc)
5. [Tester l'application](#5-tester-lapplication)
6. [Configurer l'application](#6-configurer-lapplication)
7. [Référence : routes et métriques](#7-référence--routes-et-métriques)
8. [Problèmes fréquents](#8-problèmes-fréquents)
9. [Petit glossaire](#9-petit-glossaire)

---

## 1. Les 5 étapes du projet

| Étape | Ce que vous faites | Outil principal |
|---|---|---|
| 1. Conteneuriser | Mettre l'application et sa base de données dans des conteneurs | Docker |
| 2. Livrer en continu | Tester et publier l'image automatiquement à chaque modification | GitHub Actions |
| 3. Déployer | Faire tourner l'application sur un cluster | Kubernetes intégré à Docker Desktop |
| 4. Superviser | Suivre des indicateurs et recevoir une alerte en cas de panne | Grafana Cloud |
| 5. Viser la production | Proposer une architecture cloud et estimer son coût | Note d'architecture |

Les attendus détaillés de chaque étape sont dans **le sujet distribué en cours**. Les dates et la date limite sont données en cours.

## 2. Récupérer le dépôt pour votre groupe

Ce dépôt est un **modèle** (template). Chaque groupe en crée sa propre copie.

**Une seule personne du groupe :**

1. En haut de cette page, cliquez sur **Use this template**, puis **Create a new repository**.
2. Choisissez votre compte comme propriétaire, donnez un nom (par exemple `tp-cloud-groupe-3`) et cochez **Public** : GitHub Actions et le stockage des images y sont gratuits et sans limite.
3. Dans le nouveau dépôt : **Settings › Collaborators › Add people**, et ajoutez les autres membres du groupe.

**Puis chaque membre, dans un terminal :**

```bash
git clone https://github.com/VOTRE-COMPTE/VOTRE-DEPOT.git
cd VOTRE-DEPOT
```

> **Règle d'or :** le dépôt est public : aucun mot de passe ni jeton dedans, et pas de code de votre entreprise.

## 3. Comprendre l'application

```mermaid
flowchart LR
    U["Navigateur ou curl"] -->|"POST /predict"| A["API FastAPI"]
    A -->|"charge au démarrage"| M[("Modèle v1 ou v2")]
    A -->|"enregistre chaque prédiction"| D[("Base de données<br>SQLite en local<br>PostgreSQL en production")]
    S["Outil de supervision"] -->|"lit GET /metrics"| A
```

| Dossier ou fichier | Contenu |
|---|---|
| `app/main.py` | Les routes de l'API |
| `app/model.py` | Le chargement du modèle et la prédiction |
| `app/db.py` | L'historique des prédictions en base de données |
| `app/metrics.py` | Les métriques exposées pour la supervision |
| `app/config.py` | La configuration, lue dans les variables d'environnement |
| `app/static/` | La page web de test |
| `models/` | Les deux modèles : `v1` (précision 89,5 %) et `v2` (précision 94,3 %) |
| `tests/` | Les tests automatisés |
| `training/` | Le script qui a entraîné les modèles. Vous n'en avez pas besoin. |
| `requirements.txt` | Les bibliothèques Python nécessaires |
| `requirements-dev.txt` | Les mêmes, plus les outils de test et de vérification |

## 4. Lancer l'application sur votre PC

C'est le premier réflexe avant de conteneuriser : **comprendre comment l'application démarre**. Il vous faut **Python 3.12**.

Toutes les commandes se lancent **à la racine du dépôt** (le dossier qui contient ce README).

**Étape 1 : créer un environnement virtuel**, une installation de Python propre à ce projet.

```bash
python -m venv .venv
```

Sous Linux ou macOS, utilisez `python3` à la place de `python`.

**Étape 2 : l'activer.** La ligne de votre terminal commence alors par `(.venv)`.

| Système | Commande |
|---|---|
| Linux, macOS | `source .venv/bin/activate` |
| Windows, PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows, invite de commandes | `.venv\Scripts\activate.bat` |

**Étape 3 : installer les bibliothèques.**

```bash
pip install -r requirements-dev.txt
```

**Étape 4 : lancer l'API.**

```bash
uvicorn app.main:app --reload
```

L'API tourne tant que le terminal reste ouvert. `Ctrl+C` pour l'arrêter.

## 5. Tester l'application

- **La page de test :** ouvrez http://localhost:8000, tapez un avis, cliquez.
- **La documentation interactive :** ouvrez http://localhost:8000/docs. Chaque route peut y être essayée avec le bouton **Try it out**.
- **En ligne de commande**, sous Linux ou macOS :

  ```bash
  curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"text": "Un film magnifique, je le recommande !"}'
  ```

- **En ligne de commande**, sous Windows PowerShell :

  ```powershell
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict -ContentType "application/json" -Body '{"text": "Un film magnifique, je le recommande !"}'
  ```

Réponse attendue :

```json
{"label": "positif", "confidence": 0.97, "model_version": "v1"}
```

**Les tests automatisés et la vérification du code** (ce que votre pipeline lancera à l'étape 2) :

```bash
pytest                  # les tests
ruff check .            # les erreurs et le style du code
ruff format --check .   # la mise en forme
```

## 6. Configurer l'application

L'application ne contient **aucun réglage en dur** : tout passe par des **variables d'environnement**. C'est ce qui permet d'utiliser la même image en test et en production.

| Variable | Par défaut | À quoi elle sert |
|---|---|---|
| `MODEL_VERSION` | `v1` | Le modèle à charger : `v1` ou `v2` |
| `MODELS_DIR` | `models` | Le dossier qui contient les modèles |
| `DATABASE_URL` | `sqlite:///./predictions.db` | L'adresse de la base de données |
| `FAULT_ERROR_RATE` | `0` | Provoque des erreurs : `0.3` = 30 % des prédictions en erreur |
| `FAULT_LATENCY_MS` | `0` | Ralentit chaque prédiction, en millisecondes : `800` = 0,8 seconde |

**Base de données.** Sans configuration, l'application crée un petit fichier `predictions.db` (SQLite) : parfait pour tester sur votre PC. En production, elle doit utiliser **PostgreSQL**, avec une adresse de cette forme :

```
postgresql://utilisateur:motdepasse@nom-du-serveur:5432/sentiment
```

La table est créée automatiquement au démarrage.

**Pannes simulées.** `FAULT_ERROR_RATE` et `FAULT_LATENCY_MS` servent à l'étape 4 : vous provoquez une panne et vérifiez que votre supervision la voit et que votre alerte se déclenche.

## 7. Référence : routes et métriques

| Route | Ce qu'elle fait |
|---|---|
| `POST /predict` | Analyse un avis. Corps : `{"text": "..."}`, de 3 à 5 000 caractères. |
| `GET /history?limit=10` | Les dernières prédictions enregistrées |
| `GET /health` | Répond `200` si l'application **et** la base fonctionnent, `503` sinon |
| `GET /health/live` | Répond `200` tant que l'application tourne, sans regarder la base |
| `GET /metrics` | Les métriques, au format Prometheus |
| `GET /` | La page web de test |

Les deux routes `/health` serviront à Kubernetes, à l'étape 3. Réfléchissez à laquelle utiliser pour quoi.

| Métrique sur `/metrics` | Type | Ce qu'elle compte |
|---|---|---|
| `http_requests_total` | compteur | Les requêtes, par route et code de réponse |
| `http_request_duration_seconds` | histogramme | Le temps de réponse, par route |
| `predictions_total` | compteur | Les prédictions, par version du modèle et par résultat |
| `prediction_confidence` | histogramme | La confiance des prédictions, par version du modèle |
| `model_info` | jauge | Le modèle chargé, avec sa précision |

## 8. Problèmes fréquents

**`python` n'est pas reconnu, ou ce n'est pas la version 3.12.**
Vérifiez avec `python --version` (ou `python3 --version`). Sous Windows, cochez « Add Python to PATH » à l'installation.

**PowerShell refuse d'activer l'environnement virtuel.**
Utilisez l'invite de commandes (`cmd`) et `.venv\Scripts\activate.bat` à la place.

**`ModuleNotFoundError: No module named 'app'`**
Vous n'êtes pas à la racine du dépôt. Revenez dans le dossier qui contient ce README.

**`Address already in use` ou le port 8000 est occupé.**
Une autre application l'utilise. Lancez sur un autre port : `uvicorn app.main:app --reload --port 8001`.

**L'API répond `503` sur `/health`.**
Elle n'arrive pas à joindre la base de données. Vérifiez `DATABASE_URL`, et que la base est bien démarrée.

**Je suis bloqué depuis plus de 15 minutes.**
Relisez le message d'erreur en entier, cherchez-le, demandez à une IA… puis demandez en cours.

## 9. Petit glossaire

| Mot | En deux lignes |
|---|---|
| **API** | Une application qu'on interroge par des requêtes HTTP, plutôt qu'avec une interface graphique. |
| **Route** | Une adresse de l'API, comme `/predict`, qui fait une action précise. |
| **Environnement virtuel** | Une installation de Python isolée, pour que les bibliothèques d'un projet ne gênent pas les autres. |
| **Variable d'environnement** | Un réglage donné à l'application au démarrage, sans modifier son code. |
| **Conteneur** | L'application et tout ce dont elle a besoin, empaquetés pour tourner partout de la même façon. |
| **Pipeline** | Une suite d'étapes automatiques (tests, construction, publication) lancée à chaque modification. |
| **Métrique** | Un nombre qui évolue dans le temps : requêtes par seconde, temps de réponse… |

---

*Les modèles ont été entraînés sur le jeu de données [Allociné](https://huggingface.co/datasets/tblard/allocine) (avis de films en français). Le script d'entraînement est dans `training/`.*
