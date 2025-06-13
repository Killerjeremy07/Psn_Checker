import discord

# Set the playing status of the bot, followed by the activity type
RICH_PRESENCES = {
    "Over your accounts!": discord.ActivityType.watching,
    "By KillerJeremy07": discord.ActivityType.playing,
}

# Delay in minutes between each presence/status
DELAY = 5

# Set the channels ID in which the commands can be used (leave empty for everywhere)
CORRECT_CHANNELS = []

# File in which to store the user who used the command and the amount of time they did it
CACHE_USERS = "./cache/users.json"

# File in which to store the banned users who cannot execute commands
BANNED_USERS = "./cache/bans.json"

# File in which to store the different languages settings for each users
USER_LANGUAGES = "./cache/langs.json"

# IN ORDER: BRONZE, SILVER, GOLD, PLATINIUM
TROPHY_TEXTS = ["🥉 Bronze", "🥈 Silver", "🥇 Gold", "💎 Platinium"]

# This is the icon displayed before the title of the embed
PSN_ACCOUNT_ICON_URL = "https://lachaisesirv.sirv.com/icons8-playstation-144%20(1).png"

# The amount of games to display in the user-profile command
MAX_GAMES_DISPLAY = 1

# In the game-search command :
MAX_DESC_LENGTH = 360
MAX_TAGS = 8
MAX_MEDIAS_URL = 4

# In the recent-games command :
MAX_RECENT_DISPLAY = 8
MAX_MEDIA_PER_GAMES = 3
MAX_SHORT_DESC_LENGTH = 200

# In the bot-info command :
ALLOW_SERVER_INVITES = True


# API KEYS
class Secrets:
    PSN_API = ""
    BOT_TOKEN = (
        ""
    )
    IGDB = {
        "client_id": "",
        "client_secret": "",
    }
