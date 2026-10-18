# Application de gestion d'une pharmacie (Python)

Itération 5 : tous les modules sont développés, y compris l'historique des ventes (annulation, ticket) et les statistiques avec graphiques.
Un jeu de données enrichi est fourni (script SQL 06, généré par `tools/generer_donnees.py`).

## 0. Installer la base sans DBeaver (recommandé)

DBeaver coupe parfois les triggers et les procédures au premier point-virgule (erreur 1064 « near '' »). L'installeur Python envoie chaque routine en une seule instruction :

```
pip install -r requirements.txt
python tools/installer_base.py            (scripts 01, 02 et 03)
python tools/installer_base.py --demo     (ajoute le jeu enrichi, script 06)
```

Les scripts SQL sont dans le dossier `sql/`. Attention : le script 01 supprime et recrée la base `pharmacie`. Vérification : `SHOW TRIGGERS;` dans DBeaver doit donner 13 lignes.

## 1. Prérequis

- La base `pharmacie` créée dans WampServer avec les scripts SQL **01, 02 et 03**.
- WampServer démarré (icône verte).
- **Python 3.10 ou plus récent** (python.org). Sous Windows, à l'installation, cochez
  « Add python.exe to PATH » et laissez cochée l'option « tcl/tk and IDLE » (c'est elle qui fournit Tkinter).

## 2. Installation et lancement

Dans un terminal ouvert dans ce dossier :

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Sous PowerShell, si l'activation est bloquée : `Set-ExecutionPolicy -Scope Process Bypass`, puis relancez la commande `activate`.

## 3. Configuration de la connexion

Valeurs par défaut (WampServer) : hôte `localhost`, port `3306`, utilisateur `root`, mot de passe vide, base `pharmacie`.
Pour les changer sans toucher au code, définissez des variables d'environnement avant le lancement :

| Variable | Exemple |
|---|---|
| PHARMA_DB_PORT | 3307 (MariaDB de WampServer) |
| PHARMA_DB_USER | root |
| PHARMA_DB_PASSWORD | (vide par défaut) |
| PHARMA_DB_HOST | localhost |
| PHARMA_DB_NAME | pharmacie |

Windows, invite de commandes : `set PHARMA_DB_PORT=3307`. PowerShell : `$env:PHARMA_DB_PORT = "3307"`.

## 4. Comptes du jeu de test (script SQL 03)

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| cdupont | Pharma2026! | Pharmacien |
| mngono | Caisse2026! | Personnel de caisse |
| admin | Admin2026! | Administrateur |

À la première connexion, le mot de passe est automatiquement converti du hachage SHA-256 du jeu de test vers PBKDF2 (plus robuste).

## 5. Ce qui fonctionne dans cette itération

- **Nouveau : Ventes** (caisse : ventes du jour ; pharmacien et administrateur : 7 jours, 30 jours ou tout l'historique) : liste filtrable, détail par lot, **ticket de caisse** (double-clic) à afficher, enregistrer en .txt ou imprimer (impression directe sous Windows). Le pharmacien peut **annuler une vente** : les quantités reviennent en stock et l'ordonnance est libérée.
- **Nouveau : ticket après la vente** : la caisse propose d'afficher le ticket dès que la vente est enregistrée. Le nom de la pharmacie se règle avec la variable `PHARMA_NOM`.
- **Nouveau : Statistiques** (pharmacien et administrateur) : 13 analyses du script SQL 05, chacune sous forme de tableau et, quand c'est pertinent, de diagramme en barres (chiffre d'affaires par jour, mois, semaine, top des médicaments, marges, ventes par personnel, clients fidèles, fournisseurs, ordonnance contre vente libre, couverture du stock, affluence par heure...).

- **Nouveau : Clients** (caisse et pharmacien) : liste et recherche, création et modification de fiches complètes (nom, prénom, naissance, téléphone, email, adresse). Le pharmacien voit en plus l'historique des achats et des ordonnances du client sélectionné (données de santé : RG-23, la caisse n'y a pas accès). Aucun client n'est supprimé (RG-22).
- **Nouveau : Comptes** (administrateur) : créer un compte, modifier nom et rôle, désactiver ou réactiver, réinitialiser un mot de passe. Garde-fous : jamais de suppression, impossible de désactiver son propre compte ou de changer son propre rôle, il reste toujours au moins un administrateur actif.
- **Nouveau : Mon mot de passe** (bouton en haut, tous les rôles) : changement de son propre mot de passe (8 caractères minimum, ancien mot de passe exigé).

