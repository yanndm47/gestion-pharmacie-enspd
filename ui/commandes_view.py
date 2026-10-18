"""Module Commandes : commandes aux fournisseurs, réceptions de lots, fournisseurs (pharmacien)."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.formatting import fmt_date, fmt_montant, parse_date, parse_decimal
from services import catalogue_service, commande_service, fournisseur_service
from services.commande_service import STATUTS_COMMANDE, LigneCommande
from ui.dialogs import FormulaireDialog
from ui.messages import essayer
from ui.widgets import creer_arbre, vider


class NouvelleCommandeDialog(tk.Toplevel):
    """Saisie d'une commande et de ses lignes. `resultat` = numéro créé, ou None."""

    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Nouvelle commande")
        self.user = user
        self.resultat = None
        self.fournisseurs = []
        self.medicaments_trouves = []
        self.lignes = []     # dicts : id_medicament, nom, quantite, prix (Decimal ou None)
        self.transient(parent.winfo_toplevel())

        cadre = ttk.Frame(self, padding=12)
        cadre.pack(fill="both", expand=True)
        cadre.columnconfigure(0, weight=1)

        haut = ttk.LabelFrame(cadre, text="Commande", padding=8)
        haut.grid(row=0, column=0, sticky="ew")
        ttk.Label(haut, text="Fournisseur *").grid(row=0, column=0, sticky="e", padx=4)
        ok, fournisseurs = essayer(self, fournisseur_service.lister_fournisseurs, user, False)
        self.fournisseurs = fournisseurs if ok else []
        self.combo_fournisseur = ttk.Combobox(
            haut, state="readonly", width=34,
            values=[f["raison_sociale"] for f in self.fournisseurs])
        self.combo_fournisseur.grid(row=0, column=1, padx=4)
        ttk.Label(haut, text="Livraison prévue (JJ/MM/AAAA)").grid(row=0, column=2, sticky="e", padx=(12, 4))
        self.var_livraison = tk.StringVar()
        ttk.Entry(haut, textvariable=self.var_livraison, width=12).grid(row=0, column=3)

        bloc = ttk.LabelFrame(cadre, text="Médicaments commandés", padding=8)
        bloc.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        cadre.rowconfigure(1, weight=1)
        bloc.columnconfigure(0, weight=1)
        bloc.rowconfigure(2, weight=1)
        ligne1 = ttk.Frame(bloc)
        ligne1.grid(row=0, column=0, sticky="ew")
        ligne1.columnconfigure(1, weight=1)
        self.var_med = tk.StringVar()
        ttk.Label(ligne1, text="Chercher :").grid(row=0, column=0, padx=(0, 4))
        entree = ttk.Entry(ligne1, textvariable=self.var_med)
        entree.grid(row=0, column=1, sticky="ew")
        entree.bind("<Return>", lambda _e: self._chercher())
        ttk.Button(ligne1, text="Chercher", command=self._chercher).grid(row=0, column=2, padx=6)
        self.combo_med = ttk.Combobox(ligne1, state="readonly", width=36)
        self.combo_med.grid(row=0, column=3)
        ligne2 = ttk.Frame(bloc)
        ligne2.grid(row=1, column=0, sticky="ew", pady=6)
        self.var_qte = tk.StringVar(value="10")
        self.var_prix = tk.StringVar()
        ttk.Label(ligne2, text="Quantité").grid(row=0, column=0)
        ttk.Spinbox(ligne2, from_=1, to=99999, textvariable=self.var_qte, width=7).grid(row=0, column=1, padx=4)
        ttk.Label(ligne2, text="Prix d'achat prévu (facultatif)").grid(row=0, column=2, padx=(10, 0))
        ttk.Entry(ligne2, textvariable=self.var_prix, width=10).grid(row=0, column=3, padx=4)
        ttk.Button(ligne2, text="Ajouter la ligne", command=self._ajouter).grid(row=0, column=4, padx=8)
        cadre_t = creer_arbre(bloc, [("nom", "Médicament", 260, "w"), ("qte", "Quantité", 80, "e"),
                                     ("prix", "Prix prévu", 90, "e")], height=6)
        cadre_t.grid(row=2, column=0, sticky="nsew")
        self.arbre = cadre_t.arbre
        ttk.Button(bloc, text="Retirer la ligne", command=self._retirer).grid(row=3, column=0, sticky="w", pady=(6, 0))

        boutons = ttk.Frame(cadre)
        boutons.grid(row=2, column=0, sticky="e", pady=(10, 0))
        ttk.Button(boutons, text="Enregistrer la commande", command=self._enregistrer).pack(side="left", padx=4)
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Escape>", lambda _e: self.destroy())
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _chercher(self):
        ok, meds = essayer(self, catalogue_service.rechercher_medicaments, self.user, self.var_med.get(), 30)
        if not ok:
            return
        self.medicaments_trouves = meds
        self.combo_med["values"] = [f"{m['nom_commercial']} – {m['forme']} {m['dosage']}" for m in meds]
        if meds:
            self.combo_med.current(0)
        else:
            messagebox.showinfo("Médicaments", "Aucun médicament trouvé.", parent=self)

    def _ajouter(self):
        indice = self.combo_med.current()
        if indice < 0:
            messagebox.showwarning("Ligne", "Cherchez puis choisissez un médicament.", parent=self)
            return
        med = self.medicaments_trouves[indice]
        if any(l["id_medicament"] == med["id_medicament"] for l in self.lignes):
            messagebox.showwarning("Ligne", "Ce médicament figure déjà dans la commande.", parent=self)
            return
        try:
            quantite = int(self.var_qte.get())
            if quantite <= 0:
                raise ValueError
            prix = parse_decimal(self.var_prix.get()) if self.var_prix.get().strip() else None
        except ValueError:
            messagebox.showwarning("Ligne", "Quantité entière positive et prix numérique attendus.", parent=self)
            return
        self.lignes.append({"id_medicament": med["id_medicament"], "nom": med["nom_commercial"],
                            "quantite": quantite, "prix": prix})
        self.var_prix.set("")
        self._rafraichir()

    def _retirer(self):
        sel = self.arbre.selection()
        if sel:
            self.lignes = [l for l in self.lignes if str(l["id_medicament"]) != sel[0]]
            self._rafraichir()

    def _rafraichir(self):
        vider(self.arbre)
        for l in self.lignes:
            self.arbre.insert("", "end", iid=str(l["id_medicament"]), values=(
                l["nom"], l["quantite"], fmt_montant(l["prix"]) if l["prix"] is not None else ""))

    def _enregistrer(self):
        indice = self.combo_fournisseur.current()
        if indice < 0:
            messagebox.showwarning("Commande", "Choisissez le fournisseur.", parent=self)
            return
        livraison = None
        if self.var_livraison.get().strip():
            try:
                livraison = parse_date(self.var_livraison.get())
            except ValueError as erreur:
                messagebox.showwarning("Date", str(erreur), parent=self)
                return
        lignes = [LigneCommande(l["id_medicament"], l["quantite"], l["prix"]) for l in self.lignes]
        ok, numero = essayer(self, commande_service.creer_commande, self.user,
                             self.fournisseurs[indice]["id_fournisseur"], livraison, lignes)
        if ok:
            self.resultat = numero
            messagebox.showinfo("Commande enregistrée", f"Commande n°{numero} enregistrée.", parent=self)
            self.destroy()


