#!/usr/bin/env python3
"""
monitor.py

"""

# Standard Library Imports
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from pathlib import Path

# Third-Party Imports
import discord
from discord import Message, TextChannel
from discord.ext import commands, tasks

# Local Application Imports
from .basecog import BaseCog
from .config import CogConfig
from .logger import LoggingMiddleware

# Conditional Typing Imports
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class Monitor(BaseCog):
    """monitor user (in-)activity on the server"""

    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)

        self._guild_id: int = bot.config.server_id
        self._inactivity: bool = self._config.inactivity
        self._channel_id: int = self._config.channel_id
        self._messages: bool = self._config.messages
        self._fixupx: bool = self._config.fixupx
        self._roles_privileged: List[str] = self._config.roles_privileged
        self._roles_to_monitor: List[str] = self._config.roles_to_monitor
        self._roles_inactive: List[str] = self._config.roles_inactive
        self._default_roles: List[str] = self._config.roles_default
        self._path: Path = self._config.path
        self._inactive_message: str = "\n\n".join(
            self._config.inactivity_message)
        self._inactive_message_data: Optional[int] = None

    async def _get_roles_by_name(self, roles_as_list: List[str]) -> List:
        """returns a list of discord roles"""
        _list_roles = []
        for role_name in roles_as_list:
            role = discord.utils.get(self.guild.roles, name=role_name)
            if role is not None:
                _list_roles.append(role)
            else:
                await self.logger.log_error(self, f"role '{role_name}' not found in {self.guild}!")
        return _list_roles

    # Background task: check_inactive_users
    @tasks.loop(hours=48)
    async def _check_inactive_users(self) -> None:
        """checks when a user last posted a message"""

        if self.guild is None:
            await self.logger.log_error(self, f"no valid guild {self._guild_id}!")
            return

        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        four_weeks_ago = four_weeks_ago.replace(tzinfo=None)

        # Define the roles
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
            is_active: bool = False

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

            await self.logger.log_info(self, f"(@{member},{member.id}) activity status: {is_active}.")

            if not is_active:
                # Remove roles
                roles_removed = []
                for role in roles_to_monitor:
                    if role is not None and role in member.roles:
                        roles_removed.append(role.name)
                        await member.remove_roles(role)

                # await self.logger.log_info(self, f"(@{member},{member.id}) roles removed: {roles_removed}.")

                # Add roles
                roles_assinged = []
                if (roles_to_assign is not None and
                        roles_to_assign not in member.roles):
                    for entry in roles_to_assign:
                        roles_assinged.append(entry.name)
                        await member.add_roles(entry)

                    # await self.logger.log_info(self, f"(@{member},{member.id}) roles assigned: {roles_assinged}.")
            # else:
            #     # If user is active, remove the roles
            #     for entry in roles_to_assign:
            #         if entry in member.roles:
            #             await member.remove_roles(entry)

    @tasks.loop(hours=184)
    async def _check_inactive_message(self) -> None:
        """Checks if the inactive message is still in the last 20 messages."""
        channel: Optional[TextChannel] = await self.get_text_channel(self._channel_id)
        if not channel:
            await self.logger.log_error(self, "Channel not found.")
            return

        # Load inactive message data (assumed to contain message ID)
        self._inactive_message_data = await self.load_data_from_file(self._path) or None

        if not self._inactive_message_data:
            await self.logger.log_warning(self, "No inactive message ID found in data.")
            await self._create_inactive_message(channel)
            return

        # Fetch recent messages (limit to 20)
        try:
            messages = [message async for message in channel.history(limit=20)]
        except discord.HTTPException as e:
            await self.logger.log_error(self, f"Failed to fetch channel history: {e}")
            # if bad connection, check in next cycle
            return

        # Check if the stored message ID exists in recent messages
        for message in messages:
            if message.id == self._inactive_message_data and message.author == self.bot.user:
                # no action needed
                return

        # message wasnt found
        await self.logger.log_info(self, "Inactive message not found in last 20 messages, recreating.")
        await self._create_inactive_message(channel)

    async def _create_inactive_message(self, channel: TextChannel) -> None:
        """Creates or recreates the inactive message and saves its ID."""
        try:
            new_message = await channel.send(self._inactive_message)
            self._inactive_message_data = new_message.id
            await self.save_data_to_file(self._inactive_message_data, self._path)
            await self.logger.log_info(self, f"Created new inactive message with ID {new_message.id}.")
        except discord.HTTPException as e:
            await self.logger.log_error(self, f"Failed to create inactive message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        """execute when a message is sent"""
        if message.author.bot:
            return

        if not self._messages:
            return

        await self.logger.log_info(self, f"(@{message.author},{message.author.id}) in (#{message.channel.id}): {message.content}")

        if self._fixupx:
            xcom_regex = r"https://x\.com/(\w+)/status/(\d+)"

            # Search for X.com link in the message content
            match = re.search(xcom_regex, message.content)

            if match:
                username = match.group(1)
                status_id = match.group(2)

                # Create the new fixupx.com link
                new_link = f"https://fixupx.com/{username}/status/{status_id}"

                # Select a random reply message
                # random_message = random.choice(self.reply_messages)

                # Reply to the original message with the random message and modified link
                await message.channel.send(f"{new_link}")
                await asyncio.sleep(1)
                await message.delete()

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
        self.guild = self.bot.get_guild(self._guild_id)

        if self.guild is None:
            await self.logger.log_error(self, f"no valid guild {self._guild_id}!")

        if self._inactivity:
            self._check_inactive_users.start()
            self._check_inactive_message.start()

        await self.logger.log_info(self, "loaded.")
