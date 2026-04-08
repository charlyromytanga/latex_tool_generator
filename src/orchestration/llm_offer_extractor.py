import openai
import os
import json
import re

def extract_offer_fields_with_openai(markdown_content: str) -> dict:
    """Extrait les champs d'une offre markdown via l'API OpenAI."""
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY non défini dans l'environnement.")

    prompt = ('''
        Tu es un assistant qui extrait des informations structurées à partir d’offres d’emploi en markdown, même si la structure varie.
        Pour chaque offre, retourne un JSON avec les clés suivantes :
        - title
        - company_name
        - location
        - country
        - tier (si non précisé, mets "tier-2")
        - description (si possible)
        - responsibilities (liste)
        - skills (liste)
        - qualifications (liste)
        - benefits (liste)

        Exemple 1 :
        ---
        # Finance Data Analyst - N H/F
        OVHCloud

        Paris - 75
        CDI

        Bac +5
        Secteur informatique • ESN

        ## Détail du poste
        Vous rejoignez l'équipe Data Business Analyse de l'équipe Finance dont l'objectif est fournir des insights et des recommandations basées sur des analyses de données approfondies.

        ## Vos principales missions
        Mission 1 : Analyse de données
        - Travailler en étroite collaboration avec les équipes finance pour identifier les besoins
        - Décrire avec précision les processus métiers finance
        - Générer les modèles de données métier et applicative, et s'assurer de leur cohésion
        - Collecter, modéliser, analyser et interpréter les données métier
        - Elaborer et maintenir des jeux de données et des tableaux de bord de qualité
        - S'assurer que les plans de tests soient bien définis et appliqués
        - Valoriser les données via des solutions de visualisation
        - Simplifier, automatiser et industrialiser les processus data existant sans valeur ajoutée
        - Gérer le transfert des produits finis et stables aux services techniques

        Mission 2 : Gestion de la qualité de la donnée
        - Effectuer des contrôles qualité sur les données métier
        - Identifier les critères de contrôle des données métier, et aider à l'implémentation

        ## Compétences requises
        - Maîtrise du Français courant (langue natale ou C2)
        - Bonne maîtrise de l'anglais (niveau B2 minimum)
        - Excellente maitrise des langages SQL et Python, Spark
        - Excellente maitrise des solutions DataIku, PySpark et BI Tableau Software
        - Maitrise des environnements de travail Confluence, Jira
        - Maitrise de la suite Office
        - Compétence rédactionnelle
        - Capacité à analyser et investiguer des uses cases fonctionnelles complexes
        - Positivité et résilience face aux problématiques data complexes
        - Esprit d'équipe, intelligence émotionnelle pour embarquer les collaborateurs
        ---

        Exemple 2 :
        ---
        # Data Analyst Expert - Chef de Projet Bi Assurances H/F
        MACSF

        Puteaux - 92
        CDI
        Télétravail partiel
        Bac +5
        Banque • Assurance • Finance
        Exp. 2 ans min.

        ## Les missions du poste
        Vous recherchez un poste où l'analyse opérationnelle, le Business Intelligence et le pilotage de projet se réunissent ?

        ## Votre rôle
        En tant que Data Analyst Expert / Chef de projet BI Assurances, vous serez à la fois :
        - expert(e) data (Power BI, Python, Qualité de données)
        - coordinateur(trice) entre métiers, MOA et IT
        - référent(e) métier capable de comprendre les processus et d'accompagner les utilisateurs

        ## Vos missions
        1) Reporting & Datavisualisation - Power BI
        - Participer à la migration des reportings BO vers Power BI.
        - Concevoir des dashboards Power BI ergonomiques, performants et orientés décision.
        - Optimiser les modèles de données et les performances (DAX, relations...).
        - Assurer la gouvernance : mise à jour, sécurisation, documentation et bonnes pratiques.

        2) Analyses avancées & Exploration (Python / SQL)
        - Explorer les données pour identifier comportements, tendances et anomalies.
        - Produire des analyses descriptives ou avancées en Python (pandas, numpy, etc.) ou via SQL.
        - Identifier les leviers d'optimisation et les insights stratégiques.
        - Automatiser des analyses, contrôles ou scripts de data quality via Python

        3) Participation aux projets Data & MOA
        - Contribuer à la recette fonctionnelle et au contrôle qualité des données après évolutions MOA.
        - Collaborer étroitement avec les équipes IT & Data.
        - Aider à structurer les processus data (documentation, normalisation, bonnes pratiques)
        - Participer à la mise en place ou amélioration des architectures data

        ## Profil recherché
        - Titulaire d'une formation supérieure (Bac +5 ou équivalent)
        - Expert Power BI
        - Plus de 3 ans d'expérience en développement Python
        - Compétences analytiques et de synthèse
        - Proactivité pour challenger la cohérence de la donnée
        - Bonne communication avec les parties prenantes
        - Bonne compréhension des modèles de données
        ---

        Exemple 3 :
        ---
        # FinTech Data Engineer 16998
        Veritaz AB

        Sverige (Sweden)
        CDI

        Publiée le 31 mars 2026

        ## Assignment Description
        We are looking for a Data Engineer

        ## What You Will Work On
        - Design and develop robust ELT data pipelines
        - Build and maintain data models using dbt and Snowflake
        - Implement data validation, reconciliation, and quality frameworks
        - Translate financial business logic into data transformations and controls
        - Develop incremental models and snapshot handling (SCD)
        - Ensure data lineage, dependencies, and pipeline stability
        - Integrate validation into orchestration and transformation workflows
        - Work with observability and testing frameworks for data pipelines
        - Collaborate with business stakeholders to ensure accurate financial reporting
        - Use Git-based workflows and CI/CD pipelines for development
        - Leverage AI-assisted development tools to improve productivity

        ## What You Bring
        - Strong experience with Snowflake and dbt
        - Advanced SQL skills (complex joins, aggregations, diff strategies)
        - Experience building ELT pipelines and data transformation workflows
        - Hands-on experience with data validation and reconciliation frameworks
        - Strong understanding of data lineage and pipeline dependencies
        - Experience with Git-based development and CI/CD pipelines
        - Experience with data observability and testing practices
        - Familiarity with AI-assisted development tools (e.g., Cursor or similar)
        - Ability to translate business logic into scalable data solutions
        - Strong collaboration skills across technical and business teams
        ---

        Exemple 4 :
        ---
        # Data & Analytics - Starting in September 2026
        Deloitte Belgium

        Zaventem, Vlaams-Brabant (Belgium)
        CDI

        Publiée le 1 avril 2026

        ## Description of the position
        In Data & Analytics, you'll develop your industry knowledge working for a wide range of clients on extracting valuable information from data, solving technical problems, advising organisations on how to be more data-driven, or helping them reach their business performance goals.

        ## Let's talk about you
        We are seeking highly motivated and analytical Bachelor and Master graduates to join one of our teams in the Data & Analytics field of interest.

        You are fluent in Dutch/French and English.
        ---

        Exemple 5 :
        ---
        # Data Analyst
        Novo Nordisk

        Denmark (Denmark)
        CDI

        Publiée le 6 avril 2026

        ## Your new role
        In this role, you will work hands-on with data to design, build and maintain analytics solutions that support daily operations. You will partner closely with end users to understand needs, test solutions and continuously refine your work.

        ## Your main responsibilities will include
        - Building and maintaining data pipelines that ensure reliable data flows
        - Developing intuitive Power BI dashboards and impactful visual reporting
        - Working with SQL to extract, structure and analyse data
        - Contributing to Power Platform solutions, Python scripts and data-modelling activities
        - Conducting user interviews, running tests and iteratively improving solutions

        ## Your skills and qualifications
        - Relevant bachelor's or master's degree in data analytics, data science or a similar field
        - Hands-on experience developing insightful dashboards using Power BI or similar visualisation tools
        - Solid experience working with SQL, turning raw data into clear, actionable insights
        - Strong proficiency in spoken and written English, enabling effective collaboration with global stakeholders
        - Experience or curiosity around Python for data analysis, modelling.
        - Experience testing PoCs and deploying solutions from protypes to production.
        - Experience with Git versioning and agile ways of working.
        ---

        Exemple 6 :
        ---
        # Statisticien Modélisateur - Risque de crédit H/F
        Crédit Mutuel Arkéa

        Le Relecq-Kerhuon (France)
        CDI

        Publiée le 27 mars 2026

        ## Description du poste
        Le Département "Modèles & Pilotage" rattaché à la Direction Risque de Crédit et de Contrepartie du Crédit Mutuel Arkéa prend en charge la réalisation des modèles statistiques, le calcul des provisions et le pilotage du risque de crédit afin de faciliter la prise de décision.

        ## Activités et responsabilités du poste
        - Modéliser et backtester les modèles de cotations de risque de crédit des clients en déterminant les méthodologies adaptées
        - Réaliser des études statistiques sur le profil de risque des clients et mettre en place des indicateurs de suivi du risque utilisé dans le pilotage du Groupe
        - Piloter les échanges avec les divers intervenants sur le SNI et présenter les résultats des travaux de modélisation aux groupes de travail internes ou confédéraux
        - Contribuer, en lien avec les équipes MOA et informatiques, à la maintenance du SNI sur la partie cotation
        - Assurer une veille technologique sur les méthodes de modélisation

        ## Profil recherché
        - Formation type école d'ingénieur ou cursus universitaire (Bac +5 avec une spécialité en Statistiques, Économétrie et/ou Mathématiques Appliquées)
        - Expérience préalable en modélisation, statistiques ou data science (2-3 ans minimum)
        - Maîtrise des logiciels destinés aux statistiques (R ou python)
        - Connaissance de requête d'appel de données via SQL
        - À l'aise avec les techniques statistiques, leurs outils ainsi qu'avec l'utilisation de la suite google
        ---

        Exemple 7 :
        ---
        # Data Ingénieur- Services Financiers-Strasbourg
        Sopra Steria

        15A Av. de l'Europe, 67300 Strasbourg (France)
        CDI

        Publiée le 10 mars 2026

        ## Description du poste
        Sopra Steria accompagne la transformation Data de ses clients du secteur financier de bout en bout.

        ## Votre rôle et vos missions
        - Interaction avec le métier pour collecter leurs besoins d'analyse
        - Collecte des données pertinentes pour la réalisation des analyses
        - Vérification de la qualité des données et mise en œuvre d'actions de remédiation si nécessaire
        - Transformation et analyses multidimensionnelle des données
        - Construction de tableaux de bord permettant de visualiser les données
        - Identification d'insights et interprétation avec le métier

        ## Qualifications
        - Diplômé(e) d'une Ecole d'Ingénieurs ou équivalent Universitaire en Informatique
        - Première expérience avérée en data analyse et/ou engineering
        - Connaissance large en modélisation et en consultation des bases de données (relationnel, NoSQL, orientées colonnes/documents/graphes, multi dimensionnelle)
        - Connaissance des outils d'alimentation des données (ETL, ELT)
        - Connaissance des outils de visualisation des données (tabulaire/graphique, statique/dynamique)
        - Connaissance des langages SQL, Python ou R
        - Connaissance des principes d'optimisation des performances (dénormalisation, hiérarchisation, indexation) en fonction des usages
        ---

        Exemple 8 :
        ---
        # ANALYSTES DATA SCIENCE ET STATISTIQUES - H/F
        Banque de France

        75009 Paris (France)
        CDI

        Publiée le 7 avril 2026

        ## Présentation de la direction générale et du service
        La Banque de France recherche des analystes data science et statistiques (h/f) pour renforcer ses équipes.

        ## Descriptif de mission
        - Analyser et porter un regard critique sur les dispositifs adoptés par les banques françaises pour se conformer aux exigences réglementaires en matière de modélisation du risque de crédit (modèles IRB, IFRS)
        - Apprécier la performance statistique des modèles proposés et la qualité des données qu'il utilisent
        - Participer à des missions d'enquête sur place dans les établissements de crédit
        - Être en contact permanent avec le management des établissements vérifiés

        ## Profil recherché
        - Diplômé d'une école d'ingénieur ou d'études supérieures scientifiques
        - Première expérience dans le secteur bancaire au travers de stages
        - Maîtrise de l'anglais - oral et écrit
        ---

        Maintenant, extrais les informations pour ce markdown :
        ---
    ''') + markdown_content + '\n---\n'

    from pathlib import Path
    debug_log = Path("runs/openai_debug.log")
    debug_log.parent.mkdir(parents=True, exist_ok=True)
    # Log d'entrée dans la fonction
    with debug_log.open("a", encoding="utf-8") as f:
        f.write(f"[TRACE] Appel extract_offer_fields_with_openai, OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}\n{'-'*80}\n")
    try:
        # Log après création du client OpenAI
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        with debug_log.open("a", encoding="utf-8") as f:
            f.write(f"[TRACE] Client OpenAI instancié\n{'-'*80}\n")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant d'extraction d'offres d'emploi."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )
        # Extraction du JSON de la réponse
        content = response.choices[0].message.content
        with debug_log.open("a", encoding="utf-8") as f:
            f.write(f"[DEBUG] Réponse OpenAI brute :\n{content}\n{'-'*80}\n")
        print("[DEBUG] Réponse OpenAI brute :\n", content)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Aucun JSON trouvé dans la réponse OpenAI :\n" + content)
    except Exception as e:
        with debug_log.open("a", encoding="utf-8") as f:
            f.write(f"[ERROR] Exception lors de l'appel OpenAI : {e}\n{'-'*80}\n")
        raise RuntimeError(f"Erreur lors de l'extraction de l'offre avec OpenAI : {e}")
