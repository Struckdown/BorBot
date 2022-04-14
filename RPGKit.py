import discord, random, json
from discord.ext import commands

# An RPG cog for BorBot.
# Features a dice roller and a simple character generator.

class Card():
	def __init__(self, cardName, cardEffect):
		self.cardName = cardName
		self.cardEffect = cardEffect

class Token():
	def __init__(self, tokenName=None, tokenValue:int=0, tokenEffect=None):
		self.name = tokenName
		self.value = int(tokenValue)
		self.effect = tokenEffect

	def print(self):
		finalStr = ""
		if self.name:
			finalStr += self.name + ": "
		if self.value >= 0:	# no need to add -, that is already printed by default
			finalStr += "+"
		finalStr += str(self.value)
		if self.effect:
			finalStr += ", " + self.effect
		return finalStr

class RPGKit(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.currentMonsterDeck = []
		self.currentMonsterDiscard = []
		self.bag = []	# an array of tokens, meant to be shuffled before each draw
		self.bagDefault = []
		for value in [-4, -3, -2, -2, -1, -1, 0, 0, +1]:
			token = Token(None, value, None)
			self.bagDefault.append(token)
		token = Token("Auto Fail", 0, "Your check becomes a total of 0"); self.bagDefault.append(token)
		token = Token("Auto Success", 0, "Your check becomes the DC"); self.bagDefault.append(token)
		token = Token("Unfortunate Luck", +2, "Lose a resource or a health point"); self.bagDefault.append(token)
		token = Token("Character Token", 0, "Activate your character ability"); self.bagDefault.append(token)
		token = Token("Encounter Token", 0, "Encounter ability triggers"); self.bagDefault.append(token)
		token = Token("Encounter Token", 0, "Encounter ability triggers"); self.bagDefault.append(token)
		self.bag = self.bagDefault

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

	@commands.command(name="reset", brief="Reset the bag", help="Resets the bag to the default state")
	async def resetBag(self, ctx):
		self.bag = self.bagDefault


	@commands.command(name="setDefault", usage="!setDefault {[{name:None, value:1, effect:None}, -1, -3, 'autoFail', ...]", brief="Setup a new default configuration", help="Takes in an array of dicts in the format of Token")
	async def setDefaultBag(self, ctx, elements):
		#TODO
		await ctx.channel.send("This function is unsupported at this time. Maybe someday though!")
		return

	@commands.command(name="addToken", usage="!addToken Fire 0 'Take 1 damage'", brief="Adds a new token to the bag")
	async def addTokenToBag(self, ctx, name, value, effect):
		try:
			int(value)
		except:
			await ctx.channel.send("Your second argument must be an integer (eg, !addToken Fire 0 'Take 1 damage'")
			return
		token = Token(name, value, effect)
		self.bag.append(token)
		await ctx.channel.send(token.print() + " was added to the bag")

	@commands.command(name="removeToken", usage="!removeToken 7'", brief="Removes the nth token from the bag")
	async def removeTokenFromBag(self, ctx, position:int):
		if len(self.bag) == 0:
			await ctx.channel.send("The contents of the bag are empty, nothing can be removed!")
			return
		if position > len(self.bag) or position < 0:
			await ctx.channel.send("Please provide a token number to remove between 0 and " + str(len(self.bag)-1))
			return
		token = self.bag.pop(position)
		await ctx.channel.send(token.print() + " was removed from the bag")


	@commands.command(name="draw", brief="Pull from the chaos bag...", usage="!draw X", help="X is the number of tokens to draw")
	async def bagPull(self, ctx, number:int=1):
		'''
		A simple bag of tokens that are to be drawn from.
		'''
		if number < 1 or number > len(self.bag):
			await ctx.channel.send("Please draw up to " + str(len(self.bag)) + " tokens")
			return
		random.shuffle(self.bag)

		if number == 1:
			await ctx.channel.send("```"+self.bag[0].print()+"```")
			return

		result = discord.Embed(title="Tokens drawn", color=0xFF4B45)
		for i in range(number):
			token = self.bag[i]
			name = token.name
			if name == None:
				name = 'Numeric'
			effect = token.effect
			if effect == None:
				effect = ''
			else:
				effect = ", " + effect
			value = token.value
			if value >= 0:
				value = "+" + str(value)
			result.add_field(name=name, value=str(value) + effect, inline=False)	
		await ctx.channel.send(embed=result)

		
	@commands.command(name="peek", brief="Inspect the contents of the bag", usage="!peek", help="Shows the contents of the bag")
	async def showContents(self, ctx):
		finalStr = "```There are " + str(len(self.bag)) + " tokens in the bag.\n"
		i=0
		for token in self.bag:
			finalStr += str(i) + ": "
			finalStr += token.print() + "\n"
			i+=1
		finalStr += "```"
		await ctx.channel.send(finalStr)


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


	@commands.command(name="setupMonster", brief="Sets up the monster deck to pull from", usage="One Str parameter from [animal, humanoid, shark, octopus, demon]", help="Internally sets up monster deck")
	async def setupMonsterLocations(self, ctx, foe: str=""):
		coreLocations = [
			Card("Heart", "-10 to hit; Hit: Enemy dies immediately"),
			Card("Jaw", "-2 to hit at range; Hit - Silence; Fail - Become Blinded if adjacent"),
			Card("Eyes", "-5 to hit; attack turns into crit; Hit - foe gains -2 to all attacks"),
			Card("Backside", "Hit - Reposition enemy up to 10ft away if adjacent"),
			Card("Temple", "-4 to hit, Crit on Nat 18+; Hit - Foe is Stunned"),
		]

		animalLocations = [# Locations like on an owlbear. Something that doesn't wield weapons but is otherwise quadrupedal-like
			Card("Shoulderblade", "+5 to hit; Hit - Deal 2 less damage"),
			Card("Pelvis", "Reposition yourself up to 5ft"),
			Card("Knee", "-2 to hit; Hit - Foe gains -5ft movement permanently"),
			Card("Chest", "Hit - Foe loses 1AC permanently"),
			Card("Inner Thigh", "-2 to hit; Hit - Foe is Frightened for one round"),
			Card("Hamstring", "-2 to hit at range; Hit - Foe falls prone; Fail - You are pushed back 5ft if adjacent"),
			Card("Gut", "-2 to hit, -4 at range instead; Hit - Stun; Fail - Opportunity attack from foe if within foe's reach"),
			Card("Elbow", "-2 to hit at range; Hit - Foe movement is 0ft for one round"),
			Card("Knee Joint", "-4 to hit; Hit - Paralyze for one round if creature is smaller than you, else deal extra 1d6 damage"),
			Card("Foot", "Hit - Foe gains disadvantage on next action; Fail - You become disadvantaged instead"),
			Card("Ears", "-2 to hit at range; Hit - Foe is deafened; Fail - You fall prone"),
			Card("Gonads", "-6 to hit; Hit - Paralyze for one round"),
			Card("Ribs", "+4 to hit, +2 instead at range; Fail - Become disarmed if within foe's reach"),
		]
		humanoidLocations = [
			Card("Primary Hand", "-2 to hit at range; Hit - Foe attacks with disadvantage on next attack"),
			Card("Secondary Hand", "+2 to hit; Hit - Deal extra 1d4 damage"),
			Card("Forearm", "-2 to hit at range; Hit - Disarm foe; Fail - Become disarmed if adjacent"),
		]
		humanoidLocations.extend(animalLocations)
		animalLocations.extend(
				[
					Card("Claws", "-2 to hit; Hit - foe gains disadvantage on next action"),
					Card("Exposed hide", "+2 to hit; Hit - foe charges 10ft forward"),
				]
			)
		sharkLocations = [	# fish like locations
			Card("Snout", "+4 to hit; Fail - The laser eyes activate! Take 2d4+3 damage"),
			Card("Pectoral Fin", "-2 to hit; Hit - The shark gains disadvantage on its next attack"),
			Card("Gill slits", "-4 to hit; Hit - deal an extra d8 of damage"),
			Card("Dorsal fins", "+2 to hit; The shark attacks back with disadvantage"),
			Card("Ventral surface", "+4 to hit; deal 2 less damage"),
			Card("Eyes", "-5 to hit; Hit - The shark loses laser eye attack"),
			Card("Belly", "Attack with advantage; Hit - The shark bites back with advantage"),
			Card("Tail Fin", "+4 to hit; Fail - The shark whips its tail into your face, take 1d6+3 damage"),
			Card("Teeth", "+2 to hit; Fail - The shark bites back! Become disarmed"),
		]
		octopusLocations = [
			Card("Elongated sucker", "+4 to hit; Hit - become disarmed"),
			Card("Doral mantal cavity", "+2 to hit; Hit - Foe repositions 5ft"),
			Card("Hidden ink sac", "+2 to hit; Fail - become blinded until the end of your next turn"),
			Card("Kidney", "-4 to hit; Hit - attack another drawn hit location"),
			Card("Skull", "-4 to hit; Hit - Future attacks draw an additional location"),
			Card("Poison gland", "-2 to hit; Hit - Disable poison ability of foe, become Poisoned"),
			Card("Slimy tentacle", "Hit - deal extra 1d4 damage if using slashing weapon"),
			Card("Pulsating tentacle", "Hit - deal extra 1d4 damage if using slashing weapon"),
			Card("Massive tentacle", "+2 to hit; Hit - DC 12 Str saving throw or become grappled"),
			Card("Flailing tentacle", "-2 to hit; Hit - deal an extra 2 damage"),
			Card("Writhing tentacle", "+2 to hit; Fail - fall prone"),
		]

		demonLocations = [
			Card("Void Blade", "-4 to hit; Hit - If within 10ft, the demon strikes back at -4 with the blade; Fail - You deal an extra 2d6 damage"),
			Card("Fel Thighs", "Hit - Demon moves 30ft (does not trigger AoO)"),
			Card("Cursed Eyes", "Hit - Demon strikes back with disadvantage; Fail - Demon strikes back with advantage"),
			Card("Blighted Shin", "Hit - Demon moves upto 60ft (does not trigger AoO) towards you. If it is beside you, it punts you. Move 10ft or fall prone"),
			Card("Fetid Face", "Hit - Attack becomes a crit. Move the demon 10ft, all enemies in a 15ft cone make a Dex DC 16 check, taking 3d6 acid health damage or half on success"),
			Card("Demonic Femur", "Fail - Reposition yourself 10ft, demon moves upto 30ft to end beside you"),
			Card("The Maw of Death", "Hit - All demon's foes within range 60ft are pulled in 10ft"),
			Card("Defiled Chest", "Gain +2 to hit this location, but attack with disadvantage"),
			Card("Cursed Rump", "Always hits health (only roll to see if it crits). Demon responds by attacking back."),
			Card("Unsightly Mandible", "Fail: Take 2d4+2 psychic health damage if within 15ft"),
			Card("Rotting Wings", "Reposition demon 10ft, take 1d6+2 fire damage to armor if within 5ft during any point of the movement"),
			Card("Flaming Skull", "Take 1d6+2 fire damage to armor; Hit - Take 1d6+2 fire damage to health as well"),
			Card("Forbidden Backside", "If you have no armor points, gain advantage on this attack, else gain disadvantage"),
			Card("Grotesque Hoof", "-2 to hit"),
			Card("Unholy Chest", "+2 to hit; Hit - Demon attempts a grapple check against you"),
			Card("Corrupted Arms", "Crits on nat 18+, always hits armor. Fail - Take 1d6+2 armor damage. This reaction cannot hurt health"),
			Card("Abhorid Protrusions", "Crits hit armor points first at this location"),
			Card("Curved Horns", "BLESSED CARD: Your attack does no damage. Instead, regain the use of an ability gained at 5th level or lower"),
			Card("Forgotten Backhand", "Deals double damage if the monster has no armor points. Fail: Take 1d6+5 bludgeoning damage, 1d6+2 fire damage and get knocked back 15ft"),
			Card("Scorched Breastplate", "TRAP CARD: You must pick this card. Your attack always hits armor points. After your attack resolves, the demon casts Greater Fireball (12d6) on its position!"),
			# Spellcasters tend to ignore this mechanic. Maybe use legendary actions if you don't pull from the monster's hit location deck?
		]

		fateCards = [
			Card("Death comes for us all", "Choose a player. They lose half their current hitpoints (rounded down)"),
			Card("Phantom Knives", "Take x damage OR have The Guardian perform an attack against all of your allies within 15ft of you"),
			Card("The Haunting", "The Guardian teleports to an adjacent location to a player of your choice and performs an attack"),
			Card("The Blood Runs Dry", "Until the end of your next turn, all damage done to The Guardian is also dealt to you OR choose a player, they take an attack from the Guardian"),
			Card("The Void Hungers", "Pick a player. That player and the Guardian gain vulnerability to Necrotic damage"),
			Card("Mass Frenzy", "The Guardian recovers x health OR the next player to act must perform a hostile action against another player"),
			Card("The Reckoning", "The Guardian summons a void golem OR you must make a DC 17 dex saving throw. You are pushed 30ft (15ft on a save) in a random direction (roll d8). Collisions deal 1d8+5 bludgeoning damage"),
			Card("Fate Calls", "At the start of your next turn, the player closest to the Guardian (all tied players in case of a tie) dies immediately if they have less than 10 hitpoints remaining."),
			Card("Force Shadows", "Pick a player, you and that player must each make a DC 17 dex saving throw or be tossed 15ft towards the other. If you collide, take x damage"),
			Card("The Calling", "Pick a player, they disappear and rematerialize adjacent to The Guardian")


		]

		monsterTypes = {"shark":sharkLocations, "octopus":octopusLocations, "owlbear":animalLocations, "human":humanoidLocations, "goblin":humanoidLocations, "demon":demonLocations}
		hitLocations = []
		hitLocations.extend(coreLocations)
		monsterType = ""
		for monster in monsterTypes:
			if LevenshteinFunction(foe.lower(), monster) <= 2:	# allows for mispellings and minor typos, as well as pluralizations (eg goblin vs goblins)
				monsterType = monster
				break
		if monsterType == "":	# monster not found, assume human
			monsterType = "human"
		hitLocations.extend(monsterTypes[monsterType])	# Adds new locations to the hitlocation deck
		if monsterType == "demon":
			hitLocations = demonLocations	# demons are immune to other locations?

		random.shuffle(hitLocations)
		self.currentMonsterDeck = hitLocations
		self.currentMonsterDiscard = []	# reset the discard

		finalMessage = "Successfully set up: " + monsterType
		await ctx.channel.send(finalMessage)


	@commands.command(name="hit", brief="Draws hit locations for a monster", usage="Add a monster to specify subtype", help="Returns two monster hit-locations")
	async def getHitLocation(self, ctx, number=2):
		
		# Ensure upper bounds
		if number > len(self.currentMonsterDeck) + len(self.currentMonsterDiscard):
			number = len(self.currentMonsterDeck) + len(self.currentMonsterDiscard)

		locations = []
		cardsToStillPull = number

		while cardsToStillPull > 0:
			if len(self.currentMonsterDeck) == 0:	# check if we need to reshuffle
				self.currentMonsterDeck = self.currentMonsterDiscard
				random.shuffle(self.currentMonsterDeck)
				self.currentMonsterDiscard = []
				await ctx.channel.send("Shuffled the deck after drawing the remaining cards!")

			card = self.currentMonsterDeck.pop()
			locations.append(card)
			cardsToStillPull -= 1

		self.currentMonsterDiscard.extend(locations)	# populate the discard with all drawn cards

		hitEmbed = discord.Embed(title="Hit Locations", description="Pick a location to hit! **" + str(len(self.currentMonsterDeck)) + "** cards remain in the deck", color=0xFF4B45)
		for location in locations:
			hitEmbed.add_field(name=location.cardName, value=location.cardEffect, inline=False)	
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