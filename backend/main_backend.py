import os
from flask import Flask
from flask_appbuilder import AppBuilder
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


from services.cv.routes import cv_blueprint
from services.reports.routes import reports_blueprint
from services.lm.routes import lm_blueprint
from services.emails.routes import emails_blueprint

from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/jobcv.db'
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY non défini dans les variables d\'environnement !')
app.config['SECRET_KEY'] = secret_key


admin = Admin(app, name='JobCV Admin')
admin.add_view(ModelView(CVBase, db.session))
admin.add_view(ModelView(Jobs, db.session))
admin.add_view(ModelView(CVApplications, db.session))
admin.add_view(ModelView(Applications, db.session))


app.register_blueprint(cv_blueprint, url_prefix='/cv')
app.register_blueprint(reports_blueprint, url_prefix='/reports')
app.register_blueprint(lm_blueprint, url_prefix='/lm')
app.register_blueprint(emails_blueprint, url_prefix='/emails')

if __name__ == '__main__':
    app.run(debug=True)