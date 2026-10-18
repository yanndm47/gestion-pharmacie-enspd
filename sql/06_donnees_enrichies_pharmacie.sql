-- =====================================================================
--  Script 6 : JEU DE DONNÉES ENRICHI (généré par tools/generer_donnees.py)
--  Graine : 2026 (même graine = même fichier)
--
--  À exécuter APRÈS les scripts 01, 02 et 03 (il complète le jeu de test).
--  Ajoute : 40 médicaments (50 au total), 25 clients (30), 2 fournisseurs (5), 2 membres du
--  personnel, des commandes et des lots, 19 ordonnances (20), des ventes sur 90 jours.
--
--  ATTENTION : après ce script, les valeurs attendues des scripts 04 et 05 changent
--  (elles décrivent le petit jeu de test du script 03).
--
--  Exécution : Alt+X dans DBeaver (quelques dizaines de secondes). Tout est dans une
--  transaction : en cas d'erreur, exécutez ROLLBACK; puis relancez 01, 02, 03 avant de recommencer.
--  Les dates sont relatives à CURDATE() : les ventes couvrent les 90 derniers jours.
-- =====================================================================

USE pharmacie;
START TRANSACTION;

-- ---------------------------------------------------------------------
-- 1. Personnel
-- ---------------------------------------------------------------------
INSERT INTO personnel (nom, prenom, login, mot_de_passe_hash, role, telephone, date_embauche) VALUES ('Mballa', 'Pierre', 'pmballa', SHA2('Medecin2026!', 256), 'pharmacien', '600000004', '2022-09-05');
INSERT INTO personnel (nom, prenom, login, mot_de_passe_hash, role, telephone, date_embauche) VALUES ('Tagne', 'Julie', 'jtagne', SHA2('Caisse2026!', 256), 'caissier', '600000005', '2024-02-12');
SET @p_ph1 := (SELECT id_personnel FROM personnel WHERE login = 'cdupont');
SET @p_ph2 := (SELECT id_personnel FROM personnel WHERE login = 'pmballa');
SET @p_ca1 := (SELECT id_personnel FROM personnel WHERE login = 'mngono');
SET @p_ca2 := (SELECT id_personnel FROM personnel WHERE login = 'jtagne');

-- ---------------------------------------------------------------------
-- 2. Fournisseurs
-- ---------------------------------------------------------------------
INSERT INTO fournisseur (raison_sociale, telephone, email, adresse, delai_livraison_jours) VALUES ('Oméga Pharma Distribution', '600100004', 'achats@omega-pharma.example', 'Rue du commerce, Douala', 3);
INSERT INTO fournisseur (raison_sociale, telephone, email, adresse, delai_livraison_jours) VALUES ('BioMed Afrique', '600100005', 'info@biomed-afrique.example', 'Avenue de la paix, Yaoundé', 5);
SET @f1 := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = 'PharmaDistrib');
SET @f2 := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = 'MediSupply');
SET @f3 := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = 'SantePlus Grossiste');
SET @f4 := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = 'Oméga Pharma Distribution');
SET @f5 := (SELECT id_fournisseur FROM fournisseur WHERE raison_sociale = 'BioMed Afrique');

