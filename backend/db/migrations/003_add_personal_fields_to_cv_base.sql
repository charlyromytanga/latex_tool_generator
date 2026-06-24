-- Migration 003: ajoute github et disponibilite dans cv_base
-- Permet de stocker les infos personnelles propres à chaque candidat
-- sans dépendre du dict _DEFAULT_PERSONAL hardcodé dans cv_utils.py.

ALTER TABLE cv_base ADD COLUMN github TEXT;
ALTER TABLE cv_base ADD COLUMN disponibilite TEXT;
