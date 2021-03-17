import discord, random, json
from discord.ext import commands

# An RPG cog for BorBot.
# Features a dice roller and a simple character generator.

class RPGKit(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Subfunction for roll command: Evaluates an expression of the form 1d20. Or a constant, eg: 5.
	# Returns a list of the values (multiplies by - if passed in that modifier)
	# Valid modifiers are '+' and '-'
	def resolve(self, expr, modifier):
		if expr == "":
			return []
		results = []
		if "d" not in expr:
			if modifier == "+":
				return [int(expr)]
			else:
				return [0-int(expr)]

		# "has a d seperator, make some dice rolls"
		newExpr = expr.split("d")
		diceToRoll = int(newExpr[0])
		diceSides = int(newExpr[1])

		if diceToRoll > 1000:
			raise commands.BadArgument(message="Cannot roll more than 1000 dice in a single chunk.")

		if diceSides == 0:
			raise commands.BadArgument(message="Cannot roll dice with 0 sides!")
		for i in range(diceToRoll):
			result = random.randint(1, diceSides)
			if modifier == "-":
				result = int(result) * -1
			else:
				result = int(result)
			results.append(result)

		return results

	@commands.command(name="roll", brief="Lets roll some n-sided dice!", usage="x 'd' y [+C...]", help="x is an integer, 'd' is a literal, y is an integer >0, C is a constant")
	async def diceRoll(self, ctx, dice:str):
		'''
		A simple dice roller that takes in arguments of the form mdn+C where C is a constant or another mdn expression
		m and n are variables, d is the char 'd'. Also handles subtraction signs.
		Examples:
		!roll 1d5+3
		!roll 10d8-2
		!roll 1d2+1d4-1d6+1d8
		'''

		# Initial check for valid input
		for char in dice:
			if char not in "1234567890d+-":
				await ctx.channel.send("Please check your formatting and try again. Should be xdy, eg '!roll 1d6'")
				return

		results = []
		finalMessage = ""

		currStr = ""
		dice = dice.replace(" ", "")
		modifier = "+"

		for char in dice:
			if char in "+-":
				try:
					newValues = self.resolve(currStr, modifier)
				except Exception as e:
					await ctx.channel.send(e)
					return

				if modifier != char:
					modifier = char
				results.extend(newValues)
				finalMessage += "Rolled " + str(newValues) + " on " + currStr + " **(" + str(sum(newValues)) + ")** \n"
				currStr = ""
			else:
				currStr += char
		try:
			newValues = self.resolve(currStr, modifier)
		except Exception as e:
			await ctx.channel.send(e)
			return
		results.extend(newValues)
		finalMessage += "Rolled " + str(newValues) + " on " + currStr + " **(" + str(sum(newValues)) + ")** \n"
		finalResult = sum(results)

		# Create embed and post it
		# TODO: Improve embed formatting?
		rollEmbed = discord.Embed(title="Roll Results", description=finalMessage, color=0xde6b00)
		rollEmbed.add_field(name="Final Result", value=str(finalResult), inline=False)
		await ctx.channel.send(embed=rollEmbed)



	@commands.command(name="generate", help="Generates a simple random RPG character")
	async def generateCharacter(self, ctx):
		with open('character.json', 'r') as file:
			data = json.load(file)
		race = data["races"]
		classes = data["classes"]
		activity = data["activities"]
		aspiration = data["aspirations"]
		finalMessage = "Your new character: " + random.choice(race) + " " + random.choice(classes) + " with a passion for " + random.choice(activity) + ". "
		finalMessage += "They aspire to " + random.choice(aspiration) + " and hope to one day " + random.choice(aspiration) + "."
		# Your new character is [an elf] [bard] with a passion for [stealing]. They aspire to [] and hope to one day [].
		await ctx.channel.send(finalMessage)