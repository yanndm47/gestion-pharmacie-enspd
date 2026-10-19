"""Module Ordonnances : liste, détail (reste à délivrer) et saisie d'une nouvelle ordonnance.

Réservé au pharmacien (RG-30). La validité est de 14 jours (config.VALIDITE_ORDONNANCE_JOURS).
"""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import config
from core.formatting import fmt_date, parse_date
from services import catalogue_service, client_service, ordonnance_service
from services.ordonnance_service import STATUTS, LigneOrdonnance
from ui.dialogs import NouveauClientDialog
from ui.messages import essayer
from ui.widgets import Tableau


class NouvelleOrdonnanceDialog(tk.Toplevel):
    """Saisie d'une ordonnance et de ses lignes. `resultat` = numéro créé, ou None."""

    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Nouvelle ordonnance")
        self.user = user
        self.resultat = None
        self.client = None
        self.clients_trouves = []
        self.medicaments_trouves = []
        self.lignes = []        # dicts : id_medicament, nom, quantite, posologie, duree
        self.transient(parent.winfo_toplevel())

        cadre = ttk.Frame(self, padding=12)
        cadre.pack(fill="both", expand=True)
        cadre.columnconfigure(0, weight=1)

        self._bloc_patient(cadre).grid(row=0, column=0, sticky="ew")
        self._bloc_prescription(cadre).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self._bloc_lignes(cadre).grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        cadre.rowconfigure(2, weight=1)

        boutons = ttk.Frame(cadre)
        boutons.grid(row=3, column=0, sticky="e", pady=(10, 0))
        ttk.Button(boutons, text="Enregistrer l'ordonnance", style="Accent.TButton", command=self._enregistrer).pack(side="left", padx=4)
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Escape>", lambda _e: self.destroy())
        try:
            self.grab_set()
        except tk.TclError:
            pass

    # --- construction ------------------------------------------------------
    def _bloc_patient(self, parent):
        bloc = ttk.LabelFrame(parent, text="Patient", padding=8)
        bloc.columnconfigure(0, weight=1)
        self.var_client = tk.StringVar()
        entree = ttk.Entry(bloc, textvariable=self.var_client)
        entree.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        entree.bind("<Return>", lambda _e: self._rechercher_client())
        entree.focus_set()
        ttk.Button(bloc, text="Rechercher", style="Primary.TButton", command=self._rechercher_client).grid(row=0, column=1)
        self.combo_client = ttk.Combobox(bloc, state="readonly")
        self.combo_client.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=6)
        self.combo_client.bind("<<ComboboxSelected>>", lambda _e: self._choisir_client())
        ttk.Button(bloc, text="Nouveau…", command=self._nouveau_client).grid(row=1, column=1)
        self.lbl_client = ttk.Label(bloc, text="Aucun client choisi", foreground="#b45309")
        self.lbl_client.grid(row=2, column=0, columnspan=2, sticky="w")
        return bloc

    def _bloc_prescription(self, parent):
        bloc = ttk.LabelFrame(parent, text="Prescription", padding=8)
        self.var_medecin = tk.StringVar()
        self.var_ordre = tk.StringVar()
        self.var_date = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        champs = [("Médecin *", self.var_medecin, 28), ("N° d'ordre", self.var_ordre, 16),
                  ("Date de prescription *", self.var_date, 12)]
        for i, (libelle, var, largeur) in enumerate(champs):
            ttk.Label(bloc, text=libelle).grid(row=0, column=2 * i, sticky="e", padx=(8, 4))
            ttk.Entry(bloc, textvariable=var, width=largeur).grid(row=0, column=2 * i + 1)
        ttk.Label(bloc, text=f"Valable {config.VALIDITE_ORDONNANCE_JOURS} jours à partir de la date de prescription.",
                  foreground="#6b7280").grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))
        return bloc

    def _bloc_lignes(self, parent):
        bloc = ttk.LabelFrame(parent, text="Médicaments prescrits", padding=8)
        bloc.columnconfigure(0, weight=1)
        bloc.rowconfigure(2, weight=1)

        haut = ttk.Frame(bloc)
        haut.grid(row=0, column=0, sticky="ew")
        haut.columnconfigure(1, weight=1)
        self.var_med = tk.StringVar()
        ttk.Label(haut, text="Chercher :").grid(row=0, column=0, padx=(0, 4))
        entree = ttk.Entry(haut, textvariable=self.var_med)
        entree.grid(row=0, column=1, sticky="ew")
        entree.bind("<Return>", lambda _e: self._chercher_medicament())
        ttk.Button(haut, text="Chercher", command=self._chercher_medicament).grid(row=0, column=2, padx=6)
        self.combo_med = ttk.Combobox(haut, state="readonly", width=38)
        self.combo_med.grid(row=0, column=3)

        milieu = ttk.Frame(bloc)
        milieu.grid(row=1, column=0, sticky="ew", pady=6)
        self.var_qte = tk.StringVar(value="1")
        self.var_poso = tk.StringVar()
        self.var_duree = tk.StringVar()
        ttk.Label(milieu, text="Quantité").grid(row=0, column=0)
        ttk.Spinbox(milieu, from_=1, to=999, textvariable=self.var_qte, width=5).grid(row=0, column=1, padx=4)
        ttk.Label(milieu, text="Posologie").grid(row=0, column=2, padx=(8, 0))
        ttk.Entry(milieu, textvariable=self.var_poso, width=34).grid(row=0, column=3, padx=4)
        ttk.Label(milieu, text="Durée (jours)").grid(row=0, column=4, padx=(8, 0))
        ttk.Entry(milieu, textvariable=self.var_duree, width=5).grid(row=0, column=5, padx=4)
        ttk.Button(milieu, text="Ajouter la ligne", style="Primary.TButton", command=self._ajouter_ligne).grid(row=0, column=6, padx=8)

        colonnes = [("nom", "Médicament", 200, "w"), ("qte", "Qté", 50, "e"),
                    ("poso", "Posologie", 280, "w"), ("duree", "Durée", 60, "e")]
        self.arbre = Tableau(bloc, columns=[c[0] for c in colonnes], show="headings",
                                  height=6, selectmode="browse")
        for cle, libelle, largeur, ancre in colonnes:
            self.arbre.heading(cle, text=libelle)
            self.arbre.column(cle, width=largeur, anchor=ancre)
        self.arbre.grid(row=2, column=0, sticky="nsew")
        ttk.Button(bloc, text="Retirer la ligne", command=self._retirer_ligne).grid(
            row=3, column=0, sticky="w", pady=(6, 0))
        return bloc

    # --- patient -----------------------------------------------------------
    def _rechercher_client(self):
        ok, clients = essayer(self, client_service.rechercher_clients, self.user, self.var_client.get())
        if not ok:
            return
        self.clients_trouves = clients
        self.combo_client["values"] = [
            f"{c['nom']} {c['prenom']} (né(e) le {fmt_date(c['date_naissance'])})" for c in clients]
        if clients:
            self.combo_client.current(0)
            self._choisir_client()
        else:
            messagebox.showinfo("Clients", "Aucun client trouvé. Utilisez « Nouveau… ».", parent=self)

    def _choisir_client(self):
        indice = self.combo_client.current()
        if indice >= 0:
            self.client = self.clients_trouves[indice]
            self.lbl_client.config(text=f"Patient : {self.client['nom']} {self.client['prenom']}",
                                   foreground="#111827")

    def _nouveau_client(self):
        dialogue = NouveauClientDialog(self, self.user)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.client = dialogue.resultat
            self.clients_trouves = [self.client]
            self.combo_client["values"] = [f"{self.client['nom']} {self.client['prenom']} (nouveau)"]
            self.combo_client.current(0)
            self.lbl_client.config(text=f"Patient : {self.client['nom']} {self.client['prenom']}",
                                   foreground="#111827")

    # --- lignes ------------------------------------------------------------
    def _chercher_medicament(self):
        ok, meds = essayer(self, catalogue_service.rechercher_medicaments,
                           self.user, self.var_med.get(), 30)
        if not ok:
            return
        self.medicaments_trouves = meds
        self.combo_med["values"] = [f"{m['nom_commercial']} – {m['forme']} {m['dosage']}" for m in meds]
        if meds:
            self.combo_med.current(0)
        else:
            messagebox.showinfo("Médicaments", "Aucun médicament trouvé.", parent=self)

    def _ajouter_ligne(self):
        indice = self.combo_med.current()
        if indice < 0:
            messagebox.showwarning("Ligne", "Cherchez puis choisissez un médicament.", parent=self)
            return
        med = self.medicaments_trouves[indice]
        if any(l["id_medicament"] == med["id_medicament"] for l in self.lignes):
            messagebox.showwarning("Ligne", "Ce médicament figure déjà sur l'ordonnance (RG-28).", parent=self)
            return
        try:
            quantite = int(self.var_qte.get())
            if quantite <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Ligne", "Saisissez une quantité entière positive.", parent=self)
            return
        posologie = self.var_poso.get().strip()
        if not posologie:
            messagebox.showwarning("Ligne", "La posologie est obligatoire.", parent=self)
            return
        duree = None
        if self.var_duree.get().strip():
            try:
                duree = int(self.var_duree.get())
                if duree <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Ligne", "La durée doit être un nombre de jours positif.", parent=self)
                return
        self.lignes.append({"id_medicament": med["id_medicament"], "nom": med["nom_commercial"],
                            "quantite": quantite, "posologie": posologie, "duree": duree})
        self.var_poso.set("")
        self.var_duree.set("")
        self.var_qte.set("1")
        self._rafraichir_lignes()

    def _retirer_ligne(self):
        selection = self.arbre.selection()
        if selection:
            self.lignes = [l for l in self.lignes if str(l["id_medicament"]) != selection[0]]
            self._rafraichir_lignes()

    def _rafraichir_lignes(self):
        self.arbre.delete(*self.arbre.get_children())
        for l in self.lignes:
            self.arbre.insert("", "end", iid=str(l["id_medicament"]),
                              values=(l["nom"], l["quantite"], l["posologie"], l["duree"] or ""))

    # --- enregistrement ----------------------------------------------------
    def _enregistrer(self):
        if self.client is None:
            messagebox.showwarning("Ordonnance", "Choisissez le patient.", parent=self)
            return
        try:
            date_prescription = parse_date(self.var_date.get())
        except ValueError as erreur:
            messagebox.showwarning("Date", str(erreur), parent=self)
            return
        lignes = [LigneOrdonnance(l["id_medicament"], l["quantite"], l["posologie"], l["duree"])
                  for l in self.lignes]
        ok, numero = essayer(
            self, ordonnance_service.creer_ordonnance, self.user, self.client["id_client"],
            self.var_medecin.get(), self.var_ordre.get(), date_prescription, lignes)
        if ok:
            self.resultat = numero
            messagebox.showinfo("Ordonnance enregistrée", f"Ordonnance n°{numero} enregistrée.", parent=self)
            self.destroy()


