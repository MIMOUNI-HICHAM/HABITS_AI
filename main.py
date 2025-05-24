from flask import Flask, render_template, session, Blueprint
from budget.routes import budget_bp
from sleeping.routes import sleeping_bp
from sports.routes import sports_bp
from ai_assistant.routes import ai_assistant_bp
from studying.routes import studying_bp
from auth.routes import auth_bp, login_required
from database import init_all_dbs
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Create main blueprint
main_bp = Blueprint('main', __name__)

# Main landing page
@main_bp.route('/')
def index():
    return render_template('landing.html')

# Register all blueprints
app.register_blueprint(main_bp)  # Register main blueprint first
app.register_blueprint(auth_bp)
app.register_blueprint(sports_bp, url_prefix='/sports')
app.register_blueprint(budget_bp, url_prefix='/budget')
app.register_blueprint(sleeping_bp, url_prefix='/sleeping')
app.register_blueprint(studying_bp, url_prefix='/studying')
app.register_blueprint(ai_assistant_bp, url_prefix='/ai-assistant')  # Changed back to /ai-assistant

if __name__ == '__main__':
    # Only initialize databases, don't seed data
    init_all_dbs()
    app.run(debug=True)