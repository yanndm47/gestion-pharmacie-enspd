"""Fenêtre racine : alterne entre l'écran de connexion et la fenêtre principale."""
import sys
import tkinter as tk
from tkinter import ttk

import config
from ui.login_view import LoginView
from services import maintenance_service
from ui.main_window import MainWindow


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry("1180x720")
        self.minsize(980, 620)
        try:
            ttk.Style(self).theme_use("clam")
        except tk.TclError:
            pass
        self._contenu = None
        self.afficher_login()

    def _remplacer(self, vue):
        if self._contenu is not None:
            self._contenu.destroy()
        self._contenu = vue
        vue.pack(fill="both", expand=True)

    def afficher_login(self):
        self._remplacer(LoginView(self, on_success=self.afficher_principal))

    def afficher_principal(self, utilisateur):
        # Met à jour les lots périmés et les ordonnances expirées à chaque connexion.
        # Un échec ne doit pas empêcher de travailler : on le signale dans la console.
        try:
            maintenance_service.executer_maintenance()
        except Exception as erreur:
            print(f"Maintenance quotidienne impossible : {erreur}", file=sys.stderr)
        self._remplacer(MainWindow(self, utilisateur, on_logout=self.afficher_login))
