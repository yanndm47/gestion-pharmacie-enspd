# Documentation du projet

| Document | Contenu |
|---|---|
| Cahier des charges (v2.0) | Besoins, périmètre, fonctionnalités, planning, risques |
| Règles de gestion et dictionnaire de données (v2.0) | 64 règles RG-01 à RG-64, dictionnaire des 11 tables |
| MCD, MLD et base de données (v2.0) | Modèle conceptuel et logique, scripts SQL, guide de mise en place |
| Manuel d'utilisation et guide technique | Guide par tâche, architecture, dépannage, scénario de démonstration |
| Rapport final | Rapport de projet complet |
| Support de soutenance | Diaporama de 7 diapositives |

## Travail en équipe sur GitHub

1. Cloner le dépôt (GitHub Desktop : *File > Clone repository*).
2. Ne jamais travailler directement sur `main` : créer une branche (*Branch > New branch*), par exemple `stock-lots-prenom`.
3. Faire ses modifications, les valider (*Commit*), publier la branche (*Publish branch*).
4. Ouvrir une **Pull Request** ; le chef de projet relit puis clique *Merge*.
5. Avant de commencer une nouvelle tâche : récupérer `main` à jour (*Fetch origin* puis *Pull*).

Règle d'or : toute modification de la structure de la base passe d'abord par les scripts du dossier `sql/`, validée par le responsable de la base, puis rejouée par chaque membre (`python tools/installer_base.py`).
