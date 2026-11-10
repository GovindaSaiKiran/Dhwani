# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Playful Neo-Humanist Minimalist Web Console for Artemis Voice OS.

Inspired by modern design software (Figma, Notion, Craft):
- Pure white backdrop (#FFFFFF), ultra-light borders (#F1F3F5, #E2E8F0)
- Tight ultra-bold display typography (Plus Jakarta Sans)
- Tactile candy-colored interactive components & tokens
- Pan-Indian Multilingual Support (Telugu, Tamil, Kannada, Hindi, Marathi, Odia, English)
- Interactive Confirmation & Disambiguation Banner with [Yes, Proceed] & [No, Cancel]
- Non-blocking real-time streaming subprocess of voice_commander.py
- Live synchronization with user_memory.json & device contacts
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time

from flask import Flask, jsonify, render_template_string, request
from flask_socketio import SocketIO, emit
import requests

# ==============================================================================
# Configuration & Paths
# ==============================================================================
WORKSPACE_DIR = Path(r"C:\Users\Asus\Downloads\Artemis").resolve()
VENV_PYTHON = WORKSPACE_DIR / "artemis" / ".venv" / "Scripts" / "python.exe"
PYTHON_BIN = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
VOICE_COMMANDER_SCRIPT = WORKSPACE_DIR / "voice_commander.py"
MEMORY_FILE = WORKSPACE_DIR / "user_memory.json"
ADB_BIN = (
    shutil.which("adb")
    or os.getenv("ADB_PATH")
    or r"C:\Users\Asus\Downloads\Android\platform-tools-latest-windows\platform-tools\adb.exe"
    or "adb"
)

def get_connected_devices() -> list:
    """Discover all connected ADB devices and emulators."""
    devices = []
    try:
        env = os.environ.copy()
        env["ANDROID_USER_HOME"] = str(WORKSPACE_DIR / ".android")
        res = subprocess.run([ADB_BIN, "devices", "-l"], capture_output=True, text=True, check=False, env=env, timeout=3)
        for line in res.stdout.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                serial = parts[0]
                model = "Android Device"
                for p in parts[2:]:
                    if p.startswith("model:"):
                        model = p.split(":", 1)[1].replace("_", " ")
                is_emu = serial.startswith("emulator-")
                devices.append({
                    "serial": serial,
                    "model": model,
                    "is_emulator": is_emu,
                    "label": f"{'🖥️ Emulator' if is_emu else '📱 Device'} ({serial} • {model})"
                })
    except Exception:
        pass
    return devices

def get_default_device() -> str:
    env_target = os.getenv("TARGET_DEVICE_SERIAL")
    if env_target:
        return env_target
    devs = get_connected_devices()
    for d in devs:
        if d.get("is_emulator"):
            return d["serial"]
    if devs:
        return devs[0]["serial"]
    return "emulator-5554"

TARGET_DEVICE_SERIAL = get_default_device()

app = Flask(__name__)
app.config["SECRET_KEY"] = "artemis-neo-humanist-design-console-2026"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

execution_lock = threading.Lock()
current_process = None


# ==============================================================================
# Memory Vault Helper Functions
# ==============================================================================
def load_memory_vault() -> dict:
    """Read structured user contacts and profile from user_memory.json."""
    if not MEMORY_FILE.exists():
        default_mem = {
            "profile": {},
            "contacts": {},
            "addresses": {},
            "notes": {},
        }
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(default_mem, f, indent=2, ensure_ascii=False)
            return default_mem
        except Exception:
            return default_mem

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "contacts": {}, "profile": {}}


