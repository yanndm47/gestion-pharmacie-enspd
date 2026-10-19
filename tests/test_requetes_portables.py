"""Garantit que les requêtes d'analyse fonctionnent sur MySQL 5.7, MySQL 8 et MariaDB.

Les fonctions de fenêtrage (LAG, RANK, OVER) n'existent pas sur MySQL 5.7 : elles faisaient
échouer plusieurs écrans de statistiques. De même, un signe % dans une requête exécutée avec des
paramètres est mal interprété par le connecteur."""
import os
import re
import sys
import types
import unittest
from contextlib import contextmanager
from types import SimpleNamespace

try:
    import mysql.connector  # noqa: F401
except ImportError:
    faux = types.ModuleType("mysql.connector")
    faux.Error = type("Error", (Exception,), {})
    faux.connect = lambda **kw: None
    pkg = types.ModuleType("mysql")
    pkg.connector = faux
    sys.modules["mysql"] = pkg
    sys.modules["mysql.connector"] = faux

from services import stats_service as st  # noqa: E402

PH = SimpleNamespace(role="pharmacien")
INTERDIT = re.compile(r"\bOVER\s*\(|\bLAG\s*\(|\bLEAD\s*\(|\bRANK\s*\(|\bROW_NUMBER\s*\(|\bDENSE_RANK\s*\(|DATE_FORMAT|\bWITH\s+\w+\s+AS\s*\(", re.I)
FONCTIONS = ["kpis_jour", "ca_par_jour", "ca_par_mois", "ca_par_semaine", "top_medicaments", "medicaments_jamais_vendus",
             "ventes_par_personnel", "clients_fideles", "performance_fournisseurs", "ventes_ordonnance_libre",
             "marge_par_medicament", "couverture_stock", "classement_categories", "affluence_par_heure",
             "alertes_rupture", "alertes_peremption"]


class Capteur:
    def __init__(self):
        self.requetes = []

    def execute(self, sql, params=()):
        self.requetes.append((sql, params))

    def fetchall(self):
        return []

    def fetchone(self):
        return {}


class TestRequetesPortables(unittest.TestCase):
    def capturer(self, nom):
        capteur = Capteur()

        @contextmanager
        def faux_lecture():
            yield capteur

        ancien = st.lecture
        st.lecture = faux_lecture
        try:
            getattr(st, nom)(PH)
        finally:
            st.lecture = ancien
        return capteur.requetes

    def test_aucune_requete_ne_depend_de_la_version_du_serveur(self):
        for nom in FONCTIONS:
            for sql, params in self.capturer(nom):
                self.assertIsNone(INTERDIT.search(sql), f"{nom} : fonction non portable")

    def test_signes_pourcent_et_parametres(self):
        for nom in FONCTIONS:
            for sql, params in self.capturer(nom):
                self.assertEqual(sql.count("%"), sql.count("%s"), f"{nom} : % non échappé")
                self.assertEqual(sql.count("%s"), len(params or ()), f"{nom} : nombre de paramètres")

    def test_le_script_sql_05_est_portable(self):
        chemin = os.path.join(os.path.dirname(__file__), "..", "sql", "05_requetes_analyse_pharmacie.sql")
        with open(chemin, encoding="utf-8") as f:
            code = [l for l in f.read().split("\n") if not l.strip().startswith("--")]
        for ligne in code:
            self.assertIsNone(INTERDIT.search(ligne), ligne)


if __name__ == "__main__":
    unittest.main()
