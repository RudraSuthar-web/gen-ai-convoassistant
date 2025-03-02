# app.py
from flask import Flask, request, jsonify
import requests
import time
import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# ✅ Restrict CORS to your frontend domain
CORS(app, resources={r"/api/*": {"origins": "https://gen-ai-convoassistant.vercel.app"}})

# ✅ Rate Limiting to prevent abuse
limiter = Limiter(app=app, key_func=get_remote_address)
app.config['RATELIMIT_HEADERS_ENABLED'] = True

# ✅ Configuration
class Config:
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    DEFAULT_MAX_TOKENS = 250
    DEFAULT_TEMPERATURE = 0.6
    DEFAULT_TOP_P = 0.9
    MAX_RETRIES = 3

# ✅ In-memory conversation store (for production, use a database)
conversations = {}

@app.route('/api/token', methods=['POST'])
def set_token():
    data = request.json
    if not data or 'token' not in data:
        return jsonify({"error": "API token is required"}), 400
    
    token = data['token']

    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        test_payload = {"inputs": "Hello", "parameters": {"max_new_tokens": 5}}

        response = requests.post(Config.API_URL, headers=headers, json=test_payload, timeout=10)

        if response.status_code in [401, 403]:
            return jsonify({"error": "Invalid Hugging Face API token"}), 401
        
        # ✅ Generate secure session ID
        session_id = os.urandom(16).hex()
        conversations[session_id] = {"token": token, "history": []}

        return jsonify({"success": True, "session_id": session_id})
    
    except Exception as e:
        return jsonify({"error": f"Error validating token: {str(e)}"}), 500

@app.route('/api/start', methods=['POST'])
def start_conversation():
    data = request.json
    session_id = data.get('session_id')
    person_type = data.get('person_type')
    topic = data.get('topic')

    if not session_id or not person_type or not topic:
        return jsonify({"error": "Session ID, person type, and topic are required"}), 400
    
    if session_id not in conversations:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    conversations[session_id].update({
        "history": [],
        "person_type": person_type,
        "topic": topic
    })

    prompt = f"Suggest something to say or a question to ask when starting a conversation with a {person_type} about {topic}."
    
    try:
        suggestion = generate_suggestion(prompt, conversations[session_id]["token"])
        conversations[session_id]["history"].append({"role": "assistant", "content": suggestion})

        return jsonify({"success": True, "suggestion": suggestion})
    
    except Exception as e:
        return jsonify({"error": f"Error generating suggestion: {str(e)}"}), 500

@app.route('/api/next', methods=['POST'])
@limiter.limit("60/minute")  # ✅ Prevent API abuse
def next_suggestion():
    data = request.json
    session_id = data.get('session_id')
    reply = data.get('reply')

    if not session_id or not reply:
        return jsonify({"error": "Session ID and reply are required"}), 400

    if session_id not in conversations:
        return jsonify({"error": "Invalid or expired session"}), 401

    conversation = conversations[session_id]
    person_type = conversation.get("person_type", "person")
    topic = conversation.get("topic", "topic")

    last_suggestion = next((msg["content"] for msg in reversed(conversation["history"]) if msg["role"] == "assistant"), "")

    conversation["history"].append({"role": "user", "content": reply})

    prompt = f"In a conversation with a {person_type} about {topic}, you previously said: '{last_suggestion}'. The other person replied: '{reply}'. Suggest the next thing to say or ask."

    try:
        suggestion = generate_suggestion(prompt, conversation["token"])
        conversation["history"].append({"role": "assistant", "content": suggestion})

        return jsonify({"success": True, "suggestion": suggestion})
    
    except Exception as e:
        return jsonify({"error": f"Error generating suggestion: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in conversations:
        return jsonify({"error": "Invalid or expired session"}), 401

    conversation = conversations[session_id]

    return jsonify({
        "success": True,
        "person_type": conversation.get("person_type", ""),
        "topic": conversation.get("topic", ""),
        "history": conversation["history"]
    })

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    data = request.json
    session_id = data.get('session_id')

    if not session_id or session_id not in conversations:
        return jsonify({"error": "Invalid or expired session"}), 401

    token = conversations[session_id]["token"]
    person_type = conversations[session_id].get("person_type", "")
    topic = conversations[session_id].get("topic", "")

    conversations[session_id] = {"token": token, "person_type": person_type, "topic": topic, "history": []}

    return jsonify({"success": True})

def generate_suggestion(prompt, token):
    """Generate a suggestion using the Hugging Face API"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": Config.DEFAULT_MAX_TOKENS,
            "temperature": Config.DEFAULT_TEMPERATURE,
            "top_p": Config.DEFAULT_TOP_P,
            "return_full_text": False
        }
    }

    for attempt in range(Config.MAX_RETRIES):
        try:
            response = requests.post(Config.API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 429:  # ✅ Handle rate limit (Retry with backoff)
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            result = response.json()

            if isinstance(result, list) and result and "generated_text" in result[0]:
                raw_text = result[0]["generated_text"].strip()
                last_punctuation = max(raw_text.rfind('.'), raw_text.rfind('?'), raw_text.rfind('!'))
                return raw_text[:last_punctuation+1] if last_punctuation != -1 else raw_text

            raise ValueError("Unexpected API response format")
        
        except requests.exceptions.Timeout:
            if attempt == Config.MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
        
        except Exception as e:
            if attempt == Config.MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError("Failed to generate suggestion after multiple attempts")

if __name__ == '__main__':
    app.run(debug=True)
