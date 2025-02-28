#!/usr/bin/env python3
"""
config.py
"""
# Standard library imports
from pathlib import Path
from typing import Any, Dict, List

# Third-party imports
import yaml

# Absolute Path of current file
# pylint: disable=invalid-name
SCRIPT_DIR = Path(__file__).resolve().parent


class Config:
    """represents config.yaml"""

    def __init__(self, config_file: str) -> None:
        with open(config_file, "r", encoding="utf-8") as file:
            config_data: Dict[Any, Any] = yaml.safe_load(file)

        required_keys: List[str] = ["token", "server_id", "cogs"]
        for key in required_keys:
            if key not in config_data:
                raise ValueError(
                    f"Key '{key}' is missing in Config configuration")

        for key, value in config_data.items():
            setattr(self, key, value)

        self.token: str = config_data.get("token", str)
        self.server_id: int = config_data.get("server_id", int)
        self.cogs: Dict[str, CogConfig] = config_data.get("cogs", {})

        for cog_name, cog_data in config_data.get("cogs", {}).items():
            cog = CogConfig(cog_name, cog_data)
            self.cogs[cog_name] = cog


class CogConfig:
    """represents Cog from config.yaml"""

    def __init__(self, name: str, data: Dict[str, Any]) -> None:
        self.name: str = name
        required_keys: List[str] = [
            "enabled",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(
                    f"Key '{key}' is missing in Cog configuration")

        for key, value in data.items():
            if key == "path":
                setattr(self, key, Path(SCRIPT_DIR, value))
            else:
                setattr(self, key, value)

        self.enabled: bool = data.get("enabled", bool)

        if len(data.get("boards", [])) > 0:
            self.boards: List[BoardConfig] = []
            for board_data in data.get("boards", []):
                board = BoardConfig(board_data)
                self.boards.append(board)


class BoardConfig:
    """represents a Board from config.yaml"""

    def __init__(self, data: Dict[str, Any]) -> None:
        required_keys: List[str] = [
            "board",
            "include",
            "url",
            "catalog_url",
            "sub_boards",
            "keywords",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(
                    f"Key '{key}' is missing in Board configuration")

        for key, value in data.items():
            setattr(self, key, value)

        self.board: str = data.get("board", str)
        self.include: bool = data.get("include", bool)
        self.url: str = data.get("url", str)
        self.catalog_url: str = data.get("catalog_url", str)
        self.sub_boards: List[SubboardConfig] = []
        self.keywords: List[str] = data.get("keywords", List[str])

        for sub_board_data in data.get("sub_boards", []):
            new_sub = SubboardConfig(sub_board_data)
            self.sub_boards.append(new_sub)


class SubboardConfig:
    """represent a Subboard from config.yaml"""

    def __init__(self, data: Dict[str, Any]) -> None:
        required_keys: List[str] = ["name", "include"]
        for key in required_keys:
            if key not in data:
                raise ValueError(
                    f"Key '{key}' is missing in SubBoard configuration")

        for key, value in data.items():
            setattr(self, key, value)

        self.name: str = data.get("name", str)
        self.include: bool = data.get("include", bool)
