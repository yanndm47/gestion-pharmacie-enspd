"""Règles d'affichage du stock (logique pure, testable seule)."""
from datetime import date
from typing import Optional

import config


def niveau_peremption(date_peremption: date, aujourdhui: Optional[date] = None,
                      seuil_jours: Optional[int] = None) -> str:
    """'perime' | 'urgent' (30 jours ou moins) | 'a_surveiller' (jusqu'au seuil) | 'ok'."""
    jour = aujourdhui or date.today()
    seuil = seuil_jours if seuil_jours is not None else config.SEUIL_PEREMPTION_JOURS
    reste = (date_peremption - jour).days
    if reste < 0:
        return "perime"
    if reste <= 30:
        return "urgent"
    if reste <= seuil:
        return "a_surveiller"
    return "ok"


def etat_stock(stock_disponible: int, seuil_min: int, actif: bool = True) -> str:
    """Libellé d'état d'un médicament : Désactivé, Rupture, Sous le seuil ou OK (RG-16)."""
    if not actif:
        return "Désactivé"
    if stock_disponible <= 0:
        return "Rupture"
    if stock_disponible < seuil_min:
        return "Sous le seuil"
    return "OK"
