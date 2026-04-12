"""Offer-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict, Any
import json
import uuid
import datetime
import numpy as np
import os
from dotenv import load_dotenv


import spacy
from typing import Dict, Any, List, Optional
from transformers import pipeline
from keybert import KeyBERT
from langdetect import detect
from typing import List, Tuple, Union, Optional
import os
from dotenv import load_dotenv

load_dotenv()




class OfferCreateRequest(BaseModel):
    """Payload minimal pour POST /api/offers."""
    offer_input: str = Field(min_length=1, description="L'offre")
    company: str = Field(min_length=1, description="L'entreprise")
    offer_title: str = Field(min_length=1, description="Le titre de l'offre")
    location: str = Field(min_length=1, description="Le lieu de travail")

class OfferDetailsResponse(BaseModel):
    offer_id: str = Field(description="Identifiant de l'offre")
    keywords: object =  Field(description="Mots-clés extraits de l'offre")



