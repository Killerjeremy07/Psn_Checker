import discord
from discord import Option
from discord.ext import commands

from modules.custom_bot import Bot
import config
from modules.api.common import APIError
from modules.api.psn import PSNRequest

valid_regions = [
    "ar-AE",
    "ar-BH",
    "ar-KW",
    "ar-LB",
    "ar-OM",
    "ar-QA",
    "ar-SA",
    "ch-HK",
    "ch-TW",
    "cs-CZ",
    "da-DK",
    "de-AT",
    "de-CH",
    "de-DE",
    "de-LU",
    "el-GR",
    "en-AE",
    "en-AR",
    "en-AU",
    "en-BG",
    "en-BH",
    "en-BR",
    "en-CA",
    "en-CL",
    "en-CO",
    "en-CR",
    "en-CY",
    "en-CZ",
    "en-DK",
    "en-EC",
    "en-ES",
    "en-FI",
    "en-GB",
    "en-GR",
    "en-HK",
    "en-HR",
    "en-HU",
    "en-ID",
    "en-IL",
    "en-IN",
    "en-IS",
    "en-KW",
    "en-LB",
    "en-MT",
    "en-MX",
    "en-MY",
    "en-NO",
    "en-NZ",
    "en-OM",
    "en-PA",
    "en-PE",
    "en-PL",
    "en-QA",
    "en-RO",
    "en-SA",
    "en-SE",
    "en-SG",
    "en-SI",
    "en-SK",
    "en-TH",
    "en-TR",
    "en-TW",
    "en-US",
    "en-ZA",
    "es-AR",
    "es-BR",
    "es-CL",
    "es-CO",
    "es-CR",
    "es-EC",
    "es-ES",
    "es-GT",
    "es-HN",
    "es-MX",
    "es-PA",
    "es-PE",
    "es-PY",
    "es-SV",
    "fi-FI",
    "fr-BE",
    "fr-CA",
    "fr-CH",
    "fr-FR",
    "fr-LU",
    "hu-HU",
    "id-ID",
    "it-CH",
    "it-IT",
    "ja-JP",
    "ko-KR",
    "nl-BE",
    "nl-NL",
    "no-NO",
    "pl-PL",
    "pt-BR",
    "pt-PT",
    "ro-RO",
    "ru-RU",
    "ru-UA",
    "sv-SE",
    "th-TH",
    "tr-TR",
    "vi-VN",
    "zh-CN",
    "zh-HK",
    "zh-TW",
]
valid_regionsShow = [valid_regions[i : i + 5] for i in range(0, len(valid_regions), 10)]
valid_regionsShow = "\n".join([", ".join(sublist) for sublist in valid_regionsShow])

token_desc = "pdccws_p cookie"
id_desc = "ID from psprices product_id command"
region_desc = "For example 'en-US', check 'playstation.com'"


class AvatarCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.invalid_region = discord.Embed(
            title=self.bot.get_text(None, "error_title"),
            description=(
                f"{self.bot.get_text(None, 'invalid_regions')}\n```{valid_regionsShow}```"
            ),
            color=discord.Color.red(),
        )
        self.invalid_region.set_footer(text=self.bot.get_text(None, "host2"))

    avatar_commands = discord.SlashCommandGroup("avatar")

    @avatar_commands.command(description="Checks an avatar for you.")
    async def check(
        self,
        ctx: discord.ApplicationContext,
        pdccws_p: Option(str, description=token_desc),  # type: ignore
        product_id: Option(str, description=id_desc),  # type: ignore
        region: Option(str, description=region_desc),  # type: ignore
    ) -> None:
        await ctx.respond(self.bot.get_text(ctx.author.id, "checking"), ephemeral=True)

        if region not in valid_regions:
            await ctx.respond(embed=self.invalid_region, ephemeral=True)
            return

        request = PSNRequest(pdccws_p=pdccws_p, region=region, product_id=product_id)

        try:
            avatar_url = await config.Secrets.PSN_API.check(request)
        except APIError as e:
            embed_error = discord.Embed(
                title=self.bot.get_text(ctx.author.id, "error_title"),
                description=str(e),
                color=discord.Color.red(),
            )
            embed_error.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
            await ctx.respond(embed=embed_error, ephemeral=True)
            return

        embed_success = discord.Embed(
            title=self.bot.get_text(ctx.author.id, "success_title"),
            description=self.bot.get_text(ctx.author.id, "avatar_found"),
            color=discord.Color.blue(),
        )
        embed_success.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
        embed_success.set_image(url=avatar_url)
        await ctx.respond(embed=embed_success, ephemeral=True)

    @avatar_commands.command(description="Adds the avatar you input into your cart.")
    async def add(
        self,
        ctx: discord.ApplicationContext,
        pdccws_p: Option(str, description=token_desc),  # type: ignore
        product_id: Option(str, description=id_desc),  # type: ignore
        region: Option(str, description=region_desc),  # type: ignore
    ) -> None:
        await ctx.respond(self.bot.get_text(ctx.author.id, "adding"), ephemeral=True)

        if region not in valid_regions:
            await ctx.respond(embed=self.invalid_region, ephemeral=True)
            return

        request = PSNRequest(pdccws_p=pdccws_p, region=region, product_id=product_id)

        try:
            await config.Secrets.PSN_API.add_to_cart(request)
        except APIError as e:
            embed_error = discord.Embed(
                title=self.bot.get_text(ctx.author.id, "error_title"),
                description=str(e),
                color=discord.Color.red(),
            )
            embed_error.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
            await ctx.respond(embed=embed_error, ephemeral=True)
            return

        embed_success = discord.Embed(
            title=self.bot.get_text(ctx.author.id, "success_title"),
            description=f"{product_id} {self.bot.get_text(ctx.author.id, 'added_to_cart')}",
            color=discord.Color.blue(),
        )
        embed_success.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
        await ctx.respond(embed=embed_success, ephemeral=True)

    @avatar_commands.command(description="Removes the avatar you input from your cart.")
    async def remove(
        self,
        ctx: discord.ApplicationContext,
        pdccws_p: Option(str, description=token_desc),  # type: ignore
        product_id: Option(str, description=id_desc),  # type: ignore
        region: Option(str, description=region_desc),  # type: ignore
    ) -> None:

        await ctx.respond(self.bot.get_text(ctx.author.id, "removing"), ephemeral=True)

        if region not in valid_regions:
            await ctx.respond(embed=self.invalid_region, ephemeral=True)
            return

        request = PSNRequest(pdccws_p=pdccws_p, region=region, product_id=product_id)

        try:
            await config.Secrets.PSN_API.remove_from_cart(request)
        except APIError as e:
            embed_error = discord.Embed(
                title=self.bot.get_text(ctx.author.id, "error_title"),
                description=str(e),
                color=discord.Color.red(),
            )
            embed_error.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
            await ctx.respond(embed=embed_error, ephemeral=True)
            return

        embed_success = discord.Embed(
            title=self.bot.get_text(ctx.author.id, "success_title"),
            description=f"{product_id} {self.bot.get_text(ctx.author.id, 'removed_from_cart')}",
            color=discord.Color.blue(),
        )
        embed_success.set_footer(text=self.bot.get_text(ctx.author.id, "host2"))
        await ctx.respond(embed=embed_success, ephemeral=True)


def setup(bot):
    bot.add_cog(AvatarCog(bot))
