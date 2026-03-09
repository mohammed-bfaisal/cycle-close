#!/usr/bin/env python3
"""
╔═══════════════════════════════════════╗
║         CYCLE CLOSE  v1.0             ║
║   Mental version control for mbf      ║
╚═══════════════════════════════════════╝

Stores cycles in ~/.cycle_close/
Uses OpenRouter API for cold-start doc generation.
Set OPENROUTER_API_KEY env var (or enter on first run).
"""

import os, sys, json, textwrap, datetime, time, re
from pathlib import Path
import requests

# ─── ANSI PALETTE ────────────────────────────────────────────────────────────
R  = "\033[0m"          # reset
B  = "\033[1m"          # bold
DIM= "\033[2m"          # dim
IT = "\033[3m"          # italic
UL = "\033[4m"          # underline

# Foreground
ORANGE  = "\033[38;5;208m"
RED     = "\033[38;5;196m"
GREEN   = "\033[38;5;82m"
YELLOW  = "\033[38;5;220m"
CYAN    = "\033[38;5;87m"
BLUE    = "\033[38;5;75m"
PURPLE  = "\033[38;5;141m"
GREY    = "\033[38;5;244m"
DKGREY  = "\033[38;5;236m"
WHITE   = "\033[38;5;255m"
CREAM   = "\033[38;5;230m"

# Background
BG_DARK  = "\033[48;5;232m"
BG_SEL   = "\033[48;5;235m"
BG_ORNG  = "\033[48;5;208m"

