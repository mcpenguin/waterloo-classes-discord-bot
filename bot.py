import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from tabulate import tabulate

import requests
import json

import re

from pymongo import MongoClient

load_dotenv()

# get env vars
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')
API_KEY = os.getenv('API_KEY')

CURRENT_TERM = '1219'
NO_IN_PAGE = 5

PREFIX = 'wc?'

API_URL = 'https://openapi.data.uwaterloo.ca/v3'

# get color config from json file
color_config = json.load(open('color_config.json'))

# connect to mongodb database
client = MongoClient(MONGO_URL)
db = client['waterloo']['courses']

# convert rgb string into rgb tuple
def convert_rgb_to_tuple(rgb):
    rgb_string = rgb[1:]
    if len(rgb_string) == 6:
        return (int(rgb_string[0:2], 16), int(rgb_string[2:4], 16), int(rgb_string[4:6], 16))
    else:
        return (0, 0, 0)

# get class info 
def get_class_info(subjectCode, catalogNumber, term = CURRENT_TERM):
    
    # fetch class info from database
    class_info = db.find({'subjectCode': subjectCode, 'catalogNumber': catalogNumber, 'term': term})
    
    db_class_info = None
    for x in class_info:
        db_class_info = x
        break

    # if class info is None, return does not exist error
    if db_class_info == None:
        return 'Class does not exist'

    # if class does exist, fetch additional class info using the UW API
    r = requests.get(f"{API_URL}/Courses/{term}/{subjectCode}/{catalogNumber}", headers={'X-API-KEY': API_KEY})
    # return the combined info
    return {**db_class_info, **r.json()[0]}

# get class number 
def get_class_section_info(subjectCode, catalogNumber, classNo, term = CURRENT_TERM):
    class_info = db.find({'subjectCode': subjectCode , 'catalogNumber': catalogNumber, 'term': term})
    for x in class_info[0]['classes']:
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

# parse prerequisites from reqdesc (from uwapi response)
def parse_prerequisites(reqdesc):
    result = {
        'prereq': None,
        'antireq': None,
        'coreq': None,
    }
    if reqdesc == None:
        return result

    # get prereq, antireq, and coreq from reqdesc
    prereq = re.search('(Prereq:).*?(\.)', reqdesc + '.')
    antireq = re.search('(Antireq:).*?(\.)', reqdesc + '.')
    coreq = re.search('/(Coreq:).*(\.)/g', reqdesc + '.')
    
    # remove first word for prereq, antireq and coreq
    if prereq != None:
        result['prereq'] = prereq.group(0).split(' ')[1:]
    if antireq != None:
        result['antireq'] = antireq.group(0).split(' ')[1:]
    if coreq != None:
        result['coreq'] = coreq.group(0).split(' ')[1:]

    print(result)
    return result

# setup discord client and connect to user
bot = commands.Bot(command_prefix=PREFIX, help_command=None)
bot.remove_command('help')

# set status of discord bot
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f'Type {PREFIX}help for usage'))

# get help info object from help.json
help_info = json.load(open('help.json'))

# redefine help command
@bot.command()
async def help(ctx):
    # get params from ctx
    content = ctx.message.content
    params = content.split(" ")[1:]

    response = 'Invalid command, please try again'

    # generic help message
    if len(params) == 0:
        # get list of commands as string
        commandString = '```' + f'{PREFIX}help -- Shows this message \n' + '\n'.join([f"{PREFIX}{x} -- {help_info[x]['desc']}" for x in help_info]) + '```'

        # initialize embed
        response = discord.Embed(
            title='Commands', 
            description=commandString, 
            color=discord.Color.from_rgb(255, 255, 255)
        )

    # specific command hele
    else:
        # get command
        command = params[0]

        # get help message for command
        command_info = help_info.get(command, None)
        if command_info == None:
            response = 'Invalid command, please try again'
        else:
            response = discord.Embed(
                title = f'Help for command {PREFIX}{command}',
                description = command_info['desc'],
            )

            response.add_field(
                name = 'Usage',
                value = command_info['use'],
                inline = False
            )

            response.add_field(
                name = 'Examples',
                # join examples into bullet list
                value = '```' + "\n".join(command_info['examples']) + '```',
                inline = False
            )

    # send response
    if type(response) == discord.Embed:
        await ctx.send(embed=response)
    else:
        await ctx.send(response)

# bot info
@bot.command(name='info', help='Get bot info')
async def info(ctx):

    # initialize embed
    response = discord.Embed(
        title='Waterloo Classes Bot', 
        description='''
            *Waterloo Classes Bot* is a bot that allows you to search for classes offered by the University of Waterloo, using the UWaterloo Open Data API and a web scraper for classes.uwaterloo.ca.
        ''', 
        url='https://github.com/mcpenguin/waterloo-classes-discord-bot',
        color=discord.Color.from_rgb(255, 255, 255)
    )

    # get bot info
    response.add_field(
        name = 'Author',
        value = 'Marcus Chan (https://github.com/mcpenguin)',
        inline = False
    )

    response.add_field(
        name = 'Version',
        value = '1.0.0',
        inline = False
    )

    await ctx.send(embed=response)

