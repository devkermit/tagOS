
import random
import numpy as np
import pandas as pd
import discord
from discord.ext import commands
from discord.utils import get
import shutil, pathlib, os, sys
import typing
import csv
import math

class PlayerCommands(commands.Cog):

	#Initialises bot.
	def __init__(self, bot):
		self.bot = bot
		self.databasepath = os.path.join(pathlib.Path(__file__).parents[1], 'player_database.csv')
		self.wordspath = os.path.join(pathlib.Path(__file__).parents[1], 'words.txt')
		self.codespath = os.path.join(pathlib.Path(__file__).parents[1], 'HvXenomorphcodes.csv')

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
			newplayer = np.array([ctx.message.author.id, firstname, lastname, student_number, braincode, 'Human', 0, 100])
			#newplayer = np.array([ctx.message.author.id, firstname, lastname, student_number, braincode, 'Human', 0])
			player_database = np.append(player_database, [newplayer], axis=0)
			pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
			await ctx.message.author.add_roles(discord.utils.get(ctx.message.guild.roles, name='Human'))
			if ctx.message.author != ctx.message.guild.owner:
				await ctx.message.author.edit(nick=str(player_database[-1][1] + ' ' + player_database[-1][2]))
			await ctx.send('Hi there ' + player_database[-1][1] + ' ' + player_database[-1][2] + '.')
			await ctx.message.author.send('Your braincode is: ' + braincode + '. Keep it secret, keep it safe.')
			return
		else:
			await ctx.send('The join command can only be used in ' + join.mention + '.')
			return

	# Check your braincode
	@commands.command(brief='PMs you your braincode.', description='.check_braincode: PMs you your braincode.')
	@commands.has_role('Human')
	async def check_braincode(self, ctx):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		if player_index:
			await ctx.message.author.send('Your braincode is: ' + player_database[int(player_index)][4] + '. Keep it secret, keep it safe.')
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
			await ctx.send('The bounty command can only be used in ' + bountyset.mention + '.')
        
	@commands.command(brief='Set a reward for your bounty.', description='.reward "Reward"')
	async def reward(self, ctx, reward):
		bountyset = discord.utils.get(ctx.message.guild.text_channels, name='bounty-set')
		bountywall = discord.utils.get(ctx.message.guild.text_channels, name='bounty-wall')
		if ctx.channel == bountyset:
			await ctx.message.delete()
			await bountywall.send('The reward is: ' + reward + '.')
		else:
			await ctx.send('The bounty command can only be used in ' + bountyset.mention + '.')

	@commands.command(brief='Check how many Zombies there are.')
	async def how_many_zombies(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Zombie':
				val+=1
		await ctx.send('There are ' + str(val) + ' Zombies.')

	@commands.command(brief='Check how many Humans there are.')
	async def how_many_humans(self, ctx):
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		val = 0
		for i in player_database:
			if i[5] == 'Human':
				val+=1
		await ctx.send('There are ' + str(val) + ' Humans.')

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
			player_index = self.find(player_database[:,4], braincode)
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
					await ctx.send('Congrats ' + ctx.message.author.mention + '! You have tagged ' + tagged.mention + '. Their braincode was: ' + player_database[int(player_index)][4])
					# Selects a death message randomly and sends message to human-chat announcing tag.
					death_phrase = str(random.choice(death_messages))
					await humanchat.send(player_database[int(player_index)][1] + ' ' + player_database[int(player_index)][2] + ' has been tagged. ' + death_phrase +
										 ' Their braincode was: ' + player_database[int(player_index)][4] + '.')
					return
			await ctx.send('Player does not exist.')
			return
		else:
			await ctx.send('The tag command can only be used in ' + zombiechat.mention + '.')
			return
	
	@commands.command(brief='Add credits to your account.')
	async def redeem_cache(self, ctx, code):

		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')
		codes = np.loadtxt(self.codespath, dtype=str, delimiter=',')

		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		player = ctx.guild.get_member(int(player_database[int(player_index)][0]))

		check = int(0)
		if discord.utils.get(player.roles, name = 'Human'):
			check = int(2)
		elif discord.utils.get(player.roles, name = 'Zombie'):
			check = int(3)

		for i in codes:
			if i[0] == code:
				if discord.utils.get(player.roles, name = 'Human'):
					if int(i[2]) == 1:
						await ctx.send('Code already redeemed by your team!')
						return
				if discord.utils.get(player.roles, name = 'Zombie'):
					if int(i[3] == 1):
						await ctx.send('Code already redeemed by your team!')
						return
				
				player_index = self.find(player_database[:,0], str(ctx.message.author.id))
				if player_index:
					updatemoney = int(i[1]) + int(player_database[int(player_index)][6])
					player_database[int(player_index)][6] = str(updatemoney)
					i[check] = 1
					pd.DataFrame(codes).to_csv(self.codespath, header=None, index=None)
					pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
					await ctx.message.author.send('Code redeemed. Your balance is now: ' + str(updatemoney))	

	@commands.command(brief='Transfers money.')
	async def transfer_balance(self, ctx, target: discord.Member):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')

		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		target_index = self.find(player_database[:,0], str(target.id))

		playermoney = int(player_database[int(player_index)][6])
		targetmoney = int(player_database[int(target_index)][6])

		half = int(0.5 * playermoney)
		half = 5 * round(half / 5)
		playermoney = playermoney - half
		targetmoney = targetmoney + half
		print(playermoney)
		print(targetmoney)

		player_database[int(player_index)][6] = str(playermoney)
		player_database[int(target_index)][6] = str(targetmoney)
		pd.DataFrame(player_database).to_csv(self.databasepath, header=None, index=None)
		await ctx.message.author.send('Code redeemed. Your balance is now: ' + str(playermoney))
		print("test")
	
	@commands.command(brief='Sends you your balance.')
	async def check_balance(self, ctx):
		await ctx.message.delete()
		player_database = np.loadtxt(self.databasepath, dtype=str, delimiter=',')

		player_index = self.find(player_database[:,0], str(ctx.message.author.id))
		playermoney = player_database[int(player_index)][6]
		await ctx.message.author.send('Your balance is now: ' + str(playermoney))




	
async def setup(bot):
	await bot.add_cog(PlayerCommands(bot))