-- ---------------------------------------------------------------------
-- 3. Médicaments (les 10 premiers existent déjà : on retrouve leur identifiant)
-- ---------------------------------------------------------------------
SET @m1 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Doliprane' AND forme = 'comprimé' AND dosage = '500 mg');
SET @m2 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Efferalgan' AND forme = 'comprimé effervescent' AND dosage = '1 g');
SET @m3 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Amoxicilline Biogaran' AND forme = 'gélule' AND dosage = '500 mg');
SET @m4 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Augmentin' AND forme = 'comprimé' AND dosage = '1 g/125 mg');
SET @m5 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Ventoline' AND forme = 'aérosol doseur' AND dosage = '100 mcg');
SET @m6 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Spasfon' AND forme = 'comprimé' AND dosage = '80 mg');
SET @m7 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Smecta' AND forme = 'poudre pour suspension' AND dosage = '3 g');
SET @m8 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Oméprazole Arrow' AND forme = 'gélule' AND dosage = '20 mg');
SET @m9 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Vitamine C Upsa' AND forme = 'comprimé effervescent' AND dosage = '500 mg');
SET @m10 := (SELECT id_medicament FROM medicament WHERE nom_commercial = 'Loratadine Mylan' AND forme = 'comprimé' AND dosage = '10 mg');
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Paracétamol Biogaran', 'paracétamol', 'comprimé', '1 g', 'Antalgique', 1800, 0, 15);
SET @m11 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Ibuprofène Arrow', 'ibuprofène', 'comprimé', '400 mg', 'Anti-inflammatoire', 2300, 0, 15);
SET @m12 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Aspirine Upsa', 'acide acétylsalicylique', 'comprimé effervescent', '500 mg', 'Antalgique', 2000, 0, 10);
SET @m13 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Tramadol Zentiva', 'tramadol', 'gélule', '50 mg', 'Antalgique', 4800, 1, 8);
SET @m14 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Ciprofloxacine Mylan', 'ciprofloxacine', 'comprimé', '500 mg', 'Antibiotique', 5200, 1, 8);
SET @m15 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Azithromycine Sandoz', 'azithromycine', 'comprimé', '250 mg', 'Antibiotique', 6800, 1, 8);
SET @m16 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Métronidazole Arrow', 'métronidazole', 'comprimé', '500 mg', 'Antibiotique', 2900, 1, 10);
SET @m17 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Cotrimoxazole Teva', 'sulfaméthoxazole + triméthoprime', 'comprimé', '480 mg', 'Antibiotique', 2500, 1, 10);
SET @m18 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Artéméther-Luméfantrine Mylan', 'artéméther + luméfantrine', 'comprimé', '20/120 mg', 'Antipaludique', 3800, 1, 20);
SET @m19 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Quinine Mylan', 'quinine', 'comprimé', '300 mg', 'Antipaludique', 3200, 1, 10);
SET @m20 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Metformine Biogaran', 'metformine', 'comprimé', '850 mg', 'Diabète', 3400, 1, 15);
SET @m21 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Glibenclamide Teva', 'glibenclamide', 'comprimé', '5 mg', 'Diabète', 2700, 1, 10);
SET @m22 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Amlodipine Sandoz', 'amlodipine', 'comprimé', '5 mg', 'Cardiologie', 3600, 1, 12);
SET @m23 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Énalapril Arrow', 'énalapril', 'comprimé', '10 mg', 'Cardiologie', 3100, 1, 12);
SET @m24 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Atorvastatine Zentiva', 'atorvastatine', 'comprimé', '20 mg', 'Cardiologie', 5400, 1, 10);
SET @m25 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Furosémide Teva', 'furosémide', 'comprimé', '40 mg', 'Cardiologie', 2200, 1, 8);
SET @m26 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Ésoméprazole Mylan', 'ésoméprazole', 'gélule', '20 mg', 'Gastro-entérologie', 4400, 1, 8);
SET @m27 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Dompéridone Arrow', 'dompéridone', 'comprimé', '10 mg', 'Gastro-entérologie', 2600, 0, 10);
SET @m28 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Sels de réhydratation orale', 'SRO', 'poudre pour solution buvable', '1 sachet', 'Digestif', 700, 0, 40);
SET @m29 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Lopéramide Biogaran', 'lopéramide', 'gélule', '2 mg', 'Digestif', 2100, 0, 10);
SET @m30 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Cétirizine Mylan', 'cétirizine', 'comprimé', '10 mg', 'Antihistaminique', 2400, 0, 10);
SET @m31 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Prednisolone Teva', 'prednisolone', 'comprimé', '20 mg', 'Corticoïde', 3300, 1, 8);
SET @m32 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Salbutamol Teva sirop', 'salbutamol', 'sirop', '2 mg/5 ml', 'Respiratoire', 2800, 1, 6);
SET @m33 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Ambroxol Zentiva', 'ambroxol', 'sirop', '30 mg/5 ml', 'Respiratoire', 3000, 0, 8);
SET @m34 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Vitamine B complexe', 'vitamines B', 'comprimé', '1 comprimé', 'Vitamines', 2500, 0, 10);
SET @m35 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Fer + acide folique', 'sulfate ferreux + acide folique', 'comprimé', '200/0,4 mg', 'Vitamines', 2900, 0, 15);
SET @m36 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Zinc Gifrer', 'zinc', 'comprimé dispersible', '20 mg', 'Vitamines', 2300, 0, 10);
SET @m37 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Calcium D3 Upsa', 'calcium + vitamine D3', 'comprimé à croquer', '500 mg/400 UI', 'Vitamines', 3900, 0, 8);
SET @m38 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Povidone iodée', 'povidone iodée', 'solution cutanée', '10 %', 'Antiseptique', 2200, 0, 10);
SET @m39 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Chlorhexidine', 'chlorhexidine', 'solution cutanée', '0,05 %', 'Antiseptique', 1900, 0, 10);
SET @m40 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Diclofénac gel', 'diclofénac', 'gel', '1 %', 'Anti-inflammatoire', 3500, 0, 8);
SET @m41 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Collyre Chloramphénicol', 'chloramphénicol', 'collyre', '0,5 %', 'Ophtalmologie', 2600, 1, 5);
SET @m42 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Mébendazole Teva', 'mébendazole', 'comprimé', '100 mg', 'Antiparasitaire', 1800, 0, 10);
SET @m43 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Albendazole Arrow', 'albendazole', 'comprimé', '400 mg', 'Antiparasitaire', 2200, 0, 10);
SET @m44 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Fluconazole Mylan', 'fluconazole', 'gélule', '150 mg', 'Antifongique', 3600, 1, 6);
SET @m45 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Hydrocortisone crème', 'hydrocortisone', 'crème', '1 %', 'Dermatologie', 3200, 1, 6);
SET @m46 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Diazépam Teva', 'diazépam', 'comprimé', '5 mg', 'Psychotrope', 3100, 1, 5);
SET @m47 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Lévothyroxine Merck', 'lévothyroxine', 'comprimé', '100 mcg', 'Endocrinologie', 4200, 1, 6);
SET @m48 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Lisinopril Mylan', 'lisinopril', 'comprimé', '10 mg', 'Cardiologie', 3400, 1, 8);
SET @m49 := LAST_INSERT_ID();
INSERT INTO medicament (nom_commercial, dci, forme, dosage, categorie, prix_vente, ordonnance_obligatoire, seuil_min) VALUES ('Paracétamol sirop enfant', 'paracétamol', 'sirop', '120 mg/5 ml', 'Antalgique', 2100, 0, 12);
SET @m50 := LAST_INSERT_ID();