- **Nouveau : Stock** (tous les rôles en lecture) : *État du stock* par médicament (Rupture, Sous le seuil, OK, Désactivé), *Lots* avec code couleur de péremption (périmé, moins de 30 jours, moins de 90 jours, épuisé) et filtre par statut. Le pharmacien a en plus l'onglet *Catalogue* : création, modification et désactivation des médicaments.
- **Nouveau : Commandes et réceptions** (pharmacien) : créer une commande (fournisseur, lignes, prix prévu), suivre commandé / reçu / reste, **réceptionner un lot** (numéro de lot, péremption, quantité, prix d'achat) qui alimente directement le stock vendable en caisse, annuler une commande sans réception. Le statut de la commande (en cours, partielle, reçue) est mis à jour par la base.
- **Nouveau : Fournisseurs** (pharmacien) : création, modification, désactivation.

- **Nouveau : Ordonnances** (pharmacien) : liste filtrable par statut et par client ou médecin, détail de ce qui a été délivré et de ce qui reste, saisie d'une ordonnance avec ses lignes (médicament, quantité, posologie, durée). Validité automatique de 14 jours (`VALIDITE_ORDONNANCE_JOURS` dans `config.py`), contrôles RG-26, RG-28, refus d'une ordonnance déjà expirée.
- **Nouveau : lien caisse et ordonnances** : quand le pharmacien choisit l'ordonnance d'un client, la caisse affiche ce qu'il reste à délivrer.
- **Nouveau : maintenance à la connexion** : appel de la procédure `sp_maintenance_quotidienne` (lots périmés, ordonnances expirées). Un échec est signalé dans la console sans bloquer l'application.

- Connexion, déconnexion, onglets selon le rôle (droits du tableau 2.3 du document Règles de gestion).
- **Caisse** : recherche de médicaments avec stock vendable, panier, client (recherche ou création), ordonnance (pharmacien), mode de paiement, validation en une transaction. Les lots sont consommés par date de péremption (FEFO, RG-14) et une vente peut donc produire plusieurs lignes.
- **Tableau de bord** : chiffres du jour, alertes de rupture et de péremption, top des ventes, chiffre d'affaires par jour (pharmacien et administrateur). Le personnel de caisse ne voit que les ventes du jour.
- Les règles des triggers SQL (stock insuffisant, lot périmé, ordonnance...) s'affichent comme messages clairs.

## 6. Architecture (à respecter)

```
main.py            point d'entrée
config.py          paramètres de connexion
core/              logique pure, sans base ni interface (testable seule)
  errors.py        BusinessError, PermissionDenied, StockInsuffisant...
  permissions.py   droits par rôle : can(role, permission), require(user, permission)
  security.py      hachage des mots de passe
  allocation.py    répartition FEFO d'une quantité sur les lots
  formatting.py    montants, dates, nombres
  stock_rules.py   niveaux de péremption, état d'un stock
  ticket.py        mise en forme du ticket de caisse
  chart_layout.py  géométrie des diagrammes en barres
db/connection.py   lecture() et transaction() : seul endroit qui parle à MySQL
services/          une fonction = une opération métier (SQL paramétré + droits)
ui/                écrans Tkinter : appellent les services, jamais de SQL ici
tests/             tests unitaires (sans base de données)
tools/             generer_donnees.py : génère le script SQL 06 (jeu de données enrichi)
```

Règle : une couche n'appelle que celle du dessous (ui, puis services, puis db). Pas de SQL dans `ui/`.

## 7. Ajouter ou faire évoluer un module (marche à suivre)

1. **Service** dans `services/xxx_service.py` :
   - première ligne de chaque fonction : `require(user, "permission")` ;
   - SQL avec des paramètres `%s`, jamais de texte collé dans la requête ;
   - `with lecture() as cur:` pour consulter, `with transaction() as cur:` pour modifier ;
   - erreurs métier : `raise BusinessError("message lisible par l'utilisateur")`.
2. **Vue** dans `ui/xxx_view.py` : appelez les services avec `essayer(self, fonction, ...)` (affiche l'erreur à l'utilisateur).
3. **Onglet** : ajoutez une ligne `if can(u.role, "permission"): self._ajouter("Titre", MaVue(nb, u))` dans `ui/main_window.py`.
4. **Tests** : ajoutez un fichier dans `tests/` pour la logique pure, et un test SQL dans le script 04 pour les règles de la base.

## 8. Tests

```
python -m unittest discover -s tests -t . -v
```

85 tests, sans base de données : sécurité, droits, répartition FEFO, formats, règles de stock, ticket, géométrie des graphiques, logique de vente, d'ordonnance, de commande, de réception, de catalogue, de comptes et de clients avec un curseur simulé. Un test rejoue en plus le script 06 avec un émulateur des triggers pour prouver qu'il respecte toutes les règles de gestion.
Les règles de gestion protégées par les triggers se testent avec le script SQL 04.

## 9. Limites connues de cette itération

- Les appels à la base sont synchrones : l'écran se fige quelques instants pendant une requête (acceptable pour la taille du projet).
- L'impression directe du ticket ne fonctionne que sous Windows ; ailleurs, enregistrez le ticket puis imprimez le fichier.
- Les graphiques sont des diagrammes en barres simples dessinés sans bibliothèque externe (pas de courbes ni de camemberts).
- Le code a été relu et testé en logique, mais son premier lancement réel avec Tkinter et MySQL est à valider par le groupe. Signalez toute erreur avec le message complet.

## 10. Répartition proposée pour les 10 membres (phase de finition)

| Équipe | Membres | Mission |
|---|---|---|
| Tests et correction | 4 | Faire tourner l'application sur chaque machine, dérouler le scénario de la section 11, le script SQL 04 puis les 16 requêtes du script 05 sur le jeu enrichi, remonter les erreurs avec le message complet |
| Améliorations | 2 | Idées : alerte de commande automatique à partir des ruptures, modification d'une ordonnance, graphiques supplémentaires |
| Documentation | 4 | Rapport, MCD/MLD à jour, support de soutenance, synchronisation du cahier des charges et des règles de gestion, captures d'écran |

## 10 bis. Jeu de données enrichi (script SQL 06)

À exécuter **après** les scripts 01, 02 et 03, une fois que ces trois-là fonctionnent. Il ajoute 40 médicaments (50 au total), 25 clients (30), 2 fournisseurs (5), 2 membres du personnel (pmballa / Medecin2026! et jtagne / Caisse2026!), 13 commandes avec leurs réceptions, 19 ordonnances (20 au total) et environ 120 ventes sur les 90 derniers jours, avec 4 ventes annulées, 2 lots périmés, des lots proches de la péremption et des ruptures de stock.

Il ne contient aucune vente d'aujourd'hui : le tableau de bord du jour reste donc celui du script 03. Après le script 06, les valeurs attendues des scripts 04 et 05 changent (elles décrivent le petit jeu de test).

Pour le régénérer ou changer les volumes : `python tools/generer_donnees.py sortie.sql 2026` (le dernier nombre est la graine : même graine, même fichier). Toutes les dates sont relatives au jour d'exécution.

## 11. Scénario de test de bout en bout

1. Pharmacien : *Commandes* > Nouvelle commande (Loratadine, 40 unités) > *Réceptionner…* (lot, péremption, quantité). La commande passe à « Reçue ».
2. *Stock* > État du stock : la Loratadine n'est plus en rupture ; *Lots* : le nouveau lot apparaît.
3. *Ordonnances* > Nouvelle ordonnance pour un client, avec Amoxicilline.
4. *Caisse* : chercher le client, choisir son ordonnance, vendre. Le reste à délivrer s'affiche, le stock baisse.
5. *Tableau de bord* > Actualiser : chiffre d'affaires et alertes mis à jour. *Ventes* : double-clic sur la vente pour voir le ticket.
5 bis. Pharmacien : *Ventes* > sélectionner une vente > *Annuler la vente* ; vérifier que le stock est remonté dans *Stock*.
6. Caissier : vérifier qu'un médicament sur ordonnance est refusé et que les onglets Commandes, Ordonnances et Comptes n'existent pas.
7. Administrateur : créer un compte caissier, se reconnecter avec ce compte, changer son mot de passe, puis le désactiver. Vérifier qu'on ne peut pas désactiver le dernier administrateur.

# gestion-pharmacie-enspd
Logiciel de gestion d'une pharmacie en python avec une base de données MYSQL dans le cadre des travaux du cours de BASE DE DONNEES encadré par Monsieur ETOGUE D. SAINT-CLAIR à l'Ecole Nationale Supérieure Polytechnique de DOUALA

