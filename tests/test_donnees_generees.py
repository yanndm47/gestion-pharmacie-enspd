"""Vérifie, de façon INDÉPENDANTE du générateur, que le SQL du script 06 respecte les règles
de gestion que les triggers appliqueront (script 02). Un petit émulateur rejoue chaque instruction
et lève une erreur dès qu'un trigger SQL refuserait l'écriture."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict

RACINE = os.path.join(os.path.dirname(__file__), "..")
EXISTANTS = {  # nom -> (prix, ordonnance obligatoire, seuil) : les 10 médicaments du script 03
    "Doliprane": (1500, 0, 20), "Efferalgan": (2000, 0, 15), "Amoxicilline Biogaran": (3500, 1, 10),
    "Augmentin": (6500, 1, 10), "Ventoline": (4200, 1, 5), "Spasfon": (2500, 0, 10), "Smecta": (3000, 0, 10),
    "Oméprazole Arrow": (3800, 1, 10), "Vitamine C Upsa": (2200, 0, 10), "Loratadine Mylan": (2800, 0, 8),
}
ROLES = {"@p_ph1": "pharmacien", "@p_ph2": "pharmacien", "@p_ca1": "caissier", "@p_ca2": "caissier"}


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def emuler(chemin):
    """Rejoue le script et retourne l'état final. Lève AssertionError si un trigger refuserait."""
    v = dict(ROLES)               # variables SQL -> objets
    pending = None
    lots_noms = set()
    lots, commandes, ordos, ventes, meds = [], [], [], [], {}

    def statut_ordo(o):
        if all(o.livre[m] >= q for m, q in o.lignes.items()) and o.lignes:
            return "soldee"
        return "partielle" if any(o.livre[m] > 0 for m in o.lignes) else "en_attente"

    with open(chemin, encoding="utf-8") as fichier:
        contenu = fichier.read()
    for ligne in contenu.split("\n"):
        ligne = ligne.strip()
        if not ligne or ligne.startswith("--"):
            continue
        m = re.match(r"SET (@\w+) := LAST_INSERT_ID\(\);", ligne)
        if m:
            v[m.group(1)] = pending
            continue
        m = re.match(r"SET (@m\d+) := \(SELECT id_medicament FROM medicament WHERE nom_commercial = '([^']+)'", ligne)
        if m:
            prix, ordo, seuil = EXISTANTS[m.group(2)]
            v[m.group(1)] = meds[m.group(1)] = Obj(prix=prix, ordo=ordo, seuil=seuil, lots=[])
            continue
        if ligne.startswith("SET "):
            v[ligne.split()[1]] = Obj(client=None)           # fournisseurs, clients existants
            continue
        m = re.match(r"INSERT INTO medicament .*VALUES \('[^']+', '[^']+', '[^']+', '[^']+', '[^']+', (\d+), (\d), (\d+)\);", ligne)
        if m:
            pending = Obj(prix=int(m.group(1)), ordo=int(m.group(2)), seuil=int(m.group(3)), lots=[])
            meds[f"new{len(meds)}"] = pending
            continue
        m = re.match(r"INSERT INTO commande .*VALUES \((@f\d), (@p_\w+),", ligne)
        if m:
            assert ROLES[m.group(2)] == "pharmacien", "commande passée par un non-pharmacien"
            pending = Obj(lignes={}, annulee=False, lots=[])
            commandes.append(pending)
            continue
        m = re.match(r"INSERT INTO ligne_commande .*VALUES \((@co\d+), (@m\d+), (\d+), (\d+)\);", ligne)
        if m:
            co = v[m.group(1)]
            assert m.group(2) not in co.lignes, "médicament en double dans une commande"
            co.lignes[m.group(2)] = int(m.group(3))
            continue
        m = re.match(r"UPDATE commande SET statut = 'annulee' WHERE id_commande = (@co\d+);", ligne)
        if m:
            v[m.group(1)].annulee = True
            continue
        m = re.match(r"INSERT INTO stock .*VALUES \((@m\d+), (@co\d+), '([^']+)', DATE_SUB\(CURDATE\(\), INTERVAL (\d+) DAY\), "
                     r"DATE_ADD\(CURDATE\(\), INTERVAL (\d+) DAY\), (\d+), (\d+), (\d+)\);", ligne)
        if m:
            med, co, nom = v[m.group(1)], v[m.group(2)], m.group(3)
            assert m.group(1) in co.lignes, "lot qui ne figure pas dans la commande (RG-56)"
            assert not co.annulee, "réception sur commande annulée (RG-59)"
            assert int(m.group(5)) > 0, "lot déjà périmé à la réception (RG-13)"
            assert m.group(6) == m.group(7), "quantité restante ≠ initiale à la réception"
            assert (m.group(1), nom) not in lots_noms, "numéro de lot en double (RG-12)"
            lots_noms.add((m.group(1), nom))
            pending = Obj(med=med, med_var=m.group(1), reste=int(m.group(6)), qte_init=int(m.group(6)), statut="disponible",
                          reception=int(m.group(4)), co=co)
            lots.append(pending)
            co.lots.append(pending)
            continue
        m = re.match(r"UPDATE stock SET date_peremption = DATE_SUB\(CURDATE\(\), INTERVAL (\d+) DAY\), statut = 'perime' WHERE id_stock = (@l\d+);", ligne)
        if m:
            lot = v[m.group(2)]
            assert lot.reception > int(m.group(1)), "péremption avant réception (CHECK ck_stock_dates)"
            assert lot.reste > 0
            lot.statut = "perime"
            continue
        m = re.match(r"INSERT INTO ordonnance .*VALUES \((@c\d+), (@p_\w+),", ligne)
        if m:
            assert ROLES[m.group(2)] == "pharmacien", "ordonnance saisie par un non-pharmacien (RG-30)"
            pending = Obj(client=m.group(1), lignes={}, livre=defaultdict(int), statut="en_attente", d0=None)
            ordos.append(pending)
            continue
        m = re.match(r"INSERT INTO ligne_ordonnance .*VALUES \((@o\d+), (@m\d+), (\d+),", ligne)
        if m:
            o = v[m.group(1)]
            assert m.group(2) not in o.lignes, "médicament en double sur une ordonnance (RG-28)"
            o.lignes[m.group(2)] = int(m.group(3))
            continue
        m = re.match(r"UPDATE ordonnance SET date_prescription = DATE_SUB\(CURDATE\(\), INTERVAL (\d+) DAY\)", ligne)
        if m:
            v[re.search(r"WHERE id_ordonnance = (@o\d+);", ligne).group(1)].d0 = int(m.group(1))
            continue
        m = re.match(r"INSERT INTO vente .*VALUES \(TIMESTAMP\(.*\), (@p_\w+), (@c\d+|NULL), (@o\d+|NULL), '(\w+)'\);", ligne)
        if m:
            vendeur, client, ordo = m.group(1), m.group(2), m.group(3)
            assert ROLES[vendeur] != "administrateur"
            o = v[ordo] if ordo != "NULL" else None
            if o:
                assert ROLES[vendeur] == "pharmacien", "vente sur ordonnance par un non-pharmacien (RG-38)"
                assert client == o.client, "le client de la vente n'est pas celui de l'ordonnance (RG-38)"
                assert o.statut not in ("soldee", "expiree"), "ordonnance soldée ou expirée (RG-31)"
            pending = Obj(ordo=o, statut="validee", lignes=[], vendeur=vendeur, total=0, ids=set())
            ventes.append(pending)
            continue
        m = re.match(r"INSERT INTO ligne_vente .*VALUES \(@v, (@l\d+), (\d+), (\d+)\);", ligne)
        if m:
            vente, lot, qte, prix = v["@v"], v[m.group(1)], int(m.group(2)), int(m.group(3))
            assert vente.statut == "validee" and qte > 0
            assert m.group(1) not in vente.ids, "même lot deux fois dans une vente (clé primaire)"
            assert lot.statut == "disponible", "lot périmé ou épuisé (RG-13)"
            assert qte <= lot.reste, "stock insuffisant (RG-35)"
            assert prix == lot.med.prix, "prix différent du catalogue (RG-36)"
            if lot.med.ordo:
                o = vente.ordo
                assert o is not None, "médicament sur ordonnance vendu sans ordonnance (RG-38)"
                assert lot.med_var in o.lignes, "médicament absent de l'ordonnance (RG-38)"
                assert o.livre[lot.med_var] + qte <= o.lignes[lot.med_var], "plus que prescrit (RG-38)"
            lot.reste -= qte
            if lot.reste == 0:
                lot.statut = "epuise"
            vente.ids.add(m.group(1))
            vente.lignes.append((lot, qte, lot.med_var))
            vente.total += qte * prix
            if vente.ordo:
                vente.ordo.livre[lot.med_var] += qte
                vente.ordo.statut = statut_ordo(vente.ordo)
            continue
        if ligne.startswith("UPDATE vente SET statut = 'annulee'"):
            vente = v["@v"]
            vente.statut = "annulee"
            for lot, qte, med_var in vente.lignes:
                lot.reste += qte
                if lot.statut == "epuise":
                    lot.statut = "disponible"
                if vente.ordo:
                    vente.ordo.livre[med_var] -= qte
            if vente.ordo:
                vente.ordo.statut = statut_ordo(vente.ordo)
            continue
        if ligne.startswith(("INSERT INTO personnel", "INSERT INTO fournisseur", "INSERT INTO client",
                             "USE ", "START TRANSACTION", "COMMIT", "CALL sp_maintenance", "SELECT ")):
            continue
        raise AssertionError(f"instruction non reconnue par l'émulateur : {ligne[:100]}")

    # Effet de sp_maintenance_quotidienne : ordonnances expirées
    for o in ordos:
        if o.statut in ("en_attente", "partielle") and o.d0 > 14:
            o.statut = "expiree"
    for co in commandes:                      # effet de sp_maj_statut_commande (quantités reçues)
        recu = defaultdict(int)
        for lot in co.lots:
            recu[lot.med_var] += lot.qte_init
        if co.annulee:
            co.statut = "annulee"
        elif not co.lots:
            co.statut = "en_cours"
        else:
            co.statut = "recue" if all(recu[mv] >= q for mv, q in co.lignes.items()) else "partielle"
    return Obj(lots=lots, commandes=commandes, ordos=ordos, ventes=ventes, meds=meds)


