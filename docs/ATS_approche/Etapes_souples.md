Parfait — là on va passer en **mode “agent exécutable”** :
je te donne **2 plans d’étapes structurés**, que tu peux directement donner à un agent (Copilot / Cursor / autre) pour qu’il code dans ton repo.

👉 Chaque plan = **séquence technique + fichiers à modifier + snippets attendus**

---

# 🟢 PLAN 1 — ATS SOUPLES (Workday / SmartRecruiters)

## 🎯 Objectif agent

Créer un pipeline :

> CV lisible + JSON de remplissage formulaire + cohérence globale

---

## 🧩 ÉTAPE 1 — Étendre le parsing d’offre

📁 `src/cvrepo/job_parser.py`

👉 Instruction agent :

* Ajouter une fonction `extract_structured_fields()`

```python
def extract_structured_fields(raw_offer: dict) -> dict:
    return {
        "hard_skills": raw_offer.get("skills", []),
        "soft_skills": raw_offer.get("soft_skills", []),
        "missions": raw_offer.get("missions", []),
        "keywords": raw_offer.get("keywords", [])
    }
```

👉 Puis intégrer dans pipeline existant

---

## 🧩 ÉTAPE 2 — Générer un “Form Filling Pack”

📁 `src/cvrepo/pipeline.py`

👉 Instruction agent :
Créer une fonction :

```python
def build_form_pack(profile, offer):
    return {
        "personal_info": profile["identity"],
        "experiences": profile["experiences"],
        "education": profile["education"],
        "skills": offer["hard_skills"],
        "answers": {
            "motivation": generate_motivation(profile, offer),
            "why_company": generate_why_company(offer)
        }
    }
```

👉 Sauvegarder dans :
📁 `runs/form_packs/{offer_id}.json`

---

## 🧩 ÉTAPE 3 — Adapter le template LaTeX (human-friendly)

📁 `templates/cv/en/main.tex` + `fr/main.tex`

👉 Instruction agent :

* Créer une variante :

```
main_workday.tex
```

👉 Modifier `template_engine.py` :

```python
def select_template(mode: str):
    if mode == "workday":
        return "main_workday.tex"
```

---

## 🧩 ÉTAPE 4 — Générer résumé automatique

📁 `src/cvrepo/template_engine.py`

👉 Ajouter :

```python
def generate_summary(profile, offer):
    return f"{profile['title']} with experience in {', '.join(offer['hard_skills'][:3])}"
```

👉 Injecter dans section “presentation”

---

## 🧩 ÉTAPE 5 — CLI mode workday

📁 `src/cvrepo/cli.py`

👉 Ajouter option :

```bash
cvrepo generate --mode workday --offer <path>
```

👉 Pipeline :

```python
if args.mode == "workday":
    template = select_template("workday")
    form_pack = build_form_pack(profile, offer)
```

---

## 🧩 ÉTAPE 6 — API endpoint

📁 `src/api/_routes/route_generate.py`

👉 Ajouter :

```python
@app.post("/generate/workday")
def generate_workday(payload):
    return run_pipeline(mode="workday", payload=payload)
```

---

## 🚀 OUTPUT attendu

* CV PDF (lisible humain)
* JSON formulaire prêt à copier
* cohérence parfaite

---
