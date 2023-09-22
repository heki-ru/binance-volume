import json
import tomllib
from pathlib import Path

import aiohttp


class Api:
    def __init__(self) -> None:
        self.config = tomllib.loads(Path("api.toml").read_text())

    async def start_client(self) -> None:
        self.client = aiohttp.ClientSession()

    async def send_get_request(
        self, path: str, params: dict[str, str | list], futures: bool = False
    ) -> dict:
        if futures:
            url = self.config["futures_url"]
        else:
            url = self.config["spot_url"]
        async with self.client.get(f"{url}{path}", params=params) as resp:
            resp_json = await resp.json()
        return resp_json

    async def get_spot_ticker(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        path = self.config["spot_ticker"]
        return await self.send_get_request(path, params)

    async def get_spot_tickers(self, symbols: list) -> dict:
        params = {"symbols": json.dumps(symbols, separators=(",", ":"))}
        path = self.config["spot_ticker"]
        return await self.send_get_request(path, params)

    async def get_spot_exchange_info(self) -> dict:
        params = {}
        path = self.config["spot_exchange_info"]
        return await self.send_get_request(path, params)

    async def get_futures_ticker_24h(self) -> dict:
        params = {}
        path = self.config["futures_ticker_24h"]
        return await self.send_get_request(path, params, futures=True)
