"""Tableau de bord : chiffres clés, alertes, meilleures ventes.

Le pharmacien et l'administrateur voient tout. Le personnel de caisse ne voit
que les chiffres et les ventes du jour (droits réduits).
"""
import tkinter as tk
from tkinter import ttk

from core.formatting import fmt_date, fmt_montant
from core.permissions import can
from services import stats_service, vente_service
from ui.messages import essayer
from ui.widgets import Tableau, creer_carte


class DashboardView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=10)
        self.user = user
        self.complet = can(user.role, "stats_completes")

        haut = ttk.Frame(self)
        haut.pack(fill="x")
        ttk.Label(haut, text="Tableau de bord", style="Titre.TLabel").pack(side="left")
        ttk.Button(haut, text="Actualiser", command=self.actualiser).pack(side="right")

        # --- cartes de chiffres clés ---
        cartes = ttk.Frame(self)
        cartes.pack(fill="x", pady=10)
        definitions = [("ca_du_jour", "Chiffre d'affaires du jour"), ("ventes_du_jour", "Ventes du jour")]
        if self.complet:
            definitions += [
                ("medicaments_en_alerte", "Médicaments en alerte"),
                ("lots_a_surveiller", "Lots à surveiller"),
                ("ordonnances_ouvertes", "Ordonnances ouvertes"),
            ]
        self.valeurs = {}
        for i, (cle, titre) in enumerate(definitions):
            self.valeurs[cle] = tk.StringVar(value="–")
            creer_carte(cartes, titre, self.valeurs[cle]).grid(row=0, column=i, padx=6, sticky="nsew")
            cartes.columnconfigure(i, weight=1)

        # --- tableaux ---
        zone = ttk.Frame(self)
        zone.pack(fill="both", expand=True)
        zone.columnconfigure(0, weight=1)
        zone.columnconfigure(1, weight=1)
        if self.complet:
            zone.rowconfigure(0, weight=1)
            zone.rowconfigure(1, weight=1)
            self.t_rupture = self._table(zone, 0, 0, "Médicaments sous le seuil d'alerte", [
                ("nom", "Médicament", 180, "w"), ("stock", "Stock", 60, "e"),
                ("seuil", "Seuil", 60, "e"), ("manque", "Manquant", 70, "e")])
            self.t_peremption = self._table(zone, 0, 1, "Lots périmés ou proches de la péremption", [
                ("nom", "Médicament", 150, "w"), ("lot", "Lot", 90, "w"),
                ("date", "Péremption", 85, "center"), ("jours", "Jours", 50, "e"),
                ("valeur", "Valeur", 80, "e")])
            self.t_top = self._table(zone, 1, 0, "Top des médicaments vendus", [
                ("nom", "Médicament", 180, "w"), ("qte", "Quantité", 70, "e"),
                ("ca", "Chiffre d'affaires", 110, "e")])
            self.t_ca = self._table(zone, 1, 1, "Chiffre d'affaires par jour", [
                ("jour", "Jour", 90, "center"), ("nb", "Ventes", 60, "e"),
                ("ca", "Chiffre d'affaires", 110, "e"), ("panier", "Panier moyen", 90, "e")])
        else:
            zone.rowconfigure(0, weight=1)
            self.t_jour = self._table(zone, 0, 0, "Ventes d'aujourd'hui", [
                ("id", "N°", 50, "e"), ("heure", "Heure", 70, "center"),
                ("vendeur", "Vendeur", 150, "w"), ("paiement", "Paiement", 100, "w"),
                ("total", "Total", 90, "e"), ("statut", "Statut", 80, "w")], colspan=2)
        self.actualiser()

    @staticmethod
    def _table(parent, ligne, colonne, titre, colonnes, colspan=1):
        cadre = ttk.LabelFrame(parent, text=titre, padding=6)
        cadre.grid(row=ligne, column=colonne, columnspan=colspan, sticky="nsew", padx=4, pady=4)
        arbre = Tableau(cadre, columns=[c[0] for c in colonnes], show="headings", height=6)
        for cle, libelle, largeur, ancre in colonnes:
            arbre.heading(cle, text=libelle)
            arbre.column(cle, width=largeur, anchor=ancre)
        defil = ttk.Scrollbar(cadre, orient="vertical", command=arbre.yview)
        arbre.configure(yscrollcommand=defil.set)
        arbre.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        return arbre

    @staticmethod
    def _remplir(arbre, lignes):
        arbre.delete(*arbre.get_children())
        for valeurs in lignes:
            arbre.insert("", "end", values=valeurs)

    def actualiser(self):
        ok, k = essayer(self, stats_service.kpis_jour, self.user)
        if not ok:
            return
        self.valeurs["ca_du_jour"].set(fmt_montant(k["ca_du_jour"]))
        self.valeurs["ventes_du_jour"].set(str(k["ventes_du_jour"]))

        if not self.complet:
            ok, ventes = essayer(self, vente_service.ventes_du_jour, self.user)
            if ok:
                self._remplir(self.t_jour, [
                    (v["id_vente"], v["date_vente"].strftime("%H:%M"), v["vendeur"],
                     vente_service.MODES_PAIEMENT.get(v["mode_paiement"], v["mode_paiement"]),
                     fmt_montant(v["total"]),
                     "Validée" if v["statut"] == "validee" else "Annulée")
                    for v in ventes])
            return

        self.valeurs["medicaments_en_alerte"].set(str(k["medicaments_en_alerte"]))
        self.valeurs["lots_a_surveiller"].set(str(k["lots_a_surveiller"]))
        self.valeurs["ordonnances_ouvertes"].set(str(k["ordonnances_ouvertes"]))

        ok, rupture = essayer(self, stats_service.alertes_rupture, self.user)
        if ok:
            self._remplir(self.t_rupture, [
                (r["nom_commercial"], r["stock_disponible"], r["seuil_min"], r["quantite_manquante"])
                for r in rupture])
        ok, perem = essayer(self, stats_service.alertes_peremption, self.user)
        if ok:
            self._remplir(self.t_peremption, [
                (p["nom_commercial"], p["numero_lot"], fmt_date(p["date_peremption"]),
                 p["jours_restants"], fmt_montant(p["valeur_stock_concerne"]))
                for p in perem])
        ok, top = essayer(self, stats_service.top_medicaments, self.user)
        if ok:
            self._remplir(self.t_top, [
                (t["nom_commercial"], t["quantite_vendue"], fmt_montant(t["chiffre_affaires"]))
                for t in top])
        ok, ca = essayer(self, stats_service.ca_par_jour, self.user)
        if ok:
            self._remplir(self.t_ca, [
                (fmt_date(c["jour"]), c["nb_ventes"], fmt_montant(c["chiffre_affaires"]),
                 fmt_montant(c["panier_moyen"])) for c in ca])
