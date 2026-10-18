#!/usr/bin/env python3
"""Génère 06_donnees_enrichies_pharmacie.sql : jeu de données réaliste et reproductible.

Usage :  python tools/generer_donnees.py [fichier_sortie.sql] [graine]

Le script simule la vie de la pharmacie (commandes, réceptions, ventes, ordonnances) en
respectant les règles de gestion, puis écrit le SQL correspondant. Il rejoue ensuite le SQL
produit pour vérifier : variables définies avant usage, quantités jamais négatives, prix
conformes au catalogue, apostrophes correctes. Même graine = même fichier.

Pourquoi des variables SQL (@m1, @l12...) : les identifiants auto-incrémentés ne sont pas
prévisibles (les tests du script 04 en consomment), et MySQL interdit à un trigger de modifier
une table lue par la même instruction (pas d'INSERT ... SELECT sur stock).
"""
import math
import random
import re
import sys
from collections import defaultdict

SORTIE = sys.argv[1] if len(sys.argv) > 1 else "06_donnees_enrichies_pharmacie.sql"
GRAINE = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
rng = random.Random(GRAINE)

# ---------------------------------------------------------------------------------------------
# Catalogue : les 10 médicaments du script 03, puis 40 nouveaux
# (nom, dci, forme, dosage, catégorie, prix de vente, ordonnance obligatoire, seuil)
# ---------------------------------------------------------------------------------------------
EXISTANTS = [
    ("Doliprane", "paracétamol", "comprimé", "500 mg", "Antalgique", 1500, 0, 20),
    ("Efferalgan", "paracétamol", "comprimé effervescent", "1 g", "Antalgique", 2000, 0, 15),
    ("Amoxicilline Biogaran", "amoxicilline", "gélule", "500 mg", "Antibiotique", 3500, 1, 10),
    ("Augmentin", "amoxicilline + acide clavulanique", "comprimé", "1 g/125 mg", "Antibiotique", 6500, 1, 10),
    ("Ventoline", "salbutamol", "aérosol doseur", "100 mcg", "Respiratoire", 4200, 1, 5),
    ("Spasfon", "phloroglucinol", "comprimé", "80 mg", "Antispasmodique", 2500, 0, 10),
    ("Smecta", "diosmectite", "poudre pour suspension", "3 g", "Digestif", 3000, 0, 10),
    ("Oméprazole Arrow", "oméprazole", "gélule", "20 mg", "Gastro-entérologie", 3800, 1, 10),
    ("Vitamine C Upsa", "acide ascorbique", "comprimé effervescent", "500 mg", "Vitamines", 2200, 0, 10),
    ("Loratadine Mylan", "loratadine", "comprimé", "10 mg", "Antihistaminique", 2800, 0, 8),
]
NOUVEAUX = [
    ("Paracétamol Biogaran", "paracétamol", "comprimé", "1 g", "Antalgique", 1800, 0, 15),
    ("Ibuprofène Arrow", "ibuprofène", "comprimé", "400 mg", "Anti-inflammatoire", 2300, 0, 15),
    ("Aspirine Upsa", "acide acétylsalicylique", "comprimé effervescent", "500 mg", "Antalgique", 2000, 0, 10),
    ("Tramadol Zentiva", "tramadol", "gélule", "50 mg", "Antalgique", 4800, 1, 8),
    ("Ciprofloxacine Mylan", "ciprofloxacine", "comprimé", "500 mg", "Antibiotique", 5200, 1, 8),
    ("Azithromycine Sandoz", "azithromycine", "comprimé", "250 mg", "Antibiotique", 6800, 1, 8),
    ("Métronidazole Arrow", "métronidazole", "comprimé", "500 mg", "Antibiotique", 2900, 1, 10),
    ("Cotrimoxazole Teva", "sulfaméthoxazole + triméthoprime", "comprimé", "480 mg", "Antibiotique", 2500, 1, 10),
    ("Artéméther-Luméfantrine Mylan", "artéméther + luméfantrine", "comprimé", "20/120 mg", "Antipaludique", 3800, 1, 20),
    ("Quinine Mylan", "quinine", "comprimé", "300 mg", "Antipaludique", 3200, 1, 10),
    ("Metformine Biogaran", "metformine", "comprimé", "850 mg", "Diabète", 3400, 1, 15),
    ("Glibenclamide Teva", "glibenclamide", "comprimé", "5 mg", "Diabète", 2700, 1, 10),
    ("Amlodipine Sandoz", "amlodipine", "comprimé", "5 mg", "Cardiologie", 3600, 1, 12),
    ("Énalapril Arrow", "énalapril", "comprimé", "10 mg", "Cardiologie", 3100, 1, 12),
    ("Atorvastatine Zentiva", "atorvastatine", "comprimé", "20 mg", "Cardiologie", 5400, 1, 10),
    ("Furosémide Teva", "furosémide", "comprimé", "40 mg", "Cardiologie", 2200, 1, 8),
    ("Ésoméprazole Mylan", "ésoméprazole", "gélule", "20 mg", "Gastro-entérologie", 4400, 1, 8),
    ("Dompéridone Arrow", "dompéridone", "comprimé", "10 mg", "Gastro-entérologie", 2600, 0, 10),
    ("Sels de réhydratation orale", "SRO", "poudre pour solution buvable", "1 sachet", "Digestif", 700, 0, 40),
    ("Lopéramide Biogaran", "lopéramide", "gélule", "2 mg", "Digestif", 2100, 0, 10),
    ("Cétirizine Mylan", "cétirizine", "comprimé", "10 mg", "Antihistaminique", 2400, 0, 10),
    ("Prednisolone Teva", "prednisolone", "comprimé", "20 mg", "Corticoïde", 3300, 1, 8),
    ("Salbutamol Teva sirop", "salbutamol", "sirop", "2 mg/5 ml", "Respiratoire", 2800, 1, 6),
    ("Ambroxol Zentiva", "ambroxol", "sirop", "30 mg/5 ml", "Respiratoire", 3000, 0, 8),
    ("Vitamine B complexe", "vitamines B", "comprimé", "1 comprimé", "Vitamines", 2500, 0, 10),
    ("Fer + acide folique", "sulfate ferreux + acide folique", "comprimé", "200/0,4 mg", "Vitamines", 2900, 0, 15),
    ("Zinc Gifrer", "zinc", "comprimé dispersible", "20 mg", "Vitamines", 2300, 0, 10),
    ("Calcium D3 Upsa", "calcium + vitamine D3", "comprimé à croquer", "500 mg/400 UI", "Vitamines", 3900, 0, 8),
    ("Povidone iodée", "povidone iodée", "solution cutanée", "10 %", "Antiseptique", 2200, 0, 10),
    ("Chlorhexidine", "chlorhexidine", "solution cutanée", "0,05 %", "Antiseptique", 1900, 0, 10),
    ("Diclofénac gel", "diclofénac", "gel", "1 %", "Anti-inflammatoire", 3500, 0, 8),
    ("Collyre Chloramphénicol", "chloramphénicol", "collyre", "0,5 %", "Ophtalmologie", 2600, 1, 5),
    ("Mébendazole Teva", "mébendazole", "comprimé", "100 mg", "Antiparasitaire", 1800, 0, 10),
    ("Albendazole Arrow", "albendazole", "comprimé", "400 mg", "Antiparasitaire", 2200, 0, 10),
    ("Fluconazole Mylan", "fluconazole", "gélule", "150 mg", "Antifongique", 3600, 1, 6),
    ("Hydrocortisone crème", "hydrocortisone", "crème", "1 %", "Dermatologie", 3200, 1, 6),
    ("Diazépam Teva", "diazépam", "comprimé", "5 mg", "Psychotrope", 3100, 1, 5),
    ("Lévothyroxine Merck", "lévothyroxine", "comprimé", "100 mcg", "Endocrinologie", 4200, 1, 6),
    ("Lisinopril Mylan", "lisinopril", "comprimé", "10 mg", "Cardiologie", 3400, 1, 8),
    ("Paracétamol sirop enfant", "paracétamol", "sirop", "120 mg/5 ml", "Antalgique", 2100, 0, 12),
]
POIDS_CAT = {"Antalgique": 3.0, "Antipaludique": 2.5, "Vitamines": 2.0, "Digestif": 2.0, "Antiseptique": 1.5,
             "Antihistaminique": 1.3, "Anti-inflammatoire": 1.5}

