import discord
import asyncio
import yt_dlp
import random
import aiohttp
import re
from discord.ext import commands
from collections import deque

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# YouTube audio download options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# Server-specific queue and playback state management
class ServerPlaybackState:
    def __init__(self):
        self.queue = deque()
        self.history = deque(maxlen=50)  # Keep track of recently played songs
        self.repeat_mode = 'off'  # 'off', 'song', or 'queue'
        self.current_song = None
        self.karaoke_mode = False

server_states = {}

class LyricsFetcher:
    @staticmethod
    async def fetch_lyrics(title):
        """
        Fetch lyrics from a public API
        Ensures minimal use of copyrighted content
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Use a public lyrics API
                search_url = f"https://api.lyrics.ovh/v1/{title.split('-')[0]}/{title.split('-')[-1]}"
                async with session.get(search_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Truncate lyrics to avoid copyright issues
                        lyrics = data.get('lyrics', 'Lyrics not found')
                        
                        # Limit to a reasonable excerpt
                        lyrics_lines = lyrics.split('\n')
                        limited_lyrics = '\n'.join(lyrics_lines[:20])
                        
                        return f"Lyrics excerpt for {title}:\n{limited_lyrics}"
                    else:
                        return f"Could not find lyrics for {title}"
            except Exception as e:
                return f"Error fetching lyrics: {str(e)}"

class KaraokeProcessor:
    @staticmethod
    def generate_karaoke_lyrics(lyrics):
        """
        Create a simple karaoke-style display
        Replaces words with underscores, preserving structure
        """
        if not lyrics:
            return "No lyrics available for karaoke"
        
        # Replace words with underscores, keeping punctuation and structure
        def mask_words(line):
            return ' '.join(['_' * len(word) if word.isalpha() else word for word in line.split()])
        
        # Process lyrics
        masked_lines = [mask_words(line) for line in lyrics.split('\n')]
        return '\n'.join(masked_lines)

# Rest of the previous bot code remains the same, with these additions:

@bot.command(name='lyrics', help='Fetch lyrics for the current song')
async def lyrics(ctx):
    server_id = ctx.guild.id
    
    if server_id not in server_states:
        await ctx.send("No song is currently playing.")
        return
    
    state = server_states[server_id]
    
    if not state.current_song:
        await ctx.send("No song is currently playing.")
        return
    
    # Fetch lyrics
    song_title = state.current_song['title']
    lyrics_text = await LyricsFetcher.fetch_lyrics(song_title)
    
    # Send lyrics in chunks if too long
    max_length = 1900  # Discord message length limit
    for i in range(0, len(lyrics_text), max_length):
        await ctx.send(lyrics_text[i:i+max_length])

@bot.command(name='karaoke', help='Toggle karaoke mode')
async def karaoke(ctx):
    server_id = ctx.guild.id
    
    if server_id not in server_states:
        server_states[server_id] = ServerPlaybackState()
    
    state = server_states[server_id]
    
    # Toggle karaoke mode
    state.karaoke_mode = not state.karaoke_mode
    
    if state.karaoke_mode:
        # If current song exists, generate karaoke lyrics
        if state.current_song:
            song_title = state.current_song['title']
            lyrics_text = await LyricsFetcher.fetch_lyrics(song_title)
            karaoke_lyrics = KaraokeProcessor.generate_karaoke_lyrics(lyrics_text)
            await ctx.send(f"Karaoke Mode ON for {song_title}:\n{karaoke_lyrics}")
        else:
            await ctx.send("Karaoke Mode ON. No current song.")
    else:
        await ctx.send("Karaoke Mode OFF")

# The rest of the previous bot implementation remains the same
# (Keep all the previous commands like play, repeat, shuffle, etc.)

# Replace 'YOUR_BOT_TOKEN' with your actual Discord bot token
bot.run('DISCORD_TOKEN')
