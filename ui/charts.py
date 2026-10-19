"""Diagramme en barres dessiné sur un Canvas Tkinter (aucune bibliothèque externe)."""
import tkinter as tk

from core.chart_layout import calculer_barres
from ui import theme


class BarChart(tk.Canvas):
    """Usage : graphique.tracer(["Lun", "Mar"], [120, 80], titre="Ventes")."""

    COULEUR = theme.BLEU
    COULEUR_MAX = theme.JAUNE

    def __init__(self, master, hauteur: int = 230, **options):
        super().__init__(master, height=hauteur, background="white", highlightthickness=1,
                         highlightbackground=theme.BORDURE, **options)
        self._donnees = ([], [], "")
        self.bind("<Configure>", lambda _e: self._dessiner())

    def tracer(self, etiquettes, valeurs, titre: str = "") -> None:
        self._donnees = (list(etiquettes), [float(v or 0) for v in valeurs], titre)
        self._dessiner()

    def effacer(self) -> None:
        self._donnees = ([], [], "")
        self._dessiner()

    def _dessiner(self) -> None:
        self.delete("all")
        etiquettes, valeurs, titre = self._donnees
        largeur = max(int(self.winfo_width()), 300)
        hauteur = max(int(self.winfo_height()), 150)
        if titre:
            self.create_text(10, 12, anchor="w", text=titre, font=(theme.POLICE, 10, "bold"), fill=theme.BLEU)
        if not valeurs:
            self.create_text(largeur / 2, hauteur / 2, text="Aucune donnée à afficher", fill=theme.GRIS)
            return
        barres, _ = calculer_barres(valeurs, largeur, hauteur)
        base = barres[0][3]
        self.create_line(8, base, largeur - 8, base, fill=theme.BORDURE)
        plus_grand = max(range(len(valeurs)), key=lambda i: valeurs[i]) if len(valeurs) > 1 else -1
        coupe = max(int((largeur - 20) / len(valeurs) / 7), 3)      # nb de caractères lisibles par barre
        for i, ((x0, y0, x1, y1), valeur, etiquette) in enumerate(zip(barres, valeurs, etiquettes)):
            self.create_rectangle(x0, y0, x1, y1, fill=self.COULEUR_MAX if i == plus_grand else self.COULEUR, outline="")
            centre = (x0 + x1) / 2
            texte_valeur = f"{valeur:,.0f}".replace(",", " ")
            self.create_text(centre, y0 - 8, text=texte_valeur, font=(theme.POLICE, 8), fill=theme.TEXTE)
            texte = str(etiquette)
            if len(texte) > coupe:
                texte = texte[: coupe - 1] + "…"
            self.create_text(centre, base + 14, text=texte, font=(theme.POLICE, 8), fill=theme.TEXTE)
