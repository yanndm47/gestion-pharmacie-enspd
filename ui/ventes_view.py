"""Historique des ventes : détail, ticket et annulation (annulation réservée au pharmacien)."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.formatting import fmt_montant
from core.permissions import can
from services import vente_service
from services.vente_service import MODES_PAIEMENT, PERIODES
from ui.messages import essayer
from ui.ticket_view import TicketDialog
from ui.widgets import creer_arbre, vider


class VentesView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.peut_annuler = can(user.role, "annuler_vente")
        self.peut_historique = can(user.role, "stats_completes")
        self.ventes = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)

        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.combo_periode = ttk.Combobox(barre, state="readonly", values=list(PERIODES), width=20)
        self.combo_periode.current(0)
        self.combo_periode.pack(side="left")
        self.combo_periode.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        if not self.peut_historique:
            self.combo_periode.configure(state="disabled")      # droits réduits : aujourd'hui seulement
        self.statuts = {"Toutes": None, "Validées": "validee", "Annulées": "annulee"}
        self.combo_statut = ttk.Combobox(barre, state="readonly", values=list(self.statuts), width=12)
        self.combo_statut.current(0)
        self.combo_statut.pack(side="left", padx=6)
        self.combo_statut.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Voir le ticket", command=self.voir_ticket).pack(side="left", padx=(10, 4))
        if self.peut_annuler:
            ttk.Button(barre, text="Annuler la vente", command=self.annuler).pack(side="left", padx=4)
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="right")

        cadre = ttk.LabelFrame(self, text="Ventes", padding=6)
        cadre.grid(row=1, column=0, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)
        liste = creer_arbre(cadre, [
            ("id", "N°", 60, "e"), ("date", "Date", 130, "center"), ("vendeur", "Vendeur", 150, "w"),
            ("client", "Client", 150, "w"), ("paiement", "Paiement", 100, "w"), ("total", "Total", 90, "e"),
            ("ordo", "Ordonnance", 90, "center"), ("statut", "Statut", 80, "w")])
        liste.grid(row=0, column=0, sticky="nsew")
        self.arbre = liste.arbre
        self.arbre.tag_configure("annulee", foreground="#9ca3af")
        self.arbre.bind("<<TreeviewSelect>>", lambda _e: self._afficher_detail())
        self.arbre.bind("<Double-1>", lambda _e: self.voir_ticket())

        cadre_d = ttk.LabelFrame(self, text="Détail de la vente", padding=6)
        cadre_d.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        cadre_d.columnconfigure(0, weight=1)
        cadre_d.rowconfigure(0, weight=1)
        detail = creer_arbre(cadre_d, [
            ("nom", "Médicament", 240, "w"), ("lot", "Lot", 110, "w"), ("qte", "Quantité", 70, "e"),
            ("prix", "Prix unitaire", 90, "e"), ("sous", "Sous-total", 90, "e")], height=5)
        detail.grid(row=0, column=0, sticky="nsew")
        self.arbre_detail = detail.arbre
        self.actualiser()

    def actualiser(self):
        jours = PERIODES[self.combo_periode.get()]
        ok, lignes = essayer(self, vente_service.lister_ventes, self.user, jours,
                             self.statuts[self.combo_statut.get()])
        if not ok:
            return
        self.ventes = {v["id_vente"]: v for v in lignes}
        vider(self.arbre)
        vider(self.arbre_detail)
        for v in lignes:
            self.arbre.insert("", "end", iid=str(v["id_vente"]), tags=(v["statut"],), values=(
                v["id_vente"], v["date_vente"].strftime("%d/%m/%Y %H:%M"), v["vendeur"], v["client"] or "",
                MODES_PAIEMENT.get(v["mode_paiement"], v["mode_paiement"]), fmt_montant(v["total"]),
                v["id_ordonnance"] or "", "Validée" if v["statut"] == "validee" else "Annulée"))

    def _selection(self, message=True):
        sel = self.arbre.selection()
        if not sel:
            if message:
                messagebox.showinfo("Ventes", "Sélectionnez d'abord une vente.", parent=self)
            return None
        return int(sel[0])

    def _afficher_detail(self):
        vider(self.arbre_detail)
        id_vente = self._selection(message=False)
        if id_vente is None:
            return
        ok, detail = essayer(self, vente_service.detail_vente, self.user, id_vente)
        if not ok:
            return
        for l in detail["lignes"]:
            self.arbre_detail.insert("", "end", values=(
                l["nom_commercial"], l["numero_lot"], l["quantite"],
                fmt_montant(l["prix_unitaire"]), fmt_montant(l["sous_total"])))

    def voir_ticket(self):
        id_vente = self._selection()
        if id_vente is None:
            return
        ok, texte = essayer(self, vente_service.texte_ticket, self.user, id_vente)
        if ok:
            TicketDialog(self, id_vente, texte)

    def annuler(self):
        id_vente = self._selection()
        if id_vente is None:
            return
        if self.ventes[id_vente]["statut"] == "annulee":
            messagebox.showinfo("Ventes", "Cette vente est déjà annulée.", parent=self)
            return
        if not messagebox.askyesno(
                "Annuler la vente",
                f"Annuler la vente n°{id_vente} ?\nLes quantités seront remises en stock. "
                "Cette action est définitive.", parent=self):
            return
        ok, _ = essayer(self, vente_service.annuler_vente, self.user, id_vente)
        if ok:
            self.actualiser()
