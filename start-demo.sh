#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Cafe Language Learning - AI Demo Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Store the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo ""
    echo "📦 Please install Ollama:"
    echo "   Mac/Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "   Windows:   https://ollama.com/download/windows"
    echo ""
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "📦 Starting Ollama service..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
fi

# Check if Qwen3:8B is available
echo "🔍 Checking for Qwen3:8B model..."
if ! ollama list | grep -q "qwen3:8b"; then
    echo "⚠️  Qwen3:8B not found. Downloading..."
    echo "    Size: 5.2GB - This will take 3-5 minutes"
    echo ""
    ollama pull qwen3:8b
    if [ $? -ne 0 ]; then
        echo "❌ Failed to download Qwen3:8B"
        exit 1
    fi
fi
echo "✅ Qwen3:8B ready!"

# Check if Python dependencies are installed
echo "🔍 Checking Python dependencies..."
if ! python3 -c "import flask, faster_whisper, ollama" 2>/dev/null; then
    echo "⚠️  Installing Python dependencies..."
    pip3 install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        echo "   Try manually: pip3 install -r requirements.txt"
        exit 1
    fi
fi
echo "✅ Python dependencies installed!"

# Kill any existing backend on port 5000
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5000 already in use. Killing existing process..."
    kill $(lsof -t -i:5000) 2>/dev/null
    sleep 1
fi

# Kill any existing HTTP server on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 already in use. Killing existing process..."
    kill $(lsof -t -i:8000) 2>/dev/null
    sleep 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All systems ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start backend service in background
echo "🖥️  Starting AI backend service (Flask + Whisper + Qwen3)..."
python3 backend_service.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check /tmp/backend.log for details"
    cat /tmp/backend.log
    exit 1
fi
echo "✅ Backend running (PID: $BACKEND_PID)"

# Start HTTP server in background for frontend
echo "🌐 Starting HTTP server for frontend..."
python3 -m http.server 8000 > /tmp/httpserver.log 2>&1 &
HTTP_PID=$!
sleep 2

if ! ps -p $HTTP_PID > /dev/null; then
    echo "❌ HTTP server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi
echo "✅ HTTP server running (PID: $HTTP_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Demo is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend:  http://localhost:8000"
echo "🤖 Backend:   http://localhost:5000"
echo "💬 AI Model:  Qwen3:8B (multilingual)"
echo "🎤 Speech:    Whisper (medium)"
echo ""
echo "🌐 Opening demo in browser..."
echo ""

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8000/ai-chat-demo.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:8000/ai-chat-demo.html
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 Demo is running!"
echo ""
echo "   Press Ctrl+C to stop all services"
echo ""
echo "   Logs:"
echo "   - Backend:  tail -f /tmp/backend.log"
echo "   - Ollama:   tail -f /tmp/ollama.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛑 Shutting down demo..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Kill backend
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "   Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi

    # Kill HTTP server
    if ps -p $HTTP_PID > /dev/null 2>&1; then
        echo "   Stopping HTTP server (PID: $HTTP_PID)..."
        kill $HTTP_PID 2>/dev/null
    fi

    # Optionally stop Ollama (commented out - you might want to keep it running)
    # echo "   Stopping Ollama..."
    # pkill -f "ollama serve"

    echo ""
    echo "✅ All services stopped"
    echo "👋 Thanks for using the demo!"
    echo ""
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Wait for user interrupt
wait
