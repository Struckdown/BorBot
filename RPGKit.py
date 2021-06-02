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


	@commands.command(name="hit", brief="Draws hit locations for a monster", usage="Add a monster to specify subtype", help="Returns two monster hit-locations")
	async def getHitLocation(self, ctx, monsterType: str="human", number=2):
		coreLocations = {
			"Heart": "-13 to hit; Hit: Enemy dies immediately",
			"Jaw": "-2 to hit at range; Hit - Silence; Fail - Become Blinded if adjacent",
			"Eyes": "-5 to hit; attack turns into crit; Hit - foe gains -2 to all attacks",
			"Backside": "Hit - Reposition enemy up to 10ft away if adjacent",
			"Temple": "-4 to hit, Crit on Nat 18+; Hit - Foe is Stunned",
		}

		animalLocations = {# Locations like on an owlbear. Something that doesn't wield weapons but is otherwise quadrupedal-like
			"Shoulderblade": "+5 to hit; Hit - Deal 2 less damage",
			"Shinbone": "Hit - Foe loses 5ft of movement permanently",
			"Pelvis": "Reposition yourself up to 5ft",
			"Knee": "-2 to hit; Hit - Foe gains -5ft movement permanently",
			"Chest": "Hit - Foe loses 1AC permanently",
			"Inner Thigh": "-2 to hit; Hit - Foe is Frightened for one round",
			"Hamstring": "-2 to hit at range; Hit - Foe falls prone; Fail - You are pushed back 5ft if adjacent",
			"Gut": "-2 to hit, -4 at range instead; Hit - Stun; Fail - Opportunity attack from foe if within foe's reach",
			"Elbow": "-2 to hit at range; Hit - Foe movement is 0ft for one round",
			"Knee Joint": "-4 to hit; Hit - Paralyze for one round if creature is smaller than you, else deal extra 1d6 damage",
			"Foot": "Hit - Foe gains disadvantage on next action; Fail - You become disadvantaged instead",
			"Ears": "-2 to hit at range; Hit - Foe is deafened; Fail - You fall prone",
			"Gonads": "-6 to hit; Hit - Paralyze for one round",
			"Ribs": "+4 to hit, +2 instead at range; Fail - Become disarmed if within foe's reach",
		}
		humanoidLocations = {
			"Primary Hand": "-2 to hit at range; Hit - Foe attacks with disadvantage on next attack",
			"Secondary Hand": "+2 to hit; Hit - Deal extra 1d4 damage",
			"Forearm": "-2 to hit at range; Hit - Disarm foe; Fail - Become disarmed if adjacent",
		}
		humanoidLocations.update(animalLocations)
		animalLocations.update(
				{
					"Claws": "-2 to hit; Hit - foe gains disadvantage on next action",
					"Exposed hide": "+2 to hit; Hit - foe charges 10ft forward" 
				}
			)
		sharkLocations = {	# fish like locations
			"Snout": "+4 to hit; Fail - The laser eyes activate! Take 2d4+3 damage",
			"Pectoral Fin": "-2 to hit; Hit - The shark gains disadvantage on its next attack",
			"Gill slits": "-4 to hit; Hit - deal an extra d8 of damage",
			"Dorsal fins": "+2 to hit; The shark attacks back with disadvantage",
			"Ventral surface": "+4 to hit; deal 2 less damage",
			"Eyes": "-5 to hit; Hit - The shark loses laser eye attack",
			"Belly": "Attack with advantage; Hit - The shark bites back with advantage",
			"Tail Fin": "+4 to hit; Fail - The shark whips its tail into your face, take 1d6+3 damage"
			"Teeth": "+2 to hit; Fail - The shark bites back! Become disarmed",
		}
		octopusLocations = {
			"Elongated sucker": "+4 to hit; Hit - become disarmed",
			"Doral mantal cavity": "+2 to hit; Hit - Foe repositions 5ft",
			"Hidden ink sac": "+2 to hit; Fail - become blinded until the end of your next turn",
			"Kidney": "-4 to hit; Hit - attack another drawn hit location",
			"Skull": "-4 to hit; Hit - Future attacks draw an additional location",
			"Poison gland": "-2 to hit; Hit - Disable poison ability of foe, become Poisoned",
			"Slimy tentacle": "Hit - deal extra 1d4 damage if using slashing weapon",
			"Pulsating tentacle": "Hit - deal extra 1d4 damage if using slashing weapon",
			"Massive tentacle": "+2 to hit; Hit - DC 12 Str saving throw or become grappled",
			"Flailing tentacle": "-2 to hit; Hit - deal an extra 2 damage",
			"Writhing tentacle": "+2 to hit; Fail - fall prone",
		}


		monsterTypes = {"shark":sharkLocations, "octopus":octopusLocations, "owlbear":animalLocations, "human":humanoidLocations, "goblin":humanoidLocations}
		hitLocations = {}
		hitLocations.update(coreLocations)
		monsterType = ""
		for monster in monsterTypes:
			if LevenshteinFunction(monsterType.lower(), monster) <= 2:	# allows for mispellings and minor typos, as well as pluralizations (eg goblin vs goblins)
				monsterType = monster
				break
		if monsterType == "":
			monsterType = "human"
		hitLocations.update(monsterTypes[monsterType])	# Adds new locations to the hitlocation deck

		locations = random.sample(sorted(hitLocations),number)

		finalMessage = locations[0] + "\nOR\n" + locations[1]
		hitEmbed = discord.Embed(title="Hit Locations", description="Pick a location to hit!", color=0xFF4B45)
		for location in locations:
			hitEmbed.add_field(name=location, value=hitLocations[location], inline=False)	
		await ctx.channel.send(embed=hitEmbed)


# Returns Levenshtein distance between two strings, aka the Edit distance.
# This is the amount of character changes needed to make to a string to convert it from a to b
def LevenshteinFunction(a, b):
	if len(b) == 0:
		return len(a)
	elif len(a) == 0:
		return len(b)
	elif a[0] == b[0]:
		return LevenshteinFunction(a[1:], b[1:])
	else:
		return 1 + min(LevenshteinFunction(a[1:], b), LevenshteinFunction(a, b[1:]), LevenshteinFunction(a[1:], b[1:]))