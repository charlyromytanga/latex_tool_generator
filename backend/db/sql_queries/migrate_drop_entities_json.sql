-- Migration pour supprimer la colonne entities_json de la table offers sans perte de données
-- Sauvegarde, copie, suppression, renommage, et restauration des index

-- 1. Sauvegarde de la table originale (optionnel, sécurité)
CREATE TABLE IF NOT EXISTS offers_backup AS SELECT * FROM offers;

-- 2. Création de la nouvelle table sans la colonne entities_json
CREATE TABLE offers_new AS
  SELECT offer_id, offer_text, metadata_json, keywords_json, created_at, company, location, title
  FROM offers;

-- 3. Suppression de l'ancienne table
DROP TABLE offers;

-- 4. Renommage de la nouvelle table
ALTER TABLE offers_new RENAME TO offers;

-- 5. Restauration de l'index sur created_at (si existant)
CREATE INDEX IF NOT EXISTS idx_offers_created_at ON offers(created_at);

-- 6. (Optionnel) Vérification du résultat
-- SELECT * FROM offers LIMIT 5;

-- Pour annuler en cas de problème :
-- DROP TABLE offers;
-- ALTER TABLE offers_backup RENAME TO offers;
-- (et restaurer les index si besoin)
