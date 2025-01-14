#!/usr/bin/env python3
# flake8: noqa: E501
# pylint: skip-file
# type: ignore
"""
example cog class
"""

from discord.ext import commands, tasks


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counter = 0
        self.logger = bot.logger

    @tasks.loop(seconds=10)
    async def my_loop(self):
        self.counter += 1
        print(f"My loop has run {self.counter} times.")

    @commands.command()
    async def stop_loop(self, ctx):
        self.my_loop.stop()
        await ctx.send("Loop stopped.")

    @commands.command()
    async def start_loop(self, ctx):
        self.my_loop.start()
        await ctx.send("Loop started.")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Cog {self.__cog_name__} has been loaded.")
        self.my_loop.start()
