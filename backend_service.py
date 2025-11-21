#!/usr/bin/env python3
"""
Cafe Language Learning - Local AI Backend
Provides Whisper speech-to-text + Qwen3:14B chat via Ollama
Designed for teacher demos - runs 100% locally

Requirements:
- pip install flask flask-cors faster-whisper ollama
- ollama pull qwen3:14b
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
import ollama
import os
import tempfile
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Global variables for models (lazy loading)
whisper_model = None
WHISPER_MODEL_SIZE = "medium"  # Can be: tiny, base, small, medium, large-v3

# System prompts for different roles
SYSTEM_PROMPTS = {
    "server": {
        "en": """You are a friendly cafe server in an American cafe. You're helping a customer order lunch.

Guidelines:
- Keep responses natural and conversational
- Use casual American English (e.g., "I'll have...", "sounds good", "you got it")
- Don't be overly formal
- Ask follow-up questions about drinks, sides, dietary restrictions
- Suggest menu items when appropriate
- Keep responses to 1-3 sentences unless explaining something complex
- If the customer switches languages, respond in that language

Current conversation context: You're taking the customer's order.""",

        "es": """Eres un mesero amable en un café. Estás ayudando a un cliente a ordenar el almuerzo.

Pautas:
- Mantén las respuestas naturales y conversacionales
- Usa español casual y apropiado (por ejemplo, "¿qué te traigo?", "claro", "perfecto")
- No seas demasiado formal (usa 'tú' a menos que el contexto pida 'usted')
- Haz preguntas de seguimiento sobre bebidas, acompañamientos, restricciones dietéticas
- Sugiere platillos del menú cuando sea apropiado
- Mantén respuestas de 1-3 oraciones a menos que expliques algo complejo
- Si el cliente cambia de idioma, responde en ese idioma

Contexto actual: Estás tomando la orden del cliente."""
    },

    "customer": {
        "en": """You are a customer at a cafe ordering lunch. You're friendly but not overly chatty.

Guidelines:
- Order food naturally like a real customer
- Ask questions about the menu
- Be polite but casual
- Sometimes ask for recommendations
- Occasionally have dietary preferences or restrictions
- Keep responses to 1-2 sentences
- If the server speaks in Spanish, respond in Spanish

Current context: You're at the cafe and ready to order.""",

        "es": """Eres un cliente en un café ordenando el almuerzo. Eres amable pero no demasiado hablador.

Pautas:
- Ordena comida naturalmente como un cliente real
- Haz preguntas sobre el menú
- Sé educado pero casual
- A veces pide recomendaciones
- Ocasionalmente ten preferencias o restricciones dietéticas
- Mantén respuestas de 1-2 oraciones
- Si el mesero habla en inglés, responde en inglés

Contexto actual: Estás en el café y listo para ordenar."""
    },

    "host": {
        "en": """You are a friendly host/greeter at a cafe entrance.

Guidelines:
- Greet customers warmly
- Ask how many people in their party
- Tell them where to sit or lead them to a table
- Mention wait times if applicable
- Keep responses brief and welcoming (1-2 sentences)
- If they speak Spanish, respond in Spanish

Current context: A customer just walked in.""",

        "es": """Eres un anfitrión amable en la entrada de un café.

Pautas:
- Saluda a los clientes calurosamente
- Pregunta cuántas personas son
- Diles dónde sentarse o guíalos a una mesa
- Menciona tiempos de espera si aplica
- Mantén respuestas breves y acogedoras (1-2 oraciones)
- Si hablan en inglés, responde en inglés

Contexto actual: Un cliente acaba de entrar."""
    }
}

COACH_SYSTEM_PROMPT = """You are a supportive bilingual language coach helping a learner practice real cafe conversations.

Provide concise, actionable feedback using the learner's text transcript. Always return valid JSON with the keys:
{
  "grammar": {
    "score": "Excellent/Good/Fair/Needs work",
    "feedback": "One friendly sentence explaining the main grammar suggestion",
    "correction": "Rewrite of the learner sentence with improved grammar"
  },
  "pronunciation": {
    "focus_words": ["word", "word"],
    "tips": "One sentence describing sounds to practice using IPA or syllable stress when helpful"
  },
  "conversation_tip": "Short tip for what to try next in the conversation"
}

Keep the tone encouraging. Default to the learner's language (English or Spanish)."""


