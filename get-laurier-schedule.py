from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from dotenv import load_dotenv
load_dotenv()

# Find element with WebDriverWait to prevent flakinesss
def wait_for_selector(driver, selector, seconds=10):
    wait = WebDriverWait(driver, seconds)
    element = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    return element

# Use selenium to get all the Laurier class info
# for the current term
def getClassSchedule(driver):
    driver.get("https://loris.wlu.ca/register/ssb/term/termSelection?mode=search")

    # Select desired term
    open_search = wait_for_selector(driver, "b[role='presentation']")
    open_search.click()
    search = wait_for_selector(driver, "input#s2id_autogen1_search")
    search.send_keys(os.getenv('LAURIER_TERM'))
    select = wait_for_selector(driver, ".select2-result-label div")
    select.click()
    go_button = wait_for_selector(driver, "button#term-go")
    go_button.click()

    # Select to search all Business courses
    search = wait_for_selector(driver, "#s2id_txt_subject input")
    search.click()
    search.send_keys("Business")
    correct_option = wait_for_selector(driver, ".select2-results .select2-result-label div")
    correct_option.click()
    go_button = wait_for_selector(driver, "button#search-go")
    go_button.click()

    # Scrape each class
    courses = {}
    page = 1
    while True:
        tbody = wait_for_selector(driver, "tbody")
        wait_for_selector(tbody, "tr")
        class_rows = tbody.find_elements(By.CSS_SELECTOR, "tr")
        page += 1
        for class_row in class_rows:
            class_data = {}
            class_data["term"] = wait_for_selector(driver, "h4.search-results-header").text.replace("Term: ", "")

            # Open details popup
            wait_for_selector(class_row, "a.section-details-link").click() 
            wrapper_div = wait_for_selector(driver, "#classDetailsContentDetailsDiv")
            class_data["classNumber"] = wait_for_selector(wrapper_div, "#courseReferenceNumber").text
            class_data["section"] = wait_for_selector(wrapper_div, "#sectionNumber").text
            class_data["campusLocation"] = wrapper_div.text.split("\n")[2].replace("Campus: ", "")
            # Prepend type to section number for clarity
            type = wrapper_div.text.split("\n")[3].replace("Schedule Type: ", "")
            class_data["section"] = type + " " + wait_for_selector(wrapper_div, "#sectionNumber").text
            # Get course code
            course_name = "BU" + wait_for_selector(wrapper_div, "#courseNumber").text

            # Meeting details section
            wait_for_selector(driver, "#facultyMeetingTimes").click()
            # Schedule
            try:
                days_text = wait_for_selector(
                    driver, ".right > div").text.replace("A", "").replace("P", "").replace("M", "").replace(" ", "")
                schedule_list = wait_for_selector(driver, "#classDetailsContentDiv ul")
                days = schedule_list.find_elements(By.CSS_SELECTOR, "li")
                for day in days:
                    if day.get_attribute("aria-checked") == "true":
                        days_text += day.get_attribute("data-abbreviation")
                class_data["time"] = days_text.replace("R", "Th")
            except TimeoutException:
                # The date information is not there
                class_data["time"] = "Unknown" # TODO: Should this be something else?
            # Instructor
            class_data["instructor"] = wait_for_selector(
                driver, ".meeting-faculty").text.replace("Instructor:", "").strip(" ")
            # Location
            try:
                location = wait_for_selector(driver, ".right > div:nth-child(2)").text
                location_list = location.split("|")
                if len(location_list) == 3:
                    location = location_list[2].replace(" Room ", "")
            except TimeoutException:
                # The location information is not there
                location = "Unknown"
            class_data["room"] = location

            # Enrollment/Waitlist details section
            wait_for_selector(driver, "#enrollmentInfo").click()
            # Enrollment
            wait_for_selector(driver, "#classDetailsContentDetailsDiv span[dir='ltr']")
            spans = driver.find_elements(By.CSS_SELECTOR, "#classDetailsContentDetailsDiv span[dir='ltr']")
            class_data["enrolCap"] = spans[1].text
            class_data["enrolTotal"] = spans[0].text

            # Close details popup
            wait_for_selector(driver, ".ui-icon-closethick").click()

            # Add to course dictionary
            print(class_data)
            if course_name in courses:
                courses[course_name].append(class_data)
            else:
                courses[course_name] = [class_data]
        
        # Try to go to the next page and get all the rows again
        old_page_num = wait_for_selector(driver, ".page-number").get_attribute("value")
        try:
            print("Loading next page...")
            wait_for_selector(driver, "button[title='Next'].enabled").click()
        except TimeoutException:
            # No more next button
            print("No next page")
            print("All pages scraped")
            break
        # Make sure the page actually changed (takes time to load)
        WebDriverWait(driver, 10).until(
            lambda _: driver.find_element_by_css_selector(".page-number").get_attribute("value") != old_page_num)
        print(f"Loaded page {page}")

    return courses

if __name__ == "__main__":
    driver = webdriver.Chrome()
    try:
        courses = getClassSchedule(driver)
        print(courses)
    finally:
        driver.quit()
