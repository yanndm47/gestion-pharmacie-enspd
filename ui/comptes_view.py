"""Module Comptes : gestion du personnel (administrateur uniquement)."""
from tkinter import messagebox, ttk

from core.formatting import fmt_date
from core.permissions import ROLE_LABELS, ROLES
from services import personnel_service
from ui.dialogs import FormulaireDialog
from ui.messages import essayer
from ui.widgets import creer_arbre, vider

LIBELLE_VERS_ROLE = {libelle: role for role, libelle in ROLE_LABELS.items()}
LIBELLES_ROLES = [ROLE_LABELS[r] for r in ROLES]


class ComptesView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.comptes = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(barre, text="Nouveau compte", style="Primary.TButton", command=self.nouveau).pack(side="left")
        ttk.Button(barre, text="Modifier", command=self.modifier).pack(side="left", padx=6)
        ttk.Button(barre, text="Désactiver / Réactiver", command=self.basculer).pack(side="left")
        ttk.Button(barre, text="Réinitialiser le mot de passe", command=self.reinitialiser).pack(side="left", padx=6)
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="right")

        cadre = creer_arbre(self, [
            ("nom", "Nom", 150, "w"), ("prenom", "Prénom", 130, "w"), ("login", "Identifiant", 120, "w"),
            ("role", "Rôle", 140, "w"), ("tel", "Téléphone", 110, "w"), ("embauche", "Embauché le", 100, "center"),
            ("actif", "Actif", 50, "center")])
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = cadre.arbre
        self.arbre.tag_configure("inactif", foreground="#9ca3af")
        ttk.Label(self, foreground="#6b7280", wraplength=800, justify="left", text=(
            "Un compte n'est jamais supprimé (il reste lié à l'historique des ventes) : on le désactive. "
            "Il doit toujours rester au moins un administrateur actif. Mot de passe : 8 caractères minimum."
        )).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, personnel_service.lister_personnel, self.user)
        if not ok:
            return
        self.comptes = {c["id_personnel"]: c for c in lignes}
        vider(self.arbre)
        for c in lignes:
            self.arbre.insert("", "end", iid=str(c["id_personnel"]),
                              tags=() if c["actif"] else ("inactif",), values=(
                c["nom"], c["prenom"], c["login"], ROLE_LABELS.get(c["role"], c["role"]),
                c["telephone"] or "", fmt_date(c["date_embauche"]), "Oui" if c["actif"] else "Non"))

    def _selection(self):
        sel = self.arbre.selection()
        if not sel:
            messagebox.showinfo("Comptes", "Sélectionnez d'abord un compte.", parent=self)
            return None
        return int(sel[0])

    def _ouvrir(self, titre, champs, valeurs, action):
        dialogue = FormulaireDialog(self, titre, champs, valeurs, action)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()

    def nouveau(self):
        champs = [("nom", "Nom *", "texte"), ("prenom", "Prénom *", "texte"),
                  ("login", "Identifiant de connexion *", "texte"),
                  ("mot_de_passe", "Mot de passe * (8 caractères min.)", "mdp"),
                  ("role", "Rôle *", ("choix", LIBELLES_ROLES)), ("telephone", "Téléphone", "texte")]

        def enregistrer(dialogue, v):
            if v["role"] not in LIBELLE_VERS_ROLE:
                messagebox.showwarning("Compte", "Choisissez un rôle.", parent=dialogue)
                return False
            ok, _ = essayer(dialogue, personnel_service.creer_compte, self.user, v["nom"], v["prenom"],
                            v["login"], v["mot_de_passe"], LIBELLE_VERS_ROLE[v["role"]], v["telephone"])
            return ok

        self._ouvrir("Nouveau compte", champs, {"role": ROLE_LABELS["caissier"]}, enregistrer)

    def modifier(self):
        id_p = self._selection()
        if id_p is None:
            return
        c = self.comptes[id_p]
        champs = [("nom", "Nom *", "texte"), ("prenom", "Prénom *", "texte"),
                  ("role", "Rôle *", ("choix", LIBELLES_ROLES)), ("telephone", "Téléphone", "texte")]
        valeurs = {"nom": c["nom"], "prenom": c["prenom"], "telephone": c["telephone"],
                   "role": ROLE_LABELS.get(c["role"], c["role"])}

        def enregistrer(dialogue, v):
            if v["role"] not in LIBELLE_VERS_ROLE:
                messagebox.showwarning("Compte", "Choisissez un rôle.", parent=dialogue)
                return False
            ok, _ = essayer(dialogue, personnel_service.modifier_compte, self.user, id_p, v["nom"],
                            v["prenom"], LIBELLE_VERS_ROLE[v["role"]], v["telephone"])
            return ok

        self._ouvrir(f"Modifier le compte de {c['login']}", champs, valeurs, enregistrer)

    def basculer(self):
        id_p = self._selection()
        if id_p is None:
            return
        actif = bool(self.comptes[id_p]["actif"])
        ok, _ = essayer(self, personnel_service.changer_statut_compte, self.user, id_p, not actif)
        if ok:
            self.actualiser()

    def reinitialiser(self):
        id_p = self._selection()
        if id_p is None:
            return
        champs = [("mot_de_passe", "Nouveau mot de passe *", "mdp"), ("confirmation", "Confirmation *", "mdp")]

        def enregistrer(dialogue, v):
            if v["mot_de_passe"] != v["confirmation"]:
                messagebox.showwarning("Mot de passe", "Les deux saisies sont différentes.", parent=dialogue)
                return False
            ok, _ = essayer(dialogue, personnel_service.reinitialiser_mot_de_passe, self.user, id_p,
                            v["mot_de_passe"])
            if ok:
                messagebox.showinfo("Mot de passe", "Mot de passe réinitialisé.", parent=dialogue)
            return ok

        self._ouvrir(f"Nouveau mot de passe pour {self.comptes[id_p]['login']}", champs, {}, enregistrer)
