-- =====================================================================
--  Script 3/4 : jeu de données de test
--  À exécuter APRÈS les scripts 01 et 02 (les triggers contrôlent les insertions).
--  Les identifiants (1, 2, 3...) supposent une base neuve, créée par le script 01.
--  Mots de passe de démonstration : hachés ici en SHA2 pour l'exemple.
--  Dans l'application Python, utilisez un vrai hachage (bcrypt ou argon2).
-- =====================================================================

USE pharmacie;

-- ---------------------------------------------------------------------
-- Personnel : 1 pharmacien, 1 caissier, 1 administrateur
-- ---------------------------------------------------------------------
INSERT INTO personnel (nom, prenom, login, mot_de_passe_hash, role, telephone, date_embauche) VALUES
 ('Dupont', 'Claire', 'cdupont', SHA2('Pharma2026!', 256), 'pharmacien',     '600000001', '2021-03-01'),
 ('Ngono',  'Marie',  'mngono',  SHA2('Caisse2026!', 256), 'caissier',       '600000002', '2023-06-15'),
 ('Admin',  'Base',   'admin',   SHA2('Admin2026!', 256),  'administrateur', '600000003', '2020-01-10');

-- ---------------------------------------------------------------------
-- Fournisseurs
-- ---------------------------------------------------------------------
INSERT INTO fournisseur (raison_sociale, telephone, email, adresse, delai_livraison_jours) VALUES
 ('PharmaDistrib', '600100001', 'contact@pharmadistrib.example', 'Zone industrielle, Douala', 2),
 ('MediSupply',    '600100002', 'ventes@medisupply.example',     'Avenue centrale, Yaoundé',  4),
 ('SantePlus Grossiste', '600100003', 'commandes@santeplus.example', 'Boulevard du marché, Douala', 3);

-- ---------------------------------------------------------------------
-- Médicaments (10)
-- ---------------------------------------------------------------------
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES
 ('Doliprane',          'paracétamol',                    'comprimé',                  '500 mg',       'Antalgique',       1500, 0, 20),
 ('Efferalgan',         'paracétamol',                    'comprimé effervescent',     '1 g',          'Antalgique',       2000, 0, 15),
 ('Amoxicilline Biogaran','amoxicilline',                 'gélule',                    '500 mg',       'Antibiotique',     3500, 1, 10),
 ('Augmentin',          'amoxicilline + acide clavulanique','comprimé',                '1 g/125 mg',   'Antibiotique',     6500, 1, 10),
 ('Ventoline',          'salbutamol',                     'aérosol doseur',            '100 mcg',      'Respiratoire',     4200, 1, 5),
 ('Spasfon',            'phloroglucinol',                 'comprimé',                  '80 mg',        'Antispasmodique',  2500, 0, 10),
 ('Smecta',             'diosmectite',                    'poudre pour suspension',    '3 g',          'Digestif',         3000, 0, 10),
 ('Oméprazole Arrow',   'oméprazole',                     'gélule',                    '20 mg',        'Gastro-entérologie',3800, 1, 10),
 ('Vitamine C Upsa',    'acide ascorbique',               'comprimé effervescent',     '500 mg',       'Vitamines',        2200, 0, 10),
 ('Loratadine Mylan',   'loratadine',                     'comprimé',                  '10 mg',        'Antihistaminique', 2800, 0, 8);

-- ---------------------------------------------------------------------
-- Clients (5)
-- ---------------------------------------------------------------------
INSERT INTO client (nom, prenom, date_naissance, telephone, email, adresse) VALUES
 ('Fotso',   'Jean',    '1985-04-12', '690000001', 'jean.fotso@example.com',  'Akwa, Douala'),
 ('Tchoua',  'Aminata', '1992-09-03', '690000002', NULL,                      'Bonapriso, Douala'),
 ('Essomba', 'Paul',    '1978-01-27', '690000003', 'paul.essomba@example.com', 'Bonamoussadi, Douala'),
 ('Njoya',   'Sandra',  '2001-11-19', '690000004', NULL,                      'Deido, Douala'),
 ('Kamga',   'Albert',  '1965-06-30', '690000005', NULL,                      'Makepe, Douala');

-- ---------------------------------------------------------------------
-- Commande 1 (PharmaDistrib) : réception complète -> statut "recue"
-- ---------------------------------------------------------------------
INSERT INTO commande (id_fournisseur, id_personnel, date_livraison_prevue)
VALUES (1, 1, DATE_ADD(CURDATE(), INTERVAL 2 DAY));

INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES
 (1, 1, 100, 900),
 (1, 2,  50, 1300),
 (1, 3,  40, 2200),
 (1, 6,  40, 1500),
 (1, 7,  60, 1900);

