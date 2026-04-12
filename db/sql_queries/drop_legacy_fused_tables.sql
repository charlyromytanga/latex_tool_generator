-- Script de nettoyage des anciennes tables fusionnées
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS offers_raw;
DROP TABLE IF EXISTS offer_keywords;
DROP TABLE IF EXISTS formation_matching_scores;
-- Si l'ancienne table matching_scores existe avec l'ancien schéma, la supprimer aussi :
-- DROP TABLE IF EXISTS matching_scores;

PRAGMA foreign_keys = ON;
