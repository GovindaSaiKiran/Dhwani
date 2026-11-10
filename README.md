# 🎙️ Dhwani (ध्वनि / ధ్వని / ಧ್ವನಿ / த்வனி / ध्वनि / ଧ୍ୱନି)
### Autonomous Pan-Indian Voice Operating System for Android
**100% Hands-Free & Eyes-Free Smartphone Control for the Blind, Rural Citizens, Elderly, and Vernacular Speakers**

[![Gnani.ai Voice](https://img.shields.io/badge/Powered%20By-Gnani.ai%20STT%20%26%20TTS%20APIs-orange.svg?style=for-the-badge&logo=sound)](https://gnani.ai)
[![Gnani Hackathon](https://img.shields.io/badge/Built%20For-Gnani.ai%20Hackathon%202026-blueviolet.svg?style=for-the-badge)](https://gnani.ai)
[![Accessibility](https://img.shields.io/badge/Accessibility-Blind%20%26%20Elderly%20First-green.svg?style=for-the-badge)](https://developer.android.com)
[![Fast Path](https://img.shields.io/badge/Fast--Path-12ms%20Instant%20Execution-brightgreen.svg?style=for-the-badge)]()
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](LICENSE)

---

## 🏆 Built for the Gnani.ai Hackathon

> [!IMPORTANT]
> **Dhwani** was conceptualized and built for the **Gnani.ai Hackathon**. 
> The core technological backbone of this project is powered by **Gnani.ai's Conversational AI Platform**, utilizing **Gnani's Speech-to-Text (STT) and Text-to-Speech (TTS) APIs** to break the literacy and language barrier for over 500 million underserved Indian citizens.

---

## 🇮🇳 The Problem: The Digital Divide in India

Over **500 million people in India**—including the **visually impaired, illiterate individuals, rural citizens, and elderly elders**—own or have access to a smartphone but cannot effectively use it. 

### Why Current Solutions Fail:
1. **Dense, Visual-Only User Interfaces**: Modern mobile operating systems (Android, iOS) require reading text, recognizing icons, dismissing system popups, and navigating complex nested menus. For a blind or illiterate person, a touchscreen is a flat piece of glass with no feedback.
2. **English-Centric Voice Assistants**: Mainstream assistants (Siri, Alexa, Google Assistant) are architected for English and formal grammar. They fail on rural dialects, colloquial pronunciations, and Subject-Object-Verb (SOV) Indic sentence structures.
3. **No Continuous Auditory Feedback**: When Google Assistant performs an action, it often renders a silent card or web link on the screen. A blind user cannot see whether their message was sent or what failed.
4. **App Inactivity**: Traditional assistants can only launch an app or search Google. They cannot autonomously navigate inside third-party apps to click buttons, fill forms, or complete real-world tasks.

---

## 💡 What is Dhwani?

**Dhwani** (*Sanskrit & Indic for "Sound / Voice"*) is an **Autonomous Voice Operating System for Android** that transforms any Android smartphone into a **100% voice-driven, eyes-free companion**.

With Dhwani, users **never have to look at the screen or touch the phone**. They speak naturally in their mother tongue—**Telugu, Tamil, Kannada, Hindi, Marathi, Odia, or Indian English**—and Dhwani autonomously operates the device, executing tasks and speaking aloud every action at each step.

```
                     🗣️ Natural Vernacular Voice
                 ("నాన్న కి వాట్సాప్ మెసేజ్ పెట్టు...")
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
       │   • Translates Indic verbs (తెరువు/खोलो ➔ open)       │
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
                                    │ Real-Time Milestones
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │      GNANI.AI TIMBRE v3.0 TEXT-TO-SPEECH (TTS)         │
       │    Continuous Spoken Audio Feedback at Every Step      │
       │   ("Opening WhatsApp... finding contact... message sent")
       └────────────────────────────────────────────────────────┘
```

---

## 🆚 Why Dhwani vs. Google Assistant?

| Feature | Google Assistant | Dhwani (ध्वनि) |
| :--- | :--- | :--- |
| **Target Audience** | Tech-literate, urban English/Hindi speakers | **Blind, visually impaired, rural citizens, illiterate individuals, elderly** |
| **Language Understanding** | Rigid keywords; struggles with regional rural phrasing | **Powered by Gnani.ai STT** across 7 Indian languages with deep vernacular dialect support |
| **Indic Grammar (SOV)** | Fails or gets confused on Subject-Object-Verb phrasing | **Native SOV-to-SVO grammar inverter** (*"నాన్న కి కాల్ చేయి"* $\rightarrow$ `call nanna`) |
| **Colloquial Misinterpretations** | Often searches Google when slang or accent is used | **4-Stage Phonetic Normalizer** auto-corrects (`"what's up"` / `"thasup"` $\rightarrow$ WhatsApp, `"touch light"` $\rightarrow$ Flashlight) |
| **Auditory Feedback for the Blind** | Frequently silent; displays visual cards or web links on screen | **Continuous, step-by-step spoken feedback** via **Gnani.ai Timbre TTS** for every action |
| **In-App Task Automation** | Cannot navigate or interact inside third-party apps | **Autonomous Multimodal Vision Agent** navigates apps, taps buttons, and completes workflows |
| **Missing Contact Recovery** | Says *"Contact not found"* and stops | **Phonetic Nearest-Match Confirmation** (e.g., *Rakesh* not found $\rightarrow$ asks *"Did you mean Rahul?"*) |
| **Missing App Recovery** | Tells the user to install the app and terminates | **Cross-App Category Fallback** (e.g., *Blinkit* missing $\rightarrow$ *"Blinkit not installed, opening Zepto instead"*) |
| **Execution Latency** | 3 – 6 seconds per turn via multi-hop cloud | **12ms Fast-Path Execution** for direct OS calls, messages, and hardware toggles |
| **Emergency Voice Stop** | Unreliable when tasks or media are active | **Global Voice VAD Interrupt**: saying *"Stop" / "ఆపు" / "रुको"* immediately kills the active task |

---

## 🎙️ Powered by Gnani.ai Voice APIs

Dhwani leverages the full power of **Gnani.ai's Conversational AI Suite**:

### 1. Gnani.ai Prisma Speech-to-Text (STT)
- **High-Accuracy Vernacular Recognition**: Accurately transcribes spoken Indian languages even with thick regional accents, colloquial phrasing, and background acoustic noise.
- **Dynamic Voice Activity Detection (VAD)**: Real-time RMS audio chunking detects when speech starts and stops with zero hardcoded timers, cutting off silence dynamically (0.8s) for sub-second response times.

### 2. Gnani.ai Timbre Text-to-Speech (TTS)
- **Human-Grade Vernacular Voices**: Generates natural, warm, and highly intelligible Indian speech using the `Lakshmi` voice model.
- **Accessibility Audio Milestones**: Every milestone in an execution sequence (e.g. launching dialer, opening chat, toggling flashlight, error recovery) is immediately synthesized into speech, ensuring blind users never experience silence or uncertainty.

### 🌐 Supported Indian Languages

| Language | Gnani Code | Native Script | Spoken Example | Normalized Intent |
| :--- | :--- | :--- | :--- | :--- |
| **Telugu** | `te-IN` | తెలుగు | *"నాన్న కి కాల్ చేయి"* / *"వాట్సాప్ తెరువు"* | `call nanna` / `open whatsapp` |
| **Tamil** | `ta-IN` | தமிழ் | *"அப்பாவுக்கு கால் பண்ணு"* / *"யூடியூப் ஓபன்"* | `call appa` / `open youtube` |
| **Kannada** | `kn-IN` | ಕನ್ನಡ | *"ಅಪ್ಪನಿಗೆ ಕಾಲ್ ಮಾಡು"* / *"ಟಾರ್ಚ್ ఆನ್ ಮಾಡು"* | `call appa` / `turn on flashlight` |
| **Hindi** | `hi-IN` | हिन्दी | *"पापा को कॉल करो"* / *"व्हाट्सएप खोलो"* | `call papa` / `open whatsapp` |
| **Marathi** | `mr-IN` | मराठी | *"बाबांना कॉल करा"* / *"मेसेज पाठवा"* | `call baba` / `send message` |
| **Odia** | `or-IN` | ଓଡ଼ିଆ | *"ବାପାଙ୍କୁ କଲ୍ କର"* / *"ଖୋଲ ୟୁଟ୍ୟୁବ୍"* | `call bapa` / `open youtube` |
| **Indian English** | `en-IN` | English | *"Put what's up message to Rahul saying hello"* | `send whatsapp to rahul saying hello` |

---

## ⚡ Core Innovations & Features

### 1. 12ms Fast-Path Intent Engine vs. Autonomous Vision Agent
Dhwani employs an intelligent **dual-speed execution architecture**:
- **⚡ 12ms Fast-Path Engine**: High-frequency essential tasks (placing phone calls, sending WhatsApp messages, toggling the flashlight, adjusting volume, checking battery level, opening known apps) bypass heavy vision models and execute in **12 milliseconds** via direct Android OS intents and ADB shell commands.
- **🤖 Autonomous Vision Agent Fallback**: When a user gives an open-ended or complex multi-step command (e.g., *"Open gallery and send the first photo to Rahul"* or *"Search for Telugu devotional songs on YouTube and play the second video"*), Dhwani activates its multimodal vision agent to inspect the live screen, ground buttons, and autonomously navigate third-party apps.

### 2. 4-Stage Pan-Indian Phonetic & Grammar Normalizer
Rural and vernacular users often speak with colloquialisms, English transliterations, or grammatical structures that crash standard parsers:
- **Stage A (Native Script & Indic Verb Mapping)**: Maps native scripts and transliterated Hinglish/Tanglish/Teluglish verbs (`తెరువు`, `खोलो`, `thira`, `kholo`, `open pannu`) to canonical operational intents (`open`, `call`, `send message`, `turn on`, `turn off`).
- **Stage B (Phonetic App & Hardware Corrections)**: Fixes common speech recognition distortions:
  - `"what's up"`, `"whats up"`, `"thasup"`, `"vatsap"`, `"వాట్సాప్"` $\rightarrow$ `whatsapp`
  - `"touch light"`, `"torch light"`, `"put torch"`, `"flaslight"` $\rightarrow$ `turn on flashlight`
  - `"put message"`, `"keep message"`, `"drop message"` $\rightarrow$ `send message`
- **Stage C (SOV-to-SVO Grammar Inversion)**: Indian languages follow Subject-Object-Verb order (*"Rahul ki call cheyi"*). The normalizer inverts this into standard SVO (*"call rahul"*).
- **Stage D (Universal App Catalog)**: Built-in mappings for 50+ popular Indian applications (WhatsApp, PhonePe, Google Pay, Paytm, Swiggy, Zomato, Blinkit, Zepto, IRCTC, Rapido, JioCinema, YouTube, etc.).

### 3. Voice-Driven Disambiguation & Cross-App Fallback
Blind and elderly users cannot fix errors by tapping. Dhwani handles failures autonomously through voice:
- **Nearest-Match Contact Disambiguation**: If the spoken contact (e.g., *"Rakesh"*) does not exist in memory or the phone's address book, Dhwani calculates the closest phonetic match (*"Rahul"*) and speaks aloud:
  > *"Contact Rakesh was not found. The closest match is Rahul. Should I call Rahul instead?"*
  The user simply replies *"Yes"* (*"అవును"* / *"हाँ"* / *"ஆமா"*) or *"No"*, and Dhwani proceeds accordingly.
- **Cross-App Category Fallback**: If a user asks to open an app that is not installed (e.g., *"Open Blinkit"*), Dhwani scans the phone for installed alternatives in the same category (e.g., Zepto, Swiggy Instamart) and automatically opens the alternative while explaining what it did.

### 4. Universal Android Hardware & System Automation
Engineered to work seamlessly across physical Android smartphones (Android 10 – 15+):
- **Hardware Flashlight Automation**: Universal torch control via native Android system commands and Quick Settings automation.
- **Live Contact Synchronization**: Reads contacts directly from Android's native content provider via ADB (`content://com.android.contacts/data/phones`).
- **Real-Time System Telemetry**: Spoken battery percentage, charging state, volume adjustments, and system status queries via voice.

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

Create a `.env` file in the root directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

Add your credentials to `.env`:
```env
# Gnani.ai API Credentials (Required for STT & TTS)
GNANI_API_KEY=your_gnani_api_key_here

# OpenRouter / Gemini API Key (For Autonomous Vision Agent Fallback)
OPENROUTER_API_KEY=your_openrouter_api_key_here

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

## 🗣️ Operating Dhwani (Voice Controlled)

Launch Dhwani's live voice pipeline with your preferred Indian language:

```bash
# Live Voice Mode in Telugu (తెలుగు)
python voice_commander.py --lang te-IN

# Live Voice Mode in Tamil (தமிழ்)
python voice_commander.py --lang ta-IN

# Live Voice Mode in Hindi (हिन्दी)
python voice_commander.py --lang hi-IN

# Live Voice Mode in Kannada (ಕನ್ನಡ)
python voice_commander.py --lang kn-IN

# Live Voice Mode in Marathi (मराठी)
python voice_commander.py --lang mr-IN

# Live Voice Mode in Odia (ଓଡ଼ିଆ)
python voice_commander.py --lang or-IN

# Live Voice Mode in Indian English (Default)
python voice_commander.py --lang en-IN
```

### Spoken Voice Examples:
- **Placing Phone Calls**: *"నాన్న కి కాల్ చేయి"* / *"Call Rahul"* / *"पापा को फोन लगाओ"*
- **WhatsApp Messaging**: *"Send WhatsApp to Rahul saying I will be late"* / *"వాట్సాప్ లో అమ్మ కి మెసేజ్ చేయి"*
- **Hardware Flashlight**: *"Torch on cheyi"* / *"Turn on flashlight"* / *"टॉर्च जलाओ"*
- **Checking Battery**: *"Battery percentage entha?"* / *"What is my battery level?"*
- **Adjusting Volume**: *"Volume penchu"* / *"Increase volume to 80%"*
- **Launching Apps**: *"Open YouTube"* / *"యూట్యూబ్ తెరువు"* / *"Zepto kholo"*
- **Searching Media**: *"Search Telugu devotional songs on YouTube"*
- **Emergency Task Abort**: Spoken *"Stop"* / *"ఆపు"* / *"रुको"* immediately terminates any ongoing task and returns to the phone home screen.

---

## 📁 Project Architecture

```
Dhwani/
├── voice_commander.py     # Core Pan-Indian Autonomous Voice OS Orchestrator
├── gnani_bridge.py        # Gnani.ai Prisma STT & Timbre TTS Voice Pipeline
├── user_memory.json       # Clean local user memory & VIP contact vault
├── verify_voice_os.py     # End-to-end hardware verification suite
├── requirements.txt       # Python dependencies (sounddevice, requests, etc.)
├── .env.example           # Example environment variables template
├── .gitignore             # Git ignore configuration
└── artemis/               # Autonomous multimodal vision agent framework
    ├── artemis/           # Agent execution graphs, planners, and operators
    ├── config/            # System & LLM router configurations
    └── mcp_server/        # Model Context Protocol tools & ADB interfaces
```

---

## 🛡️ Privacy, Security & Ethics

- **Zero Reading / Zero Touch**: Dhwani is built for digital inclusion, allowing individuals who cannot read or see to operate a smartphone with dignity.
- **Local Contact Privacy**: Address books and user notes remain stored locally in `user_memory.json` on the device boundary.
- **Auditory Transparency**: Dhwani strictly speaks before executing actions so visually impaired users remain in complete control of their device.

---

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