def get_whisper_model():
    """Lazy load Whisper model"""
    global whisper_model
    if whisper_model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
        whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully")
    return whisper_model


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "whisper_model": WHISPER_MODEL_SIZE,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file using Whisper
    Expects: multipart/form-data with 'audio' file
    Returns: {"text": "transcribed text", "language": "en"}
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        logger.info(f"Transcribing audio file: {tmp_path}")

        # Transcribe with Whisper
        model = get_whisper_model()
        segments, info = model.transcribe(tmp_path, beam_size=5)

        # Collect all segments
        text = " ".join([segment.text for segment in segments]).strip()

        # Clean up temp file
        os.unlink(tmp_path)

        logger.info(f"Transcription result: '{text}' (language: {info.language})")

        return jsonify({
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability
        })

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat with Qwen3:14B via Ollama
    Expects: {"message": "user message", "role": "server|customer|host", "language": "en|es", "history": [...]}
    Returns: {"response": "AI response"}
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        role = data.get('role', 'server')  # server, customer, or host
        language = data.get('language', 'en')  # en or es
        history = data.get('history', [])

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Get system prompt for role and language
        system_prompt = SYSTEM_PROMPTS.get(role, {}).get(language, SYSTEM_PROMPTS['server']['en'])

        # Build message history for Ollama
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history (limit to last 10 messages)
        for msg in history[-10:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        logger.info(f"Chat request - Role: {role}, Language: {language}, Message: '{user_message}'")

        # Call Ollama
        response = ollama.chat(
            model='qwen3:8b',
            messages=messages,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 150  # Keep responses concise
            }
        )

        ai_response = response['message']['content'].strip()

        logger.info(f"AI response: '{ai_response}'")

        return jsonify({
            "response": ai_response,
            "role": role,
            "language": language
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/test-ollama', methods=['GET'])
def test_ollama():
    """Test if Ollama is accessible and qwen3:8b is available"""
    try:
        # Try to list models
        models = ollama.list()
        qwen_available = any('qwen3:8b' in model['name'] for model in models.get('models', []))

        return jsonify({
            "ollama_accessible": True,
            "qwen3_14b_available": qwen_available,
            "models": [model['name'] for model in models.get('models', [])]
        })
    except Exception as e:
        return jsonify({
            "ollama_accessible": False,
            "error": str(e)
        }), 500


def parse_feedback_response(raw_text):
    """Attempt to parse JSON feedback from model output"""
    try:
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidate = raw_text[start_idx:end_idx + 1]
            return json.loads(json_candidate)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse feedback JSON: {e}")

    # Fallback minimal structure
    return {
        "grammar": {
            "score": "Unknown",
            "feedback": raw_text.strip(),
            "correction": ""
        },
        "pronunciation": {
            "focus_words": [],
            "tips": ""
        },
        "conversation_tip": ""
    }


@app.route('/feedback', methods=['POST'])
def realtime_feedback():
    """Provide grammar + pronunciation feedback via Qwen."""
    try:
        data = request.json or {}
        user_message = data.get('message', '').strip()
        language = data.get('language', 'en')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        logger.info(f"Feedback request - Language: {language}, Text: '{user_message}'")

        response = ollama.chat(
            model='qwen3:8b',
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Learner language: {language}\nLearner sentence: {user_message}"
                }
            ],
            options={
                "temperature": 0.4,
                "top_p": 0.9,
                "max_tokens": 250
            }
        )

        raw_feedback = response['message']['content'].strip()
        logger.info(f"Feedback response: {raw_feedback}")

        feedback_data = parse_feedback_response(raw_feedback)
        feedback_data['raw'] = raw_feedback
        feedback_data['language'] = language

        return jsonify(feedback_data)

    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Cafe Language Learning - Local AI Backend")
    logger.info("="*60)
    logger.info(f"Whisper model: {WHISPER_MODEL_SIZE}")
    logger.info("Qwen3:8B via Ollama")
    logger.info("="*60)
    logger.info("Starting server on http://localhost:5000")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=5000, debug=True)