-- Lots reçus (la date de réception est celle du jour)
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES
 (1, 1, 'DOLI-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 18 MONTH), 100, 100, 900),
 (2, 1, 'EFFE-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 MONTH),  30,  30, 1300),
 (2, 1, 'EFFE-2512', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 6 MONTH),   20,  20, 1300),
 (3, 1, 'AMOX-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 20 MONTH),  40,  40, 2200),
 (6, 1, 'SPAS-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 24 MONTH),  40,  40, 1500),
 (7, 1, 'SMEC-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 45 DAY),    60,  60, 1900);

-- Simulation d'un lot ancien et périmé (le trigger interdit de recevoir un lot déjà périmé,
-- on le fait donc "vieillir" par une mise à jour) :
UPDATE stock
   SET date_reception  = DATE_SUB(CURDATE(), INTERVAL 400 DAY),
       date_peremption = DATE_SUB(CURDATE(), INTERVAL 5 DAY),
       statut          = 'perime'
 WHERE numero_lot = 'EFFE-2512';

-- ---------------------------------------------------------------------
-- Commande 2 (MediSupply) : réception partielle -> statut "partielle"
-- (le Loratadine, médicament 10, n'est pas encore livré)
-- ---------------------------------------------------------------------
INSERT INTO commande (id_fournisseur, id_personnel, date_livraison_prevue)
VALUES (2, 1, DATE_ADD(CURDATE(), INTERVAL 4 DAY));

INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES
 (2, 4, 30, 4500),
 (2, 5, 20, 3000),
 (2, 8, 40, 2600),
 (2, 9, 50, 1500),
 (2, 10, 40, 1900);

INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES
 (4, 2, 'AUGM-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 22 MONTH), 30, 30, 4500),
 (5, 2, 'VENT-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 16 MONTH), 20, 20, 3000),
 (8, 2, 'OMEP-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 MONTH), 40, 40, 2600),
 (9, 2, 'VITC-2601', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 12 MONTH), 50, 50, 1500);

-- ---------------------------------------------------------------------
-- Ordonnance 1 : Jean Fotso, validité 2 semaines (14 jours)
-- ---------------------------------------------------------------------
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite)
VALUES (1, 1, 'Dr Mballa', 'ONMC-10234', DATE_SUB(CURDATE(), INTERVAL 2 DAY),
        DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 2 DAY), INTERVAL 14 DAY));

INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES
 (1, 3, 21, '1 gélule 3 fois par jour pendant 7 jours', 7),
 (1, 8, 14, '1 gélule le matin à jeun pendant 14 jours', 14);

-- ---------------------------------------------------------------------
-- Ventes
--  Les id_stock (lots) correspondent à l'ordre d'insertion des lots ci-dessus :
--   1 DOLI-2601, 2 EFFE-2601, 3 EFFE-2512 (périmé), 4 AMOX-2601, 5 SPAS-2601,
--   6 SMEC-2601, 7 AUGM-2601, 8 VENT-2601, 9 OMEP-2601, 10 VITC-2601
--  Le prix_unitaire DOIT être le prix de vente du catalogue (trigger, RG-36).
--  NB : on n'utilise pas INSERT ... SELECT depuis la table stock, car MySQL
--  interdit à un trigger de modifier une table lue par la même instruction.
-- ---------------------------------------------------------------------

-- Vente 1 : la caissière vend des médicaments libres, sans client
INSERT INTO vente (id_personnel, mode_paiement) VALUES (2, 'especes');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (1, 1, 2, 1500);  -- Doliprane
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (1, 6, 3, 3000);  -- Smecta

-- Vente 2 : la pharmacienne délivre l'ordonnance 1 (délivrance partielle)
INSERT INTO vente (id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (1, 1, 1, 'carte');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (2, 4, 21, 3500); -- Amoxicilline
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (2, 9, 7, 3800);  -- Oméprazole (7 sur 14)

-- Vente 3 : la pharmacienne vend à une cliente enregistrée, sans ordonnance
INSERT INTO vente (id_personnel, id_client, mode_paiement) VALUES (1, 2, 'mobile_money');
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (3, 5, 1, 2500);  -- Spasfon
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (3, 10, 2, 2200); -- Vitamine C

-- Vérification rapide : les trois requêtes ci-dessous doivent donner
--  statut commande 1 = recue, commande 2 = partielle, ordonnance 1 = partielle
SELECT id_commande, statut FROM commande;
SELECT id_ordonnance, statut FROM ordonnance;
SELECT id_vente, total, statut FROM vente;

-- Fin du script 3.
