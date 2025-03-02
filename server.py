from flask import Flask, request, jsonify
import requests
import time
import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from uuid import uuid4

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for testing (restrict in production)

limiter = Limiter(app=app, key_func=get_remote_address)
app.config['RATELIMIT_HEADERS_ENABLED'] = True

# Configuration
class Config:
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    DEFAULT_MAX_TOKENS = 250
    DEFAULT_TEMPERATURE = 0.6
    DEFAULT_TOP_P = 0.9
    MAX_RETRIES = 3

# ✅ Store user conversations separately
user_sessions = {}

@app.route('/api/token', methods=['POST'])
def set_token():
    data = request.json
    if not data or 'token' not in data:
        return jsonify({"error": "API token is required"}), 400
    
    token = data['token']
    session_id = str(uuid4())  # Unique session ID for each user
    
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        test_payload = {"inputs": "Hello", "parameters": {"max_new_tokens": 5}}
        response = requests.post(Config.API_URL, headers=headers, json=test_payload, timeout=10)
        
        if response.status_code in [401, 403]:
            return jsonify({"error": "Invalid API token"}), 401
        
        user_sessions[session_id] = {"token": token, "history": []}
        return jsonify({"success": True, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": f"Error validating token: {str(e)}"}), 500

@app.route('/api/start', methods=['POST'])
def start_conversation():
    data = request.json
    session_id = data.get('session_id')
    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    user_sessions[session_id].update({
        "person_type": data.get('person_type', 'person'),
        "topic": data.get('topic', 'general'),
        "history": []
    })
    
    prompt = f"Suggest something to say when starting a conversation with a {data['person_type']} about {data['topic']}."
    
    try:
        suggestion = generate_suggestion(prompt, user_sessions[session_id]['token'])
        user_sessions[session_id]['history'].append({"role": "assistant", "content": suggestion})
        return jsonify({"success": True, "suggestion": suggestion})
    except Exception as e:
        return jsonify({"error": f"Error generating suggestion: {str(e)}"}), 500

@app.route('/api/next', methods=['POST'])
@limiter.limit("60/minute")  # Rate limiting
def next_suggestion():
    data = request.json
    session_id = data.get('session_id')
    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    reply = data.get('reply', '')
    user_data = user_sessions[session_id]
    user_data['history'].append({"role": "user", "content": reply})
    
    prompt = f"In a conversation with a {user_data['person_type']} about {user_data['topic']}, the user replied: '{reply}'. Suggest the next response."
    
    try:
        suggestion = generate_suggestion(prompt, user_data['token'])
        user_data['history'].append({"role": "assistant", "content": suggestion})
        return jsonify({"success": True, "suggestion": suggestion})
    except Exception as e:
        return jsonify({"error": f"Error generating suggestion: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    return jsonify({"success": True, "history": user_sessions[session_id]['history']})

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    data = request.json
    session_id = data.get('session_id')
    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    user_sessions[session_id]['history'] = []
    return jsonify({"success": True})

def generate_suggestion(prompt, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": Config.DEFAULT_MAX_TOKENS, "temperature": Config.DEFAULT_TEMPERATURE, "top_p": Config.DEFAULT_TOP_P, "return_full_text": False}}
    
    for attempt in range(Config.MAX_RETRIES):
        try:
            response = requests.post(Config.API_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                return result[0]["generated_text"].strip()
            else:
                raise ValueError("Unexpected API response format")
        except requests.exceptions.Timeout:
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt == Config.MAX_RETRIES - 1:
                raise RuntimeError(f"Failed to generate suggestion: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
