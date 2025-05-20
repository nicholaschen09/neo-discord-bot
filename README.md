# Discord Unread Messages Summarizer Bot

This Discord bot helps you keep track of and summarize unread messages in your Discord channels.

## Features

- Tracks messages in channels where the bot is present
- Provides summaries of unread messages from the last 24 hours
- Allows clearing of tracked messages
- Handles long messages by splitting them into chunks

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

- `!summarize` - Shows a summary of unread messages in the current channel from the last 24 hours
- `!clear` - Clears the tracked unread messages for the current channel

## Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Under the bot section, enable the following Privileged Gateway Intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
5. Copy the bot token and add it to your `.env` file

## Inviting the Bot to Your Server

1. Go to OAuth2 > URL Generator in the Developer Portal
2. Select the following scopes:
   - bot
   - applications.commands
3. Select the following bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - Read Message History
4. Use the generated URL to invite the bot to your server 