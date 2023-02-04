import random
import numpy as np
import pandas as pd
import discord
from discord.ext import commands
from discord.utils import get
import shutil, pathlib, os, sys
from datetime import datetime as dt, timedelta as timeD
import time
import typing

class ModeratorCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.databasepath = os.path.join(pathlib.Path(__file__).parents[1], 'player_database.csv')
		self.wordspath = os.path.join(pathlib.Path(__file__).parents[1], 'words.txt')
		self.memberspath = os.path.join(pathlib.Path(__file__).parents[1], 'members.csv')

	def find(self, check_in, check_for):
		player_row = np.where(check_in == check_for)
		# Checks that a player was found
		if len(player_row[0]) != 0:
			return player_row[0][0]
		else:
			return False

	def make_braincode(self, words, player_database):
		braincode = str(random.choice(words))+str(random.choice(words))+str(random.choice(words))
		if braincode in player_database:
			braincode = self.make_braincode(self,words, player_database)
		return braincode


	# Retrieves user brain code
	@commands.command(brief='Retrieve the braincode of a user.', description='.get_braincode \"[Username]\": PMs you the braincode of a given user.')
	@commands.has_any_role('Moderator', 'Bot Dev', 'Committee')
	async def get_braincode(self, ctx, username):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		user = ctx.guild.get_member_named(username)
		if user == None:
			await ctx.send('User not found.')
			return
		else:
			player_index = self.find(player_database[:,0], str(user.id))
			if player_index:
				await ctx.message.author.send('Username: ' + username + ' Braincode: ' + player_database[int(player_index)][4])
				#await ctx.message.author.send('Username ' + user.nickname + ' has braincode ' + player_database[int(player_index)][4] + '.')
				return
			await ctx.send('User is not in game.')
			return

	# Revives a Zombie
	@commands.command(brief='Revives a Zombie.', description='.revive \"[Username]\": Revives a Zombie.')
	@commands.has_any_role('Moderator', 'Bot Dev', 'Committee')
	async def revive(self, ctx, username):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		words = np.loadtxt(self.wordspath, dtype=str)
		user = ctx.guild.get_member_named(username)
		if user == None:
			await ctx.send('User not found.')
			return
		else:
			if not discord.utils.get(user.roles, name='Zombie'):
				await ctx.send('User is not a Zombie.')
				return
			else:
				player_index = self.find(player_database[:,0], str(user.id))
				if player_index:
					newbraincode = self.make_braincode(words, player_database)
					player_database[int(player_index)][4] = newbraincode
					player_database[int(player_index)][5] = 'Human'
					pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
					await user.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Zombie'))
					await user.add_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
					await user.send('Congrats! You have been revived. Your new braincode is: ' + newbraincode + '. Keep it secret. Keep it safe.')
					await discord.utils.get(ctx.message.guild.text_channels, name='human-chat').send('Heroes never die! ' + i[1] + ' ' + i[2] + ' has returned.')
					await ctx.send(user.nickname + ' has been revived!')
					return
			await ctx.send('Player does not exist.')
			return

	# Revives all zombies.
	@commands.command(brief='Revives all Zombies.', description='.revive_all: Revives all Zombies.')
	@commands.has_any_role('Moderator', 'Bot Dev', 'Committee')
	async def revive_all(self, ctx):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		words = np.loadtxt(self.wordspath, dtype=str)
		zombie = discord.utils.get(ctx.message.guild.roles, name='Zombie')
		for user in zombie.members:
			player_index = self.find(player_database[:,0], str(user.id))
			if player_index:
				newbraincode = self.make_braincode(words, player_database)
				player_database[int(player_index)][4] = newbraincode
				player_database[int(player_index)][5] = 'Human'
				await user.remove_roles(zombie)
				await user.add_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
				await user.send('Congrats! You have been revived. Your new braincode is: ' + newbraincode + '. Keep it secret. Keep it safe.')
		pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
		await ctx.send('All players revived!')
		return

	# Delete a player from the game.
	@commands.command(brief='Deletes a player from the game.', description='.delete_player \"[Username]\": Deletes a player and their entry from the game.')
	@commands.has_any_role('Moderator', 'Bot Dev', 'Committee')
	async def delete_player(self, ctx, username):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		user = ctx.guild.get_member_named(username)
		if user == None:
			await ctx.send('User not found.')
			return
		else:
			player_index = self.find(player_database, str(user.id))
			if player_index:
				player_database = np.delete(player_database, int(player_index), 0)
				pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
				await user.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
				await user.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Zombie'))
				await ctx.send('Player removed.')
				return

async def setup(bot):
	await bot.add_cog(ModeratorCommands(bot))
