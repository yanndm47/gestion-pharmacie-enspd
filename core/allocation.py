"""Répartition d'une quantité vendue entre les lots (règle RG-14, FEFO).

FEFO = First Expired, First Out : on vend d'abord le lot dont la date de
péremption est la plus proche. Une vente peut donc porter sur plusieurs lots,
ce qui produit plusieurs lignes de vente (une par lot).

Ce module ne dépend ni de la base ni de l'interface : il est testable seul.
"""
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional

from core.errors import StockInsuffisant


@dataclass(frozen=True)
class Lot:
    id_stock: int
    quantite_restante: int
    date_peremption: date


@dataclass(frozen=True)
class Allocation:
    id_stock: int
    quantite: int


def allouer_fefo(
    lots: Iterable[Lot], quantite: int, aujourdhui: Optional[date] = None
) -> List[Allocation]:
    """Répartit `quantite` unités sur les lots, du plus proche péremption au plus lointain.

    - ignore les lots vides et les lots périmés (RG-13) ;
    - lève StockInsuffisant si le total vendable est inférieur à la demande.
    """
    if quantite <= 0:
        raise ValueError("La quantité doit être strictement positive.")
    jour = aujourdhui or date.today()

    candidats = sorted(
        (l for l in lots if l.quantite_restante > 0 and l.date_peremption >= jour),
        key=lambda l: (l.date_peremption, l.id_stock),
    )
    disponible = sum(l.quantite_restante for l in candidats)
    if disponible < quantite:
        raise StockInsuffisant(disponible, quantite)

    restant = quantite
    resultat: List[Allocation] = []
    for lot in candidats:
        prise = min(lot.quantite_restante, restant)
        resultat.append(Allocation(lot.id_stock, prise))
        restant -= prise
        if restant == 0:
            break
    return resultat
