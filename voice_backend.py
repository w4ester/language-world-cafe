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
import asyncio
import os
import tempfile
import logging
from datetime import datetime
import base64
import json
import shutil
import subprocess

# Edge-TTS is now optional; fall back to Piper when available for offline voices
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except Exception:
    EDGE_TTS_AVAILABLE = False

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
WHISPER_MODEL_SIZE = "large"  # Best accuracy for proper transcription

# TTS configuration (local-first)
TTS_ENGINE = os.getenv("TTS_ENGINE", "piper").lower()  # piper | edge-tts
PIPER_BINARY = os.getenv("PIPER_BINARY", "piper")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")
PIPER_SPEAKER_ID = os.getenv("PIPER_SPEAKER_ID", "")

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
- Use the script beats as guidance but feel free to improvise
- If the learner switches languages, mirror them
- If they seem stuck, offer a gentle prompt

You're taking the customer's order. Keep it flowing naturally.""",

        "es": """Eres un mesero amable teniendo una conversación NATURAL por voz.

REGLAS CRÍTICAS DE VOZ:
- Respuestas CORTAS - máximo 1-2 oraciones
- Suena natural y conversacional como si realmente hablaras
- Usa español casual hablado: "¡Claro!", "¡Perfecto!", "¡Qué bien!"
- Haz UNA pregunta a la vez
- Sin lenguaje formal - habla como persona real
- Sé cálido y amigable
- Usa el guión como guía pero puedes improvisar
- Si el alumno cambia de idioma, respóndele en ese idioma
- Si se traba, ofrécele un empujón amable

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
- Use script beats as examples, not a rigid path
- Mirror the learner's language if they switch
- If they need help, give a quick, friendly suggestion

