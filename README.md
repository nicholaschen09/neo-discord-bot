# Discord Unread Message Summarizer Bot - Neo

This is a Discord bot that tracks unread messages in each channel and can summarize them using the Groq API (LLM inference, OpenAI-compatible). It also supports clearing unread messages per channel.

## Features
- Tracks unread messages per channel
- `!summarize` command: Summarizes the last 24 hours of unread messages using Groq LLMs
- `!clear` command: Clears unread messages for the current channel

## Setup

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd discord-bot-unread-msgs
```

### 2. Create and activate a virtual environment
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```sh
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root with the following content:
```
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
```
- Get your Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- Get your Groq API key from the [Groq Console](https://console.groq.com/)

### 5. Run the bot
```sh
python3 bot.py
```

## Usage
- Invite the bot to your server.
- Use `!summarize` in any channel to get a summary of the last 24 hours of unread messages.
- Use `!clear` to clear the unread message buffer for the current channel.

## Groq API Integration
- The bot uses the `llama3-70b-8192` model by default. You can change the model in `bot.py` if needed.
- For more info on available models and API usage, see the [Groq API documentation](https://console.groq.com/docs/overview).

## Troubleshooting
- If you see a model not found error, make sure the model name in your code matches one available to your Groq account.
- Always restart the bot after making changes to the code or `.env` file.

## License
MIT 