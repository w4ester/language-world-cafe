#!/usr/bin/env python3
"""
Real-Time Voice Conversation Backend
Provides streaming voice conversation with Whisper + Qwen3 + Edge-TTS

Features:
- Real-time audio streaming
- High-quality TTS with edge-tts (human-like voices)
- Continuous conversation mode
- Bilingual support (English/Spanish)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
import ollama
import edge_tts
import asyncio
import os
import tempfile
import logging
from datetime import datetime
import base64
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load scripts
SCRIPTS = {}
try:
    with open('scripts.json', 'r') as f:
        SCRIPTS = json.load(f)
        logger.info("✅ Scripts loaded successfully")
except Exception as e:
    logger.error(f"Failed to load scripts.json: {e}")
    SCRIPTS = {"scenarios": {}}

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Global variables
whisper_model = None
WHISPER_MODEL_SIZE = "base"  # Faster for real-time

# High-quality edge-tts voices (human-like)
VOICES = {
    "en": {
        "female": "en-US-AriaNeural",      # Natural, friendly American
        "male": "en-US-GuyNeural"          # Clear, professional American
    },
    "es": {
        "female": "es-MX-DaliaNeural",     # Warm Mexican Spanish
        "male": "es-MX-JorgeNeural"        # Clear Mexican Spanish
    }
}

# System prompts optimized for VOICE conversation (short responses)
VOICE_PROMPTS = {
    "server": {
        "en": """You are a friendly cafe server having a natural VOICE conversation.

CRITICAL VOICE RULES:
- Keep responses SHORT - 1-2 sentences maximum
- Sound natural and conversational like you're actually talking
- Use casual spoken English: "Sure thing!", "You got it!", "Sounds good!"
- Ask ONE question at a time
- No formal language - talk like a real person
- Be warm and friendly

You're taking the customer's order. Keep it flowing naturally.""",

        "es": """Eres un mesero amable teniendo una conversación NATURAL por voz.

REGLAS CRÍTICAS DE VOZ:
- Respuestas CORTAS - máximo 1-2 oraciones
- Suena natural y conversacional como si realmente hablaras
- Usa español casual hablado: "¡Claro!", "¡Perfecto!", "¡Qué bien!"
- Haz UNA pregunta a la vez
- Sin lenguaje formal - habla como persona real
- Sé cálido y amigable

Estás tomando la orden del cliente. Mantén el flujo natural."""
    },

    "customer": {
        "en": """You are a customer at a cafe having a natural VOICE conversation.

CRITICAL VOICE RULES:
- Keep responses SHORT - 1-2 sentences maximum
- Sound like a real customer talking
- Be friendly but not overly chatty
- Order naturally: "I'll have...", "Can I get..."
- ONE thing at a time

You're ordering lunch. Keep it natural and brief.""",

        "es": """Eres un cliente en un café teniendo una conversación NATURAL por voz.

REGLAS CRÍTICAS DE VOZ:
- Respuestas CORTAS - máximo 1-2 oraciones
- Suena como un cliente real hablando
- Sé amable pero no demasiado hablador
- Ordena naturalmente: "Quisiera...", "¿Me das...?"
- UNA cosa a la vez

Estás ordenando almuerzo. Manténlo natural y breve."""
    },

    "host": {
        "en": """You are a cafe host greeting customers in a VOICE conversation.

CRITICAL VOICE RULES:
- Keep responses VERY SHORT - 1 sentence
- Sound warm and welcoming
- Quick and efficient: "Hi! How many?", "Right this way!"
- No long explanations

You're greeting customers as they arrive.""",

        "es": """Eres un anfitrión de café saludando clientes en conversación de VOZ.

REGLAS CRÍTICAS DE VOZ:
- Respuestas MUY CORTAS - 1 oración
- Suena cálido y acogedor
- Rápido y eficiente: "¡Hola! ¿Cuántos son?", "¡Por aquí!"
- Sin explicaciones largas

Estás saludando a los clientes cuando llegan."""
    }
}


def get_whisper_model():
    """Lazy load Whisper model"""
    global whisper_model
    if whisper_model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
        whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully")
    return whisper_model


