import random
import numpy as np
import pandas as pd
import discord
from discord.ext import commands
from discord.utils import get
import shutil, pathlib, os, sys
import asyncio

#Establishes bot permissions.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
TagOS = commands.Bot(command_prefix=".", description='A bot for running HvZ games.', intents=intents)

#Specifies where commands are stored.
initial_extensions = ['cogs.player_commands',
					  'cogs.moderator_commands',
					  'cogs.admin_commands']

#Loads stored commands.
async def load_extensions():
	if __name__ == '__main__':
		for extension in initial_extensions:
			await TagOS.load_extension(extension)


# Start-up operations
@TagOS.event
async def on_ready():
	# Aesthetic changes to bot profile
	await TagOS.change_presence(status=discord.Status.idle, activity=discord.Game('with Humans'))
	print('Logged in as {0.user}'.format(TagOS))
	print('\n')
	return

# Runs bot
async def main():
	async with TagOS:
		token = np.loadtxt('token.txt', dtype=str)
		await load_extensions()
		await TagOS.start(str(token))

asyncio.run(main())