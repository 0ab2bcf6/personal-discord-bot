#!/usr/bin/env python3
"""
This is the main entry point for your module, if it is called as a scripts,
e.g.:
python -m your_module
This file contains the primary main() function for your entire project.
"""
# Standard library imports
import asyncio
import logging
from pathlib import Path
import signal

# Third-party library imports

# Local application imports
from .bot import MyBot
from .config import Config


def main() -> None:
    """Main function of the project."""
    def signal_handler(sig: signal.Signals, frame) -> None:
        logger.info("Received termination signal. Shutting down...")
        bot.loop.create_task(bot.close())

    # Absolute Path of current file
    SCRIPT_DIR = Path(__file__).resolve().parent
    LOGS_DIR = Path(SCRIPT_DIR, "logs")
    CONFIG_FILE = Path(SCRIPT_DIR, "config.yaml")

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(
        filename=LOGS_DIR / "discord.log", encoding="utf-8", mode="a"
    )
    file_handler.setLevel(logging.INFO)
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

    # async def run_bot() -> None:
    #     try:
    #         await bot.setup_cogs()  # Load cogs in the bot's event loop
    #         await bot.start(bot_config.token)  # Start the bot
    #     except Exception as e:
    #         logger.error(f"Bot failed to start: {e}")
    #     finally:
    #         await bot.close()

    # asyncio.run(run_bot())


if __name__ == "__main__":
    main()
