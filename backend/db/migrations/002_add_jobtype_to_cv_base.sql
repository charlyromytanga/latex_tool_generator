-- Migration 002: ajoute la colonne jobtype dans cv_base
-- Permet de stocker le titre de poste propre à chaque cv_base
-- sans dépendre du dict _DEFAULT_PERSONAL hardcodé dans cv_utils.py.

ALTER TABLE cv_base ADD COLUMN jobtype TEXT;
