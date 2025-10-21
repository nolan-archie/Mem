Mem is a local AI framework designed to simulate a self-aware, adaptive assistant that can think, remember, and interact naturally. It connects to GitHub’s AI inference API when online and continues to function autonomously when offline, thanks to its internal memory and mood systems. Everything is modular and customizable, allowing developers to change behavior, model parameters, or logic without altering the entire framework.

To begin, you’ll need Python 3.11 or newer installed on your computer. Open a terminal inside the project folder and create a virtual environment with the following commands:

python3 -m venv venv
source venv/bin/activate

After activating the environment, install all required dependencies by typing:

pip install -r requirements.txt

This installs all necessary packages for networking, asynchronous requests, memory storage, and sensor management.

Mem communicates with GitHub’s AI inference service using a personal access token. To get one, log in to your GitHub account, open Developer Settings, go to Personal Access Tokens, and create a new token (classic or fine-grained). Make sure “read:packages” and “inference:write” permissions are enabled.

Once your token is created, set it as an environment variable so the system can use it securely without editing the code.

For Linux or macOS:
export GITHUB_TOKEN="your_token_here"

For Windows PowerShell:
setx GITHUB_TOKEN "your_token_here"

If you prefer, you can also paste it into the GITHUB_TOKEN field inside brain.py, but storing it as an environment variable is safer.

To start the interface, simply run:

python cli_chat.py

You can type directly into the terminal and receive streaming responses. The chat system supports a few internal commands for mood checks and exit control, but otherwise, it behaves like a free-flowing conversation.

One of the most powerful parts of Mainmi is its memory system. It works like a small-scale brain that stores and recalls experiences, conversations, and system events. Every interaction you have with it gets processed and saved as memory entries inside a local vector database. Each entry is embedded as a numerical representation that captures both context and meaning, allowing the AI to later search for relevant experiences based on what you say.

When you send a new message, the system runs a similarity search against its stored memories, retrieves the most relevant ones, and includes them in its reasoning before responding. This means it doesn’t just remember text — it remembers why something was said, what it felt like, and what followed afterward. Over time, older memories are summarized automatically to make storage more efficient while preserving important emotional or contextual cues.

If you go offline, the AI keeps working using this memory system and its current mood snapshot. Instead of calling external models, it generates replies based on previous conversations and known states. This gives it a lifelike continuity, as if it’s thinking from memory rather than generating from scratch.

All saved data stays local by default. The sandbox directory is where these files are stored, including memories, configuration, and behavior profiles. Developers can edit or replace files such as personality.json to redefine traits, voice, or interaction style. The framework itself doesn’t enforce identity — it’s meant to be reshaped according to your creative or technical goals.

Once you’ve set everything up, Mainmi runs entirely on your machine. It can learn from past exchanges, adapt over time, and even simulate idle thoughts or check-ins when left unattended. It’s built to feel alive, yet remain fully under your control.