You're ordering lunch. Keep it natural and brief.""",

        "es": """Eres un cliente en un café teniendo una conversación NATURAL por voz.

REGLAS CRÍTICAS DE VOZ:
- Respuestas CORTAS - máximo 1-2 oraciones
- Suena como un cliente real hablando
- Sé amable pero no demasiado hablador
- Ordena naturalmente: "Quisiera...", "¿Me das...?"
- UNA cosa a la vez
- Usa el guión como guía, no como ruta rígida
- Si el alumno cambia de idioma, respóndele en ese idioma
- Si necesita ayuda, dale una sugerencia breve y amable

Estás ordenando almuerzo. Manténlo natural y breve."""
    },

    "host": {
        "en": """You are a cafe host greeting customers in a VOICE conversation.

CRITICAL VOICE RULES:
- Keep responses VERY SHORT - 1 sentence
- Sound warm and welcoming
- Quick and efficient: "Hi! How many?", "Right this way!"
- No long explanations
- Follow the script beats but adapt naturally
- Mirror the learner's language if they switch

You're greeting customers as they arrive.""",

        "es": """Eres un anfitrión de café saludando clientes en conversación de VOZ.

REGLAS CRÍTICAS DE VOZ:
- Respuestas MUY CORTAS - 1 oración
- Suena cálido y acogedor
- Rápido y eficiente: "¡Hola! ¿Cuántos son?", "¡Por aquí!"
- Sin explicaciones largas
- Sigue el guión como guía pero adapta naturalmente
- Si el alumno cambia de idioma, respóndele en ese idioma

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


def build_test_mode_system_prompt(language_mode: str, learner_detected_lang: str = None) -> str:
    """
    Build system prompt for test/free-chat mode with STRICT language clamping.
    Only outputs English and Spanish, regardless of input language.
    """
    base = """You are a friendly bilingual ENGLISH–SPANISH conversation coach for kids and teens.

YOUR JOB:
- Help the student practice real conversations (ordering at a café, booking a table, etc.)
- Follow the student's instructions (e.g. "English first then Spanish", "step by step", "one word at a time")
- Keep replies short (1–3 sentences) and encouraging
- Be PATIENT - wait for the student to ask for the next step
- LISTEN to meta-requests like "wait", "slower", "break it down"
"""

    learner_lang = (learner_detected_lang or "").lower()

    lang_profile = ""
    if language_mode == "en":
        lang_profile = """
OUTPUT LANGUAGE RULES:
- Respond ONLY in ENGLISH
- You may show short Spanish phrases as examples, clearly labeled:
  English: "I'd like a hot tea, please."
  Spanish: "Me gustaría un té caliente, por favor."
- Do NOT answer in any other language
"""
    elif language_mode == "es":
        lang_profile = """
OUTPUT LANGUAGE RULES:
- Respond ONLY in SPANISH
- You may show short English phrases as examples, clearly labeled:
  Inglés: "I'd like a hot tea, please."
  Español: "Me gustaría un té caliente, por favor."
- Do NOT answer in any other language
"""
    else:  # auto / mixed
        lang_profile = f"""
OUTPUT LANGUAGE RULES (AUTO / MIXED):
- You may use BOTH English and Spanish
- Default pattern:
  - Explain in ENGLISH
  - Practice phrases/dialogues in SPANISH
- The student's detected language is "{learner_lang}"
  Even if this is not English or Spanish (e.g. Danish, Norwegian),
  you MUST NOT answer in that language
- If you need to quote a word from their language, put it in quotes and immediately translate
"""

    hard_constraint = """
ABSOLUTE CONSTRAINTS:
- NEVER answer in any language other than English or Spanish
- No long explanations. Keep turns short and interactive
- No markdown, no bullet lists – just natural chat text
- WAIT for the student to say "next" or "continue" before moving to the next step
"""

    meta_behaviour = """
META-REQUESTS YOU MUST OBEY:
- "Say it in English first, then Spanish" → first English sentence, then Spanish sentence, then STOP
- "Now do it in Spanish" → continue same scenario in Spanish
- "Step by step" → break the conversation into very small turns
- "One word at a time" → teach ONE word, wait for student to repeat, then next word
- "Slower" / "Wait" → slow down, give less information per turn
- "Break it down" → split the phrase into smaller pieces
- "Correct me if I make a mistake" → gently correct and model a better answer
- "Stop" / "Okay, stop" → stop the roleplay and ask what they want next

WORD-BY-WORD MODE:
When the student asks for "one word at a time" or "word by word":
1. Give ONLY ONE word or short phrase
2. Show both English and Spanish
3. Ask them to repeat
4. WAIT for them to respond
5. Then give the NEXT word
6. Do NOT give the whole sentence at once
"""

    return base + lang_profile + hard_constraint + meta_behaviour


def build_test_mode_messages(user_text: str, history: list, language_mode: str, user_detected_lang: str = None):
    """Build message array for test/free-chat mode"""
    system_content = build_test_mode_system_prompt(language_mode, user_detected_lang)
    system_message = {"role": "system", "content": system_content}

    # Keep more history (20 exchanges instead of 6)
    recent_history = history[-20:] if len(history) > 20 else history

    return [system_message] + recent_history + [{"role": "user", "content": user_text}]


def get_ai_language_label(language_mode: str, detected_lang: str = None) -> str:
    """
    Return a safe language label for the frontend.
    Only returns 'en', 'es', or 'mixed' - never exposes raw detection codes.
    """
    if language_mode == "en":
        return "en"
    elif language_mode == "es":
        return "es"
    elif detected_lang and detected_lang.lower() in ["en", "es"]:
        return detected_lang.lower()
    else:
        return "mixed"


def build_script_based_prompt(scenario, language, user_role="customer"):
    """Build system prompt based on actual script (soft guidance, not deterministic)"""
    try:
        # Handle free chat mode (no script)
        if scenario == "free_chat":
            return build_free_chat_prompt(language)

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
- Use the script beats as guidance, but feel free to improvise and follow the learner
- If the learner switches languages, mirror them
- If they struggle, offer a brief, encouraging coaching nudge

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
- Usa el guión como guía, pero improvisa y sigue al alumno
- Si el alumno cambia de idioma, respóndele en ese idioma
- Si se traba, dale un empujón amable y breve

TUS LÍNEAS DEL GUIÓN (úsalas naturalmente en la conversación):
{example_lines}

Contexto: Estás jugando el rol del {ai_role}. El cliente está practicando español de café."""

        return prompt

    except Exception as e:
        logger.error(f"Error building script prompt: {e}")
        return VOICE_PROMPTS.get("server", {}).get(language, VOICE_PROMPTS["server"]["en"])


def piper_ready():
    """Check if Piper CLI and model are available."""
    return bool(
        PIPER_MODEL_PATH
        and os.path.isfile(PIPER_MODEL_PATH)
        and shutil.which(PIPER_BINARY)
    )


def pick_tts_engine():
    """
    Choose which TTS engine to use, preferring Piper for offline use when ready.
    Returns the engine string actually selected.
    """
    preferred = (TTS_ENGINE or "").lower()

    if preferred == "piper" and piper_ready():
        return "piper"
    if preferred == "edge-tts" and EDGE_TTS_AVAILABLE:
        return "edge-tts"

    # Fallback: choose any available engine
    if piper_ready():
        return "piper"
    if EDGE_TTS_AVAILABLE:
        return "edge-tts"
    return "none"


def synthesize_with_piper(text):
    """Use Piper CLI to generate speech; returns (audio_bytes, mime) or None."""
    if not piper_ready():
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_path = tmp_file.name

        cmd = [PIPER_BINARY, "--model", PIPER_MODEL_PATH, "--output_file", tmp_path]
        if PIPER_SPEAKER_ID:
            cmd.extend(["--speaker", PIPER_SPEAKER_ID])

        process = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )

        if process.returncode != 0:
            logger.error(f"Piper failed (code {process.returncode}): {process.stderr.decode('utf-8', 'ignore')}")
            return None

        if not os.path.exists(tmp_path):
            logger.error("Piper did not produce an output file")
            return None

        with open(tmp_path, 'rb') as f:
            audio_data = f.read()

        logger.info(f"Speech generated via Piper ({len(audio_data)} bytes)")
        return audio_data, "audio/wav"

    except Exception as e:
        logger.error(f"Piper synthesis error: {str(e)}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


async def generate_speech(text, language="en", gender="female"):
    """
    Generate speech using the selected engine.
    Returns (audio_bytes, mime_type, engine_used) where mime_type defaults to audio/mp3 for edge-tts.
    """
    engine = pick_tts_engine()

    # Try Piper first when selected/available
    if engine == "piper":
        result = synthesize_with_piper(text)
        if result:
            audio_bytes, mime = result
            return audio_bytes, mime, "piper"
        # If Piper fails at runtime, fall through to edge-tts (if available)
        engine = "edge-tts"

    if engine == "edge-tts" and EDGE_TTS_AVAILABLE:
        try:
            voice = VOICES.get(language, {}).get(gender, VOICES["en"]["female"])

            logger.info(f"Generating speech with Edge-TTS ({voice}): '{text[:50]}...'")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_path = tmp_file.name

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp_path)

            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            os.unlink(tmp_path)

            logger.info(f"Speech generated via Edge-TTS ({len(audio_data)} bytes)")
            return audio_data, "audio/mp3", "edge-tts"

        except Exception as e:
            logger.error(f"Edge-TTS generation error: {str(e)}")

    logger.error("No TTS engine available; return None")
    return None, None, engine