FOURNISSEURS_EXISTANTS = ["PharmaDistrib", "MediSupply", "SantePlus Grossiste"]
FOURNISSEURS_NOUVEAUX = [
    ("Oméga Pharma Distribution", "600100004", "achats@omega-pharma.example", "Rue du commerce, Douala", 3),
    ("BioMed Afrique", "600100005", "info@biomed-afrique.example", "Avenue de la paix, Yaoundé", 5),
]
PERSONNEL_NOUVEAU = [
    ("Mballa", "Pierre", "pmballa", "Medecin2026!", "pharmacien", "600000004", "2022-09-05"),
    ("Tagne", "Julie", "jtagne", "Caisse2026!", "caissier", "600000005", "2024-02-12"),
]
CLIENTS_EXISTANTS = [("Fotso", "Jean", "1985-04-12"), ("Tchoua", "Aminata", "1992-09-03"),
                     ("Essomba", "Paul", "1978-01-27"), ("Njoya", "Sandra", "2001-11-19"),
                     ("Kamga", "Albert", "1965-06-30")]
CLIENTS_NOUVEAUX = [
    ("Nkou", "Béatrice", "1990-03-14", "691000001"), ("Mvondo", "Samuel", "1982-07-21", "691000002"),
    ("Ateba", "Colette", "1975-12-02", "691000003"), ("Biyik", "Hervé", "1998-05-30", "691000004"),
    ("Onana", "Grace", "1969-08-17", "691000005"), ("Eyenga", "Didier", "1988-10-09", "691000006"),
    ("Fouda", "Nadine", "1995-01-25", "691000007"), ("Manga", "Roland", "1958-04-04", "691000008"),
    ("Abena", "Sylvie", "1983-06-12", "691000009"), ("Tsimi", "Landry", "2003-09-19", "691000010"),
    ("Owona", "Mireille", "1971-02-28", "691000011"), ("Bekolo", "Patrick", "1992-11-11", "691000012"),
    ("Nga", "Clarisse", "1987-03-03", "691000013"), ("Zang", "Olivier", "1963-07-07", "691000014"),
    ("Ebogo", "Pascaline", "1999-12-24", "691000015"), ("Mbarga", "Thierry", "1980-05-16", "691000016"),
    ("Etoga", "Solange", "1977-09-29", "691000017"), ("Belinga", "Cédric", "1994-08-08", "691000018"),
    ("Atangana", "Josiane", "1966-01-15", "691000019"), ("Ngoh", "Bertrand", "1989-06-22", "691000020"),
    ("Ndzana", "Estelle", "1996-04-18", "691000021"), ("Messi", "Armand", "1973-10-31", "691000022"),
    ("Tabi", "Florence", "2000-02-06", "691000023"), ("Awono", "Gilbert", "1961-11-20", "691000024"),
    ("Essama", "Viviane", "1985-07-14", "691000025"),
]
MEDECINS = ["Dr Mballa", "Dr Fotso", "Dr Ngassa", "Dr Kouam", "Dr Abega", "Dr Tchamba"]
POSOLOGIES = ["1 comprimé matin et soir", "1 comprimé par jour au repas", "1 gélule 3 fois par jour",
              "2 comprimés par jour", "1 application 2 fois par jour", "5 ml 3 fois par jour",
              "1 comprimé le soir au coucher"]