# ─── PATHS ───────────────────────────────────────────────────────────────────
BASE_DIR   = Path.home() / ".cycle_close"
DATA_FILE  = BASE_DIR / "cycles.json"
CONFIG_FILE= BASE_DIR / "config.json"
BASE_DIR.mkdir(exist_ok=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def clear():
    os.system("clear")

def w(n=1):
    print("\n" * (n-1))

def divider(char="─", color=DKGREY, width=None):
    width = width or get_width()
    print(f"{color}{char * width}{R}")

def get_width():
    try:
        return min(os.get_terminal_size().columns, 100)
    except:
        return 80

def wrap(text, indent=0, width=None):
    width = (width or get_width()) - indent
    lines = textwrap.wrap(text, width)
    pad = " " * indent
    return ("\n" + pad).join(lines)

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except:
            return {"cycles": [], "projects": {}}
    return {"cycles": [], "projects": {}}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            return {}
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def date_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def spinner(msg="Generating"):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i, f in enumerate(frames * 3):
        print(f"\r{ORANGE}{f}{R} {GREY}{msg}...{R}", end="", flush=True)
        time.sleep(0.08)

# ─── HEADER ──────────────────────────────────────────────────────────────────
def print_header(subtitle=""):
    clear()
    w_  = get_width()
    print(f"{ORANGE}{B}{'━' * w_}{R}")
    title = "  CYCLE CLOSE"
    version = "v1.0  "
    gap = w_ - len(title) - len(version)
    print(f"{ORANGE}{B}{title}{R}{' ' * gap}{GREY}{version}{R}")
    if subtitle:
        print(f"  {GREY}{IT}{subtitle}{R}")
    print(f"{ORANGE}{DIM}{'━' * w_}{R}")
    print()

# ─── INPUT HELPERS ───────────────────────────────────────────────────────────
def prompt(label, hint="", allow_empty=False, default=""):
    if hint:
        print(f"  {GREY}{IT}{wrap(hint, 2)}{R}")
    dflt_str = f"{DKGREY} [{default}]{R}" if default else ""
    while True:
        try:
            val = input(f"  {CYAN}{B}› {R}{CREAM}{label}{dflt_str}{CREAM}: {R}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return default or ""
        if val == "" and default:
            return default
        if val or allow_empty:
            return val
        print(f"  {RED}Required — please enter something.{R}")

def prompt_multiline(label, hint=""):
    if hint:
        print(f"  {GREY}{IT}{wrap(hint, 2)}{R}")
    print(f"  {CYAN}{B}› {R}{CREAM}{label}{R}")
    print(f"  {DKGREY}(type lines, enter blank line when done){R}")
    lines = []
    while True:
        try:
            line = input(f"  {DKGREY}  │ {CREAM}")
        except (KeyboardInterrupt, EOFError):
            break
        if line == "" and lines:
            break
        if line:
            lines.append(line)
    return "\n".join(lines)

def choose(label, options, colors=None, default=None):
    """Numbered menu choice. Returns (index, value)."""
    colors = colors or [GREEN, YELLOW, ORANGE, BLUE, PURPLE, CYAN, RED]
    print(f"  {CREAM}{B}{label}{R}")
    print()
    for i, opt in enumerate(options):
        col = colors[i % len(colors)]
        num = f"{col}{B} {i+1} {R}"
        dflt_mark = f" {DKGREY}← default{R}" if default is not None and i == default else ""
        print(f"  {num} {col}{opt}{R}{dflt_mark}")
    print()
    while True:
        try:
            raw = input(f"  {CYAN}{B}› {R}{CREAM}Select [1-{len(options)}]: {R}").strip()
        except (KeyboardInterrupt, EOFError):
            return (default, options[default]) if default is not None else (0, options[0])
        if raw == "" and default is not None:
            return (default, options[default])
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return (idx, options[idx])
        except:
            pass
        print(f"  {RED}Enter a number between 1 and {len(options)}.{R}")

def confirm(msg, default=True):
    yn = "Y/n" if default else "y/N"
    try:
        raw = input(f"  {YELLOW}? {msg} [{yn}]: {R}").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return default
    if raw == "":
        return default
    return raw in ("y", "yes")

# ─── OPENROUTER ──────────────────────────────────────────────────────────────
def get_api_key():
    cfg = load_config()
    key = cfg.get("openrouter_api_key") or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print(f"\n  {YELLOW}No OpenRouter API key found.{R}")
        print(f"  {GREY}Get one at https://openrouter.ai — paste it below.{R}\n")
        key = prompt("OpenRouter API Key", allow_empty=False)
        cfg["openrouter_api_key"] = key
        save_config(cfg)
        print(f"  {GREEN}✓ Saved to config.{R}\n")
    return key

def get_model():
    cfg = load_config()
    return cfg.get("model", "anthropic/claude-3-haiku")

def set_model_interactive():
    models = [
        ("anthropic/claude-3-haiku",       "Claude 3 Haiku      — fast, cheap, great for this"),
        ("anthropic/claude-3.5-sonnet",     "Claude 3.5 Sonnet   — smarter, slightly slower"),
        ("openai/gpt-4o-mini",              "GPT-4o Mini         — fast OpenAI option"),
        ("openai/gpt-4o",                   "GPT-4o              — powerful OpenAI"),
        ("google/gemini-flash-1.5",         "Gemini Flash 1.5    — Google, very fast"),
        ("meta-llama/llama-3.1-8b-instruct","Llama 3.1 8B        — open source, free tier"),
    ]
    print()
    cfg = load_config()
    current = cfg.get("model", "anthropic/claude-3-haiku")
    print(f"  {GREY}Current model: {ORANGE}{current}{R}\n")
    idx, _ = choose("Select model", [f"{m[0]}  {GREY}{m[1]}{R}" for m in models])
    chosen = models[idx][0]
    cfg["model"] = chosen
    save_config(cfg)
    print(f"\n  {GREEN}✓ Model set to {ORANGE}{chosen}{R}")

def call_openrouter(system_prompt, user_prompt):
    key   = get_api_key()
    model = get_model()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cycle-close.local",
        "X-Title": "Cycle Close",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 1200,
        "temperature": 0.7,
    }
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=body, timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return "[OFFLINE] No internet connection — cold start doc could not be generated. Your raw cycle data was saved."
    except Exception as e:
        return f"[ERROR] {e}"

# ─── COLD START DOC GENERATION ───────────────────────────────────────────────
SYSTEM_PROMPT = """You are writing "cold start documents" for an AuDHD builder/researcher.
These documents are read after sleep or context switches — when all mental state holding a project together has evaporated.
The goal: get the person back INSIDE the project in under 2 minutes.
Be surgical, specific, concrete. Use their exact words. No fluff, no motivation, no pep talk.
Write like a senior engineer leaving precise handoff notes for themselves."""

def generate_cold_start(cycle):
    user_prompt = f"""Generate a cold start document from this session data:

PROJECT: {cycle['project']}
SESSION TYPE: {cycle['session_type']}
WHAT GOT DONE: {cycle['finished']}
EXACT NEXT ACTION: {cycle['next_action']}
PARALLEL THREADS: {cycle.get('parallel', 'none')}
WHAT TRIGGERED THIS SESSION: {cycle['trigger']}
WHAT NEARLY KILLED IT: {cycle.get('blocker', 'none noted')}
DATE/TIME: {cycle['timestamp']}

Write the cold start document in exactly this format:

## RE-ENTRY: {cycle['project']}
Last touched: {cycle['timestamp']}

### WHERE YOU ARE
[2-3 sentences: mental model of project — phase, what's working, current challenge]

### PICK UP HERE
[Exact re-entry — file, line, function, thought, tab — as specific as possible]

### THREADS STILL OPEN
[Parallel work items, AI outputs to review, side tabs open]

### WHY THIS SESSION WORKED
[1-2 sentences on trigger conditions — for pattern mining]

### FIRST 5 MINUTES
[Exactly what to do in the first 5 minutes — one concrete action before anything else]

Be specific. Use their exact words. No filler."""

    print(f"\n  {ORANGE}⠿{R} {GREY}Calling {get_model()} via OpenRouter...{R}", flush=True)
    result = call_openrouter(SYSTEM_PROMPT, user_prompt)
    return result

# ─── CYCLE FORM ──────────────────────────────────────────────────────────────
def close_cycle():
    data = load_data()
    print_header("Close a cycle — lock in before you sleep")

    # ── Step 1: Project ──
    print(f"  {ORANGE}{B}01 / 07  PROJECT{R}\n")
    
    # Show existing projects as shortcuts
    existing = list(data["projects"].keys())
    project = ""
    if existing:
        print(f"  {GREY}Existing projects (or type a new name):{R}\n")
        for i, p in enumerate(existing[:8], 1):
            proj_data = data["projects"][p]
            n_cycles  = len(proj_data.get("cycles", []))
            last      = proj_data.get("last_touched", "never")
            status    = proj_data.get("status", "active")
            scol      = GREEN if status == "active" else GREY
            print(f"  {DKGREY} {i} {R} {ORANGE}{p}{R}  {GREY}{n_cycles} cycles · last {last} · {scol}{status}{R}")
        print(f"  {DKGREY} N {R} {CREAM}New project{R}")
        print()
        raw = input(f"  {CYAN}{B}› {R}{CREAM}Select number or type name: {R}").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(existing[:8]):
            project = existing[int(raw)-1]
        elif raw.upper() == "N" or raw == "":
            project = ""
        else:
            project = raw
    
    if not project:
        project = prompt("Project name", "What were you working on?")
    
    print(f"\n  {GREEN}✓ {ORANGE}{B}{project}{R}\n")
    divider()

    # ── Step 2: Session type ──
    print(f"\n  {ORANGE}{B}02 / 07  SESSION TYPE{R}\n")
    _, session_type = choose(
        "What kind of session was this?",
        ["🔥 Hyperfocus — fully locked in, time disappeared",
         "⚡ Activated  — functional, got things done",
         "🌫️  Foggy      — pushed through low energy"],
        colors=[RED, YELLOW, BLUE]
    )
    session_type = session_type.split("—")[0].strip()
    divider()

    # ── Step 3: What got done ──
    print(f"\n  {ORANGE}{B}03 / 07  WHAT GOT DONE{R}\n")
    finished = prompt_multiline(
        "What did you actually finish or reach?",
        "Specific outputs — completed the auth flow, got CNN to 87%, finished essay section 2..."
    )
    divider()

    # ── Step 4: Next action ──
    print(f"\n  {ORANGE}{B}04 / 07  EXACT NEXT ACTION{R}\n")
    next_action = prompt_multiline(
        "Where does future-you pick this up?",
        "Be surgical — file path, line number, function name, exact sentence to continue, which tab to open first."
    )
    divider()

    # ── Step 5: Parallel threads ──
    print(f"\n  {ORANGE}{B}05 / 07  PARALLEL THREADS{R}  {DKGREY}(optional){R}\n")
    print(f"  {GREY}AI generating something? Side research tab? Other project you touched?{R}\n")
    parallel = prompt("Parallel threads open", allow_empty=True)
    if not parallel:
        parallel = "none"
    divider()

    # ── Step 6: Trigger ──
    print(f"\n  {ORANGE}{B}06 / 07  WHAT TRIGGERED THIS SESSION{R}\n")
    trigger = prompt_multiline(
        "What made this session happen?",
        "Time of day, mood, what you did before, conversation that sparked it, meal, environment..."
    )
    divider()

    # ── Step 7: Blocker ──
    print(f"\n  {ORANGE}{B}07 / 07  WHAT NEARLY KILLED IT{R}  {DKGREY}(optional){R}\n")
    blocker = prompt("Any friction, near-exit, or thing you pushed through?", allow_empty=True)
    if not blocker:
        blocker = "none noted"
    divider()

    # ── Assemble cycle ──
    cycle = {
        "id":           int(time.time()),
        "project":      project,
        "session_type": session_type,
        "finished":     finished,
        "next_action":  next_action,
        "parallel":     parallel,
        "trigger":      trigger,
        "blocker":      blocker,
        "timestamp":    now_str(),
        "date":         date_str(),
        "cold_start":   "",
        "notes":        [],
        "archived":     False,
    }

    # ── Generate cold start ──
    print(f"\n  {ORANGE}{B}GENERATING COLD START DOCUMENT{R}")
    cold_start = generate_cold_start(cycle)
    cycle["cold_start"] = cold_start

    # ── Save ──
    data["cycles"].append(cycle)

    if project not in data["projects"]:
        data["projects"][project] = {"cycles": [], "status": "active", "created": date_str()}

    data["projects"][project]["cycles"].append(cycle["id"])
    data["projects"][project]["last_touched"] = now_str()

    save_data(data)

    # ── Display cold start ──
    print()
    divider("═", ORANGE)
    print(f"\n{ORANGE}{B}  COLD START DOCUMENT{R}  {GREY}— paste this into Obsidian as _cycle_log/{project}.md{R}\n")
    divider()
    print()
    for line in cold_start.split("\n"):
        if line.startswith("## "):
            print(f"  {ORANGE}{B}{line}{R}")
        elif line.startswith("### "):
            print(f"\n  {CYAN}{B}{line}{R}")
        elif line.startswith("**") or line.startswith("*"):
            print(f"  {YELLOW}{line}{R}")
        elif line.strip() == "":
            print()
        else:
            print(f"  {CREAM}{wrap(line, 2)}{R}")
    print()
    divider("═", ORANGE)
    print(f"\n  {GREEN}{B}✓ Cycle saved.{R}  {GREY}Project: {ORANGE}{project}{R}  {GREY}· ID: {cycle['id']}{R}")

    # Copy to clipboard option
    try:
        import subprocess
        if confirm("\n  Copy cold start doc to clipboard?"):
            subprocess.run(["xclip", "-selection", "clipboard"],
                           input=cold_start.encode(), capture_output=True)
            print(f"  {GREEN}✓ Copied.{R}")
    except:
        pass

    input(f"\n  {DKGREY}Press Enter to return to menu...{R}")

# ─── VIEW PROJECTS ───────────────────────────────────────────────────────────
def view_projects():
    data = load_data()
    print_header("Projects — all active tracks")

    projects = data.get("projects", {})
    if not projects:
        print(f"  {GREY}No projects yet. Close a cycle to create one.{R}\n")
        input(f"  {DKGREY}Press Enter...{R}")
        return

    active   = {k:v for k,v in projects.items() if v.get("status","active") == "active"}
    paused   = {k:v for k,v in projects.items() if v.get("status") == "paused"}
    archived = {k:v for k,v in projects.items() if v.get("status") == "archived"}

    def print_project_row(name, proj, color):
        n      = len(proj.get("cycles", []))
        last   = proj.get("last_touched", "—")
        status = proj.get("status", "active")
        all_cycles = [c for c in data["cycles"] if c["project"] == name and not c.get("archived")]
        last_type  = all_cycles[-1]["session_type"] if all_cycles else "—"
        print(f"  {color}{B}{name}{R}")
        print(f"  {DKGREY}  {n} cycles · last touched {last} · last session: {last_type}{R}")
        if all_cycles:
            preview = all_cycles[-1]["next_action"][:80].replace("\n"," ")
            print(f"  {DKGREY}  Next: {GREY}{preview}{'...' if len(all_cycles[-1]['next_action'])>80 else ''}{R}")
        print()

    if active:
        print(f"  {GREEN}{B}ACTIVE  ({len(active)}){R}\n")
        for name, proj in active.items():
            print_project_row(name, proj, ORANGE)

    if paused:
        print(f"  {YELLOW}{B}PAUSED  ({len(paused)}){R}\n")
        for name, proj in paused.items():
            print_project_row(name, proj, YELLOW)

    if archived:
        print(f"  {GREY}{B}ARCHIVED  ({len(archived)}){R}\n")
        for name, proj in archived.items():
            print_project_row(name, proj, GREY)

    divider()
    print()
    print(f"  {DKGREY} P {R} {CREAM}Change project status{R}")
    print(f"  {DKGREY} V {R} {CREAM}View project cycles{R}")
    print(f"  {DKGREY} Enter {R} {CREAM}Back to menu{R}")
    print()
    raw = input(f"  {CYAN}{B}› {R}").strip().upper()

    if raw == "P":
        change_project_status(data)
    elif raw == "V":
        view_project_cycles(data)

def change_project_status(data):
    projects = list(data["projects"].keys())
    if not projects:
        return
    print(f"\n  {CREAM}Which project?{R}\n")
    for i, p in enumerate(projects, 1):
        status = data["projects"][p].get("status", "active")
        scol = GREEN if status=="active" else YELLOW if status=="paused" else GREY
        print(f"  {DKGREY} {i} {R} {ORANGE}{p}  {scol}[{status}]{R}")
    print()
    raw = input(f"  {CYAN}› {R}").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(projects)):
        return
    pname = projects[int(raw)-1]

    print(f"\n  {CREAM}Set status for {ORANGE}{pname}{R}:\n")
    _, status = choose("New status", ["active", "paused", "archived"],
                       colors=[GREEN, YELLOW, GREY])
    data["projects"][pname]["status"] = status
    save_data(data)
    print(f"\n  {GREEN}✓ {ORANGE}{pname}{R} → {status}{R}")
    input(f"\n  {DKGREY}Press Enter...{R}")

