"""Comptes, mots de passe et fiches clients, SANS base (curseur simulé)."""
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

from core.errors import BusinessError, PermissionDenied  # noqa: E402
from core.security import hash_password, valider_mot_de_passe, verify_password  # noqa: E402
from services import auth_service, client_service, personnel_service  # noqa: E402

ADMIN = SimpleNamespace(id_personnel=3, role="administrateur")
PH = SimpleNamespace(id_personnel=1, role="pharmacien")
CAISSE = SimpleNamespace(id_personnel=2, role="caissier")


class FauxCurseur:
    def __init__(self, ancien=None, autres_admins=1, hash_stocke=None):
        self.ancien, self.autres_admins, self.hash_stocke = ancien, autres_admins, hash_stocke
        self.requetes = []
        self.lastrowid = 20
        self._res = []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.requetes.append((s, params))
        if s.startswith("SELECT role, actif FROM personnel"):
            self._res = [self.ancien] if self.ancien else []
        elif s.startswith("SELECT COUNT(*) AS n"):
            self._res = [{"n": self.autres_admins}]
        elif s.startswith("SELECT mot_de_passe_hash"):
            self._res = [{"mot_de_passe_hash": self.hash_stocke}] if self.hash_stocke else []

    def fetchone(self):
        return self._res[0] if self._res else None

    def ecritures(self):
        return [s for s, _ in self.requetes if s.split()[0] in ("INSERT", "UPDATE")]


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


class TestComptes(unittest.TestCase):
    def test_creation_hache_le_mot_de_passe(self):
        c = FauxCurseur()
        n = avec(personnel_service, c, personnel_service.creer_compte, ADMIN,
                 "Ngono", "Marie", " mngono ", "MotDePasse1", "caissier")
        self.assertEqual(n, 20)
        params = c.requetes[0][1]
        self.assertEqual(params[2], "mngono")
        self.assertNotIn("MotDePasse1", params)
        self.assertTrue(verify_password("MotDePasse1", params[3]))

    def test_refus_non_administrateur(self):
        for u in (PH, CAISSE):
            with self.assertRaises(PermissionDenied):
                avec(personnel_service, FauxCurseur(), personnel_service.creer_compte, u,
                     "N", "P", "l", "MotDePasse1", "caissier")

    def test_donnees_invalides(self):
        c = FauxCurseur()
        for args in [("", "P", "l", "MotDePasse1", "caissier"), ("N", "P", "", "MotDePasse1", "caissier"),
                     ("N", "P", "l", "court", "caissier"), ("N", "P", "l", "MotDePasse1", "chef")]:
            with self.assertRaises(BusinessError):
                avec(personnel_service, c, personnel_service.creer_compte, ADMIN, *args)
        self.assertEqual(c.requetes, [])

    def test_politique_mot_de_passe(self):
        valider_mot_de_passe("12345678")
        for mauvais in ("", "1234567", " 12345678"):
            with self.assertRaises(ValueError):
                valider_mot_de_passe(mauvais)

    def test_dernier_administrateur_protege(self):
        admin_actif = {"role": "administrateur", "actif": 1}
        seul = FauxCurseur(ancien=admin_actif, autres_admins=0)
        with self.assertRaises(BusinessError) as ctx:
            avec(personnel_service, seul, personnel_service.changer_statut_compte, ADMIN, 9, False)
        self.assertIn("au moins un administrateur", str(ctx.exception))
        with self.assertRaises(BusinessError):
            avec(personnel_service, FauxCurseur(ancien=admin_actif, autres_admins=0),
                 personnel_service.modifier_compte, ADMIN, 9, "N", "P", "caissier")
        avec(personnel_service, FauxCurseur(ancien=admin_actif, autres_admins=1),
             personnel_service.changer_statut_compte, ADMIN, 9, False)

    def test_pas_d_auto_desactivation_ni_changement_de_son_role(self):
        c = FauxCurseur(ancien={"role": "administrateur", "actif": 1})
        with self.assertRaises(BusinessError):
            avec(personnel_service, c, personnel_service.changer_statut_compte, ADMIN, 3, False)
        with self.assertRaises(BusinessError):
            avec(personnel_service, c, personnel_service.modifier_compte, ADMIN, 3, "N", "P", "caissier")
        self.assertEqual(c.ecritures(), [])

    def test_compte_inexistant(self):
        with self.assertRaises(BusinessError):
            avec(personnel_service, FauxCurseur(ancien=None), personnel_service.changer_statut_compte, ADMIN, 9, True)

    def test_reinitialisation(self):
        c = FauxCurseur()
        avec(personnel_service, c, personnel_service.reinitialiser_mot_de_passe, ADMIN, 2, "NouveauMdp1")
        self.assertTrue(verify_password("NouveauMdp1", c.requetes[0][1][0]))
        with self.assertRaises(BusinessError):
            avec(personnel_service, FauxCurseur(), personnel_service.reinitialiser_mot_de_passe, ADMIN, 2, "court")


class TestChangerMotDePasse(unittest.TestCase):
    def test_changement(self):
        c = FauxCurseur(hash_stocke=hash_password("Ancien123", iterations=1000))
        avec(auth_service, c, auth_service.changer_mot_de_passe, PH, "Ancien123", "Nouveau456")
        self.assertTrue(verify_password("Nouveau456", c.requetes[-1][1][0]))

    def test_ancien_incorrect_ou_nouveau_trop_court(self):
        c = FauxCurseur(hash_stocke=hash_password("Ancien123", iterations=1000))
        with self.assertRaises(BusinessError):
            avec(auth_service, c, auth_service.changer_mot_de_passe, PH, "faux", "Nouveau456")
        with self.assertRaises(BusinessError):
            avec(auth_service, c, auth_service.changer_mot_de_passe, PH, "Ancien123", "court")
        self.assertEqual(c.ecritures(), [])


class TestClients(unittest.TestCase):
    def test_creation_avec_champs_facultatifs_vides(self):
        c = FauxCurseur()
        avec(client_service, c, client_service.creer_client, CAISSE, " Fotso ", "Jean", "12/04/1985", "", " ", "")
        p = c.requetes[0][1]
        self.assertEqual(p[0:3], ("Fotso", "Jean", date(1985, 4, 12)))
        self.assertEqual(p[3:], (None, None, None))

    def test_validations(self):
        c = FauxCurseur()
        futur = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        for args in [("", "J", "12/04/1985"), ("F", "", "12/04/1985"), ("F", "J", "n'importe quoi"), ("F", "J", futur)]:
            with self.assertRaises(BusinessError):
                avec(client_service, c, client_service.modifier_client, PH, 1, *args)
        self.assertEqual(c.requetes, [])

    def test_historique_reserve_au_pharmacien(self):
        for fonction in (client_service.historique_achats, client_service.historique_ordonnances):
            with self.assertRaises(PermissionDenied):
                fonction(CAISSE, 1)

    def test_caissier_peut_modifier_une_fiche(self):
        c = FauxCurseur()
        avec(client_service, c, client_service.modifier_client, CAISSE, 4, "Fotso", "Jean", "12/04/1985", "690", "a@b.c", "Douala")
        self.assertEqual(c.requetes[0][1][-1], 4)


if __name__ == "__main__":
    unittest.main()