# ---------------------------------------------------------------------------------------------
# Outils SQL
# ---------------------------------------------------------------------------------------------
sql = []


def q(texte):
    return "'" + str(texte).replace("'", "''") + "'"


def passe(n):
    return f"DATE_SUB(CURDATE(), INTERVAL {n} DAY)"


def futur(n):
    return f"DATE_ADD(CURDATE(), INTERVAL {n} DAY)"


def horodatage(n, h, m):
    return f"TIMESTAMP({passe(n)}, '{h:02d}:{m:02d}:00')"


def emettre(*lignes):
    sql.extend(lignes)


def titre(texte):
    sql.append("")
    sql.append("-- " + "-" * 69)
    sql.append("-- " + texte)
    sql.append("-- " + "-" * 69)


# ---------------------------------------------------------------------------------------------
# Modèle en mémoire
# ---------------------------------------------------------------------------------------------
class Med:
    def __init__(self, i, t, existant):
        (self.nom, self.dci, self.forme, self.dosage, self.cat, self.prix, self.ordo, self.seuil) = t
        self.i, self.existant = i, existant
        self.var = f"@m{i}"
        self.fournisseur = (i - 1) % 5
        self.poids = 0.0
        self.demande = 0


MEDS = [Med(i, t, True) for i, t in enumerate(EXISTANTS, start=1)]
MEDS += [Med(i, t, False) for i, t in enumerate(NOUVEAUX, start=len(EXISTANTS) + 1)]
LIBRES = [m for m in MEDS if not m.ordo]
ORDOS = [m for m in MEDS if m.ordo]
for m in MEDS:
    m.poids = POIDS_CAT.get(m.cat, 1.0) * rng.uniform(0.4, 1.6)

CLIENTS = [f"@c{i}" for i in range(1, len(CLIENTS_EXISTANTS) + len(CLIENTS_NOUVEAUX) + 1)]
PHARMACIENS = ["@p_ph1", "@p_ph2"]
CAISSIERS = ["@p_ca1", "@p_ca2"]
FOURN_VARS = [f"@f{i}" for i in range(1, 6)]
NOMS_FOURN = FOURNISSEURS_EXISTANTS + [f[0] for f in FOURNISSEURS_NOUVEAUX]

