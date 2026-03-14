"""
Configuration module for the Echoify TTS bot.

This module is responsible for loading environment variables from a .env file
and initializing global settings that are shared across the bot's components.
"""

import os
from dotenv import load_dotenv

# Load environment variables from the .env file into the system
load_dotenv()

# ==========================================
# Static Configuration (API Keys & Tokens)
# ==========================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")

# ==========================================
# Runtime Status (Dynamic Configuration)
# ==========================================
# These variables store the target channel IDs for TTS operations.
# They are initialized as None and updated dynamically via bot commands
# (e.g., !settextch, !setvoicech) while the bot is running.
TTS_TEXT_CHANNEL_ID = None
TTS_VOICE_CHANNEL_ID = None
