# *-- UTF-8 --* 

# =======IMPORTS========
import os
import json
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple



# ========IMPORTS CLASSES========
from ..utils.cv_pipeline import CV

# Load environment variables from .env file
load_dotenv()

# ========CONFIG LOGGING========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========CHEMINS RESSOURCES========
DATA_DIR = str(os.getenv('DATA_DIR'))
OFFERS_DIR = str(os.getenv('OFFERS_DIR'))
FORMATIONS_DIR = str(os.getenv('FORMATIONS_DIR'))
EXPERIENCES_DIR = str(os.getenv('EXPERIENCES_DIR'))
PROJECTS_DIR = str(os.getenv('PROJECTS_DIR'))


# ==========INSTANCES========
cv = CV(data_dir=DATA_DIR)

# ========PIPELINE OFFER - CV PROCESS======
formations, experiences, projects = cv.load_alls()

cv_base_in_all_fr, cv_base_in_all_en = cv.cv_base_in_all()

logger.info(f'--- Formations chargées ({len(formations)}) ---')
for f in formations:
    logger.info(f)
    logger.info('---')

logger.info(f'--- Expériences chargées ({len(experiences)}) ---') 
for e in experiences :
    logger.info(e)
    logger.info('---')

logger.info(f'--- Projets chargés ({len(projects)}) ---')
for p in projects:
    logger.info(p)
    logger.info('---')


logger.info(f'--- CV Base In Alls FR ---')
logger.info(cv_base_in_all_fr)
logger.info(f'--- CV Base In Alls EN ---')
logger.info(cv_base_in_all_en)