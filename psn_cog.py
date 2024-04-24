import base64

import discord
from discord import app_commands
from discord.ext import commands
from psnawp_api.core.psnawp_exceptions import PSNAWPForbidden
import config
from psnawp_api.models.trophies.trophy_summary import TrophySummary
from custom_bot import Bot


def format_trophies(trophy_infos: TrophySummary):
    trophy_amounts = {
        config.TROPHY_TEXTS[0]: trophy_infos.earned_trophies.bronze,
        config.TROPHY_TEXTS[1]: trophy_infos.earned_trophies.silver,
        config.TROPHY_TEXTS[2]: trophy_infos.earned_trophies.gold,
        config.TROPHY_TEXTS[3]: trophy_infos.earned_trophies.platinum
    }

    trophy_details = [
        f"Trophy level: {trophy_infos.trophy_level}",
        f"Total trophies: {sum(trophy_amounts.values())}"
    ]

    for trophy_name, trophy_amount in trophy_amounts.items():
        trophy_details.append(f"{trophy_name}: {trophy_amount}")

    return trophy_details


class PSNCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
    
    @app_commands.command(
        name="account_info",
        description="Display information concerning the given PSN account"
    )
    @app_commands.describe(online_id="Your online ID (A.K.A PSN username")
    @app_commands.describe(private="Should the message revealing your account details be private or public")
    async def account_info(self, interaction: discord.Interaction, online_id: str, private: bool = False):
        interaction.response: discord.InteractionResponse
        await interaction.response.defer(ephemeral=private)

        user = self.bot.psnawp.user(online_id=online_id)

        embed = discord.Embed(
            title="account_info",
            color=config.EMBED_COLOR,
        )
        embed.set_author(
            name="PSN Account",
            icon_url="https://lachaisesirv.sirv.com/icons8-playstation-144%20(1).png"
        )
        embed.set_thumbnail(url=user.profile()["avatars"][1]["url"])

        fields = {
            "username": user.online_id,
            "account ID": user.account_id,
            "HEX (for Save Wizard)": f'{int(user.account_id):016x}',
            "Base64 (for Chiaki)":  base64.b64encode(int(user.account_id).to_bytes(8,'little')).decode('ascii'),
            "about me": user.profile()["aboutMe"],
            "language/location": ", ".join(user.profile()["languages"])
        }

        for name, value in fields.items():
            embed.add_field(name=name.upper(), value=value, inline=False)

        try:
            trophy_infos = user.trophy_summary()
            trophy_details = format_trophies(trophy_infos)
        except PSNAWPForbidden:
            trophy_details = ["❌ Private", "This user chose to hide his trophies"]

        embed.add_field(name="Trophies", value="\n".join(trophy_details))

        await interaction.followup.send(f"{interaction.user.mention}", embed=embed, ephemeral=private)

    @account_info.error
    async def account_info_error(self, interaction: discord.Interaction, error):
        await interaction.followup.send(f"an error occurred: `{error}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PSNCog(bot))
