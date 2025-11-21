# 🌐 Remote Demo Setup Guide

## Quick Guide: Share Your Local AI Demo

Want others to try your language learning platform? Here's how to expose your local setup remotely.

---

## 🚀 Recommended: ngrok (Easiest)

### **Step 1: Install ngrok**

```bash
# Mac
brew install ngrok

# Windows
# Download from https://ngrok.com/download

# Linux
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok
```

### **Step 2: Get Free Account**

1. Sign up at https://dashboard.ngrok.com/signup
2. Copy your authtoken
3. Add it:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

### **Step 3: Start Your Backend**

```bash
# Terminal 1: Start the voice backend
./start-voice-demo.sh

# Wait for: "Voice backend running (PID: xxxxx)"
```

### **Step 4: Create Tunnel**

```bash
# Terminal 2: Create public URL
ngrok http 5001 --region us

# You'll see:
# Forwarding: https://abc123.ngrok-free.app -> http://localhost:5001
```

Copy that `https://abc123.ngrok-free.app` URL!

### **Step 5: Update Frontend**

**Option A: Quick Test (Manual Edit)**

Open `voice-chat-with-coach.html` and change:
```javascript
const API_BASE = 'http://localhost:5001';
```

To:
```javascript
const API_BASE = 'https://abc123.ngrok-free.app';  // Your ngrok URL
```

**Option B: Environment Variable (Recommended)**

Create `config.js`:
```javascript
// config.js
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:5001'
    : 'https://abc123.ngrok-free.app';  // Your ngrok URL
```

Then include in HTML:
```html
<script src="config.js"></script>
```

### **Step 6: Test It**

1. Open browser to your ngrok URL: `https://abc123.ngrok-free.app`
2. You should see the voice chat interface
3. Share this URL with others!

---

## 🔒 Alternative: Cloudflare Tunnel (Better for Longer Demos)

### **Why Cloudflare?**
- ✅ Free forever
- ✅ No time limits
- ✅ Faster than ngrok
- ✅ Can use custom domain

### **Setup:**

```bash
# Install
brew install cloudflare/cloudflare/cloudflared

# Login (one time)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create language-learning

# Start tunnel
cloudflared tunnel --url http://localhost:5001

# Or with config file:
cloudflared tunnel run language-learning
```

**Config file** (`~/.cloudflared/config.yml`):
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /Users/you/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: your-custom-domain.com  # Optional
    service: http://localhost:5001
  - service: http_status:404
```

---

## 🏠 Port Forwarding (If You Control Your Router)

### **Steps:**

1. Find your local IP:
   ```bash
   # Mac/Linux
   ipconfig getifaddr en0

   # Windows
   ipconfig
   ```

2. Log into your router (usually `192.168.1.1` or `192.168.0.1`)

3. Add port forwarding rule:
   - External Port: `5001`
   - Internal IP: Your computer's local IP
   - Internal Port: `5001`
   - Protocol: TCP

4. Find your public IP: Visit https://whatismyipaddress.com

5. Share: `http://YOUR_PUBLIC_IP:5001`

**⚠️ Security Note:**
- Only use for temporary demos
- Add firewall rules
- Consider using HTTPS (add reverse proxy like nginx)

---

## 📦 Deploy to Cloud (Permanent Solution)

### **Option 1: Railway (Easiest Cloud Deploy)**

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 5001

# Start backend
CMD ["python", "voice_backend.py"]
```

2. Create `railway.toml`:
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "python voice_backend.py"
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 10
```

3. Push to Railway:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

**⚠️ Note:** Railway doesn't support Ollama. You'll need to:
- Use OpenAI API instead of Ollama
- Or deploy to a VPS with GPU

### **Option 2: Hetzner Cloud CX22 (≈ $8/month)**

Looking for something under $10? Hetzner's **CX22** plan (2 vCPU / 8GB RAM / 80GB SSD) is €7.89/mo (~$8.50). Plenty for Qwen3:8B + Whisper.

