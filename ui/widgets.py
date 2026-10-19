"""Composants réutilisables : tableaux à lignes alternées, cartes d'indicateurs."""
from tkinter import ttk

from ui import theme


class Tableau(ttk.Treeview):
    """Treeview dont une ligne sur deux est légèrement colorée (lecture plus facile)."""

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.tag_configure("impair", background=theme.BLEU_CLAIR)

    def insert(self, parent, index, iid=None, **options):
        tags = tuple(options.pop("tags", ()) or ())
        if len(self.get_children(parent)) % 2:
            tags += ("impair",)
        return super().insert(parent, index, iid=iid, tags=tags, **options)


def creer_arbre(parent, colonnes, **options):
    """Tableau avec barre de défilement.

    colonnes : liste de (cle, titre, largeur, ancrage). Retourne le cadre à placer
    (grid/pack) ; le tableau lui-même est dans `cadre.arbre`.
    """
    cadre = ttk.Frame(parent)
    cadre.columnconfigure(0, weight=1)
    cadre.rowconfigure(0, weight=1)
    arbre = Tableau(cadre, columns=[c[0] for c in colonnes], show="headings",
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


def creer_carte(parent, titre, variable):
    """Carte d'indicateur : filet jaune, titre gris, grande valeur bleue."""
    carte = ttk.Frame(parent, style="Carte.TFrame")
    ttk.Frame(carte, style="Jaune.TFrame", height=4).pack(fill="x")
    corps = ttk.Frame(carte, style="Carte.TFrame", padding=(16, 12))
    corps.pack(fill="both", expand=True)
    ttk.Label(corps, text=titre, style="CarteTitre.TLabel").pack(anchor="w")
    ttk.Label(corps, textvariable=variable, style="CarteValeur.TLabel").pack(anchor="w", pady=(4, 0))
    return carte


def vider(arbre):
    arbre.delete(*arbre.get_children())