def view_project_cycles(data):
    projects = list(data["projects"].keys())
    if not projects:
        return
    print(f"\n  {CREAM}Which project?{R}\n")
    for i, p in enumerate(projects, 1):
        n = len(data["projects"][p].get("cycles",[]))
        print(f"  {DKGREY} {i} {R} {ORANGE}{p}  {GREY}({n} cycles){R}")
    print()
    raw = input(f"  {CYAN}› {R}").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(projects)):
        return
    pname = projects[int(raw)-1]
    cycles = [c for c in data["cycles"] if c["project"] == pname]
    browse_cycles(cycles, f"Project: {pname}")

# ─── BROWSE CYCLES ───────────────────────────────────────────────────────────
def browse_cycles(cycles=None, subtitle="All Cycles"):
    data = load_data()
    if cycles is None:
        cycles = [c for c in data["cycles"] if not c.get("archived")]
    print_header(subtitle)

    if not cycles:
        print(f"  {GREY}No cycles here yet.{R}\n")
        input(f"  {DKGREY}Press Enter...{R}")
        return

    # Show list
    type_colors = {"🔥 Hyperfocus": RED, "⚡ Activated": YELLOW, "🌫️  Foggy": BLUE}

    for i, c in enumerate(reversed(cycles[-20:]), 1):
        col = type_colors.get(c["session_type"], GREY)
        finished_preview = c["finished"][:60].replace("\n"," ")
        print(f"  {DKGREY} {i:2d} {R} {ORANGE}{B}{c['project']}{R}  {col}{c['session_type']}{R}  {GREY}{c['timestamp']}{R}")
        print(f"       {DKGREY}{finished_preview}{'...' if len(c['finished'])>60 else ''}{R}")
        print()

    divider()
    print(f"\n  {DKGREY}Enter number to view full cycle · {R}{CREAM}A{R}{DKGREY} to append note · {R}{CREAM}Enter{R}{DKGREY} to go back{R}\n")
    raw = input(f"  {CYAN}{B}› {R}").strip()

    if not raw:
        return

    # Append note
    if raw.upper().startswith("A"):
        rest = raw[1:].strip()
        if rest.isdigit():
            idx = len(cycles) - int(rest)
        else:
            num = input(f"  {CYAN}› Which cycle number to append note to? {R}").strip()
            idx = len(cycles) - int(num) if num.isdigit() else -1
        if 0 <= idx < len(cycles):
            target = cycles[idx]
            note_text = prompt("Note to append", "Quick thought, update, or follow-up")
            # Find in main data and update
            for c in data["cycles"]:
                if c["id"] == target["id"]:
                    c.setdefault("notes", []).append({"text": note_text, "ts": now_str()})
                    break
            save_data(data)
            print(f"  {GREEN}✓ Note appended.{R}")
            input(f"\n  {DKGREY}Press Enter...{R}")
        return

    if raw.isdigit():
        idx = len(cycles) - int(raw)
        if 0 <= idx < len(cycles):
            view_single_cycle(data, cycles[idx])

