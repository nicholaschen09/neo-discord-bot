import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import openai
from discord import ui
import re

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


for noisy_logger in ["discord", "httpx", "groq", "httpcore", "asyncio"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)


BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("OPENAI_MODEL", "llama3-70b-8192")


openai_client = openai.OpenAI(base_url=BASE_URL, api_key=os.getenv("MODEL_API_KEY"))


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logging.info("%s has connected to Discord!", bot.user)

    try:
        chat_completion = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            model=MODEL,
            temperature=0.7,
            max_tokens=100,
        )
        logging.info("LLM API connection successful! (Groq by default)")
    except Exception as e:
        logging.error("Error connecting to LLM API: %s", e)
    try:
        await bot.tree.sync()
        logging.info("Slash commands synced")
    except Exception as e:
        logging.error("Failed to sync commands: %s", e)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)

    msg_timestamp = (
        message.created_at.replace(tzinfo=timezone.utc)
        if message.created_at.tzinfo is None
        else message.created_at
    )

    logging.debug("Stored message from %s in channel %s", message.author, channel_id)

    await bot.process_commands(message)


@bot.tree.command(
    name="summary",
    description="Summarize messages in this channel or all channels. All arguments are optional.",
)
@app_commands.describe(
    from_time="Start time (ISO-8601, e.g. 2024-06-01T12:00:00Z) or duration (e.g. 30m, 2hr, 5d) ago. Defaults to 1 hour ago if not set.",
    to_time="End time (ISO-8601, e.g. 2024-06-01T15:00:00Z) or duration (e.g. 10m, 1hr, 2d) ago. Defaults to now if not set.",
    users="User(s) to include (mention one or more users, e.g. @user1 @user2). Optional.",
    all_channels="If true, summarize all accessible text channels in this server. Defaults to false (just this channel).",
    ephemeral="If true, the summary is only visible to you. Defaults to true.",
)
async def slash_summary(
    interaction: discord.Interaction,
    from_time: str | None = None,
    to_time: str | None = None,
    users: str | None = None,
    all_channels: bool = False,
    ephemeral: bool = True,
):
    await interaction.response.defer(ephemeral=ephemeral)

    channel = interaction.channel
    after_time = None
    before_time = None
    user_ids = None

    def parse_duration(duration_str):
        units = {
            "s": "seconds",
            "m": "minutes",
            "h": "hours",
            "d": "days",
            "w": "weeks",
        }

        stripped = duration_str.strip().lower()

        match = re.fullmatch(r"(\d+)\s*([smhdw]|hr|sec|min|day|wk)s?", stripped)
        if not match:

            match_num = re.fullmatch(r"(\d+)", stripped)
            if match_num:
                value = int(match_num.group(1))
                unit = "m"
            else:
                return None
        else:
            value, unit = match.groups()
            value = int(value)
            if unit in ["hr", "h"]:
                unit = "h"
            elif unit in ["min", "m"]:
                unit = "m"
            elif unit in ["sec", "s"]:
                unit = "s"
            elif unit in ["day", "d"]:
                unit = "d"
            elif unit in ["wk", "w"]:
                unit = "w"
        kwarg = {units[unit]: value}
        return timedelta(**kwarg)

    def extract_user_ids(users_str):

        ids = set()
        for part in re.split(r"[\s,]+", users_str.strip()):
            if not part:
                continue
            m = re.match(r"<@!?(\d+)>", part)
            if m:
                ids.add(int(m.group(1)))
            elif part.startswith("@") and len(part) > 1:

                for member in channel.members:
                    if member.name == part[1:] or (
                        member.nick and member.nick == part[1:]
                    ):
                        ids.add(member.id)
        return ids

    now = datetime.now(timezone.utc)

    if from_time:
        dur = parse_duration(from_time)
        if dur:
            after_time = now - dur
        else:
            try:
                after_time = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
            except Exception:
                await interaction.followup.send(
                    "Invalid 'from_time' format. Use ISO-8601 or duration like 30m, 2hr, 5d.",
                    ephemeral=ephemeral,
                )
                return
    else:
        after_time = now - timedelta(hours=1)

    if to_time:
        dur = parse_duration(to_time)
        if dur:
            before_time = now - dur
        else:
            try:
                before_time = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
            except Exception:
                await interaction.followup.send(
                    "Invalid 'to_time' format. Use ISO-8601 or duration like 10m, 1hr, 2d.",
                    ephemeral=ephemeral,
                )
                return
    else:
        before_time = now

    if users:
        user_ids = extract_user_ids(users)

    messages = []
    if all_channels and interaction.guild:

        for ch in interaction.guild.text_channels:
            try:
                async for m in ch.history(
                    after=after_time, before=before_time, oldest_first=True, limit=100
                ):
                    messages.append(m)
            except Exception:
                continue
    else:
        async for m in channel.history(
            after=after_time, before=before_time, oldest_first=True, limit=100
        ):
            messages.append(m)
    if user_ids:
        messages = [m for m in messages if m.author.id in user_ids]
    if not messages:
        await interaction.followup.send(
            "No messages found for the given range and filters.", ephemeral=ephemeral
        )
        return

    messages.sort(key=lambda m: m.created_at)
    conversation_history = ""
    for m in messages:
        timestamp = m.created_at.replace(tzinfo=timezone.utc)
        conversation_history += f"**{m.author}** ({timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}): {m.content}\n"
    chat_completion = openai_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes Discord conversations concisely. Focus on key topics and decisions.",
            },
            {
                "role": "user",
                "content": f"Please summarize the following Discord conversation:\n\n{conversation_history}",
            },
        ],
        model=MODEL,
        temperature=0.7,
        max_tokens=500,
    )
    ai_summary = chat_completion.choices[0].message.content
    if len(ai_summary) > 2000:
        chunks = [ai_summary[i : i + 1900] for i in range(0, len(ai_summary), 1900)]
        for chunk in chunks:
            await interaction.followup.send(chunk, ephemeral=ephemeral)
    else:
        await interaction.followup.send(ai_summary, ephemeral=ephemeral)


