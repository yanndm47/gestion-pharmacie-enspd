"""Exceptions de l'application.

Règle : les couches basses (db, services) lèvent ces exceptions, et l'interface
les affiche à l'utilisateur. Le texte d'une BusinessError est toujours écrit
pour être lu tel quel par un utilisateur (pharmacien, caissier...).
"""


class PharmacieError(Exception):
    """Erreur technique ou métier de l'application."""


class BusinessError(PharmacieError):
    """Règle de gestion non respectée : le message est destiné à l'utilisateur."""


class PermissionDenied(BusinessError):
    """L'utilisateur n'a pas le droit d'effectuer cette action."""


class StockInsuffisant(BusinessError):
    """Quantité demandée supérieure au stock vendable."""

    def __init__(self, disponible: int, demande: int):
        self.disponible = disponible
        self.demande = demande
        super().__init__(
            f"stock insuffisant : {disponible} disponible(s) pour {demande} demandé(s)"
        )


class DatabaseUnavailable(PharmacieError):
    """Impossible de joindre ou d'utiliser la base de données."""
