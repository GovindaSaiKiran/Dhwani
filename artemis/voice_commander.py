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

"""Pan-Indian Autonomous Voice OS for Android (Samsung Galaxy A36 - RZGL52YX8DD).

Full-featured, memory-enabled Pan-Indian Multilingual Voice OS integrating:
- Gnani AI Voice Pipeline (Prisma v3.0 STT & Timbre v3.0 TTS) for 7 Indian Languages
- 4-Stage Pan-Indian Multilingual & Phonetic Normalizer (Telugu, Tamil, Kannada, Hindi, Marathi, Odia, English)
- Two-Tier Confidence Fuzzy Matcher & Live Device Contacts Manager (380+ contacts via ADB)
- Interactive Disambiguation, Nearest-Match Confirmation & Cross-App Recovery (pending_confirmation.json)
- Universal 50+ Indian & Global App Launcher with live ADB package scanner and category alternatives
- Dynamic Silence Cutoff (VAD) via RMS Energy Chunking
- Instant Sub-100ms Static ADB Control Suite & Artemis Autonomous Agent Fallback
"""

import argparse
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.parse

# Ensure UTF-8 stdout/stderr on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Process tracking for clean aborts
active_artemis_proc = None

def _handle_exit_signal(signum, frame):
    global active_artemis_proc
    if active_artemis_proc:
        try:
            active_artemis_proc.terminate()
            active_artemis_proc.kill()
        except Exception:
            pass
    sys.exit(0)

try:
    signal.signal(signal.SIGINT, _handle_exit_signal)
    signal.signal(signal.SIGTERM, _handle_exit_signal)
except Exception:
    pass

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pyaudio = None
    HAS_PYAUDIO = False

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv(Path(__file__).resolve().parent / "artemis" / ".env")
except ImportError:
    pass

from gnani_bridge import (
    GNANI_API_KEY,
    KEY_ID_HEADER,
    PAN_INDIAN_LANGUAGES,
    get_last_stt_latency_ms,
    get_last_tts_latency_ms,
    play_audio_file,
    resolve_language,
    synthesize_and_play as _raw_gnani_synth_play,
    synthesize_speech,
    transcribe_audio as gnani_transcribe,
)

ACTIVE_VOICE = os.getenv("ACTIVE_VOICE", "Lakshmi")


class TelemetryTimer:
    """Accurately records latency across every stage of the voice assistant pipeline."""

    def __init__(self):
        self.vad_duration_s: float = 0.0
        self.stt_ms: float = 0.0
        self.router_ms: float = 0.0
        self.exec_ms: float = 0.0
        self.tts_ms: float = 0.0
        self.t_turn_start: float = time.perf_counter()

    def report(self) -> str:
        total_ms = (time.perf_counter() - self.t_turn_start) * 1000.0
        line = (
            f"[Telemetry] ⏱️ TIMING BREAKDOWN: "
            f"VAD={self.vad_duration_s:.2f}s | "
            f"STT={self.stt_ms:.0f}ms | "
            f"Router={self.router_ms:.1f}ms | "
            f"Exec={self.exec_ms:.0f}ms | "
            f"TTS={self.tts_ms:.0f}ms | "
            f"Total={total_ms:.0f}ms"
        )
        print(line, flush=True)
        return line

def gnani_synth_play(text: str, lang: str = "en-IN", voice: str = None, play_audio: bool = True, output_path: str = "response.wav") -> str:
    chosen_voice = voice or ACTIVE_VOICE or "Lakshmi"
    return _raw_gnani_synth_play(text, lang=lang, voice=chosen_voice, play_audio=play_audio, output_path=output_path)

# ==============================================================================
# Configuration & Hardware Targeting
# ==============================================================================
ADB_BIN = (
    shutil.which("adb")
    or os.getenv("ADB_PATH")
    or r"C:\Users\Asus\Downloads\Android\platform-tools-latest-windows\platform-tools\adb.exe"
    or "adb"
)

def _detect_default_device() -> str:
    env_target = os.getenv("TARGET_DEVICE_SERIAL")
    if env_target:
        return env_target
    try:
        res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True, check=False, timeout=3)
        devs = [l.split()[0] for l in res.stdout.splitlines()[1:] if len(l.split()) >= 2 and l.split()[1] == "device"]
        emus = [d for d in devs if d.startswith("emulator")]
        if emus:
            return emus[0]
        if devs:
            return devs[0]
    except Exception:
        pass
    return "emulator-5554"

TARGET_DEVICE_SERIAL = _detect_default_device()
AUDIO_SAMPLE_RATE = 16000
VOICE_COMMAND_FILE = "voice_command.wav"
RESPONSE_AUDIO_FILE = "response.wav"

WORKSPACE_DIR = Path(__file__).resolve().parent
PENDING_CONFIRMATION_FILE = WORKSPACE_DIR / "pending_confirmation.json"
USER_MEMORY_FILE = WORKSPACE_DIR / "user_memory.json"


