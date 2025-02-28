#!/usr/bin/env python3
"""
reaction roles cog class
"""

# Standard library imports
from typing import TYPE_CHECKING, Any, Dict, Optional

# Third-party library imports
import discord
from discord import Embed, RawReactionActionEvent, TextChannel
from discord.ext import commands

# Local application imports
from .basecog import BaseCog
from .config import CogConfig

# Conditional imports for type checking
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class ReactionRoles(BaseCog):
    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self.message_data: Dict[int, Dict[str, Any]] = {}

    async def cog_load(self) -> None:
        """Runs when the cog is fully loaded and dependencies are available."""
        await super().cog_load()
        self.message_data = await self.load_data_from_file(self._config.path) or {}
        if len(self.message_data.keys()) > 0:
            await self.logger.log_info(self, f"Loaded reaction role message IDs: {self.message_data}")
        else:
            await self.logger.log_warning(self, f"No message IDs found in {self._config.path}")

    async def setup_reaction_messages(self) -> None:
        """Ensure reaction role messages exist."""

        channel: Optional[TextChannel] = await self.get_text_channel(self._config.channel_id)
        if not channel:
            return

        all_messages_available = True if self.message_data else False

        # Check if stored messages still exist
        for message_id in self.message_data.keys():
            try:
                await channel.fetch_message(message_id)
                # If message is found, keep all_messages_available as True (no change needed)
            except discord.NotFound:
                await self.logger.log_warning(self, f"Message {message_id} not found, creating a new one.")
                all_messages_available = False

        if not all_messages_available:
            # Delete old messages
            for message_id in self.message_data.keys():
                try:
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                    await self.logger.log_info(self, f"Deleted orphaned message {message_id}.")
                except (discord.NotFound, discord.HTTPException):
                    pass

            # Clear the old message IDs
            self.message_data = {}

            # Create new reaction role messages
            for entry in self._config.messages:
                message_id = await self.create_reaction_message(channel, entry)
                if message_id:
                    self.message_data[message_id] = entry

            # Save the new message IDs to file
            await self.save_data_to_file(self.message_data, self._config.path)

    async def create_reaction_message(self, channel: TextChannel, entry: Dict[str, Any]) -> int:
        """Creates a reaction role message and returns its ID."""

        embed = Embed(
            title=entry.get('text', 'Reaction Roles'),
            description="Reagiere für eine Rolle",
            color=discord.Color.blue()
        )

        reactions = entry.get('reactions', {})
        for emoji, data in reactions.items():
            role_name = data.get('role', 'Unknown Role')
            description = data.get('description', 'No description provided')
            embed.add_field(
                name=f"{emoji} {role_name}",
                value=description,
                inline=False
            )

        # Send message and add reactions
        try:
            bot_message = await channel.send(embed=embed)
            for emoji in reactions:
                await bot_message.add_reaction(emoji)
        except discord.Forbidden as e:
            await self.logger.log_error(self, f"Bot lacks permissions in channel {channel.id}: {str(e)}")
        except discord.HTTPException as e:
            await self.logger.log_error(self, f"Failed to create reaction message: {str(e)}")

        if bot_message.id not in self.message_data:
            self.message_data[bot_message.id] = entry

        return bot_message.id

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:

        if payload.message_id not in self.message_data:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:  # Ignore bots
            return

        message_config = self.message_data[payload.message_id]
        emoji = str(payload.emoji)

        reaction_roles = message_config.get('reactions', {})
        role_data = reaction_roles.get(emoji)
        if not role_data or 'role' not in role_data:
            return

        # Get and assign role
        role_name = role_data['role']
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role < guild.me.top_role:
            try:
                if not message_config.get('allow_multiple', True):
                    roles_to_remove = [
                        r for r in member.roles if r.name in reaction_roles.values()]
                    if roles_to_remove:
                        await member.remove_roles(*roles_to_remove)

                await member.add_roles(role, reason="Reaction role assignment")
            except discord.Forbidden:
                await self.logger.log_error(self, f"Bot lacks permissions to assign role {role_name}.")
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent) -> None:

        if payload.message_id not in self.message_data:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        message_config = self.message_data[payload.message_id]
        emoji = str(payload.emoji)

        reaction_roles = message_config.get('reactions', {})
        role_data = reaction_roles.get(emoji)
        if not role_data or 'role' not in role_data:
            return

        # Get and remove role
        role_name = role_data['role']
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role < guild.me.top_role:  # Check if bot can remove role
            try:
                await member.remove_roles(role, reason="Reaction role removal")
            except discord.Forbidden:
                await self.logger.log_error(self, f"Bot lacks permissions to remove role {role_name}.")
                pass

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
        await self.setup_reaction_messages()
