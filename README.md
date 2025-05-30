# Personal Discord Bot

[![License](https://img.shields.io/github/license/0ab2bcf6/personal-discord-bot)](https://github.com/0ab2bcf6/personal-discord-bot/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)

A barebones structure for a self-hosted Discord bot with custom features, designed for easy individualization and extensibility.

## Table of Contents
- [Personal Discord Bot](#personal-discord-bot)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Configuration](#configuration)
  - [Installation](#installation)
    - [Virtual Environment](#virtual-environment)
    - [Local Installation](#local-installation)
  - [Usage](#usage)
  - [License](#license)

## Features

- **Modular Cog System**: Easily add or remove features via cogs (e.g., monitor, reaction roles, music).
- **Customizable Configuration**: Uses a YAML file for bot and cog settings.
- **Music Bot Integration**: Uses yt-dlp to stream audio to a discord channel. 
- **Reaction Roles**: Assign roles based on user reactions to specific messages.
- **Activity Monitoring**: Track user inactivity and manage roles accordingly.
- **HuggingFace Integration**: Leverage AI models from HuggingFace for custom functionality.

## Requirements

- Python 3.12 or higher
- Dependencies listed in `pyproject.toml`. The dependencies are automatically installed when installing your project locally using pip
- A Discord bot token (obtainable from the [Discord Developer Portal](https://discord.com/developers/applications))
- A HuggingFace token, if used (obtainable from [HuggingFace.co](https://huggingface.co))
- A `src/personal-discord-bot/cookies.txt` (in this exact path) to use the music bot for youtube (detailed instructions listed [here](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp))

## Configuration
The bot uses a `src/personal-discord-bot/config.yaml` file to manage settings for the bot and its cogs. This file should be located in the project root and contain:

- **Bot Settings**: General configuration like the Discord bot token and command prefix
- **Cog Configurations**: A section for each cog, where every cog must include an enabled key (set to true or false) to toggle its functionality. Additional variables specific to each cog (e.g., channel IDs, role IDs, API keys) can be defined as needed. Edit `src/personal-discord-bot/config.yaml` to match your desired setup before starting the bot.

## Installation
To test or run the bot, install the project locally. I recommend creating a virtual environment to isolate dependencies and avoid conflicts with your system’s Python environment.

### Virtual Environment
Set up a virtual environment to keep your project dependencies separate:

```
python3 -m venv botenv
```

Activate the virtual environment:

On Linux/macOS:
```
source botenv/bin/activate
```

And on Windows:
- Powershell:
```powershell
.\botenv\Scripts\Activate.ps1
```
- cmd:
```cmd
botenv\Scripts\activate.bat
```

Once activated, your terminal should show `(botenv)` to indicate the virtual environment is active.

### Local Installation

Now navigate into the root folder and install the project locally:

```
python3 -m pip install -e .
```

## Usage:
To run the bot effectively, follow these steps, especially if hosting it on a remote server:

### Create a Separate Screen Session (Linux/macOS)

Use the `screen` tool to run the bot in a detachable terminal session:

```sh
screen -S discordbot
```

This creates a session named `discordbot`

### Enter the Screen

After creating the screen you should be attached to it. If you’ve detached (see below), reattach to the session:

```sh
screen -r discordbot
```

### Start the Bot
Ensure your virtual environment is active (see Virtual Environment). Run the bot with:

```sh
python3 -m personal-discord-bot
```

### Detach from the Screen 
To leave the bot running in the background, press `Ctrl+A`, then `D`. This detaches you without stopping the bot.

### Exit the Screen (if needed)

To stop the bot and close the session, reattach with `screen -r discordbot`, stop the bot `(Ctrl+C)`, then type:

```sh
exit
```