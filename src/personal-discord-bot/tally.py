#!/usr/bin/env python3
"""
tally.py
"""

import random
import time
from logging import Logger
from pathlib import Path
from typing import Dict

import yaml
from discord.ext import commands, tasks

from .config import CogConfig

# Absolute Path of current file
# pylint: disable=invalid-name
SCRIPT_DIR = Path(__file__).resolve().parent


class Tally(commands.Cog):
    """a simple tally cog for discord"""

    def __init__(self, bot, config: CogConfig) -> None:
        self.bot = bot
        self.logger: Logger = bot.logger

        self._config: CogConfig = config
        self.channel_id: int = 999
        self._path = Path(SCRIPT_DIR, self._config.path)
        self._currency: str = "Striche"
        self._start_amount: int = 0
        # self._currency: str = self._config.currency_name
        # self._start_amount: int = self._config.start_amount

        self._depot_users: Dict[int, int] = {}
        self._cooldown: Dict[int, float] = {}

        # Load depots from YAML file
        self._load_depots()

    def _load_depots(self) -> None:
        """load tally from config path"""
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                self._depot_users = yaml.safe_load(file)
        except FileNotFoundError:
            self.logger.info(
                f"{self.__cog_name__}: Starting with empty tally.")

    @tasks.loop(hours=1)
    async def _save_depots(self) -> None:
        """save tally to config path"""
        with open(self._path, "w", encoding="utf-8") as file:
            yaml.dump(self._depot_users, file)

        self.logger.info(
            f"{self.__cog_name__}: tally written to {self._path}.")

    @commands.command(name="striche", aliases=["liste", "strichliste"], help="Zeig die Strichliste.")
    async def tally(self, ctx: commands.Context, target: commands.MemberConverter) -> None:
        """send message to channel with tally of ctx author"""

        # if self.channel_id is None or ctx.channel.id != self.channel_id:
        #     return  # ignore any commands not in the specific channel
        if target == None:
            user = ctx.author
        else:
            user = target

        if user.id in self._depot_users:
            if self._depot_users[user.id] > 1:
                variant_msgs = [
                    f"{user.mention} hat schon {self._depot_users[user.id]} Striche erreicht.",
                    f"Ganze {self._depot_users[user.id]} Striche auf der Liste. Wow {user.mention}.",
                ]
                message = random.choice(variant_msgs)
            else:
                message = f"{user.mention} hat {self._depot_users[user.id]} Strich."
            await ctx.send(message)
        else:
            await ctx.send(f"{user.mention} ist noch nicht negativ aufgefallen.")

    @commands.command(name="strich", help="Verteil einen Strich.")
    async def add_strich(self, ctx: commands.Context, user: commands.MemberConverter) -> None:
        """Add a token to the mentioned user's tally"""

        if user == None:
            return

        if user.id not in self._depot_users:
            self._depot_users[user.id] = 1
            variant_msgs = [
                f"So, {user.mention}, das war die 1."
                ]
            msg = random.choice(variant_msgs)
            await ctx.send(msg)
        else:
            self._depot_users[user.id] += 1
            variant_msgs = [
                f"+1 für {user.mention}."
                ]
            msg = random.choice(variant_msgs)
            await ctx.send(msg)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        self._save_depots.start()
        self.logger.info(f"{self.__cog_name__} loaded.")
