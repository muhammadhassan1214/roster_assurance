import os
import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import (
    TimeoutException, ElementNotInteractableException,
    NoSuchElementException, WebDriverException
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

driver_path = os.path.abspath(os.path.join(BASE_DIR, 'chrome.exe'))


def get_undetected_driver(headless: bool = False, max_retries: int = 3) -> Optional[webdriver.Chrome]:
    """Create undetected Chrome driver with comprehensive error handling."""
    for attempt in range(max_retries):
        driver = None
        try:
            options = webdriver.ChromeOptions()
            path = rf'{BASE_DIR}\chrome-dir'

            # Ensure chrome-dir exists
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"Created chrome directory: {path}")
                except OSError as e:
                    logger.error(f"Failed to create chrome directory: {e}")
                    path = None

            if path:
                options.add_argument(f'--user-data-dir={path}')

            # Enhanced options for stability
            options.add_argument("--log-level=3")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")

            if headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
            else:
                options.add_argument("--start-maximized")

            # Experimental options for better stability
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(service=Service(path=driver_path), options=options)

            # Allow the browser to fully initialize
            time.sleep(3)

            # Enhanced fingerprinting protection
            stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
            """
            driver.execute_script(stealth_js)

            # Test driver functionality
            driver.get("data:,")
            logger.info(f"Chrome driver initialized successfully (attempt {attempt + 1})")
            return driver

        except Exception as e:
            logger.error(f"Driver creation attempt {attempt + 1} failed: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass

            if attempt < max_retries - 1:
                logger.info(f"Retrying driver creation... Attempts left: {max_retries - attempt - 1}")
                time.sleep(3)
            else:
                logger.error("Max retries exceeded. Could not create the driver.")
                return None

    return None


def wait_for_page_load(driver, timeout: int = 30) -> bool:
    """Wait for page to fully load with exception handling."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)  # Additional buffer
        return True
    except TimeoutException:
        logger.warning(f"Page load timeout after {timeout} seconds")
        return False
    except WebDriverException as e:
        logger.error(f"Error waiting for page load: {e}")
        return False


def safe_navigate_to_url(driver, url: str, max_retries: int = 3) -> bool:
    """Navigate to URL with retry logic and exception handling."""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            if wait_for_page_load(driver):
                logger.info(f"Successfully navigated to: {url}")
                return True
            else:
                logger.warning(f"Page load incomplete for: {url}")
        except WebDriverException as e:
            logger.error(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue

    logger.error(f"Failed to navigate to {url} after {max_retries} attempts")
    return False


def click_element(driver, locator, timeout: int = 10) -> bool:
    """Click element with exception handling."""
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", element)
        time.sleep(0.5)

        element.click()
        time.sleep(0.5)
        return True
    except TimeoutException:
        logger.error(f"Element not clickable within {timeout} seconds: {locator}")
        return False
    except WebDriverException as e:
        save_error_screenshot(driver, name=f"click_error_{int(time.time())}.png")
        logger.error(f"Error clicking element: {e}")
        return False


def check_element_exists(driver, by_locator, timeout: int = 3) -> bool:
    """Check if element exists with proper exception handling."""
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(by_locator))
        return True
    except TimeoutException:
        return False
    except (NoSuchElementException, WebDriverException):
        return False
    except Exception as e:
        logger.error(f"Unexpected error in check_element_exists: {e}")
        return False


def input_element(driver, by_locator, text: str, timeout: int = 10) -> bool:
    """Input text with comprehensive exception handling and validation."""
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(by_locator))

        # Clear the field safely
        element.clear()
        time.sleep(0.2)

        # Input the text
        element.send_keys(text)

        return True
    except TimeoutException:
        logger.error(f"Input element not found within {timeout} seconds: {by_locator}")
        return False
    except (NoSuchElementException, ElementNotInteractableException) as e:
        logger.error(f"Element input failed: {e}")
        return False
    except WebDriverException as e:
        logger.error(f"WebDriver error during input: {e}")
        return False


def select_by_text(driver, by_locator, text: str, timeout: int = 10) -> bool:
    """Select dropdown option by text with exception handling."""
    try:
        select_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(by_locator))
        select = Select(select_element)

        # Check if option exists
        options = [option.text.strip() for option in select.options]
        if text not in options:
            logger.error(f"Option '{text}' not found. Available options: {options}")
            return False

        select.select_by_visible_text(text)
        time.sleep(0.5)

        return True
    except TimeoutException:
        logger.error(f"Select element not found within {timeout} seconds: {by_locator}")
        return False
    except (NoSuchElementException, ElementNotInteractableException) as e:
        logger.error(f"Select operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in select operation: {e}")
        return False


def wait_while_element_is_displaying(driver, by_locator, timeout: int = 30) -> bool:
    """Wait while element is displaying with exception handling."""
    try:
        WebDriverWait(driver, timeout).until_not(EC.visibility_of_element_located(by_locator))
        return True
    except TimeoutException:
        logger.warning(f"Element still visible after {timeout} seconds: {by_locator}")
        return False
    except WebDriverException as e:
        logger.error(f"Error waiting for element to disappear: {e}")
        return False


def save_error_screenshot(driver, name: str = "screenshot.png") -> None:
    """Save screenshot with error handling."""
    try:
        driver.save_screenshot(os.path.join(BASE_DIR, name))
        logger.info(f"Screenshot saved: {name}")
    except WebDriverException as e:
        logger.error(f"Error saving screenshot: {e}")
