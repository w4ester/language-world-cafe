# Script-Based Conversation System

## Overview

The voice conversation system now uses **actual cafe conversation scripts** to make AI responses more natural and scenario-specific. The AI follows real dialogue patterns from the one-pager scripts instead of generic prompts.

---

## How It Works

### 1. **Script Storage** (`scripts.json`)

All cafe conversation scenarios are stored in `scripts.json` with:
- **Full scenarios**: Complete multi-stage cafe visits (arriving, ordering, eating, paying)
- **Role-specific scenarios**: Server-only, customer-only, host-only
- **Bilingual support**: Both English and Spanish versions
- **Script lines**: Exact phrases the AI should use in conversation

Example structure:
```json
{
  "scenarios": {
    "server_only": {
      "en": {
        "name": "Practice Ordering (You are Customer)",
        "ai_role": "server",
        "ai_lines": [
          "Hey there! How are you doing today?",
          "Can I get you something to drink?",
          "That comes with fries or a side salad. Which would you prefer?"
        ],
        "tips": "Order naturally: 'I'll have...', 'Can I get...'"
      }
    }
  }
}
```

### 2. **Dynamic Prompt Building** (`voice_backend.py`)

The backend builds custom system prompts based on the chosen scenario:

```python
def build_script_based_prompt(scenario, language, user_role="customer"):
    # Retrieves scenario data from scripts.json
    # Extracts AI's script lines
    # Builds prompt with actual phrases embedded
    # Returns customized system prompt
```

**Key features:**
- Loads script lines for the specific scenario
- Includes first 5 script lines as examples
- Tells AI to "use these exact phrases when appropriate"
- Maintains conversational tone while following script

### 3. **URL-Based Scenario Routing**

The frontend uses URL parameters to select scenarios:

**Examples:**
- `voice-chat-with-coach.html?scenario=server_only&lang=en` - AI plays server in English
- `voice-chat-with-coach.html?scenario=customer_only&lang=es` - AI plays customer in Spanish
- `voice-chat-with-coach.html?scenario=host_only&lang=en` - AI plays host in English
- `voice-chat-with-coach.html?scenario=full_experience&lang=es` - Complete cafe visit in Spanish
  *(legacy `voice-chat.html` now redirects to this page)*

### 4. **Index Page Integration**

Each card on `index.html` now links to the appropriate scenario:

