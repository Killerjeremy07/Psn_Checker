import base64
import io
import json
from datetime import datetime, timedelta
from urllib.request import urlopen

import discord
import pycountry
from colorthief import ColorThief
from discord.ext import commands
from psnawp_api.core.psnawp_exceptions import PSNAWPForbidden
from psnawp_api.models.trophies.trophy_summary import TrophySummary

import config
from modules.custom_bot import Bot
from modules.date_formatter import translate_date


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
    def __init__(self, trophy_infos: TrophySummary, user_id: int, bot):
        """
        A class representing a collection of trophies and their formatted display fields.

        Args:
            trophy_infos (TrophySummary): Summary information about the trophies.
            user_id (int): The user's ID for language preference.
            bot (object): The bot instance to access dynamic text.
        """
        self.trophy_infos = trophy_infos
        self.user_id = user_id
        self.bot = bot
        self.trophy_fields = self.format_trophies()

    def format_trophies(self):
        """
        Formats the trophy information into a list of Field instances.

        Returns:
            list: A list of Field instances representing the formatted trophy information.
        """
        trophy_amounts = {
            self.bot.get_text(
                self.user_id, "bronze"
            ): self.trophy_infos.earned_trophies.bronze,
            self.bot.get_text(
                self.user_id, "silver"
            ): self.trophy_infos.earned_trophies.silver,
            self.bot.get_text(
                self.user_id, "gold"
            ): self.trophy_infos.earned_trophies.gold,
            self.bot.get_text(
                self.user_id, "platinum"
            ): self.trophy_infos.earned_trophies.platinum,
        }

        trophy_fields = []
        for trophy_name, trophy_amount in trophy_amounts.items():
            trophy_fields.append(Field(trophy_name, f"`{trophy_amount}`"))

        trophy_fields.extend(
            [
                Field(
                    self.bot.get_text(self.user_id, "level_progress"),
                    f"`{self.trophy_infos.trophy_level}` | `{self.trophy_infos.progress}%`",
                ),
                Field(
                    self.bot.get_text(self.user_id, "total"),
                    f"`{sum(trophy_amounts.values())}`",
                ),
            ]
        )

        return trophy_fields


