# WhisperTyping (VoiceTyper Pro fork)

**English version** | [Русская версия](./README.ru.md)

**WhisperTyping** is my personal fork of **VoiceTyper Pro**.

A minimalist GUI app for real-time speech-to-text via the **Groq API** that **types wherever your cursor is**. For Windows, a portable `.exe` is available - just double-click to run.

> From the author of the fork: this is important to me because of problems with spasticity in my hands -  typing for long periods of time is difficult for me. The goal is to speed up interaction with the PC and make voice input truly convenient.

---

## Why this fork

* Portable **Windows `.exe`** - runs with no installation and no external deps
* Backend switch: **Deepgram → Groq API**
* Ongoing small improvements for daily use

---

## Who it helps

* people with motor impairments (incl. spasticity) or fatigue from typing;
* anyone experiencing discomfort from repetitive motions;
* everyone who prefers a **voice-first** workflow with predictable flow.

What helps:

* a single global `Insert` key to start/stop recording;
* auto-typing of recognized text at the current cursor position;
* portable Windows `.exe`;
* a lightweight, unobtrusive UI.

---

## Quick Start (Windows `.exe`)

1. Download **`WhisperTyping.exe`** from **Releases**.
2. Launch it and enter your **Groq API key** on first run.
3. Press **`Insert`** to start and stop recording.
4. The transcript appears in the window and **is typed wherever your cursor is**.

> macOS/Linux: use **from source** installation (a `.dmg`/AppImage is in development).

---

## Features

* Real-time speech recognition (**Groq API**)
* **Automatic text insertion** at the cursor position
* **`Insert` hotkey** (toggle start/stop)
* **Session logging** to `transcribe.log`
* Simple, friendly UI
* Accessibility-first priorities

---

## Requirements

* **Python 3.7+** (only for building/running from source)
* **Groq API key** (get one at: [https://groq.com/](https://groq.com/))
* OS: **Windows**, **macOS**, or **Linux**

---

## Install (from source)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python main.py
```

3. Provide your **Groq API key** in the app — and you’re set.

---

## Usage

* Click **Start Recording** or press **`Insert`** to begin.
* Click again or press **`Insert`** to stop.
* The transcript is visible in the window and **typed at the cursor**.
* All sessions are logged in **`transcribe.log`**.

---

## Support & Credits

If this fork helps you, please ⭐ the repo.

**Credits:** built on **VoiceTyper Pro**. Support the original author:

* Ko-fi: [https://ko-fi.com/perrypixel](https://ko-fi.com/perrypixel)
* UPI: `kevinp@apl`