| Card | Scenario | What AI Does |
|------|----------|--------------|
| English Script | `server_only` | Acts as server, takes your order |
| Spanish Script | `server_only` | Acts as server, takes your order |
| AI Host/Greeter | `host_only` | Greets you, seats you |
| AI Server/Waiter | `server_only` | Takes your order, serves food |
| AI Customer | `customer_only` | Orders from you (you're the server) |
| Full Experience | `full_experience` | Multi-stage cafe visit |

---

## Technical Changes

### Files Modified:

1. **`scripts.json`** (created)
   - Stores all conversation scenarios
   - 258 lines of structured cafe dialogue
   - Both English and Spanish versions

2. **`voice_backend.py`** (updated)
   - Loads scripts.json on startup
   - Added `build_script_based_prompt()` function
   - Modified `/voice-chat` endpoint to use scenario parameter
   - Temperature lowered to 0.7 for more consistent script following
   - max_tokens reduced to 60 for shorter, natural responses

3. **`voice-chat-with-coach.html`** (new enhanced interface)
   - Reads `scenario` from URL parameters
   - Sends scenario to backend instead of generic role
   - Sets default language from URL
   - Includes Live Coach panel for feedback + Q&A
   - Legacy `voice-chat.html` now auto-redirects here

4. **`index.html`** (updated)
   - All voice chat links include scenario parameter
   - Reorganized buttons: Text Chat + Voice (EN) + Voice (ES)
   - Clear mapping between cards and scenarios

---

## Benefits

### 1. **More Natural Conversations**
- AI uses actual phrases from real cafe conversations
- Follows realistic dialogue patterns
- Sounds like a real person, not a chatbot

### 2. **Scenario-Specific Behavior**
- Host greets and seats naturally
- Server takes orders professionally
- Customer orders realistically

### 3. **Consistent with Scripts**
- Voice practice matches written scripts
- Students can study script, then practice with voice
- Reinforces learning from one-pagers

### 4. **Flexible and Extensible**
- Easy to add new scenarios (edit scripts.json)
- Can customize phrases for different regions
- Support for additional languages

---

## Demo Flow

### For Teachers:

1. **Show the Scripts**
   - Click "English Script" → Show written dialogue
   - Point out specific phrases

2. **Practice with Voice**
   - Click "🎤 Voice Chat" button
   - Demonstrate push-to-talk
   - Show how AI uses exact script phrases

3. **Try Different Scenarios**
   - Switch to "AI Customer" card
   - Now you're the server
   - AI orders from you using script lines

4. **Highlight the Magic**
   - Same local AI (Qwen3:8B)
   - Different behavior per scenario
   - Uses actual teaching materials (scripts)

---

## Configuration

### Available Scenarios:

- `server_only` - AI acts as server/waiter
- `customer_only` - AI acts as customer (you're the server)
- `host_only` - AI acts as host/greeter
- `full_experience` - Complete multi-stage cafe visit

### Supported Languages:

- `en` - English (American)
- `es` - Spanish (Mexican)

### Voice Options:

**English:**
- Female: `en-US-AriaNeural` (friendly, natural)
- Male: `en-US-GuyNeural` (clear, professional)

**Spanish:**
- Female: `es-MX-DaliaNeural` (warm)
- Male: `es-MX-JorgeNeural` (clear)

---

## Testing

### Quick Test:

```bash
# Start the voice demo
./start-voice-demo.sh

# Open in browser:
# - http://localhost:8000/voice-chat-with-coach.html?scenario=server_only&lang=en
# - http://localhost:8000/voice-chat-with-coach.html?scenario=host_only&lang=es
# - http://localhost:8000/voice-chat-with-coach.html?scenario=customer_only&lang=en

# Or just use the index page and click any Voice Chat button!
```

### Check Logs:

```bash
# Verify scripts loaded
grep "Scripts loaded" /tmp/voice_backend.log

# Watch conversation
tail -f /tmp/voice_backend.log
```

---

## Adding New Scenarios

Want to add a new scenario? Edit `scripts.json`:

```json
{
  "scenarios": {
    "my_new_scenario": {
      "en": {
        "name": "My Custom Scenario",
        "ai_role": "role_name",
        "ai_lines": [
          "First phrase AI should say",
          "Second phrase AI should say",
          "Third phrase AI should say"
        ],
        "tips": "Helpful tip for the learner"
      },
      "es": {
        // Spanish version
      }
    }
  }
}
```

Then restart the voice backend:
```bash
# Kill existing process
pkill -f voice_backend.py

# Restart
./start-voice-demo.sh
```

---

## Architecture

```
┌─────────────────┐
│   index.html    │  User clicks card
│                 │
│  Click "Voice"  │
└────────┬────────┘
         │
         │ URL: ?scenario=server_only&lang=en
         ↓
┌─────────────────┐
│ voice-chat-with-coach.html │  Frontend
│                 │
│ - Read scenario │
│ - Record audio  │
│ - Send to API   │
└────────┬────────┘
         │
         │ POST /voice-chat
         │ FormData: audio, scenario, language, gender
         ↓
┌─────────────────┐
│ voice_backend.py│  Backend
│                 │
│ 1. Transcribe   │ ← Whisper STT
│ 2. Build prompt │ ← scripts.json
│ 3. Get response │ ← Qwen3:8B
│ 4. Synthesize   │ ← Edge-TTS
│ 5. Return audio │
└────────┬────────┘
         │
         │ JSON: {user_text, ai_text, audio_base64}
         ↓
┌─────────────────┐
│ voice-chat-with-coach.html │
│                 │
│ - Play audio    │
│ - Show text     │
│ - Ready for     │
│   next input    │
└─────────────────┘
```

---

## Performance

- **Whisper base**: ~2-3 seconds for transcription
- **Qwen3:8B**: ~1-2 seconds for response (with script context)
- **Edge-TTS**: ~1 second for speech synthesis
- **Total latency**: 4-6 seconds per exchange

**Optimizations:**
- Temperature 0.7 (more consistent, faster)
- max_tokens 60 (shorter responses, faster generation)
- Script context limits response variability

---

## Troubleshooting

### AI not following script?

1. Check scripts.json is valid JSON
2. Verify scenario exists in scripts.json
3. Restart voice backend to reload scripts
4. Check logs: `grep "Using scenario" /tmp/voice_backend.log`

### Wrong scenario playing?

1. Check URL parameters in browser
2. Verify index.html links have correct scenario
3. Check voice-chat-with-coach.html console: "📋 Using scenario: ..."

### Scripts not loading?

1. Check file exists: `ls -la scripts.json`
2. Check JSON syntax: `python3 -m json.tool scripts.json`
3. Check backend logs: `grep -i script /tmp/voice_backend.log`

---

## Next Steps

Future enhancements:

- [ ] Add more scenarios (hotel, airport, medical)
- [ ] Multi-stage progression tracking
- [ ] Feedback on script adherence
- [ ] Record and review conversations
- [ ] Export conversation transcripts
- [ ] Performance metrics (how well you followed script)

---

**w4ester & ai orchestration**