class OrdonnancesView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)

        # --- barre de filtres ---
        barre = ttk.Frame(self)
        barre.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        barre.columnconfigure(2, weight=1)
        self.statuts = {"Tous les statuts": None}
        self.statuts.update({libelle: cle for cle, libelle in STATUTS.items()})
        self.combo_statut = ttk.Combobox(barre, state="readonly", values=list(self.statuts), width=18)
        self.combo_statut.current(0)
        self.combo_statut.grid(row=0, column=0)
        self.combo_statut.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        ttk.Label(barre, text="Client ou médecin :").grid(row=0, column=1, padx=(10, 4))
        self.var_terme = tk.StringVar()
        entree = ttk.Entry(barre, textvariable=self.var_terme)
        entree.grid(row=0, column=2, sticky="ew")
        entree.bind("<Return>", lambda _e: self.actualiser())
        ttk.Button(barre, text="Rechercher", style="Primary.TButton", command=self.actualiser).grid(row=0, column=3, padx=6)
        ttk.Button(barre, text="Nouvelle ordonnance", style="Primary.TButton", command=self.nouvelle_ordonnance).grid(row=0, column=4)

        # --- liste ---
        cadre = ttk.LabelFrame(self, text="Ordonnances", padding=6)
        cadre.grid(row=1, column=0, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)
        colonnes = [("id", "N°", 50, "e"), ("date", "Prescrite le", 90, "center"),
                    ("validite", "Valable jusqu'au", 110, "center"), ("client", "Client", 200, "w"),
                    ("medecin", "Médecin", 170, "w"), ("statut", "Statut", 100, "w")]
        self.arbre = Tableau(cadre, columns=[c[0] for c in colonnes], show="headings",
                                  selectmode="browse")
        for cle, libelle, largeur, ancre in colonnes:
            self.arbre.heading(cle, text=libelle)
            self.arbre.column(cle, width=largeur, anchor=ancre)
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=defil.set)
        self.arbre.grid(row=0, column=0, sticky="nsew")
        defil.grid(row=0, column=1, sticky="ns")
        self.arbre.tag_configure("soldee", foreground="#15803d")
        self.arbre.tag_configure("partielle", foreground="#b45309")
        self.arbre.tag_configure("expiree", foreground="#9ca3af")
        self.arbre.bind("<<TreeviewSelect>>", lambda _e: self._afficher_detail())

        # --- détail ---
        cadre_d = ttk.LabelFrame(self, text="Détail : ce qui a été délivré", padding=6)
        cadre_d.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        cadre_d.columnconfigure(0, weight=1)
        cadre_d.rowconfigure(0, weight=1)
        colonnes_d = [("nom", "Médicament", 200, "w"), ("prescrit", "Prescrit", 70, "e"),
                      ("delivre", "Délivré", 70, "e"), ("reste", "Reste", 60, "e"),
                      ("poso", "Posologie", 300, "w"), ("duree", "Durée (j)", 70, "e")]
        self.arbre_detail = Tableau(cadre_d, columns=[c[0] for c in colonnes_d],
                                         show="headings", height=5)
        for cle, libelle, largeur, ancre in colonnes_d:
            self.arbre_detail.heading(cle, text=libelle)
            self.arbre_detail.column(cle, width=largeur, anchor=ancre)
        self.arbre_detail.grid(row=0, column=0, sticky="nsew")

        self.actualiser()

    def actualiser(self):
        statut = self.statuts[self.combo_statut.get()]
        ok, lignes = essayer(self, ordonnance_service.lister_ordonnances,
                             self.user, statut, self.var_terme.get())
        if not ok:
            return
        self.arbre.delete(*self.arbre.get_children())
        self.arbre_detail.delete(*self.arbre_detail.get_children())
        for o in lignes:
            self.arbre.insert("", "end", iid=str(o["id_ordonnance"]), tags=(o["statut"],), values=(
                o["id_ordonnance"], fmt_date(o["date_prescription"]), fmt_date(o["date_validite"]),
                o["client"], o["nom_medecin"], STATUTS.get(o["statut"], o["statut"])))

    def _afficher_detail(self):
        selection = self.arbre.selection()
        self.arbre_detail.delete(*self.arbre_detail.get_children())
        if not selection:
            return
        ok, lignes = essayer(self, ordonnance_service.detail_ordonnance, self.user, int(selection[0]))
        if not ok:
            return
        for l in lignes:
            self.arbre_detail.insert("", "end", values=(
                l["nom_commercial"], l["quantite_prescrite"], l["quantite_delivree"],
                l["reste_a_delivrer"], l["posologie"], l["duree_traitement_jours"] or ""))

    def nouvelle_ordonnance(self):
        dialogue = NouvelleOrdonnanceDialog(self, self.user)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.actualiser()
