import logging
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .exceptions import LoginError


def get_login_messages(driver):
    """
    Detect error messages on login page and raise a LoginError
    with the first message found.
    """
    messages = []
    # look for alerts
    try:
        el = driver.find_element_by_css_selector('div.alert')
    except NoSuchElementException:
        pass
    else:
        messages.append(el.text.strip())

    # look for field helptext
    helptext_css = '.form-group .help-block:not(.hidden)'
    try:
        els = driver.find_elements_by_css_selector(helptext_css)
    except NoSuchElementException:
        pass
    else:
        for el in els:
            messages.append(el.text.strip())

    if messages:
        raise LoginError(messages)


class MPDriver(webdriver.Chrome, webdriver.Firefox, webdriver.Ie):
    """Webdriver extension tailored to functioning in MPathways environments"""

    ENTRY_URL = 'https://{env}.dsc.umich.edu/services/mpathways'

    def __init__(self, env='csdev9', browser='chrome'):
        self.env = env.lower()
        self.ENTRY_URL = self.ENTRY_URL.format(env=self.env)
        LOGGER.setLevel(logging.CRITICAL)
        if browser.lower() == 'ie':
            webdriver.Ie.__init__(self)
        elif browser.lower() == 'firefox':
            webdriver.Firefox.__init__(self)
        else:
            webdriver.Chrome.__init__(self)


    def mp_login(self, username, password):
        """Login to MPathways environment"""
        self.get(self.ENTRY_URL)
        self.find_element_by_id('login').send_keys(username)
        self.find_element_by_id('password').send_keys(password)
        self.find_element_by_id('loginSubmit').click()
        # detect login error messages
        try:
            get_login_messages(self)
        except LoginError as e:
            raise

        # wait for duo authentication and mpathways to finish loading
        WebDriverWait(self, 300).until(EC.title_is('My Homepage'))

    def mp_wait(self, timeout=30):
        """
        Wait for spinner to disappear.
        """
        WebDriverWait(self, timeout).until(EC.invisibility_of_element_located((By.ID, 'WAIT_win0')))
        WebDriverWait(self, timeout).until(EC.invisibility_of_element_located((By.ID, 'saveWait_win0')))

    def mp_env(self):
        """
        Derive the MPathways environment from the current_url.
        """
        pattern = r"https?://(?P<env>{\w+})\.dsc\.umich\.edu"
        return re.match(pattern, self.current_url)['env']

    def switch_to_content(self, frame='TargetContent'):
        """
        Passively try to switch to frame.
        """
        try:
            self.switch_to.frame(frame)
        except:
            pass


class OrientationDriver(MPDriver):

    ENTRY_URL = 'https://{env}.dsc.umich.edu/services/orientation'
