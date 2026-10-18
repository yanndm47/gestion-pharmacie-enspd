"""Teste la logique de creer_vente SANS base de données.

Le module mysql.connector est remplacé par un faux, et la transaction par un
curseur simulé qui enregistre les requêtes. Cela vérifie la logique Python
(FEFO, droits, fusion du panier, ordre des écritures). Les règles protégées par
les triggers sont testées avec le script SQL 04.
"""
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

# --- faux mysql.connector (installé uniquement si le vrai est absent) -------
try:
    import mysql.connector  # noqa: F401
except ImportError:
    faux = types.ModuleType("mysql.connector")

    class _Error(Exception):
        pass

    faux.Error = _Error
    faux.connect = lambda **kw: None
    pkg = types.ModuleType("mysql")
    pkg.connector = faux
    sys.modules["mysql"] = pkg
    sys.modules["mysql.connector"] = faux

from core.errors import BusinessError, PermissionDenied  # noqa: E402
from services import vente_service  # noqa: E402
from services.vente_service import LigneDemandee, creer_vente  # noqa: E402

DEMAIN = date.today() + timedelta(days=1)


class FauxCurseur:
    def __init__(self, medicaments, lots_par_medicament, total=Decimal("12000")):
        self.medicaments = medicaments
        self.lots = lots_par_medicament
        self.total = total
        self.requetes = []
        self.lastrowid = None
        self._resultat = []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.requetes.append((s, params))
        if "FROM medicament WHERE id_medicament IN" in s:
            self._resultat = [self.medicaments[i] for i in params if i in self.medicaments]
        elif s.startswith("INSERT INTO vente"):
            self.lastrowid = 42
        elif "FROM stock" in s and "FOR UPDATE" in s:
            self._resultat = self.lots.get(params[0], [])
        elif s.startswith("SELECT total FROM vente"):
            self._resultat = [{"total": self.total}]
        else:
            self._resultat = []

    def fetchall(self):
        return list(self._resultat)

    def fetchone(self):
        return self._resultat[0] if self._resultat else None

    def lignes_vente(self):
        return [p for s, p in self.requetes if s.startswith("INSERT INTO ligne_vente")]

    def a_insere_vente(self):
        return any(s.startswith("INSERT INTO vente") for s, _ in self.requetes)


def med(i, nom, prix, ordo=0, actif=1):
    return {"id_medicament": i, "nom_commercial": nom, "prix_vente": Decimal(prix),
            "ordonnance_obligatoire": ordo, "actif": actif}


def lot(id_stock, qte, jours):
    return {"id_stock": id_stock, "quantite_restante": qte,
            "date_peremption": date.today() + timedelta(days=jours)}


PHARMACIEN = SimpleNamespace(id_personnel=1, role="pharmacien")
CAISSIER = SimpleNamespace(id_personnel=2, role="caissier")


class TestCreerVente(unittest.TestCase):
    def _lancer(self, curseur, *args, **kw):
        @contextmanager
        def fausse_transaction():
            yield curseur

        ancien = vente_service.transaction
        vente_service.transaction = fausse_transaction
        try:
            return creer_vente(*args, **kw)
        finally:
            vente_service.transaction = ancien

    def test_vente_simple(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500")}, {1: [lot(10, 100, 300)]})
        res = self._lancer(c, CAISSIER, [LigneDemandee(1, 2)])
        self.assertEqual(res.id_vente, 42)
        self.assertEqual(res.total, Decimal("12000"))
        self.assertEqual(c.lignes_vente(), [(42, 10, 2, Decimal("1500"))])

    def test_repartition_fefo_sur_deux_lots(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500")},
                        {1: [lot(10, 30, 400), lot(11, 20, 30)]})
        res = self._lancer(c, CAISSIER, [LigneDemandee(1, 35)])
        self.assertEqual(res.nb_lignes, 2)
        self.assertEqual(c.lignes_vente(),
                         [(42, 11, 20, Decimal("1500")), (42, 10, 15, Decimal("1500"))])

    def test_lignes_du_meme_medicament_fusionnees(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500")}, {1: [lot(10, 100, 300)]})
        self._lancer(c, CAISSIER, [LigneDemandee(1, 2), LigneDemandee(1, 3)])
        self.assertEqual(c.lignes_vente(), [(42, 10, 5, Decimal("1500"))])

    def test_stock_insuffisant_message_avec_nom_du_medicament(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500")}, {1: [lot(10, 3, 300)]})
        with self.assertRaises(BusinessError) as ctx:
            self._lancer(c, CAISSIER, [LigneDemandee(1, 5)])
        self.assertIn("Doliprane", str(ctx.exception))
        self.assertIn("3 disponible", str(ctx.exception))

    def test_ordonnance_obligatoire_sans_ordonnance(self):
        c = FauxCurseur({3: med(3, "Amoxicilline", "3500", ordo=1)}, {3: [lot(20, 40, 300)]})
        with self.assertRaises(BusinessError) as ctx:
            self._lancer(c, PHARMACIEN, [LigneDemandee(3, 1)])
        self.assertIn("ordonnance", str(ctx.exception))
        self.assertFalse(c.a_insere_vente())   # rien n'est écrit avant le refus

    def test_vente_sur_ordonnance_reservee_au_pharmacien(self):
        c = FauxCurseur({3: med(3, "Amoxicilline", "3500", ordo=1)}, {3: [lot(20, 40, 300)]})
        with self.assertRaises(PermissionDenied):
            self._lancer(c, CAISSIER, [LigneDemandee(3, 1)], id_client=1, id_ordonnance=5)
        self.assertEqual(c.requetes, [])

    def test_pharmacien_vend_sur_ordonnance(self):
        c = FauxCurseur({3: med(3, "Amoxicilline", "3500", ordo=1)}, {3: [lot(20, 40, 300)]})
        res = self._lancer(c, PHARMACIEN, [LigneDemandee(3, 21)], id_client=1,
                           id_ordonnance=5, mode_paiement="carte")
        self.assertEqual(res.id_vente, 42)
        insert_vente = [p for s, p in c.requetes if s.startswith("INSERT INTO vente")][0]
        self.assertEqual(insert_vente, (1, 1, 5, "carte"))

    def test_panier_vide_et_mode_invalide(self):
        c = FauxCurseur({}, {})
        with self.assertRaises(BusinessError):
            self._lancer(c, CAISSIER, [])
        with self.assertRaises(BusinessError):
            self._lancer(c, CAISSIER, [LigneDemandee(1, 1)], mode_paiement="cheque")

    def test_quantite_invalide(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500")}, {1: [lot(10, 100, 300)]})
        with self.assertRaises(BusinessError):
            self._lancer(c, CAISSIER, [LigneDemandee(1, 0)])

    def test_medicament_desactive(self):
        c = FauxCurseur({1: med(1, "Doliprane", "1500", actif=0)}, {1: [lot(10, 100, 300)]})
        with self.assertRaises(BusinessError):
            self._lancer(c, CAISSIER, [LigneDemandee(1, 1)])

    def test_administrateur_ne_peut_pas_vendre(self):
        admin = SimpleNamespace(id_personnel=3, role="administrateur")
        c = FauxCurseur({1: med(1, "Doliprane", "1500")}, {1: [lot(10, 100, 300)]})
        with self.assertRaises(PermissionDenied):
            self._lancer(c, admin, [LigneDemandee(1, 1)])


if __name__ == "__main__":
    unittest.main()
