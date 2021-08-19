
# %% [markdown]
# Get class schedule data from classes.uwaterloo.ca (both undergrad + grad), store into MongoDB database
# Takes about 20 minutes to run once

# %%
import mechanize
import json
from bs4 import BeautifulSoup

from datetime import datetime
import pytz

# %%
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# initialize scheduler
sched = BlockingScheduler()

# take env vars from .env file
load_dotenv()

UNDER_LINK = "https://classes.uwaterloo.ca/under.html"
GRAD_LINK = "https://classes.uwaterloo.ca/grad.html"

# url to fetch other course data
WAPI_URL = "https://openapi.data.uwaterloo.ca/v3"

CURRENT_TERM = '1219'

# %%
# get subjects and terms
subjects = []
terms = []

# get form from website
br = mechanize.Browser()
br.open(UNDER_LINK)
br.select_form(action='/cgi-bin/cgiwrap/infocour/salook.pl')

# get list of terms and subjects offered
terms = [item.attrs['value'] for item in br.find_control(name='sess').items]
subjects = [item.attrs['value'] for item in br.find_control(name='subject').items]

# get mongodb database using mongo client
client = MongoClient(os.getenv('MONGO_URL'))

@sched.scheduled_job('interval', minutes=60)
def getClassSchedule():
    for SUBJECT in subjects:
        for TERM in [CURRENT_TERM]: # only update current term

            for link in [UNDER_LINK, GRAD_LINK]:

                # initialize courses list
                courses = []
                # initialize course object
                course = {}

                # get form from website
                br = mechanize.Browser()
                br.open(link)
                br.select_form(action='/cgi-bin/cgiwrap/infocour/salook.pl')

                br.find_control(name='sess').value = [TERM]
                br.find_control(name='subject').value= [SUBJECT]

                response = br.submit()
                # response.read()

                soup = BeautifulSoup(response.read(), 'html.parser')


                # %%
                # get main table for classes 
                mainClassTable = soup.find('table', {'border': '2'})

                # if query has no matches, move on
                if mainClassTable == None:
                    # print("No classes for subject {} for term {}".format(SUBJECT, TERM))
                    continue

                # otherwise, get iterator for children of main table
                mainClassTableChildren = mainClassTable.findChildren("tr", recursive=False)


                # %%
                for child in mainClassTableChildren:
                
                    children = child.findChildren(recursive=False)

                    # if tr is a header row, add course to classes and reinitialize the course object

                    if children[0].name == 'th':
                        # add last updated time to course
                        course['dateUpdated'] = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")

                        # add course to course list
                        courses += [course]

                        # reinitialize course
                        course = {
                            'term': TERM,
                            'level': 'UG' if link == UNDER_LINK else 'G' 
                        }

                    # if tr is a course data row, add details to the course object
                    elif children[0].name == 'td' and len(children) > 2:
                        course['subjectCode'] = children[0].text.strip()
                        course['catalogNumber'] = children[1].text.strip()
                        course['units'] = children[2].text.strip()
                        course['title'] = children[3].text.strip()

                    # if tr is a course notes row, add notes to the current course object
                    elif children[0].name == 'td' and len(children) == 1:
                        course['notes'] = children[0].text

                    # if tr is a course classes row, initialize classes list and iterate over the class table to 
                    # add the classes to the course
                    elif children[0].name == 'td' and len(children) == 2:
                        classes = []
                        class_soup = BeautifulSoup(str(children[1]), 'html.parser')
                        classTableRows = class_soup.find('table').find_all('tr')

                        for row in classTableRows:
                            indiv_class_soup = BeautifulSoup(str(row), 'html.parser')
                            # if table row is not a class (ie it is just headers or notes), we ignore it  
                            # we do this by checking the first element of the table row's children, as that is the class number
                            # if the number is not a number, it cannot be a class, so we can ignore it
                            if indiv_class_soup.find('th') != None or not indiv_class_soup.find_all('td')[0].text.strip().isnumeric():
                                continue
                            
                            # otherwise, the table row is a class, and so we add it to the classes list for the courses
                            else:
                                subchildren = indiv_class_soup.find_all('td')
                                classes += [{
                                    'classNumber': subchildren[0].text.strip() if len(subchildren) >= 1 else None,
                                    'section': subchildren[1].text.strip() if len(subchildren) >= 2 else None,
                                    'campusLocation': subchildren[2].text.strip() if len(subchildren) >= 3 else None,
                                    'enrolCap': subchildren[6].text.strip() if len(subchildren) >= 7 else None,
                                    'enrolTotal': subchildren[7].text.strip() if len(subchildren) >= 8 else None,
                                    'time': subchildren[10].text.strip() if len(subchildren) >= 11 else None,
                                    'room': subchildren[11].text.strip() if len(subchildren) >= 12 else None,
                                    'instructor': subchildren[12].text.strip() if len(subchildren) >= 13 else None,
                                }]

                        course['classes'] = classes

                    # otherwise, the tr is an undefined row, and we ignore it
                    else:
                        continue
                
                # add last updated time to course
                course['dateUpdated'] = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")
                courses += [course]

                # delete old data
                delete_query = {
                    'term': TERM,
                    'subjectCode': SUBJECT,
                    'level': 'UG' if link == UNDER_LINK else 'G'
                }
                client['waterloo']['courses'].delete_many(delete_query)

                # insert new data
                client['waterloo']['courses'].insert_many(courses)

                print('Updated courses for subject {} for term {} for level {}'.format(SUBJECT, TERM, 'UG' if link == UNDER_LINK else 'G'))

# start the scheduling
sched.start()
