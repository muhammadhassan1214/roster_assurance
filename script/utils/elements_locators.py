from selenium.webdriver.common.by import By

# E-Cards locators
class ECardsLocators:
    SIGN_IN_BUTTON = (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]")
    EMAIL_FIELD = (By.ID, "Email")
    PASSWORD_FIELD = (By.ID, "Password")
    REMEMBER_ME = (By.XPATH, "//input[@id= 'RememberMe']/following-sibling::label")
    SUBMIT_BUTTON = (By.ID, "btnSignIn")
    TRAINING_CENTER_SELECT = (By.ID, "ddlTC")
    SEARCH_CARD_BUTTON = (By.ID, "btnSearchCards")
    ENTRIES_SELECT = (By.NAME, "example_length")
    WAIT_MESSAGE = (By.XPATH, "//div[@class= 'progress']")
    NEXT_PAGE_SELECTOR = lambda x: (By.XPATH, f"//a[text()= '{x}']")
    FROM_DATE_INPUT = (By.ID, "courseFromDate")
    TO_DATE_INPUT = (By.ID, "courseToDate")
    NO_RESULT_FOUND = (By.XPATH, "//div[text()= 'No results found.']")

# Enrollware locators
class EnrollwareLocators:
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    REMEMBER_ME_BUTTON = (By.ID, "rememberMe")
    LOGIN_BUTTON = (By.ID, "loginButton")
    STUDENT_SEARCH_URL = "https://www.enrollware.com/admin/student-search.aspx"
    SEARCH_FOR_SELECT = (By.ID, "mainContent_srchChoice")
    SEARCH_INPUT = (By.ID, "mainContent_lname")
    SEARCH_BUTTON = (By.ID, "mainContent_srchButton2")
    NO_MATCHES_MESSAGE = (By.XPATH, "//div[contains(text(), 'No match found')]")
