from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from datetime import datetime
from .prompt import SYSTEM_PROMPT  # Fixed import path with relative import

# Create blueprint
ai_assistant_bp = Blueprint('ai_assistant', __name__,
                            template_folder='templates',
                            static_folder='static',
                            static_url_path='/ai-assistant/static')

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyB5p6v7D-VvnM6GhW2rEaFQZUmZu-dcrvM"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Initialize session data if not exists
def init_session():
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'user_profile' not in session:
        session['user_profile'] = {
            'name': None,
            'preferences': {},
            'last_interaction': None
        }

def get_gemini_response(user_message):
    try:
        prompt = f"""{SYSTEM_PROMPT}

User query: {user_message}"""

        # Generate response
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        return "I apologize, but I'm having trouble generating a response right now. Please try again."

# Test route
@ai_assistant_bp.route('/test')
def test():
    return jsonify({"status": "ok", "message": "Server is running"})

@ai_assistant_bp.route('/')
def home():
    init_session()
    return render_template('chat.html')

@ai_assistant_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data['message']
        session['conversation_history'].append({"role": "user", "content": user_message})

        response = get_gemini_response(user_message)
        session['conversation_history'].append({"role": "assistant", "content": response})

        return jsonify({"response": response})
    except Exception as e:
        print(f"Error in send_message: {e}")
        return jsonify({"error": str(e)}), 500
