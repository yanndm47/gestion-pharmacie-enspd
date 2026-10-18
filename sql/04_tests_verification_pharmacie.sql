-- =====================================================================
--  Script 4/4 : tests des règles de gestion
--  À exécuter APRÈS les scripts 01, 02 et 03.
--
--  MODE D'EMPLOI (important) :
--  Ne lancez PAS ce fichier en entier (Alt+X). Exécutez les tests UN PAR UN :
--  sélectionnez le bloc d'un test (de START TRANSACTION à ROLLBACK) et
--  appuyez sur Alt+X, ou lancez les lignes une à une avec Ctrl+Entrée.
--  Chaque test est entouré de START TRANSACTION ... ROLLBACK : il ne laisse
--  aucune trace dans la base. Si un test échoue en plein milieu (c'est son but),
--  exécutez ROLLBACK; à la main avant de passer au suivant.
-- =====================================================================

USE pharmacie;

-- ---------------------------------------------------------------------
-- 0. ÉTAT DE DÉPART : valeurs attendues après le script 3
--    vente 1 = 12000 | vente 2 = 100100 | vente 3 = 6900
--    commande 1 = recue | commande 2 = partielle | ordonnance 1 = partielle
-- ---------------------------------------------------------------------
SELECT id_vente, total, statut FROM vente;
SELECT id_commande, statut FROM commande;
SELECT id_ordonnance, statut FROM ordonnance;
SELECT id_stock, numero_lot, quantite_restante, statut FROM stock;

-- ---------------------------------------------------------------------
-- T1. Stock insuffisant (RG-35)
--     Attendu : ERREUR "Stock insuffisant dans ce lot (RG-35)"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, mode_paiement) VALUES (2, 'especes');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 1, 999, 1500);
ROLLBACK;

-- ---------------------------------------------------------------------
-- T2. Lot périmé (RG-13)  -  le lot 3 (EFFE-2512) est périmé
--     Attendu : ERREUR "Lot périmé ou indisponible : vente refusée (RG-13)"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, mode_paiement) VALUES (2, 'especes');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 3, 1, 2000);
ROLLBACK;

-- ---------------------------------------------------------------------
-- T3. Médicament sur ordonnance vendu sans ordonnance (RG-38)
--     Attendu : ERREUR "Ordonnance obligatoire pour ce médicament (RG-38)"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, id_client, mode_paiement) VALUES (1, 3, 'especes');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 7, 1, 6500);   -- Augmentin
ROLLBACK;

-- ---------------------------------------------------------------------
-- T4. La caissière ne peut pas vendre sur ordonnance (RG-38)
--     Attendu : ERREUR "Une vente sur ordonnance doit être faite par un pharmacien"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, id_client, id_ordonnance, mode_paiement)
VALUES (2, 1, 1, 'carte');
ROLLBACK;

-- ---------------------------------------------------------------------
-- T5. Quantité supérieure à la quantité prescrite (RG-38)
--     L'ordonnance 1 prescrit 21 Amoxicilline, déjà 21 délivrées.
--     Attendu : ERREUR "Quantité supérieure à celle prescrite..."
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, id_client, id_ordonnance, mode_paiement)
VALUES (1, 1, 1, 'carte');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 4, 1, 3500);
ROLLBACK;

-- ---------------------------------------------------------------------
-- T6. Prix différent du catalogue (RG-36)
--     Attendu : ERREUR "Le prix unitaire doit être le prix de vente du catalogue"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, mode_paiement) VALUES (2, 'especes');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 1, 1, 1000);
ROLLBACK;

-- ---------------------------------------------------------------------
-- T7. Vente réussie, avec décrémentation du stock et calcul du total
--     Attendu : lot 1 passe de 98 à 96, total de la nouvelle vente = 3000
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, mode_paiement) VALUES (2, 'carte');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire)
VALUES (LAST_INSERT_ID(), 1, 2, 1500);
SELECT id_stock, quantite_restante FROM stock WHERE id_stock = 1;
SELECT id_vente, total FROM vente ORDER BY id_vente DESC LIMIT 1;
ROLLBACK;

