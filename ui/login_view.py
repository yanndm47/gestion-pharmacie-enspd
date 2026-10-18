"""Écran de connexion."""
import tkinter as tk
from tkinter import ttk

import config
from services import auth_service
from ui.messages import essayer


class LoginView(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success

        centre = ttk.Frame(self, padding=30)
        centre.place(relx=0.5, rely=0.42, anchor="center")

        ttk.Label(centre, text=config.APP_TITLE, font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )
        ttk.Label(centre, text="Identifiant").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(centre, text="Mot de passe").grid(row=2, column=0, sticky="e", padx=6, pady=6)

        self.var_login = tk.StringVar()
        self.var_mdp = tk.StringVar()
        self.entree_login = ttk.Entry(centre, textvariable=self.var_login, width=28)
        self.entree_mdp = ttk.Entry(centre, textvariable=self.var_mdp, width=28, show="•")
        self.entree_login.grid(row=1, column=1, pady=6)
        self.entree_mdp.grid(row=2, column=1, pady=6)

        ttk.Button(centre, text="Se connecter", command=self._connecter).grid(
            row=3, column=0, columnspan=2, pady=(16, 0), ipadx=12
        )

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
