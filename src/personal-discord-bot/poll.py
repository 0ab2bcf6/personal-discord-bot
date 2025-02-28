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

    @commands.command(name='los', aliases=["enter_lot", "enterlot"], help="Erstell ein Los: !los [eintrag]")
    async def enter_lot(self, ctx: commands.Context, entry: str, print_reply:bool = False) -> None:

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        user = ctx.author
        lot_entry = (user, entry)

        if not entry:
            await ctx.send(f"Bitte das Los beschriften {user.mention}, danke.")
            return

        self._lot_entries.append(lot_entry)

        if print_reply:
            await ctx.send(f"Dein Los ist jetzt in der Urne, {user.mention}!")

    @commands.command(name='ziehen', aliases=["draw_lot", "drawlot"], help="Zieh ein Los.")
    async def draw_lot(self, ctx: commands.Context) -> None:

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not self._lot_entries:
            await ctx.send("Gerade sind keine Lose in der Urne. Du kannst aber gerne !enter_lot schreiben.")
            return

        winning_lot = random.choice(self._lot_entries)
        await ctx.send(f"Ebin für: {winning_lot[1]}, {winning_lot[0].mention}!")
        self._lot_entries.clear()

    async def start_cooldown(self) -> None:
        await asyncio.sleep(120)
        self.cooldown = False

    @commands.command(name="umfrage", aliases=["open_poll", "poll", "openpoll"], help="Erstell eine Umfrage: !umfrage [frage] [dauer min.] [opt1] [opt2] ...")
    async def open_poll(self, ctx: commands.Context, question: str, timer: int, *options: str) -> None:
        """open a poll with """

        if not question:
            await ctx.send("Bitte eine Frage formulieren, danke.")
            return

        if timer > 172800/60:
            await ctx.send("Bitte keine Umfragen über 2 Tage machen, danke.")

        if len(options) < 2:
            await ctx.send("Bitte mindestens 2 Optionen angeben, danke.")
            return

        if len(options) > 10:
            await ctx.send("Bitte nicht mehr als 10 Optionen angeben, danke.")
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
