Here's the complete README.md, ready to copy-paste:

```markdown
# AI Interview Assistant

A fully local, offline AI-powered interview assistant for Windows.
Listens to your interview audio, detects questions, and shows
AI-generated answers in a transparent floating overlay —
invisible during screen sharing.

---

## Features

- Real-time speech-to-text (Faster Whisper)
- Automatic question detection and classification
- AI answer generation (Ollama — fully offline)
- Transparent overlay (always on top, invisible in screen share)
- Resume-aware personalized answers (RAG)
- Conversation memory across the interview
- Analytics dashboard
- PDF report export

---

## Requirements

- Windows 10 build 19041 or later
- Python 3.10+
- 8GB RAM minimum (16GB recommended)
- Ollama installed

---

## Installation

### Step 1 — Clone the project

```
git clone <your-repo-url>
cd ai-interview-assistant
```

### Step 2 — Install Python dependencies

```
python -m pip install -r requirements.txt
```

### Step 3 — Install Ollama

Download from https://ollama.com/download and install.

Then pull the model:

```
ollama pull llama3.2
```

### Step 4 — Run the app

```
python main.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| CTRL+SHIFT+A | Hide / Show overlay |
| CTRL+SHIFT+T | Toggle transcript panel |
| CTRL+SHIFT+M | Mute / Unmute microphone |
| CTRL+SHIFT+Q | Quit application |

---

## Build Windows EXE

```
python -m pip install pyinstaller
pyinstaller build.spec
```

Output: `dist/AIInterviewAssistant.exe`

---

## Project Structure

```
ai-interview-assistant/
├── backend/
│   ├── audio/          # Mic capture
│   ├── transcriber/    # Faster Whisper STT
│   ├── llm/            # Ollama answer engine
│   ├── memory/         # Conversation memory + SQLite
│   ├── rag/            # Resume RAG (ChromaDB)
│   ├── utils/          # Logger, PDF exporter
│   └── pipeline.py     # Full pipeline orchestrator
├── frontend/
│   ├── overlay/        # Transparent overlay window
│   └── dashboard/      # Analytics dashboard
├── database/           # SQLite DB
├── reports/            # Generated PDF reports
├── models/             # Resume PDF storage
├── tests/              # All phase tests
├── main.py             # Entry point
└── build.spec          # PyInstaller config
```

---

## How It Works

```
Microphone
    ↓
Faster Whisper (speech-to-text)
    ↓
Question Detector (category + topic)
    ↓
Ollama LLM + Resume RAG + Memory
    ↓
Floating Overlay (invisible in screen share)
```

---

## Privacy

- 100% offline — zero internet calls
- No telemetry or analytics pings
- All data stays on your machine
- Resume embeddings stored locally in ChromaDB
```