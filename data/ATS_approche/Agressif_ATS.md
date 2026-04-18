
# 🔴 2. Stratégie ATS “agressifs” (type Taleo / iCIMS / BrassRing / SuccessFactors)

👉 Ici, c’est différent :

⚠️ Ton CV doit passer un **filtrage machine AVANT humain**

---

## 🎯 Objectif

Maximiser :

* matching mots-clés
* score ATS
* détectabilité

---

## ⚙️ Pipeline à implémenter (version “hardcore”)

### 1. Extraction agressive des mots-clés

Ton parser doit sortir :

```json
{
  "hard_skills": ["C++", "Python", "SQL"],
  "domain": ["Commodities", "Derivatives", "Risk"],
  "tools": ["Excel", "VBA"],
  "verbs": ["developed", "implemented", "analyzed"]
}
```

---

### 2. Génération CV “ATS-optimized”

👉 Template spécifique (DIFFÉRENT du précédent)

Règles strictes :

* 1 colonne
* zéro design
* sections standards

---

### 3. Injection stratégique des mots-clés

Ton algo doit :

👉 Forcer la présence des mots-clés critiques :

Ex :

```
Skills:
- Python, C++, SQL
- Financial derivatives pricing
- Risk management (VaR)
```

👉 ET dans les expériences :

```
Developed C++ tools for derivatives pricing and risk analysis
```

---

### 4. Scoring interne (gros différenciateur 🔥)

Ajoute dans ton repo :

```python
def ats_score(cv, job_offer):
    return overlap(cv.keywords, job_offer.keywords)
```

👉 Tu peux aller plus loin :

* TF-IDF
* cosine similarity

👉 Objectif :

> Ne JAMAIS envoyer un CV < 70% match

---

### 5. Génération multi-versions automatique

Pour UNE offre → génère :

* CV version A (tech heavy)
* CV version B (risk heavy)

---

## 🚀 Bonus ultra stratégique

Ajoute :

* duplication des mots-clés dans :

  * Skills
  * Experience
  * Summary

👉 Oui, c’est volontairement redondant (ATS-friendly)

---

## 🧠 Stratégie globale

👉 Ici tu joues :

> “machine first, humain après”

---

# ⚔️ Différence clé entre les 2 approches

| Aspect     | ATS souple     | ATS agressif         |
| ---------- | -------------- | -------------------- |
| Priorité   | Humain         | Machine              |
| CV         | Naturel        | Optimisé mots-clés   |
| Formulaire | Très important | Secondaire           |
| Parsing    | Approx         | Strict               |
| Stratégie  | Cohérence      | Saturation mots-clés |

---

# 🔥 3. Ce que TU peux faire (niveau avancé)

Ton repo peut devenir :

👉 un **“ATS-aware CV generator”**

Ajoute :

```bash
--mode=workday
--mode=taleo
```

Et adapte automatiquement :

* template
* wording
* densité mots-clés