# ---------------------------------------------------------------------------------------------
# Passe 1 : ce que les clients demandent (ventes libres + ordonnances)
# ---------------------------------------------------------------------------------------------
HORAIRES = list(range(8, 20))
POIDS_HEURES = [3, 4, 4, 3, 2, 2, 3, 3, 2, 3, 4, 3]
JOURS = list(range(1, 91))
POIDS_JOURS = [1 + (90 - d) / 45 for d in JOURS]


def heure():
    return rng.choices(HORAIRES, POIDS_HEURES)[0], rng.randint(0, 59)


def tirer_meds(k):
    choisis, pool = [], LIBRES[:]
    for _ in range(k):
        m = rng.choices(pool, [x.poids for x in pool])[0]
        pool.remove(m)
        choisis.append(m)
    return choisis


ventes = []   # dicts : jours, h, mn, vendeur, client, items [(Med, qte)], paiement, ordonnance, annulee
for _ in range(108):
    h, mn = heure()
    vendeur = rng.choices(CAISSIERS + PHARMACIENS, [40, 25, 20, 15])[0]
    client = rng.choice(CLIENTS) if rng.random() < 0.55 else None
    k = rng.choice([1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4])
    items = [(m, rng.choice([1, 1, 1, 2, 2, 3, 4, 5] if m.prix > 1000 else [1, 2, 3, 4, 6])) for m in tirer_meds(k)]
    ventes.append(dict(jours=rng.choices(JOURS, POIDS_JOURS)[0], h=h, mn=mn, vendeur=vendeur, client=client,
                       items=items, paiement=rng.choices(["especes", "carte", "mobile_money"], [5, 2, 3])[0],
                       ordonnance=None, annulee=False))

# 4 ventes libres annulées (entre 4 et 60 jours)
for v in rng.sample([v for v in ventes if 4 <= v["jours"] <= 60], 4):
    v["annulee"] = True

