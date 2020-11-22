# BorBot
 A Discord Bot

Hey there, this is BorBot, a bot written in Python3 using the official Discord API.

I wrote this bot after being inspired by a friend who was writing a simple bot for a community server and I wanted to make one too for fun and to practice python scripting.

This bot is very barebones and more proof-of-concept than anything, but I'm glad I was able to get this all together pretty quickly. I worked on it for an hour or so each day for about a week and here we are!

This bot features:
* Dice roller
* Reaction roles
* Image with custom text that can be dynamically generated (basically the setup for meme formats)
* Cycling custom statuses (with limitations)
* Ask command for 8ball answers
* Echo command (have the bot say something)
* Monitor command
* Simple character generator
* RPG system (with local data storage)
* Daily Quotes

# To Setup
You'll need to make a .env file in the same directory as this bot and populate it with some data, as needed in the script. At the very minimum, you will need the DISCORD_TOKEN and the DISCORD_SERVER. You should not share the DISCORD_TOKEN with anyone. You'll need to go to [Discord Developer Applications](https://discord.com/developers/applications) and make an application, and grab the discord token from there for the bot. In the OAuth2 section, you can add the bot to a server (called guilds internally). 

You will likely need to install some libraries using pip before you can run the bot. 
> pip install -r requirements.txt

Should grab you all the necessary libraries (provided I didn't miss any).

Once your bot is attached to your server, you need to run the bot for it to show up and handle commands. 
> python Borbot.py

And that's it for setting it up (though slightly simplified and skipping small steps).

# Use and Modifying the Bot
In general, the bot tries to explain itself using the !help command. Some particular things might need additional setup to work, such as the reaction roles require you to append data to the .env file, or the image with custom text feature only supports a singular image by default but can easily be swapped out or expanded. Likewise, the daily quotes grab from quotes from Reddit, but could easily be redirected to grab HTML from somewhere else.

# Screenshots
![Sample quote from Reddit](BorbotQuote.png)
![Sample dice roll][BorbotDiceRoll.png)

