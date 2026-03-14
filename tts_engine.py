import os
import asyncio
import discord
from collections import defaultdict
from elevenlabs.client import AsyncElevenLabs
import config

eleven = AsyncElevenLabs(api_key=config.ELEVENLABS_KEY)

# A dictionary mapping each guild ID to its own distinct TTS queue.
tts_queues: dict = defaultdict(asyncio.Queue)  # {guild_id: Queue}

# A dictionary tracking whether a TTS processing loop is currently active for a specific guild ID.
is_processing: dict = defaultdict(bool)  # {guild_id: bool}


async def tts_to_file(text: str, filename: str) -> str:
    """
    Asynchronously converts text to speech using the ElevenLabs API and saves it to a file.

    Args:
        text (str): The text content to be converted into speech.
        filename (str): The target file path/name to save the generated audio (.mp3).

    Returns:
        str: The filename where the audio was saved.
    """
    with open(filename, "wb") as f:
        async for chunk in eleven.text_to_speech.convert(
            voice_id=config.VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        ):
            if chunk:
                f.write(chunk)
    return filename


async def process_queue(bot: discord.Client, guild: discord.Guild):
    """
    Processes the server-specific (guild) TTS queue by generating audio files
    and playing them in the configured Discord voice channel.

    This function ensures that only one processing loop runs at a time per server
    using the `is_processing` dictionary flag. It handles connecting to the voice channel,
    playing the audio via FFmpeg, and cleaning up the generated files afterward.

    Args:
        bot (discord.Client): The Discord bot instance.
        guild (discord.Guild): The Discord guild (server) where the TTS will be played.
    """
    guild_id = guild.id

    if is_processing[guild_id]:
        return
    is_processing[guild_id] = True

    queue = tts_queues[guild_id]

    while not queue.empty():
        text, filename = await queue.get()

        voice_channel_id = config.TTS_VOICE_CHANNEL_IDS.get(guild.id)
        voice_channel = bot.get_channel(voice_channel_id)
        if not voice_channel:
            print(f"❌ [{guild.name}] Voice channel not set.")
            queue.task_done()
            continue

        await tts_to_file(text, filename)

        try:
            vc = guild.voice_client
            if vc is None:
                vc = await voice_channel.connect(timeout=60.0, reconnect=True)
            elif vc.channel != voice_channel:
                await vc.move_to(voice_channel)
        except Exception as e:
            print(f"❌ [{guild.name}] Failed to connect: {e}")
            queue.task_done()
            continue

        done_event = asyncio.Event()

        def after_play(error):
            bot.loop.call_soon_threadsafe(done_event.set)

        if vc.is_playing():
            vc.stop()
        await asyncio.sleep(0.3)

        vc.play(discord.FFmpegPCMAudio(filename, executable="ffmpeg"), after=after_play)
        await done_event.wait()
        queue.task_done()

        if os.path.exists(filename):
            os.remove(filename)

        vc = guild.voice_client
        if vc and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()

    is_processing[guild_id] = False
