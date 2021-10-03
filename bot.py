import os

from datetime import datetime, timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tabulate import tabulate

import requests
import json

import re

from pymongo import MongoClient

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.firefox.options import Options

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

load_dotenv()

# get env vars
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')
API_KEY = os.getenv('API_KEY')

# get current termcode given date (which is a datetime object)
def get_termcode(date):
    # return the 'year' part of the termcode
    year_termcode = int(date.year) - 1900
    # return the 'month' part of the termcode
    # 1 = Winter; 5 = Spring; 9 = Fall
    month_termcode = 1 if date.month < 5 else 5 if date.month < 9 else 9
    return f"{year_termcode}{month_termcode}"

# get 'default' term
# gets the 'next' term if > 15th day of the starting month of the current term; otherwise returns the current term
# so eg Sept 1 2021 -> 1219 (Fall 2021)
# Sept 16 2021 -> 1221 (Winter 2022)
# Sept 27 2021 -> 1221 (Winter 2022) etc
# this is to make sure the default switches just before course selection
def get_default_term():
    # first, get the current term and the next term which currently in
    today = datetime.now()
    current_termcode = get_termcode(datetime.now())
    # next termcode is the termcode of the current time but 16 weeks in the future
    next_termcode = get_termcode(datetime.now() + timedelta(weeks=16))

    if today.month == current_termcode[3] and today.day <= 15:
        return current_termcode
    else:
        return next_termcode

CURRENT_TERM = get_default_term()
NO_IN_PAGE = 5

PREFIX = 'wc?'

API_URL = 'https://openapi.data.uwaterloo.ca/v3'
UW_FLOW_URL = 'https://uwflow.com/course'

# get color config from json file
color_config = json.load(open(os.path.join(__location__, 'color_config.json')))

# connect to mongodb database
client = MongoClient(MONGO_URL)
db_courses = client['waterloo']['courses']
db_courses_descriptions = client['waterloo']['courses-descriptions']

# parse term code into name
# eg 1219 -> "Fall 2021"
def parse_term_code(termcode):
    if termcode != 0:
        season = {'1': 'Winter', '5': 'Spring', '9': 'Fall'}[termcode[3]]
        return f"{season} {int(termcode[0:3]) + 1900}"
    else:
        return "Not Recently Offered"

# get last term code
def get_last_term_code(termcode):
    if termcode[-1] == '9':
        return f"{int(termcode[0:3])}5"
    elif termcode[-1] == '5':
        return f"{int(termcode[0:3])}1"
    else:
        return f"{int(termcode[0:3]) - 1}9"

# convert rgb string into rgb tuple
def convert_rgb_to_tuple(rgb):
    rgb_string = rgb[1:]
    if len(rgb_string) == 6:
        return (int(rgb_string[0:2], 16), int(rgb_string[2:4], 16), int(rgb_string[4:6], 16))
    else:
        return (0, 0, 0)

# get uwflow metrics
def get_uwflow_metrics(subjectCode, catalogNumber, TIMEOUT = 2):
    try:
        driver.get(f"{UW_FLOW_URL}/{subjectCode}{catalogNumber}")
        # wait for page to load
        WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.CLASS_NAME, "iYtUny")))
        # get html of page
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        # get the metrics
        percent_liked = soup.find('div', {'class': 'sc-psQdR'}).text
        [percent_easy, percent_useful] = [x.text for x in soup.find('div', {'class': 'PQBAt'}).find_all('div', {'class': 'jjDvpo'})]

        return {'percent_liked': percent_liked, 'percent_easy': percent_easy, 'percent_useful': percent_useful}

    except Exception as e:
        # print(e)
        # print(f"Unable to retrieve course info for course {subjectCode} {catalogNumber}")

        return {}

# get class info 
def get_class_info(subjectCode, catalogNumber, term = CURRENT_TERM, tries=0):
    
    # fetch class info from database
    class_info = db_courses.find({'subjectCode': subjectCode, 'catalogNumber': catalogNumber, 'term': term})
    
    db_class_info = None
    for x in class_info:
        db_class_info = x
        break

    # if class info is None, try the previous term
    if db_class_info == None:
        if tries < 3:
            return get_class_info(subjectCode, catalogNumber, get_last_term_code(term), tries + 1)
        # after 3 tries, if still no match, let the class info just be a dict with default info
        db_class_info = {
            'term': 0,
            'dateUpdated': 'None',
            'units': 0.5,
        }

    # if class does exist, fetch additional class info from courses_descriptions collection
    course_info = db_courses_descriptions.find({'subjectCode': subjectCode, 'catalogNumber': catalogNumber})
    for x in course_info:
        db_course_info = x
        
        
    # if course info is None, return class does not exist
    if db_course_info == None:
        return 'Class does not exist'

    # if course does indeed exist, get UW Flow metrics
    uw_flow_metrics = get_uwflow_metrics(subjectCode, catalogNumber)

    # return the combined info
    return {'term': term, **db_class_info, **db_course_info}

# get class number 
def get_class_section_info(subjectCode, catalogNumber, classNo, term = CURRENT_TERM):
    class_info = db_courses.find({'subjectCode': subjectCode , 'catalogNumber': catalogNumber, 'term': term})
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
    coreq = re.search('(Coreq:).*?(\.)', reqdesc + '.')
    
    # remove first word for prereq, antireq and coreq
    if prereq != None:
        result['prereq'] = prereq.group(0).split(' ')[1:]
    if antireq != None:
        result['antireq'] = antireq.group(0).split(' ')[1:]
    if coreq != None:
        result['coreq'] = coreq.group(0).split(' ')[1:]

    return result

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

# respond to messages
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

        # add empty field for new line
        # response.add_field(name = chr(173), value = chr(173))

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

# handle errors for discord bot
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found, type ?help for list of commands')

# run bot
if __name__ == '__main__':
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=os.getenv("DRIVER_PATH"), options=firefox_options)
    try:
        bot.run(TOKEN)
    except Exception as e:
        # close driver if any errors arise
        driver.close()



