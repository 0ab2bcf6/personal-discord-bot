#!/usr/bin/env python3
# flake8: noqa: E501
# pylint: skip-file
# type: ignore
"""
reaction roles cog class
"""


from logging import Logger

import discord
from discord.ext import commands, tasks

from .config import CogConfig

class ReactionRoles(commands.Cog):
    "a simple reaction roles class"

    def __init__(self, bot, config: CogConfig):
        self.bot = bot
        self.logger: Logger = bot.logger

        self.config = config
        self.message_ids = {}

    async def setup_reaction_messages(self):
        channel = self.bot.get_channel(self.config.channel_id)
        if not channel:
            return

        for entry in self.config.messages:
            message_exists = False
            async for message in channel.history(limit=100):
                if message.embeds and message.embeds[0].description == entry['text']:
                    self.message_ids[message.id] = entry
                    message_exists = True
                    break

            if not message_exists:
                embed = discord.Embed(
                    title=entry['text'], description="Reagiere für eine Rolle")
                for emoji, data in entry['reactions'].items():
                    embed.add_field(
                        name=f"{emoji} {data['role']}", value=data['description'], inline=False)

                bot_message = await channel.send(embed=embed)
                self.message_ids[bot_message.id] = entry

                for emoji in entry['reactions'].keys():
                    await bot_message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.message_ids:
            entry = self.message_ids[payload.message_id]
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if not member:
                return

            emoji = str(payload.emoji)
            role_name = entry['reactions'][emoji]['role']

            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    if entry['allow_multiple'] or len([r for r in member.roles if r.name in [data['role'] for data in entry['reactions'].values()]]) == 0:
                        await member.add_roles(role)
                    else:
                        roles_to_remove = [r for r in member.roles if r.name in [
                            data['role'] for data in entry['reactions'].values()]]
                        await member.remove_roles(*roles_to_remove)
                        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in self.message_ids:
            entry = self.message_ids[payload.message_id]
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if not member:
                return

            emoji = str(payload.emoji)
            role_name = entry['reactions'][emoji]['role']

            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        await self.setup_reaction_messages()
        self.logger.info(f"{self.__cog_name__} loaded.")