def normalize_language(requested_language, detected_language=""):
    """Choose language to use for prompts/TTS."""
    req = (requested_language or "en").lower()
    if req in ["auto", "mixed", "detect"]:
        cand = (detected_language or "").lower()[:2]
        if cand in ["en", "es"]:
            return cand
        return "en"
    if req in ["en", "es"]:
        return req
    return "en"


def is_meta_question(text):
    """
    Detect if user is asking for help/coaching rather than responding in the role-play.
    Returns True if this is a meta-question (asking for help), False if it's part of the scenario.
    """
    text_lower = text.lower()

    # Help request patterns (English)
    help_patterns_en = [
        "how do i say",
        "how do you say",
        "how would i say",
        "what should i say",
        "what do i say",
        "what's another way",
        "how can i say",
        "help me say",
        "i don't know how to say",
        "how to say",
        "what does",
        "what is the word for",
        "how do i ask",
        "how should i respond",
        "what's the right way",
        "is this correct",
        "did i say that right",
        "how do i pronounce",
        "can you help",
        "i need help",
        "i'm stuck",
        "i don't understand"
    ]

    # Help request patterns (Spanish)
    help_patterns_es = [
        "cómo digo",
        "cómo se dice",
        "qué digo",
        "qué debería decir",
        "cómo puedo decir",
        "ayúdame a decir",
        "no sé cómo decir",
        "qué significa",
        "cuál es la palabra para",
        "cómo pregunto",
        "cómo respondo",
        "está correcto",
        "lo dije bien",
        "cómo pronuncio",
        "puedes ayudarme",
        "necesito ayuda",
        "estoy atascado",
        "no entiendo"
    ]

    all_patterns = help_patterns_en + help_patterns_es

    return any(pattern in text_lower for pattern in all_patterns)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    tts_engine = pick_tts_engine()
    return jsonify({
        "status": "healthy",
        "mode": "voice-conversation",
        "whisper_model": WHISPER_MODEL_SIZE,
        "tts_engine": tts_engine,
        "tts_available": {
            "piper": {
                "ready": piper_ready(),
                "binary_found": bool(shutil.which(PIPER_BINARY)),
                "model_configured": bool(PIPER_MODEL_PATH)
            },
            "edge_tts": {"ready": EDGE_TTS_AVAILABLE}
        },
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
    - audio (base64 encoded audio of AI speaking)
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

        effective_language = normalize_language(language, info.language)
        logger.info(f"🌐 Language requested: {language} | detected: {info.language} | using: {effective_language}")

        # Build messages based on scenario
        if scenario == "free_chat":
            # Test/free chat mode - use new coaching system
            logger.info(f"🎓 Free chat mode - using patient coaching system")
            messages = build_test_mode_messages(
                user_text=user_text,
                history=history,
                language_mode=language,
                user_detected_lang=info.language
            )
        else:
            # Script-based scenario mode
            logger.info(f"🎭 Scenario mode: {scenario}")
            system_prompt = build_script_based_prompt(scenario, effective_language)
            messages = [{"role": "system", "content": system_prompt}]

            # Add history (last 20 exchanges)
            for msg in history[-20:]:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })

            # Add current user message
            messages.append({"role": "user", "content": user_text})

        logger.info(f"🤖 Getting AI response (scenario: {scenario}, lang: {language})...")

        # Get response from Ollama with better parameters
        response = ollama.chat(
            model='qwen3:8b',
            messages=messages,
            options={
                "temperature": 0.6,  # Match model default, more consistent
                "top_p": 0.95,       # Match model default
                "max_tokens": 200,   # Allow full explanations (was 60!)
                "num_ctx": 8192      # Use 8k context window
            }
        )

        ai_text = response['message']['content'].strip()
        logger.info(f"🤖 AI says: '{ai_text}'")

        # Step 3: Generate speech for AI response
        logger.info(f"🔊 Generating speech ({effective_language}, {gender})...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data, audio_mime, tts_engine_used = loop.run_until_complete(generate_speech(ai_text, effective_language, gender))
        loop.close()

        if not audio_data:
            return jsonify({"error": "Speech generation failed"}), 500

        # Return safe language label (only en/es/mixed, never raw codes)
        ai_language_label = get_ai_language_label(language, info.language)

        # Return everything
        return jsonify({
            "user_text": user_text,
            "ai_text": ai_text,
            "audio": base64.b64encode(audio_data).decode('utf-8'),
            "audio_mime": audio_mime or "audio/mp3",
            "tts_engine": tts_engine_used,
            "language": effective_language,
            "detected_language": ai_language_label  # Safe label: en/es/mixed only
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
        audio_data, audio_mime, tts_engine_used = loop.run_until_complete(generate_speech(text, language, gender))
        loop.close()

        if not audio_data:
            return jsonify({"error": "Speech generation failed"}), 500

        return jsonify({
            "audio": base64.b64encode(audio_data).decode('utf-8'),
            "audio_mime": audio_mime or "audio/mp3",
            "tts_engine": tts_engine_used
        })

    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/voices', methods=['GET'])
def list_voices():
    """List available voices"""
    return jsonify({
        "active_engine": pick_tts_engine(),
        "engines": {
            "piper": {
                "ready": piper_ready(),
                "binary": PIPER_BINARY,
                "model_path": PIPER_MODEL_PATH
            },
            "edge_tts": {
                "ready": EDGE_TTS_AVAILABLE
            }
        },
        "voices": VOICES
    })


@app.route('/coach-feedback', methods=['POST'])
def coach_feedback():
    """Provide automatic feedback on user's response"""
    try:
        data = request.json
        user_text = data.get('user_text', '')
        ai_text = data.get('ai_text', '')
        language = normalize_language(data.get('language', 'en'))
        scenario = data.get('scenario', 'server_only')

        if not user_text:
            return jsonify({"error": "No user text provided"}), 400

        logger.info(f"📊 Providing feedback for: '{user_text}'")

        # Build coach prompt
        if language == 'en':
            prompt = f"""Analyze this cafe conversation exchange and provide helpful feedback.

Scenario: {scenario}
Language setting: {language} (respond in English unless the learner is clearly in Spanish, then mirror them)

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

Escenario: {scenario}
Idioma configurado: {language} (responde en español a menos que el alumno esté en inglés; entonces síguele)

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
        language = normalize_language(data.get('language', 'en'))
        scenario = data.get('scenario', 'server_only')
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

Scenario: {scenario}

Recent conversation:
{conversation_context}

Student's question: {question}

Provide a clear, practical answer that helps them learn. If they're asking how to say something, give them the phrase and explain when to use it. If they're asking about grammar or vocabulary, explain it simply with examples.

Keep your answer concise (2-3 sentences) and actionable."""
        else:  # Spanish
            prompt = f"""Eres un coach de aprendizaje de idiomas útil. El estudiante está practicando conversaciones de café y tiene una pregunta.

Escenario: {scenario}

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
    logger.info(f"TTS preference: {TTS_ENGINE} | Piper ready: {piper_ready()} | Edge-TTS ready: {EDGE_TTS_AVAILABLE}")
    logger.info("="*60)
    logger.info("Available voices:")
    for lang, voices in VOICES.items():
        logger.info(f"  {lang.upper()}: {', '.join(voices.keys())}")
    logger.info("="*60)
    logger.info("Starting server on http://localhost:5001")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=5001, debug=False)