def view_single_cycle(data, cycle):
    print_header(f"{cycle['project']} · {cycle['timestamp']}")
    type_colors = {"🔥 Hyperfocus": RED, "⚡ Activated": YELLOW, "🌫️  Foggy": BLUE}
    col = type_colors.get(cycle["session_type"], GREY)

    print(f"  {ORANGE}{B}{cycle['project']}{R}  {col}{cycle['session_type']}{R}  {GREY}{cycle['timestamp']}{R}\n")

    sections = [
        ("WHAT GOT DONE",       "finished",    CREAM),
        ("EXACT NEXT ACTION",   "next_action", YELLOW),
        ("PARALLEL THREADS",    "parallel",    CYAN),
        ("WHAT TRIGGERED IT",   "trigger",     GREEN),
        ("WHAT NEARLY KILLED IT","blocker",    RED),
    ]
    for label, key, col in sections:
        val = cycle.get(key, "")
        if val and val != "none" and val != "none noted":
            print(f"  {ORANGE}{B}{label}{R}")
            for line in val.split("\n"):
                print(f"  {col}{wrap(line, 2)}{R}")
            print()

    if cycle.get("cold_start"):
        print(f"  {ORANGE}{B}COLD START DOCUMENT{R}\n")
        divider("─", DKGREY)
        for line in cycle["cold_start"].split("\n"):
            if line.startswith("## "):
                print(f"\n  {ORANGE}{B}{line}{R}")
            elif line.startswith("### "):
                print(f"\n  {CYAN}{line}{R}")
            elif line.strip():
                print(f"  {CREAM}{wrap(line, 2)}{R}")
            else:
                print()
        divider("─", DKGREY)

    if cycle.get("notes"):
        print(f"\n  {PURPLE}{B}APPENDED NOTES{R}\n")
        for note in cycle["notes"]:
            print(f"  {DKGREY}{note['ts']}{R}  {CREAM}{note['text']}{R}")

    print()
    print(f"  {DKGREY} G {R} {CREAM}Regenerate cold start doc{R}")
    print(f"  {DKGREY} N {R} {CREAM}Append a note{R}")
    print(f"  {DKGREY} X {R} {CREAM}Archive this cycle{R}")
    print(f"  {DKGREY} Enter {R} {CREAM}Back{R}")
    print()
    raw = input(f"  {CYAN}{B}› {R}").strip().upper()

    if raw == "G":
        print(f"\n  {ORANGE}Regenerating...{R}")
        new_cold = generate_cold_start(cycle)
        for c in data["cycles"]:
            if c["id"] == cycle["id"]:
                c["cold_start"] = new_cold
                break
        save_data(data)
        cycle["cold_start"] = new_cold
        print(f"  {GREEN}✓ Regenerated.{R}")
        input(f"\n  {DKGREY}Press Enter to view...{R}")
        view_single_cycle(data, cycle)

    elif raw == "N":
        note_text = prompt("Note", "Quick update, follow-up, or thought")
        for c in data["cycles"]:
            if c["id"] == cycle["id"]:
                c.setdefault("notes", []).append({"text": note_text, "ts": now_str()})
                break
        save_data(data)
        print(f"  {GREEN}✓ Note saved.{R}")
        input(f"\n  {DKGREY}Press Enter...{R}")

    elif raw == "X":
        if confirm("Archive this cycle?", default=False):
            for c in data["cycles"]:
                if c["id"] == cycle["id"]:
                    c["archived"] = True
                    break
            save_data(data)
            print(f"  {GREEN}✓ Archived.{R}")
            input(f"\n  {DKGREY}Press Enter...{R}")

