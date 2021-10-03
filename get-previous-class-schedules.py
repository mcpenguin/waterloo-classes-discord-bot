# python script to get previous years' class schedules

import mechanize
import json
from bs4 import BeautifulSoup
import requests

from datetime import datetime, timedelta
import pytz

# %%
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# python script to get uwflow metrics

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.firefox.options import Options

from bs4 import BeautifulSoup

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# UW_FLOW_URL = 'https://uwflow.com/course'
# num of seconds before timeout

subjectCode = None
catalogNumber = None
tmp_subjectCode = 'ACC'

url = "https://cs.uwaterloo.ca/cscf/teaching/schedule/expert"
TIMEOUT = 2

def get_previous_class_schedule(driver, client):
    driver.get(url)
    # wait for page to load
    WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.NAME, "select")))

    # switch to select form frame
    driver.switch_to.frame(0)
    # get page source of select form
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # get list of terms, levels and subjects
    # list of termcodes
    terms = [item.attrs['value'] for item in soup.find('select', {'name': 'sess'}).find_all('option')]
    # list of levels (undergrad or grad)
    levels = [item.attrs['value'] for item in soup.find('select', {'name': 'level'}).find_all('option')]
    # list of subject codes (get if non empty)
    subjects = [item.attrs['value'] for item in soup.find('select', {'name': 'subject'}).find_all('option') if item.attrs['value']]

    # print(terms, levels, subjects)

    return

if __name__ == '__main__':
    # get mongodb database using mongo client
    client = MongoClient(os.getenv('MONGO_URL'))

    # get all courses from mongo client
    collection = client['waterloo']['courses-descriptions']
    courses = list(collection.find({}, {'subjectCode': 1, 'catalogNumber': 1,
                '_id': 0}).sort([('subjectCode', 1), ('catalogNumber', 1)]))
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=os.getenv(
        "DRIVER_PATH"), options=firefox_options)
    try:
        get_previous_class_schedule(driver, client)
    finally:
        driver.close()