# Ordonnances : 19 nouvelles
ISSUES = ["full1"] * 7 + ["full2"] * 4 + ["partielle"] * 4 + ["aucune"] * 4
rng.shuffle(ISSUES)
ordonnances = []
for n, issue in enumerate(ISSUES, start=1):
    if issue == "aucune":
        d0 = rng.choice([2, 4, 7, 9]) if n % 2 else rng.randint(20, 70)
    elif issue == "partielle":
        d0 = rng.randint(3, 12) if n % 2 else rng.randint(20, 75)
    elif issue == "full2":
        d0 = rng.randint(16, 80)
    else:
        d0 = rng.randint(3, 80)
    lignes = []
    for m in rng.sample(ORDOS, rng.choice([1, 2, 2, 3])):
        lignes.append(dict(med=m, qte=rng.choice([7, 10, 14, 15, 20, 21, 28, 30, 60]),
                           poso=rng.choice(POSOLOGIES), duree=rng.choice([5, 7, 10, 14, 30])))
    o = dict(n=n, var=f"@o{n}", d0=d0, issue=issue, client=rng.choice(CLIENTS), medecin=rng.choice(MEDECINS),
             ordre="ONMC-%05d" % rng.randint(10000, 99999), lignes=lignes, pharmacien=rng.choice(PHARMACIENS))
    ordonnances.append(o)

    def vente_ordo(jours, parts):
        h, mn = heure()
        ventes.append(dict(jours=max(1, jours), h=h, mn=mn, vendeur=o["pharmacien"], client=o["client"],
                           items=parts, paiement=rng.choice(["especes", "carte", "mobile_money"]),
                           ordonnance=o, annulee=False))

    if issue == "full1":
        vente_ordo(d0 - rng.choice([0, 0, 1, 2]), [(l["med"], l["qte"]) for l in lignes])
    elif issue == "full2":
        k1 = rng.choice([0, 1])
        k2 = k1 + rng.randint(3, 9)
        vente_ordo(d0 - k1, [(l["med"], math.ceil(l["qte"] / 2)) for l in lignes])
        vente_ordo(d0 - k2, [(l["med"], l["qte"] - math.ceil(l["qte"] / 2)) for l in lignes])
    elif issue == "partielle":
        vente_ordo(d0 - rng.choice([0, 1]), [(l["med"], max(1, l["qte"] // 2 - 1)) for l in lignes])

for v in ventes:
    for m, qte in v["items"]:
        m.demande += qte

# ---------------------------------------------------------------------------------------------
# Plan des commandes et des lots
# ---------------------------------------------------------------------------------------------
mediane = sorted(m.demande for m in LIBRES)[len(LIBRES) // 2]
forts = [m for m in LIBRES if m.demande >= mediane]
faibles = [m for m in LIBRES if m.demande < mediane]
rupture = rng.sample(forts, 4)
bas = rng.sample([m for m in forts if m not in rupture], 4)
normaux = [m for m in LIBRES if m not in rupture]
meds_b = rng.sample(normaux, 16)                       # médicaments réapprovisionnés (lot B)
pool_perimes = [m for m in meds_b if m in faibles]
perimes = rng.sample(pool_perimes if len(pool_perimes) >= 2 else meds_b, 2)
pool_proches = [m for m in normaux if m in faibles and m not in perimes]
if len(pool_proches) < 6:
    pool_proches += [m for m in normaux if m not in perimes and m not in pool_proches]
proches = rng.sample(pool_proches, 6)


class Lot:
    def __init__(self, med, nom, qte, reception, exp_final, prix_achat, couche):
        self.med, self.nom, self.qte, self.reste = med, nom, qte, qte
        self.reception, self.exp_final, self.prix_achat, self.couche = reception, exp_final, prix_achat, couche
        self.var = None


def prix_achat(m):
    return max(100, int(round(m.prix * rng.uniform(0.55, 0.75) / 50.0)) * 50)


lots = []
for m in MEDS:
    if m in rupture:
        total = max(20, math.ceil(m.demande * 0.55))
    elif m in bas:
        total = max(30, math.ceil(m.demande * 0.85))
    elif m.ordo:
        total = max(25, math.ceil(m.demande * 1.6) + 10)
    else:
        total = max(40, math.ceil(m.demande * 1.35) + 10)
    a_lot_b = m in meds_b
    qa = round(total * 0.6) if a_lot_b else total
    exp_a = rng.randint(420, 800)
    exp_final = exp_a
    if m in perimes:
        exp_final = -rng.choice([4, 9])
    elif m in proches:
        exp_final = proches.index(m) * 13 + 12          # 12, 25, 38, 51, 64, 77 jours
    lots.append(Lot(m, f"L25A-{m.i:02d}", qa, 100, exp_final, prix_achat(m), "A"))
    if a_lot_b:
        lots.append(Lot(m, f"L26B-{m.i:02d}", total - qa, 45, rng.randint(330, 700), prix_achat(m), "B"))

# ---------------------------------------------------------------------------------------------
# Événements chronologiques (jours écoulés décroissants)
# ---------------------------------------------------------------------------------------------
evenements = []  # (jours, priorité, ordre, type, données)
compteur = [0]


def evt(jours, prio, type_, data):
    compteur[0] += 1
    evenements.append((-jours, prio, compteur[0], type_, data))


commandes = []   # dicts : var, fournisseur, jours, lignes {Med: qte}, lots [Lot], statut_final
# Commandes initiales (une par fournisseur), lots A reçus à J-100
for f in range(5):
    lignes = {l.med: l.qte for l in lots if l.couche == "A" and l.med.fournisseur == f}
    commandes.append(dict(var=f"@co{len(commandes) + 1}", f=f, jours=105, lignes=lignes,
                          lots=[l for l in lots if l.couche == "A" and l.med.fournisseur == f],
                          recep=100, annulee=False, prevue=-102))
# Commandes de réapprovisionnement (lots B reçus à J-45), une par fournisseur concerné
for f in range(5):
    lots_f = [l for l in lots if l.couche == "B" and l.med.fournisseur == f]
    if not lots_f:
        continue
    commandes.append(dict(var=f"@co{len(commandes) + 1}", f=f, jours=50, lignes={l.med: l.qte for l in lots_f},
                          lots=lots_f, recep=45, annulee=False, prevue=-47))
# Une commande de réapprovisionnement partielle : on ne reçoit que la première moitié des lots
partielle = max((c for c in commandes if c["jours"] == 50), key=lambda c: len(c["lignes"]))
if len(partielle["lots"]) >= 2:
    moitie = len(partielle["lots"]) // 2
    recus, manquants = partielle["lots"][:moitie], partielle["lots"][moitie:]
    partielle["lots"] = recus
    for l in manquants:
        lots.remove(l)           # non reçus : pas de lot (la ligne de commande reste en attente)
# Deux commandes en cours (pour réapprovisionner les ruptures et stocks bas), une commande annulée
a_commander = rupture + bas
for idx, groupe in enumerate((a_commander[:4], a_commander[4:])):
    f = groupe[0].fournisseur
    commandes.append(dict(var=f"@co{len(commandes) + 1}", f=f, jours=3 - idx * 2, lignes={m: max(60, m.demande) for m in groupe},
                          lots=[], recep=None, annulee=False, prevue=3 + idx * 2))
commandes.append(dict(var=f"@co{len(commandes) + 1}", f=3, jours=20,
                      lignes={rng.choice(faibles): 40, rng.choice(LIBRES): 30}, lots=[], recep=None,
                      annulee=True, prevue=-17))
for c in commandes:
    evt(c["jours"], 0, "commande", c)
    for l in c["lots"]:
        evt(c["recep"], 1, "lot", (c, l))
for o in ordonnances:
    evt(o["d0"], 2, "ordonnance", o)
for v in ventes:
    evt(v["jours"], 3, "vente", v)
evenements.sort(key=lambda e: e[:3])

# ---------------------------------------------------------------------------------------------
# Passe 2 : simulation + émission du SQL
# ---------------------------------------------------------------------------------------------
sql_entete = [
    "-- =====================================================================",
    "--  Script 6 : JEU DE DONNÉES ENRICHI (généré par tools/generer_donnees.py)",
    f"--  Graine : {GRAINE} (même graine = même fichier)",
    "--",
    "--  À exécuter APRÈS les scripts 01, 02 et 03 (il complète le jeu de test).",
    "--  Ajoute : 40 médicaments (50 au total), 25 clients (30), 2 fournisseurs (5), 2 membres du",
    "--  personnel, des commandes et des lots, 19 ordonnances (20), des ventes sur 90 jours.",
    "--",
    "--  ATTENTION : après ce script, les valeurs attendues des scripts 04 et 05 changent",
    "--  (elles décrivent le petit jeu de test du script 03).",
    "--",
    "--  Exécution : Alt+X dans DBeaver (quelques dizaines de secondes). Tout est dans une",
    "--  transaction : en cas d'erreur, exécutez ROLLBACK; puis relancez 01, 02, 03 avant de recommencer.",
    "--  Les dates sont relatives à CURDATE() : les ventes couvrent les 90 derniers jours.",
    "-- =====================================================================",
    "",
    "USE pharmacie;",
    "START TRANSACTION;",
]
sql.extend(sql_entete)

titre("1. Personnel")
for nom, prenom, login, mdp, role, tel, emb in PERSONNEL_NOUVEAU:
    emettre(f"INSERT INTO personnel (nom, prenom, login, mot_de_passe_hash, role, telephone, date_embauche) VALUES "
            f"({q(nom)}, {q(prenom)}, {q(login)}, SHA2({q(mdp)}, 256), {q(role)}, {q(tel)}, {q(emb)});")
for var, login in (("@p_ph1", "cdupont"), ("@p_ph2", "pmballa"), ("@p_ca1", "mngono"), ("@p_ca2", "jtagne")):
    emettre(f"SET {var} := (SELECT id_personnel FROM personnel WHERE login = {q(login)});")

titre("2. Fournisseurs")
for nom, tel, email, adr, delai in FOURNISSEURS_NOUVEAUX:
    emettre(f"INSERT INTO fournisseur (raison_sociale, telephone, email, adresse, delai_livraison_jours) VALUES "
            f"({q(nom)}, {q(tel)}, {q(email)}, {q(adr)}, {delai});")
for var, nom in zip(FOURN_VARS, NOMS_FOURN):
    emettre(f"SET {var} := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = {q(nom)});")

titre("3. Médicaments (les 10 premiers existent déjà : on retrouve leur identifiant)")
for m in MEDS:
    if m.existant:
        emettre(f"SET {m.var} := (SELECT id_medicament FROM medicament WHERE nom_commercial = {q(m.nom)} "
                f"AND forme = {q(m.forme)} AND dosage = {q(m.dosage)});")
    else:
        emettre(f"INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) "
                f"VALUES ({q(m.nom)}, {q(m.dci)}, {q(m.forme)}, {q(m.dosage)}, {q(m.cat)}, {m.prix}, {m.ordo}, {m.seuil});",
                f"SET {m.var} := LAST_INSERT_ID();")

titre("4. Clients (les 5 premiers existent déjà)")
for i, (nom, prenom, naiss) in enumerate(CLIENTS_EXISTANTS, start=1):
    emettre(f"SET @c{i} := (SELECT id_client FROM client WHERE nom = {q(nom)} AND prenom = {q(prenom)} AND date_naissance = {q(naiss)});")
for i, (nom, prenom, naiss, tel) in enumerate(CLIENTS_NOUVEAUX, start=len(CLIENTS_EXISTANTS) + 1):
    emettre(f"INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ({q(nom)}, {q(prenom)}, {q(naiss)}, {q(tel)});",
            f"SET @c{i} := LAST_INSERT_ID();")

titre("5. Vie de la pharmacie, dans l'ordre chronologique : commandes, réceptions, ordonnances, ventes")
numero_lot_var = [0]
ventes_emises = 0
lignes_vente_emises = 0
lots_par_med = defaultdict(list)
suivi_ordonnance = defaultdict(int)


def eligibles(med, jours):
    res = []
    for l in lots_par_med[med.i]:
        if l.reste > 0 and l.reception >= jours and (l.exp_final > 0 or jours > -l.exp_final):
            res.append(l)
    return sorted(res, key=lambda l: (l.exp_final, l.var))


def allouer(med, qte, jours):
    dispo = sum(l.reste for l in eligibles(med, jours))
    qte = min(qte, dispo)
    parts = []
    for l in eligibles(med, jours):
        if qte == 0:
            break
        prise = min(l.reste, qte)
        parts.append((l, prise))
        qte -= prise
    return parts


for _, _, _, type_, data in evenements:
    if type_ == "commande":
        c = data
        emettre("",
                f"-- Commande {c['var']} ({NOMS_FOURN[c['f']]}) passée il y a {c['jours']} jours"
                + (" : ANNULÉE" if c["annulee"] else ""),
                f"INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES "
                f"({FOURN_VARS[c['f']]}, {PHARMACIENS[c['f'] % 2]}, {horodatage(c['jours'], 10, 15)}, "
                f"{passe(-c['prevue']) if c['prevue'] <= 0 else futur(c['prevue'])});",
                f"SET {c['var']} := LAST_INSERT_ID();")
        for m, qte in c["lignes"].items():
            pa = next((l.prix_achat for l in lots if l.med is m), prix_achat(m))
            emettre(f"INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) "
                    f"VALUES ({c['var']}, {m.var}, {qte}, {pa});")
        if c["annulee"]:
            emettre(f"UPDATE commande SET statut = 'annulee' WHERE id_commande = {c['var']};")
    elif type_ == "lot":
        c, l = data
        numero_lot_var[0] += 1
        l.var = f"@l{numero_lot_var[0]}"
        l.reception = c["recep"]
        exp_insert = l.exp_final if l.exp_final > 0 else 300       # un lot périmé ne peut pas être reçu
        emettre(f"INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, "
                f"quantite_initiale, quantite_restante, prix_achat) VALUES ({l.med.var}, {c['var']}, {q(l.nom)}, "
                f"{passe(c['recep'])}, {futur(exp_insert)}, {l.qte}, {l.qte}, {l.prix_achat});",
                f"SET {l.var} := LAST_INSERT_ID();")
        lots_par_med[l.med.i].append(l)
    elif type_ == "ordonnance":
        o = data
        emettre("",
                f"-- Ordonnance {o['var']} ({o['issue']}) : créée aujourd'hui puis antidatée en fin de script",
                f"INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) "
                f"VALUES ({o['client']}, {o['pharmacien']}, {q(o['medecin'])}, {q(o['ordre'])}, CURDATE(), {futur(14)});",
                f"SET {o['var']} := LAST_INSERT_ID();")
        for l in o["lignes"]:
            emettre(f"INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) "
                    f"VALUES ({o['var']}, {l['med'].var}, {l['qte']}, {q(l['poso'])}, {l['duree']});")
    else:
        v = data
        parts_par_item = []
        for m, qte in v["items"]:
            parts = allouer(m, qte, v["jours"])
            if parts:
                parts_par_item.append((m, parts))
        if not parts_par_item:
            continue
        o = v["ordonnance"]
        emettre("",
                f"INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES "
                f"({horodatage(v['jours'], v['h'], v['mn'])}, {v['vendeur']}, {v['client'] or 'NULL'}, "
                f"{o['var'] if o else 'NULL'}, {q(v['paiement'])});",
                "SET @v := LAST_INSERT_ID();")
        ventes_emises += 1
        for m, parts in parts_par_item:
            for l, prise in parts:
                l.reste -= prise
                lignes_vente_emises += 1
                emettre(f"INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, {l.var}, {prise}, {m.prix});")
                if o:
                    suivi_ordonnance[(o["n"], m.i)] += prise
        if v["annulee"]:
            emettre("UPDATE vente SET statut = 'annulee' WHERE id_vente = @v;")
            for m, parts in parts_par_item:
                for l, prise in parts:
                    l.reste += prise

# Contrôle : jamais plus délivré que prescrit
for o in ordonnances:
    for l in o["lignes"]:
        assert suivi_ordonnance[(o["n"], l["med"].i)] <= l["qte"], (o["n"], l["med"].nom)

titre("6. Antidatage des ordonnances (créées aujourd'hui pour passer les contrôles, puis ramenées à leur vraie date)")
for o in ordonnances:
    emettre(f"UPDATE ordonnance SET date_prescription = {passe(o['d0'])}, "
            f"date_validite = DATE_ADD({passe(o['d0'])}, INTERVAL 14 DAY), "
            f"date_enregistrement = {horodatage(o['d0'], 9, 0)} WHERE id_ordonnance = {o['var']};")

titre("7. Lots périmés et proches de la péremption (alertes du tableau de bord)")
for l in lots:
    if l.var and l.exp_final <= 0 and l.exp_final != 300:
        assert l.reste > 0, f"le lot périmé {l.nom} est vide"
        emettre(f"UPDATE stock SET date_peremption = {passe(-l.exp_final)}, statut = 'perime' WHERE id_stock = {l.var};")
    elif l.var and 0 < l.exp_final <= 90:
        emettre(f"-- {l.nom} : péremption dans {l.exp_final} jours (inséré tel quel)")

titre("8. Mise à jour des statuts (ordonnances expirées, lots périmés) puis validation")
emettre("CALL sp_maintenance_quotidienne();", "COMMIT;", "",
        "-- Vérifications (valeurs attendues en commentaire)",
        "SELECT COUNT(*) AS medicaments FROM medicament;   -- 50",
        "SELECT COUNT(*) AS clients FROM client;           -- 30",
        "SELECT COUNT(*) AS fournisseurs FROM fournisseur; -- 5",
        "SELECT COUNT(*) AS personnel FROM personnel;      -- 5",
        "SELECT COUNT(*) AS ordonnances FROM ordonnance;   -- 20",
        f"SELECT COUNT(*) AS ventes FROM vente;             -- {3 + ventes_emises}",
        "SELECT statut, COUNT(*) AS nb FROM ordonnance GROUP BY statut;",
        "SELECT statut, COUNT(*) AS nb FROM commande GROUP BY statut;",
        "SELECT statut, COUNT(*) AS nb FROM stock GROUP BY statut;",
        "SELECT * FROM v_alertes_rupture;",
        "SELECT * FROM v_alertes_peremption ORDER BY date_peremption;")
texte = "\n".join(sql) + "\n"

# ---------------------------------------------------------------------------------------------
# Rejeu de vérification sur le SQL produit
# ---------------------------------------------------------------------------------------------
prix_par_var = {m.var: m.prix for m in MEDS}
definies, reste_lot, lot_de_var, ventes_lignes = set(), {}, {}, defaultdict(list)
vente_courante, erreurs = None, []
corps = [l for l in texte.split("\n") if l.strip() and not l.startswith("--")]
for ligne in corps:
    if ligne.count("'") % 2:
        erreurs.append(f"apostrophes impaires : {ligne[:90]}")
    if not ligne.rstrip().endswith(";") and not ligne.rstrip().endswith("-- 5") and ";" not in ligne:
        erreurs.append(f"ligne sans point-virgule : {ligne[:90]}")
    cible = re.match(r"SET (@\w+) :=", ligne)
    sans_textes = re.sub(r"'(?:[^']|'')*'", "''", ligne)          # on ignore le contenu des chaînes
    utilisees = set(re.findall(r"@\w+", sans_textes)) - ({cible.group(1)} if cible else set())
    manquantes = utilisees - definies
    if manquantes:
        erreurs.append(f"variable utilisée avant définition {manquantes} : {ligne[:90]}")
    if cible:
        definies.add(cible.group(1))
    m = re.match(r"INSERT INTO stock .*VALUES \((@m\d+), (@co\d+), '([^']+)', .*, (\d+), (\d+), (\d+)\);$", ligne)
    if m:
        pending_lot = (int(m.group(4)), int(m.group(5)))
        assert pending_lot[0] == pending_lot[1]
        lot_attendu = pending_lot[0]
        derniere_var = None
    m2 = re.match(r"SET (@l\d+) := LAST_INSERT_ID\(\);", ligne)
    if m2:
        reste_lot[m2.group(1)] = lot_attendu
    mv = re.match(r"INSERT INTO ligne_vente .*VALUES \(@v, (@l\d+), (\d+), (\d+)\);", ligne)
    if mv:
        var, qte, prix = mv.group(1), int(mv.group(2)), int(mv.group(3))
        reste_lot[var] -= qte
        ventes_lignes["@v"].append((var, qte))
        if reste_lot[var] < 0:
            erreurs.append(f"stock négatif sur {var}")
    if ligne.startswith("INSERT INTO vente "):
        ventes_lignes["@v"] = []
    if ligne.startswith("UPDATE vente SET statut = 'annulee'"):
        for var, qte in ventes_lignes["@v"]:
            reste_lot[var] += qte
if erreurs:
    print("ERREURS DE COHÉRENCE :", *erreurs[:15], sep="\n  ")
    sys.exit(1)
# Les lots simulés et rejoués doivent donner les mêmes quantités restantes
for l in lots:
    if l.var:
        assert reste_lot[l.var] == l.reste, (l.nom, reste_lot[l.var], l.reste)

with open(SORTIE, "w", encoding="utf-8") as f:
    f.write(texte)
print(f"{SORTIE} : {len(corps)} instructions, {ventes_emises} ventes ({lignes_vente_emises} lignes), "
      f"{len(lots)} lots, {len(commandes)} commandes, {len(ordonnances)} ordonnances ; vérification OK")
