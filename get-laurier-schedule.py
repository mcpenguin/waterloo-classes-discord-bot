from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Find element with WebDriverWait to prevent flakinesss
def wait_for_selector(driver, selector, seconds=10):
    wait = WebDriverWait(driver, seconds)
    element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    return element

# Use selenium to get all the Laurier class info
# for the current term
def getClassSchedule(driver):
    driver.get("https://loris.wlu.ca/register/ssb/term/termSelection?mode=search")
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

    # Select to search all Business courses
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

    # Scrape each class
    courses = []
    while True:
        tbody = wait_for_selector(driver, "tbody")
        wait_for_selector(tbody, "tr")
        class_rows = tbody.find_elements(By.CSS_SELECTOR, "tr")
        for class_row in class_rows:
            course = {}
            course["term"] = wait_for_selector(driver, "h4.search-results-header").text.replace("Term: ", "")

            # Open details popup
            wait_for_selector(class_row, "a.section-details-link").click() 
            wrapper_div = wait_for_selector(driver, "#classDetailsContentDetailsDiv")
            course["classNumber"] = wait_for_selector(wrapper_div, "#courseReferenceNumber").text
            course["section"] = wait_for_selector(wrapper_div, "#sectionNumber").text
            course["campusLocation"] = wrapper_div.text.split("\n")[2].replace("Campus: ", "")
            # Prepend type to section number for clarity
            type = wrapper_div.text.split("\n")[3].replace("Schedule Type: ", "")
            course["section"] = type + " " + wait_for_selector(wrapper_div, "#sectionNumber").text

            # Meeting details section
            wait_for_selector(driver, "#facultyMeetingTimes").click()
            # Schedule
            days_text = wait_for_selector(
                driver, ".right > div").text.replace("A", "").replace("P", "").replace("M", "").replace(" ", "")
            schedule_list = wait_for_selector(driver, "#classDetailsContentDiv ul")
            days = schedule_list.find_elements(By.CSS_SELECTOR, "li")
            for day in days:
                if day.get_attribute("aria-checked") == "true":
                    days_text += day.get_attribute("data-abbreviation")
            course["time"] = days_text.replace("R", "Th")
            # Instructor
            course["instructor"] = wait_for_selector(driver, ".meeting-faculty").text.replace("Instructor:", "")
            # Location
            location = wait_for_selector(driver, ".right > div:nth-child(2)").text
            location_list = location.split("|")
            if len(location_list) == 3:
                location = location_list[2].replace(" Room ", "")
            course["room"] = location

            # Enrollment/Waitlist details section
            wait_for_selector(driver, "#enrollmentInfo").click()
            # Enrollment
            wait_for_selector(driver, "#classDetailsContentDetailsDiv span[dir='ltr']")
            spans = driver.find_elements(By.CSS_SELECTOR, "#classDetailsContentDetailsDiv span[dir='ltr']")
            course["enrolCap"] = spans[1].text
            course["enrolTotal"] = spans[0].text

            # Close details popup
            wait_for_selector(driver, ".ui-icon-closethick").click()

            print(course)
            courses.append(course)
        
        # Try to go to the next page and get all the rows again
        old_page_num = wait_for_selector(driver, ".page-number").get_attribute("value")
        try:
            print("Loading next page...")
            wait_for_selector(driver, "button[title='Next'].enabled").click()
        except TimeoutException:
            # No more next button
            print("All pages scraped")
            break
        # Make sure the page actually changed (takes time to load)
        WebDriverWait(driver, 10).until(
            lambda _: wait_for_selector(driver, ".page-number").get_attribute("value") != old_page_num)
        print("Loaded next page")

    return courses

if __name__ == "__main__":
    driver = webdriver.Chrome()
    try:
        getClassSchedule(driver)
    finally:
        driver.quit()