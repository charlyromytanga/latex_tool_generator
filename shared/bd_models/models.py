from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey

db = SQLAlchemy()

class CVBase(db.Model):
    __tablename__ = 'cv_base'
    id = db.Column(db.String, primary_key=True)
    language = db.Column(db.String, nullable=False)
    header = db.Column(db.String)
    summary = db.Column(db.String)
    skills = db.Column(db.String)
    experience = db.Column(db.String)
    education = db.Column(db.String)
    technical = db.Column(db.String)
    certifications = db.Column(db.String)
    projects = db.Column(db.String)
    languages = db.Column(db.String)
    interests = db.Column(db.String)
    target_titles = db.Column(db.String)

class Jobs(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.String, primary_key=True)
    language = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String)
    company_name = db.Column(db.String)
    company_type = db.Column(db.String)
    offer_description = db.Column(db.String)
    company_presentation = db.Column(db.String)
    job_title = db.Column(db.String)

class CVApplications(db.Model):
    __tablename__ = 'cv_applications'
    id = db.Column(db.String, primary_key=True)
    language = db.Column(db.String, nullable=False)
    header = db.Column(db.String)
    summary = db.Column(db.String)
    skills = db.Column(db.String)
    experience = db.Column(db.String)
    technical = db.Column(db.String)
    education = db.Column(db.String)
    certifications = db.Column(db.String)
    projects = db.Column(db.String)
    languages = db.Column(db.String)
    interests = db.Column(db.String)
    job_id = db.Column('job_offer_id', db.String, db.ForeignKey('jobs.id'), nullable=False)
    cv_id = db.Column('cv_base_id', db.String, db.ForeignKey('cv_base.id'), nullable=False)
    matching_score = db.Column(db.Float)
    generation_date = db.Column(db.DateTime)

class Applications(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.String, primary_key=True)
    job_id = db.Column('job_offer_id', db.String, db.ForeignKey('jobs.id'), nullable=False)
    cv_id = db.Column('cv_base_id', db.String, db.ForeignKey('cv_base.id'), nullable=False)
    lm = db.Column(db.String)
    matching_score = db.Column(db.Float)
    generation_date = db.Column(db.DateTime)
    mail_content = db.Column(db.String)
    days_to_wait = db.Column(db.Integer)
    response_email = db.Column(db.String)

