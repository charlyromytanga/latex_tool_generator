# Structure de rangement des offres

La structure canonique est maintenant : **Année -> Trimestre -> Tier -> Pays -> Ville -> Entreprise**.

## Racine canonique

- `2026/Q1/tier-1/` : priorités absolues
- `2026/Q1/tier-2/` : seconde vague
- `2026/Q1/tier-3/` : long terme
- `_templates/` : modèles de fiche offre et de métadonnées

## Convention de fichiers

Dans chaque dossier entreprise :
- `role_slug.md`
- `role_slug.metadata.json`
- `offer_YYYYMMDD_<role>.md` reste accepté pendant la migration

## Exemple cible

- `2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md`
- `2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.metadata.json`

## Process recommandé

1. Copier `_templates/offer_template.md` dans le dossier entreprise ciblé.
2. Copier `offer_metadata_template.json` et le compléter.
3. Lancer `uv run cvrepo analyze ...` pour produire le résumé JSON/LaTeX.
4. Lancer `uv run cvrepo render ...` pour produire le PDF.
5. Lancer `uv run cvrepo index-archive` pour reconstruire l'index des artefacts.
