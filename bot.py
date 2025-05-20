import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import openai
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store unread messages
unread_messages = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Store message in unread_messages
    channel_id = str(message.channel.id)
    if channel_id not in unread_messages:
        unread_messages[channel_id] = []
    
    unread_messages[channel_id].append({
        'content': message.content,
        'author': str(message.author),
        'timestamp': message.created_at
    })

    await bot.process_commands(message)

@bot.command(name='summarize')
async def summarize(ctx):
    """Summarize unread messages in the current channel"""
    channel_id = str(ctx.channel.id)
    
    if channel_id not in unread_messages or not unread_messages[channel_id]:
        await ctx.send("No unread messages to summarize!")
        return

    # Get messages from the last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    recent_messages = [
        msg for msg in unread_messages[channel_id]
        if msg['timestamp'] > one_day_ago
    ]

    if not recent_messages:
        await ctx.send("No messages in the last 24 hours!")
        return

    # Create a summary of messages
    summary = "**Message Summary (Last 24 Hours):**\n\n"
    for msg in recent_messages:
        summary += f"**{msg['author']}** ({msg['timestamp'].strftime('%H:%M:%S')}): {msg['content']}\n"

    # Clear the unread messages for this channel
    unread_messages[channel_id] = []

    # Split summary if it's too long
    if len(summary) > 2000:
        chunks = [summary[i:i+1900] for i in range(0, len(summary), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(summary)

@bot.command(name='clear')
async def clear(ctx):
    """Clear unread messages for the current channel"""
    channel_id = str(ctx.channel.id)
    if channel_id in unread_messages:
        unread_messages[channel_id] = []
        await ctx.send("Unread messages cleared!")
    else:
        await ctx.send("No unread messages to clear!")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN')) 