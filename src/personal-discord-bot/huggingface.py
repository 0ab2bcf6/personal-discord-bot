#!/usr/bin/env python3
"""
HuggingFace cog class
"""

# Standard library imports
import httpx
import io
import re
from typing import TYPE_CHECKING, Any, Dict, Optional

# Third-party library imports
import discord
from discord.ext import commands

# Local application imports
from .basecog import BaseCog
from .config import CogConfig

# Conditional imports for type checking
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any


class HuggingFace(BaseCog):
    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self.base_api_url: str = self._config.api_url  # type: ignore
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {self._config.token}"}  # type: ignore

    async def generate_response(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generates a response from the DeepSeek R1 model."""

        api_url: str = self.base_api_url + \
            self._config.text_to_text["model"]  # type: ignore
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.6,
                "top_p": 0.95, 
                "do_sample": True,
                "return_full_text": False
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # 30s timeout
                response = await client.post(api_url, headers=self.headers, json=payload)
                response.raise_for_status()

                data = response.json()
                if not data or not isinstance(data, list) or not data[0]:
                    await self.logger.log_warning(self, "Empty or invalid API response.")
                    return "Hmm, I didn’t get a proper response from the AI."

                raw_text = data[0].get(
                    "generated_text", "No response received.")
                cleaned_text = re.sub(r"\n{2,}", "\n", raw_text).strip()

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

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """Generates an image from a text prompt using DALL-E Mini."""

        api_url: str = self.base_api_url + \
            self._config.text_to_image["model"] # type: ignore
        payload = {
            "inputs": prompt,
        }

        try:
            # 30s timeout is plenty
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)
                response.raise_for_status()  # Raises exception for 4xx/5xx status codes

                # API returns image as raw bytes
                image_bytes = response.content
                return image_bytes

        except httpx.RequestError as e:
            error_msg = f"Network error contacting Hugging Face API: {str(e)}"
            await self.logger.log_error(self, error_msg)
            return None
        except httpx.HTTPStatusError as e:
            error_msg = f"API error {e.response.status_code}: {e.response.text}"
            await self.logger.log_error(self, error_msg)
            return None
        except Exception as e:
            await self.logger.log_error(self, f"Unexpected error: {str(e)}")
            return None

    @commands.command(name="imagine", aliases=["img", "draw"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def imagine_command(self, ctx: commands.Context, *, prompt: str) -> None:
        """Handles the !imagine command to generate a fun image."""

        if not self._config.text_to_image["enabled"]:  # type: ignore
            await ctx.send("Text-to-Image ist momentan deaktiviert ...")
            return

        await ctx.send("Whipping up something silly, hang on...")

        image_bytes = await self.generate_image(prompt)
        if image_bytes:
            # Convert bytes to a Discord file object
            image_file = discord.File(fp=io.BytesIO(
                image_bytes), filename="silly_image.png")
            await ctx.send(file=image_file)
        else:
            await ctx.send("Oops, couldn’t make an image this time!")

    @commands.command(name="chat", aliases=["hey", "explain"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def chat_command(self, ctx: commands.Context, *, prompt: str) -> None:
        """Handles the !chat command to talk with the AI."""

        if not self._config.text_to_text["enabled"]:  # type: ignore
            await ctx.send("Text-to-Text ist momentan deaktiviert ...")
            return

        response = await self.generate_response(prompt)
        await ctx.send(response)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
