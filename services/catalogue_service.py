"""Consultation du catalogue des médicaments avec le stock vendable."""
from core.permissions import require
from db.connection import lecture


def _echapper_like(terme: str) -> str:
    """Neutralise les caractères spéciaux de LIKE (%, _ et \\) saisis par l'utilisateur."""
    return terme.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def rechercher_medicaments(user, terme: str = "", limite: int = 100) -> list:
    """Médicaments actifs dont le nom ou la DCI contient `terme`.

    `stock_disponible` = somme des lots non périmés et au statut 'disponible' (RG-15).
    """
    require(user, "consulter_catalogue")
    motif = f"%{_echapper_like((terme or '').strip())}%"
    with lecture() as cur:
        cur.execute(
            """
            SELECT m.id_medicament, m.nom_commercial, m.dci, m.forme, m.dosage,
                   m.prix_vente, m.ordonnance_obligatoire,
                   COALESCE(SUM(CASE WHEN s.statut = 'disponible'
                                      AND s.date_peremption >= CURDATE()
                                     THEN s.quantite_restante END), 0) AS stock_disponible
              FROM medicament m
              LEFT JOIN stock s ON s.id_medicament = m.id_medicament
             WHERE m.actif = 1
               AND (m.nom_commercial LIKE %s OR m.dci LIKE %s)
             GROUP BY m.id_medicament, m.nom_commercial, m.dci, m.forme, m.dosage,
                      m.prix_vente, m.ordonnance_obligatoire
             ORDER BY m.nom_commercial
             LIMIT %s
            """,
            (motif, motif, int(limite)),
        )
        return cur.fetchall()