-- ---------------------------------------------------------------------
-- 4. Clients (les 5 premiers existent déjà)
-- ---------------------------------------------------------------------
SET @c1 := (SELECT id_client FROM client WHERE nom = 'Fotso' AND prenom = 'Jean' AND date_naissance = '1985-04-12');
SET @c2 := (SELECT id_client FROM client WHERE nom = 'Tchoua' AND prenom = 'Aminata' AND date_naissance = '1992-09-03');
SET @c3 := (SELECT id_client FROM client WHERE nom = 'Essomba' AND prenom = 'Paul' AND date_naissance = '1978-01-27');
SET @c4 := (SELECT id_client FROM client WHERE nom = 'Njoya' AND prenom = 'Sandra' AND date_naissance = '2001-11-19');
SET @c5 := (SELECT id_client FROM client WHERE nom = 'Kamga' AND prenom = 'Albert' AND date_naissance = '1965-06-30');
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Nkou', 'Béatrice', '1990-03-14', '691000001');
SET @c6 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Mvondo', 'Samuel', '1982-07-21', '691000002');
SET @c7 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Ateba', 'Colette', '1975-12-02', '691000003');
SET @c8 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Biyik', 'Hervé', '1998-05-30', '691000004');
SET @c9 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Onana', 'Grace', '1969-08-17', '691000005');
SET @c10 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Eyenga', 'Didier', '1988-10-09', '691000006');
SET @c11 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Fouda', 'Nadine', '1995-01-25', '691000007');
SET @c12 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Manga', 'Roland', '1958-04-04', '691000008');
SET @c13 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Abena', 'Sylvie', '1983-06-12', '691000009');
SET @c14 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Tsimi', 'Landry', '2003-09-19', '691000010');
SET @c15 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Owona', 'Mireille', '1971-02-28', '691000011');
SET @c16 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Bekolo', 'Patrick', '1992-11-11', '691000012');
SET @c17 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Nga', 'Clarisse', '1987-03-03', '691000013');
SET @c18 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Zang', 'Olivier', '1963-07-07', '691000014');
SET @c19 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Ebogo', 'Pascaline', '1999-12-24', '691000015');
SET @c20 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Mbarga', 'Thierry', '1980-05-16', '691000016');
SET @c21 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Etoga', 'Solange', '1977-09-29', '691000017');
SET @c22 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Belinga', 'Cédric', '1994-08-08', '691000018');
SET @c23 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Atangana', 'Josiane', '1966-01-15', '691000019');
SET @c24 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Ngoh', 'Bertrand', '1989-06-22', '691000020');
SET @c25 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Ndzana', 'Estelle', '1996-04-18', '691000021');
SET @c26 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Messi', 'Armand', '1973-10-31', '691000022');
SET @c27 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Tabi', 'Florence', '2000-02-06', '691000023');
SET @c28 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Awono', 'Gilbert', '1961-11-20', '691000024');
SET @c29 := LAST_INSERT_ID();
INSERT INTO client (nom, prenom, date_naissance, telephone) VALUES ('Essama', 'Viviane', '1985-07-14', '691000025');
SET @c30 := LAST_INSERT_ID();

-- ---------------------------------------------------------------------
-- 5. Vie de la pharmacie, dans l'ordre chronologique : commandes, réceptions, ordonnances, ventes
-- ---------------------------------------------------------------------

-- Commande @co1 (PharmaDistrib) passée il y a 105 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f1, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 105 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 102 DAY));
SET @co1 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m1, 30, 1050);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m6, 24, 1400);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m11, 41, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m16, 25, 3900);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m21, 25, 2300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m26, 25, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m31, 24, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m36, 27, 1850);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m41, 40, 2250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co1, @m46, 118, 2050);

-- Commande @co2 (MediSupply) passée il y a 105 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f2, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 105 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 102 DAY));
SET @co2 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m2, 20, 1250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m7, 24, 1900);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m12, 52, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m17, 84, 1750);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m22, 44, 1500);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m27, 25, 2600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m32, 78, 2350);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m37, 24, 1650);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m42, 58, 1450);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co2, @m47, 106, 2100);

-- Commande @co3 (SantePlus Grossiste) passée il y a 105 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f3, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 105 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 102 DAY));
SET @co3 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m3, 73, 2050);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m8, 25, 2750);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m13, 40, 1250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m18, 42, 1550);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m23, 25, 2200);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m28, 40, 1500);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m33, 25, 2100);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m38, 24, 2300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m43, 24, 1000);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co3, @m48, 25, 2850);

-- Commande @co4 (Oméga Pharma Distribution) passée il y a 105 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f4, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 105 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 102 DAY));
SET @co4 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m4, 161, 4250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m9, 18, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m14, 44, 3350);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m19, 55, 2350);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m24, 25, 1750);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m29, 20, 500);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m34, 24, 1700);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m39, 21, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m44, 24, 1450);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co4, @m49, 33, 2450);

