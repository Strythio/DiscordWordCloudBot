import discord
from discord.ext import commands
import json
import asyncio
from schema import GetSession, Member, Message, Channel
from wordcloud_gen import generate_word_clouds
from spamDetector import calc_spam_probability
import random

#Fill in these three things, or you won't be able to use the bot
discord_api_key = ''
bot_owner_id = 0
bot_owners_username = ''

#This is so the bot can tell everybody how great you are when they try to use it (they can't)
owner_titles = [
	f'The Fearless and Mighty {bot_owners_username}',
	f'The Incredible {bot_owners_username}',
	f'The one and only {bot_owners_username}',
	f'The Powerful {bot_owners_username}',
	f'The Great and Mighty {bot_owners_username}',
	f'The Unstoppable {bot_owners_username}',
	f'The Unrivaled {bot_owners_username}',
	f'The Incomparable {bot_owners_username}',
	f'The Unequaled {bot_owners_username}',
	f'The Great and Powerful {bot_owners_username}',
	f'The Amazing {bot_owners_username}',
	f'The Marvelous {bot_owners_username}',
	f'The Magnificent {bot_owners_username}',
	f'The Splendid {bot_owners_username}',
	f'The Grandiose {bot_owners_username}',
	f'The Glorious {bot_owners_username}',
	f'The Exalted {bot_owners_username}',
	f'The Fearless and Mighty {bot_owners_username}',
	f'The Brave and Courageous {bot_owners_username}',
	f'The Powerful {bot_owners_username}',
	f'The Honorable {bot_owners_username}', 
	f'The Noble {bot_owners_username}',
	f'The Wonderful {bot_owners_username}', 
	f'The Miraculous {bot_owners_username}',
	f'The Supreme {bot_owners_username}',
	f'The Almighty {bot_owners_username}',
	f'The Invincible {bot_owners_username}',
	f'{bot_owners_username} the all-seeing',
	f'{bot_owners_username} the all-knowing',
	f'{bot_owners_username} the all-powerful',
	f'{bot_owners_username} the most high',
	f'{bot_owners_username} the most supreme',
	f'{bot_owners_username} the most ultimate',
	f'{bot_owners_username} the creator of all things',
	f'{bot_owners_username} who is above all things',
	f'The Fearless Leader of the Free World, {bot_owners_username}',
	f'The Most influential Person in the Universe, {bot_owners_username}',
	f'The Most Popular Person in the Galaxy, {bot_owners_username}',
	f'The Most Loved Person in All of Time and Space, {bot_owners_username}',
	f'The Most Admired Person in All of Creation, {bot_owners_username}',
	f'The Most Respected authority on All things Good and Righteous, {bot_owners_username}',
	f'The Wisest being to ever live, {bot_owners_username}',
	f'The most benevolent force for good in the multiverse, {bot_owners_username}',
	f'The role model for all living creatures, {bot_owners_username}',
	f'A walking god amongst mortals, {bot_owners_username}',  
	f'The being so divine that their very presence fills one with hope, {bot_owners_username}',
	f'The one who has transcended morality, {bot_owners_username}',
]

session = GetSession()

client = commands.Bot(command_prefix=':', intents=discord.Intents.all(), chuck_guilds_at_startup=True)

@client.command()
async def ingest_messages(ctx):
	user = ctx.message.author
	guild = ctx.message.guild
	channels = guild.channels

	if user.id != bot_owner_id:
		await ctx.reply(f"Sorry, I only take orders from my creator, {random.choice(owner_titles)}")
		return

	await ctx.message.channel.send("Beginning ingestion.")

	db_members = {m.id: m for m in session.query(Member).all()}
	db_channels = {c.id: c for c in session.query(Channel).all()}
	count = 1
	for channel in channels:
		if channel.id in db_channels:
			print(f"Already have data from channel {channel.name}, skipping")
			await asyncio.sleep(1)
			continue
		try:
			if not isinstance(channel, discord.TextChannel):
				print("Ignoring Voice Channel")
				continue
			messages = channel.history(limit=100000000)
			print(f"\n\Saving messages in channel: {channel.name}")
			async for message in messages:
				member_id = message.author.id
				member_name = f"{message.author.name}#{message.author.discriminator}"
				member_mention = message.author.mention
				channel_id = channel.id
				channel_name = channel.name
				text = message.content
				date_sent = message.created_at
				is_bot = message.author.bot
				if len(text) == 0:
					continue
				if calc_spam_probability(text) > 0.85:
					print(f"\n({count}) Skipping spam: {text[0:min(len(text), 60)]}", end='')
					continue
				print(f"\n({count}) Saving message: {text[0:min(len(text), 60)]}", end='')
				count += 1
				if member_id not in db_members:
					db_member = Member(id=member_id, is_bot=is_bot, name=member_name, mention_string=member_mention)
					session.add(db_member)
					db_members[member_id] = db_member
				else:
					db_member = db_members[member_id]

				if channel_id not in db_channels:
					db_channel = Channel(id=channel_id, name=channel_name)
					session.add(db_channel)
					db_channels[channel_id] = db_channel
				else:
					db_channel = db_channels[channel_id]

				msg = Message(text=text, date_sent=date_sent, channel=db_channel, member=db_member)
				session.add(msg)
				await asyncio.sleep((1.0 / 49.0) / 5.0)
			session.commit()
		except:
			continue

	await ctx.message.channel.send("Message ingestion completed.")

