# BorBot.py, a bot for practicing python programming with the Discord API.
# Written by Boris
import os, random
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_SERVER')

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        print(f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})')

        if guild.name == GUILD:
            break


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


bot.run(TOKEN)