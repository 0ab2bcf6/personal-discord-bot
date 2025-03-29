#!/usr/bin/env python3
"""
basecog.py
"""

# Standard Library Imports
import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

# Third-Party Imports
import yaml
from discord import TextChannel
from discord.abc import GuildChannel, PrivateChannel
from discord.ext import commands
from discord.threads import Thread

# Local Application Imports
from .config import CogConfig
from .logger import LoggingMiddleware

# Conditional Typing Imports
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class BaseCog(commands.Cog):
    """Base class for all cogs, providing common setup logic"""

    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        self.bot: MyBot = bot
        self.logger: LoggingMiddleware = None
        self._config: CogConfig = config

    async def cog_load(self) -> None:

        # Ensure bot is set
        if self.bot is None:
            raise ValueError(
                "Bot instance is not set. Ensure it is assigned before calling setup_hook.")

        # Fetch cogs
        self.logger = self.bot.get_cog("LoggingMiddleware")
        if self.logger is None:
            raise ValueError(
                "LoggingMiddleware cog not found. Ensure it is loaded first.")

        # Log successful setup
        await self.logger.log_info(self, "Setup completed")

    async def get_text_channel(self, channel_id: int) -> Optional[TextChannel]:
        """Retrieve and validate a TextChannel by ID.

        Args:
            channel_id: The ID of the channel to fetch.

        Returns:
            Optional[TextChannel]: The TextChannel if found and valid, None otherwise.
        """
        channel: Optional[Union[GuildChannel, Thread,
                                PrivateChannel]] = self.bot.get_channel(channel_id)
        if not channel:
            await self.logger.log_error(self, f"Channel {channel_id} not found!")
            return None
        if not isinstance(channel, TextChannel):
            await self.logger.log_error(self, f"Channel {channel_id} is not a TextChannel!")
            return None
        return channel

    async def save_data_to_file(self, data: Any, file_path: Path) -> None:
        """
        Asynchronously save data to a YAML file with atomic writes for safety.

        :param data: Data structure to save (e.g., dict or list)
        :param file_path: Path where the YAML file should be saved
        """
        try:
            # Write data directly to the file
            with file_path.open('w', encoding='utf-8') as yaml_file:
                yaml.dump(data, yaml_file)

            await self.logger.log_info(self, f"Data written to {file_path}.")
        except Exception as e:
            await self.logger.log_error(self, f"Error saving data: {e}")

    async def load_data_from_file(self, file_path: Path) -> Optional[Any]:
        """
        Asynchronously load data from a YAML file.

        :param file_path: Path to the YAML file
        :return: Loaded data or None if the file doesn't exist or there's an error
        """
        try:
            # Ensure file_path is a Path object
            file_path = Path(file_path)
            data = await asyncio.to_thread(self._sync_load_data_from_file, file_path)
            if data is not None:
                await self.logger.log_info(self, f"Successfully loaded data from {file_path}.")
                return data
        except FileNotFoundError:
            await self.logger.log_info(self, "Starting with empty data structure.")
        except yaml.YAMLError as e:
            await self.logger.log_error(
                self, f"Error parsing YAML from {file_path}: {e}")
        except Exception as e:
            await self.logger.log_error(self, f"Unexpected error loading data: {e}")
        return None

    def _sync_load_data_from_file(self, file_path: Path) -> Optional[Any]:
        with open(file_path.as_posix(), "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
