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

"""Pan-Indian Multilingual Speech-to-Text & Text-to-Speech Bridge using Gnani AI.

Integrates Gnani Prisma v3.0 (STT) and Gnani Timbre v3.0 (TTS) with support for:
- English (India) [en-IN]
- Telugu (తెలుగు) [te-IN]
- Tamil (தமிழ்) [ta-IN]
- Kannada (ಕನ್ನಡ) [kn-IN]
- Hindi (हिन्दी) [hi-IN]
- Marathi (मराठी) [mr-IN]
- Odia (ଓଡ଼ିଆ) [or-IN]
"""

import json
import os
from pathlib import Path
import sys
import time

import requests
import sounddevice as sd
import soundfile as sf

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv(Path(__file__).resolve().parent / "artemis" / ".env")
except ImportError:
    pass

# ==============================================================================
# Gnani API Credentials & Endpoints
# ==============================================================================
GNANI_API_KEY = os.getenv(
    "GNANI_API_KEY",
    "vach_1ytE2CY5X2EduQ4nyGf84GfIvTvKAP4wH5OsfQ2woUHE3xrsRKK8dCSt9BTqAdqPjuxDHTfj18VIv5PWIvlOTir1CONIYqPa_08a03714455c84a662a38e5577a5de12",
).strip()
KEY_ID_HEADER = os.getenv("GNANI_KEY_ID", "G1o2v3i4n5daS7aiKiran").strip()

STT_ENDPOINT = "https://api.vachana.ai/stt/v3"
STT_MODEL = "prisma-v3.0"

TTS_ENDPOINT = "https://api.vachana.ai/api/v1/tts/inference"
TTS_MODEL = "timbre-v3.0"