# ─── TRIGGER MAP ─────────────────────────────────────────────────────────────
def trigger_map():
    data = load_data()
    print_header("Trigger Map — pattern intelligence")
    cycles = [c for c in data["cycles"] if not c.get("archived")]

    if len(cycles) < 3:
        print(f"  {GREY}Need at least 3 cycles to surface patterns. Keep logging.{R}\n")
        input(f"  {DKGREY}Press Enter...{R}")
        return

    # Session type breakdown
    from collections import Counter
    types = Counter(c["session_type"] for c in cycles)
    total = len(cycles)

    print(f"  {ORANGE}{B}SESSION TYPE BREAKDOWN  ({total} cycles){R}\n")
    type_colors = {"🔥 Hyperfocus": RED, "⚡ Activated": YELLOW, "🌫️  Foggy": BLUE}
    for stype, count in types.most_common():
        col  = type_colors.get(stype, GREY)
        pct  = count / total * 100
        bar  = "█" * int(pct / 4)
        print(f"  {col}{stype:25s}{R} {bar} {GREY}{count} ({pct:.0f}%){R}")

    print()
    divider()

    # Project heatmap
    proj_types = {}
    for c in cycles:
        p = c["project"]
        if p not in proj_types:
            proj_types[p] = Counter()
        proj_types[p][c["session_type"]] += 1

    print(f"\n  {ORANGE}{B}HYPERFOCUS BY PROJECT{R}\n")
    hf_key = "🔥 Hyperfocus"
    ranked = sorted(proj_types.items(), key=lambda x: x[1].get(hf_key, 0), reverse=True)
    for pname, tcounts in ranked[:10]:
        hf = tcounts.get(hf_key, 0)
        total_p = sum(tcounts.values())
        bar = "█" * hf
        print(f"  {ORANGE}{pname:25s}{R} {RED}{bar}{R} {GREY}{hf} hyperfocus / {total_p} total{R}")

    # Time of day (if available from trigger text — rough heuristic)
    print(f"\n  {ORANGE}{B}RECENT TRIGGERS (last 10 sessions){R}\n")
    for c in list(reversed(cycles))[:10]:
        trig = c.get("trigger","—")[:70].replace("\n"," ")
        col  = type_colors.get(c["session_type"], GREY)
        print(f"  {col}●{R} {GREY}{c['date']}{R}  {CREAM}{trig}{R}")

    # AI summary of patterns
    print()
    divider()
    print()
    if confirm("  Generate AI pattern analysis from your trigger data?"):
        all_triggers = "\n".join(
            f"- [{c['session_type']}] {c['project']} ({c['date']}): {c['trigger']}"
            for c in cycles[-20:]
        )
        sys_p = "You are analyzing productivity patterns for an AuDHD builder. Be specific, data-driven, and direct. No fluff."
        usr_p = f"""Analyze these session trigger logs and identify:
1. The most reliable conditions that produce hyperfocus sessions
2. Any patterns in timing, preceding activities, or project types
3. One concrete recommendation based on the data

Trigger data:
{all_triggers}

Be concise and specific. 3-4 sentences max per point."""

        print(f"\n  {ORANGE}Analyzing patterns...{R}\n")
        result = call_openrouter(sys_p, usr_p)
        divider("─", DKGREY)
        print()
        for line in result.split("\n"):
            print(f"  {CREAM}{wrap(line, 2)}{R}")
        print()
        divider("─", DKGREY)

    input(f"\n  {DKGREY}Press Enter to return to menu...{R}")

