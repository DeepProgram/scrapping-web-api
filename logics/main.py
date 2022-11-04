import json
import time
import re
import urllib.parse
from db.db_sql_models import Upwork, ScrapingStatus
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from fake_useragent import UserAgent


def create_Driver():
    options = uc.ChromeOptions()
    options.headless = False
    ua = UserAgent()
    # ua.update()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    # PROXY = "127.0.0.1:8889"
    # options.add_argument('--proxy-server=%s' % PROXY)
    options.add_argument('disable-extensions')
    options.add_argument("disable-default-apps")
    options.add_argument('disable-component-extensions-with-background-pages')
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--start-fullscreen')
    # options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument("--incognito")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_experimental_option('useAutomationExtension', False)
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("disable-infobars")

    driver = uc.Chrome(executable_path=r"D:\Python-Development\Projects\Free-Up-Scrapper\chromedriver.exe",
                       options=options)
    return driver


def load_individual_job_page(driver, job_page_element):
    data_dict = {}
    time.sleep(1)
    ActionChains(driver).move_to_element(job_page_element).perform()
    time.sleep(1)
    job_page_element.click()
    time.sleep(5)
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


def load_initial_page(driver, sql_db, search_key, str_uuid):
    time.sleep(2)
    driver.get(f"https://www.upwork.com/nx/jobs/search/?q={urllib.parse.quote(search_key)}&sort=recency")
    status_table_row = ScrapingStatus()
    status_table_row.user_id = str_uuid
    status_table_row.status = "page_loaded"
    sql_db.add(status_table_row)
    sql_db.commit()
    time.sleep(2)


def process_full_page(driver, sql_db, str_uuid, search_key):
    elements = driver.find_elements(By.CSS_SELECTOR,
                                    "section[class='up-card-section up-card-list-section up-card-hover']")
    for index, element in enumerate(elements):
        print(f"On Element {index}")
        try:
            job_data = load_individual_job_page(driver, element)
        except Exception as e:
            break
        db_upwork_table_row = Upwork()
        db_upwork_table_row.user_id = str_uuid
        db_upwork_table_row.search_query = search_key
        db_upwork_table_row.search_result = json.dumps(job_data)
        db_upwork_table_row.add_time = int(time.time())
        sql_db.add(db_upwork_table_row)
        sql_db.commit()

        status_table_row = ScrapingStatus()
        status_table_row.user_id = str_uuid
        status_table_row.status = "data"
        sql_db.add(status_table_row)
        sql_db.commit()

        button_element = driver.find_element(By.CSS_SELECTOR, "button[class='up-btn up-btn-link up-slider-prev-btn "
                                                              "d-block']")
        button_element.click()
    ActionChains(driver).move_to_element(driver.find_element(By.CSS_SELECTOR, "li[class='why-upwork-dropdown "
                                                                              "nav-dropdown my-5 my-lg-0']")).perform()
    time.sleep(1)


def load_multiple_page(sql_db, str_uuid, search_key, page_count):
    driver = create_Driver()
    status_table_row = ScrapingStatus()
    status_table_row.user_id = str_uuid
    status_table_row.status = "selenium_started"
    sql_db.add(status_table_row)
    sql_db.commit()

    for page_no in range(1, page_count + 1):
        if page_no == 1:
            load_initial_page(driver, sql_db, search_key, str_uuid)
        driver.get_screenshot_as_file(f"p{page_no}.png")
        process_full_page(driver, sql_db, str_uuid, search_key)
        status_table_row = ScrapingStatus()
        status_table_row.user_id = str_uuid
        status_table_row.status = str(page_no)
        sql_db.add(status_table_row)
        sql_db.commit()

        if page_no < page_count:
            try:
                pagination_elements = driver.find_elements(By.CSS_SELECTOR, "li[class='pagination-link']")
                for element in pagination_elements:
                    if element.text == "Next":
                        ActionChains(driver).move_to_element(element).perform()
                        time.sleep(2)
                        element.click()
                        driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except Exception as e:
                with open("exception_log.txt", "a") as f:
                    f.write(str(e) + "\n")
                print(e)
            time.sleep(1)
    driver.close()
    driver.quit()

    status_table_row = ScrapingStatus()
    status_table_row.user_id = str_uuid
    status_table_row.status = "completed"
    sql_db.add(status_table_row)
    sql_db.commit()


def start_automation(sql_db, str_uuid, search_key, page_count):
    status_table_row = ScrapingStatus()
    status_table_row.user_id = str_uuid
    status_table_row.status = "automation_started"
    sql_db.add(status_table_row)
    sql_db.commit()
    load_multiple_page(sql_db, str_uuid, search_key, page_count)


