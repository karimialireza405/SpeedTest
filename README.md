# SpeedTest CLI

A cyberpunk-inspired, terminal-native internet speed test built with Python, Rich, and Textual. The dashboard runs entirely in the command line, using ANSI neon accents, animated gauges, and live updates from `speedtest-cli`.

## Features
- Auto-selects the best server and measures ping, download, and upload throughput
- Live ASCII speedometer and analyzer bars with 30 FPS updates
- Dual units: Mbps and MB/s
- Clipboard copy, JSON export, and persistent history of the last 10 tests
- Keyboard-driven controls: **Enter** start, **Esc** stop, **C** copy, **J** export, **Q** quit
- Cross-platform (Windows, macOS, Linux) and runs fully in the terminal

## Requirements
- Python 3.11+
- Internet connectivity for running tests

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```

Controls are shown in the footer. Results are saved to `~/.speedtest_history.json`; exports are written to the current working directory.

## Project Structure
```
main.py
core/
  speedtest_engine.py
  units.py
  history.py
ui/
  cli_dashboard.py
  gauges.py
requirements.txt
```

## Notes
- Clipboard support uses `pyperclip` and may need a backend (e.g., `xclip` on Linux). If unavailable, the app shows a non-fatal alert.
- Animations are terminal-safe and avoid flicker; frame pacing can be adjusted via the `set_interval` call in `cli_dashboard.py`.
