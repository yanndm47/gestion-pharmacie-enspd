"""Page Crédits : école, projet, équipe et informations techniques (visible par tous les profils)."""
from tkinter import ttk

import config
from services import info_service


class CreditsView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=(24, 18))
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="Crédits", style="Titre.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=f"{config.ECOLE_SIGLE} · {config.ECOLE_NOM}", style="Sous.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(self, text=f"{config.APP_SOUS_TITRE} – projet de groupe de la matière {config.MATIERE}",
                  style="Sous.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 14))

        equipe = ttk.LabelFrame(self, text="Équipe du projet", padding=14)
        equipe.grid(row=3, column=0, sticky="ew")
        equipe.columnconfigure(0, weight=1)
        equipe.columnconfigure(1, weight=1)
        for i, nom in enumerate(config.EQUIPE):
            carte = ttk.Frame(equipe, style="Carte.TFrame")
            carte.grid(row=i // 2, column=i % 2, sticky="ew", padx=6, pady=5)
            ttk.Frame(carte, style="Jaune.TFrame", width=6).pack(side="left", fill="y")
            ttk.Label(carte, text=nom, style="Carte.TLabel", padding=(14, 10)).pack(side="left")

        bas = ttk.Frame(self)
        bas.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        bas.columnconfigure(0, weight=1)
        bas.columnconfigure(1, weight=1)

        techno = ttk.LabelFrame(bas, text="Technologies", padding=12)
        techno.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(techno, text="Python et Tkinter · MySQL (WampServer) · DBeaver\n"
                               "Méthode Merise : MCD, MLD, règles de gestion, triggers",
                  justify="left").pack(anchor="w")

        info = info_service.informations()
        technique = ttk.LabelFrame(bas, text="Informations techniques", padding=12)
        technique.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(technique, justify="left", text=(
            f"Application : version {info['application']}\n"
            f"Python : {info['python']}\n"
            f"Serveur de base : {info['serveur']}\n"
            f"Base : {info['base']}")).pack(anchor="w")
        ttk.Label(self, style="Sous.TLabel", text=f"{config.ECOLE_SIGLE} – tous droits réservés à l'équipe du projet."
                  ).grid(row=5, column=0, sticky="w", pady=(14, 0))