# ==============================================================================
# 1. Low-Level ADB Command Execution
# ==============================================================================
def run_adb(args: list[str], serial: str = TARGET_DEVICE_SERIAL, timeout: float = 4.0) -> subprocess.CompletedProcess:
    """Executes an ADB command on the target serial."""
    env = os.environ.copy()
    env["ANDROID_USER_HOME"] = str(WORKSPACE_DIR / ".android")
    cmd = [ADB_BIN, "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr="ADB command timed out")


def toggle_torch_samsung(action: str = "toggle", serial: str = TARGET_DEVICE_SERIAL) -> tuple[bool, str]:
    """Reliably controls the flashlight on Samsung One UI (Galaxy A36) and standard Android."""
    # Check current torch state via dumpsys media.camera
    res_dump = run_adb(["shell", "dumpsys media.camera | grep -iE 'Torch for camera id 0 turned' | head -n 1"], serial=serial)
    is_currently_on = "turned on" in res_dump.stdout.lower()

    if action in ["on", "turn_on"] and is_currently_on:
        return True, "Flashlight is already turned on."
    if action in ["off", "turn_off"] and not is_currently_on:
        return True, "Flashlight is already turned off."

    # Try standard cmd flash_light first
    res = run_adb(["shell", "cmd", "flash_light", "set-torch", "1" if action in ["on", "turn_on"] else "0"], serial=serial)
    if res.returncode == 0 and "Can't find service" not in (res.stderr or ""):
        return True, f"Flashlight turned {action}."

    # Samsung Quick Settings tile fallback: Flashlight tile at [651, 480]
    run_adb(["shell", "cmd statusbar expand-settings && sleep 0.4 && input tap 651 480 && sleep 0.2 && cmd statusbar collapse"], serial=serial)
    new_state = "off" if is_currently_on else "on"
    return True, f"Flashlight turned {new_state}."


def escape_adb_text(text: str) -> str:
    """Escapes text for android `adb shell input text`."""
    s = text.replace(" ", "%s")
    for char in ["'", '"', "&", "(", ")", "<", ">", "|", ";", "$", "`", "\\"]:
        s = s.replace(char, f"\\{char}")
    return s


def clean_phone_number(phone: str) -> str:
    """Extracts clean digits from a phone string (e.g. +91 98765 -> 919876543210)."""
    return re.sub(r"[^\d]", "", phone)


def get_battery_level(serial: str = TARGET_DEVICE_SERIAL) -> int | None:
    """Queries current battery percentage from target device using dumpsys."""
    res = run_adb(["shell", "dumpsys", "battery"], serial=serial)
    match = re.search(r"level:\s*(\d+)", res.stdout)
    if match:
        return int(match.group(1))
    return None


def is_app_installed(package_name: str, serial: str = TARGET_DEVICE_SERIAL) -> bool:
    """Checks whether a package is currently installed on the target Android device."""
    try:
        res = run_adb(["shell", "pm", "path", package_name], serial=serial)
        return res.returncode == 0 and "package:" in res.stdout
    except Exception:
        return False


# ==============================================================================
# 2. Persistent User Memory & Contact Vault
# ==============================================================================
class UserMemoryManager:
    """Manages persistent structured user memory, contacts, and personal profile."""

    DEFAULT_MEMORY = {
        "profile": {},
        "contacts": {},
        "addresses": {},
        "notes": {},
    }

    def __init__(self, filename: str = "user_memory.json"):
        self.filename = filename
        self.paths = [
            Path(filename),
            WORKSPACE_DIR / filename,
            WORKSPACE_DIR / "artemis" / filename,
        ]
        self.filepath = self._resolve_path()
        self.data = self._load()

    def _resolve_path(self) -> Path:
        for p in self.paths:
            if p.exists():
                return p.resolve()
        return (WORKSPACE_DIR / self.filename).resolve()

    def _load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in self.DEFAULT_MEMORY.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as exc:
                print(f"[Memory] Notice: Error reading {self.filepath}: {exc}. Reinitializing.")
        data = dict(self.DEFAULT_MEMORY)
        self._save(data)
        return data

    def _save(self, data: dict | None = None):
        if data is not None:
            self.data = data
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            for p in self.paths:
                if p != self.filepath and p.parent.exists():
                    try:
                        with open(p, "w", encoding="utf-8") as f:
                            json.dump(self.data, f, indent=2, ensure_ascii=False)
                    except Exception:
                        pass
        except Exception as exc:
            print(f"[Memory] Error saving {self.filepath}: {exc}")

    def save_contact(self, name: str, phone: str | None = None, email: str | None = None):
        key = name.strip().lower()
        if "contacts" not in self.data:
            self.data["contacts"] = {}
        if key not in self.data["contacts"]:
            self.data["contacts"][key] = {}
        if phone:
            self.data["contacts"][key]["phone"] = phone.strip()
        if email:
            self.data["contacts"][key]["email"] = email.strip()
        self._save()
        print(f"[Memory] ✔ Saved contact '{key}': {self.data['contacts'][key]}")

    def save_profile(self, key: str, value: str):
        k = key.strip().lower()
        if "profile" not in self.data:
            self.data["profile"] = {}
        self.data["profile"][k] = value.strip()
        self._save()
        print(f"[Memory] ✔ Saved profile item '{k}' = '{value.strip()}'")

    def get_contact(self, name: str) -> dict | None:
        key = name.strip().lower()
        contacts = self.data.get("contacts", {})
        if key in contacts:
            return contacts[key]
        for c_name, c_info in contacts.items():
            if key in c_name or c_name in key:
                return c_info
        return None

    def get_profile(self, key: str) -> str | None:
        k = key.strip().lower()
        profile = self.data.get("profile", {})
        if k in profile:
            return profile[k]
        return None

    def find_memory_context(self, text: str) -> str:
        lower = text.lower()
        matches = []
        for name, info in self.data.get("contacts", {}).items():
            if re.search(rf"\b{re.escape(name)}\b", lower):
                phone = info.get("phone", "")
                parts = [f"Contact {name.title()}"]
                if phone:
                    parts.append(f"phone={phone}")
                matches.append(", ".join(parts))
        return "; ".join(matches)


# Initialize global memory manager
memory = UserMemoryManager()


# ==============================================================================
# 3. Live ADB Device Contacts Manager
# ==============================================================================
class DeviceContactsManager:
    """Extracts, caches, and provides high-speed fuzzy search over live device contacts."""

    def __init__(self, serial: str = TARGET_DEVICE_SERIAL, memory_mgr: UserMemoryManager = memory):
        self.serial = serial
        self.memory_mgr = memory_mgr
        self._cached_contacts = {}
        self._last_query_time = 0.0
        self.cache_ttl = 60.0  # seconds

    def get_all_contacts(self) -> dict[str, dict]:
        """Returns unified dictionary of memory contacts + live ADB device contacts."""
        now = time.time()
        merged = {}

        # 1. Add user_memory.json contacts (highest precedence)
        for name, info in self.memory_mgr.data.get("contacts", {}).items():
            clean_k = name.lower().strip()
            merged[clean_k] = {
                "name": name.title(),
                "phone": info.get("phone", ""),
                "email": info.get("email", ""),
                "source": "memory",
            }

        # 2. Query live ADB contacts from device
        if (now - self._last_query_time) > self.cache_ttl or not self._cached_contacts:
            try:
                res = run_adb(
                    ["shell", "content", "query", "--uri", "content://com.android.contacts/data/phones", "--projection", "display_name:data1"],
                    serial=self.serial,
                )
                if res.returncode == 0 and res.stdout:
                    device_contacts = {}
                    for line in res.stdout.splitlines():
                        m = re.search(r"display_name=(.*?),\s*data1=(.*)", line.strip())
                        if m:
                            d_name = m.group(1).strip()
                            d_phone = m.group(2).strip()
                            if d_name and d_phone:
                                clean_k = d_name.lower().strip()
                                device_contacts[clean_k] = {
                                    "name": d_name,
                                    "phone": d_phone,
                                    "source": "device",
                                }
                    self._cached_contacts = device_contacts
                    self._last_query_time = now
            except Exception as e:
                print(f"[Contacts] Notice: ADB live contacts query error: {e}")

        # Merge cached device contacts
        for k, v in self._cached_contacts.items():
            if k not in merged:
                merged[k] = v

        return merged

    def find_contact(self, query: str) -> tuple[dict | None, float, str | None]:
        """Performs two-tier confidence lookup:
        - Memory contacts take precedence for auto-correct & disambiguation.
        - Tier 1 (score >= 0.82): Exact / High confidence -> returns (contact, score, None)
        - Tier 2 (0.48 <= score < 0.82): Disambiguation needed -> returns (None, score, candidate_name)
        - Sub-0.48: Fallback to device contacts.
        """
        q = query.lower().strip()
        mem_contacts = self.memory_mgr.data.get("contacts", {})

        # 1. Exact match in memory contacts
        if q in mem_contacts:
            info = mem_contacts[q]
            return {
                "name": q.title(),
                "phone": info.get("phone", ""),
                "email": info.get("email", ""),
                "source": "memory",
            }, 1.0, None

        # 2. Check memory contacts with Two-Tier matching
        best_mem_match = None
        best_mem_score = 0.0

        for k in mem_contacts.keys():
            k_clean = k.lower().strip()
            ratio = difflib.SequenceMatcher(None, q, k_clean).ratio()
            # Prefix bonus if they share first 2 letters (e.g. rakesh vs rahul)
            if len(q) >= 2 and len(k_clean) >= 2 and q[:2] == k_clean[:2]:
                ratio = max(ratio, 0.72)
            if ratio > best_mem_score:
                best_mem_score = ratio
                best_mem_match = k_clean

        if best_mem_score >= 0.82 and best_mem_match:
            info = mem_contacts[best_mem_match]
            return {
                "name": best_mem_match.title(),
                "phone": info.get("phone", ""),
                "email": info.get("email", ""),
                "source": "memory",
            }, best_mem_score, None
        elif best_mem_score >= 0.48 and best_mem_match:
            return None, best_mem_score, best_mem_match.title()

        # 3. If no memory contact matches, search device contacts
        all_contacts = self.get_all_contacts()
        if q in all_contacts:
            return all_contacts[q], 1.0, None

        for k, v in all_contacts.items():
            if (len(q) >= 3 and q in k) or (len(k) >= 3 and k in q):
                return v, 0.95, None

        best_dev_match = None
        best_dev_score = 0.0
        for k, v in all_contacts.items():
            ratio = difflib.SequenceMatcher(None, q, k).ratio()
            if ratio > best_dev_score:
                best_dev_score = ratio
                best_dev_match = k

        if best_dev_score >= 0.82 and best_dev_match:
            return all_contacts[best_dev_match], best_dev_score, None
        elif best_dev_score >= 0.48 and best_dev_match:
            return None, best_dev_score, all_contacts[best_dev_match]["name"]

        return None, 0.0, None


# Initialize global contacts manager
contacts_mgr = DeviceContactsManager()


# ==============================================================================
# 4. Interactive Disambiguation & Pending Confirmation Manager
# ==============================================================================
class PendingConfirmationManager:
    """Manages persistent confirmation state for disambiguation and fallback recovery."""

    def __init__(self, filepath: Path = PENDING_CONFIRMATION_FILE):
        self.filepath = filepath

    def get_pending(self) -> dict | None:
        if not self.filepath.exists():
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Expire after 180 seconds
                if time.time() - data.get("timestamp", 0) > 180:
                    self.clear_pending()
                    return None
                return data
        except Exception:
            return None

    def set_pending(self, action: dict):
        action["timestamp"] = time.time()
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(action, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Pending] Error saving pending confirmation: {e}")

    def clear_pending(self):
        try:
            if self.filepath.exists():
                self.filepath.unlink()
        except Exception:
            pass

    def is_affirmative(self, text: str) -> bool:
        t = text.strip().lower()
        affirmative_tokens = [
            "yes", "yeah", "yep", "sure", "ok", "okay", "proceed", "confirm",
            "do it", "send it", "call", "open it",
            # Telugu
            "అవును", "avunu", "సరే", "sare", "చేయి", "cheyi", "పంపు", "pampu",
            # Tamil
            "ஆமா", "aama", "சரி", "sari", "பண்ணு", "pannu", "அனுப்பு",
            # Kannada
            "ಹೌದು", "haudu", "ಸರಿ", "sari", "ಮಾಡು", "madu", "ಕಳಿಸು",
            # Hindi
            "हाँ", "haan", "ha", "sahi", "theek hai", "bhejo", "karo", "chalo",
            # Marathi
            "हो", "ho", "bara ahe", "pathva", "kara",
            # Odia
            "ହଁ", "han", "thik achhi", "pathao"
        ]
        return any(tok in t or t == tok for tok in affirmative_tokens)

    def is_negative(self, text: str) -> bool:
        t = text.strip().lower()
        negative_tokens = [
            "no", "nope", "nah", "cancel", "don't", "dont", "stop", "abort", "never mind",
            # Telugu
            "వద్దు", "vaddu", "కాదు", "kaadu", "వద్దులే", "ఆపు",
            # Tamil
            "இல்லை", "illai", "வேண்டாம்", "vendaam", "வேணாம்", "venam",
            # Kannada
            "ಬೇಡ", "beda", "ಇಲ್ಲ", "illa",
            # Hindi
            "नहीं", "nahi", "na", "mat karo", "ruko", "band karo",
            # Marathi
            "नाही", "nahi", "nako",
            # Odia
            "ନା", "na", "mana"
        ]
        return any(tok in t or t == tok for tok in negative_tokens)


# Initialize global confirmation manager
pending_mgr = PendingConfirmationManager()


# ==============================================================================
# 5. Universal 50+ Indian & Global App Catalog & Cross-App Fallback
# ==============================================================================
APP_CATALOG = {
    # Quick Commerce & Grocery
    "blinkit": {"package": "com.grofers.customerapp", "category": "grocery", "name": "Blinkit"},
    "zepto": {"package": "com.zeptoconsumerapp", "category": "grocery", "name": "Zepto"},
    "instamart": {"package": "in.swiggy.android", "category": "grocery", "name": "Swiggy Instamart"},
    "bigbasket": {"package": "com.bigbasket.mobileapp", "category": "grocery", "name": "BigBasket"},
    "bbnow": {"package": "com.bigbasket.mobileapp", "category": "grocery", "name": "BB Now"},

    # Food Delivery
    "swiggy": {"package": "in.swiggy.android", "category": "food", "name": "Swiggy"},
    "zomato": {"package": "com.application.zomato", "category": "food", "name": "Zomato"},
    "eatsure": {"package": "com.done.faasos", "category": "food", "name": "EatSure"},

    # Shopping & E-Commerce
    "amazon": {"package": "in.amazon.mShop.android.shopping", "category": "shopping", "name": "Amazon"},
    "flipkart": {"package": "com.flipkart.android", "category": "shopping", "name": "Flipkart"},
    "meesho": {"package": "com.meesho.supply", "category": "shopping", "name": "Meesho"},
    "myntra": {"package": "com.myntra.android", "category": "shopping", "name": "Myntra"},
    "ajio": {"package": "com.ril.ajio", "category": "shopping", "name": "Ajio"},

    # Payments & UPI
    "google pay": {"package": "com.google.android.apps.nbu.paisa.user", "category": "payments", "name": "Google Pay"},
    "gpay": {"package": "com.google.android.apps.nbu.paisa.user", "category": "payments", "name": "Google Pay"},
    "phonepe": {"package": "com.phonepe.app", "category": "payments", "name": "PhonePe"},
    "paytm": {"package": "net.one97.paytm", "category": "payments", "name": "Paytm"},
    "bhim": {"package": "in.org.npci.upiapp", "category": "payments", "name": "BHIM"},

    # Rides & Travel
    "uber": {"package": "com.ubercab", "category": "ride", "name": "Uber"},
    "ola": {"package": "com.olacabs.customer", "category": "ride", "name": "Ola"},
    "rapido": {"package": "com.rapido.passenger", "category": "ride", "name": "Rapido"},
    "redbus": {"package": "in.redbus.android", "category": "travel", "name": "redBus"},
    "irctc": {"package": "cris.org.in.prs.ima", "category": "travel", "name": "IRCTC Rail Connect"},

    # Social & Messaging
    "whatsapp": {"package": "com.whatsapp", "category": "social", "name": "WhatsApp"},
    "youtube": {"package": "com.google.android.youtube", "category": "video", "name": "YouTube"},
    "instagram": {"package": "com.instagram.android", "category": "social", "name": "Instagram"},
    "facebook": {"package": "com.facebook.katana", "category": "social", "name": "Facebook"},
    "telegram": {"package": "org.telegram.messenger", "category": "social", "name": "Telegram"},
    "snapchat": {"package": "com.snapchat.android", "category": "social", "name": "Snapchat"},
    "twitter": {"package": "com.twitter.android", "category": "social", "name": "Twitter / X"},
    "x": {"package": "com.twitter.android", "category": "social", "name": "Twitter / X"},
    "linkedin": {"package": "com.linkedin.android", "category": "social", "name": "LinkedIn"},
    "gmail": {"package": "com.google.android.gm", "category": "communication", "name": "Gmail"},

    # Entertainment & OTT
    "hotstar": {"package": "in.startv.hotstar", "category": "ott", "name": "Disney+ Hotstar"},
    "jiocinema": {"package": "com.jio.media.ondemand", "category": "ott", "name": "JioCinema"},
    "netflix": {"package": "com.netflix.mediaclient", "category": "ott", "name": "Netflix"},
    "prime video": {"package": "com.amazon.avod.thirdpartyclient", "category": "ott", "name": "Prime Video"},
    "spotify": {"package": "com.spotify.music", "category": "music", "name": "Spotify"},
    "wynk": {"package": "com.bsbportal.music", "category": "music", "name": "Wynk Music"},
    "jiosaavn": {"package": "com.jio.media.jiobeats", "category": "music", "name": "JioSaavn"},

    # Core Samsung & Android Tools
    "play store": {"package": "com.android.vending", "category": "store", "name": "Google Play Store"},
    "playstore": {"package": "com.android.vending", "category": "store", "name": "Google Play Store"},
    "chrome": {"package": "com.android.chrome", "category": "browser", "name": "Google Chrome"},
    "browser": {"package": "com.android.chrome", "category": "browser", "name": "Google Chrome"},
    "settings": {"intent": "android.settings.SETTINGS", "name": "Settings"},
    "camera": {"intent": "android.media.action.STILL_IMAGE_CAMERA", "name": "Camera"},
    "gallery": {"package": "com.sec.android.gallery3d", "name": "Gallery"},
    "photos": {"package": "com.google.android.apps.photos", "name": "Google Photos"},
    "calculator": {"package": "com.sec.android.app.popupcalculator", "name": "Calculator"},
    "files": {"package": "com.sec.android.app.myfiles", "name": "My Files"},
    "clock": {"intent": "android.intent.action.SHOW_ALARMS", "name": "Clock"},
    "phone": {"intent": "android.intent.action.DIAL", "name": "Phone"},
    "messages": {"package": "com.samsung.android.messaging", "name": "Messages"},
    "maps": {"package": "com.google.android.apps.maps", "name": "Google Maps"},
}

CATEGORY_MAP = {
    "grocery": ["zepto", "blinkit", "instamart", "bigbasket"],
    "food": ["swiggy", "zomato", "eatsure"],
    "shopping": ["amazon", "flipkart", "meesho", "myntra"],
    "payments": ["google pay", "phonepe", "paytm", "bhim"],
    "ride": ["uber", "ola", "rapido"],
    "ott": ["hotstar", "jiocinema", "netflix", "prime video", "youtube"],
}


def launch_application(app_name: str, serial: str = TARGET_DEVICE_SERIAL) -> tuple[bool, str, dict | None]:
    """Launches application with automatic category fallback recovery if uninstalled.

    Returns: (success, feedback_message, optional_fallback_dict)
    """
    clean = app_name.strip().lower()
    app_info = APP_CATALOG.get(clean)

    if not app_info:
        # Fuzzy match across catalog
        matches = difflib.get_close_matches(clean, list(APP_CATALOG.keys()), n=1, cutoff=0.7)
        if matches:
            app_info = APP_CATALOG[matches[0]]
            clean = matches[0]

    if not app_info:
        return False, f"App '{app_name}' not found in catalog.", None

    # Check intent vs package
    if "intent" in app_info:
        intent_val = app_info["intent"]
        if ":" in intent_val:
            action, category = intent_val.split(":", 1)
            run_adb(["shell", "am", "start", "-a", action, "-c", category], serial=serial)
        else:
            run_adb(["shell", "am", "start", "-a", intent_val], serial=serial)
        return True, f"Opening {app_info['name']}.", None

    pkg = app_info["package"]
    # Check if installed on device
    if is_app_installed(pkg, serial=serial):
        run_adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], serial=serial)
        return True, f"Opening {app_info['name']}.", None

    # App is NOT installed -> Find installed alternative in category
    cat = app_info.get("category")
    if cat and cat in CATEGORY_MAP:
        for alt_key in CATEGORY_MAP[cat]:
            if alt_key != clean and alt_key in APP_CATALOG:
                alt_pkg = APP_CATALOG[alt_key].get("package")
                if alt_pkg and is_app_installed(alt_pkg, serial=serial):
                    alt_name = APP_CATALOG[alt_key]["name"]
                    fallback_data = {
                        "type": "open_app",
                        "app_key": alt_key,
                        "name": alt_name,
                        "package": alt_pkg,
                    }
                    msg = (
                        f"[Ask-User] {app_info['name']} is not installed on your phone. "
                        f"Would you like me to open {alt_name} instead? Please say Yes or No."
                    )
                    return False, msg, fallback_data

    return False, f"{app_info['name']} is not installed on your phone.", None


