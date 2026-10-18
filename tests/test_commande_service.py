"""Logique de commande, réception et gestion du catalogue, SANS base (curseur simulé)."""
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal
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

from core.errors import BusinessError, PermissionDenied  # noqa: E402
from services import commande_service, stock_service  # noqa: E402
from services.commande_service import LigneCommande  # noqa: E402
from services.stock_service import MedicamentSaisie  # noqa: E402

PH = SimpleNamespace(id_personnel=1, role="pharmacien")
CAISSE = SimpleNamespace(id_personnel=2, role="caissier")
AUJ = date.today()


class FauxCurseur:
    def __init__(self, statut_commande="en_cours"):
        self.requetes = []
        self.lastrowid = 11
        self.statut = statut_commande
        self._res = []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.requetes.append((s, params))
        if s.startswith("SELECT statut FROM commande"):
            self._res = [{"statut": self.statut}] if self.statut else []

    def fetchone(self):
        return self._res[0] if self._res else None

    def inserts(self, table):
        return [p for s, p in self.requetes if s.startswith(f"INSERT INTO {table}")]


def avec(module, curseur, fonction, *args, **kw):
    @contextmanager
    def fausse():
        yield curseur

    ancien = module.transaction
    module.transaction = fausse
    try:
        return fonction(*args, **kw)
    finally:
        module.transaction = ancien


L1 = LigneCommande(1, 100, Decimal("900"))
L2 = LigneCommande(2, 50, None)


class TestCommande(unittest.TestCase):
    def test_creation(self):
        c = FauxCurseur()
        n = avec(commande_service, c, commande_service.creer_commande, PH, 3, AUJ + timedelta(days=2), [L1, L2])
        self.assertEqual(n, 11)
        self.assertEqual(c.inserts("commande")[0][0], 3)
        self.assertEqual([p[1:3] for p in c.inserts("ligne_commande")], [(1, 100), (2, 50)])

    def test_refus_caissier_et_donnees_invalides(self):
        c = FauxCurseur()
        with self.assertRaises(PermissionDenied):
            avec(commande_service, c, commande_service.creer_commande, CAISSE, 3, None, [L1])
        for args in [(0, None, [L1]), (3, None, []), (3, None, [L1, LigneCommande(1, 5)]),
                     (3, None, [LigneCommande(1, 0)]), (3, AUJ - timedelta(days=1), [L1]),
                     (3, None, [LigneCommande(1, 5, Decimal("-1"))])]:
            with self.assertRaises(BusinessError):
                avec(commande_service, c, commande_service.creer_commande, PH, *args)
        self.assertEqual(c.requetes, [])

    def test_annuler_seulement_si_en_cours(self):
        c = FauxCurseur("en_cours")
        avec(commande_service, c, commande_service.annuler_commande, PH, 5)
        self.assertTrue(any(s.startswith("UPDATE commande SET statut = 'annulee'") for s, _ in c.requetes))
        for statut in ("partielle", "recue", "annulee"):
            with self.assertRaises(BusinessError):
                avec(commande_service, FauxCurseur(statut), commande_service.annuler_commande, PH, 5)
        with self.assertRaises(BusinessError):
            avec(commande_service, FauxCurseur(None), commande_service.annuler_commande, PH, 5)

    def test_statut_invalide(self):
        with self.assertRaises(BusinessError):
            commande_service.lister_commandes(PH, statut="x")


class TestReception(unittest.TestCase):
    def _recevoir(self, c, **kw):
        base = dict(user=PH, id_commande=5, id_medicament=1, numero_lot="L1",
                    date_peremption=AUJ + timedelta(days=400), quantite=40, prix_achat=Decimal("900"))
        base.update(kw)
        user = base.pop("user")
        return avec(commande_service, c, commande_service.receptionner, user, **base)

    def test_reception_ok_quantite_initiale_egale_restante(self):
        c = FauxCurseur()
        self.assertEqual(self._recevoir(c), 11)
        (p,) = c.inserts("stock")
        self.assertEqual(p[0:3], (1, 5, "L1"))
        self.assertEqual(p[3], AUJ)
        self.assertEqual(p[5], p[6])          # quantité initiale = quantité restante

    def test_refus(self):
        c = FauxCurseur()
        with self.assertRaises(PermissionDenied):
            self._recevoir(c, user=CAISSE)
        for kw in [dict(numero_lot="  "), dict(quantite=0), dict(prix_achat=Decimal("-1")),
                   dict(date_peremption=AUJ), dict(date_peremption=AUJ - timedelta(days=1))]:
            with self.assertRaises(BusinessError):
                self._recevoir(c, **kw)
        self.assertEqual(c.requetes, [])


class TestCatalogue(unittest.TestCase):
    saisie = MedicamentSaisie("Doliprane", "paracétamol", "comprimé", "500 mg", "", Decimal("1500"), False, 20)

    def test_creation_et_modification(self):
        c = FauxCurseur()
        self.assertEqual(avec(stock_service, c, stock_service.creer_medicament, PH, self.saisie), 11)
        self.assertIsNone(c.inserts("medicament")[0][4])        # catégorie vide -> NULL
        self.assertEqual(c.inserts("medicament")[0][6], 0)
        avec(stock_service, c, stock_service.modifier_medicament, PH, 4, self.saisie)
        self.assertEqual(c.requetes[-1][1][-1], 4)

    def test_validation(self):
        c = FauxCurseur()
        with self.assertRaises(PermissionDenied):
            avec(stock_service, c, stock_service.creer_medicament, CAISSE, self.saisie)
        mauvaises = [MedicamentSaisie("", "d", "f", "x", "", Decimal("1"), False, 1),
                     MedicamentSaisie("n", "d", "f", "x", "", Decimal("0"), False, 1),
                     MedicamentSaisie("n", "d", "f", "x", "", Decimal("5"), False, -1)]
        for m in mauvaises:
            with self.assertRaises(BusinessError):
                avec(stock_service, c, stock_service.creer_medicament, PH, m)
        self.assertEqual(c.requetes, [])

    def test_statut_lot_invalide(self):
        with self.assertRaises(BusinessError):
            stock_service.lister_lots(PH, statut="x")


if __name__ == "__main__":
    unittest.main()
