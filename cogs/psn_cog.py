import base64
import io
import json
from datetime import datetime, timedelta
import re
from urllib.request import urlopen

import discord
import pycountry
from colorthief import ColorThief
from discord.ext import commands
from psnawp_api.core.psnawp_exceptions import PSNAWPForbidden, PSNAWPNotFound
from psnawp_api.models.trophies.trophy_summary import TrophySummary
from modules.custom_psnawp import Search

import config
from modules.custom_bot import Bot

class Field:
    def __init__(self, name, value, inline=True):
        """
        A class representing a field with a name, value, and inline display option.

        Args:
            name (str): The name of the field.
            value (str): The value of the field.
            inline (bool): A flag indicating if the field should be displayed inline.
        """
        self.name = name
        self.value = value
        self.inline = inline

class Trophy:
    def __init__(self, trophy_infos: TrophySummary):
        """
        A class representing a collection of trophies and their formatted display fields.

        Args:
            trophy_infos (TrophySummary): Summary information about the trophies.
        """
        self.trophy_infos = trophy_infos
        self.trophy_fields = self.format_trophies()

    def format_trophies(self):
        """
        Formats the trophy information into a list of Field instances.

        Returns:
            list: A list of Field instances representing the formatted trophy information.
        """
        trophy_amounts = {
            config.TROPHY_TEXTS[0]: self.trophy_infos.earned_trophies.bronze,
            config.TROPHY_TEXTS[1]: self.trophy_infos.earned_trophies.silver,
            config.TROPHY_TEXTS[2]: self.trophy_infos.earned_trophies.gold,
            config.TROPHY_TEXTS[3]: self.trophy_infos.earned_trophies.platinum
        }

        trophy_fields = []
        for trophy_name, trophy_amount in trophy_amounts.items():
            trophy_fields.append(Field(trophy_name, f"`{trophy_amount}`"))
        
        trophy_fields.extend([
            Field("Level | Progress", f"`{self.trophy_infos.trophy_level}` | `{self.trophy_infos.progress}%`"),
            Field("Total", f"`{sum(trophy_amounts.values())}`")
        ])

        return trophy_fields


