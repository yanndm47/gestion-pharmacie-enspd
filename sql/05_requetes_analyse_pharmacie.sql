-- =====================================================================
--  Script 5 : REQUÊTES D'ANALYSE (fonctionnalités F-32 à F-39)
--  À exécuter APRÈS les scripts 01, 02 et 03.
--
--  Mode d'emploi : placez le curseur dans une requête et appuyez sur Ctrl+Entrée
--  pour l'exécuter seule, ou lancez tout le fichier avec Alt+X (un onglet de
--  résultat s'ouvre par requête).
--
--  Les "résultats attendus" ci-dessous sont ceux du jeu de test du script 03,
--  lorsque la base vient d'être créée (aucun test du script 04 laissé en base).
--  Prérequis : MySQL 8.0+ ou MariaDB 10.2+ (fonctions de fenêtrage : LAG, RANK,
--  SUM() OVER).
--
--  Règle commune : on ne compte que les ventes au statut 'validee'.
--  Les ventes annulées sont exclues de tous les indicateurs.
-- =====================================================================

USE pharmacie;

-- =====================================================================
-- Q0. Tableau de bord : les 5 chiffres clés du jour
--     Fonctionnalités : synthèse F-32, F-34, F-35
--     Technique : sous-requêtes scalaires, utilisation des vues
--     Résultat attendu : 119000 | 3 | 1 | 2 | 1
-- =====================================================================
SELECT
  (SELECT COALESCE(SUM(total), 0) FROM vente
    WHERE statut = 'validee' AND DATE(date_vente) = CURDATE())   AS ca_du_jour,
  (SELECT COUNT(*) FROM vente
    WHERE statut = 'validee' AND DATE(date_vente) = CURDATE())   AS ventes_du_jour,
  (SELECT COUNT(*) FROM v_alertes_rupture)                       AS medicaments_en_alerte,
  (SELECT COUNT(*) FROM v_alertes_peremption)                    AS lots_a_surveiller,
  (SELECT COUNT(*) FROM ordonnance
    WHERE statut IN ('en_attente', 'partielle'))                 AS ordonnances_ouvertes;