-- Commande @co5 (BioMed Afrique) passée il y a 105 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f5, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 105 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 102 DAY));
SET @co5 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m5, 55, 2650);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m10, 24, 2050);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m15, 25, 2950);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m20, 25, 1800);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m25, 25, 3000);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m30, 24, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m35, 20, 1800);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m40, 24, 1200);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m45, 95, 2150);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co5, @m50, 29, 1250);
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m1, @co1, 'L25A-01', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 468 DAY), 30, 30, 1050);
SET @l1 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m6, @co1, 'L25A-06', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 64 DAY), 24, 24, 1400);
SET @l2 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m11, @co1, 'L25A-11', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 523 DAY), 41, 41, 1300);
SET @l3 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m16, @co1, 'L25A-16', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 750 DAY), 25, 25, 3900);
SET @l4 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m21, @co1, 'L25A-21', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 704 DAY), 25, 25, 2300);
SET @l5 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m26, @co1, 'L25A-26', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 741 DAY), 25, 25, 1600);
SET @l6 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m31, @co1, 'L25A-31', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 38 DAY), 24, 24, 1600);
SET @l7 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m36, @co1, 'L25A-36', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 680 DAY), 27, 27, 1850);
SET @l8 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m41, @co1, 'L25A-41', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 12 DAY), 40, 40, 2250);
SET @l9 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m46, @co1, 'L25A-46', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 648 DAY), 118, 118, 2050);
SET @l10 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m2, @co2, 'L25A-02', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 721 DAY), 20, 20, 1250);
SET @l11 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m7, @co2, 'L25A-07', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 698 DAY), 24, 24, 1900);
SET @l12 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m12, @co2, 'L25A-12', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 794 DAY), 52, 52, 1600);
SET @l13 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m17, @co2, 'L25A-17', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 558 DAY), 84, 84, 1750);
SET @l14 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m22, @co2, 'L25A-22', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 699 DAY), 44, 44, 1500);
SET @l15 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m27, @co2, 'L25A-27', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 494 DAY), 25, 25, 2600);
SET @l16 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m32, @co2, 'L25A-32', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 548 DAY), 78, 78, 2350);
SET @l17 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m37, @co2, 'L25A-37', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 300 DAY), 24, 24, 1650);
SET @l18 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m42, @co2, 'L25A-42', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 622 DAY), 58, 58, 1450);
SET @l19 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m47, @co2, 'L25A-47', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 456 DAY), 106, 106, 2100);
SET @l20 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m3, @co3, 'L25A-03', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 475 DAY), 73, 73, 2050);
SET @l21 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m8, @co3, 'L25A-08', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 727 DAY), 25, 25, 2750);
SET @l22 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m13, @co3, 'L25A-13', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 447 DAY), 40, 40, 1250);
SET @l23 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m18, @co3, 'L25A-18', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 742 DAY), 42, 42, 1550);
SET @l24 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m23, @co3, 'L25A-23', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 473 DAY), 25, 25, 2200);
SET @l25 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m28, @co3, 'L25A-28', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 420 DAY), 40, 40, 1500);
SET @l26 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m33, @co3, 'L25A-33', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 681 DAY), 25, 25, 2100);
SET @l27 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m38, @co3, 'L25A-38', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 486 DAY), 24, 24, 2300);
SET @l28 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m43, @co3, 'L25A-43', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 785 DAY), 24, 24, 1000);
SET @l29 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m48, @co3, 'L25A-48', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 500 DAY), 25, 25, 2850);
SET @l30 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m4, @co4, 'L25A-04', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 517 DAY), 161, 161, 4250);
SET @l31 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m9, @co4, 'L25A-09', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 524 DAY), 18, 18, 1300);
SET @l32 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m14, @co4, 'L25A-14', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 456 DAY), 44, 44, 3350);
SET @l33 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m19, @co4, 'L25A-19', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 633 DAY), 55, 55, 2350);
SET @l34 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m24, @co4, 'L25A-24', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 531 DAY), 25, 25, 1750);
SET @l35 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m29, @co4, 'L25A-29', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 601 DAY), 20, 20, 500);
SET @l36 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m34, @co4, 'L25A-34', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 567 DAY), 24, 24, 1700);
SET @l37 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m39, @co4, 'L25A-39', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 687 DAY), 21, 21, 1600);
SET @l38 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m44, @co4, 'L25A-44', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 300 DAY), 24, 24, 1450);
SET @l39 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m49, @co4, 'L25A-49', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 741 DAY), 33, 33, 2450);
SET @l40 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m5, @co5, 'L25A-05', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 596 DAY), 55, 55, 2650);
SET @l41 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m10, @co5, 'L25A-10', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 77 DAY), 24, 24, 2050);
SET @l42 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m15, @co5, 'L25A-15', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 662 DAY), 25, 25, 2950);
SET @l43 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m20, @co5, 'L25A-20', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 607 DAY), 25, 25, 1800);
SET @l44 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m25, @co5, 'L25A-25', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 459 DAY), 25, 25, 3000);
SET @l45 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m30, @co5, 'L25A-30', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 25 DAY), 24, 24, 1300);
SET @l46 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m35, @co5, 'L25A-35', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 488 DAY), 20, 20, 1800);
SET @l47 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m40, @co5, 'L25A-40', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 51 DAY), 24, 24, 1200);
SET @l48 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m45, @co5, 'L25A-45', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 497 DAY), 95, 95, 2150);
SET @l49 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m50, @co5, 'L25A-50', DATE_SUB(CURDATE(), INTERVAL 100 DAY), DATE_ADD(CURDATE(), INTERVAL 578 DAY), 29, 29, 1250);
SET @l50 := LAST_INSERT_ID();

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 86 DAY), '11:16:00'), @p_ca1, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 3, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l12, 1, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l3, 4, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l37, 2, 3000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 86 DAY), '16:13:00'), @p_ca1, @c22, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 1, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 81 DAY), '12:45:00'), @p_ph1, @c15, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 5, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 81 DAY), '14:12:00'), @p_ca2, @c4, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);

-- Ordonnance @o14 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c7, @p_ph1, 'Dr Kouam', 'ONMC-18049', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o14 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o14, @m32, 14, '1 comprimé par jour au repas', 30);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o14, @m46, 60, '1 comprimé matin et soir', 7);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 80 DAY), '09:51:00'), @p_ca1, @c4, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l39, 3, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 3, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 78 DAY), '13:38:00'), @p_ca1, @c8, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 1, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 78 DAY), '16:06:00'), @p_ph1, @c7, @o14, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l17, 14, 3300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l10, 60, 3200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 75 DAY), '10:23:00'), @p_ca1, @c30, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 1, 2800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 74 DAY), '10:40:00'), @p_ph2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l3, 4, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 73 DAY), '18:41:00'), @p_ca2, @c26, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l32, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l46, 1, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 1, 2800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 73 DAY), '19:58:00'), @p_ca2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 5, 2500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 72 DAY), '13:43:00'), @p_ph2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 3, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 1, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 4, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 72 DAY), '08:56:00'), @p_ca1, @c5, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 1, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 71 DAY), '10:41:00'), @p_ph1, @c1, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 5, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 71 DAY), '11:38:00'), @p_ca1, @c7, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l7, 4, 2400);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 2, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 3, 2600);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 69 DAY), '08:25:00'), @p_ph1, @c18, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l12, 4, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 5, 2500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 68 DAY), '15:58:00'), @p_ca2, @c24, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 5, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 3, 700);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 68 DAY), '09:18:00'), @p_ph1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 3, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 67 DAY), '10:28:00'), @p_ph1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 3, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 66 DAY), '11:32:00'), @p_ca2, @c29, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l9, 2, 3500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 3, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l12, 3, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l48, 4, 1900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 63 DAY), '09:56:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 2, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 4, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 2, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 5, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 63 DAY), '14:46:00'), @p_ca2, @c18, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 1, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 60 DAY), '15:41:00'), @p_ca1, @c5, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 4, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 60 DAY), '19:26:00'), @p_ph1, @c21, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 2, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 58 DAY), '18:07:00'), @p_ca2, @c12, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l48, 1, 1900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 5, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l3, 2, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 58 DAY), '09:50:00'), @p_ca1, @c12, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 1, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 3, 2900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 58 DAY), '13:51:00'), @p_ca1, @c14, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 1, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 2, 2800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 57 DAY), '17:37:00'), @p_ca1, @c4, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l29, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 2, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 56 DAY), '09:55:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l28, 1, 3900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 54 DAY), '10:26:00'), @p_ca2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 2, 700);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 1, 1500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 1, 2800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 54 DAY), '16:50:00'), @p_ca2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l3, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 4, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 53 DAY), '18:45:00'), @p_ca1, @c2, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 1, 2800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 52 DAY), '10:53:00'), @p_ca1, @c21, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 3, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 2, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l9, 2, 3500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 52 DAY), '19:19:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l50, 2, 2100);

