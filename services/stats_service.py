"""Indicateurs du tableau de bord (requêtes du script SQL 05)."""
from core.permissions import require
from db.connection import lecture


def kpis_jour(user) -> dict:
    """Chiffres clés du jour (requête Q0)."""
    require(user, "stats_jour")
    with lecture() as cur:
        cur.execute(
            """
            SELECT
              (SELECT COALESCE(SUM(total), 0) FROM vente
                WHERE statut = 'validee' AND DATE(date_vente) = CURDATE())  AS ca_du_jour,
              (SELECT COUNT(*) FROM vente
                WHERE statut = 'validee' AND DATE(date_vente) = CURDATE())  AS ventes_du_jour,
              (SELECT COUNT(*) FROM v_alertes_rupture)                      AS medicaments_en_alerte,
              (SELECT COUNT(*) FROM v_alertes_peremption)                   AS lots_a_surveiller,
              (SELECT COUNT(*) FROM ordonnance
                WHERE statut IN ('en_attente', 'partielle'))                AS ordonnances_ouvertes
            """
        )
        return cur.fetchone()


def ca_par_jour(user, limite: int = 14) -> list:
    """Chiffre d'affaires des derniers jours d'activité (requête Q1)."""
    require(user, "stats_completes")
    with lecture() as cur:
        cur.execute(
            """
            SELECT DATE(date_vente) AS jour, COUNT(*) AS nb_ventes,
                   SUM(total) AS chiffre_affaires, ROUND(AVG(total), 2) AS panier_moyen
              FROM vente
             WHERE statut = 'validee'
             GROUP BY DATE(date_vente)
             ORDER BY jour DESC
             LIMIT %s
            """,
            (int(limite),),
        )
        return cur.fetchall()


def top_medicaments(user, limite: int = 10) -> list:
    """Médicaments les plus vendus (requête Q4)."""
    require(user, "stats_completes")
    with lecture() as cur:
        cur.execute(
            """
            SELECT m.nom_commercial, m.categorie,
                   SUM(lv.quantite) AS quantite_vendue,
                   SUM(lv.quantite * lv.prix_unitaire) AS chiffre_affaires
              FROM ligne_vente lv
              JOIN vente v      ON v.id_vente = lv.id_vente AND v.statut = 'validee'
              JOIN stock s      ON s.id_stock = lv.id_stock
              JOIN medicament m ON m.id_medicament = s.id_medicament
             GROUP BY m.id_medicament, m.nom_commercial, m.categorie
             ORDER BY quantite_vendue DESC, chiffre_affaires DESC
             LIMIT %s
            """,
            (int(limite),),
        )
        return cur.fetchall()


def alertes_rupture(user) -> list:
    """Médicaments sous leur seuil d'alerte (requête Q6)."""
    require(user, "stats_completes")
    with lecture() as cur:
        cur.execute(
            """
            SELECT nom_commercial, seuil_min, stock_disponible,
                   seuil_min - stock_disponible AS quantite_manquante
              FROM v_alertes_rupture
             ORDER BY quantite_manquante DESC
            """
        )
        return cur.fetchall()


def alertes_peremption(user) -> list:
    """Lots périmés ou proches de la péremption (requête Q7)."""
    require(user, "stats_completes")
    with lecture() as cur:
        cur.execute(
            """
            SELECT a.nom_commercial, a.numero_lot, a.date_peremption, a.jours_restants,
                   a.quantite_restante,
                   ROUND(a.quantite_restante * s.prix_achat, 2) AS valeur_stock_concerne
              FROM v_alertes_peremption a
              JOIN stock s ON s.id_stock = a.id_stock
             ORDER BY a.date_peremption
            """
        )
        return cur.fetchall()


def _lire(user, sql: str, params: tuple = ()) -> list:
    """Exécute une requête d'analyse (droit stats_completes). Sans paramètre, le SQL est envoyé
    tel quel : les signes % de DATE_FORMAT n'ont donc pas besoin d'être doublés."""
    require(user, "stats_completes")
    with lecture() as cur:
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchall()


