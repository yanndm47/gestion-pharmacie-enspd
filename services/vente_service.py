"""Ventes : création (avec répartition FEFO sur les lots), annulation, historique du jour.

La règle d'or : TOUTE la vente est écrite dans UNE transaction (RG-52). Si une
règle de gestion est violée (stock insuffisant, ordonnance manquante...), la
base lève une erreur (trigger) et rien n'est enregistré.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import config
from core.allocation import Lot, allouer_fefo
from core.errors import BusinessError, StockInsuffisant
from core.permissions import can, require
from core.ticket import formater_ticket
from db.connection import lecture, transaction

MODES_PAIEMENT = {
    "especes": "Espèces",
    "carte": "Carte",
    "mobile_money": "Mobile money",
}


@dataclass(frozen=True)
class LigneDemandee:
    id_medicament: int
    quantite: int


@dataclass(frozen=True)
class VenteCreee:
    id_vente: int
    total: Decimal
    nb_lignes: int


def _fusionner(lignes: List[LigneDemandee]) -> List[LigneDemandee]:
    """Regroupe les lignes d'un même médicament (le panier ne doit pas avoir de doublon)."""
    cumul: Dict[int, int] = {}
    for l in lignes:
        if l.quantite <= 0:
            raise BusinessError("Les quantités doivent être strictement positives.")
        cumul[l.id_medicament] = cumul.get(l.id_medicament, 0) + l.quantite
    return [LigneDemandee(i, q) for i, q in cumul.items()]


def _charger_medicaments(cur, ids: List[int]) -> dict:
    marqueurs = ", ".join(["%s"] * len(ids))
    cur.execute(
        f"SELECT id_medicament, nom_commercial, prix_vente, ordonnance_obligatoire, actif "
        f"FROM medicament WHERE id_medicament IN ({marqueurs})",
        tuple(ids),
    )
    meds = {m["id_medicament"]: m for m in cur.fetchall()}
    for i in ids:
        if i not in meds or not meds[i]["actif"]:
            raise BusinessError("Un médicament du panier n'existe plus ou est désactivé.")
    return meds


def _charger_lots_verrouilles(cur, id_medicament: int) -> List[Lot]:
    """Lots vendables d'un médicament. FOR UPDATE verrouille ces lignes jusqu'à la fin
    de la transaction : deux caisses ne peuvent pas vendre les mêmes unités."""
    cur.execute(
        """
        SELECT id_stock, quantite_restante, date_peremption
          FROM stock
         WHERE id_medicament = %s
           AND statut = 'disponible'
           AND quantite_restante > 0
           AND date_peremption >= CURDATE()
         ORDER BY date_peremption, id_stock
           FOR UPDATE
        """,
        (id_medicament,),
    )
    return [Lot(r["id_stock"], r["quantite_restante"], r["date_peremption"]) for r in cur.fetchall()]


def creer_vente(
    user,
    lignes: List[LigneDemandee],
    id_client: Optional[int] = None,
    id_ordonnance: Optional[int] = None,
    mode_paiement: str = "especes",
) -> VenteCreee:
    """Enregistre une vente complète et retourne son identifiant et son total.

    - la caisse et le pharmacien peuvent vendre des médicaments libres ;
    - seul le pharmacien peut vendre sur ordonnance (RG-38) ;
    - le prix est celui du catalogue au moment de la vente (RG-36) ;
    - les lots sont consommés par ordre de péremption (RG-14).
    """
    require(user, "vendre_libre")
    if id_ordonnance is not None:
        require(user, "vendre_ordonnance")
    if not lignes:
        raise BusinessError("Le panier est vide.")
    if mode_paiement not in MODES_PAIEMENT:
        raise BusinessError("Mode de paiement invalide.")

    demandees = _fusionner(list(lignes))

    with transaction() as cur:
        meds = _charger_medicaments(cur, [l.id_medicament for l in demandees])

        for l in demandees:
            m = meds[l.id_medicament]
            if m["ordonnance_obligatoire"] and id_ordonnance is None:
                raise BusinessError(
                    f"« {m['nom_commercial']} » nécessite une ordonnance : "
                    "choisissez le client puis son ordonnance (pharmacien uniquement)."
                )

        cur.execute(
            "INSERT INTO vente (id_personnel, id_client, id_ordonnance, mode_paiement) "
            "VALUES (%s, %s, %s, %s)",
            (user.id_personnel, id_client, id_ordonnance, mode_paiement),
        )
        id_vente = cur.lastrowid

        nb_lignes = 0
        for l in demandees:
            m = meds[l.id_medicament]
            lots = _charger_lots_verrouilles(cur, l.id_medicament)
            try:
                repartition = allouer_fefo(lots, l.quantite)
            except StockInsuffisant as e:
                raise BusinessError(f"{m['nom_commercial']} : {e}") from e
            for a in repartition:
                cur.execute(
                    "INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_vente, a.id_stock, a.quantite, m["prix_vente"]),
                )
                nb_lignes += 1

        # Le total est calculé par le trigger de la base (RG-37) : on le relit
        cur.execute("SELECT total FROM vente WHERE id_vente = %s", (id_vente,))
        total = cur.fetchone()["total"]

    return VenteCreee(id_vente=id_vente, total=total, nb_lignes=nb_lignes)


