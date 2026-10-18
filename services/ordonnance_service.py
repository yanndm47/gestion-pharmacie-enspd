"""Ordonnances : saisie, liste, détail, et lecture pour la caisse (RG-24 à RG-31)."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

import config
from core.errors import BusinessError
from core.permissions import require
from db.connection import lecture, transaction
from services.catalogue_service import _echapper_like

STATUTS = {
    "en_attente": "En attente",
    "partielle": "Partielle",
    "soldee": "Soldée",
    "expiree": "Expirée",
}


@dataclass(frozen=True)
class LigneOrdonnance:
    id_medicament: int
    quantite_prescrite: int
    posologie: str
    duree_traitement_jours: Optional[int] = None


def creer_ordonnance(
    user,
    id_client: int,
    nom_medecin: str,
    numero_ordre_medecin: str,
    date_prescription: date,
    lignes: List[LigneOrdonnance],
) -> int:
    """Enregistre une ordonnance et ses lignes en une transaction ; retourne son numéro.

    - réservé au pharmacien (RG-30) ;
    - validité = date de prescription + VALIDITE_ORDONNANCE_JOURS (RG-25) ;
    - au moins une ligne, un médicament une seule fois par ordonnance (RG-26, RG-28).
    Le trigger SQL contrôle en plus le rôle et la date (pas dans le futur).
    """
    require(user, "gerer_ordonnances")
    if not id_client:
        raise BusinessError("Choisissez le client concerné par l'ordonnance.")
    nom_medecin = (nom_medecin or "").strip()
    if not nom_medecin:
        raise BusinessError("Le nom du médecin prescripteur est obligatoire.")
    if not lignes:
        raise BusinessError("Une ordonnance doit comporter au moins une ligne (RG-26).")

    vus = set()
    for l in lignes:
        if l.id_medicament in vus:
            raise BusinessError("Un même médicament ne peut figurer qu'une fois sur l'ordonnance (RG-28).")
        vus.add(l.id_medicament)
        if l.quantite_prescrite <= 0:
            raise BusinessError("Les quantités prescrites doivent être strictement positives.")
        if not (l.posologie or "").strip():
            raise BusinessError("La posologie est obligatoire pour chaque ligne.")
        if l.duree_traitement_jours is not None and l.duree_traitement_jours <= 0:
            raise BusinessError("La durée de traitement doit être strictement positive.")

    aujourdhui = date.today()
    if date_prescription > aujourdhui:
        raise BusinessError("La date de prescription ne peut pas être dans le futur (RG-25).")
    validite = date_prescription + timedelta(days=config.VALIDITE_ORDONNANCE_JOURS)
    if validite < aujourdhui:
        raise BusinessError(
            f"Cette ordonnance est déjà expirée : elle n'est valable que "
            f"{config.VALIDITE_ORDONNANCE_JOURS} jours après sa date de prescription."
        )

    with transaction() as cur:
        marqueurs = ", ".join(["%s"] * len(lignes))
        cur.execute(
            f"SELECT id_medicament FROM medicament WHERE actif = 1 AND id_medicament IN ({marqueurs})",
            tuple(l.id_medicament for l in lignes),
        )
        if len(cur.fetchall()) != len(lignes):
            raise BusinessError("Un médicament de l'ordonnance n'existe plus ou est désactivé.")

        cur.execute(
            "INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, "
            "date_prescription, date_validite) VALUES (%s, %s, %s, %s, %s, %s)",
            (id_client, user.id_personnel, nom_medecin,
             (numero_ordre_medecin or "").strip() or None, date_prescription, validite),
        )
        id_ordonnance = cur.lastrowid
        for l in lignes:
            cur.execute(
                "INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, "
                "posologie, duree_traitement_jours) VALUES (%s, %s, %s, %s, %s)",
                (id_ordonnance, l.id_medicament, l.quantite_prescrite,
                 l.posologie.strip(), l.duree_traitement_jours),
            )
    return id_ordonnance


def lister_ordonnances(user, statut: Optional[str] = None, terme: str = "", limite: int = 200) -> list:
    """Ordonnances récentes, filtrables par statut et par client ou médecin."""
    require(user, "gerer_ordonnances")
    if statut is not None and statut not in STATUTS:
        raise BusinessError("Statut d'ordonnance invalide.")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    requete = (
        "SELECT o.id_ordonnance, o.date_prescription, o.date_validite, o.statut, o.nom_medecin, "
        "       CONCAT(c.nom, ' ', c.prenom) AS client "
        "  FROM ordonnance o JOIN client c ON c.id_client = o.id_client "
        " WHERE (c.nom LIKE %s OR c.prenom LIKE %s OR o.nom_medecin LIKE %s)"
    )
    params = [motif, motif, motif]
    if statut is not None:
        requete += " AND o.statut = %s"
        params.append(statut)
    requete += " ORDER BY o.date_prescription DESC, o.id_ordonnance DESC LIMIT %s"
    params.append(int(limite))
    with lecture() as cur:
        cur.execute(requete, tuple(params))
        return cur.fetchall()


def detail_ordonnance(user, id_ordonnance: int) -> list:
    """Lignes d'une ordonnance : prescrit, délivré, reste, posologie, durée."""
    require(user, "gerer_ordonnances")
    with lecture() as cur:
        cur.execute(
            """
            SELECT d.nom_commercial, d.quantite_prescrite, d.quantite_delivree,
                   d.quantite_prescrite - d.quantite_delivree AS reste_a_delivrer,
                   lo.posologie, lo.duree_traitement_jours
              FROM v_ordonnance_delivrance d
              JOIN ligne_ordonnance lo ON lo.id_ordonnance = d.id_ordonnance
                                      AND lo.id_medicament = d.id_medicament
             WHERE d.id_ordonnance = %s
             ORDER BY d.nom_commercial
            """,
            (id_ordonnance,),
        )
        return cur.fetchall()


def ordonnances_ouvertes(user, id_client: int) -> list:
    """Ordonnances d'un client encore utilisables : non soldées et non expirées (RG-31)."""
    require(user, "vendre_ordonnance")
    with lecture() as cur:
        cur.execute(
            """
            SELECT id_ordonnance, nom_medecin, date_prescription, date_validite, statut
              FROM ordonnance
             WHERE id_client = %s
               AND statut IN ('en_attente', 'partielle')
               AND date_validite >= CURDATE()
             ORDER BY date_validite, id_ordonnance
            """,
            (id_client,),
        )
        return cur.fetchall()


def lignes_a_delivrer(user, id_ordonnance: int) -> list:
    """Médicaments d'une ordonnance avec la quantité restant à délivrer."""
    require(user, "vendre_ordonnance")
    with lecture() as cur:
        cur.execute(
            """
            SELECT id_medicament, nom_commercial, quantite_prescrite, quantite_delivree,
                   quantite_prescrite - quantite_delivree AS reste_a_delivrer
              FROM v_ordonnance_delivrance
             WHERE id_ordonnance = %s
             ORDER BY nom_commercial
            """,
            (id_ordonnance,),
        )
        return cur.fetchall()
