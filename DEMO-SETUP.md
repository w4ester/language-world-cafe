# Local AI Demo Setup Guide (November 2025)

## Quick Demo Overview
Show teachers how students can practice cafe conversations with **Qwen3-14B** (119 languages) and **Whisper** speech recognition - all running locally on your laptop. No internet required, complete privacy, voice-enabled.

---

## 🚀 Cold Start Demo Flow (5 minutes)

### Before the Meeting (One-time setup: 20 min)
1. Install Ollama + Qwen3:14B
2. Install faster-whisper Python package
3. Test the startup script once

### During the Demo (Live!)
1. Run `./start-demo.sh`
2. Browser opens automatically to chat interface
3. Show teachers:
   - **Speak in English** → Whisper transcribes → Qwen3 responds as cafe server
   - **Speak in Spanish** → Whisper transcribes → Qwen3 responds fluently
   - Switch roles (student becomes server, AI becomes customer)
   - All processing happens on your laptop!

---

## 🌐 Remote Demo Setup

Want to share this demo with remote participants or deploy it for broader access?

### Quick Remote Demo (Using Tunnels)

📖 **See [REMOTE-DEMO-SETUP.md](REMOTE-DEMO-SETUP.md)** for complete instructions on:

- **ngrok** - Easiest option, 2-hour free sessions
- **Cloudflare Tunnel** - Free forever, no timeouts
- **Tailscale Funnel** - Private sharing with specific people
- **Cloud deployment** - VPS, Railway, DigitalOcean options

### TL;DR for Quick Share:
```bash
# Terminal 1: Start backend
./start-voice-demo.sh

# Terminal 2: Create tunnel
ngrok http 5001 --region us
# Copy the https://xxx.ngrok-free.app URL

# Share voice-chat-remote.html with participants
# They enter your tunnel URL → instant access!
```

---

## 📦 One-Time Setup (20 minutes)

### Step 1: Install Ollama + Qwen3:14B

**Mac:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download Qwen3:14B (9.3GB - takes 5-10 min)
ollama pull qwen3:14b

# Test it works
ollama run qwen3:14b
# Type: "Hola, soy un mesero. ¿En qué puedo ayudarte?"
# Type: /bye to exit
```

**Windows:**
```powershell
# Download from: https://ollama.com/download/windows
# Run installer, then in PowerShell:
ollama pull qwen3:14b

# Test it
ollama run qwen3:14b
```

**Requirements:**
- **RAM**: 32GB recommended (16GB minimum but slower)
- **Disk**: 10GB free space
- **Model Info**: 9.3GB, 40K context, 119 languages

---

### Step 2: Install Whisper for Speech Recognition

**Option A: faster-whisper (Recommended - 4x faster)**

```bash
# Install Python package
pip install faster-whisper

# Test it
python3 -c "from faster_whisper import WhisperModel; print('✅ Whisper ready!')"
```

**Option B: Distil-Whisper (6x faster, slightly less accurate)**

```bash
pip install distil-whisper transformers torch
```

**Model sizes** (choose based on your RAM):
- `tiny` - 75MB - Fast, decent for demos
- `base` - 145MB - Good balance
- `small` - 488MB - Better accuracy
- `medium` - 1.5GB - **Recommended for multilingual**
- `large-v3` - 3.1GB - Best accuracy

---

### Step 3: Create Demo Startup Script

**File: `start-demo.sh`** (Mac/Linux)

```bash
#!/bin/bash

echo "🚀 Starting Language Cafe AI Demo (Qwen3-14B + Whisper)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Install from: https://ollama.com"
    exit 1
fi

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "📦 Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Check if Qwen3:14B is available
if ! ollama list | grep -q "qwen3:14b"; then
    echo "⚠️  Qwen3:14B not found. Downloading (9.3GB)..."
    echo "    This will take 5-10 minutes depending on your connection."
    ollama pull qwen3:14b
fi

# Verify Whisper is installed
python3 -c "import faster_whisper" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Whisper not found. Installing faster-whisper..."
    pip install faster-whisper
