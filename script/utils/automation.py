import os
import csv
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from .elements_locators import ECardsLocators as El
from .elements_locators import EnrollwareLocators as Els
from .helper import (
    logger, click_element,
    input_element, select_by_text,
    wait_while_element_is_displaying,
    safe_navigate_to_url, check_element_exists
)
from .email_log import add_entry_if_new

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
instructors_data_csv = f"{BASE_DIR}/data/instructorList.csv"
load_dotenv(verbose=True)

def login_to_ecards(driver) -> bool:
    BASE_URL = "https://ecards.heart.org"
    """Login to eCards with comprehensive error handling and retry logic."""
    try:
        safe_navigate_to_url(driver, f"{BASE_URL}/Inventory")
        # Check if already logged in
        if f"{BASE_URL}/Inventory" == driver.current_url:
            safe_navigate_to_url(driver, f"{BASE_URL}/SearchAllECards")
            return True
        # Check for sign-in button
        sign_in_button = check_element_exists(driver, El.SIGN_IN_BUTTON, timeout=3)
        email_field = check_element_exists(driver, El.EMAIL_FIELD, timeout=5)
        if sign_in_button:
            if not click_element(driver, El.SIGN_IN_BUTTON):
                return False
            time.sleep(3)
            # Check if redirected to inventory
            if "Inventory" in driver.current_url:
                return True
        # Proceed with login if email field exists
        if email_field:
            if not input_element(driver, El.EMAIL_FIELD, os.getenv("ATLAS_USERNAME")):
                return False
            time.sleep(1)
            if not input_element(driver, El.PASSWORD_FIELD, os.getenv("ATLAS_PASSWORD")):
                return False
            time.sleep(1)
            # Try to click remember me checkbox (optional)
            if check_element_exists(driver, El.REMEMBER_ME, timeout=3):
                click_element(driver, El.REMEMBER_ME)
            time.sleep(1)
            # Click sign-in button
            if not click_element(driver, El.SUBMIT_BUTTON):
                return False
            time.sleep(5)
            # Verify login success
            if f"{BASE_URL}/Inventory" == driver.current_url:
                safe_navigate_to_url(driver, f"{BASE_URL}/SearchAllECards")
                return True
            else:
                return False
        else:
            return True

    except Exception as e:
        logger.error("Failed to login to Atlas\nError: %s", e)
        return False


def login_to_enrollware(driver) -> bool | None:
    try:
        safe_navigate_to_url(driver, "https://www.enrollware.com/admin/login.aspx?")
        time.sleep(5)

        # Check if already logged in
        validation_button = check_element_exists(driver, Els.LOGIN_BUTTON, timeout=5)

        if validation_button:
            # Input credentials with validation
            if not input_element(driver, Els.USERNAME_INPUT, os.getenv("ENROLLWARE_USERNAME")):
                logger.error("Failed to input username")

            if not input_element(driver, Els.PASSWORD_INPUT, os.getenv("ENROLLWARE_PASSWORD")):
                logger.error("Failed to input password")

            # Optional remember me checkbox
            click_element(driver, Els.REMEMBER_ME_BUTTON)
            time.sleep(1)

            if not click_element(driver, Els.LOGIN_BUTTON):
                logger.error("Failed to click login button")


            # Wait for login to complete
            time.sleep(20)

        # Verify login success
        if "admin" in driver.current_url.lower():
            logger.info("Successfully logged into Enrollware")
            return True
        else:
            logger.warning("Login may have failed, checking current URL")

    except Exception as e:
        logger.error("An error occurred during Enrollware login: %s", e)
        return False


def wait_while_loading_display(driver):
    wait_while_element_is_displaying(driver, El.WAIT_MESSAGE)


def get_data_from_all_rows(driver) -> list:
    """Extract data from all rows in the eCards table."""
    try:
        data = []
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.select("#example tbody tr")

        for row in rows:
            cols = row.find_all('td')
            data_unit = {
                "Course": cols[0].get_text(strip=True),
                "Course Date": cols[1].get_text(strip=True),
                "eCard Code": cols[2].get_text(strip=True),
                "Instructor": cols[4].get_text(strip=True),
                "Student Name": f'{cols[5].get_text(strip=True)} {cols[6].get_text(strip=True)}',
                "Student Email": cols[7].find('a').get_text(strip=True) if cols[7].find('a') else ""
            }
            data.append(data_unit)
        return data
    except Exception as e:
        logger.error(f"An error occurred while extracting table data: {e}")
        return []


