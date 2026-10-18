"""Fournisseurs (RG-43 à RG-45)."""
from typing import Optional

from core.errors import BusinessError
from core.permissions import require
from db.connection import lecture, transaction


def lister_fournisseurs(user, inclure_inactifs: bool = True) -> list:
    require(user, "gerer_fournisseurs")
    requete = ("SELECT id_fournisseur, raison_sociale, telephone, email, adresse, "
               "delai_livraison_jours, actif FROM fournisseur")
    if not inclure_inactifs:
        requete += " WHERE actif = 1"
    requete += " ORDER BY raison_sociale"
    with lecture() as cur:
        cur.execute(requete)
        return cur.fetchall()


def _valider(raison_sociale: str, telephone: str, delai: Optional[int]) -> None:
    if not (raison_sociale or "").strip():
        raise BusinessError("La raison sociale est obligatoire.")
    if not (telephone or "").strip():
        raise BusinessError("Le téléphone est obligatoire (RG-43).")
    if delai is not None and delai < 0:
        raise BusinessError("Le délai de livraison doit être supérieur ou égal à 0.")


def creer_fournisseur(user, raison_sociale: str, telephone: str, email: str = "",
                      adresse: str = "", delai_livraison_jours: Optional[int] = None) -> int:
    require(user, "gerer_fournisseurs")
    _valider(raison_sociale, telephone, delai_livraison_jours)
    with transaction() as cur:
        cur.execute(
            "INSERT INTO fournisseur (raison_sociale, telephone, email, adresse, delai_livraison_jours) "
            "VALUES (%s, %s, %s, %s, %s)",
            (raison_sociale.strip(), telephone.strip(), (email or "").strip() or None,
             (adresse or "").strip() or None, delai_livraison_jours),
        )
        return cur.lastrowid


def modifier_fournisseur(user, id_fournisseur: int, raison_sociale: str, telephone: str,
                         email: str = "", adresse: str = "",
                         delai_livraison_jours: Optional[int] = None) -> None:
    require(user, "gerer_fournisseurs")
    _valider(raison_sociale, telephone, delai_livraison_jours)
    with transaction() as cur:
        cur.execute(
            "UPDATE fournisseur SET raison_sociale = %s, telephone = %s, email = %s, adresse = %s, "
            "delai_livraison_jours = %s WHERE id_fournisseur = %s",
            (raison_sociale.strip(), telephone.strip(), (email or "").strip() or None,
             (adresse or "").strip() or None, delai_livraison_jours, id_fournisseur),
        )


def changer_statut_fournisseur(user, id_fournisseur: int, actif: bool) -> None:
    """Désactive ou réactive un fournisseur (jamais de suppression, RG-44)."""
    require(user, "gerer_fournisseurs")
    with transaction() as cur:
        cur.execute("UPDATE fournisseur SET actif = %s WHERE id_fournisseur = %s",
                    (1 if actif else 0, id_fournisseur))
