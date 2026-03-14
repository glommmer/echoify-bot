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
# These dictionaries store the target channel IDs for TTS operations per server.
# They map a Discord Guild ID to a specific Channel ID.
# They are initialized as empty dictionaries and updated dynamically
# via bot commands (e.g., !settextch, !setvoicech) while the bot is running.
TTS_TEXT_CHANNEL_IDS = {}  # {guild_id: channel_id}
TTS_VOICE_CHANNEL_IDS = {}  # {guild_id: channel_id}
