# Architecture

Le dépôt implémente une plateforme de **génération intelligente de documents de candidature** (CV, lettres) autour d'une architecture en **3 niveaux d'orchestration** et d'une **base de données SQLite centralisée**.

Voir [ARCHITECTURE_COMPLETE.md](ARCHITECTURE_COMPLETE.md) pour la spécification complète de la V2.

---

## Structure des répertoires

| Dossier | Rôle |
|---------|------|
| `src/cvrepo/` | CLI et pipeline de génération LaTeX existant |
| `src/orchestration/` | Orchestrateurs de données candidat + pipeline offres |
| `templates/` | Templates LaTeX (CV, lettres, formations) |
| `data/` | Offres brutes, données candidat, schémas JSON |
| `db/` | Base SQLite + migrations |
| `runs/` | Sorties runtime, archives, index, fichiers temporaires |
| `docs/` | Documentation architecture, workflows, CLI |

---

## Pipeline existant (`cvrepo`)

1. Une offre brute est stockée dans `data/offers/…`.
2. `cvrepo generate` analyse l'offre et écrit un résumé normalisé sous `runs/tmp/summaries/`.
3. La même commande rend le CV et la lettre depuis les templates canoniques.
4. Les PDF générés arrivent dans `runs/render/`.
5. Avec `--archive`, les PDF sont copiés dans `runs/archive/` et `runs/archive/index.jsonl` est mis à jour.

---

## Orchestrateurs de données candidat (implémentés)

Dispatcher : `python main.py --target <cible>`

| Cible | Module | État | Données |
|-------|--------|------|--------|
| `my_projects` | `src/orchestration/projects_orchestrator.py` | ✅ Validé | 1 projet en DB |
| `my_experiences` | `src/orchestration/experiences_orchestrator.py` | ✅ Validé | 8 expériences en DB |
| `formations_template` | `src/orchestration/formations_orchestrator.py` | ✅ Validé | 4 formations en DB + LaTeX |

---

## Base de données SQLite

**Localisation :** `db/recruitment_assistant.db`  
**Initialisation :** `scripts/init_db.sh` ou `db/schema_init.sql`  
**Migration :** `db/migrations/001_initial_schema.sql` (schéma complet, 9 tables)

| Table | Rôle |
|-------|------|
| `offers_raw` | Offres brutes + sections parsées |
| `offer_keywords` | Keywords extraits par LLM |
| `my_experiences` | Expériences personnelles |
| `my_projects` | Projets Git personnels |
| `formations` | Formations académiques (avec `course_categories_json`) |
| `matching_scores` | Résultats matching LLM (offres vs expériences/projets) |
| `formation_matching_scores` | Matching LLM formations vs offres |
| `generations` | Traces artefacts générés |
| `archive_manifest` | Manifest des archives |

---

## Niveaux d'orchestration (feuille de route)

| Niveau | Rôle | Module | État |
|--------|------|--------|------|
| Niveau 1 | Ingestion offres + stockage DB | `src/orchestration/ingest.py` | 🔲 À implémenter |
| Niveau 2 | Extraction LLM + matching offres/profil | `src/orchestration/llm_extractors.py` | 🔲 À implémenter |
| Niveau 3 | Génération multi-canaux (CV, lettres…) | `src/cvrepo/` + `src/channels/` | 🔲 À enrichir |
