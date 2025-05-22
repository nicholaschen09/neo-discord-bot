import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone 
from groq import Groq 

load_dotenv()

# Initialize Groq client
groq_client = Groq(
    api_key=os.getenv('GROQ_API_KEY')
)

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True # Crucial: Enable in Discord Developer Portal
intents.members = True # Ensure this is enabled in Discord Developer Portal too

bot = commands.Bot(command_prefix='!', intents=intents)

# Store unread messages in memory
unread_messages = {}

@bot.event
async def on_ready():
    """Confirms the bot has connected to Discord."""
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    """Stores incoming messages for summarization, ignoring bot's own messages."""
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)

    # Ensure message.created_at is timezone-aware (Discord timestamps are UTC)
    msg_timestamp = message.created_at.replace(tzinfo=timezone.utc) if message.created_at.tzinfo is None else message.created_at
    
    if channel_id not in unread_messages:
        unread_messages[channel_id] = []
    
    unread_messages[channel_id].append({
        'content': message.content,
        'author': str(message.author),
        'timestamp': msg_timestamp
    })

    # Process commands (e.g., !summarize) after storing the message
    await bot.process_commands(message)

@bot.command(name='summarize')
async def summarize(ctx):
    """Summarizes unread messages in the current channel using Groq."""
    channel_id = str(ctx.channel.id)
    
    if channel_id not in unread_messages or not unread_messages[channel_id]:
        await ctx.send("No unread messages to summarize!")
        return

    # Filter messages from the last 24 hours
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    recent_messages = [
        msg for msg in unread_messages[channel_id]
        if msg['timestamp'] > one_day_ago
    ]

    if not recent_messages:
        await ctx.send("No messages in the last 24 hours to summarize!")
        return

    # Format messages for the Groq API
    conversation_history = ""
    for msg in recent_messages:
        # Using a consistent UTC timestamp format for clarity in the prompt
        conversation_history += f"**{msg['author']}** ({msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}): {msg['content']}\n"

    try:
        await ctx.send("Generating summary with Groq... Please wait.")
        
        # Groq API call for chat completions
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes Discord conversations concisely. Focus on key topics and decisions."},
                {"role": "user", "content": f"Please summarize the following Discord conversation:\n\n{conversation_history}"}
            ],
            model="llama3-8b-8192", # Or "mixtral-8x7b-32768" or "llama3-70b-8192" based on your preference and Groq's offerings
            temperature=0.7, # Adjust creativity, 0.0 for more factual, 1.0 for more creative
            max_tokens=500, # Max length of the summary
        )
        
        ai_summary = chat_completion.choices[0].message.content
        
        # Clear the unread messages for this channel AFTER successful summarization
        unread_messages[channel_id] = []

        # Send the AI-generated summary, splitting if too long for Discord
        if len(ai_summary) > 2000:
            # Discord message limit is 2000 characters. Leave room for title.
            chunks = [ai_summary[i:i+1900] for i in range(0, len(ai_summary), 1900)]
            for chunk in chunks:
                await ctx.send(f"**AI Summary (continued):**\n{chunk}")
        else:
            await ctx.send(f"**AI Summary (Last 24 Hours):**\n\n{ai_summary}")

    except Exception as e: # Catching a broad exception for demonstration
        print(f"An error occurred during Groq API call: {e}")
        await ctx.send(f"An error occurred while trying to summarize: {e}")

@bot.command(name='clear')
async def clear(ctx):
    """Clears unread messages for the current channel."""
    channel_id = str(ctx.channel.id)
    if channel_id in unread_messages:
        unread_messages[channel_id] = []
        await ctx.send("Unread messages cleared!")
    else:
        await ctx.send("No unread messages to clear!")

# Run the bot with your Discord token
bot.run(os.getenv('DISCORD_TOKEN'))