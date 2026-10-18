"""Vérifie que l'installeur découpe correctement les 6 scripts SQL (sans base de données)."""
import os
import re
import sys
import unittest

RACINE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RACINE, "tools"))
import installer_base as ib  # noqa: E402

SQL = os.path.join(RACINE, "sql")


def lire(nom):
    with open(os.path.join(SQL, nom), encoding="utf-8") as f:
        return list(ib.decouper(f.read()))


def hors_textes(instruction):
    """Instruction sans commentaires de ligne ni textes entre apostrophes."""
    lignes = [ib.sans_commentaire(l) for l in instruction.splitlines() if not l.strip().startswith("--")]
    return re.sub(r"'(?:[^']|'')*'", "''", "\n".join(lignes))


class TestDecoupage(unittest.TestCase):
    def test_comptes_scripts_01_et_02(self):
        s1 = lire("01_schema_pharmacie.sql")
        self.assertEqual(len(s1), 3 + 11)                                   # DROP, CREATE, USE + 11 tables
        self.assertEqual(sum(1 for s in s1 if s.startswith("CREATE TABLE")), 11)
        s2 = lire("02_regles_triggers_pharmacie.sql")
        self.assertEqual(sum(1 for s in s2 if s.startswith("CREATE PROCEDURE")), 3)
        self.assertEqual(sum(1 for s in s2 if s.startswith("CREATE TRIGGER")), 13)
        self.assertEqual(sum(1 for s in s2 if s.startswith("CREATE VIEW")), 4)
        self.assertEqual(len(s2), 1 + 3 + 13 + 4)                           # USE + 3 procédures + 13 triggers + 4 vues

    def test_chaque_routine_est_une_seule_instruction_complete(self):
        for s in lire("02_regles_triggers_pharmacie.sql"):
            if s.startswith(("CREATE PROCEDURE", "CREATE TRIGGER")):
                corps = hors_textes(s)
                self.assertTrue(corps.rstrip().upper().endswith("END"), s[:60])
                self.assertGreaterEqual(corps.count(";"), 1)                  # le corps garde ses points-virgules
                self.assertEqual(len(re.findall(r"\bBEGIN\b", corps)), 1, s[:60])
                self.assertTrue(re.search(r"\bEND;\s*\Z", s + ";") and corps.rstrip().endswith("END"), s[:60])
                if s.startswith("CREATE PROCEDURE sp_maj_statut"):                # le CASE ... END ne doit pas couper la routine
                    self.assertRegex(s, r"WHERE id_(ordonnance|commande) = p_id_\w+\s+AND statut <> '\w+';\s*END$")

    def test_instructions_simples_sans_point_virgule_residuel(self):
        for nom in ("01_schema_pharmacie.sql", "03_donnees_test_pharmacie.sql", "04_tests_verification_pharmacie.sql",
                    "05_requetes_analyse_pharmacie.sql", "06_donnees_enrichies_pharmacie.sql"):
            for s in lire(nom):
                self.assertNotIn(";", hors_textes(s), f"{nom} : {s[:70]!r}")

    def test_script_06_contient_toutes_ses_instructions(self):
        s6 = lire("06_donnees_enrichies_pharmacie.sql")
        self.assertGreater(len(s6), 900)
        self.assertEqual(s6[1], "START TRANSACTION")
        self.assertIn("COMMIT", s6)
        self.assertEqual(sum(1 for s in s6 if s.startswith("INSERT INTO vente ")), 123)

    def test_delimiter_et_commentaires(self):
        texte = "DELIMITER $$\nCREATE TRIGGER t BEFORE INSERT ON x FOR EACH ROW\nBEGIN\n  SET NEW.a = 1; -- ok\nEND$$\nDELIMITER ;\nSELECT 'a--b'; -- fin\n"
        self.assertEqual(list(ib.decouper(texte)),
                         ["CREATE TRIGGER t BEFORE INSERT ON x FOR EACH ROW\nBEGIN\n  SET NEW.a = 1; -- ok\nEND", "SELECT 'a--b'"])

    def test_script_tronque_detecte(self):
        with self.assertRaises(ValueError):
            list(ib.decouper("SELECT 1;\nINSERT INTO t VALUES (1"))


if __name__ == "__main__":
    unittest.main()
