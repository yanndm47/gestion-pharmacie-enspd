import unittest
from datetime import date
from decimal import Decimal

from core.formatting import fmt_date, fmt_montant, parse_date


class TestFormatting(unittest.TestCase):
    def test_montants(self):
        self.assertEqual(fmt_montant(12000), "12 000")
        self.assertEqual(fmt_montant(Decimal("100100.00")), "100 100")
        self.assertEqual(fmt_montant(Decimal("39666.67")), "39 666,67")
        self.assertEqual(fmt_montant(0), "0")
        self.assertEqual(fmt_montant(None), "")

    def test_dates(self):
        self.assertEqual(fmt_date(date(2026, 10, 12)), "12/10/2026")
        self.assertEqual(parse_date("12/10/2026"), date(2026, 10, 12))
        self.assertEqual(parse_date("2026-10-12"), date(2026, 10, 12))
        with self.assertRaises(ValueError):
            parse_date("31/02/2026")
        with self.assertRaises(ValueError):
            parse_date("")


if __name__ == "__main__":
    unittest.main()