def search_eCards(driver, from_date, to_date):
    try:
        select_by_text(driver, El.TRAINING_CENTER_SELECT, 'Shell CPR, LLC.')
        wait_while_loading_display(driver)
        input_element(driver, El.FROM_DATE_INPUT, from_date)
        input_element(driver, El.TO_DATE_INPUT, to_date)
        click_element(driver, El.SEARCH_CARD_BUTTON)
        wait_while_loading_display(driver)
        select_by_text(driver, El.ENTRIES_SELECT, "100")
    except Exception as e:
        logger.error(f"An error occurred while searching for eCards: {e}")


def search_student_using_email(driver, email, index):
    try:
        if index == 0:
            select_by_text(driver, Els.SEARCH_FOR_SELECT, "email address")
        input_element(driver, Els.SEARCH_INPUT, email)
        click_element(driver, Els.SEARCH_BUTTON)
        logger.info(f'Searched for {email}')
    except Exception as e:
        logger.error(f"An error occurred while searching for student: {e}")


def no_match_found(driver):
    try:
        return check_element_exists(driver, Els.NO_MATCHES_MESSAGE, timeout=1)
    except Exception as e:
        logger.error(f"An error occurred while checking for 'No matches found': {e}")
        return False


def eCards_automation(driver, from_date, to_date):
    data = []
    page_counter = 1

    try:
        if login_to_ecards(driver):
            logger.info("Login successful!")
            search_eCards(driver, from_date, to_date)
            if check_element_exists(driver, El.NO_RESULT_FOUND, timeout=2):
                logger.info("No results found for the given date range.")
                return data

            while True:

                searched_results_data = get_data_from_all_rows(driver)
                data.extend(searched_results_data)

                page_counter += 1
                next_page = check_element_exists(driver, El.NEXT_PAGE_SELECTOR(page_counter))
                if not next_page:
                    break

                click_element(driver, El.NEXT_PAGE_SELECTOR(page_counter))
                wait_while_loading_display(driver)

            logger.info(f"Fetched {len(data)} data-units from all rows")
            return data

        else:
            logger.warning("Login failed.")
    except Exception as e:
        logger.error(f"An error occurred during eCards automation: {e}")


def enrollware_automation(driver, ecards_data):
    try:
        if login_to_enrollware(driver):
            logger.info("Enrollware login successful!")

            # navigate to search-student page
            safe_navigate_to_url(driver, Els.STUDENT_SEARCH_URL)

            for i, record in enumerate(ecards_data):
                student_email = record["Student Email"]
                search_student_using_email(driver, student_email, i)
                if no_match_found(driver):
                    logger.info(f"No roster found for {student_email}.")
                    instructor_email = get_instructor_email_by_name(record["Instructor"])
                    email_send_to_list = [os.getenv("TC_EMAIL")]
                    if instructor_email:
                        email_send_to_list.append(instructor_email)
                    add_entry_if_new(record, 5, email_send_to_list)
                continue
            logger.info("All students processed in Enrollware.")
        else:
            logger.warning("Enrollware login failed.")
    except Exception as e:
        logger.error(f"An error occurred during Enrollware automation: {e}")


def get_instructor_email_by_name(name: str) -> str | None:
    first_name_col = 3
    last_name_col = 4
    email_col = 6

    try:
        with open(instructors_data_csv, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Ensure the row has enough columns to avoid an IndexError
                if len(row) > email_col:
                    current_first_name = row[first_name_col].strip()
                    current_last_name = row[last_name_col].strip()

                    # Case-insensitive comparison for better reliability
                    if (current_first_name.lower() == str(name.split(' ')[0]).strip().lower() and
                            current_last_name.lower() == str(name.split(' ')[1]).strip().lower()):
                        return row[email_col]

        return None

    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error: {e}"
