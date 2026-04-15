from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def index():
    """Render landing page with resume upload form."""
    return render_template("index.html")
