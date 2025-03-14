#!/usr/bin/env python3
# flake8: noqa: E501
# pylint: skip-file
# type: ignore
"""
poll cog class
"""
# Standard library imports
import asyncio
import random
from typing import TYPE_CHECKING, Any, List

# Third-party imports
import discord
from discord.ext import commands

# Local application imports
from .basecog import BaseCog
from .config import CogConfig
from .logger import LoggingMiddleware

# Conditional typing imports
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class Poll(BaseCog):
    "Simple Poll Class"

    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self._lot_entries: List[str] = []
        self.cooldown: bool = False

    @commands.command(name='lot', aliases=["enter_lot", "enterlot"], help="Enter a lot for polling: !lot [entry] [optional: print_reply]")
    async def enter_lot(self, ctx: commands.Context, entry: str, print_reply: bool = False) -> None:

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # Ignore commands outside the designated channel

        user = ctx.author
        lot_entry = (user, entry)

        if not entry:
            await ctx.send(f"{user.mention}, please provide an entry message for the lot. Thank you!")
            return

        self._lot_entries.append(lot_entry)

        if print_reply:
            await ctx.send(f"Your lot has been entered into the urn, {user.mention}!")

    @commands.command(name='ziehen', aliases=["draw_lot", "drawlot"], help="Draw a random lot.")
    async def draw_lot(self, ctx: commands.Context) -> None:

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # Ignore commands outside the designated channel

        if not self._lot_entries:
            await ctx.send("There are currently no lots in the urn. Feel free to enter one using !enter_lot.")
            return

        winning_lot = random.choice(self._lot_entries)
        await ctx.send(f"And the winner is: {winning_lot[1]}, congratulations {winning_lot[0].mention}!")
        self._lot_entries.clear()

    async def start_cooldown(self) -> None:
        await asyncio.sleep(60)
        self.cooldown = False

    @commands.command(name="poll", aliases=["openpoll"], help="Create a Poll: !poll [question] [duration in min.] [option1] [option2] ...")
    async def open_poll(self, ctx: commands.Context, question: str, timer: int, *options: str) -> None:
        """Create a poll with a specified question, duration, and options."""

        if not question:
            await ctx.send("You must provide a question for the poll!")
            return

        if timer > 172800 / 60:
            await ctx.send("Poll duration cannot exceed 2 days (2880 minutes)!")
            return

        if len(options) < 2:
            await ctx.send("Please provide at least two options for the poll!")
            return

        if len(options) > 10:
            await ctx.send("Polls can have a maximum of 10 options!")
            return

        if not self.cooldown:
            self.cooldown = True
        else:
            return

        poll_embed = discord.Embed(
            title=f"Poll: {question}", description="", color=0x00ff00)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                  '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        for i, option in enumerate(options):
            poll_embed.add_field(
                name=f"Option {i+1}", value=f"{emojis[i]} {option}", inline=False)

        poll_message = await ctx.send(embed=poll_embed)

        for i in range(len(options)):
            await poll_message.add_reaction(emojis[i])

        await asyncio.sleep(timer*60)

        poll_message = await ctx.channel.fetch_message(poll_message.id)
        results = {emojis[i]: 0 for i in range(len(options))}

        for reaction in poll_message.reactions:
            if reaction.emoji in results:
                results[reaction.emoji] = reaction.count - 1

        results_embed = discord.Embed(
            title=f"Poll Results: {question}", description="", color=0x00ff00)

        for i, option in enumerate(options):
            results_embed.add_field(name=f"{option}", value=f"{results[emojis[i]]} votes", inline=False)

        await ctx.send(embed=results_embed)
        await self.start_cooldown()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