class ReceptionDialog(tk.Toplevel):
    """Réception d'UN lot pour une ligne de commande. `resultat` = id du lot créé, ou None."""

    def __init__(self, parent, user, id_commande, lignes):
        super().__init__(parent)
        self.title(f"Réception – commande n°{id_commande}")
        self.resizable(False, False)
        self.user = user
        self.id_commande = id_commande
        self.lignes = lignes          # lignes de la commande avec reste_a_recevoir > 0
        self.resultat = None
        self.transient(parent.winfo_toplevel())

        cadre = ttk.Frame(self, padding=16)
        cadre.pack()
        ttk.Label(cadre, text="Médicament reçu").grid(row=0, column=0, sticky="e", padx=6, pady=5)
        self.combo = ttk.Combobox(cadre, state="readonly", width=40, values=[
            f"{l['nom_commercial']} (reste {l['reste_a_recevoir']})" for l in lignes])
        self.combo.grid(row=0, column=1, pady=5)
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self._preremplir())
        self.vars = {c: tk.StringVar() for c in ("lot", "peremption", "quantite", "prix")}
        champs = [("lot", "N° de lot *"), ("peremption", "Péremption * (JJ/MM/AAAA)"),
                  ("quantite", "Quantité reçue *"), ("prix", "Prix d'achat unitaire *")]
        for i, (cle, libelle) in enumerate(champs, start=1):
            ttk.Label(cadre, text=libelle).grid(row=i, column=0, sticky="e", padx=6, pady=5)
            ttk.Entry(cadre, textvariable=self.vars[cle], width=24).grid(row=i, column=1, sticky="w", pady=5)
        boutons = ttk.Frame(cadre)
        boutons.grid(row=len(champs) + 1, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(boutons, text="Enregistrer la réception", command=self._enregistrer).pack(side="left", padx=4)
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Escape>", lambda _e: self.destroy())
        if lignes:
            self.combo.current(0)
            self._preremplir()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _preremplir(self):
        indice = self.combo.current()
        if indice < 0:
            return
        ligne = self.lignes[indice]
        self.vars["quantite"].set(str(ligne["reste_a_recevoir"]))
        prevu = ligne["prix_achat_prevu"]
        self.vars["prix"].set(fmt_montant(prevu).replace(" ", "") if prevu is not None else "")

    def _enregistrer(self):
        indice = self.combo.current()
        if indice < 0:
            messagebox.showwarning("Réception", "Choisissez le médicament reçu.", parent=self)
            return
        try:
            peremption = parse_date(self.vars["peremption"].get())
            quantite = int(self.vars["quantite"].get())
            prix = parse_decimal(self.vars["prix"].get())
        except ValueError:
            messagebox.showwarning("Réception", "Vérifiez la date (JJ/MM/AAAA), la quantité et le prix.",
                                   parent=self)
            return
        ok, id_stock = essayer(
            self, commande_service.receptionner, self.user, self.id_commande,
            self.lignes[indice]["id_medicament"], self.vars["lot"].get(), peremption, quantite, prix)
        if ok:
            self.resultat = id_stock
            messagebox.showinfo("Réception enregistrée", "Le lot a été ajouté au stock.", parent=self)
            self.destroy()


class CommandesPanel(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.commandes = {}
        self.detail = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)

        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.statuts = {"Tous les statuts": None}
        self.statuts.update({libelle: cle for cle, libelle in STATUTS_COMMANDE.items()})
        self.combo = ttk.Combobox(barre, state="readonly", values=list(self.statuts), width=18)
        self.combo.current(0)
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Nouvelle commande", command=self.nouvelle).pack(side="left", padx=(10, 4))
        ttk.Button(barre, text="Réceptionner…", command=self.receptionner).pack(side="left", padx=4)
        ttk.Button(barre, text="Annuler la commande", command=self.annuler).pack(side="left", padx=4)
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="right")

        cadre = ttk.LabelFrame(self, text="Commandes", padding=6)
        cadre.grid(row=1, column=0, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)
        liste = creer_arbre(cadre, [
            ("id", "N°", 50, "e"), ("date", "Passée le", 90, "center"), ("livraison", "Livraison prévue", 110, "center"),
            ("fournisseur", "Fournisseur", 200, "w"), ("par", "Passée par", 150, "w"), ("statut", "Statut", 90, "w")])
        liste.grid(row=0, column=0, sticky="nsew")
        self.arbre = liste.arbre
        self.arbre.tag_configure("recue", foreground="#15803d")
        self.arbre.tag_configure("partielle", foreground="#b45309")
        self.arbre.tag_configure("annulee", foreground="#9ca3af")
        self.arbre.bind("<<TreeviewSelect>>", lambda _e: self._afficher_detail())

        cadre_d = ttk.LabelFrame(self, text="Détail de la commande", padding=6)
        cadre_d.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        cadre_d.columnconfigure(0, weight=1)
        cadre_d.rowconfigure(0, weight=1)
        detail = creer_arbre(cadre_d, [
            ("nom", "Médicament", 240, "w"), ("commande", "Commandé", 80, "e"), ("recu", "Reçu", 70, "e"),
            ("reste", "Reste", 70, "e"), ("prix", "Prix prévu", 90, "e")], height=5)
        detail.grid(row=0, column=0, sticky="nsew")
        self.arbre_detail = detail.arbre
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, commande_service.lister_commandes, self.user, self.statuts[self.combo.get()])
        if not ok:
            return
        self.commandes = {c["id_commande"]: c for c in lignes}
        vider(self.arbre)
        vider(self.arbre_detail)
        self.detail = []
        for c in lignes:
            self.arbre.insert("", "end", iid=str(c["id_commande"]), tags=(c["statut"],), values=(
                c["id_commande"], fmt_date(c["date_commande"]), fmt_date(c["date_livraison_prevue"]),
                c["fournisseur"], c["passee_par"], STATUTS_COMMANDE.get(c["statut"], c["statut"])))

    def _selection(self, message=True):
        sel = self.arbre.selection()
        if not sel:
            if message:
                messagebox.showinfo("Commandes", "Sélectionnez d'abord une commande.", parent=self)
            return None
        return int(sel[0])

    def _afficher_detail(self):
        vider(self.arbre_detail)
        self.detail = []
        id_commande = self._selection(message=False)
        if id_commande is None:
            return
        ok, lignes = essayer(self, commande_service.detail_commande, self.user, id_commande)
        if not ok:
            return
        self.detail = lignes
        for l in lignes:
            self.arbre_detail.insert("", "end", values=(
                l["nom_commercial"], l["quantite_commandee"], l["quantite_recue"], l["reste_a_recevoir"],
                fmt_montant(l["prix_achat_prevu"]) if l["prix_achat_prevu"] is not None else ""))

    def nouvelle(self):
        dialogue = NouvelleCommandeDialog(self, self.user)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()

    def receptionner(self):
        id_commande = self._selection()
        if id_commande is None:
            return
        if self.commandes[id_commande]["statut"] in ("recue", "annulee"):
            messagebox.showinfo("Réception", "Cette commande est déjà reçue ou annulée.", parent=self)
            return
        a_recevoir = [l for l in self.detail if l["reste_a_recevoir"] > 0]
        if not a_recevoir:
            messagebox.showinfo("Réception", "Il ne reste rien à recevoir sur cette commande.", parent=self)
            return
        dialogue = ReceptionDialog(self, self.user, id_commande, a_recevoir)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()
            if str(id_commande) in self.arbre.get_children():
                self.arbre.selection_set(str(id_commande))

    def annuler(self):
        id_commande = self._selection()
        if id_commande is None:
            return
        if not messagebox.askyesno("Annuler la commande", f"Annuler la commande n°{id_commande} ?", parent=self):
            return
        ok, _ = essayer(self, commande_service.annuler_commande, self.user, id_commande)
        if ok:
            self.actualiser()


