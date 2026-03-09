# cycle-close

> *Mental version control for projects,  not just code.*

I built this to solve a specific problem I usually have; I hyperfocus hard, build real things, then wake up the next day with zero re-entry context. The mental state that was holding the project together just evaporates overnight. This tool captures that state before it's gone.

---

## The Problem It Solves

Most productivity tools assume you work consistently, linearly, and remember what you were doing. I don't.  I run parallel workstreams during hyperfocus, context-switch well when one thread is waiting on something (like an AI generation), and then lose everything when the environment changes. Sleep, a conversation, a new project starting,  any of it can wipe the re-entry state completely. This is even more important for people that have ADHD/AuDHD.

Git solves this for code. There's nothing like it for the abstract mental state of a project,  the *why this decision*, *where I was heading*, *what tab was open*, *what nearly derailed it* layer that lives entirely in your head.

`cycle-close` is that tool. You answer 7 questions at the end of a session. It generates a **cold start document**,  a structured re-entry brief written for your future post-sleep self,  using an AI model via OpenRouter. It stores every cycle, lets you append notes over time, tracks patterns in what triggers your best sessions, and keeps all your projects on a single dashboard.

---

## Features

- **Guided cycle close**,  7 questions capturing what got done, exact next action, parallel threads, trigger conditions, and blockers
- **AI-generated cold start docs**,  structured re-entry briefs that get you back inside a project in under 2 minutes, not 20
- **Project dashboard**,  all tracks in one place, with status (active / paused / archived), cycle count, last touched, and next action preview
- **Full cycle history**,  browse, view, append notes, regenerate docs, archive
- **Trigger map**,  session type breakdowns, hyperfocus frequency by project, and optional AI pattern analysis across your last 20 sessions
- **Model flexibility**,  swap between Claude, GPT-4o, Gemini, Llama via OpenRouter from the settings menu
- **Zero dependencies**,  stdlib + `requests` only, pure CLI, color-coded terminal UI with ANSI, no frameworks

---

## Requirements

- Python 3.7+
- `requests` library (`pip install requests`)
- An [OpenRouter](https://openrouter.ai) API key (free tier available)

---

## Installation

### Basic,  run directly

```bash
git clone https://github.com/mohammed-bfaisal/cycle-close
cd cycle-close
python3 cycle-close.py
```

On first run it will ask for your OpenRouter API key and save it to `~/.cycle_close/config.json`. You won't be asked again.

---

### Make it a global command

**Linux / macOS:**

```bash
# Make executable
chmod +x cycle-close.py

# Symlink to somewhere on your PATH
sudo ln -s "$(pwd)/cycle-close.py" /usr/local/bin/cycle-close

# Now run from anywhere
cycle-close
```

Or without sudo, using a user-local bin:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/cycle-close.py" ~/.local/bin/cycle-close

# Add to your shell config if not already there (~/.bashrc, ~/.zshrc, etc.)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Run from anywhere
cycle-close
```

**Windows (PowerShell):**

```powershell
# Add an alias to your PowerShell profile
echo "function cycle-close { python3 C:\path\to\cycle-close.py }" >> $PROFILE
. $PROFILE

cycle-close
```

---

### Set API key via environment variable (optional)

Instead of entering it on first run, you can export it:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENROUTER_API_KEY="your_key_here"
```

The script checks for this env var first, then falls back to the saved config.

---

## Usage

```
cycle-close
```

### Main Menu

```
C   Close a cycle       ,  Lock in before you sleep
P   Projects            ,  All active tracks, status, last touched
B   Browse cycles       ,  Full history, view, append notes, archive
T   Trigger map         ,  Pattern intelligence across your sessions
S   Settings            ,  API key, model, export
Q   Quit
```

### Closing a Cycle (the core flow)

1. **Project**,  select from your existing projects by number, or type a new name
2. **Session type**,  Hyperfocus / Activated / Foggy (single keypress)
3. **What got done**,  specific outputs from this session
4. **Exact next action**,  file path, line number, function, sentence to continue,  be surgical
5. **Parallel threads**,  anything else running alongside (AI generation waiting, side tab, second project)
6. **What triggered this**,  time, mood, what preceded the session
7. **What nearly killed it**,  friction, near-exits, things you pushed through

The tool then calls your configured model via OpenRouter and generates a **cold start document**,  formatted and rendered right in the terminal, ready to copy into Obsidian or wherever you keep notes.

### Appending Notes

From Browse Cycles, press `A` + cycle number to append a timestamped note to any existing cycle. This is how you layer updates onto a project over time,  the original cycle stays intact, notes accumulate below it chronologically.

### Trigger Map

After 5+ cycles the Trigger Map screen shows:
- Session type breakdown (% hyperfocus vs activated vs foggy)
- Hyperfocus frequency ranked by project
- Last 10 trigger descriptions
- Optional AI analysis of what conditions reliably produce your best sessions

### Switching Models

From Settings → `M`. Available models:

| Model | Notes |
|---|---|
| `anthropic/claude-3-haiku` | Default,  fast, cheap, great quality for this use case |
| `anthropic/claude-3.5-sonnet` | Smarter cold start docs, slightly slower |
| `openai/gpt-4o-mini` | Fast OpenAI option |
| `openai/gpt-4o` | Most capable, higher cost |
| `google/gemini-flash-1.5` | Very fast Google option |
| `meta-llama/llama-3.1-8b-instruct` | Open source, free tier on OpenRouter |

---

## Data Storage

All data lives in `~/.cycle_close/`:

```
~/.cycle_close/
├── cycles.json     # all cycle entries + cold start docs + notes
└── config.json     # api key, model preference
```

Export a full JSON backup anytime from Settings → `E`.

The `cycles.json` structure:

```json
{
	"cycles": [
	{
		"id": 1741234567,
		"project": "Syntheco",
		"session_type": "🔥 Hyperfocus",
		"finished": "...",
		"next_action": "...",
		"parallel": "...",
		"trigger": "...",
		"blocker": "...",
		"timestamp": "2026-03-09 21:44",
		"date": "2026-03-09",
		"cold_start": "## RE-ENTRY: Syntheco\n...",
		"notes": [
		{ "text": "...", "ts": "2026-03-10 09:12" }
		],
		"archived": false
	}
	],
	"projects": {
		"Syntheco": {
			"cycles": [1741234567],
			"status": "active",
			"created": "2026-03-09",
			"last_touched": "2026-03-09 21:44"
		}
	}
}
```

---

## Offline Behaviour

If OpenRouter is unreachable (no internet, rate limit, etc.), the tool saves your raw cycle data and returns a clear message. Your answers are never lost. You can regenerate the cold start doc later from Browse Cycles → open cycle → `G`.

---

## Why OpenRouter

OpenRouter gives a single API key access to models from Anthropic, OpenAI, Google, Meta, and others. No juggling multiple API keys or accounts. Free tier is enough to generate cold start docs for months of daily use on Haiku.

Sign up at [openrouter.ai](https://openrouter.ai).

---

## License

MIT

---

*cycle-close · built by Mohammed Bin Faisal · 2026*
