
import random
import numpy as np
import pandas as pd
import discord
from discord.ext import commands
from discord.utils import get
import shutil, pathlib, os, sys
import typing

class PlayerCommands(commands.Cog):

	#Initialises bot.
	def __init__(self, bot):
		self.bot = bot
		self.databasepath = os.path.join(pathlib.Path(__file__).parents[1], 'player_database.csv')
		self.wordspath = os.path.join(pathlib.Path(__file__).parents[1], 'words.txt')

	#Finds player in database.
	def find(self, check_in, check_for):
		player_row = np.where(check_in == check_for)
		if len(player_row[0]) != 0:
			return player_row[0][0]
		else:
			return False

	# Produces 3 concatenated words to make a unique braincode.
	def make_braincode(self, words, player_database):
		braincode = str(random.choice(words))+str(random.choice(words))+str(random.choice(words))
		if braincode in player_database:
			braincode = self.make_braincode(self,words, player_database)
		return braincode

	# New users use the Join command to add themselves to the Tagger database
	@commands.command(brief='Allows user to join the game in #join.', description='.join [student_number] or .join [Firstname] [Lastname]: Adds user to the game. You can only join with your name if you have been given the Non-Member role.')
	async def join(self, ctx, firstname, lastname, student_number):
		await ctx.message.delete()
		join = discord.utils.get(ctx.message.guild.text_channels, name='join')
		if ctx.channel == join:
			# Opens required resources
			player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
			words = np.loadtxt(self.wordspath, dtype=str)
			# Checks if the user has already joined
			player_index = self.find(player_database[:,0], str(ctx.message.author.id))
			if player_index:
				await ctx.send('You have already joined the game.')
				return
			# Creates entry in player_database for the given student number / other, generates 3 word braincode,  sets role to Human
			braincode = self.make_braincode(words, player_database)
			newplayer = np.array([ctx.message.author.id, firstname, lastname, student_number, braincode.lower(), 'Human', 0, 100])
			
			player_database = np.append(player_database, [newplayer], axis=0)
			pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
			await ctx.message.author.add_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
			await ctx.message.author.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Zombie'), discord.utils.get(ctx.message.guild.roles, name='Spectator'))
			if ctx.message.author != ctx.message.guild.owner:
				await ctx.message.author.edit(nick=str(player_database[-1][1] + ' ' + player_database[-1][2]))
			await ctx.send('Hi there ' + player_database[-1][1] + ' ' + player_database[-1][2] + '.')
			await ctx.message.author.send('Your braincode is: **' + braincode + '**.\n*Keep it secret, keep it safe!*')
			return
		else:
			await ctx.send('Sorry, the `.join` command can only be used in ' + join.mention + '.')
			return

	# Lets players set their role to spectator
	@commands.command(brief='Allows the user to become a spectator', description='.spectate')
	async def spectate(self, ctx):
		# Opens required resources
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		# Checks if the user is already a Spectator
		if discord.utils.get(ctx.message.author.roles, name = 'Spectator'):
			await ctx.send('You are already a Spectator')
			return

		# Checks if the user has joined the game
		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		if not player_index:
			join = discord.utils.get(ctx.message.guild.text_channels, name='join')
			await ctx.send('Sorry, you need to join the game using `.join` in ' + join.mention + ' before you can become a spectator.')
			return

		# Sets the user's role to Spectator and removes any Human or Zombie roles
		await ctx.message.author.add_roles(discord.utils.get(ctx.message.guild.roles, name='Spectator'))
		await ctx.message.author.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Human'), discord.utils.get(ctx.message.guild.roles, name='Zombie'))

		# Sets the user's role to Spectator in the player database
		player_database[int(player_index)][5] = 'Spectator'
		pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)

		await ctx.send(player_database[-1][1] + ' ' + player_database[-1][2] + ' is now a Spectator.')
		return

	# Check your braincode
	@commands.command(brief='PMs you your braincode.', description='.check_braincode: PMs you your braincode.')
	@commands.has_role('Human')
	async def check_braincode(self, ctx):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		if player_index:
			await ctx.message.author.send('Your braincode is: **' + player_database[int(player_index)][4] + '**.\n*Keep it secret, keep it safe!*')
			return
		await ctx.message.author.send('I can\'t find your braincode. Please contact your admin.')
		return

	@commands.command(brief='Set a bounty on a player.', description='.bounty "@some_player"')
	async def bounty(self, ctx, member: discord.Member):
		bountyset = discord.utils.get(ctx.message.guild.text_channels, name='bounty-set')
		bountywall = discord.utils.get(ctx.message.guild.text_channels, name='bounty-wall')
		if ctx.channel == bountyset:
			await ctx.message.delete()
			await bountywall.send('A bounty has been set on ' + member.mention + ' by ' + ctx.message.author.mention + '.')
		else:
			await ctx.send('Sorry, the `.bounty` command can only be used in ' + bountyset.mention + '.')
        
	@commands.command(brief='Set a reward for your bounty.', description='.reward "Reward"')
	async def reward(self, ctx, reward):
		bountyset = discord.utils.get(ctx.message.guild.text_channels, name='bounty-set')
		bountywall = discord.utils.get(ctx.message.guild.text_channels, name='bounty-wall')
		if ctx.channel == bountyset:
			await ctx.message.delete()
			await bountywall.send('The reward is: ' + reward + '.')
		else:
			await ctx.send('Sorry, the `.reward` command can only be used in ' + bountyset.mention + '.')

	# Check how many zombies are currently in the game
	@commands.command(brief='Check how many Zombies there are.')
	async def how_many_zombies(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Zombie':
				val+=1
		await ctx.send('There are ' + str(val) + ' Zombies.')

	# Check how many humans are currently in the game
	@commands.command(brief='Check how many Humans there are.')
	async def how_many_humans(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Human':
				val+=1
		await ctx.send('There are ' + str(val) + ' Humans.')
	
	# Check how many spectators are currently in the game
	@commands.command(brief='Check how many Spectators there are.')
	async def how_many_spectators(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Spectator':
				val+=1
		await ctx.send('There are ' + str(val) + ' Spectators.')

	# Check how many total players are currently in the game
	@commands.command(brief='Check how many players there are.')
	async def how_many_players(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Human':
				val+=1
			elif i[5] == 'Zombie':
				val+=1
		await ctx.send('There are ' + str(val) + ' players.')

	# Check the ratio of Humans to Zombies currently in the game
	@commands.command(brief='Check the ratio of humans to zombies.')
	async def ratio(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		humans = 0
		zombies = 0
		for i in player_database:
			if i[5] == 'Human':
				humans+=1
			elif i[5] == 'Zombie':
				zombies+=1
		
		# Calculate the ratio of Humans to Zombies using their greatest common denominator
		gcd = np.gcd(humans, zombies)
		humans = int(humans / gcd)
		zombies = int(zombies / gcd)
		await ctx.send('There are ' + str(humans) + ' humans for every ' + str(zombies) + ' zombies.')

	# Used by Zombies to tag Humans
	@commands.command(brief='Tag a Human with their braincode in #zombie-chat.', description='.tag [braincode]: Tag a Human user. i.e. .tag firstsecondthird')
	async def tag(self, ctx, braincode):
		zombiechat = discord.utils.get(ctx.message.guild.text_channels, name='zombie-chat')
		await ctx.message.delete()
		# Checks if command run in zombie chat.
		if ctx.channel == zombiechat:
			# Opens databases, sets channels.
			player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
			death_messages = np.loadtxt(os.path.join(pathlib.Path(__file__).parents[1], 'death_messages.txt'), dtype=str, delimiter=',')
			humanchat = discord.utils.get(ctx.message.guild.text_channels, name='human-chat')
			# Checks player_database for tagged player.
			player_index = self.find(player_database[:,4], braincode.lower())
			if player_index:
				tagged = ctx.guild.get_member(int(player_database[int(player_index)][0]))
				# Ends command if player was alredy a Zombie
				if discord.utils.get(tagged.roles, name = 'Zombie'):
					await ctx.send('Player is already a Zombie')
					return
				else:
					player_database[int(player_index)][5] = 'Zombie'
				
					# Updates the role of the tagged player and saves all changed data to player_database.
					await tagged.add_roles(discord.utils.get(ctx.message.guild.roles, name='Zombie'))
					await tagged.remove_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
					pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
					
					# Sends message to zombie-chat announcing tag.
					await ctx.send('Congrats ' + ctx.message.author.mention + '! You have tagged ' + tagged.mention + '. Their braincode was: `' + player_database[int(player_index)][4] + '`')
					# Selects a death message randomly and sends message to human-chat announcing tag.
					death_phrase = str(random.choice(death_messages))
					await humanchat.send(player_database[int(player_index)][1] + ' ' + player_database[int(player_index)][2] + ' has been tagged. ' + death_phrase +
										 ' Their braincode was: `' + player_database[int(player_index)][4] + '`.')
					return
			await ctx.send('Player does not exist.')
			return
		else:
			await ctx.send('Sorry, the `.tag` command can only be used in ' + zombiechat.mention + '.')
			return

	# Lists all possible player commands
	@commands.command(brief='List all possible player commands')
	async def commands(self, ctx):
		bot_channel = discord.utils.get(ctx.message.guild.text_channels, name='bot-channel')
		if ctx.channel == bot_channel:
			await ctx.send('''```.join [firstname] [Lastname] [Student number] - Lets you join the current game of HvZ when used in #join

.spectate - Lets you become a spectator once you have joined the game

.check_braincode - Sends you a private message containing your braincode

.bounty [@Player_Name] - Sets a bounty on the specified player when used in #bounty

.reward [Reward Description] - Specifies the reward for a bounty when used in #bounty

.how_many_zombies - Lets you know how many zombies are currently in the game

.how_many_humans - Lets you know how many humans are currently in the game

.how_many_spectators - Lets you know how many spectators are currently in the game

.how_many_players - Lets you know how many players are currently in the game (spectators are not counted)

.ratio - Lets you know the ratio of humans to zombies currently in the game

.tag [Braincode] - Lets a zombie tag the human with the corresponding braincode```''')
		else:
			await ctx.send('Sorry, the `.commands` command can only be used in the ' + bot_channel.mention + ' channel.')

async def setup(bot):
	await bot.add_cog(PlayerCommands(bot))