# ==============================================================================
# 6. 4-Stage Pan-Indian Multilingual & Phonetic Normalizer
# ==============================================================================
# Native Indic script & transliteration patterns mapped to canonical English actions
INDIC_ACTION_DICTIONARY = [
    # Telugu (te-IN)
    (r"(?:తెరువు|ఓపెన్|\bteruvu\b|\bopen\s*cheyi\b|\bopen\s*cheyyi\b)", "open"),
    (r"(?:కాల్\s*చేయి|ఫోన్\s*చేయి|కాల్\s*చెయ్యి|ఫోన్\s*చెయ్యి|\bcall\s*cheyi\b|\bcall\s*cheyyi\b|\bphone\s*cheyi\b)", "call"),
    (r"(?:మెసేజ్\s*పెట్టు|మెసేజ్\s*పంపు|మెసేజ్\s*చెయ్యి|\bmessage\s*pettu\b|\bmessage\s*pampu\b|\bpampu\b)", "send message"),
    (r"(?:ఆపు\s*చేయి|ఆపండి|ఆపు|\bstop\s*cheyi\b|\baapu\b|\baapandi\b)", "stop"),
    (r"(?:ఆన్\s*చేయి|వెలిగించు|ఆన్\s*చెయ్యి|\bon\s*cheyi\b)", "turn on"),
    (r"(?:ఆఫ్\s*చేయి|ఆఫ్\s*చెయ్యి|\boff\s*cheyi\b)", "turn off"),
    (r"(?:టార్చ్|లైట్|ఫ్లాష్‌లైట్)", "flashlight"),
    (r"(?:నాన్న\s*కి|నాన్నకి|నాన్న|పాపా)", "nanna"),
    (r"(?:అమ్మ\s*కి|అమ్మకి|అమ్మ)", "amma"),
    (r"(?:అవును|\bavunu\b|సరే|\bsare\b)", "yes"),
    (r"(?:వద్దు|\bvaddu\b|కాదు|\bkaadu\b)", "no"),

    # Tamil (ta-IN)
    (r"(?:திற|ஓபன்|\bthira\b|\bopen\s*pannu\b)", "open"),
    (r"(?:கால்\s*பண்ணு|போன்\s*போடு|\bcall\s*pannu\b|\bphone\s*podu\b)", "call"),
    (r"(?:மெசேஜ்\s*அனுப்பு|\bmessage\s*anuppu\b)", "send message"),
    (r"(?:ஆன்\s*பண்ணு|\bon\s*pannu\b)", "turn on"),
    (r"(?:ஆஃப்\s*பண்ணு|\boff\s*pannu\b)", "turn off"),
    (r"(?:ஆமா|\baama\b|சரி|\bsari\b)", "yes"),
    (r"(?:இல்லை|\billai\b|வேண்டாம்|\bvendaam\b|வேணாம்)", "no"),
    (r"(?:அப்பாவுக்கு|அப்பா)", "appa"),
    (r"(?:அம்மாவுக்கு|அம்மா)", "amma"),
    (r"(?:டார்ச்|விளக்கு)", "flashlight"),

    # Kannada (kn-IN)
    (r"(?:ತೆರೆ|ಓಪನ್\s*ಮಾಡು|\bopen\s*madu\b)", "open"),
    (r"(?:ಕಾಲ್\s*ಮಾಡು|\bcall\s*madu\b)", "call"),
    (r"(?:ಮೆಸೇಜ್\s*ಕಳಿಸು|\bmessage\s*kalisu\b)", "send message"),
    (r"(?:ಆನ್\s*ಮಾಡು|\bon\s*madu\b)", "turn on"),
    (r"(?:ಆಫ್\s*ಮಾಡು|\boff\s*madu\b)", "turn off"),
    (r"(?:ಹೌದು|\bhaudu\b|ಸರಿ|\bsari\b)", "yes"),
    (r"(?:ಬೇಡ|\bbeda\b|ಇಲ್ಲ|\billa\b)", "no"),
    (r"(?:ಅಪ್ಪನಿಗೆ|ಅಪ್ಪ)", "appa"),
    (r"(?:ಅಮ್ಮನಿಗೆ|ಅಮ್ಮ)", "amma"),
    (r"(?:ಟಾರ್ಚ್)", "flashlight"),

    # Hindi (hi-IN)
    (r"(?:खोलो|चालू\s*करो|\bkholo\b|\bopen\s*karo\b)", "open"),
    (r"(?:कॉल\s*करो|फोन\s*लगाओ|कॉल\s*लगाओ|\bcall\s*karo\b|\bphone\s*lagao\b)", "call"),
    (r"(?:मैसेज\s*भेजो|\bmessage\s*bhejo\b)", "send message"),
    (r"(?:रुको|रोको|रोक\s*दो|रुक\s*जाओ|\broko\b|\bruko\b|\bstop\s*karo\b)", "stop"),
    (r"(?:ऑन\s*करो|जलाओ|\bon\s*karo\b)", "turn on"),
    (r"(?:बंद\s*करो|\boff\s*karo\b|\bband\s*karo\b)", "turn off"),
    (r"(?:हाँ|\bhaan\b|\bha\b|\bsahi\b)", "yes"),
    (r"(?:नहीं|\bnahi\b|मत\s*करो)", "no"),
    (r"(?:पापा\s*को|पापा)", "papa"),
    (r"(?:मम्मी\s*को|मम्मी|माँ)", "mummy"),
    (r"(?:टॉर्च|बत्ती)", "flashlight"),

    # Marathi (mr-IN)
    (r"(?:उघडा|चालू\s*करा|\bughada\b|\bopen\s*kara\b)", "open"),
    (r"(?:कॉल\s*करा|\bcall\s*kara\b|फोन\s*लावा|\bphone\s*lava\b)", "call"),
    (r"(?:मेसेज\s*पाठवा|\bmessage\s*pathva\b)", "send message"),
    (r"(?:बंद\s*करा|\bband\s*kara\b)", "turn off"),
    (r"(?:हो|\bho\b|बरं\s*आहे)", "yes"),
    (r"(?:नाही|\bnahi\b|\bnako\b)", "no"),
    (r"(?:बाबांना|बाबा)", "baba"),
    (r"(?:आईला|आई)", "aai"),
    (r"(?:टॉर्च)", "flashlight"),

    # Odia (or-IN)
    (r"(?:ଖୋଲ|\bkhola\b)", "open"),
    (r"(?:କଲ୍\s*କର|\bcall\s*kara\b)", "call"),
    (r"(?:ମେସେଜ୍\s*ପଠାଅ|\bmessage\s*pathao\b)", "send message"),
    (r"(?:ଅନ୍\s*କର|\bon\s*kara\b)", "turn on"),
    (r"(?:ବନ୍ଦ\s*କର|\bband\s*kara\b)", "turn off"),
    (r"(?:ହଁ|\bhan\b|ଠିକ୍\s*ଅଛି)", "yes"),
    (r"(?:ନା|\bna\b|\bmana\b)", "no"),
    (r"(?:ବାପାଙ୍କୁ|ବାପା)", "bapa"),
    (r"(?:ମାଆଙ୍କୁ|ମାଆ|ମା)", "maa"),
    (r"(?:ଟର୍ଚ୍ଚ)", "flashlight"),
]

