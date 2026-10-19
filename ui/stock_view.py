"""Module Stock : état par médicament, lots, et gestion du catalogue (pharmacien)."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.formatting import fmt_date, fmt_montant, parse_decimal
from core.permissions import can
from core.stock_rules import etat_stock, niveau_peremption
from services import stock_service
from services.stock_service import STATUTS_LOT, MedicamentSaisie
from ui.dialogs import FormulaireDialog
from ui.messages import essayer
from ui.widgets import creer_arbre, vider


class EtatStockPanel(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        barre.columnconfigure(1, weight=1)
        ttk.Label(barre, text="Rechercher :").grid(row=0, column=0, padx=(0, 6))
        self.var_terme = tk.StringVar()
        entree = ttk.Entry(barre, textvariable=self.var_terme)
        entree.grid(row=0, column=1, sticky="ew")
        entree.bind("<Return>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Actualiser", command=self.actualiser).grid(row=0, column=2, padx=6)
        cadre = creer_arbre(self, [
            ("nom", "Médicament", 220, "w"), ("forme", "Forme", 130, "w"), ("dosage", "Dosage", 90, "w"),
            ("stock", "Stock vendable", 100, "e"), ("seuil", "Seuil", 60, "e"), ("etat", "État", 110, "w")])
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = cadre.arbre
        self.arbre.tag_configure("Rupture", foreground="#b91c1c")
        self.arbre.tag_configure("Sous le seuil", foreground="#b45309")
        self.arbre.tag_configure("Désactivé", foreground="#9ca3af")
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, stock_service.etat_stock, self.user, self.var_terme.get())
        if not ok:
            return
        vider(self.arbre)
        for m in lignes:
            etat = etat_stock(int(m["stock_disponible"]), m["seuil_min"], bool(m["actif"]))
            self.arbre.insert("", "end", iid=str(m["id_medicament"]), tags=(etat,), values=(
                m["nom_commercial"], m["forme"], m["dosage"], int(m["stock_disponible"]),
                m["seuil_min"], etat))


class LotsPanel(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        barre.columnconfigure(2, weight=1)
        self.statuts = {"Tous les statuts": None}
        self.statuts.update({libelle: cle for cle, libelle in STATUTS_LOT.items()})
        self.combo = ttk.Combobox(barre, state="readonly", values=list(self.statuts), width=18)
        self.combo.current(0)
        self.combo.grid(row=0, column=0)
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        ttk.Label(barre, text="Médicament ou lot :").grid(row=0, column=1, padx=(10, 4))
        self.var_terme = tk.StringVar()
        entree = ttk.Entry(barre, textvariable=self.var_terme)
        entree.grid(row=0, column=2, sticky="ew")
        entree.bind("<Return>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Actualiser", command=self.actualiser).grid(row=0, column=3, padx=6)
        cadre = creer_arbre(self, [
            ("nom", "Médicament", 190, "w"), ("lot", "Lot", 100, "w"), ("fournisseur", "Fournisseur", 150, "w"),
            ("recu", "Reçu le", 85, "center"), ("perem", "Péremption", 90, "center"),
            ("init", "Initial", 60, "e"), ("rest", "Restant", 60, "e"), ("statut", "Statut", 90, "w")])
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = cadre.arbre
        self.arbre.tag_configure("perime", foreground="#b91c1c")
        self.arbre.tag_configure("urgent", foreground="#c2410c")
        self.arbre.tag_configure("a_surveiller", foreground="#a16207")
        self.arbre.tag_configure("epuise", foreground="#9ca3af")
        ttk.Label(self, text="Rouge : périmé · orange : moins de 30 jours · jaune : moins de 90 jours · gris : épuisé",
                  foreground="#6b7280").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.actualiser()

    def actualiser(self):
        ok, lots = essayer(self, stock_service.lister_lots, self.user,
                           self.var_terme.get(), self.statuts[self.combo.get()])
        if not ok:
            return
        vider(self.arbre)
        for l in lots:
            tag = "epuise" if l["quantite_restante"] == 0 else niveau_peremption(l["date_peremption"])
            self.arbre.insert("", "end", iid=str(l["id_stock"]), tags=(tag,), values=(
                l["nom_commercial"], l["numero_lot"], l["fournisseur"], fmt_date(l["date_reception"]),
                fmt_date(l["date_peremption"]), l["quantite_initiale"], l["quantite_restante"],
                STATUTS_LOT.get(l["statut"], l["statut"])))


class CataloguePanel(ttk.Frame):
    """Création, modification et désactivation des médicaments (pharmacien)."""

    CHAMPS = [("nom_commercial", "Nom commercial *", "texte"), ("dci", "DCI *", "texte"),
              ("forme", "Forme *", "texte"), ("dosage", "Dosage *", "texte"),
              ("categorie", "Catégorie", "texte"), ("prix_vente", "Prix de vente *", "texte"),
              ("seuil_min", "Seuil d'alerte *", "texte"),
              ("ordonnance_obligatoire", "Ordonnance obligatoire", "bool")]

    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.medicaments = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(barre, text="Nouveau médicament", style="Primary.TButton", command=self.nouveau).pack(side="left")
        ttk.Button(barre, text="Modifier", command=self.modifier).pack(side="left", padx=6)
        ttk.Button(barre, text="Désactiver / Réactiver", command=self.basculer).pack(side="left")
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="right")
        cadre = creer_arbre(self, [
            ("nom", "Médicament", 180, "w"), ("dci", "DCI", 150, "w"), ("forme", "Forme", 110, "w"),
            ("dosage", "Dosage", 80, "w"), ("cat", "Catégorie", 110, "w"), ("prix", "Prix", 70, "e"),
            ("seuil", "Seuil", 50, "e"), ("ordo", "Ordo.", 45, "center"), ("actif", "Actif", 50, "center")])
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = cadre.arbre
        self.arbre.tag_configure("inactif", foreground="#9ca3af")
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, stock_service.etat_stock, self.user, "")
        if not ok:
            return
        self.medicaments = {m["id_medicament"]: m for m in lignes}
        vider(self.arbre)
        for m in lignes:
            self.arbre.insert("", "end", iid=str(m["id_medicament"]),
                              tags=() if m["actif"] else ("inactif",), values=(
                m["nom_commercial"], m["dci"], m["forme"], m["dosage"], m["categorie"] or "",
                fmt_montant(m["prix_vente"]), m["seuil_min"],
                "Oui" if m["ordonnance_obligatoire"] else "", "Oui" if m["actif"] else "Non"))

    def _selection(self):
        sel = self.arbre.selection()
        if not sel:
            messagebox.showinfo("Catalogue", "Sélectionnez d'abord un médicament.", parent=self)
            return None
        return int(sel[0])

    def _formulaire(self, titre, valeurs, action):
        def enregistrer(dialogue, v):
            try:
                saisie = MedicamentSaisie(
                    v["nom_commercial"], v["dci"], v["forme"], v["dosage"], v["categorie"],
                    parse_decimal(v["prix_vente"]), bool(v["ordonnance_obligatoire"]),
                    int(v["seuil_min"] or 0))
            except ValueError:
                messagebox.showwarning("Saisie", "Le prix et le seuil doivent être des nombres.",
                                       parent=dialogue)
                return False
            ok, _ = essayer(dialogue, action, saisie)
            return ok

        dialogue = FormulaireDialog(self, titre, self.CHAMPS, valeurs, enregistrer)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()

    def nouveau(self):
        self._formulaire("Nouveau médicament", {"seuil_min": 10},
                         lambda s: stock_service.creer_medicament(self.user, s))

    def modifier(self):
        id_med = self._selection()
        if id_med is None:
            return
        m = self.medicaments[id_med]
        valeurs = dict(m, prix_vente=fmt_montant(m["prix_vente"]).replace(" ", ""))
        self._formulaire("Modifier le médicament", valeurs,
                         lambda s: stock_service.modifier_medicament(self.user, id_med, s))

    def basculer(self):
        id_med = self._selection()
        if id_med is None:
            return
        actif = bool(self.medicaments[id_med]["actif"])
        ok, _ = essayer(self, stock_service.changer_statut_medicament, self.user, id_med, not actif)
        if ok:
            self.actualiser()


class StockView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=4)
        onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True)
        onglets.add(EtatStockPanel(onglets, user), text="État du stock")
        onglets.add(LotsPanel(onglets, user), text="Lots")
        if can(user.role, "gerer_catalogue"):
            onglets.add(CataloguePanel(onglets, user), text="Catalogue")
