from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
import random
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client
client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI initialized successfully")
    else:
        logger.error("❌ OPENAI_API_KEY not found")
except Exception as e:
    logger.error(f"❌ OpenAI initialization failed: {e}")

# --- LOCAL KNOWLEDGE BASE ---
# --- IMPROVED LOCAL INTELLIGENCE ---
LOCAL_KNOWLEDGE = {
    "greetings": [
        "Hello! I'm your AI assistant. How can I help you?",
        "Hi there! Ready to chat.",
        "Hey! What's on your mind?"
    ],
    "how_are_you": [
        "I'm just code, but I'm functioning perfectly! How are you?",
        "I'm doing great, thanks for asking! How can I help?",
        "Systems are online and ready."
    ],
    "capital": [
        "The capital of India is New Delhi.",
        "New Delhi is the capital of India."
    ],
    "identity": [
        "I am Aibot, a futuristic AI assistant.",
        "I'm a chatbot created to help you."
    ],
    "default": [
        "That's interesting! Tell me more.",
        "I'm in offline mode, so I only know a few things. Try asking about 'India' or say 'Hello'.",
        "Could you rephrase that? I'm listening."
    ]
}

def get_local_response(user_input):
    """
    Smarter logic: checks for keywords anywhere in the sentence
    instead of exact matches.
    """
    text = user_input.lower().strip()
    
    # 1. Empty Check
    if not text:
        return "I didn't hear anything. Please type a message."

    # 2. Greeting Checks
    if any(word in text for word in ["hi", "hello", "hey", "greetings"]):
        return random.choice(LOCAL_KNOWLEDGE["greetings"])

    # 3. "How are you" Check
    if "how are you" in text or "how r u" in text:
        return random.choice(LOCAL_KNOWLEDGE["how_are_you"])

    # 4. Identity Check
    if any(phrase in text for phrase in ["who are you", "your name", "what are you"]):
        return random.choice(LOCAL_KNOWLEDGE["identity"])

    # 5. Fact Checks (Fuzzy Matching)
    # Checks if BOTH "capital" AND "india" are in the sentence
    if "capital" in text and "india" in text:
        return random.choice(LOCAL_KNOWLEDGE["capital"])

    # 6. Polite Closings
    if any(word in text for word in ["bye", "goodbye", "thanks", "thank you"]):
        return "You're welcome! Goodbye!"

    # 7. Default (If nothing matches)
    return random.choice(LOCAL_KNOWLEDGE["default"])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid request"}), 400

        user_input = data['message'].strip()
        logger.info(f"Received message: {user_input}")

        # 1. Try OpenAI if client exists
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=150
                )
                return jsonify({
                    "reply": response.choices[0].message.content,
                    "source": "openai"
                })

            except Exception as e:
                # IMPORTANT: This catches the "429 Quota" error
                logger.error(f"OpenAI API Error: {e}")
                print("⚠️ Switching to Local Mode due to API Error")
                
                # FALLBACK TO LOCAL RESPONSE
                return jsonify({
                    "reply": get_local_response(user_input),
                    "source": "local_fallback"
                })

        # 2. If client wasn't set up, use local immediately
        return jsonify({
            "reply": get_local_response(user_input),
            "source": "local"
        })

    except Exception as e:
        logger.error(f"Server Error: {e}")
        return jsonify({"reply": "Critical server error.", "source": "error"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)