class FournisseursPanel(ttk.Frame):
    CHAMPS = [("raison_sociale", "Raison sociale *", "texte"), ("telephone", "Téléphone *", "texte"),
              ("email", "Email", "texte"), ("adresse", "Adresse", "texte"),
              ("delai_livraison_jours", "Délai de livraison (jours)", "texte")]

    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.fournisseurs = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(barre, text="Nouveau fournisseur", command=self.nouveau).pack(side="left")
        ttk.Button(barre, text="Modifier", command=self.modifier).pack(side="left", padx=6)
        ttk.Button(barre, text="Désactiver / Réactiver", command=self.basculer).pack(side="left")
        ttk.Button(barre, text="Actualiser", command=self.actualiser).pack(side="right")
        cadre = creer_arbre(self, [
            ("nom", "Raison sociale", 220, "w"), ("tel", "Téléphone", 110, "w"), ("email", "Email", 200, "w"),
            ("adresse", "Adresse", 220, "w"), ("delai", "Délai (j)", 70, "e"), ("actif", "Actif", 50, "center")])
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = cadre.arbre
        self.arbre.tag_configure("inactif", foreground="#9ca3af")
        self.actualiser()

    def actualiser(self):
        ok, lignes = essayer(self, fournisseur_service.lister_fournisseurs, self.user, True)
        if not ok:
            return
        self.fournisseurs = {f["id_fournisseur"]: f for f in lignes}
        vider(self.arbre)
        for f in lignes:
            self.arbre.insert("", "end", iid=str(f["id_fournisseur"]),
                              tags=() if f["actif"] else ("inactif",), values=(
                f["raison_sociale"], f["telephone"], f["email"] or "", f["adresse"] or "",
                "" if f["delai_livraison_jours"] is None else f["delai_livraison_jours"],
                "Oui" if f["actif"] else "Non"))

    def _selection(self):
        sel = self.arbre.selection()
        if not sel:
            messagebox.showinfo("Fournisseurs", "Sélectionnez d'abord un fournisseur.", parent=self)
            return None
        return int(sel[0])

    def _formulaire(self, titre, valeurs, action):
        def enregistrer(dialogue, v):
            try:
                delai = int(v["delai_livraison_jours"]) if v["delai_livraison_jours"].strip() else None
            except ValueError:
                messagebox.showwarning("Saisie", "Le délai doit être un nombre entier de jours.", parent=dialogue)
                return False
            ok, _ = essayer(dialogue, action, v["raison_sociale"], v["telephone"], v["email"],
                            v["adresse"], delai)
            return ok

        dialogue = FormulaireDialog(self, titre, self.CHAMPS, valeurs, enregistrer)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()

    def nouveau(self):
        self._formulaire("Nouveau fournisseur", {},
                         lambda *a: fournisseur_service.creer_fournisseur(self.user, *a))

    def modifier(self):
        id_f = self._selection()
        if id_f is not None:
            self._formulaire("Modifier le fournisseur", self.fournisseurs[id_f],
                             lambda *a: fournisseur_service.modifier_fournisseur(self.user, id_f, *a))

    def basculer(self):
        id_f = self._selection()
        if id_f is None:
            return
        actif = bool(self.fournisseurs[id_f]["actif"])
        ok, _ = essayer(self, fournisseur_service.changer_statut_fournisseur, self.user, id_f, not actif)
        if ok:
            self.actualiser()


class CommandesView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=4)
        onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True)
        onglets.add(CommandesPanel(onglets, user), text="Commandes et réceptions")
        onglets.add(FournisseursPanel(onglets, user), text="Fournisseurs")
