import re
from dataclasses import dataclass
from enum import Enum

import aiohttp
from psnawp_api import PSNAWP

from modules.api.common import APIError

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class PSNOperation(Enum):
    CHECK_AVATAR = 1
    ADD_TO_CART = 2
    REMOVE_FROM_CART = 3


@dataclass
class PSNRequest:
    pdccws_p: str
    region: str
    product_id: str


class PSN:
    def __init__(self, npsso: str):
        self.secret = npsso
        self.psnawp = PSNAWP(self.secret)

        # for request
        self.url = ""
        self.headers = {}
        self.data_json = {}

        # for response
        self.res = {}

    @staticmethod
    def validate_request(req: PSNRequest):
        if req.product_id.count("-") != 2:
            raise APIError("Invalid product ID!")

    def get_error_cause(self) -> str:
        return self.res.get("cause")

    def get_error(self) -> str | None:
        if "subTotalPrice" in str(self.res):
            return None

        elif self.res.get("errors"):
            return self.res["errors"][0]["message"]
        return None

    def request_builder(self, request: PSNRequest, operation: PSNOperation) -> None:
        match operation:
            case PSNOperation.CHECK_AVATAR:
                self.url = f"https://store.playstation.com/store/api/chihiro/00_09_000/container/{request.region.replace('-', '/')}/19/{request.product_id}/"
                self.headers = {
                    "Origin": "https://checkout.playstation.com",
                    "content-type": "application/json",
                    "Accept-Language": request.region,
                    "Cookie": f"AKA_A2=A; pdccws_p={request.pdccws_p}; isSignedIn=true; userinfo={self.secret}; p=0; gpdcTg=%5B1%5D",
                }

            case PSNOperation.ADD_TO_CART:
                self.url = "https://web.np.playstation.com/api/graphql/v1/op"
                self.headers = {
                    "Origin": "https://checkout.playstation.com",
                    "content-type": "application/json",
                    "Accept-Language": request.region,
                    "Cookie": f"AKA_A2=A; pdccws_p={request.pdccws_p}; isSignedIn=true; userinfo={self.secret}; p=0; gpdcTg=%5B1%5D",
                }
                self.data_json = {
                    "operationName": "addToCart",
                    "variables": {"skus": [{"skuId": ""}]},
                    "extensions": {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "93eb198753e06cba3a30ed3a6cd3abc1f1214c11031ffc5b0a5ca6d08c77061f",
                        }
                    },
                }

            case PSNOperation.REMOVE_FROM_CART:
                self.url = "https://web.np.playstation.com/api/graphql/v1/op"
                self.headers = {
                    "Origin": "https://checkout.playstation.com",
                    "content-type": "application/json",
                    "Accept-Language": request.region,
                    "Cookie": f"AKA_A2=A; pdccws_p={request.pdccws_p}; isSignedIn=true; userinfo={self.secret}; p=0; gpdcTg=%5B1%5D",
                }
                self.data_json = {
                    "operationName": "removeFromCart",
                    "variables": {"skuId": ""},
                    "extensions": {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "55e50c2157c33e84f409d2a52f3bb7c19db62b144fb49e75a1a9b0acad276bba",
                        }
                    },
                }

    def insert_skuId_deep(self, skuId: str) -> None:
        self.data_json["variables"]["skus"][0]["skuId"] = skuId

    def insert_skuId(self, sku_Id: str) -> None:
        self.data_json["variables"]["skuId"] = sku_Id

    async def check_avatar(
        self, request: PSNRequest, obtain_skuget_only: bool = False
    ) -> str:
        self.validate_request(request)
        self.request_builder(request, PSNOperation.CHECK_AVATAR)

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers) as response:
                self.res = await response.json()

        sku_get = self.res.get("default_sku", {}).get("id")
        if sku_get is None:
            raise APIError(self.get_error_cause())
        if obtain_skuget_only:
            return sku_get

        picture_avatar = f"https://store.playstation.com/store/api/chihiro/00_09_000/container/{request.region.replace('-', '/')}/19/{request.product_id}/image"
        return picture_avatar

    async def add_to_cart(self, request: PSNRequest) -> None:
        sku_id = await self.check_avatar(request, obtain_skuget_only=True)
        self.request_builder(request, PSNOperation.ADD_TO_CART)
        self.insert_skuId_deep(sku_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url, headers=self.headers, json=self.data_json
            ) as response:
                self.res = await response.json()

        err = self.get_error()
        if err is not None:
            raise APIError(err)

    async def remove_from_cart(self, request: PSNRequest) -> None:
        sku_id = await self.check_avatar(request, obtain_skuget_only=True)
        self.request_builder(request, PSNOperation.REMOVE_FROM_CART)
        self.insert_skuId(sku_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url, headers=self.headers, json=self.data_json
            ) as response:
                self.res = await response.json()

        err = self.get_error()
        if err is not None:
            raise APIError(err)
