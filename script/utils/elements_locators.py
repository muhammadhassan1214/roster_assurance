from selenium.webdriver.common.by import By

BASE_URL = "https://atlas-api-gateway.heart.org/orgManagement/v1/organisation/alignments?page=1"

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
    ACCEPT_COOKIES_BUTTON = (By.XPATH, "//button[text()= 'Accept All Cookies']")
    WELCOME_POP_UP_CLOSE_BUTTON = (By.XPATH, "(//span[text()= '×']/parent::button[@class='close'])[1]")

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


class ApiEndpoints:
    GET_INSTRUCTOR_INFO = lambda x: f"{BASE_URL}&nameOrEmailOrInstructorId={x}&roleId=17&roleName=INSTRUCTOR&parentId=18260&expiryStatus=ACTIVE&sort=lastName,asc&size=10"
    GET_COORDINATOR_INFO = lambda x, y: f"{BASE_URL}&sort=name,asc&size=10&status=ACTIVE&orgCodeOrName={x}&orgType={y}&all=true&parentOrgCodeOrName=KY21007&publicAccess=false"


    def get_headers(self: str) -> dict:
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'ext_id': 'dacbf678-f0cd-4f43-aaf0-7cd5058fb9f9',
            'origin': 'https://atlas.heart.org',
            'priority': 'u=1, i',
            'referer': 'https://atlas.heart.org/',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'x-jwt-token': self
        }
        return headers
