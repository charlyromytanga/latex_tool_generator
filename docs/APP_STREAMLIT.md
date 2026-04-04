# Streamlit App Specification

## Vue d'ensemble

Interface utilisateur intuitive pour orchestrer le pipeline complet offre → CV/LM.

**Localisation:** `src/app/streamlit_app.py`

**Déploiement:** Local (`streamlit run src/app/streamlit_app.py`) ou via Render

---

## Layout & Sections

### 1. Sidebar - Navigation

```
┌─────────────────────────────┐
│ 🎯 Recruitment Assistant    │
├─────────────────────────────┤
│ 📋 Upload Offre             │ ← Active par défaut
│ 🔍 Analyse                  │
│ 🎯 Matching                 │
│ 📄 Génération               │
│ 📥 Preview                  │
│ 📤 Export                   │
│ ⚙️  Settings                │
└─────────────────────────────┘
```

### 2. Onglet 1: Upload Offre

**Composants:**

1. **Input:** Drag-drop ou Paste Markdown
   - Accept: .md ou text paste
   - Max size: 10MB

2. **Validation visuelle:**
   - ✅ Titre détecté
   - ✅ Entreprise détectée
   - ✅ Tier détecté
   - ❌ Compétences manquantes → Warning

3. **Boutons:**
   - **[Valider & Analyser]** → POST `/api/offers`
   - **[Annuler]** → Reset

4. **Metadata:**
   - Source file name
   - Ingestion date (auto-filled)

**État après submit:**
- Spinner avec "Ingestion en cours..."
- Resultat: `offer_id` + sections détectées
- Transition auto vers onglet "Analyse"

---

### 3. Onglet 2: Analyse Offre

**Affichage:**

1. **Card: Offre Résumée**
   ```
   Offre #20260405-xyz123
   ┌────────────────────────┐
   │ Titre: Senior Dev      │
   │ Entreprise: Acme Corp  │
   │ Localisation: Paris, FR│
   │ Tier: Tier-2           │
   └────────────────────────┘
   ```

2. **Sections Détectées:**
   - Texte brut Markdown affichable
   - Onglets: Description | Responsabilités | Compétences | Qualifs

3. **Keywords Extraits (LLM Model 1):**
   - Tableau: Technical | Soft Skills | Domain | Seniority
   - Badges colorés (ex. `#Python` `#Leadership`)

4. **Actions:**
   - **[Passer au Matching]** → Onglet 3

---

### 4. Onglet 3: Matching (Level 2)

**Affichage:**

1. **Score Global Confiance:**
   ```
   ████████░░ 78% - Recommandé ✅
   ```
   - Color-coded: Rouge < 50% | Orange 50-75% | Vert >= 75%
   - Seuil configurable dans Settings

2. **Top Experiences Matching:**
   ```
   Rang | Entreprise | Rôle | Score | Keywords Matchés | Explication
   ─────┼────────────┼──────┼───────┼──────────────────┼──────────────
    1   | OldCorp    | Lead | 0.85  | Python, FastAPI  | 6/7 match
    2   | StartupXYZ | Dev  | 0.72  | Python           | 3/5 match
    3   | ...        | ...  | ...   | ...              | ...
   ```
   - Tri par score DESC
   - Filtres: Par entreprise, par rôle
   - Expand row pour voir details complètes

3. **Top Projects Matching:**
   ```
   Rang | Projet | Languages | Score | Explication
   ─────┼────────┼───────────┼───────┼──────────────
    1   | my-api | Python    | 0.72  | FastAPI expertise
    2   | ...    | ...       | ...   | ...
   ```

4. **Contrôles:**
   - **Slider:** Threshold minimum (0.0 - 1.0)
   - **Checkbox:** "Use auto-selected matches" (default: ON)
   - **Bouton:** "[Voir plus de détails]" → Drawer sidebar pour chaque match

5. **Actions:**
   - **[Valider & Générer]** → POST `/api/generate/cv_letter`
   - **[Réviser manuellemnt]** → Modal pour custom select experiences/projects
   - **[Retour]** → Onglet 2

---

### 5. Onglet 4: Génération (Level 3)

**Processus:**

1. **Spinner:** "Génération en cours... 🔄"
   - Polling: GET `/api/generate/{generation_id}` toutes les 2s
   - Progress bar

