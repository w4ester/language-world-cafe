# 🧠 Live AI Coach Feature

## Overview

The **Live AI Coach** gives you instant, real-time feedback during voice conversations and can answer your questions about the conversation as it happens. It's like having a personal language tutor sitting next to you while you practice.

---

## What It Does

### 1. **Automatic Feedback After Each Exchange**

After every voice conversation turn, the AI coach automatically analyzes your response and provides:

- **Grammar Score**: Excellent / Good / Fair / Needs work
- **Grammar Feedback**: Friendly explanation of what you did well or could improve
- **Correction**: A suggested rewrite if needed (or "Good!" if no changes)
- **Focus Words**: 2-3 words to practice pronunciation
- **Pronunciation Tips**: Specific sounds or stress patterns to work on
- **Conversation Tip**: Practical advice for the next turn

### 2. **Ask Questions Anytime**

You can pause and ask the coach questions like:
- "How do I say 'without ice' in Spanish?"
- "What's another way to order coffee?"
- "Why did they use 'will' instead of 'going to'?"
- "What does 'side salad' mean?"
- "Is there a more polite way to say that?"

The coach sees your full conversation history and gives context-aware answers.

---

## How to Use It

### **Access the Coach Interface:**

1. Go to http://localhost:8000/
2. Click any "🎤 Voice + Coach" button on the index page
3. You'll see a split-screen interface:
   - **Left side**: Voice conversation
   - **Right side**: Live AI coach panel

### **Using Voice Chat:**

1. Press and **hold** the microphone button
2. Speak your response
3. Release when done
4. AI will respond with voice
5. **Coach automatically analyzes** your response

### **Asking Questions:**

1. Type your question in the "Ask me anything..." box
2. Click "Ask" or press Enter
3. Coach responds with helpful explanations
4. Continue your conversation when ready

---

## Interface Layout

```
┌─────────────────────────────┬─────────────────────┐
│   VOICE CONVERSATION        │   LIVE AI COACH     │
│                             │                     │
│   🎤 (Press & Hold)         │  📊 Auto Feedback   │
│                             │  ─────────────────  │
│   Status: Ready to talk     │  Grammar: Good      │
│                             │  Suggestion: ...    │
│   ┌───────────────────┐     │  Focus: coffee, ice │
│   │ YOU: I'll have... │     │  Tip: ...           │
│   │ AI:  Sure thing...│     │                     │
│   └───────────────────┘     │  ❓ Your Question   │
│                             │  ...                │
│   🔄 New  ← Back            │  🧠 Coach Answer    │
│                             │  ...                │
│                             │                     │
│                             │  [Ask anything...  ]│
└─────────────────────────────┴─────────────────────┘
```

---

## Example Session

### **Exchange 1:**

**You (voice):** "Hi, I want coffee"

**AI (voice):** "Hey there! Sure, what kind of coffee would you like?"

**Coach Feedback (automatic):**
```
📊 Auto Feedback
────────────────
Grammar: Good
Feedback: Your message was clear! Try "I'd like" instead of "I want"
for more natural cafe English.

💡 Try: "Hi, I'd like a coffee"

Pronunciation:
Focus Words: coffee, like
Tip: Emphasize the first syllable: COF-fee (not cof-FEE)

Conversation Tip:
Next, specify the type (iced, hot) and size (small, medium, large)
```

### **You Ask:** "How do I say 'without sugar'?"

**Coach Answer:**
```
🧠 Coach Answer
────────────
Say "without sugar" or "no sugar, please." In this context, you could
say "I'd like an iced coffee with no sugar, please." The "please" makes
it more polite in service situations.
```

---

## Technical Details

### **Backend Endpoints:**

1. **`POST /coach-feedback`**
   - Called automatically after each voice exchange
   - Analyzes user's text and AI's response
   - Returns structured feedback (grammar, pronunciation, tips)

2. **`POST /coach-question`**
   - Called when user asks a question
   - Includes conversation history for context
   - Returns helpful, actionable answer

### **How It Works:**

```
User speaks → Whisper transcribes
              ↓
           Qwen3:8b generates AI response
              ↓
           Edge-TTS speaks response
              ↓
       【SIMULTANEOUSLY】
              ↓
    Coach analyzes user's text
              ↓
    Qwen3:8b provides feedback
              ↓
    Feedback displayed in coach panel
```

### **Model Usage:**

- **Voice Conversation**: Qwen3:8B (temp 0.7, max_tokens 60)
- **Coach Feedback**: Qwen3:8B (temp 0.5, max_tokens 200)
- **Coach Questions**: Qwen3:8B (temp 0.6, max_tokens 150)

All running on the **same local model** - no additional services needed!

---

## Benefits for Learning

### **1. Immediate Correction**
- Learn from mistakes instantly
- No waiting for a teacher to review
- Gentle, encouraging feedback

### **2. Pronunciation Guidance**
- Identifies specific words to practice
- IPA and stress pattern hints
- Improves spoken fluency

### **3. Context-Aware Help**
- Coach knows your conversation history
- Answers relate to what you just said
- Learn vocabulary and grammar in context

### **4. Conversation Flow Tips**
- Suggests what to say next
- Teaches natural progression
- Builds confidence in real situations

### **5. Safe Learning Environment**
- No judgment - AI is patient
- Ask "silly" questions freely
- Practice as much as you want