# ─── SETTINGS ────────────────────────────────────────────────────────────────
def settings():
    cfg = load_config()
    print_header("Settings")
    print(f"  {GREY}Data stored at: {CREAM}{BASE_DIR}{R}")
    print(f"  {GREY}Config:         {CREAM}{CONFIG_FILE}{R}")
    print(f"  {GREY}Cycles data:    {CREAM}{DATA_FILE}{R}\n")

    key     = cfg.get("openrouter_api_key","not set")
    key_disp= key[:8] + "..." + key[-4:] if len(key) > 12 else key
    model   = cfg.get("model", "anthropic/claude-3-haiku")
    data    = load_data()
    n_cycles= len(data.get("cycles",[]))
    n_proj  = len(data.get("projects",{}))

    print(f"  {ORANGE}API Key   {R} {CREAM}{key_disp}{R}")
    print(f"  {ORANGE}Model     {R} {CREAM}{model}{R}")
    print(f"  {ORANGE}Cycles    {R} {CREAM}{n_cycles}{R}")
    print(f"  {ORANGE}Projects  {R} {CREAM}{n_proj}{R}")
    print()
    divider()
    print()
    print(f"  {DKGREY} K {R} {CREAM}Update API key{R}")
    print(f"  {DKGREY} M {R} {CREAM}Change model{R}")
    print(f"  {DKGREY} E {R} {CREAM}Export all data to JSON{R}")
    print(f"  {DKGREY} Enter {R} {CREAM}Back{R}")
    print()

    raw = input(f"  {CYAN}{B}› {R}").strip().upper()

    if raw == "K":
        key = prompt("New OpenRouter API key")
        cfg["openrouter_api_key"] = key
        save_config(cfg)
        print(f"  {GREEN}✓ Key updated.{R}")
        input(f"\n  {DKGREY}Press Enter...{R}")

    elif raw == "M":
        set_model_interactive()
        input(f"\n  {DKGREY}Press Enter...{R}")

    elif raw == "E":
        export_path = Path.home() / f"cycle_close_export_{date_str()}.json"
        export_path.write_text(DATA_FILE.read_text())
        print(f"  {GREEN}✓ Exported to {export_path}{R}")
        input(f"\n  {DKGREY}Press Enter...{R}")