2. **Résumé Génération:**
   ```
   Generation ID: gen-20260405-abc789
   Offre: Acme Corp - Senior Dev
   Langue: FR
   Status: ✅ Succès
   Durée: 12s
   ```

3. **Artifacts:**
   - CV: 245 KB PDF ✅
   - Lettre de Motivation: 178 KB PDF ✅

4. **Actions:**
   - **[Preview]** → Onglet 5
   - **[Télécharger CV]** → Download PDF
   - **[Télécharger LM]** → Download PDF
   - **[Retour]** → Onglet 2 (reload offres disponibles)

---

### 6. Onglet 5: Preview

**Affichage:**

1. **Tabs: CV | Lettre de Motivation**

2. **Pour chaque tab:**
   - **PDF Viewer:** Rendu interactif (zoom, scroll)
   - **Page Counter:** "Page 1/3"
   - **Zoom Controls:** + / - buttons ou slider

3. **Annotations (optionnel):**
   - Highlight matching keywords
   - Sidebar: "Keywords détectés dans le CV"

4. **Actions:**
   - **[Éditer Texte]** → Modal: Edit LaTeX source (avancé)
   - **[Nouvelle Génération]** → Retour Onglet 4 avec modif custom
   - **[Valider & Exporter]** → Onglet 6

---

### 7. Onglet 6: Export & Submit

**Options:**

1. **Export Local:**
   - **[Télécharger CV]**
   - **[Télécharger LM]**
   - Format: PDF (défaut) + LaTeX source (option)

2. **Candidature Directe (si integration active):**
   - Checkbox: "Je veux candidater immédiatement"
   - Selection: Platform (LinkedIn, etc.)
   - Paste offer URL
   - **[Soumettre]** → POST `/api/integrate/submit`

3. **Archivage:**
   - Auto-archive en `runs/run_cv/{year}/{month}/tier-{n}/{country}/{company}/`
   - Affichage chemin archive

4. **Résumé:**
   ```
   ✅ Candidature complète:
   - CV + LM générés et archivés
   - Offer link: recruitment_assistant.db → offer_id
   - Archive path: runs/run_cv/2026/04/tier-2/france/acme_corp/
   - Ready pour soumission
   ```

---

### 8. Settings (Sidebar)

**Configurable:**

- **Seuil confiance (matching):** Slider (0.0 - 1.0)
- **Langue par défaut:** Radio (FR | EN)
- **Auto-archive:** Toggle
- **LLM Config:** (Input fields pour API key, model, etc.)
- **DB Path:** Text input (default: `db/recruitment_assistant.db`)

---

## État & Persistence

**Session State (Streamlit):**
```python
st.session_state.current_offer_id
st.session_state.matching_results
st.session_state.generation_id
st.session_state.theme (light/dark)
```

**Persistence:**
- Offer ID + matching results: Sauvegardés en DB, chargés via API
- UI state: Session-only (reset au refresh)

---

## Design & Framework

**Framework:** Streamlit + (optionnel) Streamlit Components

**CSS:** Custom CSS via `st.markdown` + Streamlit themes

**Colors:**
- Primary: Bleu professionnel (#0066CC)
- Success: Vert (#00AA00)
- Warning: Orange (#FF9900)
- Error: Rouge (#CC0000)

**Typo:**
- Heading 1-3: Espacées, bold
- Body: Lisible, max 70ch ligne
- Code: Monospace gris (#333)

**Responsive:** Streamlit gère auto (Desktop + Tablet)

---

## Dépendances

```python
streamlit>=1.28.0
streamlit-pdf-viewer  # Ou équivalent pour viewer PDF
requests>=2.31.0
pandas>=2.0.0
pydantic>=2.0.0
```

---

## Exemple de layout en code Streamlit

```python
# src/app/streamlit_app.py

import streamlit as st
from pages import upload, analysis, matching, generation, preview, export

st.set_page_config(page_title="Recruitment Assistant", layout="wide")

# Sidebar navigation
with st.sidebar:
    st.title("🎯 Recruitment Assistant")
    page = st.radio("Navigation", [
        "📋 Upload Offre",
        "🔍 Analyse",
        "🎯 Matching",
        "📄 Génération",
        "📥 Preview",
        "📤 Export",
        "⚙️  Settings"
    ])

# Render pages
if page == "📋 Upload Offre":
    upload.render()
elif page == "🔍 Analyse":
    analysis.render()
# ... etc
```
