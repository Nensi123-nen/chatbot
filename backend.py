from flask import Flask, request, jsonify
from flask_cors import CORS  # Add CORS
from datetime import datetime
import json
import re
from typing import Dict, List, Optional
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulated database (in-memory for this example)
class ChatDatabase:
    def __init__(self):
        self.messages: List[Dict] = []
        self.users: Dict[str, Dict] = {}

    def add_message(self, user_id: str, message: str, is_bot: bool = False) -> None:
        timestamp = datetime.now().isoformat()
        self.messages.append({
            "user_id": user_id,
            "message": message,
            "is_bot": is_bot,
            "timestamp": timestamp
        })

    def get_user_history(self, user_id: str) -> List[Dict]:
        return [msg for msg in self.messages if msg["user_id"] == user_id]

    def register_user(self, user_id: str) -> None:
        if user_id not in self.users:
            self.users[user_id] = {"last_seen": datetime.now().isoformat()}

db = ChatDatabase()

# Intent recognition patterns
class IntentMatcher:
    def __init__(self):
        self.patterns = {
            "greeting": r"(hi|hello|hey|greetings|good (morning|afternoon|evening|night))",
            "hours": r"(hours|time|open|close|when)",
            "pricing": r"(price|cost|how much|expensive|cheap)",
            "contact": r"(contact|support|help|email|phone|call)",
            "goodbye": r"(bye|goodbye|thanks|see you|later)",
            "product_info": r"(product|service|what do you (sell|offer))",
            "location": r"(where|location|address|place)"
        }

    def detect_intent(self, message: str) -> Optional[str]:
        message = message.lower().strip()
        for intent, pattern in self.patterns.items():
            if re.search(pattern, message):
                return intent
        return None

intent_matcher = IntentMatcher()

# Response generator
class ResponseGenerator:
    def __init__(self):
        self.responses = {
            "greeting": [
                "Hello! How can I assist you today?",
                "Hi there! What can I help you with?",
                "Hey! Welcome to codesoft Chatbot!"
            ],
            "hours": [
                "We're open from 9 AM to 6 PM, Monday through Friday!",
                "Our business hours are 9-6, Mon-Fri."
            ],
            "pricing": [
                "Our prices vary by service. What specifically are you interested in?",
                "Pricing depends on the package. Could you tell me more?"
            ],
            "contact": [
                "Reach us at support@example.com or 1-800-555-1234.",
                "Contact us via email at support@example.com or call our hotline!"
            ],
            "goodbye": [
                "Goodbye! Have a great day!",
                "See you later! Take care!"
            ],
            "product_info": [
                "We offer various services like consulting, tech support, and more. What do you need?",
                "Our products range from software to hardware solutions. What's your interest?"
            ],
            "location": [
                "We're located at 123 Stellar Street, Tech City.",
                "Our main office is in Tech City at 123 Stellar Street."
            ],
            "default": [
                "I'm sorry, I didn't understand that. Could you please rephrase?",
                "Hmm, I'm not sure about that. Can you clarify?"
            ]
        }

    def get_response(self, intent: Optional[str]) -> str:
        import random
        if intent and intent in self.responses:
            return random.choice(self.responses[intent])
        return random.choice(self.responses["default"])

response_generator = ResponseGenerator()

# API Endpoints
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'user_id' not in data:
            return jsonify({"error": "Missing message or user_id"}), 400

        user_id = data['user_id']
        message = data['message'].strip()
        
        # Register user if new
        db.register_user(user_id)
        
        # Log user message
        db.add_message(user_id, message)
        logger.info(f"User {user_id} sent: {message}")

        # Process message
        intent = intent_matcher.detect_intent(message)
        contextual_response = None
        try:
            contextual_response = get_contextual_response(user_id, message)
        except Exception as e:
            logger.error(f"Error in contextual response: {str(e)}")
        
        response = contextual_response if contextual_response else response_generator.get_response(intent)
        
        # Log bot response
        db.add_message(user_id, response, is_bot=True)
        
        return jsonify({
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    try:
        history = db.get_user_history(user_id)
        return jsonify({"history": history})
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Context-aware response (basic implementation)
def get_contextual_response(user_id: str, current_message: str) -> str:
    history = db.get_user_history(user_id)
    if len(history) > 1 and "pricing" in current_message.lower():
        last_msg = history[-2]["message"].lower()
        if "interested" in last_msg or "specify" in last_msg:
            return "Great! For our basic package, it's $99/month. Want more details?"
    return None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)