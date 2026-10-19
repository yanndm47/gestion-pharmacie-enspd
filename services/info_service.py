"""Informations techniques affichées sur la page Crédits (aucun droit particulier requis)."""
import platform

import config
from db.connection import lecture


def informations() -> dict:
    """Versions utiles au dépannage. Ne lève jamais d'exception : en cas de problème, un texte l'indique."""
    info = {"application": config.APP_VERSION, "python": platform.python_version(),
            "serveur": "indisponible", "base": config.DB_NAME}
    try:
        with lecture() as cur:
            cur.execute("SELECT VERSION() AS v")
            info["serveur"] = str(cur.fetchone()["v"])
    except Exception as erreur:          # la page Crédits doit toujours s'afficher
        info["serveur"] = f"indisponible ({type(erreur).__name__})"
    return info
