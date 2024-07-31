import discord

# Set the playing status of the bot, followed by the activity type
RICH_PRESENCES = {
    "text that will show up by rich presence": discord.ActivityType.watching,
    "text that will show up by rich presence": discord.ActivityType.playing
}

# Delay in minutes between each presence/status
DELAY = 5

# Set the channels ID in which the commands can be used (leave empty for everywhere)
CORRECT_CHANNELS = []

# Folder in which to store the user who used the command and the amount of time they did it
CACHE_USERS = "./cache/users.json"

# Folder in which to store the banned users who cannot execute commands
BANNED_USERS = "./cache/bans.json"

# IN ORDER: BRONZE, SILVER, GOLD, PLATINIUM
TROPHY_TEXTS = [
    "🥉 Bronze",
    "🥈 Silver",
    "🥇 Gold",
    "💎 Platinum"
]

# This is the icon displayed before the title of the embed
PSN_ACCOUNT_ICON_URL = "https://lachaisesirv.sirv.com/icons8-playstation-144%20(1).png"

# The amount of games to display
MAX_GAMES_DISPLAY = 1

# The text displayed at the bottom of the embed
HOSTED_BY = "text at the bottom that displays after command is ran would be nic if you give me credit"

# API KEYS
class Secrets:
    PSN_API = ""
    BOT_TOKEN = ""
