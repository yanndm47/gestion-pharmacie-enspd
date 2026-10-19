"""Écran de connexion : panneau bleu ENSPD à gauche, formulaire à droite."""
import tkinter as tk
from tkinter import ttk

import config
from services import auth_service
from ui import theme
from ui.messages import essayer


class LoginView(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.columnconfigure(0, weight=2, uniform="login")
        self.columnconfigure(1, weight=3, uniform="login")
        self.rowconfigure(0, weight=1)

        # --- panneau d'identité (bleu, accents jaunes) ---
        panneau = ttk.Frame(self, style="Panneau.TFrame", padding=40)
        panneau.grid(row=0, column=0, sticky="nsew")
        panneau.rowconfigure(0, weight=1)
        panneau.rowconfigure(2, weight=1)
        panneau.columnconfigure(0, weight=1)
        centre = ttk.Frame(panneau, style="Panneau.TFrame")
        centre.grid(row=1, column=0)
        embleme = tk.Canvas(centre, width=120, height=120, background=theme.BLEU, highlightthickness=0)
        embleme.create_oval(6, 6, 114, 114, fill=theme.JAUNE, outline="")
        embleme.create_rectangle(50, 26, 70, 94, fill=theme.BLEU, outline="")     # croix de pharmacie
        embleme.create_rectangle(26, 50, 94, 70, fill=theme.BLEU, outline="")
        embleme.pack(pady=(0, 18))
        ttk.Label(centre, text=config.ECOLE_SIGLE, style="PanneauTitre.TLabel").pack()
        ttk.Label(centre, text=config.ECOLE_NOM, style="PanneauTexte.TLabel", wraplength=300,
                  justify="center").pack(pady=(4, 18))
        ttk.Frame(centre, style="Jaune.TFrame", height=3, width=80).pack(pady=(0, 18))
        ttk.Label(centre, text=config.APP_SOUS_TITRE, style="PanneauJaune.TLabel").pack()
        ttk.Label(centre, text=f"Projet de groupe · {config.MATIERE}", style="PanneauTexte.TLabel").pack(pady=(4, 0))
        ttk.Label(panneau, text=f"Version {config.APP_VERSION}", style="PanneauTexte.TLabel").grid(
            row=2, column=0, sticky="s")

        # --- formulaire ---
        droite = ttk.Frame(self)
        droite.grid(row=0, column=1, sticky="nsew")
        droite.rowconfigure(0, weight=1)
        droite.columnconfigure(0, weight=1)
        carte = ttk.Frame(droite, style="Carte.TFrame")
        carte.grid(row=0, column=0)
        ttk.Frame(carte, style="Jaune.TFrame", height=5).pack(fill="x")
        corps = ttk.Frame(carte, style="Carte.TFrame", padding=(44, 30))
        corps.pack()
        ttk.Label(corps, text="Connexion", style="CarteValeur.TLabel").pack(anchor="w")
        ttk.Label(corps, text="Identifiez-vous pour accéder à l'application.", style="CarteTitre.TLabel").pack(
            anchor="w", pady=(2, 18))

        self.var_login = tk.StringVar()
        self.var_mdp = tk.StringVar()
        ttk.Label(corps, text="Identifiant", style="Carte.TLabel").pack(anchor="w")
        self.entree_login = ttk.Entry(corps, textvariable=self.var_login, width=34)
        self.entree_login.pack(fill="x", pady=(2, 12))
        ttk.Label(corps, text="Mot de passe", style="Carte.TLabel").pack(anchor="w")
        self.entree_mdp = ttk.Entry(corps, textvariable=self.var_mdp, width=34, show="•")
        self.entree_mdp.pack(fill="x", pady=(2, 20))
        ttk.Button(corps, text="Se connecter", style="Accent.TButton", command=self._connecter).pack(
            fill="x", ipady=4)

        for entree in (self.entree_login, self.entree_mdp):
            entree.bind("<Return>", lambda _e: self._connecter())
        self.entree_login.focus_set()

    def _connecter(self):
        ok, utilisateur = essayer(
            self, auth_service.connecter, self.var_login.get(), self.var_mdp.get()
        )
        if ok:
            self.on_success(utilisateur)
        else:
            self.var_mdp.set("")
            self.entree_mdp.focus_set()
