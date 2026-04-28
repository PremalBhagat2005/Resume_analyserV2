import os
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

_client = None
_db = None


def init_db(app):
	"""Initialize MongoDB and attach connection metadata to the app."""
	global _client, _db

	mongo_uri = os.getenv("MONGO_URI", "").strip()
	db_name = os.getenv("MONGO_DB_NAME", "resume_analyser")

	if not mongo_uri:
		app.logger.warning("MONGO_URI is not set; database features are disabled.")
		_client = None
		_db = None
		return

	try:
		_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
		_db = _client[db_name]
		_client.admin.command("ping")

		# Ensure indexes once at startup.
		_db.users.create_index("email", unique=True)
		_db.analyses.create_index([("user_id", 1), ("created_at", -1)])

		app.logger.info("MongoDB connected (db=%s)", db_name)
	except PyMongoError as exc:
		app.logger.warning("MongoDB connection failed: %s", exc)
		_client = None
		_db = None


def is_db_available() -> bool:
	return _db is not None


def _users_collection():
	if _db is None:
		return None
	return _db.users


def _analyses_collection():
	if _db is None:
		return None
	return _db.analyses


def create_user(full_name: str, email: str, password_hash: str):
	users = _users_collection()
	if users is None:
		return None, "Database is not configured."

	email_normalized = email.strip().lower()
	now = datetime.now(timezone.utc)
	doc = {
		"full_name": full_name.strip(),
		"email": email_normalized,
		"password_hash": password_hash,
		"created_at": now,
		"updated_at": now,
	}

	try:
		result = users.insert_one(doc)
	except DuplicateKeyError:
		return None, "An account with this email already exists."

	doc["_id"] = result.inserted_id
	return doc, None


def get_user_by_email(email: str):
	users = _users_collection()
	if users is None:
		return None
	return users.find_one({"email": email.strip().lower()})


def get_user_by_id(user_id: str):
	users = _users_collection()
	if users is None:
		return None

	try:
		obj_id = ObjectId(user_id)
	except Exception:
		return None

	return users.find_one({"_id": obj_id})


def save_analysis(user_id: str, analysis_payload: dict):
	analyses = _analyses_collection()
	if analyses is None:
		return None

	try:
		obj_id = ObjectId(user_id)
	except Exception:
		return None

	payload = dict(analysis_payload)
	payload["user_id"] = obj_id
	payload["created_at"] = datetime.now(timezone.utc)

	result = analyses.insert_one(payload)
	payload["_id"] = result.inserted_id
	return payload


def get_user_analyses(user_id: str, limit: int = 25):
	analyses = _analyses_collection()
	if analyses is None:
		return []

	try:
		obj_id = ObjectId(user_id)
	except Exception:
		return []

	rows = list(
		analyses.find({"user_id": obj_id}).sort("created_at", -1).limit(limit)
	)

	for row in rows:
		row["id"] = str(row.get("_id"))
		created = row.get("created_at")
		if created:
			row["created_at_display"] = created.strftime("%Y-%m-%d %H:%M UTC")
		else:
			row["created_at_display"] = "-"
	return rows