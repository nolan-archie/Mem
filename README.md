# Mem

**Mem** is a local AI framework designed to simulate a self-aware, adaptive assistant. It can think, remember, and interact naturally. Mem connects to GitHub’s AI inference API when online and continues to function autonomously offline using its internal memory and mood systems. Everything is modular and customizable.

---

## Quickstart (Copy-paste commands)

Choose the section that matches your OS and paste commands into your terminal or PowerShell.

### SETUP: clone repository and enter folder

```bash
git clone https://github.com/nolan-archie/Mem.git
cd Mem
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

export GITHUB_TOKEN="your_token_here"

python cli_chat.py
```

### Windows (PowerShell)

```powershell
python -m venv venv

.\venv\Scripts\Activate.ps1

pip install -r requirements.txt


python cli_chat.py
```
set GITHUB_TOKEN in core/brain.py
### Windows (CMD)

```cmd
python -m venv venv

venv\Scripts\activate.bat

pip install -r requirements.txt

python cli_chat.py
```
set GITHUB_TOKEN in core/brain.py
---

## Optional single-line variants

One-line: clone, create venv, activate, install (Linux/macOS):

```bash
git clone https://github.com/nolan-archie/Mem.git && cd Mem && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

One-line (Windows PowerShell):

```powershell
git clone https://github.com/nolan-archie/Mem.git; cd Mem; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

---

## Create a GitHub Personal Access Token (PAT)

1. Sign in to GitHub.
2. Open **Settings > Developer settings > Personal access tokens**.
3. Create a new token (classic or fine-grained).
4. Give it the minimal permissions you need (for Mem: `read:packages` and `inference:write` if available).
5. Copy the token and paste it into the `export` / `setx` command above.

> Note: If you use `setx` on Windows, open a new terminal window after running it so the environment variable is available in that session.

---

## Where files live

* `sandbox/` — local storage for memories, configs, and data files.
* `config/personality.json` — personality and behavior settings to edit.
* `cli_chat.py` — main CLI interface.

---

## Troubleshooting

* If `pip install -r requirements.txt` fails, ensure the virtual environment is active.
* If `python` points to Python 2 on your system, try `python3` instead.
* After `setx GITHUB_TOKEN`, open a new shell to use the variable.
* If you see permission errors with your PAT, confirm its scopes.

---

## Run (recap)

Paste the matching commands from the Quickstart section above for your OS. The basic sequence is:

1. Clone repository
2. Create & activate venv
3. Install dependencies
4. Set `GITHUB_TOKEN`
5. Run `python cli_chat.py`

---

## License

MIT License

Copyright (c) 2025 nolan-archie

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

