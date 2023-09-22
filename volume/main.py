import asyncio
import time
import tomllib
from asyncio import sleep
from pathlib import Path

from _decimal import Decimal
from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from pydantic import BaseModel

from api import Api


class Ticker(BaseModel):
    symbol: str
    priceChange: str
    priceChangePercent: str
    weightedAvgPrice: str
    lastPrice: str
    lastQty: str
    openPrice: str
    highPrice: str
    lowPrice: str
    volume: str
    quoteVolume: str
    openTime: int
    closeTime: int
    firstId: int
    lastId: int
    count: int


class Tickers(BaseModel):
    tickers: list[Ticker]


class Volume:
    def __init__(self) -> None:
        self.api = Api()
        self.config = tomllib.loads(Path("config.toml").read_text())
        self.period = self.config["period"]
        self.interval = self.config["interval"]
        self.webhook_url = self.config["webhook_url"]
        self.blacklist = []
        with Path("blacklist.txt").open() as file:
            for symbol in file:
                self.blacklist.append(symbol.rstrip())

    @staticmethod
    async def parse_response(res):
        tickers = []
        for ticker in res:
            tickers.append(Ticker(**ticker))
        return Tickers(tickers=tickers)

    async def compare_symbols(self, symbol, ticker):
        quote_volume_diff = Decimal(ticker.quoteVolume) - Decimal(symbol["quoteVolume"])
        volume_threshold = Decimal(ticker.quoteVolume) / self.period
        if quote_volume_diff > volume_threshold:
            volume = f"{quote_volume_diff / Decimal(symbol['quoteVolume']):.2%}"
            price = f"{(Decimal(symbol['lastPrice']) - Decimal(ticker.lastPrice)) / Decimal(ticker.lastPrice):.2%}"
            trades = f"{symbol['count'] - ticker.count}"
            await self.send_webhook(ticker.symbol, volume, price, trades)

    async def send_webhook(self, symbol, volume, price, trades):
        webhook = AsyncDiscordWebhook(
            url=self.webhook_url, rate_limit_retry=True, username="Binance"
        )
        embed = DiscordEmbed(
            title=symbol,
            color="ffdb6d",
            url=f"https://www.binance.com/en/futures/{symbol}",
        )
        embed.add_embed_field(name="Volume", value=volume)
        embed.add_embed_field(name="Price", value=price)
        embed.add_embed_field(name="Trades", value=trades)
        embed.set_timestamp()
        webhook.add_embed(embed)
        await webhook.execute()

    async def worker(self):
        await self.api.start_client()
        res = await self.api.get_futures_ticker_24h()
        tickers = await self.parse_response(res)
        while True:
            start_time = time.time()
            res = await self.api.get_futures_ticker_24h()
            for symbol in res:
                if symbol["symbol"] not in self.blacklist:
                    for ticker in tickers.tickers:
                        if ticker.symbol == symbol["symbol"]:
                            await self.compare_symbols(symbol, ticker)
            tickers = await self.parse_response(res)
            end_time = time.time()
            sleep_time = self.interval - (end_time - start_time)
            await sleep(sleep_time)
        # await api.client.close()


if __name__ == "__main__":
    v = Volume()
    asyncio.run(v.worker())