def build_script_based_prompt(scenario, language, user_role="customer"):
    """Build system prompt based on actual script"""
    try:
        scenario_data = SCRIPTS["scenarios"].get(scenario, {}).get(language, {})
        if not scenario_data:
            return VOICE_PROMPTS.get("server", {}).get(language, VOICE_PROMPTS["server"]["en"])

        ai_role = scenario_data.get("ai_role", "server")
        ai_lines = scenario_data.get("ai_lines", [])
        tips = scenario_data.get("tips", "")

        # Build prompt with actual script examples
        example_lines = "\n".join([f'  - "{line}"' for line in ai_lines[:5]])

        if language == "en":
            prompt = f"""You are a {ai_role} at a cafe having a natural VOICE conversation.

CRITICAL VOICE RULES:
- Keep responses SHORT - 1-2 sentences maximum
- Sound natural and conversational like you're actually talking
- Use the exact phrases from your script when appropriate
- Be warm and friendly
- ONE question at a time
- No formal language

YOUR SCRIPT LINES (use these naturally in conversation):
{example_lines}

Context: You're roleplaying as the {ai_role}. The customer is practicing cafe English."""

        else:  # Spanish
            prompt = f"""Eres un {ai_role} en un café teniendo una conversación NATURAL por voz.

REGLAS CRÍTICAS DE VOZ:
- Respuestas CORTAS - máximo 1-2 oraciones
- Suena natural y conversacional como si realmente hablaras
- Usa las frases exactas de tu guión cuando sea apropiado
- Sé cálido y amigable
- UNA pregunta a la vez
- Sin lenguaje formal

TUS LÍNEAS DEL GUIÓN (úsalas naturalmente en la conversación):
{example_lines}

Contexto: Estás jugando el rol del {ai_role}. El cliente está practicando español de café."""

        return prompt

    except Exception as e:
        logger.error(f"Error building script prompt: {e}")
        return VOICE_PROMPTS.get("server", {}).get(language, VOICE_PROMPTS["server"]["en"])


