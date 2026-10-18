-- =====================================================================
--  PROJET BASE DE DONNÉES - GESTION D'UNE PHARMACIE
--  Script 1/4 : création de la base et des tables
--  SGBD : MySQL 8.0.16+ (ou MariaDB 10.2+) - moteur InnoDB - utf8mb4
--  Exécution dans DBeaver : ouvrir ce fichier, puis "Exécuter le script" (Alt+X)
--
--  ATTENTION : la ligne DROP DATABASE supprime toute base "pharmacie"
--  existante. Elle permet de repartir de zéro en relançant les 4 scripts.
-- =====================================================================

DROP DATABASE IF EXISTS pharmacie;
CREATE DATABASE pharmacie
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE pharmacie;

-- ---------------------------------------------------------------------
-- 1. MEDICAMENT : catalogue des produits (RG-01 à RG-06)
-- ---------------------------------------------------------------------
CREATE TABLE medicament (
  id_medicament          INT           NOT NULL AUTO_INCREMENT,
  nom_commercial         VARCHAR(100)  NOT NULL,
  dci                    VARCHAR(100)  NOT NULL,
  forme                  VARCHAR(50)   NOT NULL,
  dosage                 VARCHAR(50)   NOT NULL,
  categorie              VARCHAR(60)   NULL,
  prix_vente             DECIMAL(10,2) NOT NULL,
  ordonnance_obligatoire TINYINT(1)    NOT NULL DEFAULT 0,
  seuil_min              INT           NOT NULL DEFAULT 10,
  actif                  TINYINT(1)    NOT NULL DEFAULT 1,
  PRIMARY KEY (id_medicament),
  UNIQUE KEY uq_medicament (nom_commercial, forme, dosage),
  CONSTRAINT ck_medicament_prix  CHECK (prix_vente > 0),
  CONSTRAINT ck_medicament_seuil CHECK (seuil_min >= 0),
  CONSTRAINT ck_medicament_ordo  CHECK (ordonnance_obligatoire IN (0,1)),
  CONSTRAINT ck_medicament_actif CHECK (actif IN (0,1))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. FOURNISSEUR (RG-43, RG-44)
-- ---------------------------------------------------------------------
CREATE TABLE fournisseur (
  id_fournisseur        INT          NOT NULL AUTO_INCREMENT,
  raison_sociale        VARCHAR(100) NOT NULL,
  telephone             VARCHAR(20)  NOT NULL,
  email                 VARCHAR(100) NULL,
  adresse               VARCHAR(200) NULL,
  delai_livraison_jours INT          NULL,
  actif                 TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id_fournisseur),
  UNIQUE KEY uq_fournisseur_raison (raison_sociale),
  CONSTRAINT ck_fournisseur_delai CHECK (delai_livraison_jours IS NULL OR delai_livraison_jours >= 0),
  CONSTRAINT ck_fournisseur_actif CHECK (actif IN (0,1))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. PERSONNEL (ex-Pharmacien) : pharmacien, caissier, administrateur
--    (RG-46 à RG-50)
-- ---------------------------------------------------------------------
CREATE TABLE personnel (
  id_personnel      INT          NOT NULL AUTO_INCREMENT,
  nom               VARCHAR(60)  NOT NULL,
  prenom            VARCHAR(60)  NOT NULL,
  login             VARCHAR(50)  NOT NULL,
  mot_de_passe_hash VARCHAR(255) NOT NULL,
  role              ENUM('pharmacien','caissier','administrateur') NOT NULL,
  telephone         VARCHAR(20)  NULL,
  date_embauche     DATE         NULL,
  actif             TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id_personnel),
  UNIQUE KEY uq_personnel_login (login),
  CONSTRAINT ck_personnel_actif CHECK (actif IN (0,1))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. CLIENT (RG-19 à RG-23)
-- ---------------------------------------------------------------------
CREATE TABLE client (
  id_client      INT          NOT NULL AUTO_INCREMENT,
  nom            VARCHAR(60)  NOT NULL,
  prenom         VARCHAR(60)  NOT NULL,
  date_naissance DATE         NOT NULL,
  telephone      VARCHAR(20)  NULL,
  email          VARCHAR(100) NULL,
  adresse        VARCHAR(200) NULL,
  date_creation  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_client),
  UNIQUE KEY uq_client_identite (nom, prenom, date_naissance)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. COMMANDE : commande passée à un fournisseur (RG-55 à RG-60)
-- ---------------------------------------------------------------------
CREATE TABLE commande (
  id_commande           INT      NOT NULL AUTO_INCREMENT,
  id_fournisseur        INT      NOT NULL,
  id_personnel          INT      NOT NULL,
  date_commande         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_livraison_prevue DATE     NULL,
  statut                ENUM('en_cours','partielle','recue','annulee') NOT NULL DEFAULT 'en_cours',
  PRIMARY KEY (id_commande),
  KEY idx_commande_fournisseur (id_fournisseur),
  KEY idx_commande_personnel (id_personnel),
  CONSTRAINT fk_commande_fournisseur FOREIGN KEY (id_fournisseur)
    REFERENCES fournisseur (id_fournisseur) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_commande_personnel FOREIGN KEY (id_personnel)
    REFERENCES personnel (id_personnel) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. LIGNE_COMMANDE : médicaments demandés dans une commande
--    (association porteuse COMMANDE - MEDICAMENT)
-- ---------------------------------------------------------------------
CREATE TABLE ligne_commande (
  id_commande        INT           NOT NULL,
  id_medicament      INT           NOT NULL,
  quantite_commandee INT           NOT NULL,
  prix_achat_prevu   DECIMAL(10,2) NULL,
  PRIMARY KEY (id_commande, id_medicament),
  KEY idx_lc_medicament (id_medicament),
  CONSTRAINT fk_lc_commande FOREIGN KEY (id_commande)
    REFERENCES commande (id_commande) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_lc_medicament FOREIGN KEY (id_medicament)
    REFERENCES medicament (id_medicament) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_lc_quantite CHECK (quantite_commandee > 0),
  CONSTRAINT ck_lc_prix     CHECK (prix_achat_prevu IS NULL OR prix_achat_prevu >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. STOCK : un enregistrement = un lot reçu (RG-07 à RG-18)
--    Le fournisseur d'un lot se retrouve via la commande.
-- ---------------------------------------------------------------------
CREATE TABLE stock (
  id_stock          INT           NOT NULL AUTO_INCREMENT,
  id_medicament     INT           NOT NULL,
  id_commande       INT           NOT NULL,
  numero_lot        VARCHAR(50)   NOT NULL,
  date_reception    DATE          NOT NULL,
  date_peremption   DATE          NOT NULL,
  quantite_initiale INT           NOT NULL,
  quantite_restante INT           NOT NULL,
  prix_achat        DECIMAL(10,2) NOT NULL,
  statut            ENUM('disponible','epuise','perime','retire') NOT NULL DEFAULT 'disponible',
  PRIMARY KEY (id_stock),
  UNIQUE KEY uq_stock_lot (id_medicament, numero_lot),
  KEY idx_stock_commande (id_commande),
  KEY idx_stock_peremption (date_peremption),
  CONSTRAINT fk_stock_medicament FOREIGN KEY (id_medicament)
    REFERENCES medicament (id_medicament) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_stock_commande FOREIGN KEY (id_commande)
    REFERENCES commande (id_commande) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_stock_dates     CHECK (date_peremption > date_reception),
  CONSTRAINT ck_stock_qte_init  CHECK (quantite_initiale > 0),
  CONSTRAINT ck_stock_qte_rest  CHECK (quantite_restante >= 0 AND quantite_restante <= quantite_initiale),
  CONSTRAINT ck_stock_prix      CHECK (prix_achat >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 8. ORDONNANCE (RG-24 à RG-31)
-- ---------------------------------------------------------------------
CREATE TABLE ordonnance (
  id_ordonnance        INT          NOT NULL AUTO_INCREMENT,
  id_client            INT          NOT NULL,
  id_personnel         INT          NOT NULL,
  nom_medecin          VARCHAR(100) NOT NULL,
  numero_ordre_medecin VARCHAR(30)  NULL,
  date_prescription    DATE         NOT NULL,
  date_validite        DATE         NOT NULL,
  statut               ENUM('en_attente','partielle','soldee','expiree') NOT NULL DEFAULT 'en_attente',
  date_enregistrement  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_ordonnance),
  KEY idx_ordonnance_client (id_client),
  KEY idx_ordonnance_personnel (id_personnel),
  CONSTRAINT fk_ordonnance_client FOREIGN KEY (id_client)
    REFERENCES client (id_client) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_ordonnance_personnel FOREIGN KEY (id_personnel)
    REFERENCES personnel (id_personnel) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_ordonnance_validite CHECK (date_validite >= date_prescription)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 9. LIGNE_ORDONNANCE (association porteuse ORDONNANCE - MEDICAMENT)
-- ---------------------------------------------------------------------
CREATE TABLE ligne_ordonnance (
  id_ordonnance          INT          NOT NULL,
  id_medicament          INT          NOT NULL,
  quantite_prescrite     INT          NOT NULL,
  posologie              VARCHAR(200) NOT NULL,
  duree_traitement_jours INT          NULL,
  PRIMARY KEY (id_ordonnance, id_medicament),
  KEY idx_lo_medicament (id_medicament),
  CONSTRAINT fk_lo_ordonnance FOREIGN KEY (id_ordonnance)
    REFERENCES ordonnance (id_ordonnance) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_lo_medicament FOREIGN KEY (id_medicament)
    REFERENCES medicament (id_medicament) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_lo_quantite CHECK (quantite_prescrite > 0),
  CONSTRAINT ck_lo_duree    CHECK (duree_traitement_jours IS NULL OR duree_traitement_jours > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 10. VENTE (RG-32 à RG-42)
-- ---------------------------------------------------------------------
CREATE TABLE vente (
  id_vente       INT           NOT NULL AUTO_INCREMENT,
  date_vente     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_personnel   INT           NOT NULL,
  id_client      INT           NULL,
  id_ordonnance  INT           NULL,
  mode_paiement  ENUM('especes','carte','mobile_money') NOT NULL,
  statut         ENUM('validee','annulee') NOT NULL DEFAULT 'validee',
  total          DECIMAL(10,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id_vente),
  KEY idx_vente_date (date_vente),
  KEY idx_vente_personnel (id_personnel),
  KEY idx_vente_client (id_client),
  KEY idx_vente_ordonnance (id_ordonnance),
  CONSTRAINT fk_vente_personnel FOREIGN KEY (id_personnel)
    REFERENCES personnel (id_personnel) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_vente_client FOREIGN KEY (id_client)
    REFERENCES client (id_client) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_vente_ordonnance FOREIGN KEY (id_ordonnance)
    REFERENCES ordonnance (id_ordonnance) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_vente_total CHECK (total >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 11. LIGNE_VENTE (association porteuse VENTE - STOCK)
--     Une ligne = un lot précis, donc un médicament précis (traçabilité)
-- ---------------------------------------------------------------------
CREATE TABLE ligne_vente (
  id_vente      INT           NOT NULL,
  id_stock      INT           NOT NULL,
  quantite      INT           NOT NULL,
  prix_unitaire DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id_vente, id_stock),
  KEY idx_lv_stock (id_stock),
  CONSTRAINT fk_lv_vente FOREIGN KEY (id_vente)
    REFERENCES vente (id_vente) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_lv_stock FOREIGN KEY (id_stock)
    REFERENCES stock (id_stock) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_lv_quantite CHECK (quantite > 0),
  CONSTRAINT ck_lv_prix     CHECK (prix_unitaire > 0)
) ENGINE=InnoDB;

-- Fin du script 1. Vérification : SHOW TABLES;  (11 tables attendues)
