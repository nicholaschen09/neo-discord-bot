# Discord Message Summarizer Bot – Neo

This is a Discord bot that summarizes recent messages in a channel using the Groq API (LLM inference, OpenAI-compatible). Instead of tracking unread messages, the bot fetches message history directly from Discord in real time and summarizes on demand via slash commands.

## Features

* `/summary` slash command: Summarizes recent messages using Groq LLMs

  * Supports ISO timestamps or natural time durations (e.g. `2h`, `30m`, `1d`)
  * Optional user filters to focus on specific participants
  * Can run across a single channel or all text channels
* `/summary_links` modal command: Summarizes the conversation between two message links
* No message storage — summary is generated live using recent history from Discord

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
MODEL_API_KEY=your_groq_api_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama3-70b-8192
```

* Get your Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
* Get your Groq API key from the [Groq Console](https://console.groq.com/)
* You can change the model or provider by editing `OPENAI_MODEL` and `OPENAI_BASE_URL`

### 5. Run the bot

```sh
python3 bot.py
```

## Usage

* Invite the bot to your server.
* Use `/summary` in any channel to generate a summary of recent messages.

  * You can specify a time window (e.g. `last 2 hours`) or provide exact timestamps.
  * You can limit the summary to specific users or channels.
* Use `/summary_links` to summarize between two specific messages via a modal prompt.

## Groq API Integration

* The bot uses the `llama3-70b-8192` model by default. This can be changed via environment variables.
* Compatible with any OpenAI-style provider (Groq, OpenRouter, etc.)
* See the [Groq API documentation](https://console.groq.com/docs/overview) for details on available models and usage.

## Troubleshooting

* If you get a “model not found” error, make sure the model name matches one supported by your chosen provider.
* Be sure to restart the bot after changing the `.env` file or modifying code.

## License

MIT