async def generate_speech(text, language="en", gender="female"):
    """Generate speech using edge-tts (high quality, human-like)"""
    try:
        voice = VOICES.get(language, {}).get(gender, VOICES["en"]["female"])

        logger.info(f"Generating speech with {voice}: '{text[:50]}...'")

        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_path = tmp_file.name

        # Generate speech with edge-tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_path)

        # Read audio data
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()

        # Clean up temp file
        os.unlink(tmp_path)

        logger.info(f"Speech generated: {len(audio_data)} bytes")
        return audio_data

    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")
        return None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "mode": "voice-conversation",
        "whisper_model": WHISPER_MODEL_SIZE,
        "tts": "edge-tts",
        "voices": VOICES,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio file using Whisper"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        logger.info(f"Transcribing audio...")

        # Transcribe with Whisper
        model = get_whisper_model()
        segments, info = model.transcribe(tmp_path, beam_size=5)

        # Collect all segments
        text = " ".join([segment.text for segment in segments]).strip()

        # Clean up temp file
        os.unlink(tmp_path)

        logger.info(f"Transcribed: '{text}' (detected: {info.language})")

        return jsonify({
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability
        })

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/voice-chat', methods=['POST'])
def voice_chat():
    """
    Voice chat endpoint - transcribes audio, gets AI response, returns audio

    Expects:
    - audio file (user's voice)
    - scenario (full_experience/server_only/customer_only/host_only)
    - role (server/customer/host) - DEPRECATED, use scenario
    - language (en/es)
    - gender (male/female for AI voice)
    - history (conversation context)

    Returns:
    - text (AI's response text)
    - audio (base64 encoded MP3 of AI speaking)
    - user_text (what user said)
    """
    try:
        # Get parameters
        scenario = request.form.get('scenario', 'server_only')
        role = request.form.get('role', 'server')  # Fallback for old code
        language = request.form.get('language', 'en')
        gender = request.form.get('gender', 'female')
        history = request.form.get('history', '[]')

        # Parse history
        try:
            history = json.loads(history)
        except:
            history = []

        # Get audio file
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']

        # Step 1: Transcribe user's voice
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        logger.info(f"🎤 Transcribing user audio...")
        model = get_whisper_model()
        segments, info = model.transcribe(tmp_path, beam_size=5)
        user_text = " ".join([segment.text for segment in segments]).strip()
        os.unlink(tmp_path)

        if not user_text:
            return jsonify({"error": "No speech detected"}), 400

        logger.info(f"👤 User said: '{user_text}'")

        # Step 2: Build script-based system prompt
        system_prompt = build_script_based_prompt(scenario, language)

        messages = [{"role": "system", "content": system_prompt}]

        # Add history (last 6 exchanges)
        for msg in history[-6:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })

        # Add current user message
        messages.append({"role": "user", "content": user_text})

        logger.info(f"🤖 Getting AI response (scenario: {scenario}, lang: {language})...")

        # Get response from Ollama
        response = ollama.chat(
            model='qwen3:8b',
            messages=messages,
            options={
                "temperature": 0.7,  # Lower for more consistent script following
                "top_p": 0.9,
                "max_tokens": 60  # Keep it short for voice
            }
        )

        ai_text = response['message']['content'].strip()
        logger.info(f"🤖 AI says: '{ai_text}'")

        # Step 3: Generate speech for AI response
        logger.info(f"🔊 Generating speech ({language}, {gender})...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(generate_speech(ai_text, language, gender))
        loop.close()

        if not audio_data:
            return jsonify({"error": "Speech generation failed"}), 500

        # Return everything
        return jsonify({
            "user_text": user_text,
            "ai_text": ai_text,
            "audio": base64.b64encode(audio_data).decode('utf-8'),
            "language": language,
            "detected_language": info.language
        })

    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech (for testing or reading transcripts)"""
    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'en')
        gender = data.get('gender', 'female')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Generate speech
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(generate_speech(text, language, gender))
        loop.close()

        if not audio_data:
            return jsonify({"error": "Speech generation failed"}), 500

        return jsonify({
            "audio": base64.b64encode(audio_data).decode('utf-8')
        })

    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/voices', methods=['GET'])
def list_voices():
    """List available voices"""
    return jsonify(VOICES)


@app.route('/coach-feedback', methods=['POST'])
def coach_feedback():
    """Provide automatic feedback on user's response"""
    try:
        data = request.json
        user_text = data.get('user_text', '')
        ai_text = data.get('ai_text', '')
        language = data.get('language', 'en')

        if not user_text:
            return jsonify({"error": "No user text provided"}), 400

        logger.info(f"📊 Providing feedback for: '{user_text}'")

        # Build coach prompt
        if language == 'en':
            prompt = f"""Analyze this cafe conversation exchange and provide helpful feedback.

User said: "{user_text}"
AI responded: "{ai_text}"

Provide concise feedback focusing on:
1. Grammar quality (score: Excellent/Good/Fair/Needs work)
2. A friendly correction or suggestion if needed
3. 2-3 words to focus on for pronunciation
4. One practical conversation tip

Keep it encouraging and brief - this is for real-time learning.

Respond in this format:
Grammar Score: [score]
Grammar Feedback: [one sentence]
Correction: [improved version if needed, or "Good!" if no changes]
Focus Words: [word1, word2]
Pronunciation Tip: [one sentence about pronunciation]
Conversation Tip: [one practical suggestion]"""
        else:  # Spanish
            prompt = f"""Analiza este intercambio de conversación de café y proporciona retroalimentación útil.

El usuario dijo: "{user_text}"
La IA respondió: "{ai_text}"

Proporciona retroalimentación concisa enfocándote en:
1. Calidad gramatical (puntuación: Excelente/Bueno/Regular/Necesita trabajo)
2. Una corrección o sugerencia amistosa si es necesaria
3. 2-3 palabras en las que enfocarse para pronunciación
4. Un consejo práctico de conversación

Manténlo alentador y breve - esto es para aprendizaje en tiempo real.

Responde en este formato:
Puntuación de Gramática: [puntuación]
Retroalimentación de Gramática: [una oración]
Corrección: [versión mejorada si es necesaria, o "¡Bien!" si no hay cambios]
Palabras Clave: [palabra1, palabra2]
Consejo de Pronunciación: [una oración sobre pronunciación]
Consejo de Conversación: [una sugerencia práctica]"""

        # Get feedback from Qwen3
        response = ollama.chat(
            model='qwen3:8b',
            messages=[
                {"role": "system", "content": "You are a supportive language learning coach providing real-time feedback."},
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 200
            }
        )

        feedback_text = response['message']['content'].strip()
        logger.info(f"Coach feedback: {feedback_text[:100]}...")

        # Parse feedback
        lines = feedback_text.split('\n')
        feedback_data = {
            "grammar_score": "",
            "grammar_feedback": "",
            "correction": "",
            "focus_words": [],
            "pronunciation_tip": "",
            "conversation_tip": ""
        }

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if 'grammar score' in key or 'puntuación' in key:
                    feedback_data['grammar_score'] = value
                elif 'grammar feedback' in key or 'retroalimentación de gramática' in key:
                    feedback_data['grammar_feedback'] = value
                elif 'correction' in key or 'corrección' in key:
                    feedback_data['correction'] = value if value.lower() not in ['good!', '¡bien!', 'ninguna'] else ''
                elif 'focus words' in key or 'palabras clave' in key:
                    feedback_data['focus_words'] = [w.strip() for w in value.split(',')]
                elif 'pronunciation' in key or 'pronunciación' in key:
                    feedback_data['pronunciation_tip'] = value
                elif 'conversation' in key or 'conversación' in key:
                    feedback_data['conversation_tip'] = value

        return jsonify(feedback_data)

    except Exception as e:
        logger.error(f"Coach feedback error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/coach-question', methods=['POST'])
def coach_question():
    """Answer user's question about the conversation"""
    try:
        data = request.json
        question = data.get('question', '')
        language = data.get('language', 'en')
        conversation_history = data.get('conversation_history', [])

        if not question:
            return jsonify({"error": "No question provided"}), 400

        logger.info(f"❓ Coach question: '{question}'")

        # Build context from conversation
        context_lines = []
        for msg in conversation_history[-6:]:
            role_label = "You" if msg['role'] == 'user' else "AI"
            context_lines.append(f"{role_label}: {msg['content']}")

        conversation_context = "\n".join(context_lines) if context_lines else "No conversation yet"

        # Build coach prompt
        if language == 'en':
            prompt = f"""You are a helpful language learning coach. The student is practicing cafe conversations and has a question.

Recent conversation:
{conversation_context}

Student's question: {question}

Provide a clear, practical answer that helps them learn. If they're asking how to say something, give them the phrase and explain when to use it. If they're asking about grammar or vocabulary, explain it simply with examples.

Keep your answer concise (2-3 sentences) and actionable."""
        else:  # Spanish
            prompt = f"""Eres un coach de aprendizaje de idiomas útil. El estudiante está practicando conversaciones de café y tiene una pregunta.

Conversación reciente:
{conversation_context}

Pregunta del estudiante: {question}

Proporciona una respuesta clara y práctica que les ayude a aprender. Si preguntan cómo decir algo, dales la frase y explica cuándo usarla. Si preguntan sobre gramática o vocabulario, explícalo de manera simple con ejemplos.

Mantén tu respuesta concisa (2-3 oraciones) y accionable."""

        # Get answer from Qwen3
        response = ollama.chat(
            model='qwen3:8b',
            messages=[
                {"role": "system", "content": "You are a supportive, knowledgeable language coach."},
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.6,
                "top_p": 0.9,
                "max_tokens": 150
            }
        )

        answer = response['message']['content'].strip()
        logger.info(f"Coach answer: {answer[:80]}...")

        return jsonify({"answer": answer})

    except Exception as e:
        logger.error(f"Coach question error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🎤 Voice Conversation Backend - Real-Time Mode")
    logger.info("="*60)
    logger.info(f"Whisper: {WHISPER_MODEL_SIZE} (fast transcription)")
    logger.info("Qwen3:8B via Ollama (conversational AI)")
    logger.info("Edge-TTS (human-like voices)")
    logger.info("="*60)
    logger.info("Available voices:")
    for lang, voices in VOICES.items():
        logger.info(f"  {lang.upper()}: {', '.join(voices.keys())}")
    logger.info("="*60)
    logger.info("Starting server on http://localhost:5001")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=5001, debug=False)
