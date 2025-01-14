#!/usr/bin/env python3
"""
logger.py
"""

from discord.ext import commands


class LoggingMiddleware(commands.Cog):
    """Middleware to log commands before invoke, on error and on completion"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.logger = bot.logger

    @commands.command(name="set", aliases=["setch", "setchannel", "set_ch"], help="Leg den Output Channel für eine Funktion fest.")
    async def set_channel(self, ctx: commands.Context, cog_name: str) -> None:
        """set output channel for specified cog"""

        if ctx.author.id not in self.bot.bot_admin:
            self.logger.error(f"(@{ctx.author},{ctx.author.id}) tried to set channel id of {cog_name} to (#{ctx.channel},{ctx.channel.id})!")
            await ctx.send('You do not have permission to set the channel.')
            return

        if cog_name not in self.bot.cogs.keys():
            self.logger.error(f"Could not find {cog_name} in cogs!")
            return

        self.bot.cogs[cog_name].channel_id = ctx.channel.id
        self.logger.info(
            f"{cog_name}: dedicated output channel set to (#{ctx.channel},{ctx.channel.id})!")
        # await ctx.send(f'Dedicated channel has been set to: {channel.name}')

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """log when command is used"""
        self.logger.info(
            f"Command invoked: {ctx.command} "
            f"by (@{ctx.author},{ctx.author.id}) "
            f"in {ctx.guild}."
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """log when command throws error"""
        self.logger.error(f"Error in command {ctx.command}: {error}!")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        """log when command is completed"""
        self.logger.info(
            f"Command completed: {ctx.command} "
            f"by (@{ctx.author},{ctx.author.id}) "
            f"in {ctx.guild}."
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        self.logger.info(f"{self.__cog_name__} loaded.")
