"""Diagramme en barres dessiné sur un Canvas Tkinter (aucune bibliothèque externe)."""
import tkinter as tk

from core.chart_layout import calculer_barres


class BarChart(tk.Canvas):
    """Usage : graphique.tracer(["Lun", "Mar"], [120, 80], titre="Ventes")."""

    COULEUR = "#2563eb"

    def __init__(self, master, hauteur: int = 230, **options):
        super().__init__(master, height=hauteur, background="white", highlightthickness=1,
                         highlightbackground="#d1d5db", **options)
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
            self.create_text(10, 12, anchor="w", text=titre, font=("Segoe UI", 10, "bold"), fill="#111827")
        if not valeurs:
            self.create_text(largeur / 2, hauteur / 2, text="Aucune donnée à afficher", fill="#9ca3af")
            return
        barres, _ = calculer_barres(valeurs, largeur, hauteur)
        base = barres[0][3]
        self.create_line(8, base, largeur - 8, base, fill="#9ca3af")
        coupe = max(int((largeur - 20) / len(valeurs) / 7), 3)      # nb de caractères lisibles par barre
        for (x0, y0, x1, y1), valeur, etiquette in zip(barres, valeurs, etiquettes):
            self.create_rectangle(x0, y0, x1, y1, fill=self.COULEUR, outline="")
            centre = (x0 + x1) / 2
            texte_valeur = f"{valeur:,.0f}".replace(",", " ")
            self.create_text(centre, y0 - 8, text=texte_valeur, font=("Segoe UI", 8), fill="#374151")
            texte = str(etiquette)
            if len(texte) > coupe:
                texte = texte[: coupe - 1] + "…"
            self.create_text(centre, base + 14, text=texte, font=("Segoe UI", 8), fill="#374151")
