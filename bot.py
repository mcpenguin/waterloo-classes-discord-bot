import os

import discord
from dotenv import load_dotenv

load_dotenv()

# get discord bot token
TOKEN = os.getenv('DISCORD_TOKEN')

# setup discord client and connect to user
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(TOKEN)