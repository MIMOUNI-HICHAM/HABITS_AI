from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import json
import random
import re
from datetime import datetime
import sys
import os

# Create blueprint
ai_assistant_bp = Blueprint('ai_assistant', __name__,
                          template_folder='templates',
                          static_folder='static')

# Load the dataset with UTF-8 encoding and error handling
try:
    dataset_path = os.path.join(os.path.dirname(__file__), 'habit_bot_dataset.json')
    print(f"Loading dataset from: {dataset_path}")  # Debug print
    with open(dataset_path, 'r', encoding='utf-8') as f:
        RESPONSES = json.load(f)
    print(f"Successfully loaded {len(RESPONSES)} responses")  # Debug print
except Exception as e:
    print(f"Error loading dataset: {str(e)}", file=sys.stderr)
    RESPONSES = [
        {
            "category": "unknown",
            "response": "I'm having trouble loading my responses. Please try again later."
        }
    ]

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

# Enhanced intent detection with weighted keywords
INTENT_RULES = {
    'study': {
        'keywords': ['study', 'learn', 'exam', 'test', 'homework', 'assignment', 'pomodoro', 'focus'],
        'weight': 1.0
    },
    'sport': {
        'keywords': ['exercise', 'workout', 'fitness', 'gym', 'run', 'train', 'sport', 'cardio'],
        'weight': 1.0
    },
    'sleep': {
        'keywords': ['sleep', 'rest', 'bed', 'tired', 'exhausted', 'nap', 'dream'],
        'weight': 1.0
    },
    'mental': {
        'keywords': ['stress', 'anxiety', 'mental', 'mind', 'feel', 'emotion', 'mood', 'depression'],
        'weight': 1.0
    },
    'greeting': {
        'keywords': ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
        'weight': 1.0
    },
    'farewell': {
        'keywords': ['bye', 'goodbye', 'see you', 'farewell', 'exit', 'quit'],
        'weight': 1.0
    },
    'thanks': {
        'keywords': ['thanks', 'thank you', 'appreciate', 'grateful'],
        'weight': 1.0
    },
    'clarification': {
        'keywords': ['what', 'how', 'why', 'when', 'where', 'who', 'explain', 'clarify'],
        'weight': 1.0
    },
    'creator': {
        'keywords': ['who made you', 'created', 'developer', 'author', 'hicham'],
        'weight': 1.0
    }
}

def detect_intent(message):
    message = message.lower()
    scores = {}
    
    # Check for exact matches first
    for intent, rule in INTENT_RULES.items():
        for keyword in rule['keywords']:
            if keyword in message:
                scores[intent] = scores.get(intent, 0) + rule['weight']
    
    # If no clear intent found, return None
    if not scores:
        return None
    
    # Return the intent with the highest score
    return max(scores.items(), key=lambda x: x[1])[0]

def get_contextual_response(intent, message):
    # Get all responses for the detected intent
    responses = [r for r in RESPONSES if r['category'].startswith(intent)]
    
    if not responses:
        return random.choice([r for r in RESPONSES if r['category'] == 'unknown'])['response']
    
    # Check conversation history for context
    history = session.get('conversation_history', [])
    
    # Determine response type based on context
    if not history:
        # First interaction - use greeting
        response_type = f"{intent}_greeting"
    elif any('?' in msg['message'] for msg in history[-2:]):
        # Recent question - use challenge
        response_type = f"{intent}_challenge"
    else:
        # Use question to keep conversation going
        response_type = f"{intent}_question"
    
    # Get responses of the selected type
    type_responses = [r for r in responses if r['category'] == response_type]
    
    if not type_responses:
        # Fallback to any response of the intent
        return random.choice(responses)['response']
    
    # Select a random response of the appropriate type
    response = random.choice(type_responses)['response']
    
    # Add personality markers
    if random.random() < 0.3:  # 30% chance to add encouragement
        encouragement = random.choice([r for r in RESPONSES if r['category'] == 'encouragement'])['response']
        response = f"{response}\n\n{encouragement}"
    
    return response

# Test route to verify server is working
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
        
        # Add user message to conversation history
        session['conversation_history'].append({"role": "user", "content": user_message})
        
        # Get bot response
        response = get_bot_response(user_message)
        
        # Add bot response to conversation history
        session['conversation_history'].append({"role": "assistant", "content": response})
        
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error in send_message: {e}")
        return jsonify({"error": str(e)}), 500

def get_bot_response(message):
    # Simple keyword matching for now
    message = message.lower()
    
    # Check for greetings
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm your Habit Helper Bot. How can I assist you today?"
    
    # Check for help requests
    if 'help' in message:
        return "I can help you with:\n- Setting up new habits\n- Tracking your progress\n- Providing motivation\n- Answering questions about habit formation\nWhat would you like to know?"
    
    # Check for habit-related keywords
    if any(word in message for word in ['habit', 'routine', 'track', 'progress']):
        return "I can help you track and improve your habits. Would you like to:\n1. Set up a new habit\n2. Check your progress\n3. Get tips for habit formation"
    
    # Default response
    return "I'm here to help you develop better habits. You can ask me about setting up new habits, tracking your progress, or getting motivation. What would you like to know?"

if __name__ == '__main__':
    ai_assistant_bp.run(debug=True)