1. Create server (Ubuntu 22.04) in Hetzner Cloud console
2. SSH in and install dependencies:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull Qwen3
   ollama pull qwen3:8b

   # Install project
   git clone https://github.com/w4ester/language-world-cafe.git
   cd language-world-cafe
   pip3 install -r requirements.txt

   # Start backend (can use tmux/systemd)
   python3 voice_backend.py
   ```

3. Add swap (Hetzner allows 8GB RAM but Qwen may spike):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

4. Secure with HTTPS using Caddy (auto Let's Encrypt):
   ```bash
   curl -fsSL https://getcaddy.com | bash -s personal

   sudo tee /etc/caddy/Caddyfile <<'EOF'
   your-domain.com {
       reverse_proxy localhost:5001
   }
   EOF

   sudo systemctl enable --now caddy
   ```

**Cost:** €7.89 + VAT (≈ $8-9) per month. Billed hourly; delete when not needed to save more.

### **Option 3: DigitalOcean Droplet (Full Control)**

1. Create droplet (Ubuntu 22.04, 8GB RAM minimum)
2. SSH in and install same stack as above
3. Configure nginx/Caddy for HTTPS

**Cost:** $48-96/month for 8GB+ RAM droplet (more expensive but US-based data centers)

---

## 🎯 Recommended Setup for Different Scenarios

### **Quick Demo (1-2 hours)**
✅ Use **ngrok**
- Free tier works
- 2 hour session limit
- New URL each time

### **Workshop/Class (Full Day)**
✅ Use **Cloudflare Tunnel**
- No time limits
- More reliable
- Better performance

### **Permanent Public Demo**
✅ Use **VPS** (DigitalOcean/Linode)
- Always available
- Custom domain
- Full control

### **Private Team Demo**
✅ Use **Tailscale Funnel**
- Share with specific people
- More secure
- No bandwidth limits

---

## 🔧 Testing Your Setup

### **Check Backend Health:**
```bash
# Replace with your tunnel URL
curl https://your-tunnel.ngrok-free.app/health

# Should return:
{
  "status": "healthy",
  "mode": "voice-conversation",
  "whisper_model": "base",
  "tts": "edge-tts"
}
```

### **Check CORS:**
```bash
curl -H "Origin: https://w4ester.github.io" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://your-tunnel.ngrok-free.app/voice-chat

# Should include: Access-Control-Allow-Origin: *
```

---

## 📝 Share Instructions for Demo Participants

**Template Message:**

```
🎤 Try the AI Language Learning Demo!

Live Demo: https://your-tunnel.ngrok-free.app/voice-chat-with-coach.html?scenario=server_only&lang=en

Features:
- Real-time voice conversation with local AI
- Instant grammar & pronunciation feedback
- Bilingual (English/Spanish)
- 100% privacy (local model)

How to use:
1. Click the link above
2. Allow microphone access
3. Press & hold the microphone button
4. Speak naturally in English or Spanish
5. Release to hear AI response
6. Ask the coach questions anytime!

Requirements:
- Modern browser (Chrome, Firefox, Safari)
- Microphone access
- Decent internet connection

Note: This is running on local AI (Qwen3:8B) via a tunnel to my laptop.
If it's slow, that's my Wi-Fi, not the AI! 😄
```

---

## 🐛 Troubleshooting

### **ngrok shows "ngrok not found"**
- Install: `brew install ngrok`
- Or download manually from https://ngrok.com/download

### **Backend not accessible through tunnel**
- Check backend is running: `lsof -i :5001`
- Test locally first: `curl http://localhost:5001/health`
- Check ngrok tunnel: Look for "Forwarding" line

### **CORS errors in browser**
- Verify `CORS(app, resources={r"/*": {"origins": "*"}})` in backend
- Check browser console for specific error
- Try incognito mode

### **Microphone not working**
- HTTPS required for microphone (ngrok provides this)
- User must grant permission
- Check browser settings

### **Slow responses**
- Normal: 4-6 seconds per exchange
- Check your upload speed (voice goes to your laptop)
- Consider using smaller Whisper model ("base" is fastest)

---

## 💡 Pro Tips

1. **Save your ngrok URL** in a text file - you'll need it every time

2. **Create a shell script** for quick startup:
   ```bash
   #!/bin/bash
   # demo-start.sh

   echo "🎤 Starting voice backend..."
   python3 voice_backend.py &
   BACKEND_PID=$!

   sleep 3

   echo "🌐 Creating public tunnel..."
   ngrok http 5001 --region us

   # Cleanup on exit
   trap "kill $BACKEND_PID" EXIT
   ```

3. **Use ngrok reserved domain** (paid plan) for consistent URL

4. **Monitor usage**: ngrok dashboard shows request logs

5. **Prepare for ngrok warning page**: Free tier shows warning first visit
   - Users must click "Visit Site"
   - Explain this in demo instructions

---

## 🎬 Full Demo Script

```bash
# Terminal 1: Start everything
./start-voice-demo.sh

# Terminal 2: Create tunnel
ngrok http 5001 --region us

# Copy the https://xxx.ngrok-free.app URL

# Update voice-chat-with-coach.html:
# Change API_BASE to your ngrok URL

# Start HTTP server for frontend
python3 -m http.server 8000

# Share with others:
# Frontend: https://w4ester.github.io/language-world-cafe/voice-chat-with-coach.html
# (Make sure to update API_BASE in the GitHub Pages version)
```

---

w4ester & ai orchestration
