import os
import discord
from discord.ext import commands, tasks
import datetime
import pytz
import re
from collections import defaultdict
from tabulate import tabulate

intents = discord.Intents.all()
intents.presences = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.environ['DISCORD_BOT_TOKEN']
TARGET_USER_ID = int(os.environ['TARGET_USER_ID'])
TRIGGER_USER_ID = int(os.environ['TRIGGER_USER_ID'])
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
USER_TO_TAG = int(os.environ['USER_TO_TAG_ID'])

last_online = {}
game_stats = defaultdict(lambda: defaultdict(int))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in the following servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (id: {guild.id})')
    print(f'Listening for messages from user ID: {TARGET_USER_ID}')
    print(f'Watching for :dog2: reactions from user ID: {TRIGGER_USER_ID}')
    scheduled_message.start()
    nightly_stats.start()

@tasks.loop(time=datetime.time(hour=2, minute=59, tzinfo=pytz.UTC))
async def scheduled_message():
    now = datetime.datetime.now(pytz.UTC)
    if now.weekday() in [6, 0, 1, 2, 3]:
        channel = bot.get_channel(CHANNEL_ID)
        user_to_tag = await bot.fetch_user(USER_TO_TAG)
        await channel.send(f"{user_to_tag.mention} Servici usor, barosane!")

@scheduled_message.before_loop
async def before_scheduled_message():
    await bot.wait_until_ready()

@tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=pytz.UTC))
async def nightly_stats():
    channel = bot.get_channel(CHANNEL_ID)
    await calculate_and_post_stats(channel)

@nightly_stats.before_loop
async def before_nightly_stats():
    await bot.wait_until_ready()

async def calculate_and_post_stats(channel):
    game_stats.clear()
    yesterday = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    async for message in channel.history(after=yesterday_start, limit=None):
        if message.author == bot.user and "🚨" in message.content:
            match = re.search(r"(.*) (started|stopped) playing (.*) at", message.content)
            if match:
                user, action, game = match.groups()
                time = message.created_at
                if action == "started":
                    game_stats[user][game] = [time, None]
                elif action == "stopped":
                    if game in game_stats[user] and game_stats[user][game][1] is None:
                        game_stats[user][game][1] = time

    table_data = []
    for user, games in game_stats.items():
        for game, times in games.items():
            start, end = times
            if end is None:
                end = datetime.datetime.now(pytz.UTC)
            duration = end - start
            table_data.append([user, game, str(duration)])

    table_data.sort(key=lambda x: datetime.datetime.strptime(x[2], "%H:%M:%S.%f"), reverse=True)
    table = tabulate(table_data, headers=["User", "Game", "Play Time"], tablefmt="pipe")

    await channel.send(f"Game stats for {yesterday.date()}:\n```\n{table}\n```")

@bot.event
async def on_message(message):
    print(f'Received message from {message.author.name}#{message.author.discriminator} (ID: {message.author.id}): {message.content}')

    if message.author.id == TARGET_USER_ID:
        print(f'Responding to message from target user {message.author.name}#{message.author.discriminator}')
        await message.channel.send('jocek')

    if bot.user.mentioned_in(message):
        content_lower = message.content.lower()
        if 'dns' in content_lower:
            await file_response(message.channel, 'dns.txt', 'DNS')
        elif 'flow' in content_lower:
            await file_response(message.channel, 'flow.txt', 'Flow')
        elif 'cloudstick' in content_lower:
            await file_response(message.channel, 'cloudstick.txt', 'Cloudstick')
        elif 'last online' in content_lower:
            await last_online_response(message)

    await bot.process_commands(message)

async def file_response(channel, filename, file_type):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        if content:
            chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await channel.send(f"**{file_type} Content (Part {i+1}/{len(chunks)}):**\n{chunk}")
                else:
                    await channel.send(f"**{file_type} Content (Part {i+1}/{len(chunks)}):**\n{chunk}")
        else:
            await channel.send(f"The {file_type} file is empty.")
    except FileNotFoundError:
        await channel.send(f"{file_type} file not found.")
    except Exception as e:
        await channel.send(f"An error occurred while reading the {file_type} file: {str(e)}")

@bot.event
async def on_presence_update(before, after):
    channel = bot.get_channel(CHANNEL_ID)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alarm_emoji = "🚨" * 1  # Three alarm emojis

    # Update last online time
    if after.status != discord.Status.offline:
        last_online[after.id] = datetime.datetime.now()

    # Check if the user started playing a game
    if (before.activity is None or before.activity.type != discord.ActivityType.playing) and \
       (after.activity is not None and after.activity.type == discord.ActivityType.playing):
        await channel.send(f"{alarm_emoji} {after.name} started playing {after.activity.name} at {current_time} {alarm_emoji}")

    # Check if the user stopped playing a game
    elif (before.activity is not None and before.activity.type == discord.ActivityType.playing) and \
         (after.activity is None or after.activity.type != discord.ActivityType.playing):
        game_name = before.activity.name
        await channel.send(f"{alarm_emoji} {after.name} stopped playing {game_name} at {current_time} {alarm_emoji}")

async def last_online_response(message):
    mentioned_users = message.mentions
    if len(mentioned_users) > 1:  # The first mention is the bot itself
        user = mentioned_users[1]  # Get the first mentioned user after the bot
        if user.id in last_online:
            last_time = last_online[user.id].strftime("%Y-%m-%d %H:%M:%S")
            await message.channel.send(f"{user.name} was last seen online at {last_time}")
        else:
            await message.channel.send(f"I haven't seen {user.name} online since I started tracking.")
    else:
        await message.channel.send("Please mention a user to check their last online time.")

@bot.event
async def on_reaction_add(reaction, user):
    print(f"Reaction detected (cached): {reaction.emoji} from user {user.name}#{user.discriminator} (ID: {user.id})")

@bot.event
async def on_raw_reaction_add(payload):
    print(f"Raw reaction detected: {payload.emoji} from user ID: {payload.user_id}")

    if payload.user_id == TRIGGER_USER_ID:
        print(f"Reaction is from trigger user")
        if str(payload.emoji) == '🐕':
            print(f"Dog emoji detected")
            channel = bot.get_channel(payload.channel_id)
            print(f"Attempting to send message in channel: {channel.name}")

            try:
                target_user = await bot.fetch_user(TARGET_USER_ID)
                await channel.send(f'{target_user.mention} vezi ca joci Dota2!')
                print(f"Message sent successfully")
            except discord.errors.Forbidden:
                print(f"Error: Bot doesn't have permission to send messages in this channel")
            except Exception as e:
                print(f"Error sending message: {str(e)}")
        else:
            print(f"Not the dog emoji: {payload.emoji}")
    else:
        print(f"Reaction is not from trigger user")

@bot.command()
async def ping(ctx):
    await ctx.send('Aici sunt, barosane!')
    print(f"Responded to ping command from {ctx.author.name}#{ctx.author.discriminator}")

bot.run(TOKEN)