---

## Example Questions to Ask the Coach

### **Vocabulary:**
- "What does 'to go' mean?"
- "What's the difference between 'lunch' and 'dinner'?"
- "How do I say 'tap water' in Spanish?"

### **Grammar:**
- "Why did they use 'will' instead of 'going to'?"
- "When do I use 'can I get' vs 'I'll have'?"
- "Is 'more cheaper' correct?"

### **Pronunciation:**
- "How do I pronounce 'croissant'?"
- "Where's the stress in 'sandwich'?"
- "How do native speakers say 'water'?"

### **Culture & Usage:**
- "Is it rude to not say 'please'?"
- "Do Americans tip at cafes?"
- "What's a polite way to ask for no ice?"

### **Conversation:**
- "What should I say next?"
- "How do I politely ask for the check?"
- "What's another way to order this?"

---

## Comparison: With vs Without Coach

### **Without Coach:**
```
You: "Give me coffee"
AI: "Sure, what size?"
[You wonder if that was polite enough...]
[No feedback, just continue]
```

### **With Live Coach:**
```
You: "Give me coffee"
AI: "Sure, what size?"

Coach:
  Grammar: Fair
  Feedback: "Give me" can sound demanding. Try "Can I get" or "I'd like"
  💡 Try: "Can I get a coffee, please?"
  Conversation Tip: After they ask the size, specify small/medium/large

You can ask: "What's the most polite way to order?"
Coach: "Try 'Could I please have a [item]?' - 'could' is more polite
than 'can', and 'please' shows courtesy. In cafes, 'I'd like' or
'Can I get' are also friendly and common."
```

---

## Performance

### **Response Times:**

- **Voice conversation**: ~4-6 seconds
- **Auto feedback**: ~2-3 seconds (runs in parallel)
- **Question answers**: ~2-3 seconds

### **Resource Usage:**

- All processing on local machine
- Uses same Qwen3:8B model
- No additional downloads needed
- No cloud API calls

---

## Privacy

- **100% local processing**
- No data sent to external servers
- Full conversation history stays on your machine
- Safe for student practice

---

## Supported Languages

Currently supports:
- **English** (American)
- **Spanish** (Mexican)

Both automatic feedback and question answering work in both languages.

---

## Tips for Best Results

### **1. Speak Clearly**
- Whisper transcribes better with clear speech
- Pause briefly between sentences
- Reduce background noise

### **2. Ask Specific Questions**
- "How do I say X?" is better than "Help with vocabulary"
- Reference what was just said: "Why did they say that?"
- One question at a time for clearest answers

### **3. Review Feedback**
- Read the grammar corrections
- Practice the focus words
- Try the suggested rewrites

### **4. Use Conversation Tips**
- Follow the coach's suggestions
- Build on previous exchanges
- Practice the recommended phrases

---

## Troubleshooting

### **Feedback not appearing?**
1. Check voice backend logs: `tail -f /tmp/voice_backend.log`
2. Look for "Coach feedback" messages
3. Verify `/coach-feedback` endpoint is working

### **Questions not getting answered?**
1. Make sure question is typed clearly
2. Check if backend received it (look at logs)
3. Try rephrasing more specifically

### **Coach seems slow?**
1. Normal: 2-3 seconds per request
2. If longer, check Qwen3:8B model status: `ollama list`
3. Restart if needed: `pkill -f voice_backend && ./start-voice-demo.sh`

---

## Future Enhancements

Ideas for the roadmap:

- [ ] Pronunciation scoring (rate accuracy)
- [ ] Grammar error highlighting
- [ ] Vocabulary flashcards from conversation
- [ ] Progress tracking over time
- [ ] Conversation replay with notes
- [ ] Export learning summary
- [ ] Multi-turn conversation analysis
- [ ] Personalized difficulty adjustment

---

## Files Added/Modified

### **New Files:**
- `voice-chat-with-coach.html` - Split-screen interface with coach panel

### **Modified Files:**
- `voice_backend.py` - Added `/coach-feedback` and `/coach-question` endpoints
- `index.html` - Updated all voice buttons to use coach interface

---

## Demo Script for Teachers

**Opening (30 seconds):**
> "Now I'll show you something unique - a live AI coach that helps while you practice."

**Show Interface (1 minute):**
1. Open voice-chat-with-coach.html
2. Point out the two panels
3. Explain automatic feedback + ask questions

**Live Demo (2 minutes):**
1. Say: "I want coffee"
2. **Show automatic feedback** - grammar, pronunciation, tips
3. **Ask coach**: "What's a more polite way?"
4. **Show coach answer** - explains "I'd like" vs "I want"
5. **Try again**: "I'd like a coffee, please"
6. **Show improved feedback**: "Excellent! Natural cafe English"

**Highlight Value (1 minute):**
- Immediate correction
- Learn in context
- Ask anything anytime
- No judgment, infinite patience
- All local - private and fast

---

## Conclusion

The Live AI Coach transforms voice practice from simple conversation into **guided learning**. Students get:

- ✅ Real-time feedback
- ✅ On-demand help
- ✅ Pronunciation guidance
- ✅ Grammar corrections
- ✅ Conversation tips

All powered by the same local AI (Qwen3:8B) with no extra setup!

---

**w4ester & ai orchestration**