# ==============================================================================
# Pan-Indian Language Configuration (STT & TTS)
# ==============================================================================
PAN_INDIAN_LANGUAGES = {
    "en-IN": {
        "name": "English",
        "native": "English (India)",
        "stt_code": "en-IN",
        "tts_code": "en-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash", "Nalini"],
    },
    "te-IN": {
        "name": "Telugu",
        "native": "తెలుగు",
        "stt_code": "te-IN",
        "tts_code": "te-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
    "ta-IN": {
        "name": "Tamil",
        "native": "தமிழ்",
        "stt_code": "ta-IN",
        "tts_code": "ta-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
    "kn-IN": {
        "name": "Kannada",
        "native": "ಕನ್ನಡ",
        "stt_code": "kn-IN",
        "tts_code": "kn-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
    "hi-IN": {
        "name": "Hindi",
        "native": "हिन्दी",
        "stt_code": "hi-IN",
        "tts_code": "hi-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
    "mr-IN": {
        "name": "Marathi",
        "native": "मराठी",
        "stt_code": "mr-IN",
        "tts_code": "mr-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
    "or-IN": {
        "name": "Odia",
        "native": "ଓଡ଼ିଆ",
        "stt_code": "or-IN",
        "tts_code": "or-IN",
        "default_voice": "Lakshmi",
        "fallback_voices": ["Shivani", "Avinash"],
    },
}

LANGUAGE_ALIASES = {
    "en": "en-IN", "english": "en-IN", "en-in": "en-IN", "indian english": "en-IN",
    "te": "te-IN", "telugu": "te-IN", "te-in": "te-IN", "తెలుగు": "te-IN",
    "ta": "ta-IN", "tamil": "ta-IN", "ta-in": "ta-IN", "தமிழ்": "ta-IN",
    "kn": "kn-IN", "kannada": "kn-IN", "kn-in": "kn-IN", "ಕನ್ನಡ": "kn-IN",
    "hi": "hi-IN", "hindi": "hi-IN", "hi-in": "hi-IN", "हिन्दी": "hi-IN", "हिंदी": "hi-IN",
    "mr": "mr-IN", "marathi": "mr-IN", "mr-in": "mr-IN", "मराठी": "mr-IN",
    "or": "or-IN", "odia": "or-IN", "oriya": "or-IN", "or-in": "or-IN", "ଓଡ଼ିଆ": "or-IN",
}


def resolve_language(lang_input: str | None) -> str:
    """Resolves arbitrary language name or abbreviation into a canonical Gnani code."""
    if not lang_input:
        return "en-IN"
    cleaned = str(lang_input).strip().lower()
    return LANGUAGE_ALIASES.get(cleaned, LANGUAGE_ALIASES.get(cleaned.replace("_", "-"), "en-IN"))


# ==============================================================================
# Speech-to-Text (STT) via Gnani Prisma v3.0
# ==============================================================================
def transcribe_audio(audio_path: str, lang: str = "en-IN") -> str:
    """Sends audio to Gnani Prisma v3.0 STT endpoint in the specified Indian language."""
    canonical_lang = resolve_language(lang)
    lang_info = PAN_INDIAN_LANGUAGES.get(canonical_lang, PAN_INDIAN_LANGUAGES["en-IN"])
    stt_lang_code = lang_info["stt_code"]

    print(f"[STT] 📤 Uploading '{audio_path}' to Gnani Prisma v3.0 ({lang_info['name']} - {stt_lang_code})...")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file '{audio_path}' not found.")

    headers = {
        "X-API-Key-ID": GNANI_API_KEY,
        "X-User-Key-ID": KEY_ID_HEADER,
    }

    try:
        with open(audio_path, "rb") as f:
            files = {"audio_file": (Path(audio_path).name, f, "audio/wav")}
            data = {
                "language_code": stt_lang_code,
                "model": STT_MODEL,
            }
            resp = requests.post(STT_ENDPOINT, headers=headers, files=files, data=data, timeout=20)

        # Retry with Bearer auth if 401
        if resp.status_code == 401:
            headers = {"X-API-Key-ID": KEY_ID_HEADER, "Authorization": f"Bearer {GNANI_API_KEY}"}
            with open(audio_path, "rb") as f:
                files = {"audio_file": (Path(audio_path).name, f, "audio/wav")}
                resp = requests.post(STT_ENDPOINT, headers=headers, files=files, data=data, timeout=20)

        if resp.status_code != 200:
            print(f"[STT] ❌ HTTP {resp.status_code} Error: {resp.text}")
            return ""

        result = resp.json()
        transcript = result.get("transcript", "").strip()
        latency = result.get("end_to_end_latency", result.get("processing_time", 0))
        print(f"[STT] ✔ HTTP 200 OK | Transcribed ({stt_lang_code}): \"{transcript}\" (Latency: {latency:.3f}s)")
        return transcript

    except Exception as exc:
        print(f"[STT] ❌ Exception during transcription: {exc}")
        return ""


# ==============================================================================
# Text-to-Speech (TTS) via Gnani Timbre v3.0
# ==============================================================================
def synthesize_speech(
    text: str,
    output_path: str = "response.wav",
    lang: str = "en-IN",
    voice: str | None = None,
) -> str:
    """Synthesizes speech in any of the 7 Pan-Indian languages via Gnani Timbre."""
    canonical_lang = resolve_language(lang)
    lang_info = PAN_INDIAN_LANGUAGES.get(canonical_lang, PAN_INDIAN_LANGUAGES["en-IN"])
    tts_lang_code = lang_info["tts_code"]
    selected_voice = voice or lang_info["default_voice"]

    print(f"[TTS] 🔊 Synthesizing ({lang_info['name']} - {selected_voice}): \"{text}\"")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key-ID": GNANI_API_KEY,
        "X-User-Key-ID": KEY_ID_HEADER,
    }

    payload = {
        "text": text,
        "voice": selected_voice,
        "model": TTS_MODEL,
        "language": tts_lang_code,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": "wav",
            "sample_rate": 16000,
        },
    }

    try:
        resp = requests.post(TTS_ENDPOINT, json=payload, headers=headers, timeout=15)

        # Retry with Bearer auth on 401
        if resp.status_code == 401:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key-ID": KEY_ID_HEADER,
                "Authorization": f"Bearer {GNANI_API_KEY}",
            }
            resp = requests.post(TTS_ENDPOINT, json=payload, headers=headers, timeout=15)

        # Fallback to Lakshmi if voice rejected
        if resp.status_code != 200 and selected_voice != "Lakshmi":
            print(f"[TTS] Retrying with universal voice 'Lakshmi'...")
            payload["voice"] = "Lakshmi"
            resp = requests.post(TTS_ENDPOINT, json=payload, headers=headers, timeout=15)

        if resp.status_code == 200 and resp.content:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"[TTS] ✔ HTTP 200 OK | Audio saved to '{output_path}' ({len(resp.content)} bytes)")
            return output_path
        else:
            print(f"[TTS] ❌ HTTP {resp.status_code} Error: {resp.text}")
            return ""

    except Exception as exc:
        print(f"[TTS] ❌ Exception during speech synthesis: {exc}")
        return ""


# ==============================================================================
# Audio Playback
# ==============================================================================
def play_audio_file(audio_path: str):
    """Plays WAV audio through the system default output speakers."""
    if not os.path.exists(audio_path):
        return
    try:
        data, fs = sf.read(audio_path)
        sd.play(data, fs)
        sd.wait()
    except Exception as exc:
        print(f"[AudioPlay] Warning: Could not play audio through speakers: {exc}")


def synthesize_and_play(
    text: str,
    output_path: str = "response.wav",
    lang: str = "en-IN",
    voice: str | None = None,
    play_audio: bool = True,
) -> str:
    """Synthesizes speech and immediately plays it aloud through speakers."""
    res_path = synthesize_speech(text, output_path=output_path, lang=lang, voice=voice)
    if res_path and play_audio:
        play_audio_file(res_path)
    return res_path