# ─── MAIN MENU ───────────────────────────────────────────────────────────────
MENU_ITEMS = [
    ("C", "Close a cycle",       ORANGE, "Lock in before you sleep — generate cold start doc"),
    ("P", "Projects",            GREEN,  "All active tracks, status, last touched"),
    ("B", "Browse cycles",       CYAN,   "Full history — view, append notes, archive"),
    ("T", "Trigger map",         PURPLE, "Pattern intelligence across your sessions"),
    ("S", "Settings",            GREY,   "API key, model, export"),
    ("Q", "Quit",                DKGREY, ""),
]

def main_menu():
    while True:
        data   = load_data()
        n_cyc  = len([c for c in data.get("cycles",[]) if not c.get("archived")])
        n_proj = len([p for p,v in data.get("projects",{}).items() if v.get("status","active")=="active"])

        print_header(f"{n_cyc} cycles · {n_proj} active projects")

        # Show last closed project as a quick re-entry card
        cycles = [c for c in data.get("cycles",[]) if not c.get("archived")]
        if cycles:
            last = cycles[-1]
            type_colors = {"🔥 Hyperfocus": RED, "⚡ Activated": YELLOW, "🌫️  Foggy": BLUE}
            col = type_colors.get(last["session_type"], GREY)
            print(f"  {DKGREY}LAST CYCLE{R}  {ORANGE}{B}{last['project']}{R}  {col}{last['session_type']}{R}  {GREY}{last['timestamp']}{R}")
            na = last["next_action"][:80].replace("\n"," ")
            print(f"  {DKGREY}Next: {GREY}{na}{'...' if len(last['next_action'])>80 else ''}{R}")
            print()
            divider()
            print()

        for key, label, col, hint in MENU_ITEMS:
            hint_str = f"  {DKGREY}{hint}{R}" if hint else ""
            print(f"  {BG_SEL} {col}{B}{key}{R}{BG_SEL} {R}  {CREAM}{label}{R}{hint_str}")
        print()

        try:
            raw = input(f"  {CYAN}{B}› {R}").strip().upper()
        except (KeyboardInterrupt, EOFError):
            raw = "Q"

        if raw == "C":
            close_cycle()
        elif raw == "P":
            view_projects()
        elif raw == "B":
            browse_cycles()
        elif raw == "T":
            trigger_map()
        elif raw == "S":
            settings()
        elif raw == "Q":
            print(f"\n  {ORANGE}Stay in the cycle.{R}\n")
            sys.exit(0)

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Handle --help
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)

    # Check Python version
    if sys.version_info < (3, 7):
        print("Python 3.7+ required.")
        sys.exit(1)

    # Welcome on first run
    if not DATA_FILE.exists():
        clear()
        print(f"\n  {ORANGE}{B}CYCLE CLOSE{R}  {GREY}first run setup{R}\n")
        print(f"  {CREAM}Mental version control for projects — not just code.{R}")
        print(f"  {GREY}Data will be stored in {CREAM}{BASE_DIR}{R}\n")
        print(f"  {GREY}You'll need an OpenRouter API key to generate cold start docs.{R}")
        print(f"  {GREY}Get one free at {CYAN}https://openrouter.ai{R}\n")
        input(f"  {DKGREY}Press Enter to continue...{R}")
        save_data({"cycles": [], "projects": {}})

    main_menu()
