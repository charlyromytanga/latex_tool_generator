
import os
import sys
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Starting backend application...")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()  

from flask import Flask
from flask_appbuilder import AppBuilder
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel


from services.cv.routes import cv_blueprint
# from services.reports.routes import reports_blueprint
# from services.lm.routes import lm_blueprint
# from services.emails.routes import emails_blueprint

from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications


try:
    logging.info("DATABASE_URL: %s", os.environ.get('DATABASE_URL'))
    #logging.info("Toutes les variables d'envirionnement : %s", dict(os.environ))
    app = Flask(__name__)
    db_url = os.environ.get('DATABASE_URL', 'sqlite:////app/db/jobcv.db')
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        db_path = os.path.abspath(db_url[len('sqlite:///'):])
        db_url = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY non défini dans les variables d\'environnement !')
    app.config['SECRET_KEY'] = secret_key

    babel = Babel(app)
    db.init_app(app)
except Exception as e:
    logging.error("Erreur lors de la configuration de l'application : %s", str(e))
    traceback.print_exc()
    sys.exit(1)

admin = Admin(app, name='JobCV Admin', translations_path=None)
admin.add_view(ModelView(CVBase, db.session))
admin.add_view(ModelView(Jobs, db.session))
admin.add_view(ModelView(CVApplications, db.session))
admin.add_view(ModelView(Applications, db.session))


app.register_blueprint(cv_blueprint, url_prefix='/cv')
# app.register_blueprint(reports_blueprint, url_prefix='/reports')
# app.register_blueprint(lm_blueprint, url_prefix='/lm')
# app.register_blueprint(emails_blueprint, url_prefix='/emails')

db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if db_uri.startswith('sqlite:////'):
    db_dir = os.path.dirname(db_uri[len('sqlite:///'):])
    os.makedirs(db_dir, exist_ok=True)

with app.app_context():
    db.create_all()



@app.route("/")
def index():
    return "Backend API OK"

    
if __name__ == '__main__':
    app.run(debug=True)