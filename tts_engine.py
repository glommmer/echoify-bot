import asyncio
import discord
from elevenlabs.client import AsyncElevenLabs
import config

eleven = AsyncElevenLabs(api_key=config.ELEVENLABS_KEY)
tts_queue: asyncio.Queue = asyncio.Queue()
is_processing = False


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
    Processes the global TTS queue by generating audio files and playing them
    in the configured Discord voice channel.

    This function ensures that only one processing loop runs at a time using
    the `is_processing` flag. It handles connecting to the voice channel,
    playing the audio via FFmpeg, and cleaning up the generated files afterward.

    Args:
        bot (discord.Client): The Discord bot instance.
        guild (discord.Guild): The Discord guild (server) where the TTS will be played.
    """
    global is_processing
    if is_processing:
        return
    is_processing = True

    while not tts_queue.empty():
        text, filename = await tts_queue.get()

        voice_channel = bot.get_channel(config.TTS_VOICE_CHANNEL_ID)
        if not voice_channel:
            print("❌ Voice channel not set. Please set it using !setvoicech.")
            tts_queue.task_done()
            continue

        await tts_to_file(text, filename)

        try:
            vc = guild.voice_client
            if vc is None:
                vc = await voice_channel.connect(timeout=60.0, reconnect=True)
            elif vc.channel != voice_channel:
                await vc.move_to(voice_channel)
        except Exception as e:
            print(f"❌ Failed to connect to the voice channel: {e}")
            tts_queue.task_done()
            continue

        done_event = asyncio.Event()

        def after_play(error):
            bot.loop.call_soon_threadsafe(done_event.set)

        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.3)

        vc.play(discord.FFmpegPCMAudio(filename, executable="ffmpeg"), after=after_play)
        await done_event.wait()
        tts_queue.task_done()

        import os

        if os.path.exists(filename):
            os.remove(filename)

        vc = guild.voice_client
        if vc and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()

    is_processing = False
