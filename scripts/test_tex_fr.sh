# Candidature ADD UP — tous les items (comportement par défaut)
python backend/services/cv/core/cv_business.py --mode cv-fr \
  --cv-base-id cv_base_in_all_fr --job-id offer-711607447 --db-path backend/db/jobcv.db

# Candidature ADD UP — sélection modulable (5 projets, 3 expériences spécifiques)
python backend/services/cv/core/cv_business.py --mode cv-fr \
  --cv-base-id cv_base_in_all_fr --job-id offer-711607447 --db-path backend/db/jobcv.db \
  --max-projects 5 --project-indices 0 1 3 6 8 \
  --max-experiences 3 --experience-indices 0 1 2 \
  --max-competences 2 \
  --max-competences-techniques 3 --competence-technique-indices 0 1 2

# Candidature spontanée → Trading Analyst (titre index 1, sélection projets)
python backend/services/cv/core/cv_business.py --mode cv-fr \
  --cv-base-id cv_base_in_all_fr --job-id offer-xxx --db-path backend/db/jobcv.db \
  --target-title-index 1 \
  --max-projects 4 --project-indices 2 4 5 7