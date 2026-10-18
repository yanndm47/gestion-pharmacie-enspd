"""Stock et catalogue : état par médicament, lots, gestion des médicaments (RG-01 à RG-18)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from core.errors import BusinessError
from core.permissions import require
from db.connection import lecture, transaction
from services.catalogue_service import _echapper_like

STATUTS_LOT = {"disponible": "Disponible", "epuise": "Épuisé", "perime": "Périmé", "retire": "Retiré"}


@dataclass(frozen=True)
class MedicamentSaisie:
    nom_commercial: str
    dci: str
    forme: str
    dosage: str
    categorie: str
    prix_vente: Decimal
    ordonnance_obligatoire: bool
    seuil_min: int


def etat_stock(user, terme: str = "") -> list:
    """Un enregistrement par médicament (actif ou non) avec son stock vendable (RG-15)."""
    require(user, "consulter_catalogue")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    with lecture() as cur:
        cur.execute(
            """
            SELECT m.id_medicament, m.nom_commercial, m.dci, m.forme, m.dosage, m.categorie,
                   m.prix_vente, m.ordonnance_obligatoire, m.seuil_min, m.actif,
                   COALESCE(SUM(CASE WHEN s.statut = 'disponible' AND s.date_peremption >= CURDATE()
                                     THEN s.quantite_restante END), 0) AS stock_disponible
              FROM medicament m
              LEFT JOIN stock s ON s.id_medicament = m.id_medicament
             WHERE m.nom_commercial LIKE %s OR m.dci LIKE %s
             GROUP BY m.id_medicament, m.nom_commercial, m.dci, m.forme, m.dosage, m.categorie,
                      m.prix_vente, m.ordonnance_obligatoire, m.seuil_min, m.actif
             ORDER BY m.nom_commercial
            """,
            (motif, motif),
        )
        return cur.fetchall()


def lister_lots(user, terme: str = "", statut: Optional[str] = None, limite: int = 300) -> list:
    """Lots avec leur médicament et leur fournisseur (retrouvé via la commande)."""
    require(user, "consulter_catalogue")
    if statut is not None and statut not in STATUTS_LOT:
        raise BusinessError("Statut de lot invalide.")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    requete = (
        "SELECT s.id_stock, m.nom_commercial, s.numero_lot, f.raison_sociale AS fournisseur, "
        "       s.date_reception, s.date_peremption, s.quantite_initiale, s.quantite_restante, s.statut "
        "  FROM stock s "
        "  JOIN medicament m ON m.id_medicament = s.id_medicament "
        "  JOIN commande c   ON c.id_commande = s.id_commande "
        "  JOIN fournisseur f ON f.id_fournisseur = c.id_fournisseur "
        " WHERE (m.nom_commercial LIKE %s OR s.numero_lot LIKE %s)"
    )
    params = [motif, motif]
    if statut is not None:
        requete += " AND s.statut = %s"
        params.append(statut)
    requete += " ORDER BY s.date_peremption, s.id_stock LIMIT %s"
    params.append(int(limite))
    with lecture() as cur:
        cur.execute(requete, tuple(params))
        return cur.fetchall()


def _valider(m: MedicamentSaisie) -> None:
    for libelle, valeur in (("nom commercial", m.nom_commercial), ("DCI", m.dci),
                            ("forme", m.forme), ("dosage", m.dosage)):
        if not (valeur or "").strip():
            raise BusinessError(f"Le champ « {libelle} » est obligatoire.")
    if m.prix_vente is None or m.prix_vente <= 0:
        raise BusinessError("Le prix de vente doit être strictement positif (RG-03).")
    if m.seuil_min < 0:
        raise BusinessError("Le seuil d'alerte doit être supérieur ou égal à 0 (RG-06).")


def _parametres(m: MedicamentSaisie) -> tuple:
    return (m.nom_commercial.strip(), m.dci.strip(), m.forme.strip(), m.dosage.strip(),
            (m.categorie or "").strip() or None, m.prix_vente,
            1 if m.ordonnance_obligatoire else 0, m.seuil_min)


def creer_medicament(user, saisie: MedicamentSaisie) -> int:
    """Ajoute un médicament au catalogue ; la base refuse un doublon (RG-04)."""
    require(user, "gerer_catalogue")
    _valider(saisie)
    with transaction() as cur:
        cur.execute(
            "INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, "
            "ordonnance_obligatoire, seuil_min) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            _parametres(saisie),
        )
        return cur.lastrowid


def modifier_medicament(user, id_medicament: int, saisie: MedicamentSaisie) -> None:
    """Modifie un médicament. Les ventes passées gardent leur prix (RG-36)."""
    require(user, "gerer_catalogue")
    _valider(saisie)
    with transaction() as cur:
        cur.execute(
            "UPDATE medicament SET nom_commercial = %s, dci = %s, forme = %s, dosage = %s, "
            "categorie = %s, prix_vente = %s, ordonnance_obligatoire = %s, seuil_min = %s "
            "WHERE id_medicament = %s",
            _parametres(saisie) + (id_medicament,),
        )


def changer_statut_medicament(user, id_medicament: int, actif: bool) -> None:
    """Désactive ou réactive un médicament (jamais de suppression, RG-05)."""
    require(user, "gerer_catalogue")
    with transaction() as cur:
        cur.execute("UPDATE medicament SET actif = %s WHERE id_medicament = %s",
                    (1 if actif else 0, id_medicament))
