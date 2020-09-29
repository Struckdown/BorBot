# BorBot.py, a bot for practicing python programming with the Discord API.
# Written by Boris
import os, random
import discord
from dotenv import load_dotenv
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAME = os.getenv('DISCORD_SERVER')
GUILD = ""	# Limits this to one guild? Probably can't cache single guild like this
ROLE_MESSAGE_ID = int(os.getenv("DISCORD_ROLE_MESSAGE_ID"))
FIGHTER_ID=int(os.getenv("FIGHTER_ID"))
THIEF_ID=int(os.getenv("THIEF_ID"))
CLERIC_ID=int(os.getenv("CLERIC_ID"))
WIZARD_ID=int(os.getenv("WIZARD_ID"))

bot = commands.Bot(command_prefix="!")
roles = {
	"⚔️":FIGHTER_ID,
	'🗡️':THIEF_ID,
	'✝️':CLERIC_ID,
	'🔥':WIZARD_ID
}

@bot.event
async def on_ready():
	global GUILD
	print(f'{bot.user} has connected to Discord!')
	for guild in bot.guilds:
		print(f'{bot.user} is connected to the following guild:\n'
		f'{guild.name}(id: {guild.id})')

		if guild.name == GUILD_NAME:
			GUILD = guild


@bot.command(name="roll", help="Lets roll some n-sided dice! Format is !roll 1d20+3d10-5d8+6")
async def diceRoll(ctx, dice:str):
	'''
	A simple dice roller that takes in arguments of the form mdn+C where C is a constant or another mdn expression
	m and n are variables, d is the char 'd'. Also handles subtraction signs.
	Examples:
	!roll 1d5+3
	!roll 10d8-2
	!roll 1d2+1d4-1d6+1d8
	'''

	# TODO: Probably restrict user inputs more? 
	# Reconsider using eval (pretty obvious potential vulnerability)
	# Improve embed formatting?
	# Transition into a seperate .py script probably? This function is pretty verbose and it would be good to keep this .py file high level functions


	# Subfunction: Evaluates an expression of the form 1d20. Or a constant, eg: 5.
	# Returns a list of the values (multiplies by - if passed in that modifier)
	# Valid modifiers are '+' and '-'
	def resolve(expr, modifier):
		if expr == "":
			return []
		results = []
		if "d" not in expr:
			return [eval(modifier+str(expr))]

		newExpr = expr.split("d")
		diceToRoll = int(newExpr[0])
		diceSides = int(newExpr[1])

		if diceSides == 0:
			raise commands.BadArgument(message="Cannot roll dice with 0 sides!")
		for i in range(diceToRoll):
			result = random.randint(1, diceSides)
			result = eval(modifier + str(result))
			results.append(result)

		return results

	results = []
	finalMessage = ""

	currStr = ""
	dice = dice.replace(" ", "")
	modifier = "+"

	for char in dice:
		if char in "+-":
			newValues = resolve(currStr, modifier)
			if modifier != char:
				modifier = char
			results.extend(newValues)
			finalMessage += "Rolled " + str(newValues) + " on " + currStr + " **(" + str(sum(newValues)) + ")** \n"
			currStr = ""
		else:
			currStr += char
	newValues = resolve(currStr, modifier)
	results.extend(newValues)
	finalMessage += "Rolled " + str(newValues) + " on " + currStr + " **(" + str(sum(newValues)) + ")** \n"
	finalResult = sum(results)

	# Create embed and post it
	rollEmbed = discord.Embed(title="Roll Results", description=finalMessage, color=0xde6b00)
	rollEmbed.add_field(name="Final Result", value=str(finalResult), inline=False)
	await ctx.channel.send(embed=rollEmbed)


@diceRoll.error
async def info_error(ctx, error):
	if isinstance(error, commands.BadArgument):
		await ctx.send(error)


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


@bot.command(name="hexagon", help="Send an image with custom text. Format is !hexagon text")
async def hexagon(ctx, text:str):
	img = Image.open("hexagon_base.png")

	d = ImageDraw.Draw(img)
	fontsize = 40
	font = ImageFont.truetype("arial.ttf", fontsize)
	d.text((370,340), text, fill=(0,0,0), font=font)
	img.save('hexagon.png')

	await ctx.channel.send(file=discord.File("hexagon.png"))


bot.run(TOKEN)