#!/usr/bin/env python3
"""
tally.py
"""
# Standard library imports
import random
from pathlib import Path
from typing import Dict, TYPE_CHECKING, Any

# Third-party imports
from discord.ext import commands

# Local application/library specific imports
from .basecog import BaseCog
from .config import CogConfig
from .logger import LoggingMiddleware

if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class Tally(BaseCog):
    """tally cog for discord"""

    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self._path: Path = self._config.path
        self._currency: str = "Striche"
        self._start_amount: int = 0

        self._depot_users: Dict[int, int] = {}

    @commands.command()
    async def tally(self, ctx: commands.Context, target: discord.Member) -> None:
        """send message to channel with tally of ctx author"""

        # if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
        #     return  # ignore any commands not in the specific channel

        if not self._depot_users:
            await self.load_data_from_file(self._path)

        if target == None:
            user = ctx.author
        else:
            user = target

        if user.id in self._depot_users:
            if self._depot_users[user.id] > 1:
                variant_msgs = [
                    f"Ganze {self._depot_users[user.id]} Striche auf dem Kontom, {user.mention}."
                ]
                message = random.choice(variant_msgs)
            else:
                message = f"{user.mention} hat {self._depot_users[user.id]} Strich."
            await ctx.send(message)
        else:
            await ctx.send(f"{user.mention} ist noch nicht negativ aufgefallen.")

    @commands.command()
    async def add_strich(self, ctx: commands.Context, user: discord.Member) -> None:
        """Add a token to the mentioned user's tally"""

        if user == None:
            return

        if not self._depot_users:
            await self.load_data_from_file(self._path)

        if user.id not in self._depot_users:
            self._depot_users[user.id] = 1
            variant_msgs = [
                f"So, {user.mention}, das war die 1."]
            msg = random.choice(variant_msgs)

        else:
            self._depot_users[user.id] += 1
            variant_msgs = [
                f"+1 für {user.mention}."]
            msg = random.choice(variant_msgs)

        await ctx.send(msg)
        await self.save_data_to_file(self._depot_users, self._path)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
