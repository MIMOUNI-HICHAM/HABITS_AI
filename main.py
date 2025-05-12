from flask import Flask, render_template
from sports.routes import sports_bp
from budget.routes import budget_bp
from sleeping.routes import sleeping_bp
from studying.routes import studying_bp
from sports.database import init_db

app = Flask(__name__)

# Main landing page (outside the sports blueprint)
@app.route('/')
def home():
    return render_template('landing.html')  # This uses the main app's templates folder

# Register the blueprints with their prefixes
app.register_blueprint(sports_bp, url_prefix='/sports')
app.register_blueprint(budget_bp, url_prefix='/budget')
app.register_blueprint(sleeping_bp, url_prefix='/sleeping')
app.register_blueprint(studying_bp, url_prefix='/studying')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)