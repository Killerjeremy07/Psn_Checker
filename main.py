import os
import discord

import config
from modules.custom_bot import Bot


bot = Bot(psn_api_token=config.Secrets.PSN_API,  command_prefix="/")

@bot.event
async def on_ready():
    print("Ready!")
    bot.presence_updater.start()

for file in os.listdir("cogs"):
    if not file.endswith(".py"): continue
    complete_file_module = f"cogs.{file.removesuffix('.py')}"
    bot.load_extension(complete_file_module)

bot.run(config.Secrets.BOT_TOKEN)
