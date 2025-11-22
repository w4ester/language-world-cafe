# 🌎☕ Cafe Language Learning - AI-Powered Demo

**Immersive bilingual language learning platform with local AI**

Practice real cafe conversations in English & Spanish with **Qwen3:14B** (119 languages) and **Whisper** speech recognition - all running locally on your laptop.

---

## 🎯 What's This?

A complete language learning demo platform designed for teachers to see the power of local AI for education:

✅ **Written conversation scripts** (English & Spanish)
✅ **Live AI practice** with voice and text
✅ **Multiple role-play scenarios** (server, customer, host)
✅ **100% local** - runs entirely on your laptop
✅ **Privacy-first** - no student data sent to cloud
✅ **Bilingual** - seamlessly switch between English/Spanish

---

## 🚀 Quick Start (Cold Boot Demo)

### Prerequisites (One-Time Setup - 20 minutes)

1. **Install Ollama**
   ```bash
   # Mac/Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Windows: Download from https://ollama.com/download/windows
   ```

2. **Download Qwen3:14B** (9.3GB)
   ```bash
   ollama pull qwen3:14b
   ```

3. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

### Run the Demo (2 minutes)

```bash
# Mac/Linux
./start-demo.sh

# Windows
start-demo.bat
```

**That's it!** The browser will open automatically to the demo.

---

## 🌍 Remote Demo (Share with Others)

Want to share the live demo with remote participants? Use tunneling to expose your local backend!

### Quick Start (2 minutes)

1. **Start the backend**
   ```bash
   ./start-voice-demo.sh
   ```

2. **Create a tunnel** (choose one)
   ```bash
   # Option 1: ngrok (easiest, free)
   ngrok http 5001 --region us
   # → Copy URL: https://abc123.ngrok-free.app

   # Option 2: Cloudflare (no timeouts)
   cloudflared tunnel --url http://localhost:5001
   # → Copy URL: https://xyz.trycloudflare.com

   # Option 3: Tailscale (private sharing)
   tailscale funnel 5001
   ```

3. **Share with participants**
   - Deploy repo to GitHub Pages
   - Send link: `https://YOUR-PAGES-URL/voice-chat-remote.html`
   - Users enter your tunnel URL → instant access!

### Features

✅ **Automatic connection testing** - Verifies backend is reachable
✅ **URL persistence** - Saves tunnel URL in localStorage
✅ **Localhost fallback** - "Use Localhost" button for local testing
✅ **Works with all tunnels** - ngrok, Cloudflare, Tailscale, custom domains

### Full Guide

📖 See **[REMOTE-DEMO-SETUP.md](REMOTE-DEMO-SETUP.md)** for:
- Detailed setup instructions for each tunnel service
- Troubleshooting tips
- Cloud deployment options (VPS, Railway, DigitalOcean)
- Security considerations
- Demo participant instructions

---

## 📁 Project Structure

```
ai-workshop-language-learning/
├── index.html                    # Main landing page
├── ai-chat-demo.html             # Live AI practice interface
├── one-pager.html                # English conversation script
├── one-pager-es.html             # Spanish conversation script
├── backend_service.py            # Flask API (Whisper + Qwen3)
├── requirements.txt              # Python dependencies
├── start-demo.sh                 # Startup script (Mac/Linux)
├── start-demo.bat                # Startup script (Windows)
├── DEMO-SETUP.md                 # Detailed setup guide
└── README.md                     # This file
```

---

## 🎭 Features

### 1. **Conversation Scripts**
- Complete written dialogues in English and Spanish
- Vocabulary breakdowns
- Cultural notes and regional variations
- Printable one-pagers

### 2. **Live AI Practice**
- Real-time conversation with Qwen3:14B
- Voice input with Whisper transcription
- Text-to-speech responses
- Switch between roles (server, customer, host)
- Bilingual support (English/Spanish)
- Built-in "Learning Coach" for grammar + pronunciation tips

### 3. **Learning Coach Panel**
- Automatically analyzes every learner utterance
- Gives grammar score, friendly correction, and suggested rewrite
- Highlights pronunciation focus words with IPA/stress hints
- Offers conversation prompts to keep the dialogue flowing
- Runs on the same local Qwen3 model—no extra services needed

### 4. **Role-Play Scenarios**
- **AI as Server**: Student practices ordering
- **AI as Customer**: Student practices serving
- **AI as Host**: Student practices greeting

### 5. **Local AI Stack**
- **Qwen3:14B**: 119 languages, 40K context, hybrid thinking mode
- **Whisper**: Multilingual speech recognition (96 languages)
- **Flask Backend**: RESTful API for AI integration
- **Browser Frontend**: No app installation needed

---

## 🎬 Demo Flow for Teachers

### Opening (30 seconds)
> "Everything you see runs on this laptop - no cloud, no internet needed after setup. Complete privacy for students."

### Show the Scripts (1 minute)
1. Open `index.html` in browser
2. Click "English Script" → Show written dialogue
3. Click "Spanish Script" → Show translations

### Show Live AI (3 minutes)
1. Click "Practice with AI" button
2. **Type**: "Hi, I'd like to order lunch"
   - AI responds as server instantly
3. **Click microphone**: Say "¿Puedo ver el menú?"
   - Whisper transcribes
   - Qwen3 responds in Spanish
   - Browser speaks response
4. **Switch role**: Change AI to "Customer"
   - Now you're the server
   - AI orders from you
5. **Point to Learning Coach** panel below the chat
   - Shows grammar score, rewrite, pronunciation focus words, and next tip
   - Emphasize that feedback updates instantly with each utterance

### Highlight Benefits (1 minute)
- Privacy: All data stays local
- Cost: No ongoing API fees
- Speed: Fast responses
- Customization: Full control over scenarios
- Availability: Works offline

