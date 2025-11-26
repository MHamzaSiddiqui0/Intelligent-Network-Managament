from flask import Flask, render_template
from flask_cors import CORS
from models import db
from config import Config
from routes.logs import logs_bp
from routes.alerts import alerts_bp
from routes.chat import chat_bp

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
db.init_app(app)

# Register blueprints
app.register_blueprint(logs_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(chat_bp)

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'Intelligent Network Management System'}

# Create database tables
with app.app_context():
    db.create_all()
    print("[OK] Database tables created successfully")

if __name__ == '__main__':
    print("Starting Intelligent Network Management System...")
    print("Dashboard: http://localhost:5000")
    print("API Docs: See implementation_plan.md for endpoints")
    app.run(debug=True, host='0.0.0.0', port=5000)
