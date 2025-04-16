# backend/app.py
from flask import Flask, request, jsonify, Response
from ai_detector import detect_ai_content
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logging.basicConfig(level=logging.INFO)

@app.route('/api/detect_ai', methods=['POST'])
def detect_ai():
    """Detect AI-generated content from the input text"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data['text']
        if not text.strip():
            return jsonify({"error": "Empty text provided"}), 400

        result = detect_ai_content(text)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in detect_ai: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return Response(status=200)

if __name__ == '__main__': 
    app.run(debug=True, host='0.0.0.0', port=5000)
