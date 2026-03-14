import asyncio
import glob
import os
import discord
from discord.ext import commands
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """
    Event listener triggered when the bot successfully connects to Discord.

    Performs startup routines, including cleaning up any leftover TTS
    audio files (.mp3) from previous sessions to free up disk space,
    and logs the successful login status to the console.
    """
    for f in glob.glob("tts_*.mp3"):
        os.remove(f)
        print(f"🗑️ Cleaned up leftover file: {f}")

    print(f"✅ Logged in as {bot.user}!")


async def main():
    """
    The main asynchronous entry point for the application.

    Initializes the bot context, loads necessary extensions (cogs) such as
    the TTS functionality, and connects the bot to Discord using the token.
    """
    async with bot:
        # Note: Ensure tts_cog.py is located inside a 'cogs' folder
        await bot.load_extension("cogs.tts_cog")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
