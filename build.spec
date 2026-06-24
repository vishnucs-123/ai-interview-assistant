# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for AI Interview Assistant.
Run: pyinstaller build.spec
Output: dist/AIInterviewAssistant.exe
"""

import sys
from pathlib import Path

block_cipher = None

# Collect all hidden imports PyInstaller misses
hidden_imports = [
    # FastAPI / networking
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",

    # Audio
    "sounddevice",
    "pyaudio",
    "pydub",

    # Whisper
    "faster_whisper",
    "ctranslate2",

    # Ollama
    "ollama",

    # ChromaDB
    "chromadb",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
    "sentence_transformers",

    # PDF
    "reportlab",
    "reportlab.platypus",
    "reportlab.lib",
    "PyPDF2",

    # DB
    "sqlalchemy",

    # PyQt6
    "PyQt6",
    "PyQt6.QtWidgets",
    "PyQt6.QtCore",
    "PyQt6.QtGui",

    # Matplotlib
    "matplotlib",
    "matplotlib.backends.backend_qtagg",

    # Project modules
    "backend",
    "backend.audio",
    "backend.audio.audio_capture",
    "backend.audio.audio_config",
    "backend.transcriber",
    "backend.transcriber.transcriber",
    "backend.transcriber.question_detector",
    "backend.llm",
    "backend.llm.answer_engine",
    "backend.memory",
    "backend.memory.conversation_memory",
    "backend.memory.memory_store",
    "backend.rag",
    "backend.rag.resume_loader",
    "backend.rag.resume_rag",
    "backend.utils",
    "backend.utils.logger",
    "backend.utils.pdf_exporter",
    "backend.pipeline",
    "frontend",
    "frontend.overlay",
    "frontend.overlay.overlay_window",
    "frontend.overlay.capture_exclude",
    "frontend.dashboard",
    "frontend.dashboard.dashboard_window",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Include model configs
        ("models", "models"),
        # Include database folder
        ("database", "database"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "test",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AIInterviewAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add icon.ico here if you have one
    onefile=True,           # Single .exe file
)