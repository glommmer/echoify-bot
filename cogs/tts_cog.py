"""
Discord Cog module for the Echoify TTS bot.

This module handles TTS-related commands, event listeners for automatic
text-to-speech processing, and background tasks for resource management.
"""

import asyncio
import glob
import os
import discord
from discord.ext import commands, tasks

import config
import tts_engine


class TTSCog(commands.Cog):
    """
    A cog that encapsulates all Text-to-Speech functionality.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the TTSCog and starts the background task for checking
        empty voice channels.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        self.check_voice_channel.start()

    def cog_unload(self):
        """
        Cleans up and cancels background tasks when the cog is unloaded.
        """
        self.check_voice_channel.cancel()

    # ── Commands ────────────────────────────────────────────

    @commands.command(name="settextch")
    @commands.has_permissions(administrator=True)
    async def set_text_channel(self, ctx):
        """
        Sets the current text channel as the designated channel for automatic TTS.
        Only server administrators can use this command.
        """
        config.TTS_TEXT_CHANNEL_ID = ctx.channel.id
        await ctx.send(f"✅ TTS Text Channel set to: **#{ctx.channel.name}**")
        print(f"📢 Text channel updated: #{ctx.channel.name} (ID: {ctx.channel.id})")

    @commands.command(name="setvoicech")
    @commands.has_permissions(administrator=True)
    async def set_voice_channel(self, ctx):
        """
        Sets the user's current voice channel as the designated channel for TTS output.
        Only server administrators can use this command, and they must be in a voice channel.
        """
        if not ctx.author.voice:
            return await ctx.send("❌ Please join a voice channel first!")

        config.TTS_VOICE_CHANNEL_ID = ctx.author.voice.channel.id
        await ctx.send(
            f"✅ TTS Voice Channel set to: **{ctx.author.voice.channel.name}**"
        )
        print(
            f"🔊 Voice channel updated: {ctx.author.voice.channel.name} (ID: {config.TTS_VOICE_CHANNEL_ID})"
        )

    @commands.command(name="ttsinfo")
    async def tts_info(self, ctx):
        """
        Displays the currently configured text and voice channels for TTS.
        """
        text_ch = self.bot.get_channel(config.TTS_TEXT_CHANNEL_ID)
        voice_ch = self.bot.get_channel(config.TTS_VOICE_CHANNEL_ID)

        text_ch_name = f"#{text_ch.name}" if text_ch else "Not set"
        voice_ch_name = voice_ch.name if voice_ch else "Not set"

        await ctx.send(
            f"📢 Text Channel: **{text_ch_name}**\n"
            f"🔊 Voice Channel: **{voice_ch_name}**"
        )

    @commands.command(name="say")
    async def say(self, ctx, *, text: str):
        """
        Manually adds the provided text to the TTS queue to be spoken.

        Args:
            text (str): The text message to be converted to speech.
        """
        filename = f"tts_{ctx.author.id}.mp3"
        await tts_engine.tts_queue.put((text, filename))
        asyncio.create_task(tts_engine.process_queue(self.bot, ctx.guild))
        await ctx.send(f"🔊 Added to queue: *{text}*")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """
        Forces the bot to disconnect from the current voice channel.
        """
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Leaving the voice channel!")

    # ── Events ──────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listens for incoming messages in the designated text channel and
        automatically queues them for TTS.

        Ignores messages from bots, commands (starting with '!'), and URLs.
        Truncates messages longer than 300 characters.
        """
        if message.author.bot:
            return

        if (
            config.TTS_TEXT_CHANNEL_ID
            and message.channel.id == config.TTS_TEXT_CHANNEL_ID
        ):
            text = message.content.strip()

            # Ignore empty messages, commands, or URLs
            if not text or text.startswith("!") or text.startswith("http"):
                return

            # Truncate overly long messages
            if len(text) > 300:
                text = text[:300] + "..."

            filename = f"tts_{message.id}.mp3"
            await tts_engine.tts_queue.put((text, filename))
            asyncio.create_task(tts_engine.process_queue(self.bot, message.guild))

    # ── Tasks ───────────────────────────────────────────────

    @tasks.loop(seconds=30)
    async def check_voice_channel(self):
        """
        A background task that runs every 30 seconds to check if the bot is alone
        in a voice channel. If no human users are present, it automatically disconnects
        to save resources.
        """
        for guild in self.bot.guilds:
            vc = guild.voice_client
            if vc and vc.is_connected():
                # Check if the bot is the only one in the channel
                if len([m for m in vc.channel.members if not m.bot]) == 0:
                    await vc.disconnect()
                    print(f"🔇 Disconnected from empty voice channel in: {guild.name}")

    @check_voice_channel.before_loop
    async def before_check(self):
        """
        Ensures the bot is fully ready and connected before starting the
        background voice channel check loop.
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    """
    Registers the TTSCog with the main Discord bot.
    """
    await bot.add_cog(TTSCog(bot))
