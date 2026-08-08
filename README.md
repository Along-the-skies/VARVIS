# ⚡ VARVIS

> **A personal AI assistant built to control, understand, and interact with your computer.**

<div align="center">

**V**irtual **A**ssistant for **R**esponsive **V**oice & **I**ntelligent **S**ystems

<br>

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Active-00C853?style=for-the-badge)](#)
[![Version](https://img.shields.io/badge/Version-1.0.0-8A2BE2?style=for-the-badge)](#)

</div>

---

## 🧠 What is VARVIS?

**VARVIS** is a personal AI assistant designed to interact with your computer through natural commands.

It combines:

* 🧠 AI-powered command understanding
* 🖥️ Computer control
* 🎙️ Voice interaction
* 📦 Application management
* ⚙️ System controls
* 🌐 Browser actions
* 💬 AI conversations
* 🧩 A modular architecture

The goal isn't just to make another chatbot.

**VARVIS is built to actually do things.**

---

## ✨ Features

### 🧠 Intelligent Command System

VARVIS can interpret commands and route them to the appropriate system module.

```text
"Open Discord"
      ↓
Command Understanding
      ↓
Command Router
      ↓
Application Module
      ↓
Discord launches
```

### 🖥️ Application Control

Open and close applications directly through VARVIS.

```text
> Open Discord
VARVIS → Opening Discord...

> Close Discord
VARVIS → Closing Discord...
```

### ⚙️ System Control

Interact with system information and controls through dedicated modules.

### 🌐 Browser Control

Browser-related functionality is separated into its own module, keeping the core system clean and expandable.

### 🎙️ Voice Interaction

VARVIS is designed to support both:

```text
⌨️ Text Commands
🎙️ Voice Commands
```

### 🤖 AI Layer

Natural-language requests can be converted into the normalized command format understood by the existing command router.

This allows the AI layer to **understand** commands without replacing the core architecture.

---

# 🏗️ Architecture

VARVIS follows a modular structure so new capabilities can be added without turning the project into one giant file.

```text
VARVIS/
│
├── assets/
│   └── wake.wav
│
├── core/
│   ├── brain.py
│   ├── config.py
│   ├── gui.py
│   ├── logger.py
│   ├── memmory.py
│   └── voice.py
│
├── database/
│   ├── apps.json
│   └── jarvis.db
│
├── logs/
│
├── models/
│   └── model.py
│
├── modules/
│   ├── apps.py
│   ├── browser.py
│   ├── settings.py
│   ├── system.py
│   └── tools.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md
```

### 🔌 Modular Design

```text
                 ┌──────────────┐
                 │    VARVIS    │
                 └──────┬───────┘
                        │
                 ┌──────▼──────┐
                 │    Brain    │
                 └──────┬──────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
   ┌───▼───┐        ┌───▼───┐       ┌───▼────┐
   │ Apps  │        │System │       │Browser │
   └───────┘        └───────┘       └────────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                 ┌──────▼──────┐
                 │   Computer  │
                 └─────────────┘
```

---

# 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd VARVIS
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

**Windows:**

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

### 6. Run VARVIS

```bash
python main.py
```

---

# 🧪 Development

VARVIS is actively being developed.

The project is intentionally built in stages:

```text
Core
 ↓
Modules
 ↓
Command Router
 ↓
AI Understanding
 ↓
Voice
 ↓
GUI
 ↓
More Intelligence
```

The architecture is designed so each part can evolve independently.

---

# 🛠️ Tech Stack

| Technology            | Purpose                    |
| --------------------- | -------------------------- |
| 🐍 Python             | Core application           |
| 🧠 OpenRouter         | AI understanding           |
| 🎙️ SpeechRecognition | Voice input                |
| 🔊 pyttsx3            | Text-to-speech             |
| ⚡ PySide6             | GUI                        |
| 📦 JSON / SQLite      | Data & application storage |
| 🪟 Windows APIs       | System interaction         |

---

# 👥 Contributors

<table>
<tr>

<td align="center">

### 👨‍💻 Developer

**Vasudev**

Architecture, backend, core logic, integrations & development.

</td>

<td align="center">

### 🎨 Frontend

**Claude**

GUI design & frontend implementation.

</td>

<td align="center">

### 🎨 Asset Designer

**Kurama**

`imkurama`

Visual assets, branding & design resources.

</td>

</tr>
</table>

---

# 📜 Project Philosophy

> **Build the brain before making it beautiful.**

VARVIS is being developed around a simple idea:

**Keep the core understandable. Keep the modules replaceable. Keep the assistant expandable.**

No massive monolithic script.

No unnecessary coupling.

Just a system that can grow.

---

# 🔮 Roadmap

* [x] Project architecture
* [x] Application detection
* [x] Application opening
* [x] Application closing
* [x] Rule-based command routing
* [x] AI command understanding
* [x] PySide6 interface
* [x] Voice output
* [ ] Improved voice recognition
* [ ] Persistent memory
* [ ] More system controls
* [ ] More browser automation
* [ ] Better AI reasoning
* [ ] Plugin system
* [ ] Advanced automation

---

<div align="center">

## ⚡ VARVIS

**Not just an assistant.
A system that grows with you.**

<br>

`Made with Python • Built from scratch • Constantly evolving`

<br>

### 👨‍💻 Vasudev · 🎨 Claude · 🎨 Kurama

</div>
