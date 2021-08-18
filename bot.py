import os

from discord.ext import commands
from dotenv import load_dotenv

from pymongo import MongoClient

load_dotenv()

# get env vars
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')

# connect to mongodb database
client = MongoClient(MONGO_URL)
db = client['waterloo']['courses']

# get class info
def get_class_info(subjectCode, catalogNumber, term = '1219'):
    # get class info
    class_info = db.find({'subjectCode': subjectCode , 'catalogNumber': catalogNumber, 'term': term})
    for x in class_info:
        return x

    return 'Course does not exist'

# setup discord client and connect to user
bot = commands.Bot(command_prefix='?')

# respond to messages
@bot.command(name='class', help='Get class info')
async def get_class_list(ctx):
    # get params
    params = ctx.message.content.split(" ")[1:]

    # initialize generic response
    response = 'Unknown command, please try again'

    # ?class <subject code> <catalog number> -> return course info for that class for current term
    if len(params) == 2:
        subjectCode = params[0]
        catalogNumber = str(params[1])
        class_info = get_class_info(subjectCode, catalogNumber, '1211')
        response = class_info
    
    await ctx.send(response)

# run bot
bot.run(TOKEN)


