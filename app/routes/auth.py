import os
from flask import Blueprint, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
from app.models.db import get_user_by_email, create_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def auth_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        user_info = oauth.google.userinfo()
        
    if not user_info:
        return redirect(url_for('main.signin', error="Failed to fetch user info from Google."))
        
    email = user_info.get('email')
    name = user_info.get('name') or "Google User"
    
    user_doc = get_user_by_email(email)
    
    if not user_doc:
        # Create user without password
        user_doc, create_error = create_user(
            full_name=name,
            email=email,
            password_hash=""
        )
        if create_error:
            # We redirect to signin since we don't have a reliable way to inject error dynamically 
            # without changing the main signin route logic significantly, but appending ?error=
            # usually requires the route to handle request.args.get('error'). 
            # Since the user's signin route might not handle GET errors, we can use session 
            # or just rely on a simple flash if they have it, but for simplicity:
            return redirect(url_for('main.signin'))
            
    session["user_id"] = str(user_doc["_id"])
    session["user_name"] = user_doc.get("full_name", "")
    session["user_email"] = user_doc.get("email", "")
    
    return redirect(url_for('main.index'))
