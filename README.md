# 🎙️ Dhwani (ध्वनि / ధ్వని / ಧ್ವನಿ / த்வனி / ध्वनि / ଧ୍ୱନି)
### Pan-Indian Multilingual Autonomous Voice Operating System for Android

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Android 10-15](https://img.shields.io/badge/android-10--15%20(One%20UI%20%2F%20AOSP)-green.svg)](https://developer.android.com/)
[![Gnani.ai Voice](https://img.shields.io/badge/voice-Gnani.ai%20Prisma%20%26%20Timbre%20v3.0-orange.svg)](https://gnani.ai)
[![Latency](https://img.shields.io/badge/fast--path-12ms%20ADB%20Intent-brightgreen.svg)]()
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Dhwani** (*Sanskrit/Hindi/Telugu/Kannada for "Sound / Voice"*) is an accessibility-first, autonomous mobile voice operating system built specifically for the **elderly, visually impaired, physically disabled, and vernacular Indian language speakers**.

Dhwani empowers users who cannot read English or navigate dense touchscreens to control their Android smartphone entirely through natural, colloquial speech across **7 Indian languages** (Telugu, Tamil, Kannada, Hindi, Marathi, Odia, and Indian English), with real-time auditory step-by-step feedback.

---

## 🌟 Why Dhwani?

Traditional voice assistants (Siri, Google Assistant, Alexa) are heavily English-centric, fail on native Indic grammatical structures (Subject-Object-Verb / SOV), struggle with Indian English colloquialisms, and halt when an app or contact isn't found. 

Dhwani introduces a fundamentally different paradigm:
1. **Accessibility First (Blind & Elderly)**: Speaks every action aloud at each step via high-fidelity Indian TTS (`Lakshmi`). Users always know what is happening without looking at the screen.
2. **Dual-Speed Execution Architecture**:
   - **⚡ 12ms Fast-Path Intent Engine**: High-frequency tasks (calling, WhatsApp messaging, hardware controls, app switching, YouTube searches) bypass heavy LLMs and execute instantly via direct ADB Android intents.
   - **🤖 Artemis Autonomous Vision Agent**: Complex, dynamic, multi-step tasks across third-party apps automatically route to an autonomous multimodal vision agent powered by OpenRouter / Gemini 2.5 Flash.
3. **Colloquial & Vernacular Phonetic Normalizer**: Understands native Indic scripts, transliterated Hinglish/Tanglish/Teluglish, and common speech recognition distortions (`"what's up"`, `"thasup"` $\rightarrow$ `"whatsapp"`; `"touch light"` $\rightarrow$ `"flashlight"`).
4. **Interactive Disambiguation & Cross-App Fallback**: If a contact or app isn't found, Dhwani never hangs. It finds the nearest phonetic match (e.g. *Rakesh* $\rightarrow$ *Rahul*) or installed category alternatives (e.g. *Blinkit* $\rightarrow$ *Zepto*) and politely asks for confirmation.
5. **Hardware Integration for Samsung One UI & AOSP**: Tested on physical hardware (Samsung Galaxy A36), overcoming One UI-specific constraints such as Quick Settings hardware tile flashlight toggling and live contact database querying.

---

## 🌐 Supported Languages & Dialects

Dhwani integrates **Gnani.ai Prisma v3.0 STT** and **Timbre v3.0 TTS** for pan-Indian vernacular support:

| Language | Code | Native Script | Spoken Example | Normalized Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Telugu** | `te-IN` | తెలుగు | *"నాన్న కి కాల్ చేయి"* / *"వాట్సాప్ తెరువు"* | `call nanna` / `open whatsapp` |
| **Tamil** | `ta-IN` | தமிழ் | *"அப்பாவுக்கு கால் பண்ணு"* / *"யூடியூப் ஓபன்"* | `call appa` / `open youtube` |
| **Kannada** | `kn-IN` | ಕನ್ನಡ | *"ಅಪ್ಪನಿಗೆ ಕಾಲ್ ಮಾಡು"* / *"ಟಾರ್ಚ್ ಆನ್ ಮಾಡು"* | `call appa` / `turn on flashlight` |
| **Hindi** | `hi-IN` | हिन्दी | *"पापा को कॉल करो"* / *"व्हाट्सएप खोलो"* | `call papa` / `open whatsapp` |
| **Marathi** | `mr-IN` | मराठी | *"बाबांना कॉल करा"* / *"मेसेज पाठवा"* | `call baba` / `send message` |
| **Odia** | `or-IN` | ଓଡ଼ିଆ | *"ବାପାଙ୍କୁ କଲ୍ କର"* / *"ଖୋଲ ୟୁଟ୍ୟୁବ୍"* | `call bapa` / `open youtube` |
| **Indian English** | `en-IN` | English | *"Put what's up message to Rahul saying hello"* | `send whatsapp to rahul saying hello` |

---

## 🏗️ Architecture Overview

```
                      🎙️ Spoken Voice / Web Console / PTT [Space]
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │   Dynamic Silence VAD (RMS Chunking)     │
                  └────────────────────┬─────────────────────┘
                                       │ Raw Audio (.wav)
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │    Gnani.ai Prisma v3.0 Multilingual STT │
                  └────────────────────┬─────────────────────┘
                                       │ Raw Transcript
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │  4-Stage Pan-Indian Phonetic Normalizer  │
                  │  • Indic Dictionary & Action Mappings    │
                  │  • Colloquialism & STT Distortions       │
                  │  • SOV-to-SVO Grammar Inversion          │
                  │  • Two-Tier Fuzzy Contact Matching       │
                  └────────────────────┬─────────────────────┘
                                       │ Clean Normalized Command
                                       ▼
                     ┌────────────────────────────────────┐
                     │ Intent Classifier & Router Engine  │
                     └───────┬────────────────────┬───────┘
                             │                    │
              [Sub-100ms Known Action]    [Complex Multi-Step Task]
                             │                    │
                             ▼                    ▼
             ┌─────────────────────────┐  ┌─────────────────────────┐
             │ ⚡ Fast-Path ADB Engine │  │ 🤖 Artemis Vision Agent │
             │ • am start ACTION_CALL  │  │ • OpenRouter 2.5 Flash  │
             │ • WhatsApp Direct URL   │  │ • Screenshot Grounding  │
             │ • Samsung QS Flashlight │  │ • Multi-turn Action Loop│
             │ • Volume / Battery / UI │  │ • Human-in-the-Loop VAD │
             └───────────────┬─────────┘  └─────────────┬───────────┘
                             │                          │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                  ┌──────────────────────────────────────────┐
                  │   Timbre v3.0 Step-by-Step Spoken TTS    │
                  │        (Lakshmi Universal Voice)         │
                  └──────────────────────────────────────────┘
```

---

## ⚡ Core Capabilities

### 1. 4-Stage Multilingual & Phonetic Normalizer
- **Native Unicode Script Support**: Bypasses regex `\b` word boundary limitations on combining vowel signs (matras) and viramas across Indic scripts.
- **SOV-to-SVO Grammar Inversion**: Converts Indian language Subject-Object-Verb phrasing (`"nanna call"`, `"whatsapp open"`, `"torch turn on"`) into canonical imperative SVO commands (`"call nanna"`, `"open whatsapp"`, `"turn on torch"`).
- **Phonetic App Auto-Correction**: Maps speech distortions (`"what's up"`, `"watsapp"`, `"thasup"` $\rightarrow$ `"whatsapp"`; `"crome"` $\rightarrow$ `"chrome"`; `"play star"` $\rightarrow$ `"play store"`).
- **Bare App Launcher**: Instantly launches apps by name alone (`"whatsapp"`, `"settings"`, `"zepto"`).

### 2. Interactive Disambiguation & Cross-App Fallback
- **Missing Contact Disambiguation**: Queries the phone's live Android Contacts database (`content://com.android.contacts/data/phones`). If the exact name is missing, finds the nearest phonetic match and asks:
  > *"I couldn't find Rakesh in your contacts. Did you mean Rahul? Please say Yes or No."*
- **Uninstalled App Category Fallback**: If an app isn't installed, queries the live package manager and recommends an installed category alternative:
  > *"Blinkit is not installed on your phone. Would you like me to open Zepto instead? Please say Yes or No."*
- **Persistent Confirmation State**: Stores suggestions in `pending_confirmation.json`. Responding affirmatively (`"Yes"`, `"Haan"`, `"Avunu"`, `"Aama"`, `"Haudu"`) executes the pending action instantly.

### 3. Sub-100ms Hardware & System Controls
- **Samsung One UI Hardware Flashlight**: Toggles physical LED via Quick Settings panel coordinate automation (`cmd statusbar expand-settings` $\rightarrow$ `input tap 651 480` $\rightarrow$ `cmd statusbar collapse`), with state inspection via `dumpsys media.camera`.
- **Battery Status & Audio Level**: Opens battery saver settings and announces current percentage aloud.
- **Hardware Keys**: Instant sub-second Volume Up/Down, Mute, Take Screenshot, Home, Back, and Recent Apps.

### 4. Universal 50+ App Catalog
Pre-mapped with verified package names, launch activities, and fallback categories:
- **Food & Grocery**: Blinkit, Zepto, Swiggy, Zomato, BigBasket.
- **Payments & Banking**: GPay, PhonePe, Paytm, BHIM.
- **Travel & Transit**: Uber, Ola, Rapido, Where Is My Train, IRCTC, RedBus.
- **Shopping**: Amazon, Flipkart, Myntra, Meesho.
- **Media & Social**: WhatsApp, YouTube, Instagram, Spotify, JioSaavn, JioCinema, Hotstar.

---

## 🎨 Neo-Humanist Minimalist Web Console

Dhwani features a web console running at **`http://localhost:5000`**:

- **Pure-White Canvas (`#FFFFFF`)**: High-contrast, clean typography (Plus Jakarta Sans & JetBrains Mono) designed for elderly readability.
- **Pan-Indian Language Pill Bar**: 1-click language toggling (`EN`, `TE`, `TA`, `KN`, `HI`, `MR`, `OR`).
- **Tactile Push-to-Talk (PTT)**: Oversized pill switch with real-time RMS Voice Activity Equalizer and hotkey support (`Space` to talk, `Esc` to stop).
- **Barge-In Emergency Stop `[Esc]`**: Instantly halts any running autonomous agent task or audio capture and returns the device to the Home screen.
- **Interactive Disambiguation Banner**: Surfaces `[Yes, Proceed]` and `[No, Cancel]` buttons during ambiguities.
- **Saved Contacts Vault**: Direct `[Call]` and `[WA]` buttons, `[+ Add]` VIP contact modal, `[✕]` instant delete, and `[↻ Sync]` to pull contacts from phone.
- **Real-Time Telemetry Terminal**: Streams line-by-line ADB bus events, STT transcripts, and routing decisions.

---

## 🚀 Quick Start

### Prerequisites
1. **Python 3.10+** (Virtual environment recommended)
2. **Android Device or Emulator**:
   - Enable **Developer Options** and **USB Debugging** on your phone.
   - Connect via USB: verify with `adb devices`.
3. **Gnani.ai API Key**: For Indian multilingual STT and TTS ([Gnani.ai](https://gnani.ai)).
4. **OpenRouter / Gemini API Key**: For autonomous vision agent fallback ([OpenRouter](https://openrouter.ai)).

### Installation

```bash
# 1. Clone repository
git clone https://github.com/GovindaSaiKiran/Dhwani.git
cd Dhwani

# 2. Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
# Or using uv:
uv pip install -e artemis
```

### Configuration

Copy `.env.example` to `.env` and insert your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# API Keys
GNANI_API_KEY=your_gnani_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Target Android Device
TARGET_DEVICE_SERIAL=your_device_serial_here  # Run 'adb devices' to find
ADB_HOST=127.0.0.1
ADB_PORT=5037
```

### Launching Dhwani

#### Option A: Web Console (Recommended)
```bash
python web_ui.py
```
Open **`http://localhost:5000`** in your browser.

#### Option B: Command Line Interface (CLI)
```bash
# Live microphone mode (Default English)
python voice_commander.py

# Live microphone in Telugu
python voice_commander.py --lang te-IN

# Direct text simulation mode
python voice_commander.py --simulate "నాన్న కి కాల్ చేయి" --lang te-IN
python voice_commander.py --simulate "Open Zepto"
python voice_commander.py --simulate "turn on flashlight"
```

---

## 📁 Repository Structure

```
Dhwani/
├── voice_commander.py     # Main Pan-Indian Voice OS orchestrator & intent engine
├── web_ui.py              # Neo-Humanist Modern Design Web Console (Flask + Socket.IO)
├── gnani_bridge.py        # Gnani.ai Prisma v3.0 STT & Timbre v3.0 TTS pipeline
├── user_memory.json       # Persistent user memory & VIP contact vault
├── verify_voice_os.py     # End-to-end hardware verification suite
├── .env.example           # Example configuration template
├── .gitignore             # Git exclusion rules
├── requirements.txt       # Python dependencies
└── artemis/               # Artemis autonomous multimodal agent framework
    ├── artemis/           # Agent execution graphs, planners, and operators
    ├── config/            # System & LLM router configurations
    └── mcp_server/        # Model Context Protocol tools & ADB interfaces
```

---

## 🔌 API Endpoints

The Web Console exposes a clean REST & WebSocket API:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Serves the Neo-Humanist Web Console |
| `GET /api/memory` | `GET` | Fetches saved contacts and user profile |
| `POST /api/contacts/add` | `POST` | Adds a new contact (`{"name": "...", "phone": "..."}`) |
| `POST /api/contacts/delete` | `POST` | Deletes a contact (`{"name": "..."}`) |
| `POST /api/contacts/sync` | `POST` | Pulls live contacts from Android device via ADB |
| `POST /api/listen` | `POST` | Activates microphone recording with VAD (`?lang=te-IN`) |
| `POST /api/simulate` | `POST` | Executes text prompt simulation (`?prompt=...&lang=...`) |
| `POST /api/stop` | `POST` | Emergency abort: kills running tasks and returns phone to Home |

---

## 🛡️ Privacy & Safety
- **Local Contact Storage**: Contacts and memory are saved locally in `user_memory.json` on your machine.
- **Credential Protection**: API keys are isolated in `.env` and never tracked or committed.
- **Hardware Sandboxing**: All ADB interactions run strictly against the authorized target device serial.

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) to add new Indian languages, app package mappings, or accessibility features.

---

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