-- Ordonnance @o6 (full2) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c25, @p_ph2, 'Dr Kouam', 'ONMC-78854', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o6 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o6, @m46, 7, '1 gélule 3 fois par jour', 14);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o6, @m5, 21, '5 ml 3 fois par jour', 5);

-- Ordonnance @o10 (partielle) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c17, @p_ph2, 'Dr Abega', 'ONMC-72580', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o10 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o10, @m17, 21, '2 comprimés par jour', 5);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o10, @m4, 15, '1 comprimé matin et soir', 10);

-- Ordonnance @o18 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c19, @p_ph1, 'Dr Mballa', 'ONMC-96399', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o18 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o18, @m17, 28, '2 comprimés par jour', 7);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o18, @m47, 60, '1 comprimé le soir au coucher', 7);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 51 DAY), '18:45:00'), @p_ph2, @c17, @o10, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l14, 9, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l31, 6, 6500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 51 DAY), '14:57:00'), @p_ph1, @c19, @o18, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l14, 28, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l20, 60, 3100);

-- Commande @co6 (PharmaDistrib) passée il y a 50 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f1, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 47 DAY));
SET @co6 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co6, @m6, 16, 1400);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co6, @m11, 28, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co6, @m31, 16, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co6, @m36, 18, 1850);

-- Commande @co7 (MediSupply) passée il y a 50 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f2, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 47 DAY));
SET @co7 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co7, @m7, 16, 1900);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co7, @m37, 16, 1650);

-- Commande @co8 (SantePlus Grossiste) passée il y a 50 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f3, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 47 DAY));
SET @co8 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co8, @m13, 27, 1250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co8, @m38, 16, 2300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co8, @m43, 16, 1000);

-- Commande @co9 (Oméga Pharma Distribution) passée il y a 50 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f4, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 47 DAY));
SET @co9 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co9, @m9, 12, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co9, @m34, 16, 1700);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co9, @m44, 16, 1450);

-- Commande @co10 (BioMed Afrique) passée il y a 50 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f5, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 47 DAY));
SET @co10 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co10, @m10, 16, 2050);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co10, @m30, 16, 1300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co10, @m40, 16, 1200);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co10, @m50, 20, 1250);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '09:19:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l3, 4, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 50 DAY), '09:44:00'), @p_ph2, @c25, @o6, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l10, 4, 3200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l41, 11, 4200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 49 DAY), '18:39:00'), @p_ph1, @c20, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l28, 2, 3900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 48 DAY), '12:20:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l9, 1, 3500);

-- Ordonnance @o2 (partielle) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c4, @p_ph1, 'Dr Fotso', 'ONMC-65400', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o2 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o2, @m45, 7, '2 comprimés par jour', 7);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o2, @m4, 30, '2 comprimés par jour', 5);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o2, @m42, 21, '1 comprimé matin et soir', 10);

-- Ordonnance @o4 (aucune) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c23, @p_ph1, 'Dr Fotso', 'ONMC-53344', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o4 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o4, @m16, 28, '1 comprimé le soir au coucher', 10);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o4, @m5, 15, '1 application 2 fois par jour', 30);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o4, @m22, 30, '1 gélule 3 fois par jour', 10);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 47 DAY), '11:40:00'), @p_ca2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l37, 1, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l32, 3, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 4, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l12, 1, 3000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 47 DAY), '10:06:00'), @p_ph2, @c28, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 2, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 47 DAY), '10:13:00'), @p_ph1, @c4, @o2, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l49, 2, 3600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l31, 14, 6500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l19, 9, 2600);
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m6, @co6, 'L26B-06', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 415 DAY), 16, 16, 1450);
SET @l51 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m11, @co6, 'L26B-11', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 515 DAY), 28, 28, 1050);
SET @l52 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m7, @co7, 'L26B-07', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 683 DAY), 16, 16, 2000);
SET @l53 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m37, @co7, 'L26B-37', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 388 DAY), 16, 16, 1700);
SET @l54 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m13, @co8, 'L26B-13', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 698 DAY), 27, 27, 1300);
SET @l55 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m38, @co8, 'L26B-38', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 440 DAY), 16, 16, 2700);
SET @l56 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m43, @co8, 'L26B-43', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 486 DAY), 16, 16, 1300);
SET @l57 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m9, @co9, 'L26B-09', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 394 DAY), 12, 12, 1450);
SET @l58 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m34, @co9, 'L26B-34', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 339 DAY), 16, 16, 2150);
SET @l59 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m44, @co9, 'L26B-44', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 496 DAY), 16, 16, 1350);
SET @l60 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m10, @co10, 'L26B-10', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 494 DAY), 16, 16, 1550);
SET @l61 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m30, @co10, 'L26B-30', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 697 DAY), 16, 16, 1200);
SET @l62 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m40, @co10, 'L26B-40', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 580 DAY), 16, 16, 1350);
SET @l63 := LAST_INSERT_ID();
INSERT INTO stock (id_medicament, id_commande, numero_lot, date_reception, date_peremption, quantite_initiale, quantite_restante, prix_achat) VALUES (@m50, @co10, 'L26B-50', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_ADD(CURDATE(), INTERVAL 653 DAY), 20, 20, 1350);
SET @l64 := LAST_INSERT_ID();

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 45 DAY), '08:48:00'), @p_ca1, @c28, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 5, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 2, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 44 DAY), '10:45:00'), @p_ph2, @c25, @o6, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l10, 3, 3200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l41, 10, 4200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '09:20:00'), @p_ph1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 2, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 5, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '17:46:00'), @p_ph1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 3, 700);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '09:20:00'), @p_ca1, @c16, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 3, 2000);
UPDATE vente SET statut = 'annulee' WHERE id_vente = @v;

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '08:29:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l48, 2, 1900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 1, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 1, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '10:55:00'), @p_ca2, @c14, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 1, 1500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 3, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 2, 700);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 42 DAY), '19:07:00'), @p_ph1, @c14, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 3, 2600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 4, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l2, 5, 2500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 41 DAY), '08:30:00'), @p_ca1, @c11, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 4, 700);