# Indian English colloquialisms & phonetic app distortions
INDIAN_COLLOQUIALISMS = [
    (r"(?:what'?s\s*up|whats\s*up|watsap|vatsap|वाट्सएप|వాట్సాప్|வாட்ஸ்அப்|thasup|wattsapp|watsapp)", "whatsapp"),
    (r"(?:you\s*tube|utube|yutube|यूट्यूब|యూట్యూబ్|yotube|youtub)", "youtube"),
    (r"(?:touch\s*light|torch\s*light|on\s+the\s+torch|put\s+torch|flaslight|torchlight)", "turn on flashlight"),
    (r"(?:put\s+what'?s\s*up\s+message|put\s+whatsapp\s+message|drop\s+whatsapp\s+message)", "send whatsapp message"),
    (r"(?:put\s+message|keep\s+message|drop\s+message)", "send message"),
    (r"(?:make\s+on|put\s+on)", "turn on"),
    (r"(?:make\s+off|put\s+off)", "turn off"),
    (r"(?:setings|satting|సెట్టింగ్స్|सेटिंग्स)", "settings"),
    (r"(?:my\s*file|file\s*manajar|fayls|files\s*app)", "files"),
    (r"(?:galary|gallary|gelary|photoes)", "gallery"),
    (r"(?:crome|crom|chrom)", "chrome"),
    (r"(?:play\s*stor|play\s*star|place\s*store|pleystore)", "play store"),
    (r"(?:cancle|stope|halt|pause|ruk|roko|bas)", "stop"),
]


def normalize_indian_command(raw_text: str, lang_code: str = "en-IN") -> str:
    """4-Stage Pan-Indian Multilingual & Phonetic Normalizer."""
    if not raw_text:
        return ""

    # Strip any leading/trailing punctuation (e.g. "Open Blinkit." -> "Open Blinkit")
    text = re.sub(r"^[^\w\s]+|[.!?,;:\"']+$", "", raw_text.strip()).strip()

    # Stage A: Native Script & Transliterated Action Normalization
    for pat, rep in INDIC_ACTION_DICTIONARY:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # Stage B: Indian English Colloquialisms & Phonetic Corrections
    for pat, rep in INDIAN_COLLOQUIALISMS:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    # Stage C: Two-Tier Confidence Fuzzy Matcher for Contact Names
    contacts = contacts_mgr.get_all_contacts()
    words = text.split()
    for idx, w in enumerate(words):
        w_clean = re.sub(r"[^\w]", "", w).lower()
        if not w_clean or len(w_clean) < 3:
            continue
        # Only evaluate words after action prepositions
        if idx > 0 and words[idx - 1].lower() in ["to", "call", "dial", "whatsapp", "message", "ki", "ko", "ku", "ge"]:
            matched_contact, score, _ = contacts_mgr.find_contact(w_clean)
            if matched_contact and score >= 0.82:
                # Tier 1 Auto-correct silently in place!
                words[idx] = matched_contact["name"].lower()

    text = " ".join(words)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[.!?,;:\"']+$", "", text).strip()

    # Stage D: SOV-to-SVO grammar inversion for Indian languages (e.g. "nanna call" -> "call nanna")
    text = re.sub(r"(?:^|\s+)(?:చేయి|చెయ్యి|కరో|పన్ను|మాడు|करा|କର)(?:\s+|$)", " ", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"^(?P<obj>.+?)\s+(?P<verb>call|dial|open|launch|start|run|turn\s+on|turn\s+off)$",
        r"\g<verb> \g<obj>",
        text,
        flags=re.IGNORECASE
    ).strip()

    # Postposition cleanups (e.g. "call nanna ki" -> "call nanna")
    text = re.sub(r"\bcall\s+(?:to\s+)?(?P<name>.+?)\s+(?:ki|ko|ku|kku|ge|la)\b", r"call \g<name>", text, flags=re.I).strip()
    text = re.sub(r"\b(?P<name>.+?)\s+(?:ki|ko|ku|kku|ge|la)\s+call\b", r"call \g<name>", text, flags=re.I).strip()

    if text.strip().lower() != raw_text.strip().lower():
        print(f"[Speech:NLP] 🔤 Pan-Indian Normalization: \"{raw_text}\" -> \"{text}\"")

    return text.strip()


# ==============================================================================
# 7. Audio Recording & Dynamic VAD
# ==============================================================================
def calculate_rms(samples: np.ndarray) -> float:
    """Calculates Root Mean Square (RMS) energy for 16-bit PCM audio samples."""
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


# ==============================================================================
# Wake Word & Trigger Extraction ("Vinda" & Multilingual Phonetics)
# ==============================================================================
WAKE_WORD_PATTERN = (
    r"^(?:(?:hey|hi|hello|ok|okay|oye)\s+)?"
    r"(?:vinda|winda|binda|venda|windha|vindha|govinda|winter|window|vendor|"
    r"విందా|వింద|विंदा|विन्दा|विन्द|விந்தா|விந்த|ವಿಂದಾ|ವಿಂದ|ବିନ୍ଦା|ଭିନ୍ଦା)"
    r"[\s,:\-]*"
)

TRIGGER_PROMPTS = {
    "en-IN": "Yes? How can I help you?",
    "te-IN": "చెప్పండి, నేను మీకు ఎలా సహాయపడగలను?",
    "hi-IN": "हाँ, मैं आपकी क्या मदद कर सकता हूँ?",
    "ta-IN": "சொல்லுங்கள், நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
    "kn-IN": "ಹೇಳಿ, ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
    "mr-IN": "बोला, मी तुम्हाला कशी मदत करू शकतो?",
    "or-IN": "କୁହନ୍ତୁ, ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
}


def extract_wake_word(text: str, wake_word: str = "vinda") -> tuple[bool, str]:
    """Detects if 'Vinda' trigger exists and returns (has_trigger, stripped_command)."""
    if not text:
        return False, ""

    text_clean = text.strip()

    # 1. Leading match: "Vinda, open youtube" / "Hey Vinda call nanna"
    leading_match = re.search(WAKE_WORD_PATTERN, text_clean, re.IGNORECASE)
    if leading_match:
        stripped = text_clean[leading_match.end():].strip()
        stripped = re.sub(r"^[^\w\s]+", "", stripped).strip()
        return True, stripped

    # 2. Anywhere in text: "Please Vinda open camera"
    embedded_match = re.search(
        r"\b(?:vinda|winda|binda|venda|windha|vindha|govinda|"
        r"విందా|వింద|विंदा|विन्दा|विन्द|விந்தா|விந்த|ವಿಂದಾ|ವಿಂದ|ବିନ୍ଦା|ଭିନ୍ଦା)\b[\s,:\-]*",
        text_clean,
        re.IGNORECASE
    )
    if embedded_match:
        before = text_clean[:embedded_match.start()].strip()
        after = text_clean[embedded_match.end():].strip()
        combined = f"{before} {after}".strip()
        combined = re.sub(r"\s+", " ", combined).strip()
        return True, combined

    return False, text_clean


