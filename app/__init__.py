from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
	app = Flask(
		__name__,
		template_folder="templates",
		static_folder="static"
	)

	app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
	app.config["MAX_CONTENT_LENGTH"] = (
		int(os.getenv("MAX_FILE_SIZE_MB", 5)) * 1024 * 1024
	)
	app.config["UPLOAD_FOLDER"] = os.path.join(
		os.path.dirname(__file__), "static", "uploads"
	)

	os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

	from app.routes.main import main_bp
	app.register_blueprint(main_bp)

	# MongoDB hook - future
	# from app.models.db import init_db
	# init_db(app)

	return app
