import aiohttp
import re
from modules.api import APIError

DECIMAL_RE = re.compile(r"\d+")


class PSPrices:
    def __init__(self, url: str) -> None:
        match = DECIMAL_RE.search(url)

        if not match:
            raise APIError("Invalid URL!")

        self.game_id = match.group()
        self.url = f"https://psprices.com/game/buy/{self.game_id}"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async def obtain_skuid(self) -> str:
        async with aiohttp.ClientSession() as session:
            res = await session.get(
                self.url, allow_redirects=True, headers=self.HEADERS
            )

            # product_id = url.split("productId=")[1].split("&")[0]
            product_id = res.url.query.get("productId", "FAIL!")
            if product_id == "FAIL!":
                raise APIError("FAIL!")

            return product_id
