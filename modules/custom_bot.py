import json
import os

import discord
from discord.ext import commands, tasks
from psnawp_api import PSNAWP
import config
from itertools import cycle


class Bot(commands.Bot):
    def __init__(self, psn_api_token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.psnawp = PSNAWP(psn_api_token)
        self.presence_iter = cycle(config.RICH_PRESENCES.keys())
        
        if not os.path.exists(config.CACHE_USERS):
            with open(config.CACHE_USERS, "w") as json_file:
                json_file.write(json.dumps({}))
        
        with open(config.CACHE_USERS, "r") as json_file:
            self.users_json = json.load(json_file)

        with open(config.BANNED_USERS, "r") as json_file:
            self.banned_user = json.load(json_file)

        self.before_invoke(self.__before_commands)
    
    async def __before_commands(self, ctx: discord.ApplicationContext):
        print(f"{ctx.author.name} used {ctx.command.name}")
        
        if str(ctx.author.id) in self.banned_user:
            raise discord.ApplicationCommandError("You are currently banned, you have not access to the bot")
        
        if config.CORRECT_CHANNELS == []: return
        if ctx.channel.id not in config.CORRECT_CHANNELS:
            raise discord.ApplicationCommandError("Incorect channel.")
    
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        error_message = f"{ctx.author.mention}, An error occurred: `{error}`"

        try:
            await ctx.respond(error_message)
        except Exception:
            await ctx.send(error_message)
        
        raise error
    
    @tasks.loop(minutes=config.DELAY)
    async def presence_updater(self):
        current_presence = next(self.presence_iter)
        current_type = config.RICH_PRESENCES[current_presence]
        
        await self.change_presence(activity=discord.Activity(type=current_type, name=current_presence))