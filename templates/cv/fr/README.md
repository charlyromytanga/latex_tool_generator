# Template modulaire FR — comment l'utiliser

Fichiers ajoutés :

- `main.tex` : template principal qui inclut les sections.
- `sections/` : dossier contenant les fichiers modifiables pour chaque section (entête, présentation, expériences, certifications, compétences, formation).
- `variants/` : variantes historiques de CV FR conservées comme sources secondaires.

Personnalisation rapide :

1. Ouvrez `main.tex` et éditez les commandes en tête : `\cvname`, `\cvaddress`, `\cvmail`, `\cvphone`, `\cvlinkedin`, `\cvgithub`, `\jobtype`, `\presentation`.
2. Modifiez le contenu des fichiers dans `sections/` pour adapter vos expériences, certifications, etc.
3. Compilation et génération PDF dans `runs/render` :

Utilisez le Makefile ou la CLI pour générer le PDF :

```bash
make generate OFFER=data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md DOC_LANG=fr
# ou
uv run cvrepo render runs/tmp/summaries/offer_20260219_quant_dev_junior_summary.json --template fr
```

Le rendu génère un PDF dans `runs/render`.

Astuce : si vous produisez souvent des CVs avec seuls certains champs qui changent, conservez une copie du `main.tex` et remplacez seulement les commandes en tête.