# respond to messages
@bot.command(name='class', help='Get class info')
async def get_class_list(ctx):
    # get params
    content = ctx.message.content
    params = content.split(" ")[1:]

    # initialize generic response
    response = 'The system could not find the specified class/course, please try again'

    # usage
    # ?class [subject code] [catalog number] (-t term) (-p page) (-c class_no) 
    subjectCode = params[0].upper()
    catalogNumber = str(params[1]).upper()

    # get tag values (if they exist)
    term = get_tag_value('-t', content, CURRENT_TERM)
    page = get_tag_value('-p', content, 1)
    class_no = get_tag_value('-c', content, None)

    # get color of embed from subject code
    color = convert_rgb_to_tuple(color_config[subjectCode]['color']['background'])
    disc_color = discord.Color.from_rgb(color[0], color[1], color[2])

    # get class info
    class_info = get_class_info(subjectCode, catalogNumber, term)
    # if class is not valid, return error response 
    if type(class_info) == str:
        await ctx.send(response)
        return

    # get course info and list of classes
    if class_no == None:

        # create response
        response = discord.Embed(
            title = f"{class_info['subjectCode']} {class_info['catalogNumber']} - {class_info['title']} [{class_info['termName']}]",
            color = disc_color,
            description = class_info['description']
        )

        # add course level
        response.add_field(
            name = 'Level',
            value = {
                'UG': 'Undergraduate',
                'G': 'Graduate'
            }[class_info['associatedAcademicCareer']],
        ) 
        # add course units
        response.add_field(
            name = 'Units',
            value = class_info['units'],
            inline = True
        )

        # add course reqs
        reqs = parse_prerequisites(class_info['requirementsDescription'])
        print(' '.join(reqs['coreq']) if reqs['coreq'] != None else 'None')

        # add empty field for new line
        response.add_field(name = chr(173), value = chr(173))

        response.add_field(
            name = 'Prerequisites',
            value = ' '.join(reqs['prereq']) if reqs['prereq'] != None else 'None',
            inline = False
        )

        # add course description
        response.add_field(
            name = 'Antirequisites',
            value = ' '.join(reqs['antireq']) if reqs['antireq'] != None else 'None',
            inline = True
        )

        response.add_field(
            name = 'Corequisites',
            value = ' '.join(reqs['coreq']) if reqs['coreq'] != None else 'None',
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
        ][int(NO_IN_PAGE * (int(page) - 1)):int(min(int(NO_IN_PAGE * int(page)), len(classes)))]

        response.add_field(
            name = 'Classes (page {} of {})'.format(page, (len(classes) - 1 )// NO_IN_PAGE + 1),
            value = '```' + tabulate(classes_body, classes_head) + '```',
            inline = False
        )

        # add last updated
        response.set_footer(
            text = 'Last updated: ' + class_info['dateUpdated'] + ' EST'
        )

    # if class number is specified, get the specific class info
    else:
        class_section_info = get_class_section_info(subjectCode, catalogNumber, class_no, term)
        # check whether valid class
        if type(class_section_info) == str:
            await ctx.send(response)
            return
        
        # create response
        response = discord.Embed(
            title = class_info['subjectCode'] + ' ' + class_info['catalogNumber'] + ' - ' + class_info['title'],
            color = disc_color,
        )

        response.add_field(
            name = 'Class #',
            value = class_section_info['classNumber'],
            inline = True
        )

        response.add_field(
            name = 'Section',
            value = class_section_info['section'],
            inline = True
        )

        response.add_field(
            name = 'Capacity',
            value = '{}/{}'.format(class_section_info['enrolTotal'], class_section_info['enrolCap']),
            inline = False
        )

        response.add_field(
            name = 'Campus Location',
            value = " ".join(class_section_info['campusLocation'].split()),
            inline = False

        )

        response.add_field(
            name = 'Time',
            value = "Not Given" if class_section_info['time'] == "" else class_section_info['time'],
            inline = True
        )

        response.add_field(
            name = 'Room',
            value = class_section_info['room'],
            inline = True
        )

        response.add_field(
            name = 'Instructor',
            value = class_section_info['instructor'],
            inline = False
        )

        # add last updated
        response.set_footer(
            text = 'Last updated: ' + class_info['dateUpdated'] + ' EST'
        )

    
    if type(response) == discord.Embed:
        await ctx.send(embed=response)
    else:
        await ctx.send(response)

# handle errors for discord bot
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found, type ?help for list of commands')

# run bot
bot.run(TOKEN)


