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


class MPDriver(webdriver.Chrome,
               webdriver.Firefox,
               webdriver.Ie,
               webdriver.Remote):
    """
    Webdriver extension tailored to functioning in MPathways environments.

    Parameters
    ----------
    env : str
        The MPathways environment to use (csprod, csqa9, csdev9, etc.).
    browser : str
        The browser to use ('chrome', 'firefox', 'ie', 'remote').
    kwargs : kwargs
        Keyword arguments to pass to the webdriver browser constructor.
        Generally things like `command_executor` and `desired_capabilities`.
    """

    ENTRY_URL = 'https://{env}.dsc.umich.edu/services/mpathways'

    def __init__(self, env='csdev9', browser='chrome', **kwargs):
        self.env = env.lower()
        self.ENTRY_URL = self.ENTRY_URL.format(env=self.env)
        LOGGER.setLevel(logging.CRITICAL)
        if browser.lower() == 'ie':
            webdriver.Ie.__init__(self, **kwargs)
        elif browser.lower() == 'firefox':
            webdriver.Firefox.__init__(self, **kwargs)
        elif browser.lower() == 'remote':
            webdriver.Remote.__init__(self, **kwargs)
        else:
            webdriver.Chrome.__init__(self, **kwargs)


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
        wait_loc = (By.ID, 'processing')
        save_loc = (By.XPATH, "//*[starts-with(@id, 'saveWait']")
        wait = WebDriverWait(self, timeout)
        wait.until(EC.invisibility_of_element_located(wait_loc))
        wait.until(EC.invisibility_of_element_located(save_loc))

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
