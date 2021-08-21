from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Use selenium and bs4 to get all the Laurier class info
# for the current term
def getClassSchedule(driver):
    driver.get("https://loris.wlu.ca/register/ssb/term/termSelection?mode=search")
    # Use WebDriverWait to prevent flakinesss
    wait = WebDriverWait(driver, 10)

    # Select desired term
    open_search = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "b[role='presentation']")))
    open_search.click()
    search = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input#s2id_autogen1_search")))
    search.send_keys(os.getenv('LAURIER_TERM'))
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-result-label div"))).click()
    button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#term-go")))
    button.click()

    # Search all Business courses
    search = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#s2id_txt_subject input")))
    search.click()
    search.send_keys("Business")
    correct_option = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-results .select2-result-label div")))
    correct_option.click()
    button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#search-go")))
    button.click()
    time.sleep(10000)

    return

if __name__ == "__main__":
    driver = webdriver.Chrome()
    try:
        getClassSchedule(driver)
    finally:
        driver.quit()