-- =====================================================================
-- Q1. Chiffre d'affaires par jour                              [F-32]
--     Objectif : suivre l'activité quotidienne et le panier moyen.
--     Technique : agrégats (COUNT, SUM, AVG), GROUP BY sur une date.
--     Résultat attendu : 1 ligne (aujourd'hui) : 3 ventes, 119000, panier moyen 39666.67
-- =====================================================================
SELECT DATE(date_vente)       AS jour,
       COUNT(*)               AS nb_ventes,
       SUM(total)             AS chiffre_affaires,
       ROUND(AVG(total), 2)   AS panier_moyen
  FROM vente
 WHERE statut = 'validee'
 GROUP BY DATE(date_vente)
 ORDER BY jour DESC;

-- =====================================================================
-- Q2. Chiffre d'affaires par mois et évolution                 [F-32]
--     Objectif : mesurer la croissance d'un mois à l'autre.
--     Technique : sous-requête dans FROM + fonction de fenêtrage LAG().
--     Résultat attendu : 1 ligne (mois courant), évolution vide (pas de mois précédent)
-- =====================================================================
SELECT mois,
       chiffre_affaires,
       LAG(chiffre_affaires) OVER (ORDER BY mois) AS ca_mois_precedent,
       ROUND(100 * (chiffre_affaires - LAG(chiffre_affaires) OVER (ORDER BY mois))
                 / NULLIF(LAG(chiffre_affaires) OVER (ORDER BY mois), 0), 1) AS evolution_pct
  FROM (
        SELECT DATE_FORMAT(date_vente, '%Y-%m') AS mois,
               SUM(total)                       AS chiffre_affaires
          FROM vente
         WHERE statut = 'validee'
         GROUP BY DATE_FORMAT(date_vente, '%Y-%m')
       ) t
 ORDER BY mois;

-- =====================================================================
-- Q3. Chiffre d'affaires par semaine                           [F-32]
--     Technique : YEARWEEK(date, 1) pour des semaines commençant le lundi.
--     Résultat attendu : 1 ligne (semaine courante), 3 ventes, 119000
-- =====================================================================
SELECT YEARWEEK(date_vente, 1) AS annee_semaine,
       MIN(DATE(date_vente))   AS premier_jour_observe,
       COUNT(*)                AS nb_ventes,
       SUM(total)              AS chiffre_affaires
  FROM vente
 WHERE statut = 'validee'
 GROUP BY YEARWEEK(date_vente, 1)
 ORDER BY annee_semaine DESC;

-- =====================================================================
-- Q4. Top 10 des médicaments les plus vendus                   [F-33]
--     Objectif : savoir quoi réapprovisionner en priorité.
--     Technique : 4 jointures (ligne_vente, vente, stock, medicament), agrégats, LIMIT.
--     Résultat attendu : en tête Amoxicilline Biogaran (21 unités, 73500)
-- =====================================================================
SELECT m.id_medicament,
       m.nom_commercial,
       m.categorie,
       SUM(lv.quantite)                    AS quantite_vendue,
       SUM(lv.quantite * lv.prix_unitaire) AS chiffre_affaires
  FROM ligne_vente lv
  JOIN vente v      ON v.id_vente = lv.id_vente AND v.statut = 'validee'
  JOIN stock s      ON s.id_stock = lv.id_stock
  JOIN medicament m ON m.id_medicament = s.id_medicament
 GROUP BY m.id_medicament, m.nom_commercial, m.categorie
 ORDER BY quantite_vendue DESC, chiffre_affaires DESC
 LIMIT 10;

-- =====================================================================
-- Q5. Médicaments actifs jamais vendus                         [F-33]
--     Objectif : repérer les produits dormants (stock immobilisé).
--     Technique : NOT EXISTS (sous-requête corrélée).
--     Résultat attendu : 4 lignes : Efferalgan, Augmentin, Ventoline, Loratadine Mylan
-- =====================================================================
SELECT m.id_medicament, m.nom_commercial, m.categorie
  FROM medicament m
 WHERE m.actif = 1
   AND NOT EXISTS (
         SELECT 1
           FROM stock s
           JOIN ligne_vente lv ON lv.id_stock = s.id_stock
           JOIN vente v        ON v.id_vente = lv.id_vente AND v.statut = 'validee'
          WHERE s.id_medicament = m.id_medicament
       )
 ORDER BY m.nom_commercial;

-- =====================================================================
-- Q6. Médicaments en rupture ou sous leur seuil d'alerte       [F-34]
--     Objectif : déclencher les commandes.
--     Technique : utilisation d'une vue (v_alertes_rupture), calcul de la quantité manquante.
--     Résultat attendu : 1 ligne : Loratadine Mylan, stock 0, seuil 8, manquant 8
-- =====================================================================
SELECT id_medicament, nom_commercial, seuil_min, stock_disponible,
       seuil_min - stock_disponible AS quantite_manquante
  FROM v_alertes_rupture
 ORDER BY quantite_manquante DESC;

-- =====================================================================
-- Q7. Lots périmés ou proches de la péremption et valeur concernée  [F-35]
--     Objectif : chiffrer la perte potentielle et agir avant la date limite.
--     Technique : jointure avec une vue, CASE pour classer l'urgence.
--     Résultat attendu : EFFE-2512 (Périmé, -5 jours, 26000) et SMEC-2601 (45 jours, 108300)
-- =====================================================================
SELECT a.nom_commercial,
       a.numero_lot,
       a.date_peremption,
       a.jours_restants,
       a.quantite_restante,
       ROUND(a.quantite_restante * s.prix_achat, 2) AS valeur_stock_concerne,
       CASE WHEN a.jours_restants < 0   THEN 'Périmé'
            WHEN a.jours_restants <= 30 THEN 'Urgent (30 jours)'
            ELSE 'À surveiller (90 jours)'
       END AS niveau
  FROM v_alertes_peremption a
  JOIN stock s ON s.id_stock = a.id_stock
 ORDER BY a.date_peremption;

-- =====================================================================
-- Q8. Ventes par membre du personnel et part du chiffre d'affaires  [F-36]
--     Objectif : mesurer la contribution de chacun.
--     Technique : LEFT JOIN (garde ceux qui n'ont rien vendu), SUM() OVER ().
--     Résultat attendu : Dupont 2 ventes 107000 (89.9 %), Ngono 1 vente 12000 (10.1 %), Admin 0 (0.0 %)
-- =====================================================================
SELECT p.nom, p.prenom, p.role,
       COUNT(v.id_vente)                AS nb_ventes,
       COALESCE(SUM(v.total), 0)        AS montant,
       ROUND(100 * COALESCE(SUM(v.total), 0)
                 / NULLIF(SUM(SUM(v.total)) OVER (), 0), 1) AS part_ca_pct
  FROM personnel p
  LEFT JOIN vente v ON v.id_personnel = p.id_personnel AND v.statut = 'validee'
 GROUP BY p.id_personnel, p.nom, p.prenom, p.role
 ORDER BY montant DESC;

-- =====================================================================
-- Q9. Clients les plus fidèles                                 [F-37]
--     Objectif : identifier les meilleurs clients (nombre et montant d'achats).
--     Technique : jointure, agrégats multiples, MAX sur une date.
--     Résultat attendu : Fotso Jean (1 achat, 100100) puis Tchoua Aminata (1 achat, 6900)
-- =====================================================================
SELECT c.id_client, c.nom, c.prenom,
       COUNT(v.id_vente)     AS nb_achats,
       SUM(v.total)          AS montant_total,
       ROUND(AVG(v.total),2) AS panier_moyen,
       MAX(v.date_vente)     AS dernier_achat
  FROM client c
  JOIN vente v ON v.id_client = c.id_client AND v.statut = 'validee'
 GROUP BY c.id_client, c.nom, c.prenom
 ORDER BY montant_total DESC
 LIMIT 10;

-- =====================================================================
-- Q10. Performance des fournisseurs                            [F-38]
--     Objectif : comparer les fournisseurs (volumes, montants, délai réel).
--     Technique : LEFT JOIN en cascade, COUNT(DISTINCT ...), AVG(CASE ...).
--     Le CASE écarte le lot du jeu de test "vieilli" artificiellement (réception
--     avant la commande) pour ne pas fausser le délai moyen.
--     Résultat attendu :
--       PharmaDistrib : 1 commande, 1 reçue, 6 lots, 290 unités, 417000, délai réel 0.0
--       MediSupply    : 1 commande, 0 reçue, 4 lots, 140 unités, 374000, délai réel 0.0
--       SantePlus Grossiste : 0 commande, 0 lot, 0 unité, montant 0
-- =====================================================================
SELECT f.id_fournisseur,
       f.raison_sociale,
       COUNT(DISTINCT c.id_commande)                                         AS nb_commandes,
       COUNT(DISTINCT CASE WHEN c.statut = 'recue' THEN c.id_commande END)   AS nb_commandes_recues,
       COUNT(s.id_stock)                                                     AS nb_lots_recus,
       COALESCE(SUM(s.quantite_initiale), 0)                                 AS unites_recues,
       COALESCE(SUM(s.quantite_initiale * s.prix_achat), 0)                  AS montant_achats,
       ROUND(AVG(CASE WHEN s.date_reception >= DATE(c.date_commande)
                      THEN DATEDIFF(s.date_reception, DATE(c.date_commande)) END), 1) AS delai_reel_moyen_jours,
       f.delai_livraison_jours                                               AS delai_annonce_jours
  FROM fournisseur f
  LEFT JOIN commande c ON c.id_fournisseur = f.id_fournisseur
  LEFT JOIN stock s    ON s.id_commande = c.id_commande
 GROUP BY f.id_fournisseur, f.raison_sociale, f.delai_livraison_jours
 ORDER BY montant_achats DESC;

-- =====================================================================
-- Q11. Ventes sur ordonnance et ventes libres                  [F-39]
--     Objectif : connaître la part de l'activité réglementée.
--     Technique : CASE dans le GROUP BY, SUM(COUNT(*)) OVER () pour le pourcentage.
--     Résultat attendu : Vente libre 2 ventes, 18900 (66.7 %) ; sur ordonnance 1 vente, 100100 (33.3 %)
-- =====================================================================
SELECT CASE WHEN id_ordonnance IS NULL THEN 'Vente libre'
            ELSE 'Vente sur ordonnance' END       AS type_vente,
       COUNT(*)                                   AS nb_ventes,
       SUM(total)                                 AS chiffre_affaires,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_ventes_pct
  FROM vente
 WHERE statut = 'validee'
 GROUP BY CASE WHEN id_ordonnance IS NULL THEN 'Vente libre'
               ELSE 'Vente sur ordonnance' END;

-- =====================================================================
-- Q12. Marge brute par médicament (bonus)
--     Objectif : savoir ce qui rapporte vraiment (prix de vente moins prix d'achat du lot vendu).
--     Technique : jointure ligne_vente -> stock pour retrouver le coût d'achat réel.
--     Résultat attendu : en tête Amoxicilline Biogaran, marge 27300 (taux 37.1 %)
-- =====================================================================
SELECT m.nom_commercial,
       SUM(lv.quantite)                                   AS quantite_vendue,
       SUM(lv.quantite * lv.prix_unitaire)                AS chiffre_affaires,
       SUM(lv.quantite * s.prix_achat)                    AS cout_achat,
       SUM(lv.quantite * (lv.prix_unitaire - s.prix_achat)) AS marge_brute,
       ROUND(100 * SUM(lv.quantite * (lv.prix_unitaire - s.prix_achat))
                 / SUM(lv.quantite * lv.prix_unitaire), 1) AS taux_marge_pct
  FROM ligne_vente lv
  JOIN vente v      ON v.id_vente = lv.id_vente AND v.statut = 'validee'
  JOIN stock s      ON s.id_stock = lv.id_stock
  JOIN medicament m ON m.id_medicament = s.id_medicament
 GROUP BY m.id_medicament, m.nom_commercial
 ORDER BY marge_brute DESC;

-- =====================================================================
-- Q13. Ordonnances à finaliser (bonus)
--     Objectif : relancer les patients dont l'ordonnance n'est pas soldée.
--     Technique : jointure avec la vue v_ordonnance_delivrance, DATEDIFF.
--     Résultat attendu : 1 ligne : Jean Fotso, Dr Mballa, Oméprazole Arrow, prescrit 14,
--                        délivré 7, reste 7, 12 jours avant expiration
-- =====================================================================
SELECT o.id_ordonnance,
       CONCAT(c.prenom, ' ', c.nom)              AS client,
       o.nom_medecin,
       o.date_validite,
       DATEDIFF(o.date_validite, CURDATE())      AS jours_avant_expiration,
       d.nom_commercial,
       d.quantite_prescrite,
       d.quantite_delivree,
       d.quantite_prescrite - d.quantite_delivree AS reste_a_delivrer
  FROM ordonnance o
  JOIN client c                   ON c.id_client = o.id_client
  JOIN v_ordonnance_delivrance d  ON d.id_ordonnance = o.id_ordonnance
 WHERE o.statut IN ('en_attente', 'partielle')
   AND d.quantite_delivree < d.quantite_prescrite
 ORDER BY o.date_validite, o.id_ordonnance;

-- =====================================================================
-- Q14. Jours de couverture du stock (bonus)                    [F-34]
--     Objectif : anticiper les ruptures d'après le rythme de vente des 30 derniers jours.
--     Technique : jointure avec une sous-requête agrégée, NULLIF pour éviter la division par 0.
--     Résultat attendu : Loratadine : stock 0, aucune vente (couverture vide) ;
--                        les médicaments jamais vendus apparaissent en fin de liste
-- =====================================================================
SELECT sd.nom_commercial,
       sd.stock_disponible,
       COALESCE(v30.qte, 0)                                       AS vendu_30_jours,
       ROUND(sd.stock_disponible / NULLIF(v30.qte / 30, 0), 1)    AS jours_de_couverture
  FROM v_stock_disponible sd
  LEFT JOIN (
        SELECT s.id_medicament, SUM(lv.quantite) AS qte
          FROM ligne_vente lv
          JOIN vente v ON v.id_vente = lv.id_vente
                      AND v.statut = 'validee'
                      AND v.date_vente >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
          JOIN stock s ON s.id_stock = lv.id_stock
         GROUP BY s.id_medicament
       ) v30 ON v30.id_medicament = sd.id_medicament
 ORDER BY jours_de_couverture IS NULL, jours_de_couverture;

-- =====================================================================
-- Q15. Classement des médicaments au sein de chaque catégorie (bonus)
--     Objectif : comparer les produits d'une même famille thérapeutique.
--     Technique : RANK() OVER (PARTITION BY ...).
--     Résultat attendu : un rang 1 par catégorie vendue (ex. Antibiotique : Amoxicilline Biogaran)
-- =====================================================================
SELECT categorie, nom_commercial, quantite_vendue,
       RANK() OVER (PARTITION BY categorie ORDER BY quantite_vendue DESC) AS rang_categorie
  FROM (
        SELECT m.categorie, m.nom_commercial, SUM(lv.quantite) AS quantite_vendue
          FROM ligne_vente lv
          JOIN vente v      ON v.id_vente = lv.id_vente AND v.statut = 'validee'
          JOIN stock s      ON s.id_stock = lv.id_stock
          JOIN medicament m ON m.id_medicament = s.id_medicament
         GROUP BY m.id_medicament, m.categorie, m.nom_commercial
       ) t
 ORDER BY categorie, rang_categorie;

-- =====================================================================
-- Q16. Affluence par heure de la journée (bonus)
--     Objectif : adapter les horaires et les effectifs.
--     Technique : fonction HOUR() et GROUP BY.
--     Résultat attendu : 1 ligne (l'heure d'exécution du script 03), 3 ventes, 119000
-- =====================================================================
SELECT HOUR(date_vente) AS heure,
       COUNT(*)         AS nb_ventes,
       SUM(total)       AS chiffre_affaires
  FROM vente
 WHERE statut = 'validee'
 GROUP BY HOUR(date_vente)
 ORDER BY heure;

-- Fin du script 5.
