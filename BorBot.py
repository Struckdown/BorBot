# BorBot.py, a bot for practicing python programming with the Discord API.
# Written by Boris
import os, random, json
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import urllib3
import asyncio
from RPGKit import *
from Music import *

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('DISCORD_SERVER')
GUILD = ""	# Limits this to one guild? Probably can't cache single guild like this
ROLE_MESSAGE_ID = int(os.getenv("DISCORD_ROLE_MESSAGE_ID"))
FIGHTER_ID=int(os.getenv("FIGHTER_ID"))
THIEF_ID=int(os.getenv("THIEF_ID"))
CLERIC_ID=int(os.getenv("CLERIC_ID"))
WIZARD_ID=int(os.getenv("WIZARD_ID"))
STATUS_LOOP_INTERVAL = 5	# seconds between status updates
QUOTE_CHANNEL_ID = int(os.getenv("QUOTE_ID"))

DEBUG = False

intents = discord.Intents().all()
bot = commands.Bot(command_prefix="!", intents=intents)

roles = {
	"⚔️":FIGHTER_ID,
	'🗡️':THIEF_ID,
	'✝️':CLERIC_ID,
	'🔥':WIZARD_ID
}

botStatuses = [
	[discord.ActivityType.playing, "with your heart"],
	[discord.ActivityType.streaming, " StarCraft II"],
	[discord.ActivityType.listening, "the people"],
	[discord.ActivityType.watching, "with great interest"],
	#[discord.ActivityType.custom, "A CUSTOM STATUS?"],	# Don't seem to work?
	[discord.ActivityType.competing, "life"], # Starts with "Competing in"
]

@bot.event
async def on_ready():
	global GUILD
	print(f'{bot.user} has connected to Discord!')
	for guild in bot.guilds:
		print(f'{bot.user} is connected to the following guild:\n'
		f'{guild.name}(id: {guild.id})')

		if guild.name == GUILD_NAME:
			GUILD = guild

	if GUILD == "":
		print("No guild was set correctly!")

	if not os.path.exists("level.json"):
		f = open('level.json', 'w+')
		f.write("{}")
		f.close()

#	loop = asyncio.new_event_loop()  # *new*_event_loop

	await bot.add_cog(RPGKit(bot))
	#bot.add_cog(Music(bot))

	updateBotStatus.start()
	#if not DEBUG:
	#	postDailyQuote.start()


@tasks.loop(seconds=STATUS_LOOP_INTERVAL)
async def updateBotStatus():
	number = random.randint(0, len(botStatuses)-1)
	activity = discord.Activity(type=botStatuses[number][0], name=botStatuses[number][1])
	await bot.change_presence(activity=activity)


@tasks.loop(hours=24)
async def postDailyQuote():
	http = urllib3.PoolManager()
	quote_page = "https://www.reddit.com/r/quotes/top/?t=day"
	r = http.request("GET", quote_page)
	soup = BeautifulSoup(r.data, "html.parser")

	quotes = soup.find("div", attrs={"class":"rpBJOHq2PR60pnwJlUyP0"})	# How does reddit generate these class names? Do they change???
	quote = quotes.find("h3").get_text()

	channel = discord.utils.find(lambda x: x.id == QUOTE_CHANNEL_ID, GUILD.channels)
	await channel.send(quote)


@bot.event
async def on_raw_reaction_add(payload):
	user = payload.member
	emoji = payload.emoji
	msg_id = payload.message_id
	if msg_id != ROLE_MESSAGE_ID:	# Only listen to specific message
		return

	newRoles = user.roles
	if emoji.name in roles:
		newRole = GUILD.get_role(roles[emoji.name])
	else:
		return 	# Do nothing on other roles

	newRoles.append(newRole)
	await user.edit(roles=newRoles)


@bot.event
async def on_raw_reaction_remove(payload):
	user_id = payload.user_id
	emoji = payload.emoji
	msg_id = payload.message_id
	if msg_id != ROLE_MESSAGE_ID:
		return

	user = discord.utils.find(lambda m: m.id == user_id, GUILD.members)
	newRoles = user.roles
	roleToRemove = ""
	if emoji.name in roles:
		roleToRemove = GUILD.get_role(roles[emoji.name])
	else:
		return	# Do nothing on other roles

	roleIndex = -1
	i = 0
	for role in newRoles:
		if role == roleToRemove:
			roleIndex = i
			break
		i += 1
	if roleIndex >= 0:	# Prevents it from trying to pop a role that doesn't exist
		newRoles.pop(roleIndex)
	await user.edit(roles=newRoles)