class PSNCog(commands.Cog):

    def __init__(self, bot):
        self.bot: Bot = bot

    @discord.slash_command(
        name="user-search",
        description="Display information concerning the given PSN account by using its name or id",
    )
    @discord.option(
        name="private",
        description="Should the message revealing your account details be private or public",
    )
    @discord.option(name="online_id", description="The GamerTag of the user.")
    @discord.option(name="account_id", description="The id of the user's account.")
    async def account_info(
        self,
        ctx: discord.ApplicationContext,
        online_id: str = None,
        account_id: str = None,
        private: bool = False,
    ):
        await ctx.response.defer(
            ephemeral=private
        )  # This will prevent the command from timing out

        await self.register_usage(ctx.author.id)

        if account_id and online_id:
            raise ValueError(
                self.bot.get_text(ctx.author.id, "psn_user_argument_conflict")
            )
        elif online_id is None and account_id is None:
            raise ValueError(self.bot.get_text(ctx.author.id, "psn_missing_argument"))
        elif online_id is not None:
            user = self.bot.psnawp.user(online_id=online_id)
            account_id = user.account_id
        elif account_id is not None:
            user = self.bot.psnawp.user(account_id=account_id)

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
            title=self.bot.get_text(ctx.author.id, "psn_user_title"),
            color=user_avatar_primary_color,
            timestamp=datetime.now(),
        )

        embed.set_author(
            name=self.bot.get_text(ctx.author.id, "psn_user_account"),
            icon_url=config.PSN_ACCOUNT_ICON_URL,
        )

        embed.set_thumbnail(url=user_avatar)

        image_url = f"""
        https://image.api.playstation.com/profile/images/acct/prod/{account_id}/profile.JPEG?img=
        """
        embed.set_image(url=image_url)

        footer_text = self.bot.get_text(
            ctx.author.id,
            "psn_user_viewcount",
            exec_amount=self.bot.users_json[str(ctx.author.id)],
        )
        embed.set_footer(
            text=f"{footer_text} | {self.bot.get_text(ctx.author.id, 'host')}"
        )

        fields = self.set_embed_fields(
            ctx.author,
            user,
            user_profile,
            user_friendship,
            user_region,
            user_avatar_primary_color,
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
        Get the primary color of an image from a URL.
        """
        fd = urlopen(url)
        image = io.BytesIO(fd.read())

        color_thief = ColorThief(image)
        primary_color = color_thief.get_color(quality=15)

        return discord.Color.from_rgb(
            r=primary_color[0], g=primary_color[1], b=primary_color[2]
        )

    def set_embed_fields(
        self,
        author,
        user,
        user_profile,
        user_friendship,
        user_region,
        user_avatar_color,
    ) -> list[Field]:
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
        user_id = author.id
        fields = [
            Field(
                self.bot.get_text(user_id, "profile_primary_color"),
                f"`{str(user_avatar_color).upper()}`",
                False,
            ),
            Field(self.bot.get_text(user_id, "online_id"), f"`{user.online_id}`"),
            Field(
                self.bot.get_text(user_id, "ps_plus"),
                f"{'`✅`' if user_profile['isPlus'] else '`❌`'}",
            ),
            Field(
                self.bot.get_text(user_id, "officially_verified"),
                f"{'`✅`' if user_profile['isOfficiallyVerified'] else '`❌`'}",
            ),
            Field(self.bot.get_text(user_id, "account_id"), f"`{user.account_id}`"),
            Field(
                self.bot.get_text(user_id, "hex"),
                f"`{(f'{int(user.account_id):016x}'.upper())}`",
            ),
            Field(
                self.bot.get_text(user_id, "base64"),
                f"`{base64.b64encode(int(user.account_id).to_bytes(8, 'little')).decode('ascii').upper()}`",
            ),
            Field(
                self.bot.get_text(user_id, "social"),
                f"{self.bot.get_text(user_id, 'friends')}: `{user_friendship['friendsCount'] if user_friendship['friendsCount'] >= 0 else self.bot.get_text(user_id, 'private')}`",
                False,
            ),
        ]

        try:
            user_region_field = Field(
                self.bot.get_text(
                    user_id, "region_flag", flag=f":flag_{user_region.lower()}:"
                ),
                f"`{user_region}` | `{pycountry.countries.get(alpha_2=user_region).name}`",
            )
        except AttributeError:
            user_region_field = Field(
                self.bot.get_text(user_id, "region_unknown"),
                f"`{self.bot.get_text(user_id, 'private')}`",
            )

        fields.insert(2, user_region_field)

        self.get_trophy_info(author, user, fields)
        self.get_user_presence(author, user, fields)
        self.get_titles(author, user, fields)

        fields.append(
            Field(
                self.bot.get_text(user_id, "about_me"),
                f"```{user_profile['aboutMe'] if user_profile['aboutMe'] else self.bot.get_text(user_id, 'not_visible')}```",
                False,
            )
        )

        fields.append(
            Field(
                self.bot.get_text(user_id, "previous_online_id"),
                f"`{user.prev_online_id}`",
                False,
            ),
        )

        return fields

    def get_trophy_info(self, author, user, fields):
        """
        Gets the user's trophy information and appends it to the fields.

        Args:
            user (object): The user object containing user details.
            fields (list[Field]): A list of Field objects to append the trophy information to.
        """
        user_id = author.id
        try:
            trophy_infos = user.trophy_summary()
            trophies = Trophy(trophy_infos, user_id, self.bot)
            fields.extend(trophies.trophy_fields)
        except PSNAWPForbidden:
            fields.append(
                Field(
                    self.bot.get_text(user_id, "trophies"),
                    f"`{self.bot.get_text(user_id, 'private')}`",
                )
            )

    def get_user_presence(self, author, user, fields):
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
            self.process_presence_status(
                author, user_presence, user_presence_info, current_game, fields
            )
        except PSNAWPForbidden:
            fields.append(
                Field(
                    self.bot.get_text(author.id, "user_presence"),
                    f"`{self.bot.get_text(author.id, 'private')}`",
                )
            )

    def extract_current_game(self, user_presence):
        """
        Extracts the current game the user is playing from the presence information.

        Args:
            user_presence (dict): The user's presence information.

        Returns:
            str: The name of the current game the user is playing, or None if not playing any game.
        """
        current_game = user_presence.get("gameTitleInfoList")
        if current_game:
            return current_game[0]["titleName"]
        return None

    def process_presence_status(
        self, author, user_presence, user_presence_info, current_game, fields
    ):
        """
        Processes the user's presence status and appends it to the fields.

        Args:
            user_presence_info (dict): The user's primary platform presence information.
            current_game (str): The name of the current game the user is playing, or None if not playing any game.
            fields (list[Field]): A list of Field objects to append the presence status information to.
        """
        if user_presence_info["onlineStatus"] == "offline":
            self.process_offline_status(author, user_presence_info, fields)
        else:
            self.process_online_status(
                author, user_presence, user_presence_info, current_game, fields
            )

    def process_offline_status(self, author, user_presence_info, fields):
        """
        Processes the user's offline status and appends it to the fields.

        Args:
            author (discord.User): The author (user) invoking the command.
            user_presence_info (dict): The user's primary platform presence information.
            fields (list[Field]): A list of Field objects to append the offline status information to.
        """
        try:
            last_online = datetime.strptime(
                user_presence_info["lastOnlineDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            presence_data = f"<t:{int(last_online.timestamp())}:R> {user_presence_info['platform'].upper()}"
        except KeyError:
            presence_data = self.bot.get_text(author.id, "console_absent")
        fields.append(
            Field(self.bot.get_text(author.id, "last_seen"), presence_data, False)
        )

    def process_online_status(
        self, author, user_presence, user_presence_info, current_game, fields
    ):
        """
        Processes the user's online status and appends it to the fields.

        Args:
            author (discord.User): The author (user) invoking the command.
            user_presence_info (dict): The user's primary platform presence information.
            current_game (str): The name of the current game the user is playing, or None if not playing any game.
            fields (list[Field]): A list of Field objects to append the online status information to.
        """
        presence_data = f"`{self.bot.get_text(author.id, 'currently_online')}` {user_presence_info['platform'].upper()}"
        fields.append(
            Field(self.bot.get_text(author.id, "last_seen"), presence_data, False)
        )

        availability: str = user_presence["availability"]
        availability = availability.replace(
            "unavailable", self.bot.get_text(author.id, "unavailable")
        )
        availability = availability.replace(
            "availableToPlay", self.bot.get_text(author.id, "ready_to_play")
        )

        fields.append(
            Field(self.bot.get_text(author.id, "availability"), availability, False)
        )

        if current_game:
            fields.append(
                Field(
                    self.bot.get_text(author.id, "playing"), f"`{current_game}`", False
                )
            )

    def get_titles(self, author, user, fields):
        """
        Gets the user's recent and favorite titles and appends them to the fields.

        Args:
            user (object): The user object containing user details.
            fields (list[Field]): A list of Field objects to append the titles to.
        """
        user_id = author.id
        try:
            all_titles = user.title_stats()

            # Process recent games
            recent_titles = []
            for i, title in enumerate(all_titles):
                if i == config.MAX_GAMES_DISPLAY:
                    break

                launched_text = self.bot.get_text(
                    user_id,
                    "launched",
                    timestamp=int(title.last_played_date_time.timestamp()),
                )
                played_times_text = self.bot.get_text(
                    user_id, "played_times", play_count=title.play_count
                )
                played_duration_text = self.bot.get_text(
                    user_id,
                    "played_duration",
                    play_duration=translate_date(
                        str(title.play_duration), user_id, self.bot
                    ),
                )

                recent_titles.append(
                    f"{title.name}\n"
                    f"{launched_text}\n"
                    f"{played_times_text}\n"
                    f"{played_duration_text}"
                )

            fields.append(
                Field(
                    self.bot.get_text(user_id, "recent_games"),
                    "\n\n".join(recent_titles),
                )
            )

            total_playtime = timedelta(seconds=0)
            all_favorite_titles = []
            for title in all_titles:
                total_playtime += title.play_duration
                all_favorite_titles.append(title)

            total_games = len(all_favorite_titles)
            all_favorite_titles = sorted(
                all_favorite_titles, key=lambda x: x.play_duration, reverse=True
            )

            favorite_titles = []
            for i, title in enumerate(all_favorite_titles):
                if i == config.MAX_GAMES_DISPLAY:
                    break

                launched_text = self.bot.get_text(
                    user_id,
                    "launched",
                    timestamp=int(title.last_played_date_time.timestamp()),
                )
                played_times_text = self.bot.get_text(
                    user_id, "played_times", play_count=title.play_count
                )
                played_duration_text = self.bot.get_text(
                    user_id,
                    "played_duration",
                    play_duration=translate_date(
                        str(title.play_duration), user_id, self.bot
                    ),
                )

                favorite_titles.append(
                    f"{title.name}\n"
                    f"{launched_text}\n"
                    f"{played_times_text}\n"
                    f"{played_duration_text}"
                )

            fields.append(
                Field(
                    self.bot.get_text(user_id, "favorite_games"),
                    "\n\n".join(favorite_titles),
                )
            )

            fields.append(
                Field(
                    self.bot.get_text(user_id, "total_play_time"),
                    f"`{translate_date(str(total_playtime), user_id, self.bot)}`",
                    inline=False,
                )
            )

            fields.append(
                Field(self.bot.get_text(user_id, "total_games"), f"`{total_games}`")
            )
        except PSNAWPForbidden:
            fields.append(
                Field(
                    self.bot.get_text(user_id, "games"),
                    f"`{self.bot.get_text(user_id, 'private')}`",
                )
            )

    @discord.slash_command(
        name="game-search",
        description="Allows you to look up a game on the Playstation Store.",
    )
    @discord.option(name="game_name", description="The name of the game to look for.")
    @discord.option(
        name="search_index",
        description="The result index to return (depends on search results amounts).",
    )
    async def search_game(
        self,
        ctx: discord.ApplicationContext,
        game_name: str,
        search_index: int = 0,
    ):
        await ctx.defer()

        game_search = self.bot.igdb.search_game(game_name, limit=100)

        if game_search == []:
            await ctx.respond(self.bot.get_text(ctx.author.id, "no_games"))
            return

        if search_index >= len(game_search):
            search_index = len(game_search) - 1
        game = game_search[search_index]

        embed = discord.Embed(
            title=f"{game.name} ({game.release_date.strftime('%Y-%m-%d') if game.release_date else 'TBA'})",
            description=f"{game.description[: config.MAX_DESC_LENGTH] if game.description else self.bot.get_text(ctx.author.id, 'no_desc')}...[({self.bot.get_text(ctx.author.id, 'read_more')})]({game.url})",
            timestamp=datetime.now(),
        )

        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "publishers"),
            value=", ".join(game.publishers),
            inline=False,
        )
        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "platforms"),
            value=", ".join(game.platforms),
            inline=False,
        )
        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "genres"),
            value=", ".join([genre for genre in game.genres[: config.MAX_TAGS]]),
            inline=False,
        )
        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "keywords"),
            value=", ".join([keyword for keyword in game.keywords[: config.MAX_TAGS]]),
            inline=False,
        )
        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "media"),
            value="\n".join(
                [
                    f"{name}: {' | '.join([f'[{name} n°{i}]({url})' for i, url in enumerate(url_list[: config.MAX_MEDIAS_URL])])}"
                    for name, url_list in game.medias.items()
                ]
            ),
            inline=False,
        )
        embed.add_field(
            name=self.bot.get_text(ctx.author.id, "similar_games"),
            value=", ".join(game.similar_games[: config.MAX_TAGS]),
            inline=False,
        )
        embed.set_thumbnail(url=game.cover_url)
        if game.medias["artworks"]:
            embed.set_image(url=game.medias["artworks"][0])

        embed.set_footer(
            text=f"{self.bot.get_text(ctx.author.id, 'score')}: {int(game.rating) if game.rating else self.bot.get_text(ctx.author.id, 'no_ratings')} | {self.bot.get_text(ctx.author.id, 'showing_result', current=search_index+1, total=len(game_search))} | {self.bot.get_text(ctx.author.id, 'host')}"
        )

        await ctx.respond(ctx.author.mention, embed=embed)
        print(f"Obtained data for {game_name}")

    @discord.slash_command(
        name="list-recent-games",
        description="List all of the recently played games by the user.",
    )
    async def list_recent_games(self, ctx: discord.ApplicationContext, online_id: str):
        await ctx.defer()
        user = self.bot.psnawp.user(online_id=online_id)

        recent_games_iterator = user.title_stats()
        embed = discord.Embed(
            title=f"{self.bot.get_text(ctx.author.id, 'recent_games')} {online_id}",
            color=discord.Color.red(),
        )
        embed.set_footer(text=self.bot.get_text(ctx.author.id, "host"))

        for i, game in enumerate(recent_games_iterator):
            if i >= config.MAX_RECENT_DISPLAY:
                break

            search_results = self.bot.psnawp.search(
                game.name, "MobileUniversalSearchGame", limit=1
            )
            search_results = [r for r in search_results]
            media_texts = []

            if search_results:
                game_media = search_results[0]["result"]["media"]

                for j, media in enumerate(game_media):
                    if j >= config.MAX_MEDIA_PER_GAMES:
                        break
                    if media["role"] == "MASTER":
                        continue

                    media_texts.append(f"[{media['role']}]({media['url']})")

            game_search = self.bot.igdb.search_game(game.name, limit=1)

            if game_search:
                game_result = game_search[0]
                game_description = (
                    game_result.description
                    if game_result.description
                    else self.bot.get_text(ctx.author.id, "no_desc")
                )
            else:
                game_description = self.bot.get_text(ctx.author.id, "no_games")

            play_time = str(game.play_duration)
            embed.add_field(
                name=game.name,
                value=(
                    f"{self.bot.get_text(ctx.author.id, 'description')}: {game_description[:config.MAX_SHORT_DESC_LENGTH]}...\n"
                    f"{self.bot.get_text(ctx.author.id, 'category')}: {game.category.name}\n"
                    f"{self.bot.get_text(ctx.author.id, 'game_id')}: {game.title_id}\n"
                    f"{self.bot.get_text(ctx.author.id, 'play_count')}: {game.play_count}\n"
                    f"{self.bot.get_text(ctx.author.id, 'first_played')}: <t:{int(game.first_played_date_time.timestamp())}:R>\n"
                    f"{self.bot.get_text(ctx.author.id, 'last_played')}: <t:{int(game.last_played_date_time.timestamp())}:R>\n"
                    f"{self.bot.get_text(ctx.author.id, 'play_duration')}: {translate_date(play_time, ctx.author.id, self.bot)}\n"
                    f"[{self.bot.get_text(ctx.author.id, 'game_icon')}]({game.image_url})\n"
                    f"{self.bot.get_text(ctx.author.id, 'media')}: {' | '.join(media_texts)}"
                ),
                inline=False,
            )

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(PSNCog(bot))
