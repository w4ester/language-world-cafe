#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎤 Voice Conversation Demo - Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Store the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "📦 Starting Ollama service..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
fi

# Check if qwen3:8b is available
if ! ollama list | grep -q "qwen3:8b"; then
    echo "❌ Qwen3:8B not found!"
    echo "   Run: ollama pull qwen3:8b"
    exit 1
fi

echo "✅ Qwen3:8B ready!"

# Kill existing processes on ports
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Voice Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start voice backend
echo "🎤 Starting voice backend (Flask + Whisper + Edge-TTS + Qwen3)..."
python3 voice_backend.py > /tmp/voice_backend.log 2>&1 &
VOICE_PID=$!
sleep 3

if ! ps -p $VOICE_PID > /dev/null; then
    echo "❌ Voice backend failed to start"
    cat /tmp/voice_backend.log
    exit 1
fi
echo "✅ Voice backend running (PID: $VOICE_PID)"

# Start HTTP server
echo "🌐 Starting HTTP server..."
python3 -m http.server 8000 > /tmp/httpserver.log 2>&1 &
HTTP_PID=$!
sleep 2

if ! ps -p $HTTP_PID > /dev/null; then
    echo "❌ HTTP server failed"
    exit 1
fi
echo "✅ HTTP server running (PID: $HTTP_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Voice Demo Ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend:     http://localhost:8000/voice-chat-with-coach.html"
echo "🎤 Voice API:    http://localhost:5001"
echo "💬 AI Model:     Qwen3:8B"
echo "🗣️  TTS:          Edge-TTS (human-like voices)"
echo "👂 STT:          Whisper (base model)"
echo ""
echo "🌐 Opening voice chat..."
echo ""

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8000/voice-chat-with-coach.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:8000/voice-chat-with-coach.html
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 Demo is running!"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
echo "   Logs:"
echo "   - Voice:  tail -f /tmp/voice_backend.log"
echo "   - Ollama: tail -f /tmp/ollama.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."

    if ps -p $VOICE_PID > /dev/null 2>&1; then
        kill $VOICE_PID 2>/dev/null
    fi

    if ps -p $HTTP_PID > /dev/null 2>&1; then
        kill $HTTP_PID 2>/dev/null
    fi

    echo "✅ All services stopped"
    exit 0
}

trap cleanup INT TERM
wait
