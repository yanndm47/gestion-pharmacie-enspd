import unittest
from datetime import date, timedelta
from decimal import Decimal

from core.formatting import parse_decimal
from core.stock_rules import etat_stock, niveau_peremption

AUJ = date(2026, 10, 12)


class TestStockRules(unittest.TestCase):
    def test_niveaux_de_peremption(self):
        j = lambda n: AUJ + timedelta(days=n)
        self.assertEqual(niveau_peremption(j(-5), AUJ, 90), "perime")
        self.assertEqual(niveau_peremption(j(0), AUJ, 90), "urgent")
        self.assertEqual(niveau_peremption(j(30), AUJ, 90), "urgent")
        self.assertEqual(niveau_peremption(j(31), AUJ, 90), "a_surveiller")
        self.assertEqual(niveau_peremption(j(45), AUJ, 90), "a_surveiller")
        self.assertEqual(niveau_peremption(j(90), AUJ, 90), "a_surveiller")
        self.assertEqual(niveau_peremption(j(91), AUJ, 90), "ok")

    def test_etat_stock(self):
        self.assertEqual(etat_stock(0, 8), "Rupture")
        self.assertEqual(etat_stock(5, 8), "Sous le seuil")
        self.assertEqual(etat_stock(8, 8), "OK")
        self.assertEqual(etat_stock(100, 20), "OK")
        self.assertEqual(etat_stock(100, 20, actif=False), "Désactivé")

    def test_parse_decimal(self):
        self.assertEqual(parse_decimal("1 500"), Decimal("1500"))
        self.assertEqual(parse_decimal("1500,50"), Decimal("1500.50"))
        self.assertEqual(parse_decimal("2.5"), Decimal("2.5"))
        for mauvais in ("", "abc", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                parse_decimal(mauvais)


if __name__ == "__main__":
    unittest.main()
