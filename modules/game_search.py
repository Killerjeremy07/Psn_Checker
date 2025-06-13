import requests
from datetime import datetime
from typing import List, Dict, Optional


class Game:
    def __init__(
        self,
        data: list[any],
        name: str,
        description: str,
        story: str,
        publishers: List[str],
        cover_url: str,
        similar_games: List[str],
        platforms: List[str],
        release_date: Optional[datetime],
        medias: Dict[str, List[str]],
        url: str,
        genres: List[str],
        keywords: List[str],
        rating: float,
    ):
        self.data = data
        self.name = name
        self.description = description
        self.story = story
        self.publishers = publishers
        self.cover_url = cover_url
        self.similar_games = similar_games
        self.platforms = platforms
        self.release_date = release_date
        self.medias = medias
        self.url = url
        self.genres = genres
        self.keywords = keywords
        self.rating = rating


class IGDB:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.URLS = {"games": "https://api.igdb.com/v4/games"}
        self.token = self.__get_token()

    def __get_token(self):
        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        return response.json()["access_token"]

    def __get_request_header(self):
        return {"Client-ID": self.client_id, "Authorization": f"Bearer {self.token}"}

    def search_game(self, query: str, limit: int = 1) -> list[Game]:
        response = requests.post(
            self.URLS["games"],
            headers=self.__get_request_header(),
            data=f'search "{query}"; fields name,summary,storyline,involved_companies.company.name,cover.url,similar_games.name,platforms.name,first_release_date,videos.video_id,artworks.url,url,genres.name,keywords.name,rating; limit {limit};',
        )
        games_data = response.json()
        games = []

        for game_data in games_data:
            name = game_data.get("name")
            description = game_data.get("summary")
            story = game_data.get("storyline")
            publishers = [
                company["company"]["name"]
                for company in game_data.get("involved_companies", [])
            ]
            cover_url = game_data.get("cover", {}).get("url")
            if cover_url and cover_url.startswith("//"):
                cover_url = f"https:{cover_url}".replace("t_thumb", "t_original")
            similar_games = [
                similar_game["name"]
                for similar_game in game_data.get("similar_games", [])
            ]
            platforms = [
                platform["name"] for platform in game_data.get("platforms", [])
            ]
            release_date = (
                datetime.utcfromtimestamp(game_data["first_release_date"])
                if game_data.get("first_release_date")
                else None
            )
            medias = {
                "videos": [
                    f'https://www.youtube.com/watch?v={video["video_id"]}'
                    for video in game_data.get("videos", [])
                ],
                "artworks": [
                    (
                        f'https:{artwork["url"].replace("t_thumb", "t_original")}'
                        if artwork["url"].startswith("//")
                        else artwork["url"]
                    )
                    for artwork in game_data.get("artworks", [])
                ],
            }
            url = game_data.get("url")
            genres = [genre["name"] for genre in game_data.get("genres", [])]
            keywords = [keyword["name"] for keyword in game_data.get("keywords", [])]
            rating = game_data.get("rating")

            games.append(
                Game(
                    data=game_data,
                    name=name,
                    description=description,
                    story=story,
                    publishers=publishers,
                    cover_url=cover_url,
                    similar_games=similar_games,
                    platforms=platforms,
                    release_date=release_date,
                    medias=medias,
                    url=url,
                    genres=genres,
                    keywords=keywords,
                    rating=rating,
                )
            )

        return games
