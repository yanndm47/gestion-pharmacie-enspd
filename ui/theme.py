"""Charte graphique ENSPD : bleu et jaune.

TOUTES les couleurs et la police sont ici. Pour ajuster la charte (par exemple avec les codes
exacts du logo de l'école), modifiez uniquement les constantes ci-dessous : l'application entière
suivra, sans toucher aux écrans.
"""
import tkinter as tk
from tkinter import ttk

# --- Palette -------------------------------------------------------------------------------------
BLEU = "#0B3A8C"          # bleu principal (en-tête, titres, boutons)
BLEU_FONCE = "#082A66"    # texte sur fond jaune, survol
BLEU_MOYEN = "#3B63B8"    # survol des boutons
BLEU_CLAIR = "#E6ECF8"    # fonds discrets, lignes alternées
JAUNE = "#F9B200"         # accent (onglet actif, bouton principal, sélection)
JAUNE_FONCE = "#D99A00"
JAUNE_CLAIR = "#FFF3C9"
FOND = "#F3F5FA"          # fond des pages
BLANC = "#FFFFFF"
TEXTE = "#1B2433"
GRIS = "#6B7280"
BORDURE = "#D5DBE8"
ROUGE = "#C62828"
ORANGE = "#C2570C"
VERT = "#2E7D32"
POLICE = "Segoe UI"


def appliquer(racine) -> None:
    """Applique la charte à tous les composants ttk de l'application."""
    st = ttk.Style(racine)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    racine.configure(background=FOND)
    st.configure(".", background=FOND, foreground=TEXTE, font=(POLICE, 10), bordercolor=BORDURE,
                 focuscolor=JAUNE, troughcolor=BLEU_CLAIR)

    # Cadres et libellés
    st.configure("TFrame", background=FOND)
    st.configure("TLabel", background=FOND, foreground=TEXTE)
    st.configure("Titre.TLabel", font=(POLICE, 17, "bold"), foreground=BLEU)
    st.configure("Sous.TLabel", foreground=GRIS)
    st.configure("Total.TLabel", font=(POLICE, 22, "bold"), foreground=BLEU)
    st.configure("Carte.TFrame", background=BLANC, bordercolor=BORDURE, relief="solid", borderwidth=1)
    st.configure("Carte.TLabel", background=BLANC, foreground=TEXTE)
    st.configure("CarteTitre.TLabel", background=BLANC, foreground=GRIS, font=(POLICE, 10))
    st.configure("CarteValeur.TLabel", background=BLANC, foreground=BLEU, font=(POLICE, 24, "bold"))
    st.configure("Jaune.TFrame", background=JAUNE)
    st.configure("Entete.TFrame", background=BLEU)
    st.configure("Entete.TLabel", background=BLEU, foreground=BLANC, font=(POLICE, 11))
    st.configure("Sigle.TLabel", background=BLEU, foreground=JAUNE, font=(POLICE, 20, "bold"))
    st.configure("Panneau.TFrame", background=BLEU)
    st.configure("PanneauTitre.TLabel", background=BLEU, foreground=BLANC, font=(POLICE, 24, "bold"))
    st.configure("PanneauTexte.TLabel", background=BLEU, foreground="#C9D6F2", font=(POLICE, 11))
    st.configure("PanneauJaune.TLabel", background=BLEU, foreground=JAUNE, font=(POLICE, 12, "bold"))

    st.configure("TLabelframe", background=FOND, bordercolor=BORDURE, relief="solid", borderwidth=1)
    st.configure("TLabelframe.Label", background=FOND, foreground=BLEU, font=(POLICE, 10, "bold"))

    # Boutons : discret par défaut, bleu pour les actions, jaune pour l'action principale
    st.configure("TButton", background=BLEU_CLAIR, foreground=BLEU, padding=(12, 6), borderwidth=0,
                 font=(POLICE, 10, "bold"), relief="flat")
    st.map("TButton", background=[("pressed", BORDURE), ("active", "#D4DEF3"), ("disabled", FOND)],
           foreground=[("disabled", "#9AA5BC")])
    st.configure("Primary.TButton", background=BLEU, foreground=BLANC)
    st.map("Primary.TButton", background=[("pressed", BLEU_FONCE), ("active", BLEU_MOYEN)])
    st.configure("Accent.TButton", background=JAUNE, foreground=BLEU_FONCE, padding=(14, 8))
    st.map("Accent.TButton", background=[("pressed", JAUNE_FONCE), ("active", "#FFC72E")])
    st.configure("Entete.TButton", background=BLEU_MOYEN, foreground=BLANC)
    st.map("Entete.TButton", background=[("pressed", BLEU_FONCE), ("active", "#4F78CC")])

    # Champs de saisie
    for nom in ("TEntry", "TCombobox", "TSpinbox"):
        st.configure(nom, fieldbackground=BLANC, background=BLANC, foreground=TEXTE, padding=5,
                     bordercolor=BORDURE, lightcolor=BORDURE, darkcolor=BORDURE)
        st.map(nom, bordercolor=[("focus", BLEU)], lightcolor=[("focus", BLEU)])
    st.map("TCombobox", fieldbackground=[("readonly", BLANC)], foreground=[("readonly", TEXTE)])
    racine.option_add("*TCombobox*Listbox.selectBackground", JAUNE)
    racine.option_add("*TCombobox*Listbox.selectForeground", BLEU_FONCE)

    # Onglets
    st.configure("TNotebook", background=FOND, borderwidth=0, tabmargins=(0, 6, 0, 0))
    st.configure("TNotebook.Tab", background=BLEU_CLAIR, foreground=BLEU, padding=(18, 9),
                 font=(POLICE, 10, "bold"), borderwidth=0)
    st.map("TNotebook.Tab", background=[("selected", JAUNE), ("active", "#D4DEF3")],
           foreground=[("selected", BLEU_FONCE)], expand=[("selected", (0, 0, 0, 0))])

    # Tableaux
    st.configure("Treeview", background=BLANC, fieldbackground=BLANC, foreground=TEXTE, rowheight=28,
                 bordercolor=BORDURE, borderwidth=0, font=(POLICE, 10))
    st.map("Treeview", background=[("selected", JAUNE)], foreground=[("selected", BLEU_FONCE)])
    st.configure("Treeview.Heading", background=BLEU, foreground=BLANC, font=(POLICE, 10, "bold"),
                 padding=(8, 7), relief="flat", borderwidth=0)
    st.map("Treeview.Heading", background=[("active", BLEU_MOYEN)])

    st.configure("TScrollbar", background=BLEU_CLAIR, troughcolor=FOND, arrowcolor=BLEU, bordercolor=FOND)
    st.configure("TCheckbutton", background=FOND)
