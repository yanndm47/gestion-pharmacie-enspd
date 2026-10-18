"""Commandes aux fournisseurs et réceptions de lots (RG-55 à RG-60, RG-07 à RG-12)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from core.errors import BusinessError
from core.permissions import require
from db.connection import lecture, transaction

STATUTS_COMMANDE = {
    "en_cours": "En cours",
    "partielle": "Partielle",
    "recue": "Reçue",
    "annulee": "Annulée",
}


@dataclass(frozen=True)
class LigneCommande:
    id_medicament: int
    quantite_commandee: int
    prix_achat_prevu: Optional[Decimal] = None


def creer_commande(user, id_fournisseur: int, date_livraison_prevue: Optional[date],
                   lignes: List[LigneCommande]) -> int:
    """Crée une commande et ses lignes en une transaction ; retourne son numéro.

    Réservé au pharmacien. Les triggers SQL vérifient en plus que le fournisseur
    et les médicaments sont actifs (RG-44, RG-05).
    """
    require(user, "gerer_fournisseurs")
    if not id_fournisseur:
        raise BusinessError("Choisissez le fournisseur.")
    if not lignes:
        raise BusinessError("Une commande doit comporter au moins une ligne (RG-56).")
    vus = set()
    for l in lignes:
        if l.id_medicament in vus:
            raise BusinessError("Un même médicament ne peut figurer qu'une fois par commande (RG-56).")
        vus.add(l.id_medicament)
        if l.quantite_commandee <= 0:
            raise BusinessError("Les quantités commandées doivent être strictement positives.")
        if l.prix_achat_prevu is not None and l.prix_achat_prevu < 0:
            raise BusinessError("Le prix d'achat prévu ne peut pas être négatif.")
    if date_livraison_prevue is not None and date_livraison_prevue < date.today():
        raise BusinessError("La date de livraison prévue ne peut pas être dans le passé.")

    with transaction() as cur:
        cur.execute(
            "INSERT INTO commande (id_fournisseur, id_personnel, date_livraison_prevue) "
            "VALUES (%s, %s, %s)",
            (id_fournisseur, user.id_personnel, date_livraison_prevue),
        )
        id_commande = cur.lastrowid
        for l in lignes:
            cur.execute(
                "INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, "
                "prix_achat_prevu) VALUES (%s, %s, %s, %s)",
                (id_commande, l.id_medicament, l.quantite_commandee, l.prix_achat_prevu),
            )
    return id_commande


def lister_commandes(user, statut: Optional[str] = None, limite: int = 200) -> list:
    require(user, "gerer_fournisseurs")
    if statut is not None and statut not in STATUTS_COMMANDE:
        raise BusinessError("Statut de commande invalide.")
    requete = (
        "SELECT c.id_commande, c.date_commande, c.date_livraison_prevue, c.statut, "
        "       f.raison_sociale AS fournisseur, CONCAT(p.prenom, ' ', p.nom) AS passee_par "
        "  FROM commande c "
        "  JOIN fournisseur f ON f.id_fournisseur = c.id_fournisseur "
        "  JOIN personnel p   ON p.id_personnel = c.id_personnel"
    )
    params = []
    if statut is not None:
        requete += " WHERE c.statut = %s"
        params.append(statut)
    requete += " ORDER BY c.date_commande DESC, c.id_commande DESC LIMIT %s"
    params.append(int(limite))
    with lecture() as cur:
        cur.execute(requete, tuple(params))
        return cur.fetchall()


def detail_commande(user, id_commande: int) -> list:
    """Lignes d'une commande : commandé, reçu, reste à recevoir."""
    require(user, "gerer_fournisseurs")
    with lecture() as cur:
        cur.execute(
            """
            SELECT lc.id_medicament, m.nom_commercial, lc.quantite_commandee, lc.prix_achat_prevu,
                   COALESCE(r.qte, 0) AS quantite_recue,
                   lc.quantite_commandee - COALESCE(r.qte, 0) AS reste_a_recevoir
              FROM ligne_commande lc
              JOIN medicament m ON m.id_medicament = lc.id_medicament
              LEFT JOIN (SELECT id_medicament, SUM(quantite_initiale) AS qte
                           FROM stock WHERE id_commande = %s GROUP BY id_medicament) r
                     ON r.id_medicament = lc.id_medicament
             WHERE lc.id_commande = %s
             ORDER BY m.nom_commercial
            """,
            (id_commande, id_commande),
        )
        return cur.fetchall()


def receptionner(user, id_commande: int, id_medicament: int, numero_lot: str,
                 date_peremption: date, quantite: int, prix_achat: Decimal,
                 date_reception: Optional[date] = None) -> int:
    """Enregistre la réception d'un lot (crée une ligne de stock) ; retourne son identifiant.

    Les triggers vérifient que le médicament figure dans la commande, que la commande
    n'est pas annulée et que le lot n'est pas déjà périmé, puis mettent à jour le
    statut de la commande (RG-56, RG-58, RG-59).
    """
    require(user, "gerer_lots")
    numero_lot = (numero_lot or "").strip()
    if not numero_lot:
        raise BusinessError("Le numéro de lot est obligatoire.")
    if quantite <= 0:
        raise BusinessError("La quantité reçue doit être strictement positive (RG-11).")
    if prix_achat is None or prix_achat < 0:
        raise BusinessError("Le prix d'achat ne peut pas être négatif.")
    reception = date_reception or date.today()
    if date_peremption <= reception:
        raise BusinessError("La date de péremption doit être postérieure à la date de réception (RG-10).")

    with transaction() as cur:
        cur.execute(
            "INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, "
            "date_peremption, quantite_initiale, quantite_restante, prix_achat) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (id_medicament, id_commande, numero_lot, reception, date_peremption,
             quantite, quantite, prix_achat),
        )
        return cur.lastrowid


def annuler_commande(user, id_commande: int) -> None:
    """Annule une commande sans aucune réception (RG-59)."""
    require(user, "gerer_fournisseurs")
    with transaction() as cur:
        cur.execute("SELECT statut FROM commande WHERE id_commande = %s FOR UPDATE", (id_commande,))
        ligne = cur.fetchone()
        if ligne is None:
            raise BusinessError("Cette commande n'existe pas.")
        if ligne["statut"] != "en_cours":
            raise BusinessError("Seule une commande en cours, sans aucune réception, peut être annulée.")
        cur.execute("UPDATE commande SET statut = 'annulee' WHERE id_commande = %s", (id_commande,))
