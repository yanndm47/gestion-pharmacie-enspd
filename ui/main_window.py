"""Fenêtre principale : les onglets affichés dépendent du rôle de l'utilisateur."""
from tkinter import messagebox, ttk

import config
from core.permissions import can
from services import auth_service
from ui.caisse_view import CaisseView
from ui.clients_view import ClientsView
from ui.commandes_view import CommandesView
from ui.comptes_view import ComptesView
from ui.credits_view import CreditsView
from ui.dashboard_view import DashboardView
from ui.dialogs import FormulaireDialog
from ui.messages import essayer
from ui.ordonnances_view import OrdonnancesView
from ui.statistiques_view import StatistiquesView
from ui.stock_view import StockView
from ui.ventes_view import VentesView


class MainWindow(ttk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user

        entete = ttk.Frame(self, style="Entete.TFrame", padding=(18, 10))
        entete.pack(fill="x")
        ttk.Label(entete, text=config.ECOLE_SIGLE, style="Sigle.TLabel").pack(side="left")
        ttk.Label(entete, text=f"  |  {config.APP_SOUS_TITRE}", style="Entete.TLabel").pack(side="left")
        ttk.Button(entete, text="Se déconnecter", style="Entete.TButton", command=on_logout).pack(side="right")
        ttk.Button(entete, text="Mon mot de passe", style="Entete.TButton",
                   command=self.changer_mot_de_passe).pack(side="right", padx=8)
        ttk.Label(entete, text=f"{user.nom_complet}  ·  {user.role_libelle}", style="Entete.TLabel").pack(
            side="right", padx=14)
        ttk.Frame(self, style="Jaune.TFrame", height=4).pack(fill="x")

        self.onglets = ttk.Notebook(self)
        self.onglets.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self._construire_onglets()

    def changer_mot_de_passe(self):
        champs = [("ancien", "Mot de passe actuel *", "mdp"),
                  ("nouveau", "Nouveau mot de passe * (8 car. min.)", "mdp"),
                  ("confirmation", "Confirmation *", "mdp")]

        def enregistrer(dialogue, v):
            if v["nouveau"] != v["confirmation"]:
                messagebox.showwarning("Mot de passe", "Les deux saisies sont différentes.", parent=dialogue)
                return False
            ok, _ = essayer(dialogue, auth_service.changer_mot_de_passe, self.user, v["ancien"], v["nouveau"])
            if ok:
                messagebox.showinfo("Mot de passe", "Votre mot de passe a été changé.", parent=dialogue)
            return ok

        dialogue = FormulaireDialog(self, "Changer mon mot de passe", champs, {}, enregistrer)
        self.wait_window(dialogue)

    def _ajouter(self, titre, vue):
        self.onglets.add(vue, text=titre)

    def _construire_onglets(self):
        u, nb = self.user, self.onglets

        # Un onglet par module : il n'apparaît que si le rôle en a le droit.
        if can(u.role, "stats_jour"):
            self._ajouter("Tableau de bord", DashboardView(nb, u))
        if can(u.role, "vendre_libre"):
            self._ajouter("Caisse", CaisseView(nb, u))
        if can(u.role, "stats_jour"):
            self._ajouter("Ventes", VentesView(nb, u))

        if can(u.role, "consulter_catalogue"):
            self._ajouter("Stock", StockView(nb, u))
        if can(u.role, "gerer_clients"):
            self._ajouter("Clients", ClientsView(nb, u))
        if can(u.role, "gerer_ordonnances"):
            self._ajouter("Ordonnances", OrdonnancesView(nb, u))
        if can(u.role, "gerer_fournisseurs"):
            self._ajouter("Commandes", CommandesView(nb, u))
        if can(u.role, "stats_completes"):
            self._ajouter("Statistiques", StatistiquesView(nb, u))
        if can(u.role, "gerer_comptes"):
            self._ajouter("Comptes", ComptesView(nb, u))
        # La page Crédits est visible par tous les profils.
        self._ajouter("Crédits", CreditsView(nb, u))
