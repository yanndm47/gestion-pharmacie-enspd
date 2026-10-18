"""Droits par profil (tableau 2.3 du document « Règles de gestion »).

Les droits sont vérifiés ICI (côté application) en plus des triggers SQL qui
protègent les données quoi qu'il arrive.
"""
from core.errors import PermissionDenied

ROLES = ("pharmacien", "caissier", "administrateur")

ROLE_LABELS = {
    "pharmacien": "Pharmacien",
    "caissier": "Personnel de caisse",
    "administrateur": "Administrateur",
}

PERMISSIONS = {
    # Personnel de caisse : droits les plus réduits
    "caissier": {
        "consulter_catalogue",
        "vendre_libre",
        "gerer_clients",
        "stats_jour",
    },
    # Pharmacien : toutes les opérations métier, pas l'administration technique
    "pharmacien": {
        "consulter_catalogue",
        "gerer_catalogue",
        "gerer_lots",
        "gerer_clients",
        "vendre_libre",
        "vendre_ordonnance",
        "gerer_ordonnances",
        "annuler_vente",
        "gerer_fournisseurs",
        "stats_jour",
        "stats_completes",
    },
    # Administrateur : comptes, sauvegardes, lecture des statistiques
    "administrateur": {
        "consulter_catalogue",
        "stats_jour",
        "stats_completes",
        "gerer_comptes",
        "sauvegarde",
    },
}


def can(role: str, permission: str) -> bool:
    """Vrai si ce rôle possède cette permission."""
    return permission in PERMISSIONS.get(role, set())


def require(user, permission: str) -> None:
    """Lève PermissionDenied si l'utilisateur n'a pas la permission."""
    if user is None or not can(user.role, permission):
        raise PermissionDenied("Vous n'avez pas le droit d'effectuer cette action.")
