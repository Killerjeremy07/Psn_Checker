import discord
from discord.ext import commands
from modules.custom_bot import Bot
import json
import config


class Diverse(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @discord.slash_command(
        name="ping",
        description="See the ping of the bot"
    )
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"My ping is: {int(self.bot.latency*1000)}ms")

    @discord.slash_command(
        name="toggle-ban",
        description="Block/Unblock an user from using commands."
    )
    @commands.is_owner()
    async def toggle_ban(self, ctx: discord.ApplicationContext, member: discord.User, private: bool = False):
        await ctx.defer(ephemeral=private)

        if member.id == self.bot.owner_id:
            raise discord.ApplicationCommandError("You cannot do that with the owner of the bot.")
        
        if str(member.id) in self.bot.banned_user:
            self.bot.banned_user.remove(str(member.id))
            with open(config.BANNED_USERS, "w") as f:
                json.dump(self.bot.banned_user, f)
            
            await ctx.respond(member.name + " has been unbanned")
            return
        
        self.bot.banned_user.append(str(member.id))
        with open(config.BANNED_USERS, "w") as f:
            json.dump(self.bot.banned_user, f)
        
        await ctx.respond("You have successfully banned " + member.name)
        print(f"{member.global_name} ({member.id}) was sucessfully yeeted out of existence.")

    @commands.slash_command(
        name="refresh-psn-token",
        description="Changes the NPSSO token to a new one."
    )
    @commands.is_owner()
    async def refresh_token(self, ctx: discord.ApplicationContext):
        self.bot.psnawp._request_builder.authenticator.obtain_fresh_access_token()
        await ctx.respond("Sucessfully generated a new token!")
        print("Generated a new NPPSO token.")


def setup(bot):
    bot.add_cog(Diverse(bot))

