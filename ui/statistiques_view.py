"""Statistiques : 13 analyses (script SQL 05) sous forme de tableau et de diagramme."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.errors import BusinessError
from core.formatting import fmt_valeur
from services import stats_service as st
from ui.charts import BarChart
from ui.widgets import creer_arbre

# (titre, fonction, colonnes, graphique)
#  colonnes  : (clé, titre, genre, largeur, ancrage)
#  graphique : (clé des étiquettes, genre des étiquettes, clé des valeurs, ordre inversé ?) ou None
ANALYSES = [
    ("Chiffre d'affaires par jour", st.ca_par_jour,
     [("jour", "Jour", "date", 100, "center"), ("nb_ventes", "Ventes", "int", 70, "e"),
      ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e"), ("panier_moyen", "Panier moyen", "montant", 110, "e")],
     ("jour", "date", "chiffre_affaires", True)),
    ("Chiffre d'affaires par mois", st.ca_par_mois,
     [("mois", "Mois", "texte", 90, "center"), ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e"),
      ("ca_mois_precedent", "Mois précédent", "montant", 130, "e"), ("evolution_pct", "Évolution", "pct", 90, "e")],
     ("mois", "texte", "chiffre_affaires", False)),
    ("Chiffre d'affaires par semaine", st.ca_par_semaine,
     [("annee_semaine", "Semaine", "texte", 90, "center"), ("premier_jour_observe", "Premier jour", "date", 100, "center"),
      ("nb_ventes", "Ventes", "int", 70, "e"), ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e")],
     ("annee_semaine", "texte", "chiffre_affaires", True)),
    ("Top des médicaments vendus", st.top_medicaments,
     [("nom_commercial", "Médicament", "texte", 220, "w"), ("categorie", "Catégorie", "texte", 130, "w"),
      ("quantite_vendue", "Quantité", "int", 80, "e"), ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e")],
     ("nom_commercial", "texte", "quantite_vendue", False)),
    ("Médicaments jamais vendus", st.medicaments_jamais_vendus,
     [("nom_commercial", "Médicament", "texte", 260, "w"), ("categorie", "Catégorie", "texte", 160, "w")], None),
    ("Marge brute par médicament", st.marge_par_medicament,
     [("nom_commercial", "Médicament", "texte", 200, "w"), ("quantite_vendue", "Quantité", "int", 70, "e"),
      ("chiffre_affaires", "Chiffre d'affaires", "montant", 120, "e"), ("cout_achat", "Coût d'achat", "montant", 110, "e"),
      ("marge_brute", "Marge brute", "montant", 110, "e"), ("taux_marge_pct", "Taux", "pct", 70, "e")],
     ("nom_commercial", "texte", "marge_brute", False)),
    ("Ventes par membre du personnel", st.ventes_par_personnel,
     [("nom", "Nom", "texte", 130, "w"), ("prenom", "Prénom", "texte", 110, "w"), ("role", "Rôle", "texte", 110, "w"),
      ("nb_ventes", "Ventes", "int", 70, "e"), ("montant", "Montant", "montant", 120, "e"), ("part_ca_pct", "Part du CA", "pct", 90, "e")],
     ("nom", "texte", "montant", False)),
    ("Clients les plus fidèles", st.clients_fideles,
     [("nom", "Nom", "texte", 130, "w"), ("prenom", "Prénom", "texte", 110, "w"), ("nb_achats", "Achats", "int", 70, "e"),
      ("montant_total", "Montant total", "montant", 120, "e"), ("panier_moyen", "Panier moyen", "montant", 110, "e"),
      ("dernier_achat", "Dernier achat", "datetime", 130, "center")],
     ("nom", "texte", "montant_total", False)),
    ("Performance des fournisseurs", st.performance_fournisseurs,
     [("raison_sociale", "Fournisseur", "texte", 170, "w"), ("nb_commandes", "Commandes", "int", 80, "e"),
      ("nb_commandes_recues", "Reçues", "int", 60, "e"), ("nb_lots_recus", "Lots", "int", 50, "e"),
      ("unites_recues", "Unités", "int", 70, "e"), ("montant_achats", "Montant d'achats", "montant", 120, "e"),
      ("delai_reel_moyen_jours", "Délai réel (j)", "decimal", 90, "e"), ("delai_annonce_jours", "Annoncé (j)", "int", 80, "e")],
     ("raison_sociale", "texte", "montant_achats", False)),
    ("Ventes sur ordonnance et ventes libres", st.ventes_ordonnance_libre,
     [("type_vente", "Type", "texte", 180, "w"), ("nb_ventes", "Ventes", "int", 70, "e"),
      ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e"), ("part_ventes_pct", "Part des ventes", "pct", 100, "e")],
     ("type_vente", "texte", "nb_ventes", False)),
    ("Jours de couverture du stock", st.couverture_stock,
     [("nom_commercial", "Médicament", "texte", 220, "w"), ("stock_disponible", "Stock", "int", 70, "e"),
      ("vendu_30_jours", "Vendu en 30 j", "int", 90, "e"), ("jours_de_couverture", "Jours de couverture", "decimal", 130, "e")], None),
    ("Classement par catégorie", st.classement_categories,
     [("categorie", "Catégorie", "texte", 150, "w"), ("nom_commercial", "Médicament", "texte", 220, "w"),
      ("quantite_vendue", "Quantité", "int", 80, "e"), ("rang_categorie", "Rang", "int", 60, "e")], None),
    ("Affluence par heure", st.affluence_par_heure,
     [("heure", "Heure", "int", 70, "center"), ("nb_ventes", "Ventes", "int", 70, "e"),
      ("chiffre_affaires", "Chiffre d'affaires", "montant", 130, "e")],
     ("heure", "int", "nb_ventes", False)),
]


class StatistiquesView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(barre, text="Analyse :").pack(side="left")
        self.combo = ttk.Combobox(barre, state="readonly", width=42, values=[a[0] for a in ANALYSES])
        self.combo.current(0)
        self.combo.pack(side="left", padx=6)
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="left")

        self.graphique = BarChart(self)
        self.graphique.grid(row=1, column=0, sticky="ew")
        self.zone = ttk.Frame(self)
        self.zone.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        self.zone.columnconfigure(0, weight=1)
        self.zone.rowconfigure(0, weight=1)
        self.tableau = None
        self.actualiser()

    def actualiser(self):
        indice = self.combo.current()
        if indice < 0:
            return
        titre, fonction, colonnes, graphique = ANALYSES[indice]
        try:
            lignes = fonction(self.user)
        except BusinessError as erreur:
            messagebox.showwarning(f"Analyse « {titre} »", str(erreur), parent=self)
            return
        except Exception as erreur:        # on indique QUELLE analyse échoue et pourquoi
            messagebox.showerror(f"Analyse « {titre} » impossible", f"{type(erreur).__name__} : {erreur}",
                                 parent=self)
            return
        try:
            self._afficher(titre, lignes, colonnes, graphique)
        except Exception as erreur:
            messagebox.showerror(f"Analyse « {titre} »", f"Affichage impossible : {type(erreur).__name__} : {erreur}",
                                 parent=self)

    def _afficher(self, titre, lignes, colonnes, graphique):
        if self.tableau is not None:
            self.tableau.destroy()
        self.tableau = creer_arbre(self.zone, [(c[0], c[1], c[3], c[4]) for c in colonnes])
        self.tableau.grid(row=0, column=0, sticky="nsew")
        for ligne in lignes:
            self.tableau.arbre.insert("", "end", values=[fmt_valeur(ligne.get(c[0]), c[2]) for c in colonnes])
        if graphique is None:
            self.graphique.effacer()
            return
        cle_etiquette, genre_etiquette, cle_valeur, inverser = graphique
        donnees = list(reversed(lignes)) if inverser else list(lignes)
        donnees = donnees[-15:] if inverser else donnees[:15]
        self.graphique.tracer([fmt_valeur(d.get(cle_etiquette), genre_etiquette) for d in donnees],
                              [d.get(cle_valeur) or 0 for d in donnees], titre)
