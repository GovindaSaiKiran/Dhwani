# 🎙️ Dhwani (ध्वनि / ధ్వని / ಧ್ವನಿ / த்வனி / ध्वनि / ଧ୍ୱନି)
### Autonomous Pan-Indian Voice Operating System for Android
**100% Hands-Free & Eyes-Free Smartphone Control for the Blind, Rural Citizens, Elderly, and Vernacular Speakers**

[![Gnani.ai Voice](https://img.shields.io/badge/Powered%20By-Gnani.ai%20STT%20%26%20TTS%20APIs-orange.svg?style=for-the-badge&logo=sound)](https://gnani.ai)
[![Gnani Hackathon](https://img.shields.io/badge/Built%20For-Gnani.ai%20Hackathon%202026-blueviolet.svg?style=for-the-badge)](https://gnani.ai)
[![Accessibility](https://img.shields.io/badge/Accessibility-Blind%20%26%20Elderly%20First-green.svg?style=for-the-badge)](https://developer.android.com)
[![Fast Path](https://img.shields.io/badge/Fast--Path-12ms%20Instant%20Execution-brightgreen.svg?style=for-the-badge)]()
[![Web Console](https://img.shields.io/badge/Web%20Console-Neo--Humanist%20Figma%20UI-blue.svg?style=for-the-badge)](http://localhost:5000)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](LICENSE)

---

## 🏆 Built for the Gnani.ai Hackathon 2026

> [!IMPORTANT]
> **Dhwani** was conceptualized, architected, and built for the **Gnani.ai Hackathon 2026**.
> The technological core is powered by **Gnani.ai's Conversational AI Platform**, utilizing **Gnani Prisma v3.0 Speech-to-Text (STT)** and **Gnani Timbre v3.0 Text-to-Speech (TTS)** to eliminate the literacy, digital, and language barrier for over 500 million underserved Indian citizens.

---

## 🇮🇳 The Problem: The Digital Divide in India

Over **500 million people in India**—including **visually impaired individuals, illiterate citizens, rural populations, and the elderly**—own or have access to an Android smartphone but cannot operate modern visual touchscreens.

### Why Existing Solutions Fail:
1. **Dense, Visual-Only User Interfaces**: Touchscreens are flat, non-tactile sheets of glass. Interacting requires reading small text, interpreting icons, dismissing system popups, and navigating nested menus.
2. **English-Centric Voice Assistants**: Siri, Alexa, and Google Assistant are designed for urban English and standard Hindi. They fail on rural regional dialects, colloquial pronunciations, and Subject-Object-Verb (SOV) Indic sentence structures.
3. **No Continuous Auditory Feedback**: When Google Assistant performs an action, it frequently renders a silent card or web search link on the screen. A blind user cannot see whether their message was sent or what failed.
4. **App Inactivity**: Traditional voice assistants can only launch an app or search the web. They cannot autonomously navigate inside third-party apps to click buttons, fill forms, or complete complex real-world workflows.

---

## 💡 What is Dhwani?

**Dhwani** (*Sanskrit & Indic for "Sound / Voice"*) is an **Autonomous Pan-Indian Voice Operating System for Android** that transforms any Android smartphone into a **100% voice-driven, eyes-free companion**.

With Dhwani, users **never have to look at the screen or touch the phone**. They speak naturally in their mother tongue—**Telugu, Tamil, Kannada, Hindi, Marathi, Odia, or Indian English**—and Dhwani autonomously operates the device, executing tasks and speaking aloud every action at each step.

```
                     🗣️ Natural Vernacular Speech
               ("విందా, నాన్న కి వాట్సాప్ మెసేజ్ పెట్టు...")
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   GNANI.AI PRISMA v3.0 MULTILINGUAL SPEECH-TO-TEXT     │
       │     (Native Indic Scripts, Dialects & Accents)         │
       │       te-IN | ta-IN | kn-IN | hi-IN | mr-IN | or-IN    │
       └────────────────────────────┬───────────────────────────┘
                                    │ Raw Transcript
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │     4-STAGE PAN-INDIAN PHONETIC & SOV NORMALIZER       │
       │   • Wake-Word Gating ("Vinda" / "విందా" trigger engine) │
       │   • Translates Indic verbs (తెరువు/खोलो ➔ open)        │
       │   • Fixes colloquialisms ("what's up" ➔ whatsapp)      │
       │   • Inverts SOV grammar (నాన్న కి కాల్ ➔ call nanna)    │
       │   • Fuzzy matches nearest contacts & app names         │
       └────────────────────────────┬───────────────────────────┘
                                    │ Clean Intent
                                    ▼
                     ┌─────────────────────────────┐
                     │   DUAL-SPEED ROUTING CORE   │
                     └──────────────┬──────────────┘
                                    │
             ┌──────────────────────┴──────────────────────┐
             │                                             │
      [Daily Essentials]                             [Complex Tasks]
             │                                             │
             ▼                                             ▼
  ┌───────────────────────┐                     ┌──────────────────────┐
  │  ⚡ 12ms FAST-PATH   │                     │  🤖 AUTONOMOUS AGENT │
  │ • Instant Phone Calls │                     │ • Multimodal Vision  │
  │ • Direct WhatsApp Msg │                     │ • UI Element Ground  │
  │ • Hardware Controls   │                     │ • In-App Navigation  │
  │ • Battery / Volume    │                     │ • Form Filling       │
  └──────────┬────────────┘                     └──────────┬───────────┘
             │                                             │
             └──────────────────────┬──────────────────────┘
                                    │ Real-Time Spoken Milestones
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │      GNANI.AI TIMBRE v3.0 TEXT-TO-SPEECH (TTS)         │
       │    Continuous Spoken Audio Feedback at Every Step      │
       │  Voices: Lakshmi (Universal) | Shivani | Avinash | Nalini
       │  ("Opening WhatsApp... finding contact... message sent")
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │       REAL-TIME MILLISECOND LATENCY TELEMETRY STRIP    │
       │  [VAD: 1.84s] [STT: 340ms] [Router: 7ms] [Exec: 85ms] │
       │              [TTS: 748ms] [Total: 1180ms]              │
       └────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Innovations & Breakthroughs

### 1. "Vinda" Multi-Lingual Wake-Word Engine & Silent Filtering
- **Two Flexible Trigger Modes**:
  1. **Pure Trigger ("Vinda" / "హే విందా" / "हे विंदा")**: System speaks an immediate localized prompt (*"Yes? How can I help you?"* / *"చెప్పండి, నేను మీకు ఎలా సహాయపడగలను?"* / *"हाँ, मैं आपकी क्या मदद कर सकता हूँ?"*) and opens a **10-second active window** where commands are accepted without repeating the trigger word.
  2. **Trigger + Command ("Vinda turn on flashlight" / "విందా హోమ్")**: Automatically strips the wake word and executes the command immediately without delay.
- **Silent Ambient Noise & Chatter Filtering**: Background speech without the wake word and outside the active window is filtered silently (`[WakeWord] 🤫 Ambient conversation filtered`), preventing accidental triggers.
- **Phonetic Variations Supported**: English & 6 Indic scripts (`vinda`, `winda`, `binda`, `venda`, `vindha`, `windha`, `govinda`, `విందా`, `వింద`, `विंदा`, `விந்தா`, `ವಿಂದಾ`, `ବିନ୍ଦା`).

### 2. Universal Barge-In Emergency Stop Commands
- **Universal Voice Interruption**: Saying `"stop"`, `"cancel"`, `"ఆపు"`, `"ఆపండి"`, `"రోకో"`, `"रुको"`, `"थांबवा"`, `"நிறுத்து"`, `"नಿಲ್ಲಿಸು"`, or `"band karo"` at any point during task execution immediately:
  - Kills any active autonomous Artemis or vision runner via OS process tree termination (`taskkill /F /T /PID`).
  - Sends Android `Back` (keyevent 4) and `Home` (keyevent 3) to clear and reset the phone screen.
  - Speaks a native language cancellation confirmation aloud (*"Task stopped. Returning to home screen."* / *"టాస్క్ ఆపివేయబడింది. హోమ్ స్క్రీన్‌కు తిరిగి వెళ్తున్నాను."*).
- **One-Click Web UI Stop**: Clicking **Stop [Esc]** in the Web UI triggers the exact same instant process abortion.

### 3. Adaptive Listening Breaks & Smart VAD
- **Ambient Noise Floor Calibration**: Dynamically samples the first 200ms of audio to calibrate ambient room noise, automatically setting speech thresholds relative to the room floor.
- **Snappier Listening Breaks**: Trailing silence cutoff reduced from 1.6s to **1.1s**, cutting perceived delay by ~500ms after speaking.
- **False-Trigger Suppression**: Requires $\ge$ 0.35s of sustained speech, preventing microphone pops, keyboard clicks, or breath sounds from burning STT requests.
- **Idle Silence Cycle**: Cycles after 2.8s of idle room silence to keep the microphone responsive without lag.

### 4. Precision Millisecond Latency Telemetry ("Time Each and Everything")
Every stage of the voice execution cycle is measured via high-precision `time.perf_counter()`:
- **`VAD`**: Spoken audio recording duration (in seconds, e.g., `1.84s`).
- **`STT`**: Gnani Prisma v3.0 HTTP roundtrip latency (in ms, e.g., `340ms`).
- **`Router`**: NLP normalization, fuzzy contact matching, and intent classification (in ms, e.g., `7.0ms`).
- **`Exec`**: Target device ADB or autonomous vision agent execution time (in ms, e.g., `85ms` for instant ADB, variable for vision).
- **`TTS`**: Gnani Timbre v3.0 voice synthesis roundtrip (in ms, e.g., `748ms`).
- **`Total`**: Wall-clock end-to-end turnaround time.

**Real-Time Latency Candy Strip**:
Embedded in the Web UI below the spoken transcript box, dynamically updating with live color-coded chips:
$$\boxed{\text{🎙️ VAD: 1.84s}} \quad \boxed{\text{⚡ STT: 340ms}} \quad \boxed{\text{🧠 Router: 7.0ms}} \quad \boxed{\text{📱 Exec: 85ms}} \quad \boxed{\text{🔊 TTS: 748ms}} \quad \boxed{\text{⏱️ Total: 1180ms}}$$

### 5. Multi-Voice Timbre v3.0 Selector & Instant Spoken Acknowledgments
- **Full Timbre v3.0 Voice Suite**:
  - 👩 **`Lakshmi`**: Universal Warm Indian Voice (Default)
  - 👩 **`Shivani`**: Expressive Modern Female Voice
  - 👨 **`Avinash`**: Deep & Confident Male Voice
  - 👩 **`Nalini`**: Soft Female Voice (English)
- **Instant Spoken Feedback**: Clicking any language or voice pill in the Web UI instantly speaks aloud a personalized native-language confirmation (*"భాష తెలుగుగా మార్చబడింది. మీ ఆదేశం కోసం వేచి చూస్తున్నాను."*) through both browser audio and PC speakers.

### 6. 12ms Fast-Path Intent Engine vs. Autonomous Multimodal Vision Agent
- **⚡ 12ms Fast-Path Engine**: High-frequency essential tasks (placing phone calls, sending WhatsApp messages, toggling flashlight, adjusting volume, checking battery level, opening known apps) bypass heavy vision models and execute in **12 milliseconds** via direct Android OS intents and ADB shell commands.
- **🤖 Autonomous Multimodal Vision Agent**: When a user gives an open-ended or multi-step command (e.g., *"Open gallery and select the 1st photo"* or *"Search for Telugu devotional songs on YouTube and play the second video"*), Dhwani activates its multimodal vision agent to inspect the live screen, ground buttons, and autonomously navigate third-party apps.

---

## 🆚 Comparison: Dhwani vs. Google Assistant

| Feature | Google Assistant | Dhwani (ध्वनि) |
| :--- | :--- | :--- |
| **Target Audience** | Tech-literate, urban English/Hindi speakers | **Blind, visually impaired, rural citizens, illiterate individuals, elderly** |
| **Language Understanding** | Rigid keywords; struggles with regional rural phrasing | **Powered by Gnani.ai STT** across 7 Indian languages with deep vernacular dialect support |
| **Indic Grammar (SOV)** | Fails or gets confused on Subject-Object-Verb phrasing | **Native SOV-to-SVO grammar inverter** (*"నాన్న కి కాల్ చేయి"* $\rightarrow$ `call nanna`) |
| **Colloquial Misinterpretations** | Often searches Google when slang or accent is used | **4-Stage Phonetic Normalizer** auto-corrects (`"what's up"` / `"thasup"` $\rightarrow$ WhatsApp, `"touch light"` $\rightarrow$ Flashlight) |
| **Auditory Feedback for the Blind** | Frequently silent; displays visual cards or web links on screen | **Continuous, step-by-step spoken feedback** via **Gnani.ai Timbre TTS** for every action |
| **In-App Task Automation** | Cannot navigate or interact inside third-party apps | **Autonomous Multimodal Vision Agent** navigates apps, taps buttons, and completes workflows |
| **Wake-Word Gating** | Fixed "Hey Google" | **"Vinda" / "విందా" trigger engine** with 10s active window and ambient chatter suppression |
| **Emergency Voice Stop** | Unreliable when tasks or media are active | **Global Voice VAD Interrupt**: saying *"Stop" / "ఆపు" / "रुको"* immediately kills the active task |
| **Execution Latency** | 3 – 6 seconds per turn via multi-hop cloud | **12ms Fast-Path Execution** for direct OS calls, messages, and hardware toggles |
| **Latency Telemetry** | Hidden black box | **Live Millisecond Telemetry Strip** (`VAD`, `STT`, `Router`, `Exec`, `TTS`, `Total`) |

---

## 🌐 Supported Pan-Indian Languages

| Language | Gnani Code | Native Script | Spoken Example | Normalized Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Telugu** | `te-IN` | తెలుగు | *"విందా, నాన్న కి కాల్ చేయి"* / *"వాట్సాప్ తెరువు"* | `call nanna` / `open whatsapp` |
| **Tamil** | `ta-IN` | தமிழ் | *"அப்பாவுக்கு கால் பண்ணு"* / *"யூடியூப் ஓபன்"* | `call appa` / `open youtube` |
| **Kannada** | `kn-IN` | ಕನ್ನಡ | *"ಅಪ್ಪನಿಗೆ ಕಾಲ್ ಮಾಡು"* / *"ಟಾರ್ಚ್ ಆನ್ ಮಾಡು"* | `call appa` / `turn on flashlight` |
| **Hindi** | `hi-IN` | हिन्दी | *"विंदा, पापा को कॉल करो"* / *"व्हाट्सएप खोलो"* | `call papa` / `open whatsapp` |
| **Marathi** | `mr-IN` | मराठी | *"बाबांना कॉल करा"* / *"मेसेज पाठवा"* | `call baba` / `send message` |
| **Odia** | `or-IN` | ଓଡ଼ିଆ | *"ବାପାଙ୍କୁ କଲ୍ କର"* / *"ଖୋଲ ୟୁଟ୍ୟୁବ୍"* | `call bapa` / `open youtube` |
| **Indian English** | `en-IN` | English | *"Vinda, put what's up message to Rahul saying hello"* | `send whatsapp to rahul saying hello` |

---

## 🚀 Getting Started

### Prerequisites
1. **Python 3.10+**
2. **Android Device or Emulator** (Android 10 to 15, Developer Options & USB Debugging enabled).
3. **ADB (Android Debug Bridge)** installed and accessible on PATH.
4. **Gnani.ai API Key**: Sign up at [Gnani.ai](https://gnani.ai) to obtain your STT and TTS API credentials.

### Installation

```bash
# 1. Clone repository
git clone https://github.com/GovindaSaiKiran/Dhwani.git
cd Dhwani

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
# Gnani.ai API Credentials (Required for STT & TTS)
GNANI_API_KEY=your_gnani_api_key_here

# Google Gemini / OpenRouter API Key (For Autonomous Vision Agent Fallback)
GEMINI_API_KEY=your_gemini_api_key_here

# Target Android Device Serial (Run 'adb devices' to find)
TARGET_DEVICE_SERIAL=your_device_serial_here
ADB_HOST=127.0.0.1
ADB_PORT=5037
```

Connect your Android phone via USB and verify ADB detection:
```bash
adb devices
```

---

## 💻 Running the Neo-Humanist Web Console

Launch the interactive web console:

```bash
python web_ui.py
```

Open your browser at **`http://localhost:5000`**.

### Web UI Features:
- **Neo-Humanist Minimalist Canvas**: Figma/Notion aesthetic with tactile candy tokens and Plus Jakarta Sans typography.
- **Interactive Multi-Language & Multi-Voice Selectors**: Switch between 7 Indian languages and 4 Timbre voices with instant spoken audio acknowledgments.
- **Push-to-Talk & Always-On "Vinda" Modes**: Toggle single-shot listening or always-on continuous listening with ambient chatter suppression.
- **Live Latency Candy Strip**: Real-time badges for `VAD`, `STT`, `Router`, `Exec`, `TTS`, and `Total`.
- **Dynamic Device Selector**: Live discovery and switching between connected physical phones and emulators.
- **Saved Contacts Vault**: Search, add, sync, and one-click call or WhatsApp contacts.
- **Interactive Disambiguation Banner**: Visual & spoken confirmation dialogs (`Yes, Proceed` / `No, Cancel`).

---

## 🗣️ Running via Command Line (CLI)

```bash
# Continuous Always-On Listening with "Vinda" Wake-Word in Telugu
python voice_commander.py --continuous --lang te-IN --wake-word vinda

# Continuous Always-On Listening in Hindi with Shivani Voice
python voice_commander.py --continuous --lang hi-IN --voice Shivani

# Single-Shot Voice Command in English
python voice_commander.py --lang en-IN

# Text-Only Direct Command Simulation
python voice_commander.py --text-only "vinda turn on flashlight" -d <SERIAL>

# Stop / Emergency Abort Test
python voice_commander.py --text-only "stop" -d <SERIAL>
```

---

## 📁 Project Architecture

```
Dhwani/
├── voice_commander.py     # Core Pan-Indian Autonomous Voice OS & Trigger Engine
├── gnani_bridge.py        # Gnani.ai Prisma STT & Timbre TTS Voice Pipeline
├── web_ui.py              # Neo-Humanist Minimalist Web Console & Telemetry Hub
├── user_memory.json       # Clean local user memory & VIP contact vault
├── verify_voice_os.py     # End-to-end hardware verification suite
├── requirements.txt       # Python dependencies (flask, sounddevice, requests, etc.)
├── .env.example           # Example environment variables template
├── .gitignore             # Git ignore configuration
└── artemis/               # Autonomous multimodal vision agent framework
    ├── artemis/           # Agent execution graphs, planners, and operators
    ├── config/            # System & LLM router configurations (artemis.jsonc)
    └── mcp_server/        # Model Context Protocol tools & ADB interfaces
```

---

## 🛡️ Privacy, Accessibility & Ethics

- **Zero Reading / Zero Touch**: Dhwani is built for digital inclusion, allowing individuals who cannot read or see to operate a smartphone with dignity.
- **Local Contact Privacy**: Address books and user notes remain stored locally in `user_memory.json` on the device boundary.
- **Auditory Transparency**: Dhwani strictly speaks before executing actions so visually impaired users remain in complete control of their device.

---

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
