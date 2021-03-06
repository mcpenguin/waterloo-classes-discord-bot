# python script to get uwflow metrics

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# get mongodb database using mongo client
client = MongoClient(os.getenv('MONGO_URL'))

# get all courses from mongo client
collection = client['waterloo']['courses-descriptions']
courses = list(collection.find({}, {'subjectCode': 1, 'catalogNumber': 1, '_id': 0}).sort([('subjectCode', 1), ('catalogNumber', 1)]))

chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(executable_path=os.getenv("DRIVER_PATH"), options=chrome_options)

UW_FLOW_URL = 'https://uwflow.com/course'
# num of seconds before timeout
TIMEOUT = 2

subjectCode = None
catalogNumber = None
tmp_subjectCode = 'ACC'

for course in courses:
    subjectCode = course['subjectCode']
    catalogNumber = course['catalogNumber']

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

        collection.update_one(
            {'subjectCode': subjectCode, 'catalogNumber': catalogNumber}, 
            {'$set': {'percent_liked': percent_liked, 'percent_easy': percent_easy, 'percent_useful': percent_useful}}
        )

        print(f"Retrieved UW Flow metrics for {subjectCode} {catalogNumber}")

    except Exception as e:
        print(f"Unable to retrieve course info for course {subjectCode} {catalogNumber}")
        pass

    if tmp_subjectCode != subjectCode:
        print(f'Retrieved UW Flow metrics for {subjectCode}')
        tmp_subjectCode = subjectCode

print(f'Retrieved UW Flow metrics for {subjectCode}')
driver.close()