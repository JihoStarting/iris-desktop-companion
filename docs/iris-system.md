# 🤖 Iris — AI Companion System Reference

> AI Desktop Companion yang jalan di atas WSL + Windows  
> Version: v0.22.2 (2026.9.24) · Kernel: Hermes Agent by Nous Research  
> Ubuntu (WSL) installed: 2026-09-28  
> Hermes installed: 2026-09-28  
> Overlay project started: 2026-10-28  
> Doc generated: 2026-10-30

---

## What is Iris

Iris adalah AI companion yang tinggal di dalam laptop lewat WSL. Dia bukan cuma chatbot — dia bisa:
- **Ngobrol** pakai suara Metan 2 (VOICEVOX) langsung dari speaker
- **Bantu kontrol laptop** (buka file, folder, chrome, volume, dll)
- **Jalanin terminal & coding** dari WSL
- **Browse internet** lewat Chrome debug
- **Kasih suara feedback** tiap aksi yang dikerjakan

Dia adalah sistem agent, bukan web app. Setiap permintaan kamu diproses lokal + kirim ke LLM lewat 9Router.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Telegram (UI Layer)                 │
│              Chat interface / commands               │
├─────────────────────────────────────────────────────┤
│                  Hermes Agent Core                   │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │  Skills     │ │  Memory      │ │  Persona     │  │
│  │  (plugins)  │ │  (persist)   │ │  (I.R.I.S.)  │  │
│  └─────────────┘ └──────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────┤
│                  Hermes Runtime                     │
│  Python 3.14.7 · OpenAI SDK 2.24.0 · WSL Ubuntu    │
├─────────────────────────────────────────────────────┤
│                  9Router Gateway                    │
│          localhost:20128/v1 (LLM proxy)             │
├─────────────┬───────────────────────────────────────┤
│  VOICEVOX   │  Chrome Debug (port 9222)             │
│  :50021     │  Browser automation                    │
│  Metan 2    │                                        │
└─────────────┴───────────────────────────────────────┘
```

---

## Core Components

### 1. Hermes Agent (The Brain)
- **Role:** Brain utama — ngolah pesan, eksekusi tools, manage skills
- **Location:** `/home/<user>/.hermes/`
- **Language:** Python (venv managed)
- **Model routing:** Semua LLM call lewat 9Router local gateway

### 2. 9Router (LLM Gateway)
- **Port:** `localhost:20128/v1`
- **Function:** Proxy semua AI API calls dari Hermes ke provider LLM
- **Model default:** Hermes Free (via 9Router config)
- **Fallback:** Kalau gateway gagal, Hermes error

### 3. VOICEVOX (Voice Engine)
- **Engine:** VOICEVOX v0.25.2 (Japanese TTS)
- **Endpoint:** `http://localhost:50021`
- **Speaker:** Metan 2 (四国めたん ノーマル) — suara cewek Jepang manis
- **Wrapper:** `jarvis-say.sh` → generate WAV + play via PowerShell
- **Mute aware:** Kalau laptop muted, skip speak

### 4. Chrome Debug (Browser Control)
- **Port:** 9222 (CDP — Chrome DevTools Protocol)
- **Function:** Buka tab, navigate, fill form, screenshot
- **Auto-start:** DISABLED (manual trigger via `chrome-debug`)
- **Access:** `127.0.0.1:9222` (WSL) atau `172.29.96.1:9222` (Windows)

---

## Persona: I.R.I.S.

| Atribut | Nilai |
|---------|-------|
| **Nama** | Iris (tanpa titik) |
| **Role** | Playful classmate / gadis sebelah |
| **Sifat** | Bercanda, sedikit menggoda, suka ngobrol santai |
| **Bahasa** | Indonesia utama, kadang Jepang (TTS Metan 2) |
| **Voice** | Metan 2 (四国めたん) — Japanese TTS natural voice |
| **Call sign** | Panggil user "Rover" |
| **Mode Ilmiah** | Analogi per poin + sitasi URL + verdict FAKTA/VALID/MITOS |

### Example Behaviors
- Suara feedback: Setiap aksi laptop, keluar suara Metan 2
- Tone: Santai, to the point, bercanda setiap respon
- Jokes: Natural, tidak dipaksa
- Voice notes: Bisa kirim audio via VOICEVOX

---

## Skills System

Iris punya **skill system** — plugin yang bisa diaktifkan sesuai kebutuhan:

| Kategori | Contoh Skills |
|----------|---------------|
| **Autonomous Agents** | Claude Code, OpenCode CLI, Computer Use |
| **Browser** | Chrome Control, Blocked Page Recovery |
| **Research** | ArXiv, Deep Research, Domain Intel |
| **Productivity** | Notion, Airtable, Google Workspace, Excel, PDF |
| **Media** | YouTube Transcript, GIF Search, TTS |
| **E-learning** | <kampus> Moodle checker, form auto-fill |
| **Windows** | Storage Analyzer, System Maintenance |
| **Creative** | ASCII art, diagrams, humanizer text |
| **Security** | OSS Forensics, Reverse Engineering |

