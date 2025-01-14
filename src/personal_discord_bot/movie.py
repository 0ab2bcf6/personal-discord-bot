#!/usr/bin/env python3
# flake8: noqa: E501
# pylint: skip-file
# type: ignore
"""
movie cog class
"""

import sqlite3

from logging import Logger
from pathlib import Path
from typing import Dict

from discord.ext import commands, tasks

from .config import CogConfig

# Absolute Path of current file
# pylint: disable=invalid-name
SCRIPT_DIR = Path(__file__).resolve().parent


class Movie(commands.Cog):
    """movie cog"""

    def __init__(self, bot, config: CogConfig) -> None:
        self.bot = bot
        self.logger: Logger = bot.logger
        self._config: CogConfig = config

        self.channel_id: int = self._config.channel_id

        db_path = Path(SCRIPT_DIR, self._config.path)

        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.logger.info(
                f"{self.__cog_name__}: Connection to database {self._config.path} successful.")
        except sqlite3.Error as e:
            self.conn = None
            self.logger.error(
                f"{self.__cog_name__}: Error connecting to database {self._config.path}: {e}!"
            )

    @commands.command(name="film", aliases=['filme', 'movies', 'movie', 'movie_suggestion'], help="Lass Dir Filmvorschläge geben: !film [genre] [min. rating] [anzahl]")
    async def suggest_movies(
        self,
        ctx: commands.Context,
        genre: str = None,
        min_rating: float = 4.0,
        top_n: int = 5,
    ) -> None:
        """suggest top n movies that fit the genre and mininum rating filters"""

        if self.channel_id is None or ctx.channel.id != self.channel_id:
            return  # ignore any commands not in the specific channel

        if not self._check_genre(genre):
            await ctx.send(f"Genre '{genre}' is not an entry in the imdb database! (Action, History, Film-Noir ...)")
            return

        if not (0 <= min_rating <= 10):
            await ctx.send("Minimum rating must be a float between 0 and 10.")
            return

        if not (0 <= top_n <= 30):
            await ctx.send("Top N must be an integer between 0 and 30.")
            return

        if self.conn is None:
            await ctx.send("Bot is currently not connected to a database!")
            return

        rating_query = f"""SELECT *
                        FROM TitleRatings tr
                        WHERE CAST(tr.averageRating AS REAL) >= {min_rating}
                        AND CAST(tr.numVotes AS INTEGER) >= 50"""

        movie_query = f"""SELECT *
                        FROM TitleBasics tb
                        WHERE (tb.titleType = 'movie' OR tb.titleType = 'tvMovie')
                        AND tb.genres LIKE '%{genre}%'"""

        sugg_query = f"""SELECT * FROM (SELECT tbo.tconst, tbo.primaryTitle, tro.averageRating
                        FROM ({movie_query}) tbo
                        JOIN ({rating_query}) tro ON tbo.tconst = tro.tconst
                        ORDER BY RANDOM() LIMIT {top_n}) ts ORDER BY ts.averageRating DESC;"""

        self.cursor.execute(sugg_query)
        results = self.cursor.fetchall()

        suggestions = "\n".join(
            [f"{row[1]} (Rating: {row[2]}, url: {self._imdb_url(row[0])}/)" for row in results])

        await ctx.send(f"Top {top_n} movies in {genre} by rating:\n{suggestions}")

    def _check_genre(self, genre: str) -> bool:
        """checks if input genre is in imdb genre list"""

        COMMON_GENRES = [
            "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Documentary",
            "Drama", "Family", "Fantasy", "Film-Noir", "History", "Horror", "Music", "Musical",
            "Mystery", "Romance", "Sci-Fi", "Sport", "Thriller", "War", "Western"
        ]

        return genre in COMMON_GENRES

    def _imdb_url(self, tconst: str) -> str:
        """returns imdb url for given imdb id tconst"""
        IMDB_BASE_URL = "https://www.imdb.com/title/"
        return f"{IMDB_BASE_URL}{tconst}"

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """execute when ready"""
        await self.bot.wait_until_ready()
        self.logger.info(f"{self.__cog_name__} loaded.")
