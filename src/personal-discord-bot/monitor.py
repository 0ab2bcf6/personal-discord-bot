#!/usr/bin/env python3
"""
monitor.py

"""

import asyncio
import random
import re
import requests

from datetime import timezone, datetime, timedelta
from typing import List

import discord
# from bs4 import BeautifulSoup
from discord import Message
from discord.ext import commands, tasks

from .config import CogConfig


class Monitor(commands.Cog):
    """a cog to monitor user (in-)activity on the server"""

    def __init__(self, bot, config: CogConfig) -> None:
        self.bot = bot
        self.logger = bot.logger
        self.guild_id = bot.config.server_id

        self._config: CogConfig = config
        self._inactivity: bool = self._config.inactivity
        self._channel_id: int = self._config.channel_id
        self._messages: bool = self._config.messages
        self._fixupx: bool = self._config.fixupx
        self._roles_privileged: List[str] = self._config.roles_privileged
        self._roles_to_monitor: List[str] = self._config.roles_to_monitor
        self._roles_inactive: List[str] = self._config.roles_inactive
        self._default_roles: List[str] = self._config.roles_default
        self._inactive_message = "\n\n".join(self._config.inactivity_message)
        self._inactive_message_id: int = 0

        self.reply_messages = [
            "Immer an den Embed denken, bitte!"
        ]

    async def _get_roles_by_name(self, roles_as_list: List[str]) -> List:
        """returns a list of discord roles"""
        _list_roles = []
        for role_name in roles_as_list:
            role = discord.utils.get(self.guild.roles, name=role_name)
            if role is not None:
                _list_roles.append(role)
            else:
                self.logger.error(
                    f"{self.__cog_name__}: role '{role_name}' not found in {self.guild}!"
                )
        return _list_roles

    # Background task: check_inactive_users
    @tasks.loop(hours=24)
    async def _check_inactive_users(self) -> None:
        """checks when a user last posted a message"""

        if self.guild is None:
            self.logger.error(
                f"{self.__cog_name__}: no valid guild {self.guild_id}!")
            return

        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        four_weeks_ago = four_weeks_ago.replace(tzinfo=None)

        roles_to_monitor = await self._get_roles_by_name(
            self._roles_to_monitor
        )
        roles_to_assign = await self._get_roles_by_name(
            self._roles_inactive
        )
        privileged_roles = await self._get_roles_by_name(
            self._roles_privileged
        )

        for member in self.guild.members:
            is_active = False

            if member.id == self.bot.user.id:
                continue

            if privileged_roles in member.roles:
                continue

            last_message = None
            for channel in self.guild.text_channels:
                fetch_message = await discord.utils.get(
                    channel.history(
                        limit=10000, after=four_weeks_ago, oldest_first=False
                    ),
                    author__id=member.id,
                )
                if fetch_message is None:
                    continue

                if last_message is None:
                    last_message = fetch_message
                else:
                    if fetch_message.created_at > last_message.created_at:
                        last_message = fetch_message

            member_joined = member.joined_at.replace(tzinfo=None)

            is_active = (
                last_message is not None
                or member_joined > four_weeks_ago
            )

            self.logger.info(
                f"{self.__cog_name__}: (@{member},{member.id}) activity status: "
                f"{is_active}."
            )

            if not is_active:
                # Remove roles
                roles_removed = []
                for role in roles_to_monitor:
                    if role is not None and role in member.roles:
                        roles_removed.append(role.name)
                        await member.remove_roles(role)

                self.logger.info(
                    f"{self.__cog_name__}: (@{member},{member.id}) roles removed: "
                    f"{roles_removed}."
                )

                # Add roles
                roles_assinged = []
                if (roles_to_assign is not None and
                        roles_to_assign not in member.roles):
                    for entry in roles_to_assign:
                        roles_assinged.append(entry.name)
                        await member.add_roles(entry)

                    self.logger.info(
                        f"{self.__cog_name__}: (@{member},{member.id}) roles assigned: "
                        f"{roles_assinged}."
                    )
            # else:
            #     # If user is active, remove the roles
            #     for entry in roles_to_assign:
            #         if entry in member.roles:
            #             await member.remove_roles(entry)

    @tasks.loop(hours=120)
    async def _check_inactive_message(self) -> None:
        """checks if the inactive_message is still in the inactive channel"""
        channel = self.bot.get_channel(self._channel_id)

        messages = []
        async for message in channel.history(limit=50):
            messages.append(message)

        for message in messages:
            # if message.author == self.bot.user and message.content == self._inactive_message:
            if message.author == self.bot.user and self._inactive_message_id == message.id:
                break
        else:
            sent_message = await channel.send(self._inactive_message)
            self._inactive_message_id = sent_message.id

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        """execute when a message is sent"""
        if message.author.bot:
            return

        if not self._messages:
            return

        self.logger.info(
            f"{self.__cog_name__}: (@{message.author.name},{message.author.id}) in (#{message.channel.id}): {message.content}"
        )

        if self._fixupx:
            xcom_regex = r"https://x\.com/(\w+)/status/(\d+)"

            # Search for X.com link in the message content
            match = re.search(xcom_regex, message.content)

            if match:
                username = match.group(1)
                status_id = match.group(2)

                new_link = f"https://fixupx.com/{username}/status/{status_id}"
                random_message = random.choice(self.reply_messages)

                await message.reply(f"{random_message} {new_link}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """assign default role when member joins"""
        default_roles = await self._get_roles_by_name(self._default_roles)
        if default_roles is not None:
            for role in default_roles:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        self.guild = self.bot.get_guild(self.guild_id)

        if self.guild is None:
            self.logger.error(
                f"{self.__cog_name__}: no valid guild {self.guild_id}!")

        if self._inactivity:
            self._check_inactive_users.start()
            self._check_inactive_message.start()

        self.logger.info(f"{self.__cog_name__} loaded.")
