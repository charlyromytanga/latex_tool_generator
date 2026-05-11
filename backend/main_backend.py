
import os
import sys
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Starting backend application...")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel
from markupsafe import Markup

from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications


# ---------------------------------------------------------------------------
# Vues Admin enrichies — une par table
# ---------------------------------------------------------------------------

def _truncate(max_len: int = 120):
    """Formateur qui tronque le texte long dans la liste Admin."""
    def _fmt(view, context, model, name):
        val = getattr(model, name, "") or ""
        return Markup(f'<span title="{val}">{val[:max_len]}{"…" if len(val) > max_len else ""}</span>')
    return _fmt


class CVBaseAdmin(ModelView):
    column_list              = [
        "id", "language", "target_titles",
        "header", "summary", "skills",
        "experience", "education", "certifications",
        "projects", "languages", "interests",
    ]
    column_searchable_list   = ["id", "language", "target_titles"]
    column_filters           = ["language"]
    column_labels            = {
        "id":            "Identifiant",
        "language":      "Langue",
        "target_titles": "Postes visés",
        "header":        "En-tête",
        "summary":       "Résumé",
        "skills":        "Compétences",
        "experience":    "Expérience",
        "education":     "Formation",
        "certifications":"Certifications",
        "projects":      "Projets",
        "languages":     "Langues",
        "interests":     "Centres d'intérêt",
        "target_titles": "Postes visés",
    }
    column_formatters        = {
        "target_titles":  _truncate(60),
        "header":         _truncate(60),
        "summary":        _truncate(60),
        "skills":         _truncate(60),
        "experience":     _truncate(60),
        "education":      _truncate(60),
        "certifications": _truncate(60),
        "projects":       _truncate(60),
        "languages":      _truncate(60),
        "interests":      _truncate(60),
        "target_titles":  _truncate(60),
    }
    form_columns             = [
        "id", "language", "header", "summary", "skills",
        "experience", "education", "certifications",
        "projects", "languages", "interests", "target_titles",
    ]
    can_create   = True
    can_edit     = True
    can_delete   = True
    can_export   = True
    page_size    = 20


class JobsAdmin(ModelView):
    column_list              = ["id", "language", "country", "city", "company_name", "company_type", "offer_description", "company_presentation", "job_title"]
    column_searchable_list   = ["id", "company_name", "city", "country"]
    column_filters           = ["language", "country", "company_type"]
    column_labels            = {
        "id":                   "Identifiant offre",
        "language":             "Langue",
        "country":              "Pays",
        "city":                 "Ville",
        "company_name":         "Entreprise",
        "company_type":         "Type d'entreprise",
        "offer_description":    "Description de l'offre",
        "company_presentation": "Présentation entreprise",
        "job_title":            "Intitulé du poste",
    }
    column_formatters        = {
        "offer_description":    _truncate(100),
        "company_presentation": _truncate(100),
    }
    form_columns             = [
        "id", "language", "country", "city",
        "company_name", "company_type",
        "offer_description", "company_presentation", "job_title",
    ]
    can_create   = True
    can_edit     = True
    can_delete   = True
    can_export   = True
    page_size    = 20


class CVApplicationsAdmin(ModelView):
    column_list              = ["id", "language", "header", "summary", "skills", "experience", "education", "certifications", "projects", "languages", "interests", "job_id", "cv_id", "matching_score", "generation_date"]
    column_searchable_list   = ["id", "cv_id", "job_id"]
    column_filters           = ["language", "matching_score", "generation_date"]
    column_labels            = {
        "id":               "Identifiant",
        "language":         "Langue",
        "header":           "En-tête",
        "summary":          "Résumé",
        "skills":           "Compétences",
        "experience":       "Expérience",
        "education":        "Formation",
        "certifications":   "Certifications",
        "projects":        "Projets",
        "languages":       "Langues",
        "interests":       "Centres d'intérêt",
        "job_id":          "Offre (id)",
        "cv_id":           "CV base (id)",
        "matching_score":   "Score matching",
        "generation_date":  "Date génération",
    }
    form_columns             = [
        "id", "language", "header", "summary", "skills", "experience", "education",
        "certifications", "projects", "languages", "interests", "job_id", "cv_id",
        "matching_score", "generation_date",
    ]
    can_create   = True
    can_edit     = True
    can_delete   = True
    can_export   = True
    page_size    = 20