def is_stop_command(text: str, lang_code: str = "en-IN") -> bool:
    """Checks if text contains an explicit emergency stop/cancel command in any supported language."""
    if not text:
        return False
    lower = text.strip().lower()
    stop_tokens = [
        "stop", "cancel", "abort", "halt", "pause", "exit", "quit", "nevermind", "never mind",
        "ఆపు", "ఆపండి", "వద్దు", "ఆపరా", "ఆపుము", "రుకో", "रोको", "रुक", "बस", "बंद करो", "रोक दो",
        "थांबवा", "थांबा", "नको", "बंद करा", "நிறுத்து", "நில்", "போதும்", "வேண்டாம்",
        "ನಿಲ್ಲಿಸು", "ನಿಲ್ಲು", "ಬೇಡ", "ବନ୍ଦ କର", "ଅଟକ", "ରୁହ",
        "ruk", "roko", "bas", "aapu", "aapandi", "nillisu", "thambva", "band kara", "band karo"
    ]
    if lower in stop_tokens:
        return True
    pattern = (
        r"\b(?:(?:hey\s+|hi\s+|hello\s+)?(?:vinda|winda|binda)\s+)?"
        r"(?:stop|cancel|abort|halt|pause|never\s*mind|exit|quit|ruk|roko|bas|aapu|aapandi|band\s*karo|band\s*kara|thambva)\b"
    )
    if re.search(pattern, lower, re.IGNORECASE):
        return True
    for token in ["ఆపు", "ఆపండి", "వద్దు", "రుకో", "रोको", "बंद करो", "थांबवा", "थांबा", "बंद करा", "நிறுத்து", "நில்", "ನಿಲ್ಲಿಸು", "ನಿಲ್ಲು", "ବନ୍ଦ କର"]:
        if token in text:
            return True
    return False


def abort_active_tasks(serial: str = TARGET_DEVICE_SERIAL, lang_code: str = "en-IN", play_audio: bool = True) -> str:
    """Terminates active Artemis runners, resets phone to Home, and announces cancellation."""
    global active_artemis_proc
    if active_artemis_proc:
        try:
            pid = active_artemis_proc.pid
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)
            else:
                active_artemis_proc.terminate()
                active_artemis_proc.kill()
        except Exception:
            pass
        active_artemis_proc = None

    try:
        requests.post("http://127.0.0.1:8000/api/stop", json={"all": True}, timeout=1.0)
    except Exception:
        pass

    # Send Back and Home keyevents to device
    run_adb(["shell", "input", "keyevent", "4"], serial=serial)
    run_adb(["shell", "input", "keyevent", "3"], serial=serial)

    stop_messages = {
        "en-IN": "Task stopped. Returning to home screen.",
        "te-IN": "టాస్క్ ఆపివేయబడింది. హోమ్ స్క్రీన్‌కు తిరిగి వెళ్తున్నాను.",
        "hi-IN": "कार्य रोक दिया गया है। होम स्क्रीन पर वापस जा रहे हैं।",
        "ta-IN": "பணி நிறுத்தப்பட்டது. முகப்புத் திரைக்குத் திரும்புகிறது.",
        "kn-IN": "ಕಾರ್ಯವನ್ನು ನಿಲ್ಲಿಸಲಾಗಿದೆ. ಮುಖಪುಟ ಪರದೆಗೆ ಹಿಂತಿರುಗಲಾಗುತ್ತಿದೆ.",
        "mr-IN": "कार्य थांबवले आहे. होम स्क्रीनवर परत जात आहे.",
        "or-IN": "କାର୍ଯ୍ୟ ବନ୍ଦ ହେଲା। ମୂଳ ପରଦାକୁ ଫେରୁଛି।",
    }
    msg = stop_messages.get(lang_code, stop_messages["en-IN"])
    gnani_synth_play(msg, lang=lang_code, play_audio=play_audio)
    return msg


LAST_RECORDED_DURATION: float = 0.0


def get_last_recorded_duration() -> float:
    """Returns the recorded audio duration in seconds of the most recent capture."""
    return LAST_RECORDED_DURATION


def record_audio(
    silence_threshold: float = 320.0,
    silence_duration: float = 1.1,
    max_timeout: float = 10.0,
    sample_rate: int = AUDIO_SAMPLE_RATE,
    output_path: str = VOICE_COMMAND_FILE,
    require_speech: bool = False,
    idle_timeout: float = 2.8,
) -> str:
    """Records audio using continuous chunk reading with dynamic Voice Activity Detection (VAD)."""
    global LAST_RECORDED_DURATION
    chunk_size = int(sample_rate * 0.1)  # 100ms
    speech_start_threshold = silence_threshold + 40.0
    speech_end_threshold = max(180.0, silence_threshold - 60.0)

    frames = []
    initial_chunks = []
    speech_started = False
    speech_start_time = None
    silence_start_time = None
    calibrated = False
    start_time = time.time()

    print(f"\n[Microphone:VAD] 🎙️  Listening with adaptive VAD (silence_break={silence_duration}s, idle={idle_timeout}s)...", flush=True)

    def handle_chunk(chunk_samples: np.ndarray) -> bool:
        nonlocal speech_started, speech_start_time, silence_start_time, calibrated, speech_start_threshold, speech_end_threshold
        frames.append(chunk_samples)
        rms = calculate_rms(chunk_samples)

        # Baseline noise floor calibration during first ~200ms
        if not calibrated:
            initial_chunks.append(rms)
            if len(initial_chunks) >= 2:
                baseline_rms = float(np.mean(initial_chunks))
                speech_start_threshold = max(silence_threshold, baseline_rms * 1.6 + 30.0)
                speech_end_threshold = max(160.0, baseline_rms * 1.15 + 15.0)
                calibrated = True

        if not speech_started:
            if rms >= speech_start_threshold:
                speech_started = True
                speech_start_time = time.time()
                print(f"[VAD] 🗣️  Speech detected (RMS: {rms:.1f} > {speech_start_threshold:.0f})! Dynamic recording active.", flush=True)
            elif require_speech and (time.time() - start_time >= idle_timeout):
                # Idle silence in continuous mode: cycle turn cleanly without burning STT API
                return True
        else:
            time_speaking = time.time() - speech_start_time
            if rms < speech_end_threshold:
                if silence_start_time is None:
                    silence_start_time = time.time()
                else:
                    silence_elapsed = time.time() - silence_start_time
                    if time_speaking >= 0.35 and silence_elapsed >= silence_duration:
                        print(f"[VAD] 🤫 Auto-silence cutoff triggered ({silence_elapsed:.2f}s trailing silence).", flush=True)
                        return True
            else:
                silence_start_time = None
        return False

    if HAS_PYAUDIO and pyaudio:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
        )
        try:
            while True:
                data = stream.read(chunk_size, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16)
                if handle_chunk(samples):
                    break
                if time.time() - start_time >= max_timeout:
                    print(f"[VAD] ⏱️  Failsafe max timeout ({max_timeout:.0f}s) reached.", flush=True)
                    break
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    else:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", blocksize=chunk_size) as stream:
            while True:
                samples, _ = stream.read(chunk_size)
                flat_samples = samples.flatten()
                if handle_chunk(flat_samples):
                    break
                if time.time() - start_time >= max_timeout:
                    print(f"[VAD] ⏱️  Failsafe max timeout ({max_timeout:.0f}s) reached.", flush=True)
                    break

    if require_speech and not speech_started:
        LAST_RECORDED_DURATION = 0.0
        return ""

    if frames:
        full_audio = np.concatenate(frames)
    else:
        full_audio = np.zeros(sample_rate, dtype=np.int16)

    recorded_duration = len(full_audio) / sample_rate
    LAST_RECORDED_DURATION = recorded_duration
    print(f"[Microphone] ✔ Recording finished ({recorded_duration:.2f}s). Saving to '{output_path}'", flush=True)
    sf.write(output_path, full_audio, sample_rate, subtype="PCM_16")
    return output_path