---

## 🛠️ Technical Details

### Backend API Endpoints

```python
GET  /health           # Health check
POST /transcribe       # Whisper speech-to-text
POST /chat             # Qwen3 chat completion
GET  /test-ollama      # Test Ollama connection
```

### Voice TTS Engines (local-first)

- Default: **Piper** (offline) when `PIPER_MODEL_PATH` points to a Piper ONNX voice and the `piper` binary is on PATH (or set `PIPER_BINARY`).
- Fallback: **Edge-TTS** (cloud) when Piper is missing or when `TTS_ENGINE=edge-tts`.
- Optional env vars: `TTS_ENGINE` (`piper`|`edge-tts`), `PIPER_MODEL_PATH` (onnx voice), `PIPER_BINARY` (cli name/path), `PIPER_SPEAKER_ID` (numeric speaker id for multi-speaker models).
- Frontend override: pass `?api=http://localhost:5002` to `voice-chat-with-coach.html` (or set in `voice-chat-remote.html`) to point at a different backend port; language select supports `Auto / Mixed` to mirror the learner using Whisper detection.

### System Requirements

**Minimum** (Demo works, slower):
- CPU: 4 cores
- RAM: 16GB
- Disk: 15GB free

**Recommended** (Smooth):
- CPU: 8 cores (M1/M2 Mac or Intel i7/i9)
- RAM: 32GB
- Disk: 20GB free (SSD)

### Model Sizes

- **Qwen3:14B**: 9.3GB
- **Whisper medium**: ~1.5GB
- **Total download**: ~11GB

---

## 🧪 Testing the Setup

```bash
# Test Ollama
ollama run qwen3:14b
# Type: "Hola, ¿cómo estás?"
# Should respond in Spanish

# Test backend
python3 backend_service.py
# Visit: http://localhost:5000/health

# Test frontend
python3 -m http.server 8000
# Visit: http://localhost:8000
```

---

## 🎓 Use Cases

### For Students
- Practice conversations 24/7
- No judgment, safe environment
- Immediate feedback
- Works at their own pace
- Switch between languages freely

### For Teachers
- Demonstrate real-world scenarios
- Assign practice homework
- Track which scenarios students try
- Customize vocabulary and phrases
- Add new languages/scenarios

### For Schools
- One-time setup cost
- No ongoing subscriptions
- Complete data privacy (FERPA compliant)
- Works in classrooms without internet
- Scales to unlimited students

---

## 📈 Future Enhancements

Ideas to show teachers what's possible:

- ✅ Grammar correction in real-time
- ✅ Vocabulary hints during conversation
- ✅ Pronunciation scoring
- ✅ Progress tracking & analytics
- ✅ Multi-turn complex conversations
- ✅ Additional scenarios (hotel, airport, medical)
- ✅ More languages (French, German, Mandarin)
- ✅ Classroom management dashboard
- ✅ Integration with existing LMS

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 5000 is in use
lsof -i :5000
# Kill existing process
kill $(lsof -t -i:5000)
```

### Qwen3 is slow
```bash
# Check if model is loaded
ollama list
# Restart Ollama
pkill ollama && ollama serve
```

### Whisper not transcribing
```bash
# Check microphone permissions
# System Settings → Privacy → Microphone
# Allow browser access

# Try smaller model
# Edit backend_service.py: WHISPER_MODEL_SIZE = "base"
```

### Port conflicts
```bash
# Use different ports
python3 -m http.server 8080  # Frontend
# Edit backend_service.py: port=5001  # Backend
```

---

## 📚 Documentation

- **Setup Guide**: `DEMO-SETUP.md` - Comprehensive setup instructions
- **Ollama Docs**: https://ollama.com/
- **Qwen3 Info**: https://github.com/QwenLM/Qwen3
- **faster-whisper**: https://github.com/SYSTRAN/faster-whisper

---

## 🤝 Contributing

This demo is built on **The Forrester Standard** - a model-agnostic AI workspace system.

Want to add features?
1. Fork the repository
2. Make your changes
3. Test the complete flow
4. Submit a pull request

---

## 📄 License

MIT License - Free to use, modify, and distribute

---

## 👥 Credits

**Built for**: Baltimore AI Producers Lab
**Purpose**: Demonstrate local AI for education
**Stack**: Qwen3:14B + Whisper + Flask + Vanilla JS
**Philosophy**: Privacy, sovereignty, and accessibility

---

## 📞 Support

### Quick Links
- **GitHub Issues**: Report bugs or request features
- **Demo Video**: (Coming soon)
- **Teacher Guide**: `DEMO-SETUP.md`

### Common Questions

**Q: Does this require internet?**
A: Only for initial setup (downloading models). After that, runs 100% offline.

**Q: Can students use this at home?**
A: Yes! Works on Mac, Windows, Linux. Requires 16GB+ RAM.

**Q: How accurate is the speech recognition?**
A: Whisper is industry-leading, handles accents well, supports 96 languages.

**Q: Can we customize the scenarios?**
A: Absolutely! Edit the system prompts in `backend_service.py`

**Q: What about data privacy?**
A: All processing happens locally. No data sent to external servers.

---

## 🚀 Let's GrOw!

Questions? Want to see this in action?

**Repository**: https://github.com/w4ester/language-world-cafe
**Demo**: Run `./start-demo.sh` and see it live!

---

## 🧪 Test Interface

Try the new **test-chat.html** for free-form coaching practice:
- Patient word-by-word teaching mode
- Meta-request handling ("step by step", "one word at a time")
- Strict English/Spanish language clamping
- Increased context window (200 tokens, 8k context)

Visit: `http://localhost:8000/test-chat.html?api=http://localhost:5002`

---

**w4ester & ai orchestration**
