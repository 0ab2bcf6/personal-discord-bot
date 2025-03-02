#!/usr/bin/env python3
"""
huggingface cog class
"""

# Standard library imports
import asyncio
import httpx
import re
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

# TODO better handle parameters

class HuggingFace(BaseCog):
    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self.model: str = self._config.model 
        self.api_url: str = self._config.api_url + f"{self.model}"
        self.headers = {"Authorization": f"Bearer {self._config.token}"}

    async def generate_response(self, prompt: str, max_tokens: Optional[int] = 2048) -> str:
        """Generates a response from Hugging Face model."""
        refined_prompt = (
            f"<|system|>You are a precise, factual assistant. Answer only what is asked, "
            f"avoid speculation, and stick to verified information. If unsure, say so.<|user|>{prompt}<|assistant|> "
        )

        payload = {
            "inputs": refined_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.1,       # creativity
                "top_p": 0.5,            # sampling
                "do_sample": False,       # sampling for variety
                "return_full_text": False  # Return only generated text
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # 30s timeout
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()  # Raises exception for 4xx/5xx status codes

                data = response.json()
                if not data or not isinstance(data, list) or not data[0]:
                    await self.logger.log_warning(self, "Empty or invalid API response.")
                    return "Hmm, I didn’t get a proper response from the AI."

                raw_text = data[0].get("generated_text", "No response received.")

                cleaned_text = re.sub(r"\n{2,}", "\n", raw_text).strip()
                cleaned_text = re.sub(r"<\|.*?\|>", "", raw_text)
                cleaned_text = re.sub(r"\n{2,}", "\n", cleaned_text).strip()

                if max_tokens and len(cleaned_text) > max_tokens:
                    cleaned_text = cleaned_text[:max_tokens].rsplit(" ", 1)[
                        0] + "..."
                return cleaned_text

        except httpx.RequestError as e:
            error_msg = f"Network error contacting Hugging Face API: {str(e)}"
            await self.logger.log_error(self, error_msg)
            return "Sorry, I couldn’t reach the AI service right now."
        except httpx.HTTPStatusError as e:
            error_msg = f"API error {e.response.status_code}: {e.response.text}"
            await self.logger.log_error(self, error_msg)
            return "Sorry, there was an issue with the AI service."
        except Exception as e:
            await self.logger.log_error(self, f"Unexpected error: {str(e)}")
            return "Oops, something went wrong generating your response!"

    @commands.command(name="chat", aliases=["hey", "explain"])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def chat_command(self, ctx: commands.Context, *, prompt: str) -> None:
        """Handles the !chat command to talk with the AI."""
        response = await self.generate_response(prompt)
        await ctx.send(response)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