def ca_par_mois(user) -> list:
    """Chiffre d'affaires par mois et évolution (requête Q2)."""
    return _lire(user, """
        SELECT mois, chiffre_affaires,
               LAG(chiffre_affaires) OVER (ORDER BY mois) AS ca_mois_precedent,
               ROUND(100 * (chiffre_affaires - LAG(chiffre_affaires) OVER (ORDER BY mois))
                         / NULLIF(LAG(chiffre_affaires) OVER (ORDER BY mois), 0), 1) AS evolution_pct
          FROM (SELECT DATE_FORMAT(date_vente, '%Y-%m') AS mois, SUM(total) AS chiffre_affaires
                  FROM vente WHERE statut = 'validee'
                 GROUP BY DATE_FORMAT(date_vente, '%Y-%m')) t
         ORDER BY mois""")


def ca_par_semaine(user) -> list:
    """Chiffre d'affaires par semaine (requête Q3)."""
    return _lire(user, """
        SELECT YEARWEEK(date_vente, 1) AS annee_semaine, MIN(DATE(date_vente)) AS premier_jour_observe,
               COUNT(*) AS nb_ventes, SUM(total) AS chiffre_affaires
          FROM vente WHERE statut = 'validee'
         GROUP BY YEARWEEK(date_vente, 1)
         ORDER BY annee_semaine DESC LIMIT 26""")


def medicaments_jamais_vendus(user) -> list:
    """Médicaments actifs jamais vendus (requête Q5)."""
    return _lire(user, """
        SELECT m.nom_commercial, m.categorie
          FROM medicament m
         WHERE m.actif = 1 AND NOT EXISTS (
               SELECT 1 FROM stock s
                 JOIN ligne_vente lv ON lv.id_stock = s.id_stock
                 JOIN vente v ON v.id_vente = lv.id_vente AND v.statut = 'validee'
                WHERE s.id_medicament = m.id_medicament)
         ORDER BY m.nom_commercial""")


def ventes_par_personnel(user) -> list:
    """Ventes par membre du personnel et part du chiffre d'affaires (requête Q8)."""
    return _lire(user, """
        SELECT p.nom, p.prenom, p.role, COUNT(v.id_vente) AS nb_ventes,
               COALESCE(SUM(v.total), 0) AS montant,
               ROUND(100 * COALESCE(SUM(v.total), 0) / NULLIF(SUM(SUM(v.total)) OVER (), 0), 1) AS part_ca_pct
          FROM personnel p
          LEFT JOIN vente v ON v.id_personnel = p.id_personnel AND v.statut = 'validee'
         GROUP BY p.id_personnel, p.nom, p.prenom, p.role
         ORDER BY montant DESC""")


def clients_fideles(user, limite: int = 15) -> list:
    """Clients les plus fidèles (requête Q9)."""
    return _lire(user, """
        SELECT c.nom, c.prenom, COUNT(v.id_vente) AS nb_achats, SUM(v.total) AS montant_total,
               ROUND(AVG(v.total), 2) AS panier_moyen, MAX(v.date_vente) AS dernier_achat
          FROM client c JOIN vente v ON v.id_client = c.id_client AND v.statut = 'validee'
         GROUP BY c.id_client, c.nom, c.prenom
         ORDER BY montant_total DESC LIMIT %s""", (int(limite),))


def performance_fournisseurs(user) -> list:
    """Performance des fournisseurs (requête Q10)."""
    return _lire(user, """
        SELECT f.raison_sociale, COUNT(DISTINCT c.id_commande) AS nb_commandes,
               COUNT(DISTINCT CASE WHEN c.statut = 'recue' THEN c.id_commande END) AS nb_commandes_recues,
               COUNT(s.id_stock) AS nb_lots_recus,
               COALESCE(SUM(s.quantite_initiale), 0) AS unites_recues,
               COALESCE(SUM(s.quantite_initiale * s.prix_achat), 0) AS montant_achats,
               ROUND(AVG(CASE WHEN s.date_reception >= DATE(c.date_commande)
                              THEN DATEDIFF(s.date_reception, DATE(c.date_commande)) END), 1) AS delai_reel_moyen_jours,
               f.delai_livraison_jours AS delai_annonce_jours
          FROM fournisseur f
          LEFT JOIN commande c ON c.id_fournisseur = f.id_fournisseur
          LEFT JOIN stock s ON s.id_commande = c.id_commande
         GROUP BY f.id_fournisseur, f.raison_sociale, f.delai_livraison_jours
         ORDER BY montant_achats DESC""")