def generer(graine):
    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
        chemin = f.name
    r = subprocess.run([sys.executable, os.path.join(RACINE, "tools", "generer_donnees.py"), chemin, str(graine)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    return chemin


class TestDonneesGenerees(unittest.TestCase):
    def test_plusieurs_graines_respectent_les_regles(self):
        for graine in (2026, 7, 99, 12345):
            with self.subTest(graine=graine):
                etat = emuler(generer(graine))
                self.assertGreaterEqual(len(etat.ventes), 97)              # 3 existantes + 97 = 100 minimum
                self.assertEqual(sum(1 for v in etat.ventes if v.statut == "annulee"), 4)
                self.assertEqual(len(etat.ordos), 19)

    def test_variete_des_donnees_pour_les_statistiques(self):
        etat = emuler(generer(2026))
        self.assertEqual({o.statut for o in etat.ordos}, {"en_attente", "partielle", "soldee", "expiree"})
        self.assertEqual({c.statut for c in etat.commandes}, {"en_cours", "partielle", "recue", "annulee"})
        self.assertEqual(sum(1 for l in etat.lots if l.statut == "perime"), 2)
        sans_vente_ordo = sum(1 for v in etat.ventes if v.ordo is None)
        self.assertGreater(sans_vente_ordo, 80)
        self.assertGreater(len(etat.ventes) - sans_vente_ordo, 10)
        dispo = defaultdict(int)
        for l in etat.lots:
            if l.statut == "disponible":
                dispo[l.med_var] += l.reste
        sous_seuil = [mv for mv, mobj in ((l.med_var, l.med) for l in etat.lots) if dispo[mv] < mobj.seuil]
        self.assertGreaterEqual(len(set(sous_seuil)), 3)                  # alertes de rupture visibles

    def test_meme_graine_meme_fichier(self):
        textes = []
        for chemin in (generer(5), generer(5)):
            with open(chemin, encoding="utf-8") as f:
                textes.append(f.read())
        self.assertEqual(textes[0], textes[1])


if __name__ == "__main__":
    unittest.main()
