"""Teste la logique de creer_ordonnance SANS base de données (curseur simulé)."""
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
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

import config  # noqa: E402
from core.errors import BusinessError, PermissionDenied  # noqa: E402
from services import ordonnance_service  # noqa: E402
from services.ordonnance_service import LigneOrdonnance, creer_ordonnance, lister_ordonnances  # noqa: E402

PHARMACIEN = SimpleNamespace(id_personnel=1, role="pharmacien")
CAISSIER = SimpleNamespace(id_personnel=2, role="caissier")
AUJ = date.today()


class FauxCurseur:
    def __init__(self, ids_actifs=(3, 8)):
        self.ids_actifs = set(ids_actifs)
        self.requetes = []
        self.lastrowid = None
        self._res = []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.requetes.append((s, params))
        if s.startswith("SELECT id_medicament FROM medicament"):
            self._res = [{"id_medicament": i} for i in params if i in self.ids_actifs]
        elif s.startswith("INSERT INTO ordonnance"):
            self.lastrowid = 7

    def fetchall(self):
        return list(self._res)

    def inserts(self, table):
        return [p for s, p in self.requetes if s.startswith(f"INSERT INTO {table}")]


def lancer(curseur, *args, **kw):
    @contextmanager
    def fausse_transaction():
        yield curseur

    ancien = ordonnance_service.transaction
    ordonnance_service.transaction = fausse_transaction
    try:
        return creer_ordonnance(*args, **kw)
    finally:
        ordonnance_service.transaction = ancien


L1 = LigneOrdonnance(3, 21, "1 gélule 3 fois par jour", 7)
L2 = LigneOrdonnance(8, 14, "1 gélule le matin", None)


class TestCreerOrdonnance(unittest.TestCase):
    def test_creation_complete(self):
        c = FauxCurseur()
        numero = lancer(c, PHARMACIEN, 1, " Dr Mballa ", "  ", AUJ - timedelta(days=2), [L1, L2])
        self.assertEqual(numero, 7)
        (ordo,) = c.inserts("ordonnance")
        self.assertEqual(ordo[0:3], (1, 1, "Dr Mballa"))
        self.assertIsNone(ordo[3])                                   # n° d'ordre vide -> NULL
        self.assertEqual(ordo[5] - ordo[4], timedelta(days=config.VALIDITE_ORDONNANCE_JOURS))
        self.assertEqual(config.VALIDITE_ORDONNANCE_JOURS, 14)
        lignes = c.inserts("ligne_ordonnance")
        self.assertEqual([l[1:3] for l in lignes], [(3, 21), (8, 14)])
        self.assertEqual(lignes[1][4], None)

    def test_reservee_au_pharmacien(self):
        c = FauxCurseur()
        with self.assertRaises(PermissionDenied):
            lancer(c, CAISSIER, 1, "Dr X", "", AUJ, [L1])
        self.assertEqual(c.requetes, [])

    def test_champs_obligatoires(self):
        c = FauxCurseur()
        for args in [(0, "Dr X", [L1]), (1, "  ", [L1]), (1, "Dr X", [])]:
            with self.assertRaises(BusinessError):
                lancer(c, PHARMACIEN, args[0], args[1], "", AUJ, args[2])

    def test_medicament_en_double(self):
        c = FauxCurseur()
        with self.assertRaises(BusinessError) as ctx:
            lancer(c, PHARMACIEN, 1, "Dr X", "", AUJ, [L1, LigneOrdonnance(3, 5, "x")])
        self.assertIn("RG-28", str(ctx.exception))

    def test_lignes_invalides(self):
        c = FauxCurseur()
        for ligne in (LigneOrdonnance(3, 0, "x"), LigneOrdonnance(3, 1, "  "),
                      LigneOrdonnance(3, 1, "x", 0)):
            with self.assertRaises(BusinessError):
                lancer(c, PHARMACIEN, 1, "Dr X", "", AUJ, [ligne])

    def test_date_dans_le_futur(self):
        with self.assertRaises(BusinessError):
            lancer(FauxCurseur(), PHARMACIEN, 1, "Dr X", "", AUJ + timedelta(days=1), [L1])

    def test_ordonnance_deja_expiree(self):
        c = FauxCurseur()
        with self.assertRaises(BusinessError) as ctx:
            lancer(c, PHARMACIEN, 1, "Dr X", "", AUJ - timedelta(days=15), [L1])
        self.assertIn("expirée", str(ctx.exception))
        self.assertEqual(c.requetes, [])

    def test_derniere_date_valable(self):
        # prescrite il y a 14 jours : valable jusqu'à aujourd'hui inclus
        lancer(FauxCurseur(), PHARMACIEN, 1, "Dr X", "", AUJ - timedelta(days=14), [L1])

    def test_medicament_desactive(self):
        c = FauxCurseur(ids_actifs=(3,))
        with self.assertRaises(BusinessError):
            lancer(c, PHARMACIEN, 1, "Dr X", "", AUJ, [L1, L2])
        self.assertEqual(c.inserts("ordonnance"), [])


class TestListe(unittest.TestCase):
    def test_statut_invalide(self):
        with self.assertRaises(BusinessError):
            lister_ordonnances(PHARMACIEN, statut="nimporte")

    def test_caissier_refuse(self):
        with self.assertRaises(PermissionDenied):
            lister_ordonnances(CAISSIER)


if __name__ == "__main__":
    unittest.main()