-- Ordonnance @o16 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c13, @p_ph1, 'Dr Fotso', 'ONMC-53224', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o16 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o16, @m3, 30, '1 comprimé le soir au coucher', 10);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o16, @m45, 21, '1 gélule 3 fois par jour', 30);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o16, @m22, 21, '1 comprimé matin et soir', 14);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 40 DAY), '18:28:00'), @p_ca1, @c9, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 1, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 40 DAY), '19:40:00'), @p_ca2, @c10, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 3, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 38 DAY), '17:33:00'), @p_ph2, @c22, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 4, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 38 DAY), '11:46:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 38 DAY), '14:35:00'), @p_ca2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 1, 700);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 38 DAY), '13:50:00'), @p_ph1, @c13, @o16, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l21, 30, 3500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l49, 21, 3600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l15, 21, 2700);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 37 DAY), '18:41:00'), @p_ph1, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 2, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 37 DAY), '09:12:00'), @p_ph1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 2, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l59, 4, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l46, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 37 DAY), '10:44:00'), @p_ca2, @c27, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 3, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 3, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 4, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 36 DAY), '08:31:00'), @p_ca1, @c12, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l9, 3, 3500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 2, 2600);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 36 DAY), '17:11:00'), @p_ca2, @c1, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 4, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 3, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 35 DAY), '18:32:00'), @p_ca1, @c6, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 2, 2200);
UPDATE vente SET statut = 'annulee' WHERE id_vente = @v;

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 35 DAY), '12:05:00'), @p_ca1, @c13, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 1, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 2, 2800);

-- Ordonnance @o12 (partielle) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c7, @p_ph2, 'Dr Kouam', 'ONMC-21330', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o12 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o12, @m3, 20, '1 comprimé par jour au repas', 14);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '09:35:00'), @p_ph2, @c9, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l36, 5, 700);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 1, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '16:48:00'), @p_ca1, @c21, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l7, 3, 2400);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 1, 1500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '18:10:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l58, 4, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l53, 4, 3000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '11:04:00'), @p_ph2, @c19, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l11, 2, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l59, 1, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 1, 2800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 2, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '09:58:00'), @p_ph2, @c7, @o12, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l21, 9, 3500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 31 DAY), '17:31:00'), @p_ph1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l48, 3, 1900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 31 DAY), '18:23:00'), @p_ca1, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l53, 1, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 31 DAY), '12:04:00'), @p_ph1, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 2, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 2, 2900);
UPDATE vente SET statut = 'annulee' WHERE id_vente = @v;

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 29 DAY), '10:29:00'), @p_ca2, @c18, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 5, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 2, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 29 DAY), '18:16:00'), @p_ca1, @c17, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l57, 1, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 28 DAY), '17:52:00'), @p_ca1, @c1, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l57, 3, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 28 DAY), '18:38:00'), @p_ca2, @c25, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 3, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 1, 2900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 28 DAY), '18:50:00'), @p_ph1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 2, 2600);

-- Ordonnance @o11 (full2) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c3, @p_ph1, 'Dr Mballa', 'ONMC-10657', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o11 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o11, @m19, 28, '1 comprimé par jour au repas', 10);

-- Ordonnance @o13 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c26, @p_ph2, 'Dr Fotso', 'ONMC-88942', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o13 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o13, @m4, 14, '2 comprimés par jour', 14);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o13, @m5, 7, '1 application 2 fois par jour', 5);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 25 DAY), '18:06:00'), @p_ca1, @c20, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 4, 2600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l48, 2, 1900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 25 DAY), '14:02:00'), @p_ph1, @c3, @o11, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l34, 14, 3800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 24 DAY), '14:33:00'), @p_ca1, @c28, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l8, 3, 2900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 24 DAY), '10:19:00'), @p_ca2, @c18, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 2, 2600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l57, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l58, 1, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 24 DAY), '14:24:00'), @p_ca2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l7, 4, 2400);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 24 DAY), '14:18:00'), @p_ca2, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l58, 5, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 23 DAY), '14:09:00'), @p_ph2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 2, 2300);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 23 DAY), '17:03:00'), @p_ca2, @c3, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 4, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 23 DAY), '08:21:00'), @p_ph2, @c26, @o13, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l31, 14, 6500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l41, 7, 4200);

