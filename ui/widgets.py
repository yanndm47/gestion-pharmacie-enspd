"""Petits composants réutilisables."""
from tkinter import ttk


def creer_arbre(parent, colonnes, **options):
    """Tableau (Treeview) avec barre de défilement.

    colonnes : liste de (cle, titre, largeur, ancrage). Retourne le cadre à placer
    (grid/pack) ; le tableau lui-même est dans `cadre.arbre`.
    """
    cadre = ttk.Frame(parent)
    cadre.columnconfigure(0, weight=1)
    cadre.rowconfigure(0, weight=1)
    arbre = ttk.Treeview(cadre, columns=[c[0] for c in colonnes], show="headings",
                         selectmode="browse", **options)
    for cle, titre, largeur, ancre in colonnes:
        arbre.heading(cle, text=titre)
        arbre.column(cle, width=largeur, anchor=ancre)
    defil = ttk.Scrollbar(cadre, orient="vertical", command=arbre.yview)
    arbre.configure(yscrollcommand=defil.set)
    arbre.grid(row=0, column=0, sticky="nsew")
    defil.grid(row=0, column=1, sticky="ns")
    cadre.arbre = arbre
    return cadre


def vider(arbre):
    arbre.delete(*arbre.get_children())
