"""Calcul de la géométrie d'un diagramme en barres (logique pure, testable)."""
from typing import List, Sequence, Tuple


def calculer_barres(valeurs: Sequence[float], largeur: int, hauteur: int,
                    marge_gauche: int = 12, marge_droite: int = 12,
                    marge_haut: int = 26, marge_bas: int = 44) -> Tuple[List[tuple], float]:
    """Retourne (rectangles, valeur_max).

    Chaque rectangle est (x0, y0, x1, y1) en pixels ; la hauteur d'une barre est proportionnelle
    à sa valeur (les valeurs négatives sont ramenées à 0).
    """
    n = len(valeurs)
    if n == 0:
        return [], 0.0
    positives = [max(float(v), 0.0) for v in valeurs]
    maximum = max(positives)
    zone_l = max(largeur - marge_gauche - marge_droite, n)
    zone_h = max(hauteur - marge_haut - marge_bas, 1)
    pas = zone_l / n
    largeur_barre = pas * 0.7
    base = marge_haut + zone_h
    echelle = zone_h / maximum if maximum > 0 else 0.0
    rectangles = []
    for i, v in enumerate(positives):
        x0 = marge_gauche + i * pas + (pas - largeur_barre) / 2
        rectangles.append((x0, base - v * echelle, x0 + largeur_barre, base))
    return rectangles, maximum
