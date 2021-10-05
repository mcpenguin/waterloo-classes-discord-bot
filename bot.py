import os
import json
import re
from tabulate import tabulate

import discord
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from helpers import get_default_term, get_tag_value, convert_rgb_to_tuple, color_config, get_class_info, parse_term_code, parse_prerequisites, get_class_section_info, terms_course_last_offered

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

load_dotenv()

# get env vars
TOKEN = os.getenv('DISCORD_TOKEN')

CURRENT_TERM = get_default_term()
NO_IN_PAGE = 5

PREFIX = 'wc?'

API_URL = 'https://openapi.data.uwaterloo.ca/v3'
UW_FLOW_URL = 'https://uwflow.com/course'

driver = None

# setup discord client and connect to user
bot = commands.Bot(command_prefix=PREFIX, help_command=None)
bot.remove_command('help')

# set status of discord bot
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f'Type {PREFIX}help for usage'))

# get help info object from help.json
help_info = json.load(open(os.path.join(__location__, 'help.json')))

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

    response.add_field(
        name = 'Add the bot to other servers!',
        value = 'https://discord.com/api/oauth2/authorize?client_id=877440425718333460&permissions=2048&scope=bot',
        inline = False
    )

    await ctx.send(embed=response)

# get information about a class
@bot.command(name='class', help='Get class info')
async def get_class_list(ctx):
    # get params
    content = ctx.message.content
    params = content.split(" ")[1:]

    # initialize generic response
    response = 'The system could not find the specified class/course, please try again'

    # usages
    subjectCode, catalogNumber = None, None
    # case 1: ?class [subject code] [catalog number] (-t term) (-p page) (-c class_no) 
    if params[0].isalpha():
        subjectCode = params[0].upper()
        catalogNumber = str(params[1]).upper()
    # case 2: ?class [subject code][catalog number] (-t term) (-p page) (-c class_no) 
    # ie the subject code and catalog number is concatenated together (eg wc?class cs246e)
    else:
        # split the first part (subject code) and the second part (catalog number)
        parts = re.split('(\d.*)', params[0])
        subjectCode = parts[0].upper()
        catalogNumber = parts[1].upper() 

    # get tag values (if they exist)
    term = get_tag_value('-term', content, CURRENT_TERM)
    page = get_tag_value('-page', content, 1)
    class_no = get_tag_value('-class', content, None)

    print(term, page, class_no)

    # get color of embed from subject code
    color = convert_rgb_to_tuple(color_config[subjectCode]['color']['background'])
    disc_color = discord.Color.from_rgb(color[0], color[1], color[2])

    # get class info
    class_info = get_class_info(driver, subjectCode, catalogNumber, term)
    # if class is not valid, return error response 
    if type(class_info) == str:
        await ctx.send(response)
        return

    # get course info and list of classes
    if class_no == None:
        # make uwflow url
        uwflow_url = UW_FLOW_URL + '/' + class_info['subjectCode'] + class_info['catalogNumber']

        # create response
        response = discord.Embed(
            title = f"{class_info['subjectCode']} {class_info['catalogNumber']} - {class_info['title']} [{parse_term_code(class_info['term'])}]",
            color = disc_color,
            description = class_info['description'] + '\n' + f"[View this course on UW Flow]({uwflow_url})"
        )

        # add course level
        response.add_field(
            name = 'Level',
            value = {
                'UG': 'Undergraduate',
                'GRD': 'Graduate'
            }[class_info['associatedAcademicCareer']],
        ) 
        # add course units
        response.add_field(
            name = 'Units',
            value = class_info['units'],
            inline = True
        )

        # add uwflow metrics (percent liked, easy, useful)
        response.add_field(name = chr(173), value = chr(173))

        response.add_field(
            name = 'Liked % (on UW Flow)',
            value = class_info.get('percent_liked', 'N/A'),
            inline = True
        )

        response.add_field(
            name = 'Easy % (on UW Flow)',
            value = class_info.get('percent_easy', 'N/A'),
            inline = True
        )

        response.add_field(
            name = 'Useful % (on UW Flow)',
            value = class_info.get('percent_useful', 'N/A'),
            inline = True
        )

        # add course reqs
        reqs = parse_prerequisites(class_info['requirementsDescription'])

        response.add_field(
            name = 'Prerequisites',
            value = ' '.join(reqs['prereq']) if reqs['prereq'] != None else 'None',
            inline = False
        )

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
      
        # add course classes only if term code is not 0
        if class_info['term'] != 0:
            classes = class_info['classes']
            classes_head = [ '#', 'Sect', 'Camp Loc', 'Cap', 'Prof']

            classes_body = [
                [c['classNumber'], 
                c['section'], 
                " ".join(c['campusLocation'].split()), 
                '{}/{}'.format(c['enrolTotal'], c['enrolCap']),
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

        else:
            response.set_footer(text = 'No classes available for last three terms')

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

# get information about when a course was last offered
@bot.command(name='history')
async def get_course_history(ctx):
    # get params
    content = ctx.message.content
    params = content.split(" ")[1:]

    page = get_tag_value('-page', content, 1)

    # initialize generic response
    response = 'The system could not find the specified class/course, please try again'

    # usages
    subjectCode, catalogNumber = None, None
    # case 1: ?class [subject code] [catalog number] (-t term) (-p page) (-c class_no) 
    if params[0].isalpha():
        subjectCode = params[0].upper()
        catalogNumber = str(params[1]).upper()
    # case 2: ?class [subject code][catalog number] (-t term) (-p page) (-c class_no) 
    # ie the subject code and catalog number is concatenated together (eg wc?class cs246e)
    else:
        # split the first part (subject code) and the second part (catalog number)
        parts = re.split('(\d.*)', params[0])
        subjectCode = parts[0].upper()
        catalogNumber = parts[1].upper() 

    # get color of embed from subject code
    color = convert_rgb_to_tuple(color_config[subjectCode]['color']['background'])
    disc_color = discord.Color.from_rgb(color[0], color[1], color[2])

    # get the last offerings of the course
    offerings_list = terms_course_last_offered(subjectCode, catalogNumber)
    if len(offerings_list) == 0:
        return
    # get class info
    class_info = get_class_info(driver, subjectCode, catalogNumber)
    # if class is not valid, return error response 
    if type(class_info) == str:
        await ctx.send(response)
        return

    # create response
    response = discord.Embed(
        title = class_info['subjectCode'] + ' ' + class_info['catalogNumber'] + ' - ' + class_info['title'],
        description = f"This course has been offered {len(offerings_list)} times since 2001.",
        color = disc_color,
    )

    # add offerings
    offerings_head = [ 'Term Name', '# Enrolled', '# Cap', '# Sections', ]
    offerings_body = [
        [
            parse_term_code(o['term']),
            sum([int(c['enrolTotal']) for c in o['classes']]),
            sum([int(c['enrolCap']) for c in o['classes']]),
            len(o['classes']),
        ] for o in offerings_list
    ][int(NO_IN_PAGE * 2 * (int(page) - 1)):int(min(int(NO_IN_PAGE * 2 * int(page)), len(offerings_list)))]

    response.add_field(
        name = 'Offerings (page {} of {})'.format(page, (len(offerings_list) - 1 )// (NO_IN_PAGE * 2) + 1),
        value = '```' + tabulate(offerings_body, offerings_head) + '```',
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
        await ctx.send('Command not found, type wc?help for list of commands')

# run bot
if __name__ == '__main__':
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=os.getenv("DRIVER_PATH"), options=firefox_options)
    print("Driver is up and running")
    try:
        bot.run(TOKEN)
    except Exception as e:
        # close driver if any errors arise
        driver.close()
    finally:
        driver.close()



