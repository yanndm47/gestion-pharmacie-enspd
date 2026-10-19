# Gestion d'une pharmacie · ENSPD

Logiciel de gestion d'une pharmacie construit autour d'une **base de données MySQL** soigneusement modélisée
(méthode Merise, règles de gestion appliquées par la base elle-même) et d'une application **Python / Tkinter**
aux couleurs de l'**ENSPD** (École Nationale Supérieure Polytechnique de Douala).

Projet de groupe de la matière **Bases de données**.

## Aperçu

| Connexion | Caisse | Tableau de bord |
|---|---|---|
| ![Connexion](docs/captures/connexion.png) | ![Caisse](docs/captures/caisse.png) | ![Tableau de bord](docs/captures/tableau-de-bord.png) |

> Les captures sont à ajouter dans `docs/captures/` (voir `docs/README.md`).

## Fonctionnalités

- **Caisse** : recherche de médicaments, panier, client, paiement, ticket de caisse ; les lots sont vendus dans l'ordre de péremption (FEFO).
- **Ordonnances** : saisie, validité de 14 jours, suivi de ce qui reste à délivrer, vente réservée au pharmacien.
- **Stock par lot** : état du stock, alertes de rupture et de péremption, catalogue des médicaments.
- **Commandes et réceptions** : commandes aux fournisseurs, réception des lots, statuts automatiques.
- **Ventes** : historique, détail par lot, annulation avec remise en stock (pharmacien).
- **Clients, fournisseurs, comptes du personnel**, avec mots de passe hachés (PBKDF2).
- **Statistiques** : 13 analyses avec diagrammes (chiffre d'affaires, marges, ruptures, fournisseurs…).
- **Crédits** : page visible par tous les profils.

### Trois profils

| Profil | Droits |
|---|---|
| Personnel de caisse | Droits les plus réduits : ventes sans ordonnance obligatoire, fiches clients, ventes du jour |
| Pharmacien | Toute l'activité : ordonnances, commandes, lots, catalogue, annulations, statistiques |
| Administrateur | Comptes du personnel, lecture des statistiques |

## Technologies

Python 3.10+ · Tkinter · MySQL 5.7 / 8 ou MariaDB (WampServer) · DBeaver · mysql-connector-python

## Démarrage rapide

1. Démarrez **WampServer** (icône verte).
2. Installez Python 3.10 ou plus récent (cochez *Add python.exe to PATH* et gardez *tcl/tk*).
3. Dans un terminal, depuis le dossier du projet :
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python tools/installer_base.py --demo
   python main.py
   ```
   `installer_base.py` crée la base `pharmacie` (scripts du dossier `sql/`) ; `--demo` ajoute le jeu de données de démonstration.
4. Connectez-vous avec un compte de test :

| Identifiant | Mot de passe | Profil |
|---|---|---|
| `cdupont` | `Pharma2026!` | Pharmacien |
| `mngono` | `Caisse2026!` | Personnel de caisse |
| `admin` | `Admin2026!` | Administrateur |

Avec MariaDB (port 3307) : définissez d'abord `PHARMA_DB_PORT=3307`. Autres variables : `PHARMA_DB_HOST`, `PHARMA_DB_USER`, `PHARMA_DB_PASSWORD`, `PHARMA_DB_NAME`, `PHARMA_NOM` (nom sur les tickets).

> Le script SQL 01 **supprime et recrée** la base `pharmacie`. Ne le lancez pas sur une base contenant des données à garder.

## Dépannage

- Une analyse de la page *Statistiques* affiche une erreur : `python tools/tester_requetes.py` teste chaque requête sur votre base et affiche le message exact de MySQL.
- DBeaver coupe les triggers (erreur 1064) : utilisez `python tools/installer_base.py`.

## Tests

```
python -m unittest discover -s tests -t . -v
```

94 tests automatisés, sans base de données (sécurité, droits, répartition des lots, requêtes portables, génération des données…).

## Structure du dépôt

```
main.py  config.py  requirements.txt
core/      logique pure : droits, sécurité, répartition des lots, ticket, formats
db/        accès à MySQL (lecture et transactions)
services/  une fonction par opération métier (droits, SQL paramétré)
ui/        écrans Tkinter et charte graphique (ui/theme.py)
sql/       scripts 01 à 06 : schéma, triggers, données, tests, requêtes d'analyse, jeu de démonstration
tools/     installer_base.py, tester_requetes.py, generer_donnees.py
tests/     tests unitaires
docs/      documentation du projet et captures d'écran
```

Les couleurs de la charte (bleu et jaune) sont toutes dans `ui/theme.py` ; l'équipe et le nom de l'école dans `config.py`.

## Documentation

Cahier des charges, règles de gestion et dictionnaire de données, MCD / MLD, manuel d'utilisation et rapport sont décrits dans `docs/README.md`.

## Équipe

Projet réalisé à l'**ENSPD** par :

- YANN RAÏS DIKOUME MAYIBA
- MOLO BLAISE EMMANUEL
- BISAI BI MAHOP JOHN JOICE
- MOUKOKO NGALLE
- FOUMAN NGA
- DOUNGMENE ZOMESSI
- ATANGAGNA ADA SHAUN
- RYAN EKE NAMEKONG
- KOUNYEB EKEMBENGUE ROSINE GAËLLE
- ZE ZE CALIXT JAURES

## Licence

Projet académique : usage pédagogique. Contactez l'équipe avant toute réutilisation.