-- Ordonnance @o1 (full2) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c28, @p_ph2, 'Dr Ngassa', 'ONMC-36457', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o1 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o1, @m45, 30, '5 ml 3 fois par jour', 14);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o1, @m32, 28, '1 comprimé matin et soir', 10);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '16:36:00'), @p_ph2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l59, 4, 3000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '11:46:00'), @p_ph2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 4, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '10:37:00'), @p_ca1, @c3, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 1, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l38, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 5, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '18:00:00'), @p_ph1, @c3, @o11, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l34, 14, 3800);

-- Commande @co13 (Oméga Pharma Distribution) passée il y a 20 jours : ANNULÉE
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f4, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '10:15:00'), DATE_SUB(CURDATE(), INTERVAL 17 DAY));
SET @co13 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co13, @m38, 40, 2300);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co13, @m2, 30, 1250);
UPDATE commande SET statut = 'annulee' WHERE id_commande = @co13;

-- Ordonnance @o19 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c17, @p_ph1, 'Dr Fotso', 'ONMC-71220', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o19 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o19, @m14, 14, '1 comprimé matin et soir', 10);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o19, @m42, 14, '2 comprimés par jour', 7);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '12:55:00'), @p_ph2, @c28, @o1, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l49, 15, 3600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l17, 14, 3300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 19 DAY), '08:56:00'), @p_ph2, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l47, 1, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 5, 1500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 19 DAY), '08:03:00'), @p_ph1, @c17, @o19, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l33, 14, 4800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l19, 14, 2600);

-- Ordonnance @o3 (full2) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c6, @p_ph1, 'Dr Kouam', 'ONMC-94233', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o3 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o3, @m4, 60, '2 comprimés par jour', 10);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 17 DAY), '15:11:00'), @p_ph1, @c6, @o3, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l31, 30, 6500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 15 DAY), '19:07:00'), @p_ca1, @c20, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 4, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 13 DAY), '09:12:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l58, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l53, 1, 3000);

-- Ordonnance @o8 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c20, @p_ph1, 'Dr Ngassa', 'ONMC-62936', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o8 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o8, @m18, 20, '2 comprimés par jour', 5);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o8, @m49, 14, '2 comprimés par jour', 5);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 12 DAY), '16:45:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l46, 4, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l2, 1, 2500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 12 DAY), '08:56:00'), @p_ph1, @c20, @o8, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l24, 20, 2500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l40, 14, 3400);

-- Ordonnance @o7 (partielle) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c30, @p_ph2, 'Dr Fotso', 'ONMC-84153', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o7 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o7, @m17, 21, '1 comprimé par jour au repas', 10);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o7, @m20, 20, '1 comprimé matin et soir', 10);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 11 DAY), '14:36:00'), @p_ph1, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 2, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 11 DAY), '13:55:00'), @p_ca1, @c20, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 4, 1500);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l42, 2, 2800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l18, 3, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 11 DAY), '15:56:00'), @p_ph2, @c28, @o1, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l49, 15, 3600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l17, 14, 3300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '10:33:00'), @p_ph2, @c30, @o7, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l14, 9, 2900);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l44, 9, 3200);

-- Ordonnance @o15 (aucune) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c5, @p_ph1, 'Dr Abega', 'ONMC-87906', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o15 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o15, @m21, 60, '1 comprimé le soir au coucher', 5);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 9 DAY), '17:18:00'), @p_ph1, @c6, @o3, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l31, 30, 6500);

-- Ordonnance @o9 (full1) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c19, @p_ph1, 'Dr Mballa', 'ONMC-68154', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o9 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o9, @m42, 7, '1 comprimé matin et soir', 14);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o9, @m14, 7, '1 comprimé le soir au coucher', 5);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '09:41:00'), @p_ca2, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l57, 5, 1800);
UPDATE vente SET statut = 'annulee' WHERE id_vente = @v;

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '11:11:00'), @p_ca1, @c16, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 5, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l58, 1, 2200);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l32, 4, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '14:51:00'), @p_ph1, @c26, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l64, 2, 2100);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l32, 3, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '19:34:00'), @p_ca2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 2, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '17:38:00'), @p_ph1, @c19, @o9, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l19, 7, 2600);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l33, 7, 4800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 7 DAY), '18:42:00'), @p_ca1, @c28, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l13, 2, 2300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 6 DAY), '16:19:00'), @p_ca2, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l46, 1, 2100);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 6 DAY), '14:09:00'), @p_ca2, @c15, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l53, 5, 3000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '08:13:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 2, 2600);

-- Ordonnance @o5 (aucune) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c14, @p_ph1, 'Dr Kouam', 'ONMC-69593', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o5 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o5, @m15, 30, '1 comprimé par jour au repas', 7);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o5, @m5, 15, '1 gélule 3 fois par jour', 30);

-- Ordonnance @o17 (aucune) : créée aujourd'hui puis antidatée en fin de script
INSERT INTO ordonnance (id_client, id_personnel, nom_medecin, numero_ordre_medecin, date_prescription, date_validite) VALUES (@c4, @p_ph1, 'Dr Kouam', 'ONMC-99607', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));
SET @o17 := LAST_INSERT_ID();
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o17, @m32, 15, '1 gélule 3 fois par jour', 30);
INSERT INTO ligne_ordonnance (id_ordonnance, id_medicament, quantite_prescrite, posologie, duree_traitement_jours) VALUES (@o17, @m24, 10, '1 comprimé par jour au repas', 10);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '14:16:00'), @p_ca1, @c24, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l9, 5, 3500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '19:48:00'), @p_ph2, @c22, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 5, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '17:08:00'), @p_ca1, @c9, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l53, 2, 3000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 5, 2000);

