from flask import Blueprint, Flask
import os

ai_assistant_bp = Blueprint('ai_assistant', __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/ai-assistant/static')

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Register the blueprint
    app.register_blueprint(ai_assistant_bp, url_prefix='/ai-assistant')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 