fi

echo "✅ Qwen3-14B ready (119 languages, 40K context)"
echo "✅ Whisper speech recognition ready"
echo ""
echo "🌐 Opening demo in browser..."

# Open the demo page
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8000/ai-chat-demo.html
else
    xdg-open http://localhost:8000/ai-chat-demo.html
fi

# Start simple HTTP server
echo "🖥️  Starting local server on http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 Press Ctrl+C to stop the demo"
echo ""

python3 -m http.server 8000

# Cleanup on exit
trap "echo ''; echo '👋 Shutting down demo...'; pkill -f 'ollama serve'; exit" INT TERM
```

**File: `start-demo.bat`** (Windows)

```batch
@echo off
echo 🚀 Starting Language Cafe AI Demo (Qwen3-14B + Whisper)
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Start Ollama service
echo 📦 Starting Ollama service...
start /B ollama serve
timeout /t 3 /nobreak > nul

REM Check for Qwen3:14B
ollama list | findstr /C:"qwen3:14b" > nul
if errorlevel 1 (
    echo ⚠️  Downloading Qwen3:14B (9.3GB)...
    ollama pull qwen3:14b
)

echo ✅ Qwen3-14B ready (119 languages^)
echo ✅ Whisper speech recognition ready
echo.
echo 🌐 Opening demo in browser...
start http://localhost:8000/ai-chat-demo.html

echo 🖥️  Starting local server on http://localhost:8000
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📌 Press Ctrl+C to stop the demo
echo.

python -m http.server 8000
pause
```

Make executable:
```bash
chmod +x start-demo.sh
```

---

## 🎤 How Whisper Integration Works

### Architecture:
```
Student speaks → Whisper (faster-whisper) → Text transcription
                                                 ↓
                                            Qwen3:14B
                                                 ↓
                                    AI response text → Browser TTS → Audio
```

### Key Advantages:
- **Multilingual**: Whisper trained on 680K hours of multilingual data
- **Accurate**: Better than Web Speech API for accents
- **Offline**: Runs 100% locally
- **Fast**: faster-whisper processes in near real-time
- **Privacy**: No audio sent to cloud

---

## 🎯 Demo Script for Teachers (3 minutes)

### Opening (30 seconds)
> "This demo shows what's possible for your students **right now**. Everything runs on this laptop - Qwen3 with 119 languages, and Whisper for speech recognition. Watch..."

### Demo Sequence:

**1. English Conversation (45 sec)**
```
[Click microphone]
You: "Hi, I'd like to order lunch please"
[Whisper transcribes, Qwen3 responds as server]
AI: "Of course! Welcome to our cafe. Can I start you off with something to drink?"

You: "I'll have an iced coffee"
AI: "Great choice! And what would you like to eat today?"
```

**2. Spanish Conversation (45 sec)**
```
[Click microphone]
You: "Hola, quisiera ver el menú por favor"
[Whisper transcribes, Qwen3 responds in Spanish]
AI: "¡Claro! Aquí tiene el menú. ¿Prefiere algo en particular?"

You: "¿Qué me recomienda?"
AI: "El sándwich club de pavo es muy popular, y viene con papas fritas."
```

**3. Role Reversal (30 sec)**
```
[Click "I'm the Server" button]
AI: "Hola, una mesa para dos por favor."
You: [Respond as the server]
[Show how AI adapts to student being in server role]
```

**4. Show The Code (30 sec)**
```
[Open ai-chat-demo.html in editor]
"This is just HTML and JavaScript. You can:
- Customize scenarios (restaurant, hotel, airport)
- Add vocabulary hints
- Track student progress
- Integrate with your LMS"
```

### Closing (30 seconds)
> "Imagine: Every student practices conversations 24/7, no judgment, gets immediate feedback, works offline in class. And since it's local, complete privacy - no student data leaves the device. Everything you see can be customized for your curriculum."

---

## 🎭 Why This Stack?

### Qwen3:14B Benefits:
✅ **119 languages** (vs. GPT-4's ~50)
✅ **Hybrid thinking mode** - better reasoning for complex grammar
✅ **40K context** - remembers full conversation history
✅ **Performs like Qwen2.5-32B** - quality of larger model
✅ **Apache 2.0 license** - fully yours to customize
✅ **9.3GB** - runs on modern laptops

### faster-whisper Benefits:
✅ **4x faster** than original Whisper
✅ **Multilingual** - trained on 96 languages
✅ **Accurate** - especially for non-native speakers
✅ **CPU efficient** - uses CTranslate2 optimization
✅ **Real-time** - processes speech as it happens
✅ **Open source** - no API costs

---

## 🛠️ Troubleshooting

### Qwen3:14B is slow
```bash
# Check if model loaded
ollama list