@bot.command(name="hexagon", brief="Send an image with custom text.", usage="text", help="Generates the hexagon image with the given text")
async def hexagon(ctx, text:str):
	img = Image.open("hexagon_base.png")

	d = ImageDraw.Draw(img)
	fontsize = 40
	font = ImageFont.truetype("arial.ttf", fontsize)
	d.text((370,340), text, fill=(0,0,0), font=font)
	img.save('hexagon.png')

	await ctx.channel.send(file=discord.File("hexagon.png"))


@bot.command(name="ask", brief="Answer any question you might have.", usage="[question]", help="Recieve an answer from the bot about whatever questions you might have")
async def magicball(ctx, *, text:str):

	randomReplies = [
	"It is certain.",
	"It is decidedly so.",
	"Without a doubt.",
	"Yes – definitely.",
	"You may rely on it.",
	"As I see it, yes.",
	"Most likely.",
	"Outlook good.",
	"Yes.",
	"Signs point to yes.",
	"Reply hazy, try again.",
	"Ask again later.",
	"Better not tell you now.",
	"Cannot predict now.",
	"Concentrate and ask again.",
	"Don't count on it.",
	"My reply is no.",
	"My sources say no.",
	"Outlook not so good.",
	"Very doubtful.",
	]
	# As in true magic 8-ball style, random replies.
	await ctx.channel.send(random.choice(randomReplies))


@bot.command(name="echo", brief="Talk as the bot", usage="channel text", help="Have the bot say something and deletes your message. Use channel to specify which channel.")
async def echo(ctx, channel:discord.TextChannel, *, text:str):
	guild = ctx.guild
	channelToPost = discord.utils.find(lambda c: c.id == channel.id, guild.channels)
	if channelToPost:
		await ctx.message.delete()
		await channelToPost.send(text)


@bot.command(name="monitor", brief="The bot is always watching", usage="user", help="Begin monitoring this user.")
async def monitor(ctx, user: discord.User):
	
	memeberToMonitor = discord.utils.find(lambda m: m.id == user.id, ctx.guild.members)
	newMessage = memeberToMonitor.nick
	newMessage += " is now being monitored"

	await ctx.channel.send(newMessage)



@bot.event
async def on_message(message):
	if message.author == bot:	# Never process itself
		return

	with open('level.json', 'r') as file:
		data = json.load(file)

	writerID = str(message.author.id)
	if writerID not in data:
		data[writerID] = 1
	else:
		data[writerID] = int(data[writerID]) + 1

	with open("level.json", "w") as file:
		json.dump(data, file)
		file.truncate()

	await bot.process_commands(message)	# Process any commands if possible


@bot.command(name="stats", brief="Shows you a user's stats", usage="user", help="Gives you the amount of times this user has messaged in any chat channel the bot can access.")
async def stats(ctx, user: discord.User):
	message = user.name
	with open("level.json", "r") as file:
		data = json.load(file)
		if str(user.id) not in data:
			message += " has not yet gotten any xp!"
		else:
			xp = int(data[str(user.id)])
			message += " has " + str(data[str(user.id)]) + " xp!"
			if xp > 1000:
				message += " They are ranked as a True Hero. Well done!"
			elif xp > 500:
				message += " They are ranked as a Mighty Wizard. They have begun to comprehend the meaning of the universe!"
			elif xp > 250:
				message += " They are ranked as a High Knight! Sword not included."
			elif xp > 125:
				message += " They are ranked as an Established Guard! Thank you for your contributions!"
			elif xp > 75:
				message += " They are ranked as a Promising Squire! The Council believes in you."
			elif xp > 25:
				message += " They are ranked as a Beginner. Keep on growing!"
			else:
				message += " They do not have any official ranking yet. More research is needed."
	await ctx.channel.send(message)

bot.run(TOKEN)