class SummaryLinksModal(ui.Modal, title="Summarize by Message Links"):
    start_link = ui.TextInput(
        label="Start message link",
        placeholder="Paste the first message link",
        required=True,
    )
    end_link = ui.TextInput(
        label="End message link",
        placeholder="Paste the second message link",
        required=True,
    )
    ephemeral = ui.TextInput(
        label="Ephemeral? (true/false)", default="true", required=True
    )

    def __init__(self, bot, interaction):
        super().__init__()
        self.bot = bot
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        ephemeral_value = self.ephemeral.value.strip().lower()
        ephemeral = True if ephemeral_value in ("true", "yes", "1", "y") else False
        await interaction.response.defer(ephemeral=ephemeral)

        def parse_link(link: str):
            parts = link.split("/")
            if len(parts) < 3:
                raise ValueError("Invalid message link")
            return int(parts[-3]), int(parts[-2]), int(parts[-1])

        try:
            _, channel_id, start_id = parse_link(self.start_link.value)
            _, channel_id2, end_id = parse_link(self.end_link.value)
            if channel_id != channel_id2:
                await interaction.followup.send(
                    "Both links must be from the same channel", ephemeral=ephemeral
                )
                return
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
            start_msg = await channel.fetch_message(start_id)
            end_msg = await channel.fetch_message(end_id)
            after_time = start_msg.created_at
            before_time = end_msg.created_at
            messages = [start_msg]
            async for m in channel.history(
                after=after_time, before=before_time, oldest_first=True, limit=100
            ):
                messages.append(m)
            messages.append(end_msg)
            messages.sort(key=lambda m: m.created_at)
            conversation_history = ""
            for m in messages:
                timestamp = m.created_at.replace(tzinfo=timezone.utc)
                conversation_history += f"**{m.author}** ({timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}): {m.content}\n"
            chat_completion = openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that summarizes Discord conversations.\n"
                            "Please follow these instructions when creating your summary:\n"
                            "- **Conciseness**: Keep the summary brief and to the point.\n"
                            "- **Key Topics**: Highlight the main topics discussed.\n"
                            "- **Decisions**: Clearly note any decisions or action items.\n"
                            "- **Clarity**: Use clear, easy-to-understand language.\n"
                            "- **Formatting**: Present each note as a bullet point, with the **user name** in bold at the start of each bullet.\n"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Please summarize the following Discord conversation:\n\n{conversation_history}"
                        ),
                    },
                ],
                model=MODEL,
                temperature=0.7,
                max_tokens=500,
            )
            ai_summary = chat_completion.choices[0].message.content
            if len(ai_summary) > 2000:
                chunks = [
                    ai_summary[i : i + 1900] for i in range(0, len(ai_summary), 1900)
                ]
                for chunk in chunks:
                    await interaction.followup.send(chunk, ephemeral=ephemeral)
            else:
                await interaction.followup.send(ai_summary, ephemeral=ephemeral)
        except Exception as e:
            import logging

            logging.exception("Error in summary_links modal: %s", e)
            await interaction.followup.send(
                f"An error occurred: {e}", ephemeral=ephemeral
            )


@bot.tree.command(
    name="summary_links",
    description="Summarize messages between two message links (ephemeral modal)",
)
async def summary_links(interaction: discord.Interaction):
    await interaction.response.send_modal(SummaryLinksModal(bot, interaction))


bot.run(os.getenv("DISCORD_TOKEN"))
