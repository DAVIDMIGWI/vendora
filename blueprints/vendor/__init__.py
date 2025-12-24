from flask import Blueprint

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

from . import routes

