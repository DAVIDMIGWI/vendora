from flask import Blueprint

buyer_bp = Blueprint('buyer', __name__, url_prefix='/buyer')

from . import routes

