#!/usr/bin/env python3
"""
bot.py
"""

from typing import Dict, List

from logging import Logger

import discord
from discord.ext import commands

from .config import Config
from .tally import Tally
from .logger import LoggingMiddleware
from .monitor import Monitor
from .music import Music
from .movie import Movie
from .poll import Poll
from .reactionroles import ReactionRoles


class MyBot(commands.Bot):
    """mybot"""

    def __init__(self, config: Config, logger: Logger) -> None:
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, case_insensitive=True)
        self.logger: Logger = logger
        self.config: Config = config

        self.bot_admin: List[int] = self.config.bot_admin

    async def setup_cogs(self) -> None:
        """setup cogs"""
        logger_cog = LoggingMiddleware(self)
        await self.add_cog(logger_cog)

        if self.config.cogs["tally"].enabled:
            tally_cog = Tally(self, self.config.cogs["tally"])
            await self.add_cog(tally_cog)

        if self.config.cogs["monitor"].enabled:
            monitor_cog = Monitor(self, self.config.cogs["monitor"])
            await self.add_cog(monitor_cog)

        if self.config.cogs["music"].enabled:
            music_cog = Music(self)
            await self.add_cog(music_cog)

        if self.config.cogs["movie"].enabled:
            movie_cog = Movie(self, self.config.cogs["movie"])
            await self.add_cog(movie_cog)

        if self.config.cogs["poll"].enabled:
            poll_cog = Poll(self, self.config.cogs["poll"])
            await self.add_cog(poll_cog)
        
        if self.config.cogs["reactionroles"].enabled:
            reactionroles_cog = ReactionRoles(self, self.config.cogs["reactionroles"])
            await self.add_cog(reactionroles_cog)

    async def close(self) -> None:
        """close bot"""
        self.logger.info("Bot is shutting down.")
        await super().close()
