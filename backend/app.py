from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from routes.chat import chat_bp
from routes.upload import upload_bp
from routes.health import health_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "https://*.vercel.app"]}})

# Register blueprints
app.register_blueprint(chat_bp,   url_prefix="/api")
app.register_blueprint(upload_bp, url_prefix="/api")
app.register_blueprint(health_bp, url_prefix="/api")

@app.errorhandler(Exception)
def handle_global_error(error):
    code = 500
    message = "Internal server error"
    if isinstance(error, HTTPException):
        code = error.code
        message = error.description
    app.logger.exception(error)
    return jsonify({"error": message}), code

if __name__ == "__main__":
    app.run(debug=True, port=5000)
