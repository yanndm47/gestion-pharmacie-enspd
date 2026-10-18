import unittest
from types import SimpleNamespace

from core.errors import PermissionDenied
from core.permissions import PERMISSIONS, can, require


class TestPermissions(unittest.TestCase):
    def test_caissier_droits_reduits(self):
        self.assertTrue(can("caissier", "vendre_libre"))
        for interdit in ("vendre_ordonnance", "annuler_vente", "gerer_catalogue",
                         "gerer_lots", "gerer_fournisseurs", "gerer_comptes",
                         "stats_completes", "gerer_ordonnances"):
            self.assertFalse(can("caissier", interdit), interdit)

    def test_caissier_a_le_moins_de_droits(self):
        n_caisse = len(PERMISSIONS["caissier"])
        self.assertLess(n_caisse, len(PERMISSIONS["pharmacien"]))
        self.assertLess(n_caisse, len(PERMISSIONS["administrateur"]) + 1)

    def test_pharmacien(self):
        for p in ("vendre_libre", "vendre_ordonnance", "annuler_vente",
                  "gerer_ordonnances", "gerer_lots", "stats_completes"):
            self.assertTrue(can("pharmacien", p), p)
        self.assertFalse(can("pharmacien", "gerer_comptes"))
        self.assertFalse(can("pharmacien", "sauvegarde"))

    def test_administrateur_ne_vend_pas(self):
        self.assertFalse(can("administrateur", "vendre_libre"))
        self.assertTrue(can("administrateur", "gerer_comptes"))
        self.assertTrue(can("administrateur", "sauvegarde"))

    def test_role_inconnu(self):
        self.assertFalse(can("inconnu", "vendre_libre"))

    def test_require(self):
        caissier = SimpleNamespace(role="caissier")
        require(caissier, "vendre_libre")
        with self.assertRaises(PermissionDenied):
            require(caissier, "annuler_vente")
        with self.assertRaises(PermissionDenied):
            require(None, "vendre_libre")


if __name__ == "__main__":
    unittest.main()
