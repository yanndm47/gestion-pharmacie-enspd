"""Module Clients : fiches complètes et historique (l'historique est réservé au pharmacien)."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.formatting import fmt_date, fmt_montant
from core.permissions import can
from services import client_service
from services.ordonnance_service import STATUTS as STATUTS_ORDONNANCE
from services.vente_service import MODES_PAIEMENT
from ui.dialogs import FormulaireDialog
from ui.messages import essayer
from ui.widgets import creer_arbre, vider


class ClientsView(ttk.Frame):
    CHAMPS = [("nom", "Nom *", "texte"), ("prenom", "Prénom *", "texte"),
              ("date_naissance", "Date de naissance * (JJ/MM/AAAA)", "texte"),
              ("telephone", "Téléphone", "texte"), ("email", "Email", "texte"),
              ("adresse", "Adresse", "texte")]

    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.clients = {}
        self.avec_historique = can(user.role, "gerer_ordonnances")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)

        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        barre.columnconfigure(1, weight=1)
        ttk.Label(barre, text="Rechercher :").grid(row=0, column=0, padx=(0, 6))
        self.var_terme = tk.StringVar()
        entree = ttk.Entry(barre, textvariable=self.var_terme)
        entree.grid(row=0, column=1, sticky="ew")
        entree.bind("<Return>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Rechercher", command=self.actualiser).grid(row=0, column=2, padx=6)
        ttk.Button(barre, text="Nouveau client", command=self.nouveau).grid(row=0, column=3)
        ttk.Button(barre, text="Modifier", command=self.modifier).grid(row=0, column=4, padx=(6, 0))

        cadre = ttk.LabelFrame(self, text="Clients", padding=6)
        cadre.grid(row=1, column=0, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)
        liste = creer_arbre(cadre, [
            ("nom", "Nom", 150, "w"), ("prenom", "Prénom", 130, "w"), ("naissance", "Né(e) le", 90, "center"),
            ("tel", "Téléphone", 110, "w"), ("email", "Email", 190, "w"), ("adresse", "Adresse", 200, "w")])
        liste.grid(row=0, column=0, sticky="nsew")
        self.arbre = liste.arbre
        self.arbre.bind("<<TreeviewSelect>>", lambda _e: self._afficher_historique())

        if self.avec_historique:
            onglets = ttk.Notebook(self)
            onglets.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
            achats = creer_arbre(onglets, [
                ("id", "N° vente", 70, "e"), ("date", "Date", 130, "center"), ("vendeur", "Vendeur", 160, "w"),
                ("paiement", "Paiement", 100, "w"), ("total", "Total", 90, "e"), ("statut", "Statut", 80, "w"),
                ("ordo", "Ordonnance", 90, "center")], height=5)
            ordos = creer_arbre(onglets, [
                ("id", "N°", 60, "e"), ("date", "Prescrite le", 100, "center"),
                ("validite", "Valable jusqu'au", 120, "center"), ("medecin", "Médecin", 200, "w"),
                ("statut", "Statut", 100, "w")], height=5)
            onglets.add(achats, text="Historique des achats")
            onglets.add(ordos, text="Historique des ordonnances")
            self.arbre_achats, self.arbre_ordos = achats.arbre, ordos.arbre
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, client_service.lister_clients, self.user, self.var_terme.get())
        if not ok:
            return
        self.clients = {c["id_client"]: c for c in lignes}
        vider(self.arbre)
        for c in lignes:
            self.arbre.insert("", "end", iid=str(c["id_client"]), values=(
                c["nom"], c["prenom"], fmt_date(c["date_naissance"]), c["telephone"] or "",
                c["email"] or "", c["adresse"] or ""))
        if self.avec_historique:
            vider(self.arbre_achats)
            vider(self.arbre_ordos)

    def _afficher_historique(self):
        if not self.avec_historique:
            return
        vider(self.arbre_achats)
        vider(self.arbre_ordos)
        sel = self.arbre.selection()
        if not sel:
            return
        id_client = int(sel[0])
        ok, achats = essayer(self, client_service.historique_achats, self.user, id_client)
        if ok:
            for v in achats:
                self.arbre_achats.insert("", "end", values=(
                    v["id_vente"], v["date_vente"].strftime("%d/%m/%Y %H:%M"), v["vendeur"],
                    MODES_PAIEMENT.get(v["mode_paiement"], v["mode_paiement"]), fmt_montant(v["total"]),
                    "Validée" if v["statut"] == "validee" else "Annulée", v["id_ordonnance"] or ""))
        ok, ordos = essayer(self, client_service.historique_ordonnances, self.user, id_client)
        if ok:
            for o in ordos:
                self.arbre_ordos.insert("", "end", values=(
                    o["id_ordonnance"], fmt_date(o["date_prescription"]), fmt_date(o["date_validite"]),
                    o["nom_medecin"], STATUTS_ORDONNANCE.get(o["statut"], o["statut"])))

    def _formulaire(self, titre, valeurs, action):
        def enregistrer(dialogue, v):
            ok, _ = essayer(dialogue, action, v["nom"], v["prenom"], v["date_naissance"],
                            v["telephone"], v["email"], v["adresse"])
            return ok

        dialogue = FormulaireDialog(self, titre, self.CHAMPS, valeurs, enregistrer)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()

    def nouveau(self):
        self._formulaire("Nouveau client", {},
                         lambda *a: client_service.creer_client(self.user, *a))

    def modifier(self):
        sel = self.arbre.selection()
        if not sel:
            messagebox.showinfo("Clients", "Sélectionnez d'abord un client.", parent=self)
            return
        id_client = int(sel[0])
        valeurs = dict(self.clients[id_client])
        valeurs["date_naissance"] = fmt_date(valeurs["date_naissance"])
        self._formulaire("Modifier le client", valeurs,
                         lambda *a: client_service.modifier_client(self.user, id_client, *a))
