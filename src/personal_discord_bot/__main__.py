#!/usr/bin/env python3
"""
This is the main entry point for your module, if it is called as a scripts,
e.g.:
python -m your_module
This file contains the primary main() function for your entire project.
"""

import asyncio
import logging
import signal

from pathlib import Path

from .bot import MyBot
from .config import Config


def main() -> None:
    """
    This is the main function of this project. The main function usually
    returns nothing.

    Parameters
    ---------
    args :
        This is the Namespace-object returned by ArgumentParser. It contains
        all command line arguments passed to this script by the user.
    """
    def signal_handler(sig: signal.Signals, frame) -> None:
        logger.info("Received termination signal. Shutting down...")
        bot.loop.create_task(bot.close())

    # Absolute Path of current file
    # pylint: disable=invalid-name
    SCRIPT_DIR = Path(__file__).resolve().parent

    # Define paths using pathlib
    # pylint: disable=invalid-name
    LOGS_DIR = Path(SCRIPT_DIR, "logs")
    # pylint: disable=invalid-name
    CONFIG_FILE = Path(SCRIPT_DIR, "config.yaml")

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    # Create a file handler for logging
    file_handler = logging.FileHandler(
        filename=LOGS_DIR / "discord.log", encoding="utf-8", mode="a"
    )
    file_handler.setLevel(logging.INFO)
    # Create a formatter and set it for both handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot_config = Config(CONFIG_FILE)
    bot = MyBot(bot_config, logger)

    asyncio.run(bot.setup_cogs())
    bot.run(bot_config.token)


if __name__ == "__main__":

    main()
