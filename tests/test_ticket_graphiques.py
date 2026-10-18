import sys
import types
import unittest
from contextlib import contextmanager
from datetime import date, datetime, timedelta
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

from core.chart_layout import calculer_barres  # noqa: E402
from core.errors import BusinessError, PermissionDenied  # noqa: E402
from core.formatting import fmt_valeur  # noqa: E402
from core.ticket import formater_ticket  # noqa: E402
from services import vente_service  # noqa: E402

LIGNES = [
    {"nom_commercial": "Doliprane", "quantite": 2, "prix_unitaire": Decimal("1500"), "sous_total": Decimal("3000")},
    {"nom_commercial": "Un médicament au nom vraiment très très long pour tester", "quantite": 1,
     "prix_unitaire": Decimal("100100"), "sous_total": Decimal("100100")},
]
QUAND = datetime(2026, 10, 12, 14, 32)


class TestTicket(unittest.TestCase):
    def test_largeur_et_contenu(self):
        t = formater_ticket("Pharmacie du Centre", 123, QUAND, "Claire Dupont", "Jean Fotso",
                            LIGNES, Decimal("103100"), "Carte", largeur=42)
        for ligne in t.split("\n"):
            self.assertLessEqual(len(ligne), 42, ligne)
        self.assertIn("PHARMACIE DU CENTRE", t)
        self.assertIn("Ticket n° 123", t)
        self.assertIn("12/10/2026 14:32", t)
        self.assertIn("Client  : Jean Fotso", t)
        self.assertRegex(t, r"TOTAL\s+103 100")
        self.assertIn("2 x 1 500", t)
        self.assertNotIn("ANNULÉE", t)

    def test_vente_anonyme_et_annulee(self):
        t = formater_ticket("P", 1, QUAND, "V", None, LIGNES[:1], Decimal("3000"), "Espèces", "annulee")
        self.assertNotIn("Client", t)
        self.assertIn("VENTE ANNULÉE", t)


class TestGraphiques(unittest.TestCase):
    def test_proportions_et_bornes(self):
        barres, maxi = calculer_barres([10, 20, 5], 600, 300)
        self.assertEqual(maxi, 20)
        hauteurs = [b[3] - b[1] for b in barres]
        self.assertAlmostEqual(hauteurs[0] * 2, hauteurs[1])
        self.assertAlmostEqual(hauteurs[2] * 4, hauteurs[1])
        for x0, y0, x1, y1 in barres:
            self.assertGreaterEqual(x0, 0); self.assertLessEqual(x1, 600)
            self.assertGreaterEqual(y0, 0); self.assertLessEqual(y1, 300)
        self.assertLess(barres[0][2], barres[1][0])        # les barres ne se chevauchent pas

    def test_cas_limites(self):
        self.assertEqual(calculer_barres([], 600, 300), ([], 0.0))
        barres, maxi = calculer_barres([0, 0], 600, 300)
        self.assertEqual(maxi, 0)
        self.assertTrue(all(b[1] == b[3] for b in barres))   # barres de hauteur nulle
        barres, _ = calculer_barres([-5, 10], 600, 300)
        self.assertEqual(barres[0][1], barres[0][3])          # négatif ramené à 0


class TestFormats(unittest.TestCase):
    def test_fmt_valeur(self):
        self.assertEqual(fmt_valeur(Decimal("37.14"), "pct"), "37,1 %")
        self.assertEqual(fmt_valeur(Decimal("1470.0"), "decimal"), "1470,0")
        self.assertEqual(fmt_valeur(Decimal("119000"), "montant"), "119 000")
        self.assertEqual(fmt_valeur(date(2026, 10, 12), "date"), "12/10/2026")
        self.assertEqual(fmt_valeur(QUAND, "datetime"), "12/10/2026 14:32")
        self.assertEqual(fmt_valeur(Decimal(3), "int"), "3")
        self.assertEqual(fmt_valeur(None, "montant"), "")
        self.assertEqual(fmt_valeur("abc"), "abc")


class FauxCurseur:
    def __init__(self, vente=None, lignes=()):
        self.vente, self.lignes = vente, list(lignes)
        self.requetes = []
        self._res = []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.requetes.append((s, params))
        if "FROM vente v JOIN personnel p" in s and "WHERE v.id_vente" in s:
            self._res = [self.vente] if self.vente else []
        elif "FROM ligne_vente lv" in s:
            self._res = self.lignes
        else:
            self._res = []

    def fetchone(self):
        return self._res[0] if self._res else None

    def fetchall(self):
        return list(self._res)


def avec_lecture(curseur, fonction, *a, **k):
    @contextmanager
    def fausse():
        yield curseur

    ancien = vente_service.lecture
    vente_service.lecture = fausse
    try:
        return fonction(*a, **k)
    finally:
        vente_service.lecture = ancien


PH = SimpleNamespace(id_personnel=1, role="pharmacien")
CAISSE = SimpleNamespace(id_personnel=2, role="caissier")
ADMIN = SimpleNamespace(id_personnel=3, role="administrateur")


def vente(jours_avant=0):
    return {"id_vente": 5, "date_vente": datetime.now() - timedelta(days=jours_avant), "total": Decimal("3000"),
            "statut": "validee", "mode_paiement": "carte", "id_ordonnance": None,
            "vendeur": "Claire Dupont", "client": None}


class TestVentesService(unittest.TestCase):
    def test_caissier_limite_a_aujourdhui(self):
        c = FauxCurseur()
        avec_lecture(c, vente_service.lister_ventes, CAISSE, jours=None)
        debut = c.requetes[0][1][0]
        self.assertEqual(debut.date(), date.today())          # malgré jours=None

    def test_pharmacien_periodes(self):
        c = FauxCurseur()
        avec_lecture(c, vente_service.lister_ventes, PH, jours=30)
        self.assertEqual(c.requetes[0][1][0].date(), date.today() - timedelta(days=30))
        c = FauxCurseur()
        avec_lecture(c, vente_service.lister_ventes, PH, jours=None, statut="annulee")
        self.assertEqual(c.requetes[0][1][0], "annulee")      # pas de filtre de date, statut seul

    def test_statut_invalide(self):
        with self.assertRaises(BusinessError):
            vente_service.lister_ventes(PH, statut="x")

    def test_detail_et_droits(self):
        c = FauxCurseur(vente(), LIGNES)
        d = avec_lecture(c, vente_service.detail_vente, PH, 5)
        self.assertEqual(len(d["lignes"]), 2)
        c = FauxCurseur(vente(jours_avant=3), LIGNES)
        with self.assertRaises(BusinessError):
            avec_lecture(c, vente_service.detail_vente, CAISSE, 5)
        c = FauxCurseur(vente(jours_avant=3), LIGNES)
        avec_lecture(c, vente_service.detail_vente, PH, 5)    # le pharmacien peut tout voir
        with self.assertRaises(BusinessError):
            avec_lecture(FauxCurseur(None), vente_service.detail_vente, PH, 99)

    def test_texte_ticket(self):
        c = FauxCurseur(vente(), LIGNES[:1])
        t = avec_lecture(c, vente_service.texte_ticket, PH, 5)
        self.assertIn("Ticket n° 5", t)
        self.assertIn("Carte", t)
        self.assertIn("Vendeur : Claire Dupont", t)

    def test_administrateur_voit_les_ventes_du_jour(self):
        avec_lecture(FauxCurseur(), vente_service.lister_ventes, ADMIN, jours=7)


if __name__ == "__main__":
    unittest.main()
