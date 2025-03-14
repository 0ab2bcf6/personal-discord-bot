#!/usr/bin/env python3
"""
Copyright (c) 2019 Valentin B.

A simple music bot written in discord.py using youtube-dl.

Though it's a simple example, music bots are complex and require much time and knowledge until they work perfectly.
Use this as an example or a base for your own bot and extend it as you want. If there are any bugs, please let me know.

Requirements:

Python 3.5+
pip install -U discord.py pynacl youtube-dl

You also need FFmpeg in your PATH environment variable or the FFmpeg.exe binary in your bot's directory on Windows.
"""

# Standard library imports
import asyncio
import functools
import itertools
import math
import random

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, TypeVar, Union

# Third-party imports
import discord
from discord.ext import commands
from async_timeout import timeout
import yt_dlp as youtube_dl

# Local application imports
from .basecog import BaseCog
from .config import CogConfig

# Conditional imports for type checking
if TYPE_CHECKING:
    from .bot import MyBot
else:
    MyBot = Any

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'cookiefile': './cookies.txt',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: Dict[str, Any], volume: float = 0.5) -> None:
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        # ytdl_options = cls.YTDL_OPTIONS.copy()
        # ytdl_options['cookiefile'] = config_path  # Set dynamically

        # self.ytdl = youtube_dl.YoutubeDL(ytdl_options)

        self.channel_id: int = None  # this does nothing

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date: str = data.get('upload_date', '')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration', '0')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self) -> str:
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, config_path: str, search: str, *, loop: asyncio.BaseEventLoop = None)-> Any:
        # set path/to/cookies.txt dynamically
        ytdl_options = cls.YTDL_OPTIONS.copy()
        ytdl_options['cookiefile'] = config_path
        ytdl = youtube_dl.YoutubeDL(ytdl_options)

        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(
                'Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(
                    'Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(
                        'Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int) -> str:
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration_as_str: List[str] = []
        if days > 0:
            duration_as_str.append('{} days'.format(days))
        if hours > 0:
            duration_as_str.append('{} hours'.format(hours))
        if minutes > 0:
            duration_as_str.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration_as_str.append('{} seconds'.format(seconds))

        return ', '.join(duration_as_str)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self) -> discord.Embed:
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(
                                   self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item: int | slice) -> 'Song' | List['Song']:
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            song: Union[Song, List[Song]] = self._queue[item]
            return song

    def __iter__(self) -> Iterator['Song']:
        return self._queue.__iter__()

    def __len__(self) -> int:
        return self.qsize()

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self) -> None:
        self.audio_player.cancel()

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        self._loop = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    @property
    def is_playing(self) -> None:
        return self.voice and self.current

    async def audio_player_task(self) -> None:
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(BaseCog):
    def __init__(self, bot: MyBot, config: CogConfig) -> None:
        super().__init__(bot, config)
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self) -> Any:
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                'This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context) -> None:
        """Joins a voice channel."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None) -> None:
        """Summons the bot to a voice channel.

        If no channel was specified, it joins your channel.
        """

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not channel and not ctx.author.voice:
            raise VoiceError(
                'You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        return

    @commands.command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context) -> Any:
        """Clears the queue and leaves the voice channel."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]
        return

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int) -> Any:
        """Sets the volume of the player."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))
        return

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context) -> None:
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    async def _pause(self, ctx: commands.Context) -> None:
        """Pauses the currently playing song."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')
        return

    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context) -> None:
        """Resumes a currently paused song."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context) -> None:
        """Stops playing song and clears the queue."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        ctx.voice_state.songs.clear()

        if not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context) -> None:
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1) -> None:
        """Shows the player's queue.

        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(
                i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context) -> None:
        """Shuffles the queue."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int) -> None:
        """Removes a song from the queue at a given index."""

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context) -> None:
        """Loops the currently playing song.

        Invoke this command again to unloop the song.
        """

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str) -> None:
        """Plays a song.

        If there are songs in the queue, this will be queued until the
        other songs finished playing.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if self._config.channel_id is None or ctx.channel.id != self._config.channel_id:
            return  # ignore any commands not in the specific channel

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, str(self._config.path), search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context) -> None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError(
                'You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError(
                    'Bot is already in a voice channel.')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.wait_until_ready()
        await self.logger.log_info(self, "loaded.")
