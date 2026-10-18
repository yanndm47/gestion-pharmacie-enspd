"""Gestion des clients (RG-19 à RG-23)."""
from datetime import date

from core.errors import BusinessError
from core.formatting import parse_date
from core.permissions import require
from db.connection import lecture, transaction
from services.catalogue_service import _echapper_like


def rechercher_clients(user, terme: str = "", limite: int = 30) -> list:
    """Clients dont le nom, le prénom ou le téléphone contient `terme`."""
    require(user, "gerer_clients")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    with lecture() as cur:
        cur.execute(
            """
            SELECT id_client, nom, prenom, date_naissance, telephone
              FROM client
             WHERE nom LIKE %s OR prenom LIKE %s OR telephone LIKE %s
             ORDER BY nom, prenom
             LIMIT %s
            """,
            (motif, motif, motif, int(limite)),
        )
        return cur.fetchall()


def lister_clients(user, terme: str = "", limite: int = 200) -> list:
    """Fiches clients complètes, filtrées par nom, prénom ou téléphone."""
    require(user, "gerer_clients")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    with lecture() as cur:
        cur.execute(
            """
            SELECT id_client, nom, prenom, date_naissance, telephone, email, adresse
              FROM client
             WHERE nom LIKE %s OR prenom LIKE %s OR telephone LIKE %s
             ORDER BY nom, prenom
             LIMIT %s
            """,
            (motif, motif, motif, int(limite)),
        )
        return cur.fetchall()


def _valider(nom: str, prenom: str, date_naissance: str):
    nom, prenom = (nom or "").strip(), (prenom or "").strip()
    if not nom or not prenom:
        raise BusinessError("Le nom et le prénom sont obligatoires.")
    try:
        naissance = parse_date(date_naissance)
    except ValueError as e:
        raise BusinessError(str(e)) from e
    if naissance > date.today():
        raise BusinessError("La date de naissance ne peut pas être dans le futur.")
    return nom, prenom, naissance


def _vide_en_none(texte):
    return (texte or "").strip() or None


def creer_client(user, nom: str, prenom: str, date_naissance: str, telephone: str = "",
                 email: str = "", adresse: str = "") -> int:
    """Crée un client et retourne son identifiant.

    Nom, prénom et date de naissance obligatoires (RG-20) ; la base refuse
    les doublons sur ce triplet.
    """
    require(user, "gerer_clients")
    nom, prenom, naissance = _valider(nom, prenom, date_naissance)
    with transaction() as cur:
        cur.execute(
            "INSERT INTO client (nom, prenom, date_naissance, telephone, email, adresse) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nom, prenom, naissance, _vide_en_none(telephone), _vide_en_none(email),
             _vide_en_none(adresse)),
        )
        return cur.lastrowid


def modifier_client(user, id_client: int, nom: str, prenom: str, date_naissance: str,
                    telephone: str = "", email: str = "", adresse: str = "") -> None:
    """Modifie la fiche d'un client (un client n'est jamais supprimé, RG-22)."""
    require(user, "gerer_clients")
    nom, prenom, naissance = _valider(nom, prenom, date_naissance)
    with transaction() as cur:
        cur.execute(
            "UPDATE client SET nom = %s, prenom = %s, date_naissance = %s, telephone = %s, "
            "email = %s, adresse = %s WHERE id_client = %s",
            (nom, prenom, naissance, _vide_en_none(telephone), _vide_en_none(email),
             _vide_en_none(adresse), id_client),
        )


def historique_achats(user, id_client: int, limite: int = 200) -> list:
    """Ventes d'un client, les plus récentes d'abord (pharmacien : données de santé, RG-23)."""
    require(user, "gerer_ordonnances")
    with lecture() as cur:
        cur.execute(
            """
            SELECT v.id_vente, v.date_vente, v.total, v.statut, v.mode_paiement, v.id_ordonnance,
                   CONCAT(p.prenom, ' ', p.nom) AS vendeur
              FROM vente v
              JOIN personnel p ON p.id_personnel = v.id_personnel
             WHERE v.id_client = %s
             ORDER BY v.date_vente DESC, v.id_vente DESC
             LIMIT %s
            """,
            (id_client, int(limite)),
        )
        return cur.fetchall()


def historique_ordonnances(user, id_client: int, limite: int = 200) -> list:
    """Ordonnances d'un client, les plus récentes d'abord."""
    require(user, "gerer_ordonnances")
    with lecture() as cur:
        cur.execute(
            """
            SELECT id_ordonnance, date_prescription, date_validite, statut, nom_medecin
              FROM ordonnance
             WHERE id_client = %s
             ORDER BY date_prescription DESC, id_ordonnance DESC
             LIMIT %s
            """,
            (id_client, int(limite)),
        )
        return cur.fetchall()