# ==============================================================================
# 8. Dynamic Intent Engine (Calls, WhatsApp, Search, E-Commerce, Typing)
# ==============================================================================
def match_dynamic_intent(
    transcript: str,
    serial: str = TARGET_DEVICE_SERIAL,
    lang_code: str = "en-IN",
) -> tuple[bool, str]:
    """Matches parameterized natural language voice commands using Regex."""
    clean = transcript.strip()
    lower = clean.lower()

    # 1. WhatsApp Direct Messaging
    # Pattern: "send whatsapp to [Name] saying [Message]" or "whatsapp [Name] [Message]"
    wa_m = re.search(
        r"(?:send\s+)?whatsapp\s+(?:message\s+)?(?:to\s+)?(?P<target>[a-zA-Z\s\d\+]+?)\s+(?:saying|message|with\s+text)\s+(?P<msg>.+)",
        clean,
        re.IGNORECASE,
    )
    if not wa_m:
        wa_m = re.search(r"^whatsapp\s+(?P<target>[a-zA-Z\d\+]+)\s+(?P<msg>.+)", clean, re.IGNORECASE)

    if wa_m:
        target = wa_m.group("target").strip()
        msg_text = wa_m.group("msg").strip()

        # Two-Tier Contact Resolution
        contact, score, candidate = contacts_mgr.find_contact(target)

        # Tier 2: Not found with certainty -> Ask user confirmation!
        if not contact and candidate:
            pending_action = {
                "type": "whatsapp",
                "target": candidate,
                "phone": contacts_mgr.get_all_contacts().get(candidate.lower(), {}).get("phone", ""),
                "message": msg_text,
                "prompt": f"I couldn't find {target} in your contacts. Did you mean {candidate}?",
            }
            pending_mgr.set_pending(pending_action)
            feedback = (
                f"[Ask-User] I couldn't find {target} in your contacts. "
                f"Did you mean {candidate}? Please say Yes or No."
            )
            return True, feedback

        if not contact:
            return True, f"I could not find {target} in your contacts."

        phone = contact.get("phone", "")
        clean_phone = clean_phone_number(phone)
        if not clean_phone:
            return True, f"Could not find phone number for {contact['name']}."

        encoded_msg = urllib.parse.quote(msg_text)
        wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
        print(f"[Router:WhatsApp] Sending message to {clean_phone} ({contact['name']}): '{msg_text}'")
        run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", wa_url], serial=serial)
        time.sleep(2.5)
        run_adb(["shell", "input", "keyevent", "66"], serial=serial)
        return True, f"Sending WhatsApp message to {contact['name']}: {msg_text}"

    # 2. Direct Voice Calling
    call_m = re.search(r"^(?:call|dial|make\s+a\s+call\s+to)\s+(?P<target>[a-zA-Z\s\d\+]+)", clean, re.IGNORECASE)
    if call_m:
        target = call_m.group("target").strip()
        contact, score, candidate = contacts_mgr.find_contact(target)

        # Tier 2: Disambiguation prompt
        if not contact and candidate:
            candidate_info = contacts_mgr.get_all_contacts().get(candidate.lower(), {})
            pending_action = {
                "type": "call",
                "target": candidate,
                "phone": candidate_info.get("phone", ""),
                "prompt": f"I couldn't find {target} in your contacts. Did you mean {candidate}?",
            }
            pending_mgr.set_pending(pending_action)
            feedback = (
                f"[Ask-User] I couldn't find {target} in your contacts. "
                f"Did you mean {candidate}? Please say Yes or No."
            )
            return True, feedback

        if not contact:
            return True, f"I could not find {target} in your contacts."

        phone = contact.get("phone", "")
        clean_phone = clean_phone_number(phone) or phone
        dial_phone = f"+{clean_phone}" if (clean_phone.startswith("91") and len(clean_phone) == 12) else clean_phone
        print(f"[Router:Call] Calling {contact['name']} ({dial_phone})...")
        run_adb(["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{dial_phone}"], serial=serial)

        # Native multilingual spoken confirmation
        if lang_code.startswith("te"):
            return True, f"{contact['name']}కు కాల్ చేస్తున్నాను."
        elif lang_code.startswith("ta"):
            return True, f"{contact['name']}க்கு கால் செய்கிறேன்."
        elif lang_code.startswith("hi"):
            return True, f"{contact['name']} को कॉल लगा रहा हूँ."
        return True, f"Calling {contact['name']} now."

    # 3. Universal App Launcher Intent: "open [App]" / "launch [App]"
    app_launch_m = re.match(r"^(?:open|launch|start|run|go\s+to)\s+(?P<app>[a-zA-Z0-9\s]+)$", clean, re.IGNORECASE)
    app_query = app_launch_m.group("app").strip().lower() if app_launch_m else None
    if not app_query and clean.lower() in APP_CATALOG:
        app_query = clean.lower()
    if app_query:
        if not any(conj in app_query for conj in [" and ", " then ", " download", " search", " install"]):
            success, launch_msg, fallback_data = launch_application(app_query, serial=serial)
            if success:
                return True, launch_msg
            elif fallback_data:
                # Save pending confirmation for fallback recovery!
                pending_mgr.set_pending(fallback_data)
                return True, launch_msg

    # 4. Google Play Store Search & Install
    play_m = re.search(
        r"(?:open\s+)?play\s*store\s+(?:and\s+)?(?:download|install|search\s+for|search|get)\s+(?P<app1>.+)",
        clean,
        re.IGNORECASE,
    )
    if not play_m:
        play_m = re.search(
            r"(?:download|install|get)\s+(?P<app2>.+?)\s+(?:from|on|in)\s+(?:the\s+)?play\s*store",
            clean,
            re.IGNORECASE,
        )
    if play_m:
        raw_app = (play_m.groupdict().get("app1") or play_m.groupdict().get("app2") or "").strip()
        target_app = re.sub(r"\b(?:app|game|application|some|any)\b", "", raw_app, flags=re.IGNORECASE).strip() or raw_app
        encoded = urllib.parse.quote_plus(target_app)
        run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"market://search?q={encoded}"], serial=serial)
        return True, f"Opening Google Play Store search for {target_app}."

    # 5. YouTube Deep Search
    yt_m = re.search(r"^(?:search\s+youtube\s+for|play|watch)\s+(?P<query>.+?)(?:\s+on\s+youtube)?$", clean, re.IGNORECASE)
    if yt_m and ("youtube" in lower or lower.startswith("search youtube for")):
        query = yt_m.group("query").strip()
        run_adb([
            "shell", "am", "start",
            "-a", "android.intent.action.SEARCH",
            "-p", "com.google.android.youtube",
            "--es", "query", query,
        ], serial=serial)
        return True, f"Searching YouTube for {query}."

    # 6. E-Commerce Searches (Amazon & Flipkart)
    if "amazon" in lower:
        m = re.search(r"^(?:search\s+amazon\s+for|buy\s+(?P<item_a>.+?)\s+on\s+amazon|amazon\s+(?P<item_a2>.+))", clean, re.IGNORECASE)
        if m:
            item = (m.group("item_a") or m.group("item_a2") or clean.replace("search amazon for", "")).strip()
            url = f"https://www.amazon.in/s?k={urllib.parse.quote_plus(item)}"
            run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url], serial=serial)
            return True, f"Searching Amazon for {item}."

    if "flipkart" in lower:
        m = re.search(r"^(?:search\s+flipkart\s+for|buy\s+(?P<item_f>.+?)\s+on\s+flipkart|flipkart\s+(?P<item_f2>.+))", clean, re.IGNORECASE)
        if m:
            item = (m.group("item_f") or m.group("item_f2") or clean.replace("search flipkart for", "")).strip()
            url = f"https://www.flipkart.com/search?q={urllib.parse.quote_plus(item)}"
            run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url], serial=serial)
            return True, f"Searching Flipkart for {item}."

    # 7. Voice Typing
    type_m = re.search(r"^(?:type|write|enter\s+text)\s+(?P<text>.+)", clean, re.IGNORECASE)
    if type_m:
        text_to_type = type_m.group("text").strip()
        escaped = escape_adb_text(text_to_type)
        run_adb(["shell", "input", "text", escaped], serial=serial)
        return True, f"Typed: {text_to_type}"

    return False, ""


# ==============================================================================
# 9. Static Instant ADB Control Suite (<100ms Execution)
# ==============================================================================
STATIC_FAST_ACTIONS = {
    "home": ("shell", "input", "keyevent", "3"),
    "back": ("shell", "input", "keyevent", "4"),
    "recent": ("shell", "input", "keyevent", "187"),
    "recent apps": ("shell", "input", "keyevent", "187"),
    "open notifications": ("shell", "cmd", "statusbar", "expand-notifications"),
    "quick settings": ("shell", "cmd", "statusbar", "expand-settings"),
    "lock": ("shell", "input", "keyevent", "26"),
    "wake": ("shell", "input", "keyevent", "224"),
    "screenshot": ("shell", "screencap", "-p", "/sdcard/screenshot.png"),
    "take screenshot": ("shell", "screencap", "-p", "/sdcard/screenshot.png"),
    "turn on flashlight": ("shell", "cmd", "flash_light", "set-torch", "1"),
    "flashlight on": ("shell", "cmd", "flash_light", "set-torch", "1"),
    "torch on": ("shell", "cmd", "flash_light", "set-torch", "1"),
    "turn off flashlight": ("shell", "cmd", "flash_light", "set-torch", "0"),
    "flashlight off": ("shell", "cmd", "flash_light", "set-torch", "0"),
    "torch off": ("shell", "cmd", "flash_light", "set-torch", "0"),
    "mute": ("shell", "input", "keyevent", "164"),
    "play": ("shell", "input", "keyevent", "85"),
    "pause": ("shell", "input", "keyevent", "85"),
    "scroll down": ("shell", "input", "swipe", "540", "1600", "540", "600", "300"),
    "scroll up": ("shell", "input", "swipe", "540", "600", "540", "1600", "300"),
}


def match_static_instant_action(
    transcript: str,
    serial: str = TARGET_DEVICE_SERIAL,
) -> tuple[bool, str]:
    """Matches instant (<100ms) hardware and system controls."""
    clean = transcript.strip().lower()

    if any(k in clean for k in ["volume up", "increase volume", "louder"]):
        for _ in range(3):
            run_adb(["shell", "input", "keyevent", "24"], serial=serial)
        return True, "Increased volume."

    if any(k in clean for k in ["volume down", "decrease volume", "lower volume"]):
        for _ in range(3):
            run_adb(["shell", "input", "keyevent", "25"], serial=serial)
        return True, "Decreased volume."

    if "battery" in clean:
        run_adb(["shell", "am", "start", "-a", "android.settings.BATTERY_SAVER_SETTINGS"], serial=serial)
        lvl = get_battery_level(serial)
        return True, f"Opening battery settings. Current battery level is {lvl}%." if lvl is not None else "Opening battery settings."

    if any(k == clean or k in clean for k in ["turn on flashlight", "flashlight on", "torch on", "turn on torch", "torch", "flashlight"]):
        if any(off in clean for off in ["turn off", " off", "band"]):
            return toggle_torch_samsung("off", serial=serial)
        return toggle_torch_samsung("on", serial=serial)

    if any(k == clean or k in clean for k in ["turn off flashlight", "flashlight off", "torch off", "turn off torch"]):
        return toggle_torch_samsung("off", serial=serial)

    for key, adb_args in STATIC_FAST_ACTIONS.items():
        if clean == key or clean == f"open {key}" or clean == f"turn on {key}":
            run_adb(list(adb_args), serial=serial)
            return True, f"Executing {key}."

    return False, ""