def annuler_vente(user, id_vente: int) -> None:
    """Annule une vente validée : le trigger remet les quantités en stock (RG-41)."""
    require(user, "annuler_vente")
    with transaction() as cur:
        cur.execute("SELECT statut FROM vente WHERE id_vente = %s FOR UPDATE", (id_vente,))
        ligne = cur.fetchone()
        if ligne is None:
            raise BusinessError("Cette vente n'existe pas.")
        if ligne["statut"] == "annulee":
            raise BusinessError("Cette vente est déjà annulée.")
        cur.execute("UPDATE vente SET statut = 'annulee' WHERE id_vente = %s", (id_vente,))


def ventes_du_jour(user) -> list:
    """Ventes enregistrées aujourd'hui (la caisse n'a accès qu'à cet historique)."""
    require(user, "stats_jour")
    with lecture() as cur:
        cur.execute(
            """
            SELECT v.id_vente, v.date_vente, v.total, v.statut, v.mode_paiement,
                   CONCAT(p.prenom, ' ', p.nom) AS vendeur
              FROM vente v
              JOIN personnel p ON p.id_personnel = v.id_personnel
             WHERE DATE(v.date_vente) = CURDATE()
             ORDER BY v.date_vente DESC, v.id_vente DESC
            """
        )
        return cur.fetchall()


PERIODES = {"Aujourd'hui": 0, "7 derniers jours": 7, "30 derniers jours": 30, "Tout l'historique": None}


def lister_ventes(user, jours=0, statut=None, limite: int = 500) -> list:
    """Ventes récentes (jours=0 : aujourd'hui, None : tout). La caisse est limitée à aujourd'hui."""
    require(user, "stats_jour")
    if statut is not None and statut not in ("validee", "annulee"):
        raise BusinessError("Statut de vente invalide.")
    if not can(user.role, "stats_completes"):
        jours = 0                      # droits réduits : ventes du jour uniquement
    requete = (
        "SELECT v.id_vente, v.date_vente, v.total, v.statut, v.mode_paiement, v.id_ordonnance, "
        "       CONCAT(p.prenom, ' ', p.nom) AS vendeur, CONCAT(c.prenom, ' ', c.nom) AS client "
        "  FROM vente v "
        "  JOIN personnel p ON p.id_personnel = v.id_personnel "
        "  LEFT JOIN client c ON c.id_client = v.id_client "
        " WHERE 1 = 1"
    )
    params = []
    if jours is not None:
        debut = datetime.combine(date.today() - timedelta(days=int(jours)), time.min)
        requete += " AND v.date_vente >= %s"
        params.append(debut)
    if statut is not None:
        requete += " AND v.statut = %s"
        params.append(statut)
    requete += " ORDER BY v.date_vente DESC, v.id_vente DESC LIMIT %s"
    params.append(int(limite))
    with lecture() as cur:
        cur.execute(requete, tuple(params))
        return cur.fetchall()


def detail_vente(user, id_vente: int) -> dict:
    """{'vente': en-tête, 'lignes': lignes avec lot et sous-total}."""
    require(user, "stats_jour")
    with lecture() as cur:
        cur.execute(
            "SELECT v.id_vente, v.date_vente, v.total, v.statut, v.mode_paiement, v.id_ordonnance, "
            "       CONCAT(p.prenom, ' ', p.nom) AS vendeur, CONCAT(c.prenom, ' ', c.nom) AS client "
            "  FROM vente v "
            "  JOIN personnel p ON p.id_personnel = v.id_personnel "
            "  LEFT JOIN client c ON c.id_client = v.id_client "
            " WHERE v.id_vente = %s",
            (id_vente,),
        )
        vente = cur.fetchone()
        if vente is None:
            raise BusinessError("Cette vente n'existe pas.")
        if not can(user.role, "stats_completes") and vente["date_vente"].date() != date.today():
            raise BusinessError("Les ventes des jours précédents sont réservées au pharmacien.")
        cur.execute(
            "SELECT m.nom_commercial, s.numero_lot, lv.quantite, lv.prix_unitaire, "
            "       lv.quantite * lv.prix_unitaire AS sous_total "
            "  FROM ligne_vente lv "
            "  JOIN stock s      ON s.id_stock = lv.id_stock "
            "  JOIN medicament m ON m.id_medicament = s.id_medicament "
            " WHERE lv.id_vente = %s "
            " ORDER BY m.nom_commercial, s.date_peremption",
            (id_vente,),
        )
        return {"vente": vente, "lignes": cur.fetchall()}


def texte_ticket(user, id_vente: int) -> str:
    """Ticket de caisse prêt à afficher, enregistrer ou imprimer."""
    detail = detail_vente(user, id_vente)
    v = detail["vente"]
    return formater_ticket(
        config.NOM_PHARMACIE, v["id_vente"], v["date_vente"], v["vendeur"], v["client"],
        detail["lignes"], v["total"], MODES_PAIEMENT.get(v["mode_paiement"], v["mode_paiement"]),
        v["statut"],
    )
