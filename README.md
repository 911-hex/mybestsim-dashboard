# MyBestSim Dashboard eSIM

Dashboard Streamlit pour explorer les offres eSIM à partir de plusieurs fichiers CSV.

## Fonctionnalités

- Six indicateurs clés : nombre de produits, produits à plus de 100 €, prix minimum, prix maximum, moyenne de données en Go et prix moyen global.
- Répartition du nombre de produits par fournisseur.
- Prix moyen par fournisseur.
- Histogramme des prix et destinations les plus représentées.
- Filtres par fournisseur, destination et prix.
- Recherche de produits et téléchargement des données filtrées.

## 1. Préparer les données

Place les fichiers CSV dans le dossier `data/`.

Les quatre fichiers fournis avec le projet sont :
- `4sesim.csv`
- `airalo.csv`
- `alosim.csv`
- `esimx.csv`

Tu peux ajouter les autres fichiers CSV reçus pour le test dans ce même dossier. L'application détecte automatiquement les fichiers `.csv` présents dans `data/` ; les colonnes supplémentaires sont tolérées. Les champs `provider` et `price` sont nécessaires. Les champs `data_gb`, `product_name` et `country_name` sont utilisés quand ils existent.

**Avant de publier sur GitHub**, vérifie que les données peuvent être partagées publiquement. Tout CSV inclus dans un dépôt public pourra être téléchargé par d'autres personnes.

## 2. Lancer le dashboard sur ton Mac

Ouvre le Terminal, puis va dans le dossier du projet. Exemple si le dossier est dans Téléchargements :

```bash
cd ~/Downloads/mybestsim-dashboard
```

Crée un environnement Python :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installe les dépendances :

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Lance l'application :

```bash
streamlit run app.py
```

Streamlit affichera une adresse locale, généralement `http://localhost:8501`. Garde le Terminal ouvert pendant que tu utilises l'application localement.

Pour arrêter le serveur : `Ctrl + C` dans le Terminal.

## 3. Publier sur GitHub

1. Crée un dépôt GitHub nommé `mybestsim-dashboard`.
2. Depuis le Terminal, à la racine du projet, exécute :

```bash
git init
git add app.py requirements.txt README.md data/
git commit -m "Create MyBestSim eSIM dashboard"
git branch -M main
git remote add origin https://github.com/TON-PSEUDO/mybestsim-dashboard.git
git push -u origin main
```

Remplace `TON-PSEUDO` par ton identifiant GitHub. Si Git demande une authentification, utilise la méthode d'authentification configurée sur ton compte.

Ajoute un fichier `.gitignore` pour ne pas publier l'environnement local :

```text
.venv/
__pycache__/
.streamlit/secrets.toml
.DS_Store
```

## 4. Déployer sur Streamlit Community Cloud

1. Ouvre https://share.streamlit.io/ et connecte-toi avec GitHub.
2. Choisis **Create app**.
3. Sélectionne le dépôt `mybestsim-dashboard`, la branche `main` et le fichier principal `app.py`.
4. Lance le déploiement.
5. Une fois l'application démarrée, copie l'URL publique générée et teste-la dans une fenêtre privée ou un autre navigateur.

Les fichiers CSV doivent être présents dans le dépôt (ou accessibles par une source de données en ligne) pour que l'application hébergée puisse les lire. Ton Mac n'a pas besoin de rester allumé après le déploiement.

## Définitions et limites de calcul

- **Prix > 100 €** : strictement supérieur à 100 €, pas supérieur ou égal.
- **Prix minimum / maximum / moyen** : calculés sur les produits disposant d'un prix numérique valide.
- **Données moyennes (Go)** : calculées uniquement sur les valeurs numériques de `data_gb`. Les offres « illimitées » sans valeur numérique ne sont pas incluses dans cette moyenne.
- Les filtres affectent les indicateurs, les graphiques, le tableau et le téléchargement.

## Dépannage

- Si `streamlit` n'est pas trouvé, vérifie que l'environnement `.venv` est activé puis exécute `python -m pip install -r requirements.txt`.
- Si un fichier CSV est ignoré, vérifie qu'il contient au minimum les colonnes `provider` et `price`.
- Si les noms de colonnes sont différents, adapte la correspondance dans `app.py`.