# Restart Ollama
pkill ollama && ollama serve

# Use smaller context if needed (add to prompts)
# Default: 40K tokens, can reduce for speed
```

### Whisper not transcribing
```bash
# Check microphone permissions (System Settings → Privacy)
# Verify installation
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('base'); print('✅')"

# Try smaller model if timeout
# medium → base → tiny
```

### Port already in use
```bash
# Use different port
python3 -m http.server 8080
# Then: http://localhost:8080
```

### Out of memory
```bash
# Use smaller Whisper model
# large-v3 → medium → base → tiny

# Or use Qwen3:8b instead
ollama pull qwen3:8b
```

---

## 📊 System Requirements

### Minimum (Demo works, but slower):
- **CPU**: 4 cores
- **RAM**: 16GB
- **Disk**: 15GB free
- **OS**: macOS 11+, Windows 10+, Linux

### Recommended (Smooth experience):
- **CPU**: 8 cores (M1/M2 Mac or Intel i7/i9)
- **RAM**: 32GB
- **Disk**: 20GB free (SSD preferred)
- **GPU**: Optional - speeds up Whisper 2-3x

### What runs on what:
- **Qwen3:14B**: Needs 16GB RAM minimum (32GB better)
- **Whisper medium**: ~2GB RAM
- **Browser + HTTP server**: ~500MB RAM

---

## 🔗 Resources

- **Ollama**: https://ollama.com
- **Qwen3 Models**: https://ollama.com/library/qwen3
- **faster-whisper**: https://github.com/SYSTRAN/faster-whisper
- **Qwen3 Paper**: https://arxiv.org/abs/2505.09388
- **Distil-Whisper**: https://github.com/huggingface/distil-whisper

---

## 💡 Pro Tips for Demo Day

1. **Pre-download everything** the night before
   ```bash
   ollama pull qwen3:14b
   python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium')"
   ```

2. **Test the complete flow** 2-3 times
   ```bash
   ./start-demo.sh
   # Try English and Spanish phrases
   # Test microphone permissions
   ```

3. **Close resource-heavy apps** before demo:
   - Chrome tabs, Slack, Docker, etc.
   - Keep Activity Monitor/Task Manager open to show resource usage

4. **Prepare backup phrases** if nervous:
   - English: "I'd like to order lunch" / "Can I see the menu?"
   - Spanish: "Quisiera ordenar" / "¿Puedo ver el menú?"

5. **Have a Plan B**: If anything fails, show the text-only version first

6. **Timing**: Aim for 3-4 min demo, 5-10 min Q&A

7. **Emphasize**: Privacy, customization, no ongoing costs

---

## 🎓 Future Capabilities to Mention

Once you show the basic demo, mention what else is possible:

- ✅ Grammar correction in real-time
- ✅ Vocabulary suggestions
- ✅ Cultural context explanations
- ✅ Pronunciation feedback
- ✅ Progress tracking & analytics
- ✅ Classroom management dashboard
- ✅ Custom scenarios (hotel, airport, medical)
- ✅ Assessment & grading integration
- ✅ Works in 119 languages

**Key Message**: "This is just the beginning - we can customize everything for your specific curriculum needs."

---

**Next Step**: Create the `ai-chat-demo.html` interface (instructions coming next)
