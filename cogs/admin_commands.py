import random
import numpy as np
import pandas as pd
import discord
from discord.ext import commands
from discord.utils import get
import shutil, pathlib, os, sys
from datetime import datetime as dt, timedelta as timeD

#Establish bot permissions.
intents = discord.Intents.default()
client = discord.Client(intents=intents)

#Class for all admin commands.
class AdminCommands(commands.Cog):

	# Initalises needed params.
	def __init__(self, bot):
		self.bot = bot
		self.databasepath = os.path.join(pathlib.Path(__file__).parents[1], 'player_database.csv')


	# Prints data about players to a Discord channel.
	@commands.command(brief='Sends player data.')
	@commands.has_any_role('Bot Dev', 'Committee')
	@client.event
	async def check(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		for i in player_database:
			await ctx.send(i)
		return

	# Removes all Human and Zombie roles.
	@commands.command(brief='Removes all Human, Zombie and Spectator roles.', description='.deroll_all: Removes all Human, Zombie and Spectator roles.')
	@commands.has_any_role('Bot Dev', 'Committee')
	async def deroll_all(self, ctx):
		await ctx.send('Removing all Human, Zombie and Spectator roles. This will take some time.')
		human = discord.utils.get(ctx.message.guild.roles, name='Human')
		zombie = discord.utils.get(ctx.message.guild.roles, name='Zombie')
		spectator = discord.utils.get(ctx.message.guild.roles, name='Spectator')
		for i in ctx.message.guild.members:
			await i.remove_roles(human)
			await i.remove_roles(zombie)
			await i.remove_roles(spectator)
		await ctx.send('All roles removed.')
		return

	# Resets player database.
	@commands.command(brief='Resets the player database.', description='.reset_database: Resets the player database.')
	@commands.has_any_role('Bot Dev', 'Committee')
	async def reset_database(self, ctx):
		backuppath = os.path.join(pathlib.Path(__file__).parents[1], 'backupdatabase', 'player_database.csv')
		newpath = os.path.join(pathlib.Path(__file__).parents[1], 'player_database.csv')
		shutil.copy(backuppath, newpath)
		await ctx.send('Player database reset.')
		return

	# Ends the game.
	@commands.command(brief='Runs all reset commands to end the game.', description='.reset_all: Runs all reset commands to end the game.')
	@commands.has_any_role('Bot Dev', 'Committee')
	async def end_game(self, ctx):
		await ctx.send('Starting reset, this will take some time.')
		await ctx.invoke(self.bot.get_command("reset_database"))
		print("reset database done")
		await ctx.invoke(self.bot.get_command("deroll_all"))
		await ctx.send('All reset.')
		return

	# Logs Tagger out
	@commands.command(brief='Logs out of Tagger.', description='Logs out of Tagger')
	@commands.has_any_role('Bot Dev', 'Committee')
	async def k(self, ctx):
		await ctx.send('Logging out, see you next game!')
		await ctx.bot.logout()


async def setup(bot):
	await bot.add_cog(AdminCommands(bot))
