"""Affichage uniforme des erreurs dans l'interface."""
from tkinter import messagebox

from core.errors import BusinessError, DatabaseUnavailable, PharmacieError


def essayer(parent, fonction, *args, **kwargs):
    """Appelle `fonction` ; en cas d'erreur, affiche un message clair.

    Retourne (True, résultat) si tout s'est bien passé, (False, None) sinon.
    Utilisation :
        ok, lignes = essayer(self, stats_service.top_medicaments, user)
        if not ok:
            return
    """
    try:
        return True, fonction(*args, **kwargs)
    except BusinessError as e:
        messagebox.showwarning("Action impossible", str(e), parent=parent)
    except DatabaseUnavailable as e:
        messagebox.showerror("Base de données", str(e), parent=parent)
    except PharmacieError as e:
        messagebox.showerror("Erreur", str(e), parent=parent)
    except Exception as e:  # bug inattendu : on l'affiche au lieu de planter en silence
        messagebox.showerror("Erreur inattendue", f"{type(e).__name__} : {e}", parent=parent)
    return False, None
