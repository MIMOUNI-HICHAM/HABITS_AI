from flask import Flask, render_template, request, jsonify, session
import json
import random
import re
from datetime import datetime
import sys

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Load the dataset with UTF-8 encoding and error handling
try:
    with open('habit_bot_dataset.json', 'r', encoding='utf-8') as f:
        RESPONSES = json.load(f)
except Exception as e:
    print(f"Error loading dataset: {str(e)}", file=sys.stderr)
    sys.exit(1)

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

@app.route('/')
def home():
    init_session()
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.json['message']
    
    # Initialize session if needed
    init_session()
    
    # Update last interaction time
    session['user_profile']['last_interaction'] = datetime.now().isoformat()
    
    # Detect intent
    intent = detect_intent(message)
    
    # Get contextual response
    if intent:
        response = get_contextual_response(intent, message)
    else:
        response = random.choice([r for r in RESPONSES if r['category'] == 'unknown'])['response']
    
    # Update conversation history
    history = session.get('conversation_history', [])
    history.append({
        'message': message,
        'response': response,
        'timestamp': datetime.now().isoformat()
    })
    session['conversation_history'] = history[-5:]  # Keep last 5 interactions
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
