# Discord Gemini Bot

A Discord bot powered by Google's Gemini AI, designed to assist with coding questions (specifically Godot Engine, but generalizable) and file management.

## Features

- **Chat with Gemini:** use the `/bard` command (or DM the bot) to chat with the AI. Supports text and image inputs (OCR via Tesseract).
- **Git Integration:** use `/commit_push` to commit and push changes to a repository directly from Discord.
- **Context Awareness:** The bot is pre-loaded with context to act as a Godot Engine expert, but this can be modified in `data/bot_context.json`.

## Prerequisites

- **Python 3.8+**
- **Git** installed and available in the system PATH.
- **Tesseract OCR** installed and available in the system PATH (required for image text extraction).
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki) and add installation path to PATH environment variable.
  - Linux: `sudo apt install tesseract-ocr`
  - macOS: `brew install tesseract`

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/yourrepo.git
    cd yourrepo
    ```

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    # or on Windows: copy .env.example .env
    ```

2.  Open `.env` and fill in your credentials:
    -   `DISCORD_BOT_TOKEN`: Your Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications)).
    -   `GEMINI_API_KEY`: Your Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/)).
    -   `REPO_PATH`: The local path to the Git repository you want to manage with `/commit_push` (can be this repo or another one).

## Usage

1.  Run the bot:
    ```bash
    python main.py
    ```

2.  Invite the bot to your server.
3.  Use `/bard <prompt>` or DM the bot to start chatting.
4.  Use `/commit_push <message>` to commit changes to the configured repository.

## Hosting

A `server.py` script is included to help keep the bot alive on hosting services that require a web server (e.g., Replit, Glitch). You can import `keep_alive` from `server` in `main.py` and call `keep_alive()` before `bot.run()`.

## License

[MIT](LICENSE)
