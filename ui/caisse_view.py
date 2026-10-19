"""Écran de caisse : recherche de médicaments, panier, client, ordonnance, paiement.

Pour le personnel de caisse : médicaments sans ordonnance obligatoire uniquement.
Le pharmacien peut en plus rattacher la vente à une ordonnance ouverte du client.
La validation appelle vente_service.creer_vente (une seule transaction).
"""
import tkinter as tk
from decimal import Decimal
from tkinter import messagebox, ttk

from core.formatting import fmt_date, fmt_montant
from core.permissions import can
from services import catalogue_service, client_service, ordonnance_service, vente_service
from services.vente_service import MODES_PAIEMENT, LigneDemandee
from ui.dialogs import NouveauClientDialog
from ui.messages import essayer
from ui.widgets import Tableau
from ui.ticket_view import TicketDialog


AIDE_ORDONNANCE = "Choisissez d'abord le client : ses ordonnances ouvertes apparaissent ici."


class CaisseView(ttk.Frame):
    def __init__(self, master, user):
        super().__init__(master, padding=8)
        self.user = user
        self.peut_ordonnance = can(user.role, "vendre_ordonnance")
        self.catalogue = {}        # id_medicament -> ligne du catalogue
        self.panier = {}           # id_medicament -> dict(nom, prix, quantite, stock)
        self.client = None         # dict ou None (vente anonyme)
        self.clients_trouves = []
        self.ordonnances = []
        self.id_ordonnance = None
        self._timer = None

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)
        self._construire_catalogue()
        self._construire_vente()
        self.actualiser_catalogue()

    # ------------------------------------------------------------------
    # Colonne de gauche : catalogue
    # ------------------------------------------------------------------
    def _construire_catalogue(self):
        cadre = ttk.LabelFrame(self, text="Catalogue", padding=8)
        cadre.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(1, weight=1)

        ligne = ttk.Frame(cadre)
        ligne.grid(row=0, column=0, sticky="ew")
        ligne.columnconfigure(1, weight=1)
        ttk.Label(ligne, text="Rechercher :").grid(row=0, column=0, padx=(0, 6))
        self.var_recherche = tk.StringVar()
        entree = ttk.Entry(ligne, textvariable=self.var_recherche)
        entree.grid(row=0, column=1, sticky="ew")
        entree.bind("<KeyRelease>", self._recherche_differee)
        entree.focus_set()

        colonnes = [("nom", "Médicament", 190, "w"), ("forme", "Forme", 110, "w"),
                    ("dosage", "Dosage", 80, "w"), ("prix", "Prix", 70, "e"),
                    ("stock", "Stock", 55, "e"), ("ordo", "Ordo.", 45, "center")]
        zone = ttk.Frame(cadre)
        zone.grid(row=1, column=0, sticky="nsew", pady=6)
        zone.columnconfigure(0, weight=1)
        zone.rowconfigure(0, weight=1)
        self.arbre_cat = Tableau(zone, columns=[c[0] for c in colonnes],
                                      show="headings", selectmode="browse")
        for cle, libelle, largeur, ancre in colonnes:
            self.arbre_cat.heading(cle, text=libelle)
            self.arbre_cat.column(cle, width=largeur, anchor=ancre)
        defil = ttk.Scrollbar(zone, orient="vertical", command=self.arbre_cat.yview)
        self.arbre_cat.configure(yscrollcommand=defil.set)
        self.arbre_cat.grid(row=0, column=0, sticky="nsew")
        defil.grid(row=0, column=1, sticky="ns")
        self.arbre_cat.tag_configure("rupture", foreground="#9ca3af")
        self.arbre_cat.bind("<Double-1>", lambda _e: self.ajouter_au_panier())

        bas = ttk.Frame(cadre)
        bas.grid(row=2, column=0, sticky="ew")
        ttk.Label(bas, text="Quantité :").pack(side="left")
        self.var_qte = tk.StringVar(value="1")
        ttk.Spinbox(bas, from_=1, to=999, textvariable=self.var_qte, width=6).pack(side="left", padx=6)
        ttk.Button(bas, text="Ajouter au panier", style="Primary.TButton", command=self.ajouter_au_panier).pack(side="left", padx=6)
        ttk.Label(bas, text="(ou double-clic sur la ligne)", foreground="#6b7280").pack(side="left")

    def _recherche_differee(self, _event=None):
        if self._timer is not None:
            self.after_cancel(self._timer)
        self._timer = self.after(300, self.actualiser_catalogue)

    def actualiser_catalogue(self):
        ok, lignes = essayer(self, catalogue_service.rechercher_medicaments,
                             self.user, self.var_recherche.get())
        if not ok:
            return
        self.catalogue = {m["id_medicament"]: m for m in lignes}
        self.arbre_cat.delete(*self.arbre_cat.get_children())
        for m in lignes:
            stock = int(m["stock_disponible"])
            self.arbre_cat.insert(
                "", "end", iid=str(m["id_medicament"]),
                values=(m["nom_commercial"], m["forme"], m["dosage"], fmt_montant(m["prix_vente"]),
                        stock, "Oui" if m["ordonnance_obligatoire"] else ""),
                tags=("rupture",) if stock == 0 else (),
            )

    # ------------------------------------------------------------------
    # Colonne de droite : client, ordonnance, panier, paiement
    # ------------------------------------------------------------------
    def _construire_vente(self):
        droite = ttk.Frame(self)
        droite.grid(row=0, column=1, sticky="nsew")

        # --- client ---
        cadre = ttk.LabelFrame(droite, text="Client (facultatif)", padding=8)
        cadre.pack(fill="x")
        cadre.columnconfigure(0, weight=1)
        self.var_client = tk.StringVar()
        entree = ttk.Entry(cadre, textvariable=self.var_client)
        entree.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        entree.bind("<Return>", lambda _e: self.rechercher_client())
        ttk.Button(cadre, text="Rechercher", style="Primary.TButton", command=self.rechercher_client).grid(row=0, column=1)
        self.combo_client = ttk.Combobox(cadre, state="readonly")
        self.combo_client.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=6)
        self.combo_client.bind("<<ComboboxSelected>>", lambda _e: self._choisir_client())
        ttk.Button(cadre, text="Nouveau…", command=self.nouveau_client).grid(row=1, column=1)
        self.lbl_client = ttk.Label(cadre, text="Vente anonyme", foreground="#6b7280")
        self.lbl_client.grid(row=2, column=0, sticky="w")
        ttk.Button(cadre, text="Effacer", command=self._effacer_client).grid(row=2, column=1)

        # --- ordonnance (pharmacien uniquement) ---
        self.combo_ordo = None
        if self.peut_ordonnance:
            cadre_o = ttk.LabelFrame(droite, text="Ordonnance (pharmacien)", padding=8)
            cadre_o.pack(fill="x", pady=(6, 0))
            cadre_o.columnconfigure(0, weight=1)
            self.combo_ordo = ttk.Combobox(cadre_o, state="readonly", values=["(aucune)"])
            self.combo_ordo.current(0)
            self.combo_ordo.grid(row=0, column=0, sticky="ew")
            self.combo_ordo.bind("<<ComboboxSelected>>", lambda _e: self._choisir_ordonnance())
            self.var_aide_ordo = tk.StringVar(value=AIDE_ORDONNANCE)
            ttk.Label(cadre_o, textvariable=self.var_aide_ordo, foreground="#6b7280",
                      wraplength=380, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 0))

        # --- panier ---
        cadre_p = ttk.LabelFrame(droite, text="Panier", padding=8)
        cadre_p.pack(fill="both", expand=True, pady=(6, 0))
        cadre_p.columnconfigure(0, weight=1)
        cadre_p.rowconfigure(0, weight=1)
        colonnes = [("nom", "Médicament", 170, "w"), ("qte", "Qté", 45, "e"),
                    ("prix", "Prix", 65, "e"), ("sous", "Sous-total", 85, "e")]
        self.arbre_panier = Tableau(cadre_p, columns=[c[0] for c in colonnes],
                                         show="headings", height=7, selectmode="browse")
        for cle, libelle, largeur, ancre in colonnes:
            self.arbre_panier.heading(cle, text=libelle)
            self.arbre_panier.column(cle, width=largeur, anchor=ancre)
        self.arbre_panier.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Button(cadre_p, text="Retirer la ligne", command=self.retirer_ligne).grid(
            row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Button(cadre_p, text="Vider le panier", command=self.vider_panier).grid(
            row=1, column=1, sticky="e", pady=(6, 0))

        # --- total, paiement, validation ---
        bas = ttk.Frame(droite)
        bas.pack(fill="x", pady=(8, 0))
        bas.columnconfigure(1, weight=1)
        ttk.Label(bas, text="Total :", font=("Segoe UI", 13)).grid(row=0, column=0, sticky="w")
        self.var_total = tk.StringVar(value="0")
        ttk.Label(bas, textvariable=self.var_total, style="Total.TLabel").grid(
            row=0, column=1, sticky="e")
        ttk.Label(bas, text="Paiement :").grid(row=1, column=0, sticky="w", pady=6)
        self.modes_par_libelle = {libelle: cle for cle, libelle in MODES_PAIEMENT.items()}
        self.combo_paiement = ttk.Combobox(bas, state="readonly",
                                           values=list(self.modes_par_libelle))
        self.combo_paiement.current(0)
        self.combo_paiement.grid(row=1, column=1, sticky="e")
        ttk.Button(bas, text="Valider la vente", style="Accent.TButton", command=self.valider_vente).grid(
            row=2, column=0, columnspan=2, sticky="ew", ipady=6, pady=(4, 0))

    # ------------------------------------------------------------------
    # Client et ordonnance
    # ------------------------------------------------------------------
    def rechercher_client(self):
        ok, clients = essayer(self, client_service.rechercher_clients,
                              self.user, self.var_client.get())
        if not ok:
            return
        self.clients_trouves = clients
        self.combo_client["values"] = [
            f"{c['nom']} {c['prenom']} (né(e) le {fmt_date(c['date_naissance'])})" for c in clients]
        if clients:
            self.combo_client.current(0)
            self._choisir_client()
        else:
            self.combo_client.set("")
            messagebox.showinfo("Clients", "Aucun client trouvé. Utilisez « Nouveau… ».", parent=self)

    def _choisir_client(self):
        indice = self.combo_client.current()
        if indice < 0:
            return
        self.client = self.clients_trouves[indice]
        self.lbl_client.config(text=f"Client : {self.client['nom']} {self.client['prenom']}",
                               foreground="#111827")
        self._charger_ordonnances()

    def nouveau_client(self):
        dialogue = NouveauClientDialog(self, self.user)
        self.wait_window(dialogue)
        if dialogue.resultat:
            self.client = dialogue.resultat
            self.clients_trouves = [self.client]
            self.combo_client["values"] = [f"{self.client['nom']} {self.client['prenom']} (nouveau)"]
            self.combo_client.current(0)
            self.lbl_client.config(text=f"Client : {self.client['nom']} {self.client['prenom']}",
                                   foreground="#111827")
            self._charger_ordonnances()

    def _effacer_client(self):
        self.client = None
        self.clients_trouves = []
        self.combo_client.set("")
        self.combo_client["values"] = []
        self.var_client.set("")
        self.lbl_client.config(text="Vente anonyme", foreground="#6b7280")
        self._reinitialiser_ordonnances()

    def _reinitialiser_ordonnances(self):
        self.ordonnances = []
        self.id_ordonnance = None
        if self.combo_ordo is not None:
            self.combo_ordo["values"] = ["(aucune)"]
            self.combo_ordo.current(0)
            self.var_aide_ordo.set(AIDE_ORDONNANCE)

    def _charger_ordonnances(self):
        self._reinitialiser_ordonnances()
        if not self.peut_ordonnance or self.client is None:
            return
        ok, ordos = essayer(self, ordonnance_service.ordonnances_ouvertes,
                            self.user, self.client["id_client"])
        if not ok:
            return
        self.ordonnances = ordos
        self.combo_ordo["values"] = ["(aucune)"] + [
            f"N°{o['id_ordonnance']} – {o['nom_medecin']} – valable jusqu'au {fmt_date(o['date_validite'])}"
            for o in ordos]
        self.combo_ordo.current(0)

    def _choisir_ordonnance(self):
        indice = self.combo_ordo.current()
        self.id_ordonnance = None if indice <= 0 else self.ordonnances[indice - 1]["id_ordonnance"]
        self._afficher_reste_a_delivrer()

    def _afficher_reste_a_delivrer(self):
        """Affiche, sous la liste, ce qu'il reste à délivrer sur l'ordonnance choisie."""
        if self.id_ordonnance is None:
            self.var_aide_ordo.set(AIDE_ORDONNANCE)
            return
        ok, lignes = essayer(self, ordonnance_service.lignes_a_delivrer,
                             self.user, self.id_ordonnance)
        if not ok:
            return
        restes = [f"• {l['nom_commercial']} : {l['reste_a_delivrer']} à délivrer "
                  f"(sur {l['quantite_prescrite']})"
                  for l in lignes if l["reste_a_delivrer"] > 0]
        self.var_aide_ordo.set("\n".join(restes) if restes else "Tout a déjà été délivré.")

    # ------------------------------------------------------------------
    # Panier
    # ------------------------------------------------------------------
    def ajouter_au_panier(self):
        selection = self.arbre_cat.selection()
        if not selection:
            messagebox.showinfo("Panier", "Sélectionnez d'abord un médicament.", parent=self)
            return
        med = self.catalogue[int(selection[0])]
        try:
            quantite = int(self.var_qte.get())
            if quantite <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Quantité", "Saisissez une quantité entière positive.", parent=self)
            return

        if med["ordonnance_obligatoire"]:
            if not self.peut_ordonnance:
                messagebox.showwarning(
                    "Ordonnance obligatoire",
                    f"« {med['nom_commercial']} » nécessite une ordonnance : vente réservée au pharmacien.",
                    parent=self)
                return
            if self.id_ordonnance is None:
                messagebox.showwarning(
                    "Ordonnance obligatoire",
                    f"« {med['nom_commercial']} » nécessite une ordonnance : choisissez le client "
                    "puis son ordonnance.", parent=self)
                return

        stock = int(med["stock_disponible"])
        deja = self.panier.get(med["id_medicament"], {}).get("quantite", 0)
        if deja + quantite > stock:
            messagebox.showwarning(
                "Stock insuffisant",
                f"{med['nom_commercial']} : {stock} disponible(s), {deja} déjà dans le panier.",
                parent=self)
            return

        self.panier[med["id_medicament"]] = {
            "nom": med["nom_commercial"], "prix": Decimal(med["prix_vente"]),
            "quantite": deja + quantite, "stock": stock}
        self._rafraichir_panier()

    def retirer_ligne(self):
        selection = self.arbre_panier.selection()
        if selection:
            self.panier.pop(int(selection[0]), None)
            self._rafraichir_panier()

    def vider_panier(self):
        self.panier.clear()
        self._rafraichir_panier()

    def _rafraichir_panier(self):
        self.arbre_panier.delete(*self.arbre_panier.get_children())
        total = Decimal(0)
        for id_med, p in self.panier.items():
            sous_total = p["prix"] * p["quantite"]
            total += sous_total
            self.arbre_panier.insert("", "end", iid=str(id_med), values=(
                p["nom"], p["quantite"], fmt_montant(p["prix"]), fmt_montant(sous_total)))
        self.var_total.set(fmt_montant(total))

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def valider_vente(self):
        if not self.panier:
            messagebox.showinfo("Vente", "Le panier est vide.", parent=self)
            return
        lignes = [LigneDemandee(i, p["quantite"]) for i, p in self.panier.items()]
        ok, vente = essayer(
            self, vente_service.creer_vente, self.user, lignes,
            id_client=self.client["id_client"] if self.client else None,
            id_ordonnance=self.id_ordonnance,
            mode_paiement=self.modes_par_libelle[self.combo_paiement.get()],
        )
        if ok:
            afficher = messagebox.askyesno(
                "Vente enregistrée",
                f"Vente n°{vente.id_vente} – Total : {fmt_montant(vente.total)}\n\nAfficher le ticket ?",
                parent=self)
            if afficher:
                reussi, texte = essayer(self, vente_service.texte_ticket, self.user, vente.id_vente)
                if reussi:
                    TicketDialog(self, vente.id_vente, texte)
            self.panier.clear()
            self._rafraichir_panier()
            self._effacer_client()
        # Dans tous les cas, on recharge le stock affiché (il a pu changer)
        self.actualiser_catalogue()