class PSNCog(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @discord.slash_command(
        name="user-search",
        description="Display information concerning the given PSN account by using its name or its id"
    )
    @discord.option(name="private", description="Should the message revealing your account details be private or public")
    @discord.option(name="online_id", description="The GamerTag of the user.")
    @discord.option(name="account_id", description="The id of the user's account.")
    async def account_info(
        self,
        ctx: discord.ApplicationContext,
        online_id: str = None,
        account_id: str = None,
        private: bool = False
    ):
        await ctx.response.defer(ephemeral=private)  # This will prevent the command from timing out
        
        await self.register_usage(ctx.author.id)

        if account_id and online_id:
            raise ValueError("You cannot use both, please enter only an username or an id.")
        elif online_id is None and account_id is None:
            raise ValueError("You have to specify either an username or an account id.")
        elif online_id is not None:
            user = self.bot.psnawp.user(online_id=online_id)
            account_id = user.account_id
        elif account_id is not None:
            new_account_id: str | int = account_id
            try:
                base_64_account_id = base64.b64decode(new_account_id)
            except Exception:
                pass
            else:
                if len(base_64_account_id) == 8:
                    new_account_id = int.from_bytes(base_64_account_id,'little')
                else:
                    new_account_id = account_id
                
            try:
                user = self.bot.psnawp.user(account_id=new_account_id)
            except PSNAWPNotFound as e:
                new_account_id = account_id
                if len(new_account_id) != 16:
                    raise PSNAWPNotFound(f"Account ID {account_id} does not exist.")
                try:
                    new_account_id = str(int(new_account_id,16))
                except ValueError:
                    raise PSNAWPNotFound(f"Account ID {account_id} does not exist.")
                try:
                    user = self.bot.psnawp.user(account_id=new_account_id)
                except PSNAWPNotFound:
                    raise PSNAWPNotFound(f"Account ID {account_id} does not exist.")
            
        user_profile = user.profile()
        user_friendship = user.friendship()
        user_language: list[str] = user_profile["languages"]
        user_region = user_language[0].split("-")[1]
        user_avatar = user_profile["avatars"][1]["url"]

        try:
            user_avatar_primary_color = await self.get_url_primary_color(user_avatar)
        except Exception:  # Because colorthief doesn't have custom exceptions
            user_avatar_primary_color = discord.Color.blue()

        embed = discord.Embed(
            title="Infos",
            color=user_avatar_primary_color,
            timestamp=datetime.now()
        )

        embed.set_author(
            name="PSN Account",
            icon_url=config.PSN_ACCOUNT_ICON_URL
        )

        embed.set_thumbnail(url=user_avatar)

        image_url = f"https://image.api.playstation.com/profile/images/acct/prod/{account_id}/profile.JPEG?img="
        embed.set_image(url=image_url)

        embed.set_footer(text=f"You have executed this command {self.bot.users_json[str(ctx.author.id)]} time(s) | {config.HOSTED_BY}")

        fields = self.set_embed_fields(
            user,
            user_profile,
            user_friendship,
            user_region,
            user_avatar_primary_color
        )
    
        for field in fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)

        await ctx.followup.send(f"{ctx.user.mention}", embed=embed, ephemeral=private)
        print(f"Obtained data for: {user.online_id}")
    
    async def register_usage(self, user_id: int):
        """
        Add a new user to the usage count of the PSN command.

        Args:
            user_id (int): The ID of the user to register
        """
        user_id = str(user_id)

        if self.bot.users_json.get(user_id) is not None:
            self.bot.users_json[user_id] += 1
        else:
            self.bot.users_json[user_id] = 1
        
        with open(config.CACHE_USERS, "w") as json_file:
            json.dump(self.bot.users_json, json_file)
    
    async def get_url_primary_color(self, url: str) -> discord.Color:
        """
        Get the primary color of an image from an URL.
        """
        fd = urlopen(url)
        image = io.BytesIO(fd.read())

        color_thief = ColorThief(image)
        primary_color = color_thief.get_color(quality=15)

        return discord.Color.from_rgb(
            r=primary_color[0],
            g=primary_color[1],
            b=primary_color[2]
        )

    def set_embed_fields(self, user, user_profile, user_friendship, user_region, user_avatar_color) -> list[Field]:
        """
        Sets the embed fields with user information.

        Args:
            user (object): The user object containing user details.
            user_profile (dict): The user's profile information.
            user_friendship (dict): The user's friendship information.
            user_region (str): The user's region code.
            user_avatar_color (str): The user's avatar color.

        Returns:
            list[Field]: A list of Field objects with the user's information.
        """
        fields = [
            Field("Profile Primary Color", f"`{str(user_avatar_color).upper()}`", False),
            Field("Online ID", f"`{user.online_id}`"),
            Field("PS+", f"{'`Active`' if user_profile['isPlus'] else '`Unactive`'}"),
            Field("Officially verified", f"{'`Yes`' if user_profile['isOfficiallyVerified'] else '`No`'}"),
            Field("Account ID", f"`{user.account_id}`"),
            Field("HEX", f"`{int(user.account_id):016x}`"),
            Field("Base64", f"`{base64.b64encode(int(user.account_id).to_bytes(8, 'little')).decode('ascii')}`"),
            Field("Social", f"Friends: `{user_friendship['friendsCount'] if user_friendship['friendsCount'] >= 0 else '`Private`'}`", False)
        ]

        try:
            user_region_field = Field(f"Region | :flag_{user_region.lower()}:", f"`{user_region}` | `{pycountry.countries.get(alpha_2=user_region).name}`")
        except AttributeError:
            user_region_field = Field("Region | Unknown", "`Private`")

        fields.insert(
            2, 
            user_region_field
        )

        self.get_trophy_info(user, fields)
        self.get_user_presence(user, fields)
        self.get_titles(user, fields)

        fields.append(Field("About Me", f"```{user_profile['aboutMe'] if user_profile['aboutMe'] else 'Not visible'}```", False))

        if user.prev_online_id != user.online_id:
            fields.append(Field("Previous Online ID", f"`{user.prev_online_id}`"), False)
        
        return fields

    def get_trophy_info(self, user, fields):
        """
        Gets the user's trophy information and appends it to the fields.

        Args:
            user (object): The user object containing user details.
            fields (list[Field]): A list of Field objects to append the trophy information to.
        """
        try:
            trophy_infos = user.trophy_summary()
            trophies = Trophy(trophy_infos)
            fields.extend(trophies.trophy_fields)
        except PSNAWPForbidden:
            fields.append(Field("Trophies", "Private"))

    def get_user_presence(self, user, fields):
        """
        Gets the user's presence information and appends it to the fields.

        Args:
            user (object): The user object containing user details.
            fields (list[Field]): A list of Field objects to append the presence information to.
        """
        try:
            user_presence = user.get_presence()["basicPresence"]
            user_presence_info = user_presence["primaryPlatformInfo"]

            current_game = self.extract_current_game(user_presence)
            self.process_presence_status(user_presence, user_presence_info, current_game, fields)
        except PSNAWPForbidden:
            fields.append(Field("User presence", "`Private`"))

    def extract_current_game(self, user_presence):
        """
        Extracts the current game the user is playing from the presence information.

        Args:
            user_presence (dict): The user's presence information.

        Returns:
            str: The name of the current game the user is playing, or None if not playing any game.
        """
        current_game = user_presence.get('gameTitleInfoList')
        if current_game:
            return current_game[0]['titleName']
        return None

    def process_presence_status(self, user_presence, user_presence_info, current_game, fields):
        """
        Processes the user's presence status and appends it to the fields.

        Args:
            user_presence_info (dict): The user's primary platform presence information.
            current_game (str): The name of the current game the user is playing, or None if not playing any game.
            fields (list[Field]): A list of Field objects to append the presence status information to.
        """
        if user_presence_info["onlineStatus"] == "offline":
            self.process_offline_status(user_presence_info, fields)
        else:
            self.process_online_status(user_presence, user_presence_info, current_game, fields)

    def process_offline_status(self, user_presence_info, fields):
        """
        Processes the user's offline status and appends it to the fields.

        Args:
            user_presence_info (dict): The user's primary platform presence information.
            fields (list[Field]): A list of Field objects to append the offline status information to.
        """
        try:
            last_online = datetime.strptime(user_presence_info['lastOnlineDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            presence_data = f"<t:{int(last_online.timestamp())}:R> {user_presence_info['platform'].upper()}"
        except KeyError:
            presence_data = "This user doesn't own a console"
        fields.append(Field("Last seen", presence_data, False))

    def process_online_status(self, user_presence, user_presence_info, current_game, fields):
        """
        Processes the user's online status and appends it to the fields.

        Args:
            user_presence_info (dict): The user's primary platform presence information.
            current_game (str): The name of the current game the user is playing, or None if not playing any game.
            fields (list[Field]): A list of Field objects to append the online status information to.
        """
        presence_data = f"`Currently online` {user_presence_info['platform'].upper()}"
        fields.append(Field("Last seen", presence_data, False))

        availability: str = user_presence["availability"]
        availability = availability.replace("unavailable", "Unavailable")
        availability = availability.replace("availableToPlay", "Ready to play!")

        fields.append(Field("Availability", availability, False))

        if current_game:
            fields.append(Field("Playing", f"`{current_game}`", False))

    def get_titles(self, user, fields):
        """
        Gets the user's recent and favorite titles and appends them to the fields.

        Args:
            user (object): The user object containing user details.
            fields (list[Field]): A list of Field objects to append the titles to.
        """
        try:
            all_titles = user.title_stats()

            recent_titles = []
            for i, title in enumerate(all_titles):
                if i == config.MAX_GAMES_DISPLAY: break

                recent_titles.append(
                    f"{title.name}\n" \
                    f"Launched <t:{int(title.last_played_date_time.timestamp())}:R>\n" \
                    f"Played {title.play_count} times\n" \
                    f"Played for {title.play_duration}"
                )
            
            fields.append(Field(
                "Recent games",
                "\n\n".join(recent_titles)
            ))
            
            total_playtime = timedelta(seconds=0)
            all_favorite_titles = []
            for title in all_titles:
                total_playtime += title.play_duration
                all_favorite_titles.append(title)
            
            total_games = len(all_favorite_titles)
            all_favorite_titles = sorted(all_favorite_titles, key=lambda x: x.play_duration, reverse=True)
            
            favorite_titles = []
            for i, title in enumerate(all_favorite_titles):
                if i == config.MAX_GAMES_DISPLAY: break
                
                favorite_titles.append(
                    f"{title.name}\n" \
                    f"Launched <t:{int(title.last_played_date_time.timestamp())}:R>\n" \
                    f"Played {title.play_count} times\n" \
                    f"Played for {title.play_duration}"
                )

            fields.append(Field(
                "Favorite games",
                "\n\n".join(favorite_titles)
            ))

            fields.append(Field(
                "Total play time",
                f"`{total_playtime}`",
                inline=False
            ))

            fields.append(Field(
                "Total games",
                f"`{total_games}`"
            ))
        except PSNAWPForbidden:
            fields.append(Field("Games", "`Private`"))
    
    @discord.slash_command(
        name="game-search",
        description="Allows you to look up a game on the Playstation Store."
    )
    @discord.option(name="game_name", description="The name of the game to look for.")
    @discord.option(name="search_index", description="The result index to return (depends on search results amounts).")
    async def search_game(self, ctx: discord.ApplicationContext, game_name: str, search_index: int = 0):
        await ctx.defer()

        searcher = Search(self.bot.psnawp._request_builder)
        search_results = searcher.universal_search(game_name, "MobileUniversalSearchGame")
        first_game_details = search_results[search_index]["result"]

        embed = discord.Embed(title=first_game_details["name"], timestamp=datetime.now())

        for media in first_game_details["media"]:
            media_url = media["url"]

            match media["role"]:
                case "GAMEHUB_COVER_ART":
                    embed.set_image(url=media_url)
                case "LOGO":
                    embed.set_thumbnail(url=media_url)
                    try:
                        embed.colour =  await self.get_url_primary_color(media_url)
                    except Exception:
                        embed.colour = discord.Color.blue()
        
        platforms = ", ".join(first_game_details["platforms"])
        embed.add_field(name="Platforms", value=platforms)

        embed.add_field(name="Store Display Classification", value=first_game_details["defaultProduct"]["localizedStoreDisplayClassification"])
    
        price = first_game_details["price"]
        embed.add_field(name="Price", value=price)
        embed.set_footer(text=config.HOSTED_BY)
        
        await ctx.respond(ctx.author.mention, embed=embed)
        print(f"Obtained data for {game_name}: {first_game_details['name']}")

def setup(bot):
    bot.add_cog(PSNCog(bot))