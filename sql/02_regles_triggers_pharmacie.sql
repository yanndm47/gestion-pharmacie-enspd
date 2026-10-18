-- =====================================================================
--  Script 2/4 : règles de gestion automatiques (procédures, triggers, vues)
--  À exécuter APRÈS 01_schema_pharmacie.sql
--
--  Dans DBeaver : Alt+X (exécuter le script).
--  Ce fichier ne contient volontairement AUCUNE ligne vide à l'intérieur des routines :
--  DBeaver coupe une instruction à chaque ligne vide dans son réglage par défaut.
--  Si un bloc CREATE TRIGGER / CREATE PROCEDURE donne une erreur de syntaxe :
--  sélectionnez ce bloc entier (de CREATE jusqu'au END;) puis Ctrl+Entrée.
--  Les erreurs métier sont levées avec SIGNAL SQLSTATE '45000'.
-- =====================================================================

USE pharmacie;

-- =====================================================================
-- A. PROCÉDURES UTILITAIRES
-- =====================================================================

-- Recalcule le statut d'une ordonnance d'après les ventes validées (RG-29)
CREATE PROCEDURE sp_maj_statut_ordonnance(IN p_id_ordonnance INT)
BEGIN
  DECLARE v_nb_lignes   INT DEFAULT 0;
  DECLARE v_nb_soldees  INT DEFAULT 0;
  DECLARE v_total_deliv INT DEFAULT 0;
  SELECT COUNT(*),
         COALESCE(SUM(CASE WHEN COALESCE(d.qte,0) >= lo.quantite_prescrite THEN 1 ELSE 0 END),0),
         COALESCE(SUM(d.qte),0)
    INTO v_nb_lignes, v_nb_soldees, v_total_deliv
    FROM ligne_ordonnance lo
    LEFT JOIN (
        SELECT s.id_medicament, SUM(lv.quantite) AS qte
          FROM vente v
          JOIN ligne_vente lv ON lv.id_vente = v.id_vente
          JOIN stock s        ON s.id_stock  = lv.id_stock
         WHERE v.id_ordonnance = p_id_ordonnance
           AND v.statut = 'validee'
         GROUP BY s.id_medicament
    ) d ON d.id_medicament = lo.id_medicament
   WHERE lo.id_ordonnance = p_id_ordonnance;
  UPDATE ordonnance
     SET statut = CASE
                    WHEN v_nb_lignes > 0 AND v_nb_soldees = v_nb_lignes THEN 'soldee'
                    WHEN v_total_deliv > 0 THEN 'partielle'
                    ELSE 'en_attente'
                  END
   WHERE id_ordonnance = p_id_ordonnance
     AND statut <> 'expiree';
END;

-- Recalcule le statut d'une commande d'après les lots reçus (RG-58)
CREATE PROCEDURE sp_maj_statut_commande(IN p_id_commande INT)
BEGIN
  DECLARE v_nb_lignes  INT DEFAULT 0;
  DECLARE v_nb_soldees INT DEFAULT 0;
  DECLARE v_total_recu INT DEFAULT 0;
  SELECT COUNT(*),
         COALESCE(SUM(CASE WHEN COALESCE(r.qte,0) >= lc.quantite_commandee THEN 1 ELSE 0 END),0),
         COALESCE(SUM(r.qte),0)
    INTO v_nb_lignes, v_nb_soldees, v_total_recu
    FROM ligne_commande lc
    LEFT JOIN (
        SELECT id_medicament, SUM(quantite_initiale) AS qte
          FROM stock
         WHERE id_commande = p_id_commande
         GROUP BY id_medicament
    ) r ON r.id_medicament = lc.id_medicament
   WHERE lc.id_commande = p_id_commande;
  UPDATE commande
     SET statut = CASE
                    WHEN v_nb_lignes > 0 AND v_nb_soldees = v_nb_lignes THEN 'recue'
                    WHEN v_total_recu > 0 THEN 'partielle'
                    ELSE statut
                  END
   WHERE id_commande = p_id_commande
     AND statut <> 'annulee';
END;

-- Maintenance quotidienne : lots périmés (RG-13) et ordonnances expirées (RG-29)
-- À appeler chaque jour (par l'application Python au démarrage, par exemple).
CREATE PROCEDURE sp_maintenance_quotidienne()
BEGIN
  UPDATE stock
     SET statut = 'perime'
   WHERE date_peremption < CURDATE()
     AND statut = 'disponible';
  UPDATE ordonnance
     SET statut = 'expiree'
   WHERE date_validite < CURDATE()
     AND statut IN ('en_attente','partielle');
END;

-- =====================================================================
-- B. TRIGGERS SUR LES COMMANDES ET LES RÉCEPTIONS
-- =====================================================================

-- Une commande est passée par un pharmacien actif, à un fournisseur actif (RG-44, RG-55)
CREATE TRIGGER trg_commande_bi BEFORE INSERT ON commande
FOR EACH ROW
BEGIN
  DECLARE v_role  VARCHAR(20);
  DECLARE v_actif TINYINT;
  DECLARE v_f_actif TINYINT;
  SELECT p.role, p.actif INTO v_role, v_actif
    FROM personnel p WHERE p.id_personnel = NEW.id_personnel;
  IF v_role IS NULL OR v_role <> 'pharmacien' OR v_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seul un pharmacien actif peut passer une commande (RG-55)';
  END IF;
  SELECT f.actif INTO v_f_actif
    FROM fournisseur f WHERE f.id_fournisseur = NEW.id_fournisseur;
  IF v_f_actif IS NULL OR v_f_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Fournisseur inactif : commande impossible (RG-44)';
  END IF;
END;

-- On ne commande que des médicaments actifs (RG-05)
CREATE TRIGGER trg_ligne_commande_bi BEFORE INSERT ON ligne_commande
FOR EACH ROW
BEGIN
  DECLARE v_actif TINYINT;
  SELECT m.actif INTO v_actif FROM medicament m WHERE m.id_medicament = NEW.id_medicament;
  IF v_actif IS NULL OR v_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Médicament désactivé : commande impossible (RG-05)';
  END IF;
END;

-- Réception d'un lot (RG-07 à RG-12, RG-56)
CREATE TRIGGER trg_stock_bi BEFORE INSERT ON stock
FOR EACH ROW
BEGIN
  DECLARE v_actif   TINYINT;
  DECLARE v_nb      INT;
  DECLARE v_cstatut VARCHAR(10);
  SELECT COALESCE(MAX(m.actif),0) INTO v_actif
    FROM medicament m WHERE m.id_medicament = NEW.id_medicament;
  IF v_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Médicament inconnu ou désactivé (RG-05)';
  END IF;
  SELECT COUNT(*) INTO v_nb
    FROM ligne_commande lc
   WHERE lc.id_commande = NEW.id_commande AND lc.id_medicament = NEW.id_medicament;
  IF v_nb = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Ce médicament ne figure pas dans la commande (RG-56)';
  END IF;
  SELECT c.statut INTO v_cstatut FROM commande c WHERE c.id_commande = NEW.id_commande;
  IF v_cstatut = 'annulee' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Commande annulée : réception impossible (RG-56)';
  END IF;
  IF NEW.quantite_restante <> NEW.quantite_initiale THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'À la réception, quantité restante = quantité initiale (RG-11)';
  END IF;
  IF NEW.date_peremption <= CURDATE() THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Lot déjà périmé : réception refusée (RG-13)';
  END IF;
  SET NEW.statut = 'disponible';
END;

-- Après réception : mise à jour du statut de la commande (RG-58)
CREATE TRIGGER trg_stock_ai AFTER INSERT ON stock
FOR EACH ROW
BEGIN
  CALL sp_maj_statut_commande(NEW.id_commande);
END;

-- =====================================================================
-- C. TRIGGERS SUR LES ORDONNANCES
-- =====================================================================

-- Une ordonnance est enregistrée par un pharmacien actif, date de prescription pas dans le futur
CREATE TRIGGER trg_ordonnance_bi BEFORE INSERT ON ordonnance
FOR EACH ROW
BEGIN
  DECLARE v_role  VARCHAR(20);
  DECLARE v_actif TINYINT;
  SELECT p.role, p.actif INTO v_role, v_actif
    FROM personnel p WHERE p.id_personnel = NEW.id_personnel;
  IF v_role IS NULL OR v_role <> 'pharmacien' OR v_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Seul un pharmacien actif peut enregistrer une ordonnance (RG-30)';
  END IF;
  IF NEW.date_prescription > CURDATE() THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La date de prescription ne peut pas être dans le futur (RG-25)';
  END IF;
END;

-- =====================================================================
-- D. TRIGGERS SUR LES VENTES
-- =====================================================================

-- Création d'une vente : qui vend, et lien avec l'ordonnance (RG-33, RG-38)
CREATE TRIGGER trg_vente_bi BEFORE INSERT ON vente
FOR EACH ROW
BEGIN
  DECLARE v_role      VARCHAR(20);
  DECLARE v_actif     TINYINT;
  DECLARE v_o_client  INT;
  DECLARE v_o_statut  VARCHAR(12);
  DECLARE v_o_valid   DATE;
  SELECT p.role, p.actif INTO v_role, v_actif
    FROM personnel p WHERE p.id_personnel = NEW.id_personnel;
  IF v_role IS NULL OR v_actif = 0 OR v_role = 'administrateur' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Ce compte ne peut pas enregistrer de vente (RG-32)';
  END IF;
  IF NEW.id_ordonnance IS NOT NULL THEN
    IF v_role <> 'pharmacien' THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Une vente sur ordonnance doit être faite par un pharmacien (RG-38)';
    END IF;
    SELECT o.id_client, o.statut, o.date_validite INTO v_o_client, v_o_statut, v_o_valid
      FROM ordonnance o WHERE o.id_ordonnance = NEW.id_ordonnance;
    IF NEW.id_client IS NULL OR NEW.id_client <> v_o_client THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Le client de la vente doit être celui de l''ordonnance (RG-38)';
    END IF;
    IF v_o_statut IN ('expiree','soldee') OR v_o_valid < CURDATE() THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ordonnance expirée ou soldée (RG-31)';
    END IF;
  END IF;
  SET NEW.total = 0;   -- le total est calculé par les lignes de vente (RG-37)
END;

-- Contrôles sur chaque ligne de vente (RG-13, RG-35, RG-36, RG-38)
CREATE TRIGGER trg_ligne_vente_bi BEFORE INSERT ON ligne_vente
FOR EACH ROW
BEGIN
  DECLARE v_vente_statut VARCHAR(10);
  DECLARE v_id_ordo      INT;
  DECLARE v_lot_statut   VARCHAR(12);
  DECLARE v_peremption   DATE;
  DECLARE v_restante     INT;
  DECLARE v_id_med       INT;
  DECLARE v_prix         DECIMAL(10,2);
  DECLARE v_ordo_oblig   TINYINT;
  DECLARE v_med_actif    TINYINT;
  DECLARE v_prescrit     INT;
  DECLARE v_deja         INT;
  SELECT v.statut, v.id_ordonnance INTO v_vente_statut, v_id_ordo
    FROM vente v WHERE v.id_vente = NEW.id_vente;
  IF v_vente_statut <> 'validee' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Impossible d''ajouter une ligne à une vente annulée (RG-41)';
  END IF;
  SELECT s.statut, s.date_peremption, s.quantite_restante, s.id_medicament
    INTO v_lot_statut, v_peremption, v_restante, v_id_med
    FROM stock s WHERE s.id_stock = NEW.id_stock;
  SELECT m.prix_vente, m.ordonnance_obligatoire, m.actif
    INTO v_prix, v_ordo_oblig, v_med_actif
    FROM medicament m WHERE m.id_medicament = v_id_med;
  IF v_lot_statut <> 'disponible' OR v_peremption < CURDATE() THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Lot périmé ou indisponible : vente refusée (RG-13)';
  END IF;
  IF v_med_actif = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Médicament désactivé : vente refusée (RG-05)';
  END IF;
  IF NEW.quantite > v_restante THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Stock insuffisant dans ce lot (RG-35)';
  END IF;
  IF NEW.prix_unitaire <> v_prix THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Le prix unitaire doit être le prix de vente du catalogue (RG-36)';
  END IF;
  IF v_ordo_oblig = 1 THEN
    IF v_id_ordo IS NULL THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ordonnance obligatoire pour ce médicament (RG-38)';
    END IF;
    SELECT COALESCE(MAX(lo.quantite_prescrite),0) INTO v_prescrit
      FROM ligne_ordonnance lo
     WHERE lo.id_ordonnance = v_id_ordo AND lo.id_medicament = v_id_med;
    IF v_prescrit = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ce médicament ne figure pas sur l''ordonnance (RG-38)';
    END IF;
    SELECT COALESCE(SUM(lv.quantite),0) INTO v_deja
      FROM vente v2
      JOIN ligne_vente lv ON lv.id_vente = v2.id_vente
      JOIN stock s2       ON s2.id_stock = lv.id_stock
     WHERE v2.id_ordonnance = v_id_ordo
       AND v2.statut = 'validee'
       AND s2.id_medicament = v_id_med;
    IF v_deja + NEW.quantite > v_prescrit THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantité supérieure à celle prescrite sur l''ordonnance (RG-38)';
    END IF;
  END IF;
END;

-- Après insertion d'une ligne : sortie de stock, total, statut de l'ordonnance (RG-37, RG-40)
CREATE TRIGGER trg_ligne_vente_ai AFTER INSERT ON ligne_vente
FOR EACH ROW
BEGIN
  DECLARE v_id_ordo INT;
  -- Attention : MySQL évalue les affectations de gauche à droite,
  -- donc "statut" voit la nouvelle valeur de quantite_restante.
  UPDATE stock
     SET quantite_restante = quantite_restante - NEW.quantite,
         statut = IF(quantite_restante = 0, 'epuise', statut)
   WHERE id_stock = NEW.id_stock;
  UPDATE vente
     SET total = total + (NEW.quantite * NEW.prix_unitaire)
   WHERE id_vente = NEW.id_vente;
  SELECT v.id_ordonnance INTO v_id_ordo FROM vente v WHERE v.id_vente = NEW.id_vente;
  IF v_id_ordo IS NOT NULL THEN
    CALL sp_maj_statut_ordonnance(v_id_ordo);
  END IF;
END;

-- Annulation d'une vente : remise en stock et libération de l'ordonnance (RG-41)
CREATE TRIGGER trg_vente_bu BEFORE UPDATE ON vente
FOR EACH ROW
BEGIN
  IF OLD.statut = 'annulee' AND NEW.statut = 'validee' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Une vente annulée ne peut pas être réactivée (RG-41)';
  END IF;
END;

CREATE TRIGGER trg_vente_au AFTER UPDATE ON vente
FOR EACH ROW
BEGIN
  IF OLD.statut = 'validee' AND NEW.statut = 'annulee' THEN
    UPDATE stock s
      JOIN ligne_vente lv ON lv.id_stock = s.id_stock
       SET s.quantite_restante = s.quantite_restante + lv.quantite,
           s.statut = IF(s.statut = 'epuise', 'disponible', s.statut)
     WHERE lv.id_vente = NEW.id_vente;
    IF NEW.id_ordonnance IS NOT NULL THEN
      CALL sp_maj_statut_ordonnance(NEW.id_ordonnance);
    END IF;
  END IF;
END;

-- Pas de suppression ni de modification de l'historique des ventes (RG-51)
CREATE TRIGGER trg_vente_bd BEFORE DELETE ON vente
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Suppression interdite : annulez la vente à la place (RG-51)';
END;

CREATE TRIGGER trg_ligne_vente_bd BEFORE DELETE ON ligne_vente
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Suppression interdite : annulez la vente à la place (RG-51)';
END;

CREATE TRIGGER trg_ligne_vente_bu BEFORE UPDATE ON ligne_vente
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Modification interdite : annulez la vente et refaites-la (RG-51)';
END;

-- =====================================================================
-- E. VUES (la donnée mise en avant)
-- =====================================================================

-- Stock disponible par médicament (RG-15)
CREATE VIEW v_stock_disponible AS
SELECT m.id_medicament,
       m.nom_commercial,
       m.seuil_min,
       COALESCE(SUM(CASE WHEN s.statut = 'disponible' AND s.date_peremption >= CURDATE()
                         THEN s.quantite_restante END), 0) AS stock_disponible
  FROM medicament m
  LEFT JOIN stock s ON s.id_medicament = m.id_medicament
 WHERE m.actif = 1
 GROUP BY m.id_medicament, m.nom_commercial, m.seuil_min;

-- Médicaments sous leur seuil d'alerte (RG-16)
CREATE VIEW v_alertes_rupture AS
SELECT id_medicament, nom_commercial, seuil_min, stock_disponible
  FROM v_stock_disponible
 WHERE stock_disponible < seuil_min;

-- Lots périmés ou proches de la péremption : 90 jours (RG-17)
CREATE VIEW v_alertes_peremption AS
SELECT s.id_stock, m.nom_commercial, s.numero_lot, s.date_peremption,
       s.quantite_restante,
       DATEDIFF(s.date_peremption, CURDATE()) AS jours_restants
  FROM stock s
  JOIN medicament m ON m.id_medicament = s.id_medicament
 WHERE s.quantite_restante > 0
   AND s.statut IN ('disponible','perime')
   AND s.date_peremption <= DATE_ADD(CURDATE(), INTERVAL 90 DAY);

-- Quantité déjà délivrée par ligne d'ordonnance
CREATE VIEW v_ordonnance_delivrance AS
SELECT lo.id_ordonnance, lo.id_medicament, m.nom_commercial,
       lo.quantite_prescrite,
       COALESCE(SUM(CASE WHEN v.statut = 'validee' AND s.id_stock IS NOT NULL
                         THEN lv.quantite END), 0) AS quantite_delivree
  FROM ligne_ordonnance lo
  JOIN medicament m ON m.id_medicament = lo.id_medicament
  LEFT JOIN vente v        ON v.id_ordonnance = lo.id_ordonnance
  LEFT JOIN ligne_vente lv ON lv.id_vente = v.id_vente
  LEFT JOIN stock s        ON s.id_stock = lv.id_stock AND s.id_medicament = lo.id_medicament
 GROUP BY lo.id_ordonnance, lo.id_medicament, m.nom_commercial, lo.quantite_prescrite;

-- Fin du script 2.
