import asyncio

import discord
from custom_bot import Bot

import config

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.watching, name="Your Ps Account")
bot = Bot(psn_api_token=config.Secrets.PSN_API, intents=intents, command_prefix="/", activity=activity)

# You can add a custom command here (see also inside the psn_cog file)
@bot.tree.command(name='ping', description='test if bot is responding!')
async def ping(interaction):
    await interaction.response.send_message(f'Pong! ||{round(bot.latency * 1000)}ms||') 

@bot.event
async def on_ready():
    # Set the activity once the bot is ready
    await bot.change_presence(activity=activity)
    await bot.tree.sync()
    print("Ready!")

async def main():
    # Load the psn_cog extension
    await bot.load_extension("psn_cog")


asyncio.run(main())
bot.run(config.Secrets.BOT_TOKEN)