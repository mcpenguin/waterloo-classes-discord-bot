import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from tabulate import tabulate

from pymongo import MongoClient

load_dotenv()

# get env vars
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')

CURRENT_TERM = '1219'
NO_IN_PAGE = 5

# connect to mongodb database
client = MongoClient(MONGO_URL)
db = client['waterloo']['courses']

# get class info method
def get_class_info(subjectCode, catalogNumber, term = CURRENT_TERM):
    
    class_info = db.find({'subjectCode': subjectCode , 'catalogNumber': catalogNumber, 'term': term})
    
    for x in class_info:
        return x

    return 'Course does not exist'

# get class number method
def get_class_section_info(subjectCode, catalogNumber, classNo, term = CURRENT_TERM):
    
    class_info = db.find({'subjectCode': subjectCode , 'catalogNumber': catalogNumber, 'term': term})
    
    for x in class_info['classes']:
        if x['classNumber'] == classNo:
            return x
    
    return 'Class does not exist'


# get value of tag in command
def get_tag_value(tag, command, default=None):
    command_split = command.split(" ")
    if tag in command_split:
        tag_pos = command_split.index(tag)
        return command_split[tag_pos + 1]
    else:
        return default

# setup discord client and connect to user
bot = commands.Bot(command_prefix='?')

# respond to messages
@bot.command(name='class', help='Get class info')
async def get_class_list(ctx):
    # get params
    content = ctx.message.content
    params = content.split(" ")[1:]

    # initialize generic response
    response = 'Unknown course, please check and try again'

    # usage
    # ?class [subject code] [catalog number] (-t term) (-p page) (-c class_no) 
    subjectCode = params[0]
    catalogNumber = str(params[1])

    term = get_tag_value('-t', content, CURRENT_TERM)
    page = get_tag_value('-p', content, 1)
    class_no = get_tag_value('-c', content)

    # get class info
    class_info = get_class_info(subjectCode, catalogNumber, term)
    # if class is not valid, return error response 
    if type(class_info) == str:
        await ctx.send(response)
        return

    # create response
    response = discord.Embed(
        title = class_info['subjectCode'] + ' ' + class_info['catalogNumber'] + ' - ' + class_info['title'],
        color = discord.Color.from_rgb(0, 0, 255),
    )

    # add course level
    response.add_field(
        name = 'Level',
        value = {
            'UG': 'Undergraduate',
            'G': 'Graduate',
        }[class_info['level']],
        inline = True
    ) 
    # add course units
    response.add_field(
        name = 'Units',
        value = class_info['units'],
        inline = True
    )

    # add course classes
    classes = class_info['classes']
    classes_head = [
        '#',
        'Sect',
        'Camp Loc',
        'Cap',
        # 'Time',
        # 'Room',
        'Prof'
    ]

    classes_body = [
        [c['classNumber'], 
        c['section'], 
        " ".join(c['campusLocation'].split()), # replace adjacent white spaces with single spaces
        '{}/{}'.format(c['enrolTotal'], c['enrolCap']),
        # c['time'],
        # c['room'],
        c['instructor']] for c in class_info['classes']
    ][int(NO_IN_PAGE * (int(page) - 1)):int(min(int(NO_IN_PAGE * int(page)), len(classes) - 1))]

    response.add_field(
        name = 'Classes (page {} of {})'.format(page, (len(classes) - 1 )// NO_IN_PAGE + 1),
        value = '```' + tabulate(classes_body, classes_head) + '```',
        inline = False
    )

    # add last updated
    response.set_footer(
        text = 'Last updated: ' + class_info['dateUpdated'] + ' ' * 30
    )

    
    if type(response) == discord.Embed:
        await ctx.send(embed=response)
    else:
        await ctx.send(response)

# run bot
bot.run(TOKEN)


