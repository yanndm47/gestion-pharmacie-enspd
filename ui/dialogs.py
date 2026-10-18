"""Fenêtres de dialogue réutilisables."""
import tkinter as tk
from tkinter import ttk

from services import client_service
from ui.messages import essayer


class NouveauClientDialog(tk.Toplevel):
    """Petite fenêtre de création d'un client. `resultat` contient le client créé, ou None."""

    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Nouveau client")
        self.resizable(False, False)
        self.user = user
        self.resultat = None
        self.transient(parent.winfo_toplevel())

        cadre = ttk.Frame(self, padding=16)
        cadre.pack()
        self.vars = {c: tk.StringVar() for c in ("nom", "prenom", "naissance", "telephone")}
        libelles = [("nom", "Nom *"), ("prenom", "Prénom *"),
                    ("naissance", "Date de naissance * (JJ/MM/AAAA)"), ("telephone", "Téléphone")]
        for i, (cle, libelle) in enumerate(libelles):
            ttk.Label(cadre, text=libelle).grid(row=i, column=0, sticky="e", padx=6, pady=5)
            ttk.Entry(cadre, textvariable=self.vars[cle], width=26).grid(row=i, column=1, pady=5)
        boutons = ttk.Frame(cadre)
        boutons.grid(row=len(libelles), column=0, columnspan=2, pady=(12, 0))
        ttk.Button(boutons, text="Créer", command=self._creer).pack(side="left", padx=4)
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda _e: self._creer())
        self.bind("<Escape>", lambda _e: self.destroy())
        try:
            self.grab_set()   # rend la fenêtre modale (peut échouer sur certains systèmes)
        except tk.TclError:
            pass

    def _creer(self):
        v = {c: var.get() for c, var in self.vars.items()}
        ok, id_client = essayer(
            self, client_service.creer_client, self.user,
            v["nom"], v["prenom"], v["naissance"], v["telephone"],
        )
        if ok:
            self.resultat = {"id_client": id_client, "nom": v["nom"].strip(),
                             "prenom": v["prenom"].strip()}
            self.destroy()


class FormulaireDialog(tk.Toplevel):
    """Formulaire générique : une ligne par champ, un bouton Enregistrer.

    champs     : liste de (cle, libelle, type) avec type = "texte", "bool", "mdp" (saisie masquée)
                 ou ("choix", [valeurs]) (liste déroulante)
    valeurs    : valeurs initiales {cle: valeur}
    enregistrer: fonction(dialogue, valeurs_dict) -> bool ; renvoyer True ferme la fenêtre.
                 Elle appelle le service avec essayer(dialogue, ...) pour afficher les erreurs.
    `resultat` vaut True si l'enregistrement a réussi.
    """

    def __init__(self, parent, titre, champs, valeurs=None, enregistrer=None):
        super().__init__(parent)
        self.title(titre)
        self.resizable(False, False)
        self.resultat = False
        self._enregistrer = enregistrer
        self.transient(parent.winfo_toplevel())
        valeurs = valeurs or {}

        cadre = ttk.Frame(self, padding=16)
        cadre.pack()
        self.vars = {}
        for i, (cle, libelle, genre) in enumerate(champs):
            if genre == "bool":
                var = tk.BooleanVar(value=bool(valeurs.get(cle, False)))
                ttk.Checkbutton(cadre, text=libelle, variable=var).grid(
                    row=i, column=0, columnspan=2, sticky="w", pady=5)
            else:
                brut = valeurs.get(cle)
                var = tk.StringVar(value="" if brut is None else str(brut))
                ttk.Label(cadre, text=libelle).grid(row=i, column=0, sticky="e", padx=6, pady=5)
                if isinstance(genre, tuple) and genre[0] == "choix":
                    ttk.Combobox(cadre, textvariable=var, state="readonly", width=31,
                                 values=list(genre[1])).grid(row=i, column=1, sticky="w", pady=5)
                elif genre == "mdp":
                    ttk.Entry(cadre, textvariable=var, width=34, show="•").grid(row=i, column=1, pady=5)
                else:
                    ttk.Entry(cadre, textvariable=var, width=34).grid(row=i, column=1, pady=5)
            self.vars[cle] = var
        boutons = ttk.Frame(cadre)
        boutons.grid(row=len(champs), column=0, columnspan=2, pady=(12, 0))
        ttk.Button(boutons, text="Enregistrer", command=self._valider).pack(side="left", padx=4)
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda _e: self._valider())
        self.bind("<Escape>", lambda _e: self.destroy())
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _valider(self):
        valeurs = {cle: var.get() for cle, var in self.vars.items()}
        if self._enregistrer(self, valeurs):
            self.resultat = True
            self.destroy()