-- Commande @co11 (MediSupply) passée il y a 3 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f2, @p_ph2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '10:15:00'), DATE_ADD(CURDATE(), INTERVAL 3 DAY));
SET @co11 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co11, @m2, 60, 1250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co11, @m29, 60, 500);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co11, @m39, 60, 1600);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co11, @m35, 60, 1800);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '11:09:00'), @p_ca1, @c11, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l23, 3, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l55, 1, 2000);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '14:39:00'), @p_ca1, @c20, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l52, 1, 1800);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l56, 4, 3900);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '11:48:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 5, 1500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '19:10:00'), @p_ca1, @c14, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l55, 1, 2000);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l1, 2, 1500);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '16:07:00'), @p_ca1, NULL, NULL, 'mobile_money');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l60, 4, 2200);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '19:36:00'), @p_ca1, NULL, NULL, 'especes');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l7, 3, 2400);
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l26, 1, 2600);

-- Commande @co12 (BioMed Afrique) passée il y a 1 jours
INSERT INTO commande (id_fournisseur, id_personnel, date_commande, date_livraison_prevue) VALUES (@f5, @p_ph1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '10:15:00'), DATE_ADD(CURDATE(), INTERVAL 5 DAY));
SET @co12 := LAST_INSERT_ID();
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co12, @m50, 60, 1250);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co12, @m36, 60, 1850);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co12, @m1, 60, 1050);
INSERT INTO ligne_commande (id_commande, id_medicament, quantite_commandee, prix_achat_prevu) VALUES (@co12, @m9, 60, 1300);

INSERT INTO vente (date_vente, id_personnel, id_client, id_ordonnance, mode_paiement) VALUES (TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:45:00'), @p_ph2, NULL, NULL, 'carte');
SET @v := LAST_INSERT_ID();
INSERT INTO ligne_vente (id_vente, id_stock, quantite, prix_unitaire) VALUES (@v, @l60, 2, 2200);

-- ---------------------------------------------------------------------
-- 6. Antidatage des ordonnances (créées aujourd'hui pour passer les contrôles, puis ramenées à leur vraie date)
-- ---------------------------------------------------------------------
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 21 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 21 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '09:00:00') WHERE id_ordonnance = @o1;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 47 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 47 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 47 DAY), '09:00:00') WHERE id_ordonnance = @o2;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 17 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 17 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 17 DAY), '09:00:00') WHERE id_ordonnance = @o3;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 47 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 47 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 47 DAY), '09:00:00') WHERE id_ordonnance = @o4;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 4 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 4 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '09:00:00') WHERE id_ordonnance = @o5;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 51 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 51 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 51 DAY), '09:00:00') WHERE id_ordonnance = @o6;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 11 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 11 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 11 DAY), '09:00:00') WHERE id_ordonnance = @o7;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 12 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 12 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 12 DAY), '09:00:00') WHERE id_ordonnance = @o8;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 8 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 8 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 8 DAY), '09:00:00') WHERE id_ordonnance = @o9;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 51 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 51 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 51 DAY), '09:00:00') WHERE id_ordonnance = @o10;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 25 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 25 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 25 DAY), '09:00:00') WHERE id_ordonnance = @o11;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 33 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 33 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 33 DAY), '09:00:00') WHERE id_ordonnance = @o12;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 25 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 25 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 25 DAY), '09:00:00') WHERE id_ordonnance = @o13;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 80 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 80 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 80 DAY), '09:00:00') WHERE id_ordonnance = @o14;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 9 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 9 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 9 DAY), '09:00:00') WHERE id_ordonnance = @o15;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 40 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 40 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 40 DAY), '09:00:00') WHERE id_ordonnance = @o16;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 4 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 4 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '09:00:00') WHERE id_ordonnance = @o17;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 51 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 51 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 51 DAY), '09:00:00') WHERE id_ordonnance = @o18;
UPDATE ordonnance SET date_prescription = DATE_SUB(CURDATE(), INTERVAL 20 DAY), date_validite = DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 20 DAY), INTERVAL 14 DAY), date_enregistrement = TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '09:00:00') WHERE id_ordonnance = @o19;

-- ---------------------------------------------------------------------
-- 7. Lots périmés et proches de la péremption (alertes du tableau de bord)
-- ---------------------------------------------------------------------
-- L25A-06 : péremption dans 64 jours (inséré tel quel)
-- L25A-10 : péremption dans 77 jours (inséré tel quel)
-- L25A-30 : péremption dans 25 jours (inséré tel quel)
-- L25A-31 : péremption dans 38 jours (inséré tel quel)
UPDATE stock SET date_peremption = DATE_SUB(CURDATE(), INTERVAL 9 DAY), statut = 'perime' WHERE id_stock = @l18;
-- L25A-40 : péremption dans 51 jours (inséré tel quel)
-- L25A-41 : péremption dans 12 jours (inséré tel quel)
UPDATE stock SET date_peremption = DATE_SUB(CURDATE(), INTERVAL 9 DAY), statut = 'perime' WHERE id_stock = @l39;

-- ---------------------------------------------------------------------
-- 8. Mise à jour des statuts (ordonnances expirées, lots périmés) puis validation
-- ---------------------------------------------------------------------
CALL sp_maintenance_quotidienne();
COMMIT;

-- Vérifications (valeurs attendues en commentaire)
SELECT COUNT(*) AS medicaments FROM medicament;   -- 50
SELECT COUNT(*) AS clients FROM client;           -- 30
SELECT COUNT(*) AS fournisseurs FROM fournisseur; -- 5
SELECT COUNT(*) AS personnel FROM personnel;      -- 5
SELECT COUNT(*) AS ordonnances FROM ordonnance;   -- 20
SELECT COUNT(*) AS ventes FROM vente;             -- 126
SELECT statut, COUNT(*) AS nb FROM ordonnance GROUP BY statut;
SELECT statut, COUNT(*) AS nb FROM commande GROUP BY statut;
SELECT statut, COUNT(*) AS nb FROM stock GROUP BY statut;
SELECT * FROM v_alertes_rupture;
SELECT * FROM v_alertes_peremption ORDER BY date_peremption;
