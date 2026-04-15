
# 🔴 PLAN 2 — ATS AGRESSIFS (Taleo / iCIMS / BrassRing / SuccessFactors)

## 🎯 Objectif agent

Créer un pipeline :

> scoring + injection mots-clés + CV optimisé machine

---

## 🧩 ÉTAPE 1 — Keyword extractor avancé

📁 `src/db_orchestration/update_keywords.py`

👉 Instruction agent :
Créer :

```python
def extract_keywords_advanced(offer_text: str):
    import re
    words = re.findall(r"\b[A-Za-z\+\#]+\b", offer_text)
    return list(set(words))
```

---

## 🧩 ÉTAPE 2 — Structuration keywords

📁 `job_parser.py`

```python
def categorize_keywords(keywords):
    return {
        "tech": [k for k in keywords if k in ["Python", "C++", "SQL"]],
        "finance": [k for k in keywords if k in ["Derivatives", "Risk", "VaR"]],
    }
```

---

## 🧩 ÉTAPE 3 — ATS scoring engine

📁 `src/cvrepo/pipeline.py`

👉 Ajouter :

```python
def compute_ats_score(cv_keywords, job_keywords):
    overlap = set(cv_keywords) & set(job_keywords)
    return len(overlap) / len(job_keywords)
```

---

## 🧩 ÉTAPE 4 — Injection mots-clés dans CV

📁 `template_engine.py`

👉 Ajouter :

```python
def inject_keywords(section_text, keywords):
    for kw in keywords:
        if kw not in section_text:
            section_text += f", {kw}"
    return section_text
```

---

## 🧩 ÉTAPE 5 — Template ATS strict

📁 `templates/cv/en/main_ats.tex`

👉 Contraintes :

* 1 colonne
* sections standard
* pas d’images

👉 Modifier selector :

```python
if mode == "ats":
    return "main_ats.tex"
```

---

## 🧩 ÉTAPE 6 — Multi-version CV

📁 `pipeline.py`

```python
def generate_variants(profile, offer):
    return [
        generate_cv(profile, offer, focus="tech"),
        generate_cv(profile, offer, focus="risk")
    ]
```

---

## 🧩 ÉTAPE 7 — Seuil de validation

```python
if ats_score < 0.7:
    raise ValueError("CV not optimized for ATS")
```

---

## 🧩 ÉTAPE 8 — CLI mode ats

```bash
cvrepo generate --mode ats --offer <path>
```

---

## 🧩 ÉTAPE 9 — API endpoint

```python
@app.post("/generate/ats")
def generate_ats(payload):
    return run_pipeline(mode="ats", payload=payload)
```

---

## 🚀 OUTPUT attendu

* CV ultra optimisé ATS
* score calculé
* variantes générées

---

# ⚔️ BONUS — UNIFICATION INTELLIGENTE

👉 Ajoute un mode global :

```bash
cvrepo generate --mode auto
```

👉 Logique :

```python
if company in ["BNP", "SG"]:
    mode = "workday"
elif company in ["Goldman", "MS"]:
    mode = "ats"
```

---

# 🔥 CE QUE TU ES EN TRAIN DE CONSTRUIRE

Très concrètement :

👉 Un **ATS-aware CV compiler**

C’est exactement le type de projet qui :

* impressionne en entretien quant/dev
* montre **engineering + compréhension business**

---

# 🎯 Prochaine étape (si tu veux)

Je peux te faire :

👉 un **design d’algorithme de matching type quant (cosine similarity + weighting finance)**
👉 ou un **schéma d’architecture propre pour scaler ton API**

Et là tu passes clairement niveau “top candidat CIB”.
