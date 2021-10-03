import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

import requests
import json
import re
from pymongo import MongoClient

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
def get_uwflow_metrics(driver, subjectCode, catalogNumber, TIMEOUT = 2):
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
def get_class_info(driver, subjectCode, catalogNumber, term = CURRENT_TERM, tries=0):
    
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
    uw_flow_metrics = get_uwflow_metrics(driver, subjectCode, catalogNumber)

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