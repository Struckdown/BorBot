import discord
from discord.ext import commands
import youtube_dl
import asyncio
import functools

# A music cog for BorBot.
# Heavily inspired by https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d#file-music_bot_example-py
# Since I wasn't familiar with ytdl or ffmpeg
# The idea was to create a simple music bot for practice as a non-trivial task

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"	# Get ready to rick-roll myself

class YTDLError(Exception):
	pass


class YTDLSource(discord.PCMVolumeTransformer):
	YTDL_OPTIONS = {
		'format': 'bestaudio/best',
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

	def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
		super().__init__(source, volume)

		self.requester = ctx.author
		self.channel = ctx.channel
		self.data = data

		self.uploader = data.get('uploader')
		self.uploader_url = data.get('uploader_url')
		date = data.get('upload_date')
		self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
		self.title = data.get('title')
		self.thumbnail = data.get('thumbnail')
		self.description = data.get('description')
		#self.duration = self.parse_duration(int(data.get('duration')))
		self.tags = data.get('tags')
		self.url = data.get('webpage_url')
		self.views = data.get('view_count')
		self.likes = data.get('like_count')
		self.dislikes = data.get('dislike_count')
		self.stream_url = data.get('url')

	def __str__(self):
		return '**{0.title}** by **{0.uploader}**'.format(self)

	@classmethod
	async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
		loop = loop or asyncio.get_event_loop()

		partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
		data = await loop.run_in_executor(None, partial)

		if data is None:
			raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

		if 'entries' not in data:
			process_info = data
		else:
			process_info = None
			for entry in data['entries']:
				if entry:
					process_info = entry
					break

			if process_info is None:
				raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

		webpage_url = process_info['webpage_url']
		partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
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
					raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

		return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)




class Song():
	def __init__(self, source: YTDLSource):
		self.source = source
		self.requester = source.requester

	def create_embed():
		pass #TODO


class SongQueue():
	# Simple queue data struct. Pops at index 0, adds to tail at end
	def __init__(self):
		queue = []

	def clear():
		queue.clear()

	def remove(index):
		queue.pop(index)

	def add(song):
		queue.append(song)

	def pop():
		return queue.pop(0)



class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.ctx = None
		self.voiceClient = None
		self.songQueue = SongQueue()

	@commands.command(name="play", brief="Lets play some music", usage="youtubeURL", help="Youtube url")
	async def play(self, ctx, *, search:str):
		'''
		Tries to add a song to the queue and play music.
		'''

		try:
			source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
		except YTDLError as e:
			await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
		else:
			song = Song(source)

		if not self.voiceClient:
			self.voiceClient = await ctx.author.voice.channel.connect()
		try:
			await vc.play(song.source)
		except:
			print("Couldn't find music")
			#await ctx.voice_state.songs.put(song)
			#await ctx.send('Enqueued {}'.format(str(source)))

		#TODO Create embed?
#		await ctx.channel.send(embed=embed)

	@commands.command(name="stop")
	async def stop(self, ctx):
		self.voiceClient.stop()

	@commands.command(name="clear")
	async def clear(self, ctx):
		self.voiceClient.stop()
		self.songQueue.clear()

	@commands.command(name="leave")
	async def leave(self, ctx):
		self.voiceClient.stop()
		self.songQueue.clear()
		self.voiceClient.disconnect()
		self.voiceClient = None
