from flask import Blueprint
cv_blueprint = Blueprint('cv', __name__)

@cv_blueprint.route('/cv', methods=['GET'])
def get_cv():
    # Logic to retrieve and return the CV data
    return "CV data goes here"