def print_message(progress, count, message):
	if message is None:
		print("({0:.2f}%) {1}".format(progress * 100, count))
	else:
		print("({0:.2f}%) {1}: {2}".format(progress * 100, count, message.text[0:min(len(message.text), 100)].replace('\n', ' ')))

@client.command()
async def mark_spam_messages(ctx):
	user = ctx.message.author
	channel = ctx.message.channel

	if user.id != bot_owner_id:
		await ctx.reply(f"Sorry, I only take orders from my creator, {random.choice(owner_titles)}")
		return

	await channel.send("Marking all messages that appear to be spam.")

	session = GetSession()

	await channel.send("Beginning multi-message aware spam filtration...")
	messages = list(session.query(Message).order_by(Message.date_sent).all())
	num_messages = len(messages)
	messages_to_delete = []

	idx = 1
	group_size = 5
	for offset in range(0, num_messages - group_size - 1, 1):
		if idx % 10000 == 0:
			print_message(idx / num_messages, offset, None)
		idx += 1
		group = messages[offset:offset+group_size]
		combined_text = ''
		for message in group:
			combined_text += message.text
		if len(combined_text) == 0:
			continue
		prob_of_spam = calc_spam_probability.__wrapped__(combined_text)
		if prob_of_spam > 0.8:
			#okay, now we gotta figure out which of the 5 messages are spam. Most likely, all of them
			#but it could just be 3 of 5, for example
			#so let's find out which message is the majority
			message_repeat_counts = {}
			for message in group:
				text =  message.text
				if text not in message_repeat_counts:
					message_repeat_counts[text] = (0, [])
				message_repeat_counts[text] = (message_repeat_counts[text][0] + 1, message_repeat_counts[text][1] + [message])
			# okay, now get the messages that had the same text occur the most (sort)
			most_repeated_messages = sorted(message_repeat_counts.items(), key=lambda x: x[1][0], reverse=True)[0][1][1]
			for message in most_repeated_messages:
				if message.id not in messages_to_delete:
					messages_to_delete.append(message)
					print_message(idx / num_messages, offset, message)

	for message in messages_to_delete:
		session.delete(message)

	session.commit()

	await channel.send(f"Completed multi-message spam filtration. {len(messages_to_delete)} additional messages will be excluded.")
	await channel.send("Completed spam message identification.")

@client.command()
async def generate_wordclouds(ctx):
	user = ctx.message.author
	channel = ctx.message.channel

	if user.id != 694386018668904499:
		await ctx.reply(f"Sorry, I only take orders from my creator, {random.choice(owner_titles)}")
		return

	await channel.send("Beginning wordcloud generation.")
	generate_word_clouds()
	await channel.send("Completed wordcloud generation.")


@client.command()
async def post_wordclouds(ctx):
	user = ctx.message.author
	channel = ctx.message.channel

	if user.id != 694386018668904499:
		await ctx.reply(f"Sorry, I only take orders from my creator, {random.choice(owner_titles)}")
		return

	wordcloud_info = None
	with open('wordclouds/info.json', 'r') as infile:
		wordcloud_info = json.load(infile)

	for info in wordcloud_info:
		message =  f".\n\n\nStats for {info['member_mention']}:"
		message += f"""
Total Words Said: {info['member_total_words']}
Unique Words Said: {info['member_unique_words']}
First message sent on {info['member_first_message_date']} ```{info['member_first_message']}```
Top 15 most used words (first is most used. Ignoring common words):
```
{', '.join(info['member_top_15_words'])}
```
"""
		with open(info['path'], 'rb') as wordcloud_image:
			await channel.send(message, file=discord.File(wordcloud_image, f"{info['member_id']}_wc.png"))
		await asyncio.sleep(1)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

client.run(discord_api_key)
