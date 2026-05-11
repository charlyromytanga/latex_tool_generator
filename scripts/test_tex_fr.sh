python backend/services/cv/core/cv_business.py --mode cv-fr --cv-base-id cv_base_in_all_fr --job-id offer-711607447 --db-path backend/db/jobcv.db 
# Candidature ADD UP avec titre de l'offre (auto)
python -m backend.services.cv.core.cv_business --mode cv-fr \
  --cv-base-id cv_base_in_all_fr --job-id offer-711607447

# Candidature spontanée → Trading Analyst
python -m backend.services.cv.core.cv_business --mode cv-fr \
  --cv-base-id cv_base_in_all_fr --job-id offer-xxx --target-title-index 1