import unittest
from datetime import date, timedelta

from core.allocation import Allocation, Lot, allouer_fefo
from core.errors import StockInsuffisant

AUJ = date(2026, 10, 12)


def lot(id_stock, qte, jours):
    return Lot(id_stock, qte, AUJ + timedelta(days=jours))


class TestAllocationFEFO(unittest.TestCase):
    def test_un_seul_lot(self):
        self.assertEqual(allouer_fefo([lot(1, 100, 300)], 2, AUJ), [Allocation(1, 2)])

    def test_prend_d_abord_le_lot_le_plus_proche_de_la_peremption(self):
        lots = [lot(1, 50, 400), lot(2, 50, 30), lot(3, 50, 200)]
        self.assertEqual(allouer_fefo(lots, 10, AUJ), [Allocation(2, 10)])

    def test_repartition_sur_plusieurs_lots(self):
        lots = [lot(1, 30, 400), lot(2, 20, 30)]
        self.assertEqual(
            allouer_fefo(lots, 35, AUJ), [Allocation(2, 20), Allocation(1, 15)]
        )

    def test_lot_perime_ignore(self):
        lots = [lot(1, 20, -5), lot(2, 40, 100)]
        self.assertEqual(allouer_fefo(lots, 5, AUJ), [Allocation(2, 5)])

    def test_lot_qui_perime_aujourd_hui_reste_vendable(self):
        # Le trigger SQL refuse seulement date_peremption < CURDATE()
        self.assertEqual(allouer_fefo([lot(1, 5, 0)], 5, AUJ), [Allocation(1, 5)])

    def test_lot_vide_ignore(self):
        lots = [lot(1, 0, 10), lot(2, 5, 100)]
        self.assertEqual(allouer_fefo(lots, 5, AUJ), [Allocation(2, 5)])

    def test_egalite_de_date_departagee_par_id(self):
        lots = [lot(7, 10, 50), lot(3, 10, 50)]
        self.assertEqual(allouer_fefo(lots, 4, AUJ), [Allocation(3, 4)])

    def test_stock_insuffisant(self):
        with self.assertRaises(StockInsuffisant) as ctx:
            allouer_fefo([lot(1, 10, 100), lot(2, 5, -1)], 11, AUJ)
        self.assertEqual(ctx.exception.disponible, 10)
        self.assertEqual(ctx.exception.demande, 11)

    def test_quantite_invalide(self):
        with self.assertRaises(ValueError):
            allouer_fefo([lot(1, 10, 100)], 0, AUJ)

    def test_quantite_exacte_du_stock(self):
        lots = [lot(1, 10, 100), lot(2, 5, 10)]
        res = allouer_fefo(lots, 15, AUJ)
        self.assertEqual(sum(a.quantite for a in res), 15)


if __name__ == "__main__":
    unittest.main()
