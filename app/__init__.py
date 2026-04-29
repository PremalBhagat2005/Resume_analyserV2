from flask import Flask
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()


def create_app():
	app = Flask(
		__name__,
		template_folder="templates",
		static_folder="static"
	)

	app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
	try:
		max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
	except ValueError:
		max_file_size_mb = 5
	app.config["MAX_CONTENT_LENGTH"] = max_file_size_mb * 1024 * 1024

	default_upload_folder = os.path.join(
		tempfile.gettempdir(), "resume_analyser_uploads"
	) if os.getenv("VERCEL") else os.path.join(
		os.path.dirname(__file__), "static", "uploads"
	)
	app.config["UPLOAD_FOLDER"] = os.getenv(
		"UPLOAD_FOLDER", default_upload_folder
	)

	try:
		os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
	except OSError:
		fallback_upload_folder = os.path.join(
			tempfile.gettempdir(), "resume_analyser_uploads"
		)
		os.makedirs(fallback_upload_folder, exist_ok=True)
		app.config["UPLOAD_FOLDER"] = fallback_upload_folder

	from app.routes.main import main_bp
	app.register_blueprint(main_bp)

	from app.models.db import init_db
	init_db(app)

	return app