def ventes_ordonnance_libre(user) -> list:
    """Ventes sur ordonnance et ventes libres (requête Q11)."""
    return _lire(user, """
        SELECT CASE WHEN id_ordonnance IS NULL THEN 'Vente libre' ELSE 'Vente sur ordonnance' END AS type_vente,
               COUNT(*) AS nb_ventes, SUM(total) AS chiffre_affaires,
               ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_ventes_pct
          FROM vente WHERE statut = 'validee'
         GROUP BY CASE WHEN id_ordonnance IS NULL THEN 'Vente libre' ELSE 'Vente sur ordonnance' END""")


def marge_par_medicament(user, limite: int = 15) -> list:
    """Marge brute par médicament (requête Q12)."""
    return _lire(user, """
        SELECT m.nom_commercial, SUM(lv.quantite) AS quantite_vendue,
               SUM(lv.quantite * lv.prix_unitaire) AS chiffre_affaires,
               SUM(lv.quantite * s.prix_achat) AS cout_achat,
               SUM(lv.quantite * (lv.prix_unitaire - s.prix_achat)) AS marge_brute,
               ROUND(100 * SUM(lv.quantite * (lv.prix_unitaire - s.prix_achat))
                         / SUM(lv.quantite * lv.prix_unitaire), 1) AS taux_marge_pct
          FROM ligne_vente lv
          JOIN vente v ON v.id_vente = lv.id_vente AND v.statut = 'validee'
          JOIN stock s ON s.id_stock = lv.id_stock
          JOIN medicament m ON m.id_medicament = s.id_medicament
         GROUP BY m.id_medicament, m.nom_commercial
         ORDER BY marge_brute DESC LIMIT %s""", (int(limite),))


def couverture_stock(user) -> list:
    """Jours de couverture du stock d'après les ventes des 30 derniers jours (requête Q14)."""
    return _lire(user, """
        SELECT sd.nom_commercial, sd.stock_disponible, COALESCE(v30.qte, 0) AS vendu_30_jours,
               ROUND(sd.stock_disponible / NULLIF(v30.qte / 30, 0), 1) AS jours_de_couverture
          FROM v_stock_disponible sd
          LEFT JOIN (SELECT s.id_medicament, SUM(lv.quantite) AS qte
                       FROM ligne_vente lv
                       JOIN vente v ON v.id_vente = lv.id_vente AND v.statut = 'validee'
                                   AND v.date_vente >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                       JOIN stock s ON s.id_stock = lv.id_stock
                      GROUP BY s.id_medicament) v30 ON v30.id_medicament = sd.id_medicament
         ORDER BY jours_de_couverture IS NULL, jours_de_couverture LIMIT 60""")


def classement_categories(user) -> list:
    """Classement des médicaments dans chaque catégorie (requête Q15)."""
    return _lire(user, """
        SELECT categorie, nom_commercial, quantite_vendue,
               RANK() OVER (PARTITION BY categorie ORDER BY quantite_vendue DESC) AS rang_categorie
          FROM (SELECT m.categorie, m.nom_commercial, SUM(lv.quantite) AS quantite_vendue
                  FROM ligne_vente lv
                  JOIN vente v ON v.id_vente = lv.id_vente AND v.statut = 'validee'
                  JOIN stock s ON s.id_stock = lv.id_stock
                  JOIN medicament m ON m.id_medicament = s.id_medicament
                 GROUP BY m.id_medicament, m.categorie, m.nom_commercial) t
         ORDER BY categorie, rang_categorie""")


def affluence_par_heure(user) -> list:
    """Affluence par heure de la journée (requête Q16)."""
    return _lire(user, """
        SELECT HOUR(date_vente) AS heure, COUNT(*) AS nb_ventes, SUM(total) AS chiffre_affaires
          FROM vente WHERE statut = 'validee'
         GROUP BY HOUR(date_vente) ORDER BY heure""")