# ==============================================================================
# Subprocess Runner with Unbuffered Line-by-Line Streaming
# ==============================================================================
def run_voice_commander_streaming(cmd_args: list, mode_name: str = "LIVE"):
    """Execute voice_commander.py in a background thread and stream outputs via SocketIO."""
    global current_process
    with execution_lock:
        socketio.emit("tx_start", {"mode": mode_name})
        socketio.emit("log_event", {
            "type": "SYS",
            "line": f"Broadcast engaged [{mode_name}] // Device: {TARGET_DEVICE_SERIAL}",
            "timestamp": time.strftime("%H:%M:%S")
        })

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["ANDROID_USER_HOME"] = str(WORKSPACE_DIR / ".android")

        actual_args = list(cmd_args)
        if "--device" not in actual_args and "-d" not in actual_args:
            actual_args = ["--device", TARGET_DEVICE_SERIAL] + actual_args
        full_cmd = [PYTHON_BIN, "-u", str(VOICE_COMMANDER_SCRIPT)] + actual_args

        try:
            current_process = subprocess.Popen(
                full_cmd,
                cwd=str(WORKSPACE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                encoding="utf-8",
                errors="replace"
            )

            for raw_line in iter(current_process.stdout.readline, ""):
                if not raw_line:
                    break
                line = raw_line.strip()
                if not line:
                    continue

                ts = time.strftime("%H:%M:%S")
                log_type = "STREAM"

                # 1. Interactive Disambiguation / User Confirmation Check
                if "[Ask-User]" in line:
                    log_type = "CONFIRM"
                    q_match = re.search(r"\[Ask-User\]\s*(.+)", line)
                    question = q_match.group(1).strip() if q_match else line
                    socketio.emit("ask_user_confirmation", {"question": question})

                # 2. STT Speech Decoded
                elif "Transcribed:" in line or "Transcribed (" in line:
                    log_type = "STT"
                    match = re.search(r'Transcribed(?:\s*\([^\)]*\))?:\s*["\']?([^"\']+)["\']?', line)
                    if match:
                        decoded_speech = match.group(1).strip()
                        socketio.emit("speech_decoded", {"text": decoded_speech})
                elif "[Microphone:VAD]" in line or "[Recording]" in line or "Listening with auto-silence" in line:
                    log_type = "STT"
                    socketio.emit("recording_active", {"vad": True})
                elif "Auto-silence cutoff" in line or "Recording finished" in line or "Max timeout reached" in line:
                    log_type = "STT"
                    socketio.emit("recording_finished", {})

                # 3. Fast-Path ADB Action
                elif "Fast-Path" in line or "⚡" in line or "Instant" in line or "[Fast-Path]" in line or "[Router:Fast]" in line or "[Router:Call]" in line or "[Router:WhatsApp]" in line:
                    log_type = "FAST"
                    socketio.emit("routing_state", {
                        "mode": "FAST",
                        "label": "⚡ 12ms Fast ADB Intent",
                        "color": "#22C55E",
                        "badge": "FAST ADB"
                    })

                # 4. Artemis Vision Fallback
                elif "Artemis" in line or "Autonomous" in line or "Dispatching" in line or "Flash Turn" in line:
                    log_type = "ARTEMIS"
                    socketio.emit("routing_state", {
                        "mode": "ARTEMIS",
                        "label": "🤖 Artemis Flash Vision",
                        "color": "#F59E0B",
                        "badge": "VISION AGENT"
                    })

                # 5. TTS Feedback
                elif "Synthesizing:" in line or "Synthesizing (" in line or "[TTS]" in line:
                    log_type = "TTS"
                    match = re.search(r'Synthesizing(?:\s*\([^\)]*\))?:\s*["\']?([^"\']+)["\']?', line)
                    if match:
                        tts_text = match.group(1).strip()
                        socketio.emit("tts_event", {"text": tts_text})

                # 6. Memory updates
                elif "[Memory]" in line:
                    log_type = "MEMORY"
                    updated_mem = load_memory_vault()
                    socketio.emit("memory_updated", updated_mem)

                # Mirror to server terminal
                print(f"[{ts}] [{log_type}] {line}", flush=True)

                # Emit to connected browser client
                socketio.emit("log_event", {
                    "type": log_type,
                    "line": line,
                    "timestamp": ts
                })

            current_process.stdout.close()
            ret_code = current_process.wait()

            status_str = "Completed cleanly" if ret_code == 0 else f"Exit code {ret_code}"
            socketio.emit("log_event", {
                "type": "SYS",
                "line": f"Execution finished ({status_str})",
                "timestamp": time.strftime("%H:%M:%S")
            })

        except Exception as e:
            socketio.emit("log_event", {
                "type": "ERROR",
                "line": f"Subprocess fault: {str(e)}",
                "timestamp": time.strftime("%H:%M:%S")
            })
        finally:
            current_process = None
            socketio.emit("tx_complete", {})
            socketio.emit("memory_updated", load_memory_vault())


# ==============================================================================
# HTML Template: Neo-Humanist Modern Design Console
# ==============================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Artemis Voice OS // Galaxy A36</title>
  
  <!-- Modern Clean Typography: Plus Jakarta Sans & JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>

  <style>
    /* ==========================================================================
       NEO-HUMANIST MINIMALIST PLAYFUL DESIGN SYSTEM
       Pure White Canvas | Tight Bold Headlines | Tactile Candy Tokens
       ========================================================================== */
    :root {
      --bg-canvas: #FFFFFF;
      --bg-surface: #F8FAFC;
      --bg-subtle: #F1F5F9;
      --border-subtle: #F1F3F5;
      --border-strong: #E2E8F0;
      
      --ink-primary: #0F172A;
      --ink-secondary: #475569;
      --ink-tertiary: #94A3B8;

      /* Playful Candy Accent Tokens */
      --blue-500: #3B82F6;
      --blue-100: #EFF6FF;
      --blue-600: #2563EB;

      --lime-500: #22C55E;
      --lime-100: #F0FDF4;
      --lime-600: #16A34A;

      --amber-500: #F59E0B;
      --amber-100: #FEF3C7;
      --amber-600: #D97706;

      --rose-500: #EC4899;
      --rose-100: #FDF2F8;
      
      --purple-500: #8B5CF6;
      --purple-100: #F5F3FF;

      --shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 16px -2px rgba(15, 23, 42, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.04);
      --shadow-lg: 0 12px 32px -4px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.03);
      --shadow-candy: 0 6px 20px -3px rgba(59, 130, 246, 0.25);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    body {
      background-color: var(--bg-canvas);
      background-image: radial-gradient(#E2E8F0 1.2px, transparent 1.2px);
      background-size: 28px 28px;
      color: var(--ink-primary);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 20px;
    }

    /* Main Responsive Container */
    .app-shell {
      width: 100%;
      max-width: 1080px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* ==========================================================================
       TOP BAR & HEADER NAVIGATION
       ========================================================================== */
    .top-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 0;
      flex-wrap: wrap;
      gap: 12px;
    }

    .brand-mark {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 19px;
      letter-spacing: -0.03em;
      color: var(--ink-primary);
    }

    .brand-logo-disc {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 16px;
      box-shadow: 0 3px 10px rgba(59, 130, 246, 0.3);
    }

    .device-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      color: var(--ink-secondary);
    }

    .device-badge .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--lime-500);
      box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
      animation: pulse-ring 2s infinite;
    }

    @keyframes pulse-ring {
      0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5); }
      70% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
      100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    .header-pills {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .status-pill {
      font-size: 11px;
      font-weight: 700;
      padding: 5px 12px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 5px;
      letter-spacing: -0.01em;
    }
    .status-pill.blue { background: var(--blue-100); color: var(--blue-600); }
    .status-pill.amber { background: var(--amber-100); color: var(--amber-600); }
    .status-pill.green { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }

    /* ==========================================================================
       LANGUAGE SELECTOR BAR (PAN-INDIAN)
       ========================================================================== */
    .lang-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      padding: 6px 12px;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 9999px;
      width: fit-content;
      box-shadow: var(--shadow-sm);
    }

    .lang-label {
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--ink-tertiary);
      margin-right: 4px;
    }

    .lang-pill {
      padding: 5px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      color: var(--ink-secondary);
      background: transparent;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .lang-pill:hover {
      color: var(--ink-primary);
      background: #FFFFFF;
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }
    .lang-pill.active {
      color: #FFFFFF;
      background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
      border-color: transparent;
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
    }

    /* ==========================================================================
       HERO COMMAND & SPEECH UNIT
       ========================================================================== */
    .hero-card {
      background: var(--bg-canvas);
      border: 1px solid var(--border-strong);
      border-radius: 28px;
      padding: 32px 36px;
      box-shadow: var(--shadow-md);
      display: flex;
      flex-direction: column;
      gap: 20px;
      position: relative;
      overflow: hidden;
    }

    .hero-headline {
      font-size: 34px;
      font-weight: 800;
      letter-spacing: -0.04em;
      line-height: 1.2;
      color: var(--ink-primary);
    }

    .token-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      vertical-align: middle;
      padding: 2px 14px;
      border-radius: 9999px;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.02em;
      box-shadow: var(--shadow-sm);
    }
    .token-pill.mic {
      background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
      color: white;
    }
    .token-pill.device {
      background: linear-gradient(135deg, #22C55E 0%, #4ADE80 100%);
      color: white;
    }

    /* Live Transcript Bubble */
    .transcript-box {
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 20px;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: all 0.25s ease;
    }
    .transcript-box.active {
      border-color: #93C5FD;
      background: #F8FAFF;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
    }

    .transcript-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .transcript-tag {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--ink-tertiary);
    }

    .route-candy-tag {
      font-size: 12px;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 9999px;
      background: var(--bg-subtle);
      color: var(--ink-secondary);
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s ease;
    }
    .route-candy-tag.fast {
      background: #DCFCE7;
      color: #15803D;
      border: 1px solid #86EFAC;
    }
    .route-candy-tag.artemis {
      background: #FEF3C7;
      color: #B45309;
      border: 1px solid #FCD34D;
    }

    .transcript-content {
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.03em;
      color: var(--ink-primary);
      min-height: 40px;
      word-break: break-word;
    }
    .transcript-content.placeholder {
      color: #94A3B8;
      font-weight: 500;
    }

    /* ==========================================================================
       INTERACTIVE DISAMBIGUATION / CONFIRMATION BANNER
       ========================================================================== */
    .confirmation-banner {
      background: #FFFBEB;
      border: 1.5px solid #F59E0B;
      border-radius: 18px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.15);
      animation: banner-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    @keyframes banner-pop {
      0% { opacity: 0; transform: translateY(-8px) scale(0.98); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    .confirm-content {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .confirm-icon {
      font-size: 26px;
      line-height: 1;
    }
    .confirm-title {
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #B45309;
    }
    .confirm-question {
      font-size: 15px;
      font-weight: 700;
      color: #78350F;
      margin-top: 2px;
    }

    .confirm-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .btn-confirm-yes {
      background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
      color: white;
      border: none;
      border-radius: 9999px;
      padding: 8px 18px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 8px rgba(34, 197, 94, 0.35);
      transition: all 0.15s ease;
    }
    .btn-confirm-yes:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.45);
    }
    .btn-confirm-no {
      background: #FFFFFF;
      border: 1px solid #CBD5E1;
      color: #475569;
      border-radius: 9999px;
      padding: 8px 18px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-confirm-no:hover {
      background: #FEE2E2;
      border-color: #FECDD3;
      color: #DC2626;
      transform: translateY(-1px);
    }

    /* ==========================================================================
       TACTILE TRANSMITTER & CONTROLS ROW
       ========================================================================== */
    .transmitter-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
      padding-top: 4px;
    }

    .tactile-toggle-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .pill-transmitter {
      width: 230px;
      height: 56px;
      background: var(--bg-subtle);
      border: 2px solid var(--border-strong);
      border-radius: 9999px;
      padding: 3px;
      display: flex;
      align-items: center;
      cursor: pointer;
      position: relative;
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      user-select: none;
    }
    .pill-transmitter:hover {
      border-color: #CBD5E1;
      transform: translateY(-1px);
    }
    .pill-transmitter:active {
      transform: translateY(1px);
    }

    .pill-thumb {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 20px;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
      transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s ease;
    }

    .pill-label {
      flex: 1;
      text-align: center;
      font-size: 14px;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: var(--ink-secondary);
      padding-right: 12px;
      transition: color 0.2s ease;
    }

    /* Active Listening State for Pill Transmitter */
    .pill-transmitter.transmitting {
      background: #DCFCE7;
      border-color: #86EFAC;
      box-shadow: 0 0 24px rgba(34, 197, 94, 0.25);
    }
    .pill-transmitter.transmitting .pill-thumb {
      transform: translateX(170px);
      background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
      box-shadow: 0 0 16px rgba(34, 197, 94, 0.6);
    }
    .pill-transmitter.transmitting .pill-label {
      color: #15803D;
      padding-left: 14px;
      padding-right: 0;
    }

    /* Tactile Stop / Cancel Button */
    .btn-stop-task {
      display: none;
      align-items: center;
      gap: 6px;
      background: #FEE2E2;
      border: 1px solid #FECDD3;
      border-radius: 9999px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 700;
      color: #DC2626;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(220, 38, 38, 0.15);
      transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      user-select: none;
    }
    .btn-stop-task.active {
      display: inline-flex;
      animation: stop-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .btn-stop-task:hover {
      background: #FCA5A5;
      color: #991B1B;
      transform: translateY(-2px) scale(1.03);
      box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
    }
    .btn-stop-task:active {
      transform: translateY(1px);
    }
    .stop-icon {
      font-size: 13px;
    }

    @keyframes stop-pop {
      0% { opacity: 0; transform: scale(0.85); }
      100% { opacity: 1; transform: scale(1); }
    }

    /* Soundwave Equalizer Dots */
    .soundwave-cluster {
      display: flex;
      align-items: center;
      gap: 4px;
      height: 28px;
    }
    .wave-bar {
      width: 4px;
      height: 6px;
      border-radius: 9999px;
      background: #CBD5E1;
      transition: height 0.15s ease, background 0.2s ease;
    }
    .soundwave-cluster.active .wave-bar {
      background: #22C55E;
      animation: wave-bounce 0.8s infinite ease-in-out alternate;
    }
    .soundwave-cluster.active .wave-bar:nth-child(1) { animation-delay: 0.1s; }
    .soundwave-cluster.active .wave-bar:nth-child(2) { animation-delay: 0.3s; }
    .soundwave-cluster.active .wave-bar:nth-child(3) { animation-delay: 0.15s; }
    .soundwave-cluster.active .wave-bar:nth-child(4) { animation-delay: 0.4s; }
    .soundwave-cluster.active .wave-bar:nth-child(5) { animation-delay: 0.25s; }

    @keyframes wave-bounce {
      0% { height: 6px; }
      100% { height: 26px; }
    }

    /* Sleek Manual Prompt Bar */
    .prompt-input-bar {
      flex: 1;
      min-width: 280px;
      display: flex;
      align-items: center;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 9999px;
      padding: 4px 6px 4px 18px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s ease;
    }
    .prompt-input-bar:focus-within {
      border-color: #3B82F6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
      background: #FFFFFF;
    }
    .prompt-input-bar input {
      flex: 1;
      border: none;
      background: transparent;
      outline: none;
      font-size: 14px;
      font-family: inherit;
      color: var(--ink-primary);
    }
    .prompt-input-bar input::placeholder {
      color: var(--ink-tertiary);
    }
    .btn-run {
      background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
      color: white;
      border: none;
      border-radius: 9999px;
      padding: 8px 18px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    .btn-run:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .btn-run:active {
      transform: translateY(1px);
    }

    /* ==========================================================================
       PLAYFUL QUICK-ACTION CANDY TOYS
       ========================================================================== */
    .quick-actions-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      padding-top: 6px;
    }

    .action-pill {
      font-size: 13px;
      font-weight: 700;
      padding: 8px 16px;
      border-radius: 9999px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      user-select: none;
      border: 1px solid transparent;
    }
    .action-pill:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .action-pill:active {
      transform: translateY(1px);
    }

    .pill-blue   { background: #EFF6FF; color: #2563EB; border-color: #DBEAFE; }
    .pill-green  { background: #F0FDF4; color: #16A34A; border-color: #DCFCE7; }
    .pill-amber  { background: #FEF3C7; color: #D97706; border-color: #FDE68A; }
    .pill-rose   { background: #FDF2F8; color: #DB2777; border-color: #FCE7F3; }
    .pill-purple { background: #F5F3FF; color: #7C3AED; border-color: #EDE9FE; }
    .pill-cyan   { background: #ECFEFF; color: #0891B2; border-color: #CFFAFE; }
    .pill-slate  { background: #F1F5F9; color: #475569; border-color: #E2E8F0; }

    /* ==========================================================================
       TWO-COLUMN DASHBOARD GRID
       ========================================================================== */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }

    @media (max-width: 860px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
    }

    .card-panel {
      background: var(--bg-canvas);
      border: 1px solid var(--border-strong);
      border-radius: 24px;
      padding: 24px;
      box-shadow: var(--shadow-md);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .panel-title {
      font-size: 17px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--ink-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-sync {
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 9999px;
      padding: 4px 12px;
      font-size: 12px;
      font-weight: 600;
      color: var(--ink-secondary);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-sync:hover {
      background: #FFFFFF;
      color: var(--blue-600);
      border-color: #BFDBFE;
    }

    /* Contacts List & Profile Badges */
    .contacts-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 280px;
      overflow-y: auto;
      padding-right: 4px;
    }
    .contacts-list::-webkit-scrollbar {
      width: 4px;
    }
    .contacts-list::-webkit-scrollbar-thumb {
      background: #E2E8F0;
      border-radius: 4px;
    }

    .contact-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .contact-item:hover {
      border-color: #CBD5E1;
      background: #FFFFFF;
      transform: translateX(2px);
      box-shadow: var(--shadow-sm);
    }

    .contact-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .avatar-disc {
      width: 36px;
      height: 36px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 800;
      font-size: 14px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .contact-details {
      display: flex;
      flex-direction: column;
    }
    .contact-name {
      font-weight: 700;
      font-size: 14px;
      color: var(--ink-primary);
      text-transform: capitalize;
    }
    .contact-meta {
      font-size: 12px;
      color: var(--ink-tertiary);
    }

    .contact-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .mini-pill-btn {
      background: #FFFFFF;
      border: 1px solid var(--border-strong);
      border-radius: 9999px;
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 700;
      color: var(--ink-secondary);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .mini-pill-btn:hover {
      background: var(--blue-100);
      border-color: #BFDBFE;
      color: var(--blue-600);
    }

    .btn-del {
      background: #FFFFFF;
      border: 1px solid var(--border-strong);
      border-radius: 9999px;
      width: 24px;
      height: 24px;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 700;
      color: #94A3B8;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-del:hover {
      background: #FEE2E2;
      border-color: #FECDD3;
      color: #DC2626;
      transform: scale(1.08);
    }

    /* ==========================================================================
       INSPECTOR & SERIAL TERMINAL
       ========================================================================== */
    .terminal-container {
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: 18px;
      padding: 12px;
      height: 280px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .terminal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 8px;
    }

    .terminal-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      color: var(--ink-secondary);
    }

    .terminal-logs {
      flex: 1;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      line-height: 1.6;
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding-right: 4px;
    }
    .terminal-logs::-webkit-scrollbar {
      width: 4px;
    }
    .terminal-logs::-webkit-scrollbar-thumb {
      background: #E2E8F0;
      border-radius: 4px;
    }

    .log-entry {
      display: flex;
      align-items: baseline;
      gap: 8px;
      word-break: break-word;
    }
    .log-ts {
      color: var(--ink-tertiary);
      font-size: 10px;
      min-width: 55px;
    }

    .log-badge {
      font-size: 9px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .log-badge.STT     { background: #E0F2FE; color: #0369A1; }
    .log-badge.FAST    { background: #DCFCE7; color: #15803D; font-weight: 800; }
    .log-badge.ARTEMIS { background: #FEF3C7; color: #B45309; }
    .log-badge.TTS     { background: #F3E8FF; color: #7E22CE; }
    .log-badge.SYS     { background: #F1F5F9; color: #475569; }
    .log-badge.CONFIRM { background: #FEF3C7; color: #D97706; font-weight: 800; }
    .log-badge.ERROR   { background: #FEE2E2; color: #DC2626; font-weight: 800; }
    .log-badge.STREAM  { background: #F1F5F9; color: #64748B; }

    .log-text {
      color: var(--ink-primary);
      flex: 1;
    }
  </style>
</head>
<body>

  <div class="app-shell">

    <!-- TOP BAR -->
    <header class="top-header">
      <div class="brand-mark">
        <div class="brand-logo-disc">🎙️</div>
        <span>Dhwani</span>
        <div class="device-badge" style="padding: 2px 10px;">
          <div class="pulse-dot"></div>
          <select id="deviceSelector" style="background: transparent; border: none; font-size: 11px; font-weight: 700; color: #1E293B; cursor: pointer; outline: none;">
            <option value="emulator-5554">🖥️ Emulator (emulator-5554)</option>
            <option value="RZGL52YX8DD">📱 Physical Phone</option>
          </select>
        </div>
      </div>

      <div class="header-pills">
        <div id="voiceStopBadge" class="status-pill green" title="Voice Barge-In: Say 'Stop' or 'Cancel' at any time to halt task">🎙️ Voice Stop: Active</div>
        <div class="status-pill blue">Prisma v3.0 STT</div>
        <div class="status-pill amber">OpenRouter 2.5 Flash</div>
      </div>
    </header>

    <!-- PAN-INDIAN LANGUAGE SELECTOR BAR -->
    <div class="lang-bar">
      <span class="lang-label">Language:</span>
      <button class="lang-pill active" data-lang="en-IN">English EN</button>
      <button class="lang-pill" data-lang="te-IN">తెలుగు TE</button>
      <button class="lang-pill" data-lang="ta-IN">தமிழ் TA</button>
      <button class="lang-pill" data-lang="kn-IN">ಕನ್ನಡ KN</button>
      <button class="lang-pill" data-lang="hi-IN">हिन्दी HI</button>
      <button class="lang-pill" data-lang="mr-IN">मराठी MR</button>
      <button class="lang-pill" data-lang="or-IN">ଓଡ଼ିଆ OR</button>
    </div>

    <!-- HERO LIVE COMMAND & TRANSCRIPT CARD -->
    <section class="hero-card">
      <div class="hero-headline">
        voice <span class="token-pill mic">🎙️ live</span> every <span class="token-pill device">📱 Galaxy A36</span> action.
      </div>

      <!-- Live Transcribed Speech Unit -->
      <div id="transcriptBox" class="transcript-box">
        <div class="transcript-header">
          <span class="transcript-tag">Live Spoken Transcript</span>
          <div id="routeBadge" class="route-candy-tag">
            <span>● Standby</span>
          </div>
        </div>

        <div id="transcriptText" class="transcript-content placeholder">
          Tap the transmitter or type a command below...
        </div>
      </div>

      <!-- Interactive Disambiguation & Confirmation Banner -->
      <div id="confirmationBanner" class="confirmation-banner" style="display: none;">
        <div class="confirm-content">
          <div class="confirm-icon">🔔</div>
          <div class="confirm-text-wrap">
            <div class="confirm-title">Confirmation Required</div>
            <div id="confirmQuestion" class="confirm-question">Please confirm your action...</div>
          </div>
        </div>
        <div class="confirm-actions">
          <button id="btnConfirmYes" class="btn-confirm-yes" onclick="answerConfirmation('Yes')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Yes, Proceed
          </button>
          <button id="btnConfirmNo" class="btn-confirm-no" onclick="answerConfirmation('No')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            No, Cancel
          </button>
        </div>
      </div>

      <!-- Transmitter & Manual Prompt Bar -->
      <div class="transmitter-row">
        <div class="tactile-toggle-wrap">
          <!-- Oversized Pill Toggle Switch -->
          <div id="pillTransmitter" class="pill-transmitter" title="Click to Speak / Click to Stop [Space]">
            <div class="pill-thumb">🎙️</div>
            <div id="pillLabel" class="pill-label">Push to Talk [Space]</div>
          </div>

          <!-- Tactile Stop / Cancel Button -->
          <button id="btnStopTask" class="btn-stop-task" title="Stop recording or cancel active task [Esc]">
            <span class="stop-icon">⏹</span>
            <span>Stop [Esc]</span>
          </button>

          <!-- Soundwave Equalizer -->
          <div id="soundwave" class="soundwave-cluster">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
          </div>
        </div>

        <!-- Sleek Manual Search/Command Bar -->
        <div class="prompt-input-bar">
          <input type="text" id="promptInput" placeholder="Type prompt (e.g. 'call nanna', 'open zepto')...">
          <button id="btnRunPrompt" class="btn-run">Run ↵</button>
        </div>
      </div>

      <!-- Floating Quick-Action Candy Pills -->
      <div class="quick-actions-bar">
        <div class="action-pill pill-blue" data-prompt="take screenshot">📸 Screenshot</div>
        <div class="action-pill pill-green" data-prompt="open whatsapp">💬 WhatsApp</div>
        <div class="action-pill pill-rose" data-prompt="search youtube for Google DeepMind">▶️ YouTube</div>
        <div class="action-pill pill-green" data-prompt="battery">🔋 Battery</div>
        <div class="action-pill pill-slate" data-prompt="open settings">⚙️ Settings</div>
        <div class="action-pill pill-amber" data-prompt="turn on flashlight">🔦 Torch</div>
        <div class="action-pill pill-cyan" data-prompt="home">🏠 Home</div>
        <div class="action-pill pill-purple" data-prompt="back">🔙 Back</div>
      </div>
    </section>

    <!-- TWO-COLUMN DASHBOARD GRID -->
    <div class="dashboard-grid">

      <!-- LEFT: CONTACT & MEMORY VAULT -->
      <section class="card-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span>📇 Saved Contacts</span>
          </div>
          <div style="display: flex; gap: 6px;">
            <button id="btnAddContact" class="btn-sync">+ Add</button>
            <button id="btnSyncMemory" class="btn-sync">↻ Sync</button>
          </div>
        </div>

        <div id="contactsContainer" class="contacts-list">
          <div style="font-size: 13px; color: #94A3B8;">Loading contacts...</div>
        </div>
      </section>

      <!-- RIGHT: SLEEK TELEMETRY INSPECTOR -->
      <section class="card-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span>⚡ Real-Time Inspector</span>
          </div>
          <div style="display: flex; gap: 6px;">
            <button id="btnClearLogs" class="btn-sync">Clear</button>
          </div>
        </div>

        <div class="terminal-container">
          <div class="terminal-header">
            <div class="terminal-status">
              <span style="color: #22C55E;">●</span> ADB-5037 Bus Active
            </div>
            <div style="font-size: 10px; color: #94A3B8;">115200 BAUD</div>
          </div>

          <div id="terminalLogs" class="terminal-logs">
            <div class="log-entry">
              <span class="log-ts">00:00:00</span>
              <span class="log-badge SYS">SYS</span>
              <span class="log-text">Artemis Voice OS console ready on Samsung Galaxy A36.</span>
            </div>
          </div>
        </div>
      </section>

    </div>

  </div>

  <!-- CLIENT-SIDE EVENT STREAMING & INTERACTIONS -->
  <script>
    const socket = io();

    // State Variables
    let currentLanguage = 'en-IN';
    let isTransmitting = false;

    // DOM References
    const pillTransmitter = document.getElementById('pillTransmitter');
    const pillLabel = document.getElementById('pillLabel');
    const btnStopTask = document.getElementById('btnStopTask');
    const soundwave = document.getElementById('soundwave');
    const transcriptBox = document.getElementById('transcriptBox');
    const transcriptText = document.getElementById('transcriptText');
    const routeBadge = document.getElementById('routeBadge');
    const promptInput = document.getElementById('promptInput');
    const btnRunPrompt = document.getElementById('btnRunPrompt');
    const contactsContainer = document.getElementById('contactsContainer');
    const terminalLogs = document.getElementById('terminalLogs');
    const btnClearLogs = document.getElementById('btnClearLogs');
    const btnSyncMemory = document.getElementById('btnSyncMemory');
    const confirmationBanner = document.getElementById('confirmationBanner');
    const confirmQuestion = document.getElementById('confirmQuestion');

    // Language Pill Selector
    document.querySelectorAll('.lang-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.lang-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentLanguage = pill.getAttribute('data-lang') || 'en-IN';
        appendLog('SYS', `Language switched to ${currentLanguage} (${pill.textContent.trim()})`);
      });
    });

    // Confirmation Banner Helpers
    function showConfirmation(question) {
      if (confirmQuestion && confirmationBanner) {
        confirmQuestion.textContent = question;
        confirmationBanner.style.display = 'flex';
      }
    }

    function hideConfirmation() {
      if (confirmationBanner) {
        confirmationBanner.style.display = 'none';
      }
    }

    function answerConfirmation(answer) {
      hideConfirmation();
      executePrompt(answer);
    }

    // Append log line with high-contrast pill badge
    function appendLog(type, text, ts) {
      const entry = document.createElement('div');
      entry.className = 'log-entry';

      const timeSpan = document.createElement('span');
      timeSpan.className = 'log-ts';
      timeSpan.textContent = ts || new Date().toLocaleTimeString();

      const badgeSpan = document.createElement('span');
      badgeSpan.className = `log-badge ${type || 'STREAM'}`;
      badgeSpan.textContent = type || 'STREAM';

      const textSpan = document.createElement('span');
      textSpan.className = 'log-text';
      textSpan.textContent = text;

      entry.appendChild(timeSpan);
      entry.appendChild(badgeSpan);
      entry.appendChild(textSpan);
      terminalLogs.appendChild(entry);

      terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    const CANDY_GRADIENTS = [
      'linear-gradient(135deg, #EC4899 0%, #F43F5E 100%)',
      'linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%)',
      'linear-gradient(135deg, #10B981 0%, #059669 100%)',
      'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
      'linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)',
      'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)'
    ];

    function getAvatarGradient(str) {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = (hash << 5) - hash + str.charCodeAt(i);
        hash |= 0;
      }
      return CANDY_GRADIENTS[Math.abs(hash) % CANDY_GRADIENTS.length];
    }

    // Render Contact Badges
    function renderContacts(data) {
      if (!data) return;
      contactsContainer.innerHTML = '';

      const contacts = data.contacts || {};
      const names = Object.keys(contacts);

      if (names.length === 0) {
        contactsContainer.innerHTML = `
          <div style="font-size: 13px; color: #94A3B8; padding: 24px 12px; text-align: center; line-height: 1.6;">
            No contacts saved yet.<br>Click <strong>+ Add</strong> or <strong>↻ Sync</strong> to load contacts.
          </div>
        `;
        return;
      }

      names.forEach(name => {
        const item = contacts[name];
        const card = document.createElement('div');
        card.className = 'contact-item';

        const initial = name.charAt(0).toUpperCase();
        const gradient = getAvatarGradient(name);

        card.innerHTML = `
          <div class="contact-left">
            <div class="avatar-disc" style="background: ${gradient};">${initial}</div>
            <div class="contact-details">
              <span class="contact-name">${name}</span>
              <span class="contact-meta">${item.phone || item.email || ''}</span>
            </div>
          </div>
          <div class="contact-actions">
            <button class="mini-pill-btn btn-call" data-name="${name}">Call</button>
            <button class="mini-pill-btn btn-wa" data-name="${name}">WA</button>
            <button class="btn-del btn-remove-contact" data-name="${name}" title="Remove contact">✕</button>
          </div>
        `;

        card.addEventListener('click', (e) => {
          if (e.target.classList.contains('btn-call')) {
            e.stopPropagation();
            executePrompt(`call ${name}`);
          } else if (e.target.classList.contains('btn-wa')) {
            e.stopPropagation();
            executePrompt(`send whatsapp to ${name} saying hello`);
          } else if (e.target.classList.contains('btn-remove-contact') || e.target.closest('.btn-remove-contact')) {
            e.stopPropagation();
            deleteContact(name);
          } else {
            promptInput.value = `call ${name}`;
            promptInput.focus();
          }
        });

        contactsContainer.appendChild(card);
      });
    }

    function deleteContact(name) {
      fetch('/api/contacts/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      .then(r => r.json())
      .then(data => {
        appendLog('SYS', `Removed ${name} from saved contacts.`);
        renderContacts(data);
      })
      .catch(err => appendLog('ERROR', 'Delete error: ' + err));
    }

    // Trigger Live Microphone Broadcast
    function startListening() {
      if (isTransmitting) return;
      isTransmitting = true;

      pillTransmitter.classList.add('transmitting');
      pillLabel.textContent = 'Listening... (Tap to Stop)';
      if (btnStopTask) btnStopTask.classList.add('active');
      soundwave.classList.add('active');
      transcriptBox.classList.add('active');
      transcriptText.className = 'transcript-content';
      transcriptText.textContent = `Listening in ${currentLanguage}...`;

      routeBadge.className = 'route-candy-tag';
      routeBadge.innerHTML = '<span>● Capturing</span>';

      fetch(`/api/listen?lang=${currentLanguage}`, { method: 'POST' })
        .then(r => r.json())
        .catch(err => {
          appendLog('ERROR', 'Failed to engage microphone: ' + err);
          resetTransmitter();
        });
    }

    // Trigger Prompt Simulation
    function executePrompt(promptText) {
      if (!promptText || isTransmitting) return;
      isTransmitting = true;

      pillTransmitter.classList.add('transmitting');
      pillLabel.textContent = 'Running... (Tap to Stop)';
      if (btnStopTask) btnStopTask.classList.add('active');
      soundwave.classList.add('active');
      transcriptBox.classList.add('active');
      transcriptText.className = 'transcript-content';
      transcriptText.textContent = `"${promptText}"`;

      fetch(`/api/simulate?prompt=${encodeURIComponent(promptText)}&lang=${currentLanguage}`, { method: 'POST' })
        .then(r => r.json())
        .catch(err => {
          appendLog('ERROR', 'Execution failed: ' + err);
          resetTransmitter();
        });
    }

    // Stop / Abort Task
    function stopTask() {
      if (!isTransmitting) return;
      appendLog('SYS', '⏹ Stopping task / audio capture on user request...');
      fetch('/api/stop', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          resetTransmitter();
          routeBadge.className = 'route-candy-tag';
          routeBadge.textContent = '● Standby';
        })
        .catch(err => {
          appendLog('ERROR', 'Stop request error: ' + err);
          resetTransmitter();
        });
    }

    function resetTransmitter() {
      isTransmitting = false;
      pillTransmitter.classList.remove('transmitting');
      pillLabel.textContent = 'Push to Talk [Space]';
      soundwave.classList.remove('active');
      transcriptBox.classList.remove('active');
      if (btnStopTask) btnStopTask.classList.remove('active');
    }

    // Device Selection Discovery & Switcher
    const deviceSelector = document.getElementById('deviceSelector');
    function loadDevices() {
      fetch('/api/devices')
        .then(r => r.json())
        .then(data => {
          if (!data || !data.devices || !deviceSelector) return;
          deviceSelector.innerHTML = '';
          data.devices.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.serial;
            opt.textContent = d.label;
            if (d.serial === data.active) opt.selected = true;
            deviceSelector.appendChild(opt);
          });
        })
        .catch(console.error);
    }
    loadDevices();

    if (deviceSelector) {
      deviceSelector.addEventListener('change', (e) => {
        const chosen = e.target.value;
        fetch('/api/device/set', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device: chosen })
        })
        .then(r => r.json())
        .then(res => {
          appendLog('SYS', `Target device changed to: ${chosen}`);
        })
        .catch(err => appendLog('ERROR', 'Failed to switch device: ' + err));
      });
    }

    // Socket.IO Real-Time Stream Listeners
    fetch('/api/memory').then(r => r.json()).then(renderContacts).catch(console.error);
    socket.on('connect', () => {
      appendLog('SYS', 'Telemetry stream connected to server.');
      loadDevices();
      fetch('/api/memory').then(r => r.json()).then(renderContacts);
    });

    socket.on('disconnect', () => {
      appendLog('ERROR', 'Telemetry stream lost.');
    });

    socket.on('tx_start', () => {
      isTransmitting = true;
      pillTransmitter.classList.add('transmitting');
      pillLabel.textContent = 'Listening... (Tap to Stop)';
      if (btnStopTask) btnStopTask.classList.add('active');
      soundwave.classList.add('active');
    });

    socket.on('log_event', (data) => {
      appendLog(data.type, data.line, data.timestamp);
    });

    socket.on('ask_user_confirmation', (data) => {
      showConfirmation(data.question || 'Confirmation required. Proceed?');
    });

    socket.on('speech_decoded', (data) => {
      transcriptText.className = 'transcript-content';
      transcriptText.textContent = `"${data.text}"`;
    });

    socket.on('routing_state', (data) => {
      if (data.mode === 'FAST') {
        routeBadge.className = 'route-candy-tag fast';
        routeBadge.textContent = '⚡ 12ms Fast ADB Intent';
      } else {
        routeBadge.className = 'route-candy-tag artemis';
        routeBadge.textContent = '🤖 Artemis Flash Vision';
      }
    });

    socket.on('tts_event', (data) => {
      appendLog('TTS', `Speaking feedback: "${data.text}"`);
    });

    socket.on('recording_finished', () => {
      soundwave.classList.remove('active');
      pillLabel.textContent = 'Processing command... ⚡';
    });

    socket.on('tx_complete', () => {
      resetTransmitter();
      routeBadge.className = 'route-candy-tag';
      routeBadge.textContent = '● Standby';
    });

    socket.on('memory_updated', (data) => {
      renderContacts(data);
    });

    // PTT Click & Mouse Events
    pillTransmitter.addEventListener('click', () => {
      if (isTransmitting) {
        stopTask();
      } else {
        startListening();
      }
    });

    if (btnStopTask) {
      btnStopTask.addEventListener('click', () => {
        stopTask();
      });
    }

    // Hotkey: Spacebar to Transmit / Escape to Stop
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;

      if (e.code === 'Escape' && isTransmitting) {
        e.preventDefault();
        stopTask();
      } else if (e.code === 'Space') {
        e.preventDefault();
        if (isTransmitting) {
          stopTask();
        } else {
          startListening();
        }
      }
    });

    // Prompt Input Run
    btnRunPrompt.addEventListener('click', () => {
      const val = promptInput.value.trim();
      if (val) {
        executePrompt(val);
        promptInput.value = '';
      }
    });

    promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const val = promptInput.value.trim();
        if (val) {
          executePrompt(val);
          promptInput.value = '';
        }
      }
    });

    // Quick-Action Candy Pills
    document.querySelectorAll('.action-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const prompt = pill.getAttribute('data-prompt');
        if (prompt) {
          executePrompt(prompt);
        }
      });
    });

    // Add Contact
    const btnAddContact = document.getElementById('btnAddContact');
    if (btnAddContact) {
      btnAddContact.addEventListener('click', () => {
        const name = prompt('Enter contact name:');
        if (!name || !name.trim()) return;
        const phone = prompt(`Enter phone number for "${name.trim()}":`);
        if (!phone || !phone.trim()) return;

        fetch('/api/contacts/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name.trim(), phone: phone.trim() })
        })
        .then(r => r.json())
        .then(data => {
          appendLog('SYS', `Added ${name.trim()} (${phone.trim()}) to saved contacts.`);
          renderContacts(data);
        })
        .catch(err => appendLog('ERROR', 'Add error: ' + err));
      });
    }

    // Sync Memory Contacts
    if (btnSyncMemory) {
      btnSyncMemory.addEventListener('click', () => {
        btnSyncMemory.textContent = 'Syncing...';
        fetch('/api/contacts/sync', { method: 'POST' })
          .then(r => r.json())
          .then(data => {
            btnSyncMemory.textContent = '↻ Sync';
            renderContacts({ contacts: data.contacts });
            appendLog('SYS', `Synced contacts with device.`);
          })
          .catch(() => {
            btnSyncMemory.textContent = '↻ Sync';
          });
      });
    }

    // Clear Terminal Logs
    if (btnClearLogs) {
      btnClearLogs.addEventListener('click', () => {
        terminalLogs.innerHTML = '';
        appendLog('SYS', 'Logs cleared.');
      });
    }
  </script>
</body>
</html>
"""


# ==============================================================================
# REST API Endpoints
# ==============================================================================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/memory", methods=["GET"])
def api_get_memory():
    return jsonify(load_memory_vault())


@app.route("/api/contacts/add", methods=["POST"])
def api_add_contact():
    """Adds or updates a contact in user_memory.json."""
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip().lower()
    phone = payload.get("phone", "").strip()
    if not name or not phone:
        return jsonify({"status": "error", "message": "Name and phone are required"}), 400

    mem = load_memory_vault()
    if "contacts" not in mem:
        mem["contacts"] = {}

    mem["contacts"][name] = {"phone": phone}
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)
    socketio.emit("memory_updated", mem)
    return jsonify({"status": "added", "contacts": mem.get("contacts", {})})


@app.route("/api/contacts/delete", methods=["POST"])
def api_delete_contact():
    """Deletes a contact from user_memory.json."""
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip().lower()
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400

    mem = load_memory_vault()
    if "contacts" in mem and name in mem["contacts"]:
        del mem["contacts"][name]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
        socketio.emit("memory_updated", mem)
        return jsonify({"status": "deleted", "contacts": mem.get("contacts", {})})

    return jsonify({"status": "not_found", "contacts": mem.get("contacts", {})}), 404


@app.route("/api/contacts/sync", methods=["GET", "POST"])
def api_sync_contacts():
    """Syncs live device contacts via ADB and merges into user_memory.json."""
    mem = load_memory_vault()
    if "contacts" not in mem:
        mem["contacts"] = {}

    try:
        env = os.environ.copy()
        env["ANDROID_USER_HOME"] = str(WORKSPACE_DIR / ".android")
        res = subprocess.run(
            [ADB_BIN, "-s", TARGET_DEVICE_SERIAL, "shell", "content", "query", "--uri", "content://com.android.contacts/data/phones", "--projection", "display_name:data1"],
            capture_output=True, text=True, check=False, env=env, timeout=5
        )
        if res.returncode == 0 and res.stdout:
            added = 0
            for line in res.stdout.splitlines():
                m = re.search(r"display_name=(.*?),\s*data1=(.*)", line.strip())
                if m:
                    d_name = m.group(1).strip()
                    d_phone = m.group(2).strip()
                    if d_name and d_phone:
                        clean_k = d_name.lower().strip()
                        if clean_k not in mem["contacts"]:
                            mem["contacts"][clean_k] = {"phone": d_phone}
                            added += 1

            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(mem, f, indent=2, ensure_ascii=False)
            socketio.emit("memory_updated", mem)
            print(f"[Sync] Added {added} new contacts from phone.")
    except Exception as e:
        print(f"[Sync] Error syncing contacts: {e}")

    return jsonify({"status": "synced", "contacts": mem.get("contacts", {})})


@app.route("/api/listen", methods=["POST"])
def api_listen():
    """Trigger microphone audio recording and pipeline execution with language selection."""
    if execution_lock.locked():
        return jsonify({"status": "busy", "message": "Pipeline already active"}), 429

    lang = request.args.get("lang") or "en-IN"
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        lang = payload.get("lang") or lang

    thread = threading.Thread(
        target=run_voice_commander_streaming,
        args=(["--lang", lang], f"LIVE_MIC_{lang}"),
        daemon=True
    )
    thread.start()
    return jsonify({"status": "initiated", "mode": "LIVE_MIC", "lang": lang})


@app.route("/api/simulate", methods=["GET", "POST"])
def api_simulate():
    """Trigger text command execution with language support."""
    prompt = request.args.get("prompt")
    lang = request.args.get("lang") or "en-IN"

    if not prompt and request.is_json:
        payload = request.get_json(silent=True) or {}
        prompt = payload.get("text") or payload.get("prompt")
        lang = payload.get("lang") or lang

    if not prompt:
        return jsonify({"status": "error", "message": "No prompt provided"}), 400

    prompt = prompt.strip()

    if execution_lock.locked():
        return jsonify({"status": "busy", "message": "Pipeline already active"}), 429

    thread = threading.Thread(
        target=run_voice_commander_streaming,
        args=(["--lang", lang, "--text-only", prompt], f"PROMPT: {prompt[:20]} ({lang})"),
        daemon=True
    )
    thread.start()
    return jsonify({"status": "initiated", "prompt": prompt, "lang": lang})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Cancel and terminate any currently running audio recording or Artemis task immediately."""
    global current_process
    stopped = False

    # 1. Halt Artemis Daemon scheduler tasks immediately
    try:
        requests.post("http://127.0.0.1:8000/api/stop", json={"all": True}, timeout=1.0)
    except Exception as e:
        print(f"[STOP] Artemis daemon stop error: {e}")

    # 2. Terminate the subprocess tree on Windows
    if current_process:
        try:
            pid = current_process.pid
            try:
                if current_process.stdout:
                    current_process.stdout.close()
            except Exception:
                pass
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            stopped = True
        except Exception as e:
            print(f"[STOP] Exception terminating subprocess tree: {e}")
        finally:
            current_process = None

    # 3. Dismiss active screen / dialog on phone and return to Home
    try:
        subprocess.run([ADB_BIN, "-s", TARGET_DEVICE_SERIAL, "shell", "input", "keyevent", "4"], timeout=2)
        subprocess.run([ADB_BIN, "-s", TARGET_DEVICE_SERIAL, "shell", "input", "keyevent", "3"], timeout=2)
    except Exception:
        pass

    socketio.emit("log_event", {
        "type": "SYS",
        "line": "🛑 Process and running tasks stopped by user request.",
        "timestamp": time.strftime("%H:%M:%S")
    })
    socketio.emit("tx_complete", {"stopped_by_user": True})
    return jsonify({"status": "stopped", "process_killed": stopped})


@app.route("/api/devices", methods=["GET"])
def api_get_devices():
    """Returns all attached Android devices/emulators and active selection."""
    return jsonify({
        "devices": get_connected_devices(),
        "active": TARGET_DEVICE_SERIAL
    })


@app.route("/api/device/set", methods=["POST"])
def api_set_device():
    """Sets active target device serial."""
    global TARGET_DEVICE_SERIAL
    payload = request.get_json(silent=True) or {}
    device = payload.get("device")
    if device:
        TARGET_DEVICE_SERIAL = device
        socketio.emit("log_event", {
            "type": "SYS",
            "line": f"Target hardware switched to: {TARGET_DEVICE_SERIAL}",
            "timestamp": time.strftime("%H:%M:%S")
        })
        return jsonify({"status": "ok", "active": TARGET_DEVICE_SERIAL})
    return jsonify({"status": "error", "message": "Device serial required"}), 400


# ==============================================================================
# Main Entry Point
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("✨  ARTEMIS // PAN-INDIAN NEO-HUMANIST CONSOLE")
    print(f"Canvas: Pure White (#FFFFFF) with Tactile Candy Tokens")
    print(f"Target Device: {TARGET_DEVICE_SERIAL} (Samsung Galaxy A36)")
    print(f"Memory Vault: {MEMORY_FILE}")
    print(f"Endpoint: http://localhost:5000")
    print("=" * 70)

    mem = load_memory_vault()
    contacts_count = len(mem.get("contacts", {}))
    print(f"✓ Loaded {contacts_count} contacts from user_memory.json")

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
