import concurrent.futures
import json
import time
import re
import urllib.parse
from functools import partial

import undetected_chromedriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from fake_useragent import UserAgent


def create_Driver():
    options = uc.ChromeOptions()
    options.headless = True
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('disable-extensions')
    options.add_argument("disable-default-apps")
    options.add_argument('disable-component-extensions-with-background-pages')
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(executable_path="C:\\Users\\sudo\\Desktop\\scrapping-web-api-devs\\logics\\chromedriver.exe",
                       options=options)
    return driver


def load_individual_job_page(driver, job_page_element):
    data_dict = {}
    time.sleep(2)
    ActionChains(driver).move_to_element(driver.find_element(By.CSS_SELECTOR, "li[class='why-upwork-dropdown "
                                                                              "nav-dropdown my-5 my-lg-0']")).perform()
    time.sleep(2)
    job_page_element.click()
    time.sleep(4)
    data_dict["title"] = get_job_title(driver)
    data_dict["url"] = get_job_url(driver)
    data_dict["details"] = get_job_details(driver)
    return data_dict


def get_job_url(driver):
    data = driver.find_element(By.CSS_SELECTOR, "a[class='up-btn up-btn-link m-0 d-none d-md-block']")
    job_url = data.get_attribute("href")
    return job_url


def get_job_title(driver):
    data = driver.find_element(By.CSS_SELECTOR, "h1[class='my-0 mr-10 display-rebrand']")
    job_title = data.text
    return job_title


def get_job_details(driver):
    job_details_dict = {}
    section_elements = driver.find_elements(By.CSS_SELECTOR, "section[class='up-card-section']")
    for index, content in enumerate(section_elements[:5]):
        if index == 0:
            job_applicable_location, job_posted_time = process_job_applicable_location_time(content)
            job_details_dict["job_applicable_location"] = job_applicable_location
            job_details_dict["job_posted_time"] = job_posted_time
        elif index == 1:
            job_description = content.text
            job_details_dict["job_description"] = job_description
        elif index == 2:
            job_type_details_dict = process_job_type_details(content)
            job_details_dict["job_type_details"] = job_type_details_dict
        elif index == 3:
            required_job_skill_dict = process_job_skills(content)
            job_details_dict["required_skills"] = required_job_skill_dict
        elif index == 4:
            job_activity_dict = process_job_activity(content)
            job_details_dict["job_activity"] = job_activity_dict
    return job_details_dict


def process_job_applicable_location_time(content):
    job_applicable_location_and_post_time = re.split(r"Posted |Renewed ", content.text)[1].split("\n")
    if len(job_applicable_location_and_post_time) != 2:
        return ["N/A", "N/A"]
    job_applicable_location = job_applicable_location_and_post_time[1]
    job_posted_time = job_applicable_location_and_post_time[0]
    return [job_applicable_location, job_posted_time]


def process_job_type_details(content):
    job_info_dict = {}
    for list_element in content.find_elements(By.TAG_NAME, "li"):
        job_info = list_element.text.split("\n")
        if len(job_info) == 1:
            job_info_dict["job_location"] = job_info[0]
        else:
            attribute_key = job_info[1]
            attribute_value = job_info[0]
            if attribute_key == "Hourly" or attribute_key == "Fixed-price":
                job_info_dict["payment_type"] = attribute_key
                job_info_dict["amount"] = attribute_value
            else:
                job_info_dict[attribute_key] = attribute_value
    return job_info_dict


def process_job_skills(content):
    job_skills_required_dict = {}
    for skills in content.find_elements(By.XPATH, "div/div/div"):
        skills_list = skills.text.split("\n")
        if len(skills_list) == 0:
            continue
        job_skills_required_dict[skills_list[0]] = \
            skills_list[1:] if "more" not in skills_list[-1] else skills_list[1:-1]
    return job_skills_required_dict


def process_job_activity(content):
    job_activity_dict = {}
    for values in content.find_elements(By.XPATH, "div/ul/li"):
        each_activity = values.text.split("\n")
        if len(each_activity) == 2:
            job_activity_dict[each_activity[1]] = each_activity[0]
    return job_activity_dict

def load_initial_page(driver, redis_db, search_key, str_uuid):
    driver.get(f"https://www.upwork.com/nx/jobs/search/?q={urllib.parse.quote(search_key)}&sort=recency")
    redis_db.rpush(str_uuid, "page_loaded")
    time.sleep(2)


def process_full_page(driver, redis_db, str_uuid):
    elements = driver.find_elements(By.CSS_SELECTOR,
                                    "section[class='up-card-section up-card-list-section up-card-hover']")
    for index, element in enumerate(elements):
        job_data = load_individual_job_page(driver, element)
        redis_db.rpush(str_uuid, json.dumps(job_data))
        button_element = driver.find_element(By.CSS_SELECTOR, "button[class='up-btn up-btn-link up-slider-prev-btn "
                                                              "d-block']")
        button_element.click()
    


def load_multiple_page(redis_db, str_uuid, search_key, page_count):
    driver = create_Driver()
    redis_db.rpush(str_uuid, "selenium_started")

    for page_no in range(1, page_count + 1):
        if page_no == 1:
            load_initial_page(driver, redis_db, search_key, str_uuid)
        process_full_page(driver, redis_db, str_uuid)
        redis_db.rpush(str_uuid, str(page_no))  # Added Page No In Redis Database
        if page_no < page_count:
            try:
                next_page_element = driver.find_element(By.CSS_SELECTOR,
                                                    "button[class='up-pagination-item up-btn up-btn-link']")
                next_page_element.click()
            except Exception as e:
                print(e)
            time.sleep(1)
    driver.close()
    driver.quit()
    redis_db.rpush(str_uuid, "end")


def start_automation(redis_db, str_uuid, search_key, page_count):
    redis_db.rpush(str_uuid, "automation_started")
    load_multiple_page(redis_db, str_uuid, search_key, page_count)

