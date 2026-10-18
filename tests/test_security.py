import hashlib
import unittest

from core.security import hash_password, needs_rehash, verify_password


class TestSecurity(unittest.TestCase):
    def test_hash_puis_verification(self):
        h = hash_password("Pharma2026!", iterations=1000)
        self.assertTrue(verify_password("Pharma2026!", h))
        self.assertFalse(verify_password("autre", h))

    def test_deux_hachages_du_meme_mot_de_passe_different(self):
        self.assertNotEqual(hash_password("x", 1000), hash_password("x", 1000))

    def test_ancien_format_sha256_du_jeu_de_test(self):
        # SHA2('Pharma2026!', 256) tel que produit par MySQL (script 03)
        ancien = hashlib.sha256("Pharma2026!".encode("utf-8")).hexdigest()
        self.assertTrue(verify_password("Pharma2026!", ancien))
        self.assertTrue(verify_password("Pharma2026!", ancien.upper()))
        self.assertFalse(verify_password("mauvais", ancien))
        self.assertTrue(needs_rehash(ancien))

    def test_hachage_faible_ou_corrompu(self):
        self.assertTrue(needs_rehash(hash_password("x", iterations=1000)))
        self.assertFalse(verify_password("x", ""))
        self.assertFalse(verify_password("x", "pbkdf2_sha256$abc"))
        self.assertFalse(verify_password("x", "n'importe quoi"))

    def test_hachage_courant_pas_a_convertir(self):
        self.assertFalse(needs_rehash(hash_password("x")))


if __name__ == "__main__":
    unittest.main()
