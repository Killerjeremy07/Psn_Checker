from discord.ext import commands
from psnawp_api import PSNAWP


class Bot(commands.Bot):
    def __init__(self, psn_api_token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.psnawp = PSNAWP(psn_api_token)