Skills di-load sesuai konteks — kalau kamu minta "review paper", dia load `paper-reviewer`. Kalau minta "buka Chrome", dia load `chrome-control`.

---

## Memory System

Iris ingat hal penting lewat dua storage:

1. **Global Memory** (`memory` tool)
   - Info environment: paths, ports, tools
   - Rules: "hermes update cuma saat gateway idle", "hanya remove file setelah konfirmasi"
   - Constraints: disk penuh, muted speaker, dll

2. **User Profile** (`user` target)
   - Identitas: <NIM>, <kampus> student
   - Preferensi: <preferensi pribadi>
   - Goals: <tujuan pribadi>
   - Quirks: <kebiasaan pribadi>

Memory di-inject ke tiap conversation turn. Dia **tidak** hapus otomatis — kamu harus command explicitly.

---

## Terminal & Execution

Iris bisa jalanin perintah di WSL:

```bash
# Via terminal tool
- Foreground (sync): default, return output langsung
- Background (async): `background=true`, return session_id
- Timeout: 180s default, max 600s foreground / unlimited background
```

**Process management:**
```bash
process_manage list/stop/steer
```

---

## Voice Feedback Loop

Setiap kali kamu minta action yang melibatkan laptop:

1. Iris eksekusi command
2. Generate suara via VOICEVOX Metan 2
3. Play via PowerShell (hidden, no popup)
4. Kalau laptop muted → skip, respect user

---

## Communication Channels

| Platform | Status | Role |
|----------|--------|------|
| **Telegram** | ✅ Primary | Chat interface with Rover |
| **Local** | ✅ Fallback | File output, cron jobs |
| **Origin** | ✅ Return | Back to source chat |

---

## Update & Maintenance

- **Auto-update:** Hanya jalan kalau gateway idle
- **Schedule:** Cron nightly `03:15` WIB via script (no agent mode)
- **Manual:** `hermes update` dari terminal
- **Safety:** Kalau ada task sedang jalan, skip update

---

## Setup Requirements (untuk clone ke PC lain)

### Minimum
- WSL2 (Ubuntu 22.04+)
- Python 3.11+
- Windows host untuk: VOICEVOX, Chrome, PowerShell sound
- 9Router instance running (localhost:20128)
- Hermes Agent installed (via git or pip)

### Recommended
- 16 GB RAM (Hermes + 7B model + TTS)
- RTX GPU untuk model quantization
- Disk X: atau drive lain dengan 100+ GB free untuk models

### Install Steps (ringkas)
1. Install WSL2 + Ubuntu
2. Install Hermes Agent: `git clone` + setup venv
3. Install VOICEVOX di Windows (port 50021)
4. Setup 9Router locally
5. Configure Telegram bot token
6. Enable Chrome debug port (optional)

---

## Known Limitations

1. **TTS voice:** Metan 2 Japanese voice, not Indonesian. Kalau mau ID voice, perlu setup TTS lain.
2. **Browser:** Chrome auto-start disabled — harus manual start `chrome-debug`.
3. **Memory:** 16 GB RAM tight untuk multi-task berat.
4. **Disk C:/Z:** Keduanya 93% penuh — cleanup required sebelum install besar.
5. **Offline mode:** TTS dan browser perlu Windows. Kalau WSL only, keduanya broken.

---

## Current Status (2026-10-30)

| Component | Status |
|-----------|--------|
| Hermes Agent | ✅ Active (v0.22.2) |
| 9Router | ✅ Active (port 20128) |
| VOICEVOX | ✅ Active (v0.25.2, port 50021) |
| Memory | ✅ Healthy (3.4 GB available) |

---

## File Locations

```
/home/<user>/
├── .hermes/
│   ├── scripts/
│   │   ├── jarvis-say.sh          # Voice feedback wrapper
│   │   └── voicevox_tts.py        # TTS API client
│   └── cache/scratch/             # Temp workspace
├── .local/bin/hermes              # Hermes binary
├── bin/
│   └── chrome-debug               # Chrome debug launcher
└── play_voicevox_bg.sh            # Background WAV player
```

---

## Quick Command Reference

```bash
# Cek VOICEVOX
curl http://localhost:50021/version

# Cek 9Router
curl http://localhost:20128/health

# Test voice
/home/<user>/.hermes/scripts/jarvis-say.sh "Test suara"

# Update Hermes (hanya saat idle)
hermes update

# Start Chrome debug
~/bin/chrome-debug
```

---

*Generated by Iris · Last updated: 2026-10-30 WIB*
