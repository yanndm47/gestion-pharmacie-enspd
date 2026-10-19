#!/usr/bin/env python3
"""Teste TOUTES les requêtes d'analyse de l'application sur VOTRE base et affiche l'erreur exacte.

Usage (depuis le dossier pharmacie_app, environnement virtuel activé, WampServer démarré) :
    python tools/tester_requetes.py

Si une ligne affiche ERREUR, copiez-la telle quelle : elle contient le message exact de MySQL.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from db.connection import lecture  # noqa: E402
from services import stats_service as st  # noqa: E402
from services import vente_service  # noqa: E402
from services.auth_service import Utilisateur  # noqa: E402

PHARMACIEN = Utilisateur(0, "Test", "Diagnostic", "pharmacien")
ANALYSES = ["kpis_jour", "ca_par_jour", "ca_par_mois", "ca_par_semaine", "top_medicaments",
            "medicaments_jamais_vendus", "ventes_par_personnel", "clients_fideles", "performance_fournisseurs",
            "ventes_ordonnance_libre", "marge_par_medicament", "couverture_stock", "classement_categories",
            "affluence_par_heure", "alertes_rupture", "alertes_peremption"]


def main() -> int:
    try:
        with lecture() as cur:
            cur.execute("SELECT VERSION() AS version, @@sql_mode AS mode")
            infos = cur.fetchone()
    except Exception as erreur:
        print(f"Connexion impossible : {erreur}")
        return 2
    print(f"Serveur : {infos['version']}")
    print(f"sql_mode : {infos['mode']}\n")

    tests = [(nom, getattr(st, nom)) for nom in ANALYSES]
    tests += [("lister_ventes (tout l'historique)", lambda u: vente_service.lister_ventes(u, None))]
    echecs = 0
    for nom, fonction in tests:
        try:
            resultat = fonction(PHARMACIEN)
            n = 1 if isinstance(resultat, dict) else len(resultat)
            print(f"  OK       {nom:<40} {n} ligne(s)")
        except Exception as erreur:
            echecs += 1
            print(f"  ERREUR   {nom:<40} {type(erreur).__name__} : {erreur}")
    print(f"\n{len(tests) - echecs} requête(s) sur {len(tests)} fonctionnent.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
