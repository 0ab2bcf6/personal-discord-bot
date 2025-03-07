# Personal Discord Bot

[![License](https://img.shields.io/github/license/0ab2bcf6/personal-discord-bot)](https://github.com/0ab2bcf6/personal-discord-bot/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)

A barebones structure for a self-hosted Discord bot with custom features, designed for easy individualization and extensibility.

## Table of Contents
- [Personal Discord Bot](#personal-discord-bot)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Virtual Environment](#virtual-environment)
    - [Local Installation](#local-installation)
  - [Configuration](#configuration)
  - [Building and Testing](#building-and-testing)
    - [Static Analysis](#static-analysis)
    - [Unit Testing](#unit-testing)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Modular Cog System**: Easily add or remove features via cogs (e.g., monitor, reaction roles, movie database).
- **Customizable Configuration**: Uses a YAML file for bot and cog settings.
- **Reaction Roles**: Assign roles based on user reactions to specific messages.
- **Activity Monitoring**: Track user inactivity and manage roles accordingly.
- **HuggingFace Integration**: Leverage AI models like Llama for custom functionality.
- **Developer-Friendly**: Includes static analysis and unit testing setup with `mypy`, `pylint`, `flake8`, and `pytest`.

## Requirements

- Python 3.12 or higher
- A Discord bot token (obtainable from the [Discord Developer Portal](https://discord.com/developers/applications))
- A HuggingFace token, if used (obtainable from [HuggingFace.co](https://huggingface.co))
- Dependencies listed in `pyproject.toml`

## Building
Your project can be tested by installing it locally.

### Local Installation
To make the tests function properly, it is important to install the project
locally.
The following command can be used to install the project in an editable
state:
```
python -m pip install -e ".[dev]"
```
Use the option `[dev]` to also install the optional development requirements.

### Virtual Environment
If you want to avoid altering your environment, you can initializing a local
virtual environment:
```
python -m virtualenv venv
```
Followed by this command on Linux:
```
source venv/bin/activate
```
And on Windows:
Powershell:
```
venv\Scripts\Activate.ps1
```
cmd:
```
venv\Scripts\Activate.bat
```