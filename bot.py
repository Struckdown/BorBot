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

	# Refactor to allow this subfunction to return messages to build a nicer message format

	def resolve(expr, modifier):
		if expr == "":
			return 0
		total = 0
		if "d" in expr:
			newExpr = expr.split("d")

			diceToRoll = int(newExpr[0])
			diceSides = int(newExpr[1])
			for i in range(diceToRoll):
				result = random.randint(1, diceSides)
				total += result
				print("Rolled: " + str(result) + " on " + expr)
			total = eval(modifier+str(total))

		else:
			return eval(modifier+str(expr))
		return total

	finalResult = 0
	finalMessage = ""


	currStr = ""
	dice = dice.replace(" ", "")
	modifier = "+"

	for char in dice:
		if char in "+-":
			newValue = resolve(currStr, modifier)
			if modifier != char:
				modifier = char
			finalResult += newValue
			finalMessage += "Rolled " + str(newValue) + " on " + currStr + "\n"
			currStr = ""
		else:
			currStr += char
	newValue = resolve(currStr, modifier)
	finalResult += newValue
	finalMessage += "Rolled " + str(newValue) + " on " + currStr + "\n"

	await ctx.channel.send("```" + finalMessage + "```")
	await ctx.channel.send("```Final result: " + str(finalResult) + "```")


bot.run(TOKEN)