-- ---------------------------------------------------------------------
-- T8. Annulation de la vente 2 (délivrance de l'ordonnance) (RG-41)
--     Attendu : lot 4 repasse de 19 à 40, lot 9 de 33 à 40,
--               ordonnance 1 repasse à "en_attente"
-- ---------------------------------------------------------------------
START TRANSACTION;
UPDATE vente SET statut = 'annulee' WHERE id_vente = 2;
SELECT id_stock, numero_lot, quantite_restante FROM stock WHERE id_stock IN (4, 9);
SELECT id_ordonnance, statut FROM ordonnance WHERE id_ordonnance = 1;
ROLLBACK;

-- ---------------------------------------------------------------------
-- T9. Suppression interdite d'une vente (RG-51)
--     Attendu : ERREUR "Suppression interdite : annulez la vente à la place"
-- ---------------------------------------------------------------------
START TRANSACTION;
DELETE FROM vente WHERE id_vente = 1;
ROLLBACK;

-- ---------------------------------------------------------------------
-- T10. Réception d'un lot qui ne figure pas dans la commande (RG-56)
--      La commande 2 ne contient pas le Doliprane (médicament 1).
--      Attendu : ERREUR "Ce médicament ne figure pas dans la commande"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption,
                   quantite_initiale, quantite_restante, prix_achat)
VALUES (1, 2, 'DOLI-TEST', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 12 MONTH), 10, 10, 900);
ROLLBACK;

-- ---------------------------------------------------------------------
-- T11. Réception du dernier médicament de la commande 2 (RG-58)
--      Attendu : la commande 2 passe de "partielle" à "recue"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption,
                   quantite_initiale, quantite_restante, prix_achat)
VALUES (10, 2, 'LORA-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 24 MONTH), 40, 40, 1900);
SELECT id_commande, statut FROM commande WHERE id_commande = 2;
ROLLBACK;

-- ---------------------------------------------------------------------
-- T12. Un administrateur ne peut pas vendre (RG-32)
--      Attendu : ERREUR "Ce compte ne peut pas enregistrer de vente"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO vente (id_personnel, mode_paiement) VALUES (3, 'especes');
ROLLBACK;

-- ---------------------------------------------------------------------
-- T13. Doublon client (RG-20)
--      Attendu : ERREUR "Duplicate entry ... for key 'uq_client_identite'"
-- ---------------------------------------------------------------------
START TRANSACTION;
INSERT INTO client (nom, prenom, date_naissance) VALUES ('Fotso', 'Jean', '1985-04-12');
ROLLBACK;

-- =====================================================================
-- VUES D'ANALYSE : valeurs attendues
-- =====================================================================

-- Stock disponible par médicament (ex. Doliprane = 98, Loratadine = 0)
SELECT * FROM v_stock_disponible ORDER BY nom_commercial;

-- Alertes de rupture : attendu = Loratadine Mylan uniquement (stock 0 < seuil 8)
SELECT * FROM v_alertes_rupture;

-- Alertes de péremption : attendu = EFFE-2512 (périmé, -5 jours) et SMEC-2601 (45 jours)
SELECT * FROM v_alertes_peremption ORDER BY date_peremption;

-- Délivrance de l'ordonnance 1 : Amoxicilline 21/21, Oméprazole 7/14
SELECT * FROM v_ordonnance_delivrance WHERE id_ordonnance = 1;

-- Maintenance quotidienne : passe les lots périmés en statut 'perime'
CALL sp_maintenance_quotidienne();

-- ---------------------------------------------------------------------
-- 3 premières requêtes d'analyse (à enrichir pour la phase suivante)
-- ---------------------------------------------------------------------

-- Chiffre d'affaires par jour (ventes validées)
SELECT DATE(date_vente) AS jour, COUNT(*) AS nb_ventes, SUM(total) AS chiffre_affaires
  FROM vente WHERE statut = 'validee'
 GROUP BY DATE(date_vente) ORDER BY jour DESC;

-- Top des médicaments les plus vendus
SELECT m.nom_commercial, SUM(lv.quantite) AS quantite_vendue,
       SUM(lv.quantite * lv.prix_unitaire) AS montant
  FROM ligne_vente lv
  JOIN vente v       ON v.id_vente = lv.id_vente AND v.statut = 'validee'
  JOIN stock s       ON s.id_stock = lv.id_stock
  JOIN medicament m  ON m.id_medicament = s.id_medicament
 GROUP BY m.id_medicament, m.nom_commercial
 ORDER BY quantite_vendue DESC;

-- Ventes par membre du personnel
SELECT p.nom, p.prenom, p.role, COUNT(v.id_vente) AS nb_ventes, COALESCE(SUM(v.total),0) AS montant
  FROM personnel p
  LEFT JOIN vente v ON v.id_personnel = p.id_personnel AND v.statut = 'validee'
 GROUP BY p.id_personnel, p.nom, p.prenom, p.role;
