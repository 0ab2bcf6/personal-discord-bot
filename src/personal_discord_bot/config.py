#!/usr/bin/env python3
# type: ignore
"""
config.py
"""

from typing import Any, Dict, List

import yaml


class Config:
    """represents config.yaml"""

    def __init__(self, config_file: str) -> None:
        with open(config_file, "r", encoding="utf-8") as file:
            config_data: Dict[str, Any] = yaml.safe_load(file)

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
            setattr(self, key, value)

        self.enabled: bool = data.get("enabled", bool)

        if len(data.get("boards", [])) > 0:
            self.boards: List[BoardConfig] = []
            for board_data in data.get("boards", []):
                board = BoardConfig(board_data)
                self.boards.append(board)