# ==============================================================================
# 10. Artemis Autonomous Agent Fallback with Auditory Narration
# ==============================================================================
def dispatch_artemis_fallback(
    transcript: str,
    serial: str = TARGET_DEVICE_SERIAL,
    lang_code: str = "en-IN",
) -> str:
    """Dispatches complex multi-step UI goals to the ARTEMIS Flash runner."""
    context = memory.find_memory_context(transcript)
    enriched_goal = f"{transcript} [Context: {context}]" if context else transcript

    feedback = f"Starting task: {transcript}. I will announce each step aloud."
    gnani_synth_play(feedback, lang=lang_code, play_audio=True)

    artemis_dir = WORKSPACE_DIR / "artemis"
    configured_profile = os.getenv("ARTEMIS_DEFAULT_PROFILE", "flash")

    env = os.environ.copy()
    venv_site = str(artemis_dir / ".venv" / "Lib" / "site-packages")
    client_src = str(artemis_dir / "packages" / "artemis-client" / "src")
    extra_paths = [venv_site, str(artemis_dir), client_src]
    existing_pp = env.get("PYTHONPATH", "")
    if existing_pp:
        extra_paths.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(extra_paths)
    env["ARTEMIS_STANDALONE"] = "1"

    artemis_cmd = [
        sys.executable, "-m", "artemis", "run",
        enriched_goal,
        "-s", serial,
        "--profile", configured_profile,
        "--standalone",
    ]
    print(f"[Artemis] Executing in {artemis_dir}: {' '.join(artemis_cmd)}")

    global active_artemis_proc
    try:
        proc = subprocess.Popen(artemis_cmd, cwd=str(artemis_dir), env=env)
        active_artemis_proc = proc
        proc.wait()

        success_messages = {
            "en-IN": "Task completed successfully.",
            "te-IN": "టాస్క్ విజయవంతంగా పూర్తయింది.",
            "hi-IN": "टास्क सफलतापूर्वक पूरा हो गया।",
            "ta-IN": "பணி வெற்றிகரமாக முடிந்தது.",
            "kn-IN": "ಕಾರ್ಯ ಯಶಸ್ವಿಯಾಗಿ ಪೂರ್ಣಗೊಂಡಿದೆ.",
            "mr-IN": "काम यशस्वीरित्या पूर्ण झाले.",
            "or-IN": "କାର୍ଯ୍ୟ ସଫଳତାର ସହ ସମାପ୍ତ ହେଲା."
        }
        stopped_messages = {
            "en-IN": "Task was stopped.",
            "te-IN": "టాస్క్ ఆపివేయబడింది.",
            "hi-IN": "टास्क रोक दिया गया।",
            "ta-IN": "பணி நிறுத்தப்பட்டது.",
            "kn-IN": "ಕಾರ್ಯವನ್ನು ನಿಲ್ಲಿಸಲಾಗಿದೆ.",
            "mr-IN": "कार्य थांबवले गेले.",
            "or-IN": "କାର୍ଯ୍ୟ ବନ୍ଦ କରାଗଲା."
        }
        error_messages = {
            "en-IN": "Task could not be completed. Please try again.",
            "te-IN": "టాస్క్ పూర్తి కాలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి.",
            "hi-IN": "टास्क पूरा नहीं हो सका। कृपया पुनः प्रयास करें।",
            "ta-IN": "பணியை முடிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
            "kn-IN": "ಕಾರ್ಯವನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
            "mr-IN": "कार्य पूर्ण होऊ शकले नाही. कृपया पुन्हा प्रयत्न करा.",
            "or-IN": "କାର୍ଯ୍ୟ ସମ୍ପୂର୍ଣ୍ଣ ହୋଇପାରିଲା ନାହିଁ। ଦୟାକରି ପୁନର୍ବାର ଚେଷ୍ଟା କରନ୍ତୁ."
        }

        if proc.returncode == 0:
            finish_msg = success_messages.get(lang_code, success_messages["en-IN"])
        elif proc.returncode in (-15, -9, 130, -2, -1) or active_artemis_proc is None:
            finish_msg = stopped_messages.get(lang_code, stopped_messages["en-IN"])
        else:
            finish_msg = error_messages.get(lang_code, error_messages["en-IN"])

        gnani_synth_play(finish_msg, lang=lang_code, play_audio=True)
        return finish_msg
    except Exception as e:
        err_msg = f"Task could not be dispatched: {e}"
        gnani_synth_play(err_msg, lang=lang_code, play_audio=True)
        return err_msg
    finally:
        active_artemis_proc = None


# ==============================================================================
# 11. Unified Command Execution Workflow
# ==============================================================================
def execute_on_device(
    transcript: str,
    serial: str = TARGET_DEVICE_SERIAL,
    lang_code: str = "en-IN",
    play_audio: bool = True,
    timer: TelemetryTimer | None = None,
) -> str:
    """Main execution orchestrator handling confirmation recovery, fast paths, and fallback."""
    if timer is None:
        timer = TelemetryTimer()

    contacts_mgr.serial = serial

    raw_input = transcript.strip()
    if not raw_input:
        msg = "I did not catch any command. Please try speaking again."
        t_tts = time.perf_counter()
        gnani_synth_play(msg, lang=lang_code, play_audio=play_audio)
        timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
        timer.report()
        return msg

    # 0. Emergency Abort / Stop Intent (Highest Precedence)
    if is_stop_command(raw_input, lang_code=lang_code):
        print(f"[Router:Emergency] 🛑 Stop requested: aborting active tasks and returning to home screen.", flush=True)
        t_abort = time.perf_counter()
        msg = abort_active_tasks(serial=serial, lang_code=lang_code, play_audio=play_audio)
        timer.exec_ms = (time.perf_counter() - t_abort) * 1000.0
        timer.tts_ms = get_last_tts_latency_ms()
        timer.report()
        return msg

    # 1. Check for Pending Confirmation (Disambiguation / Recovery Flow)
    pending = pending_mgr.get_pending()
    if pending:
        if pending_mgr.is_affirmative(raw_input):
            print(f"[Confirmation] ✔ Affirmative confirmation received ('{raw_input}'). Executing pending action!")
            action_type = pending.get("type")
            pending_mgr.clear_pending()

            t_exec = time.perf_counter()
            if action_type == "whatsapp":
                phone = clean_phone_number(pending.get("phone", ""))
                msg_text = pending.get("message", "")
                target_name = pending.get("target", "contact")
                encoded = urllib.parse.quote(msg_text)
                wa_url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded}"
                run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", wa_url], serial=serial)
                time.sleep(2.5)
                run_adb(["shell", "input", "keyevent", "66"], serial=serial)
                feedback = f"Confirmed. Sending WhatsApp to {target_name}: {msg_text}"
            elif action_type == "call":
                phone = clean_phone_number(pending.get("phone", ""))
                target_name = pending.get("target", "contact")
                dial_phone = f"+{phone}" if (phone.startswith("91") and len(phone) == 12) else phone
                run_adb(["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{dial_phone}"], serial=serial)
                feedback = f"Confirmed. Calling {target_name} now."
            elif action_type == "open_app":
                pkg = pending.get("package")
                app_name = pending.get("name") or pending.get("app_key", "application")
                run_adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], serial=serial)
                feedback = f"Confirmed. Opening {app_name}."
            else:
                feedback = "Action executed."

            timer.exec_ms = (time.perf_counter() - t_exec) * 1000.0
            t_tts = time.perf_counter()
            gnani_synth_play(feedback, lang=lang_code, play_audio=play_audio)
            timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
            timer.report()
            return feedback

        elif pending_mgr.is_negative(raw_input):
            print(f"[Confirmation] ✖ Negative confirmation received ('{raw_input}'). Cancelling pending action.")
            pending_mgr.clear_pending()
            feedback = "Action cancelled."
            t_tts = time.perf_counter()
            gnani_synth_play(feedback, lang=lang_code, play_audio=play_audio)
            timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
            timer.report()
            return feedback
        else:
            # Different command entered: clear stale confirmation and proceed
            pending_mgr.clear_pending()

    # 2. Check for Wake Word Trigger ("Vinda")
    has_trigger, stripped_command = extract_wake_word(raw_input)
    if has_trigger:
        if not stripped_command:
            prompt = TRIGGER_PROMPTS.get(lang_code, TRIGGER_PROMPTS["en-IN"])
            print(f"[WakeWord] ✨ Trigger detected! Prompting user: '{prompt}'", flush=True)
            t_tts = time.perf_counter()
            gnani_synth_play(prompt, lang=lang_code, play_audio=play_audio)
            timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
            timer.report()
            return prompt
        else:
            raw_input = stripped_command

    # 3. Pan-Indian Normalizer & Intent Routing
    t_router_start = time.perf_counter()
    clean = normalize_indian_command(raw_input, lang_code=lang_code)
    # Strip any trailing punctuation (periods from STT, question marks, commas)
    clean = re.sub(r"[.!?,;:\"']+$", "", clean).strip()
    timer.router_ms = (time.perf_counter() - t_router_start) * 1000.0

    print(f"\n======================================================================")
    print(f"⚙️  PROCESSING COMMAND [{lang_code}]: \"{clean}\" (raw: \"{raw_input}\")")
    print(f"======================================================================")

    # 4. Check for Emergency Abort on normalized text
    if is_stop_command(clean, lang_code=lang_code):
        print(f"[Router:Emergency] 🛑 Stop requested: aborting active tasks and returning to home screen.", flush=True)
        t_abort = time.perf_counter()
        msg = abort_active_tasks(serial=serial, lang_code=lang_code, play_audio=play_audio)
        timer.exec_ms = (time.perf_counter() - t_abort) * 1000.0
        timer.tts_ms = get_last_tts_latency_ms()
        timer.report()
        return msg

    # 5. Dynamic Parameterized Intent Engine
    t_exec_start = time.perf_counter()
    matched, feedback = match_dynamic_intent(clean, serial=serial, lang_code=lang_code)
    if matched:
        timer.exec_ms = (time.perf_counter() - t_exec_start) * 1000.0
        t_tts = time.perf_counter()
        gnani_synth_play(feedback, lang=lang_code, play_audio=play_audio)
        timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
        timer.report()
        return feedback

    # 6. Static Instant ADB Controls (<100ms)
    matched, feedback = match_static_instant_action(clean, serial=serial)
    if matched:
        timer.exec_ms = (time.perf_counter() - t_exec_start) * 1000.0
        t_tts = time.perf_counter()
        gnani_synth_play(feedback, lang=lang_code, play_audio=play_audio)
        timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
        timer.report()
        return feedback

    # 7. Artemis Autonomous Vision Agent Fallback
    print(f"[Router] 👉 Complex or multi-step command -> Dispatching to Autonomous Artemis Agent...")
    feedback = dispatch_artemis_fallback(clean, serial=serial, lang_code=lang_code)
    timer.exec_ms = (time.perf_counter() - t_exec_start) * 1000.0
    timer.tts_ms = get_last_tts_latency_ms()
    timer.report()
    return feedback


