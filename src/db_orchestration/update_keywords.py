

import os
import sys
import json
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from sqlalchemy import create_engine, text
from api._run.engine_offer import extract_keywords

# Configuration du logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Adapter ce chemin à ta config si besoin
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'db' / 'recruitment_assistant.db'}"

def update_keywords_for_all_offers():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Récupérer toutes les offres
        result = conn.execute(text("SELECT offer_id, offer_text, keywords_json FROM offers"))
        offers = result.fetchall()
        updated = 0
        for offer in offers:
            offer_id = offer[0]
            offer_text = offer[1]
            keywords_json = offer[2]
            if not keywords_json or keywords_json.strip() in ("", "[]", "null", "None"):
                keywords = extract_keywords(offer_text, top_k=500)
                logging.debug(f"Offre {offer_id} - keywords extraits : {keywords[:10]} ... total={len(keywords)}")
                conn.execute(
                    text("UPDATE offers SET keywords_json = :keywords_json WHERE offer_id = :offer_id"),
                    {"keywords_json": json.dumps(keywords, ensure_ascii=True), "offer_id": offer_id}
                )
                logging.info(f"[OK] Offre {offer_id} mise à jour avec {len(keywords)} mots-clés.")
                updated += 1
            else:
                logging.info(f"[SKIP] Offre {offer_id} déjà renseignée.")
        logging.info(f"Mises à jour terminées. {updated} offres corrigées.")

if __name__ == "__main__":
    update_keywords_for_all_offers()