class ApplicationsAdmin(ModelView):
    column_list              = ["id", "job_id", "cv_id", "lm", "matching_score", "generation_date", "mail_content", "days_to_wait", "response_email"]
    column_searchable_list   = ["id", "cv_id", "job_id", "response_email"]
    column_filters           = ["matching_score", "generation_date", "days_to_wait"]
    column_labels            = {
        "id":               "Identifiant",
        "cv_id":            "CV base (id)",
        "job_id":           "Offre (id)",
        "lm":               "Lettre de motivation",
        "matching_score":   "Score matching",
        "generation_date":  "Date génération",
        "mail_content":     "Contenu email",
        "days_to_wait":     "Jours d'attente",
        "response_email":   "Email de réponse",
    }
    column_formatters        = {
        "id":           _truncate(20),
        "cv_id":        _truncate(20),
        "job_id":       _truncate(20),
        "lm":           _truncate(100),
        "matching_score": lambda v, c, m, n: f"{getattr(m, n):.2f}",
        "generation_date": lambda v, c, m, n: getattr(m, n).strftime("%Y-%m-%d %H:%M") if getattr(m, n) else "",
        "mail_content": _truncate(100),
        "days_to_wait": lambda v, c, m, n: str(getattr(m, n)) + " j",
        "response_email": _truncate(100),
    }
    form_columns             = [
        "id", "cv_id", "job_id", "lm",
        "matching_score", "generation_date",
        "mail_content", "days_to_wait", "response_email",
    ]
    can_create   = True
    can_edit     = True
    can_delete   = True
    can_export   = True
    page_size    = 20


# ---------------------------------------------------------------------------
# Registre des services — ajouter ici chaque nouveau service
# ---------------------------------------------------------------------------
_SERVICE_REGISTRY = [
    {
        "name":        "cv",
        "import":      "services.cv.routes",
        "blueprint":   "cv_blueprint",
        "prefix":      "/cv",
        "admin_models": [
            (CVBase,          CVBaseAdmin),
            (Jobs,            JobsAdmin),
            (CVApplications,  CVApplicationsAdmin),
            (Applications,    ApplicationsAdmin),
        ],
    },
    # {"name": "reports", "import": "services.reports.routes", "blueprint": "reports_blueprint", "prefix": "/reports", "admin_models": []},
    # {"name": "lm",      "import": "services.lm.routes",      "blueprint": "lm_blueprint",      "prefix": "/lm",      "admin_models": []},
    # {"name": "emails",  "import": "services.emails.routes",  "blueprint": "emails_blueprint",  "prefix": "/emails",  "admin_models": []},
]

_registered_services: list[str] = []
_failed_services:     list[dict] = []


def _create_app() -> Flask:
    app = Flask(__name__)

    db_url = os.environ.get("DATABASE_URL", "sqlite:////app/db/jobcv.db")
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        db_path = os.path.abspath(db_url[len("sqlite:///"):])
        db_url = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY non défini dans les variables d'environnement !")
    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    Babel(app)
    db.init_app(app)

    if db_url.startswith("sqlite:////"):
        db_dir = os.path.dirname(db_url[len("sqlite:///"):])
        os.makedirs(db_dir, exist_ok=True)

    with app.app_context():
        db.create_all()

    return app


def _register_services(app: Flask) -> None:
    admin = Admin(app, name="JobCV Admin")

    for svc in _SERVICE_REGISTRY:
        try:
            module = __import__(svc["import"], fromlist=[svc["blueprint"]])
            blueprint = getattr(module, svc["blueprint"])
            app.register_blueprint(blueprint, url_prefix=svc["prefix"])
            for model, view_class in svc.get("admin_models", []):
                admin.add_view(view_class(model, db.session))
            _registered_services.append(svc["name"])
            logging.info("Service enregistré : %s → %s", svc["name"], svc["prefix"])
        except Exception as exc:
            logging.error("Échec enregistrement service '%s' : %s", svc["name"], exc)
            _failed_services.append({"service": svc["name"], "error": str(exc)})


def _register_core_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return jsonify({
            "status":   "ok",
            "app":      "latex-tool-generator backend",
            "services": _registered_services,
        })

    @app.route("/health")
    def health():
        ok = not _failed_services
        return jsonify({
            "status":   "healthy" if ok else "degraded",
            "services": {
                "registered": _registered_services,
                "failed":     _failed_services,
            },
        }), 200 if ok else 207


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
try:
    logging.info("DATABASE_URL: %s", os.environ.get("DATABASE_URL"))
    app = _create_app()
    _register_services(app)
    _register_core_routes(app)
except Exception as e:
    logging.error("Erreur fatale lors du démarrage : %s", str(e))
    traceback.print_exc()
    sys.exit(1)


if __name__ == "__main__":
    app.run(debug=True)