# ==============================================================================
# Continuous Always-On Listening Loop with Wake-Word Gating
# ==============================================================================
def run_continuous_loop(
    serial: str = TARGET_DEVICE_SERIAL,
    lang_code: str = "en-IN",
    silence_threshold: float = 320.0,
    silence_duration: float = 1.1,
    max_timeout: float = 9.0,
    play_audio: bool = True,
    require_wake_word: bool = True,
    wake_word: str = "vinda",
):
    """Continuous listening loop with Voice Activity Detection (VAD) and Wake-Word gating."""
    print("=" * 70, flush=True)
    print(f"👂 ALWAYS-ON LISTENING ACTIVE // TRIGGER: '{wake_word.upper()}' // LANG: {lang_code}", flush=True)
    print(f"Ambient conversation without '{wake_word}' will be silently filtered.", flush=True)
    print("=" * 70, flush=True)

    awaiting_command_until = 0.0

    while True:
        try:
            timer = TelemetryTimer()

            # 1. Capture audio chunk via VAD (cycles quickly on silence to remain responsive)
            audio_file = record_audio(
                silence_threshold=silence_threshold,
                silence_duration=silence_duration,
                max_timeout=max_timeout,
                output_path=VOICE_COMMAND_FILE,
                require_speech=True,
                idle_timeout=2.8,
            )

            # Check if file has audio
            if not audio_file or not os.path.exists(audio_file) or os.path.getsize(audio_file) < 1000:
                time.sleep(0.05)
                continue

            timer.vad_duration_s = get_last_recorded_duration()

            # 2. Transcribe via Gnani STT
            t_stt_start = time.perf_counter()
            transcript = gnani_transcribe(audio_file, lang=lang_code)
            timer.stt_ms = get_last_stt_latency_ms() or ((time.perf_counter() - t_stt_start) * 1000.0)

            raw = transcript.strip() if transcript else ""
            if not raw:
                continue

            now = time.time()
            in_awaiting_window = (now < awaiting_command_until)

            # 3. Emergency STOP / ABORT check (ALWAYS active, with or without trigger name!)
            if is_stop_command(raw, lang_code=lang_code):
                print(f"[Router:Emergency] 🛑 Stop requested: aborting active tasks and returning to Home.", flush=True)
                abort_active_tasks(serial=serial, lang_code=lang_code, play_audio=play_audio)
                awaiting_command_until = 0.0
                timer.report()
                continue

            # 4. Pending confirmation check
            if pending_mgr.get_pending():
                execute_on_device(raw, serial=serial, lang_code=lang_code, play_audio=play_audio, timer=timer)
                awaiting_command_until = 0.0
                continue

            # 5. Check for Wake Word Trigger ("Vinda")
            has_trigger, stripped_command = extract_wake_word(raw, wake_word=wake_word)

            if has_trigger:
                if not stripped_command:
                    # User said just "Vinda" or "Hey Vinda"!
                    prompt = TRIGGER_PROMPTS.get(lang_code, TRIGGER_PROMPTS["en-IN"])
                    print(f"[WakeWord] ✨ Trigger detected! Prompting user: '{prompt}'", flush=True)
                    t_tts = time.perf_counter()
                    gnani_synth_play(prompt, lang=lang_code, play_audio=play_audio)
                    timer.tts_ms = get_last_tts_latency_ms() or ((time.perf_counter() - t_tts) * 1000.0)
                    timer.report()
                    # Grant a 10-second active window where the user can speak the task directly
                    awaiting_command_until = time.time() + 10.0
                    continue
                else:
                    # User said "Vinda open YouTube" or similar in one sentence!
                    print(f"[WakeWord] 🚀 Trigger + Command: '{stripped_command}'", flush=True)
                    awaiting_command_until = 0.0
                    execute_on_device(stripped_command, serial=serial, lang_code=lang_code, play_audio=play_audio, timer=timer)
                    continue

            # 6. If inside the awaiting command window, treat raw as the command
            if in_awaiting_window:
                print(f"[WakeWord] 🎯 Command received during active window: '{raw}'", flush=True)
                awaiting_command_until = 0.0
                execute_on_device(raw, serial=serial, lang_code=lang_code, play_audio=play_audio, timer=timer)
                continue

            # 7. Ambient conversation filtering
            if require_wake_word:
                print(f"[WakeWord] 🤫 Ambient conversation filtered (No '{wake_word}' trigger): \"{raw}\"", flush=True)
                timer.report()
                continue
            else:
                # If wake word not required, execute directly
                execute_on_device(raw, serial=serial, lang_code=lang_code, play_audio=play_audio, timer=timer)

        except KeyboardInterrupt:
            print("[Continuous] Stopped by user.", flush=True)
            break
        except Exception as exc:
            print(f"[Continuous] Error in listening loop: {exc}", flush=True)
            time.sleep(0.5)


# ==============================================================================
# 12. Main CLI Entry Point
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Pan-Indian Autonomous Voice OS")
    parser.add_argument("--simulate", "-s", type=str, help="Simulate voice command via text")
    parser.add_argument("--text-only", "-t", type=str, help="Skip audio and route text command")
    parser.add_argument("--lang", "-l", type=str, default="en-IN", help="Language code or name (e.g. te-IN, telugu, hi-IN, en-IN)")
    parser.add_argument("--voice", "-v", type=str, default=None, help="Timbre TTS voice name (Lakshmi, Shivani, Avinash, Nalini)")
    parser.add_argument("--device", "-d", type=str, default=TARGET_DEVICE_SERIAL, help=f"Device serial (default: {TARGET_DEVICE_SERIAL})")
    parser.add_argument("--silence-threshold", type=float, default=320.0, help="RMS silence threshold for VAD")
    parser.add_argument("--silence-duration", type=float, default=1.1, help="Silence cutoff duration in seconds")
    parser.add_argument("--max-timeout", type=float, default=10.0, help="Failsafe max recording timeout")
    parser.add_argument("--no-audio-output", action="store_true", help="Bypass speaker audio playback")
    parser.add_argument("--continuous", "-c", action="store_true", help="Always-listening continuous loop")
    parser.add_argument("--wake-word", "-w", type=str, default="vinda", help="Trigger word (default: vinda)")
    parser.add_argument("--require-wake-word", action="store_true", default=False, help="Require trigger word to execute commands; ignore ambient chatter")
    args = parser.parse_args()

    canonical_lang = resolve_language(args.lang)
    lang_info = PAN_INDIAN_LANGUAGES.get(canonical_lang, PAN_INDIAN_LANGUAGES["en-IN"])

    global ACTIVE_VOICE
    if args.voice:
        ACTIVE_VOICE = args.voice
    elif not ACTIVE_VOICE:
        ACTIVE_VOICE = lang_info.get("default_voice", "Lakshmi")

    print("=" * 70)
    print("🎙️  PAN-INDIAN MULTILINGUAL VOICE OS // SAMSUNG GALAXY A36")
    print(f"Target Device: {args.device}")
    print(f"Language: {lang_info['name']} ({canonical_lang}) // Voice: {ACTIVE_VOICE}")
    print(f"Memory Contacts: {len(memory.data.get('contacts', {}))} | Device Contacts: {len(contacts_mgr.get_all_contacts())}")
    print("=" * 70)

    # Mode 1: Text-only
    if args.text_only:
        timer = TelemetryTimer()
        execute_on_device(args.text_only, serial=args.device, lang_code=canonical_lang, play_audio=not args.no_audio_output, timer=timer)
        return

    # Mode 2: Simulated voice (synthesize command audio first, then test full STT loop)
    if args.simulate:
        timer = TelemetryTimer()
        print(f"\n[Simulation] Synthesizing command audio for: '{args.simulate}' ({canonical_lang})...")
        synthesize_speech(args.simulate, output_path=VOICE_COMMAND_FILE, lang=canonical_lang)
        t_stt = time.perf_counter()
        transcript = gnani_transcribe(VOICE_COMMAND_FILE, lang=canonical_lang)
        timer.stt_ms = get_last_stt_latency_ms() or ((time.perf_counter() - t_stt) * 1000.0)
        execute_on_device(transcript or args.simulate, serial=args.device, lang_code=canonical_lang, play_audio=not args.no_audio_output, timer=timer)
        return

    # Mode 3: Continuous Always-On Listening with Wake Word
    if args.continuous:
        run_continuous_loop(
            serial=args.device,
            lang_code=canonical_lang,
            silence_threshold=args.silence_threshold,
            silence_duration=args.silence_duration,
            max_timeout=args.max_timeout,
            play_audio=not args.no_audio_output,
            require_wake_word=True,
            wake_word=args.wake_word,
        )
        return

    # Mode 4: Live Single-Shot Microphone capture with dynamic VAD
    timer = TelemetryTimer()
    audio_file = record_audio(
        silence_threshold=args.silence_threshold,
        silence_duration=args.silence_duration,
        max_timeout=args.max_timeout,
        output_path=VOICE_COMMAND_FILE,
    )
    timer.vad_duration_s = get_last_recorded_duration()
    t_stt = time.perf_counter()
    transcript = gnani_transcribe(audio_file, lang=canonical_lang)
    timer.stt_ms = get_last_stt_latency_ms() or ((time.perf_counter() - t_stt) * 1000.0)
    execute_on_device(transcript, serial=args.device, lang_code=canonical_lang, play_audio=not args.no_audio_output, timer=timer)


if __name__ == "__main__":
    main()
