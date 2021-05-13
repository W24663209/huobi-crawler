from selenium.webdriver import Remote
from selenium.webdriver.chrome import options
from selenium.common.exceptions import InvalidArgumentException
from selenium import webdriver
from Start import *


class ReuseChrome(Remote):

    def __init__(self, command_executor, session_id):
        self.r_session_id = session_id
        Remote.__init__(self, command_executor=command_executor, desired_capabilities={})

    def start_session(self, capabilities, browser_profile=None):
        """
        重写start_session方法
        """
        if not isinstance(capabilities, dict):
            raise InvalidArgumentException("Capabilities must be a dictionary")
        if browser_profile:
            if "moz:firefoxOptions" in capabilities:
                capabilities["moz:firefoxOptions"]["profile"] = browser_profile.encoded
            else:
                capabilities.update({'firefox_profile': browser_profile.encoded})

        self.capabilities = options.Options().to_capabilities()
        self.session_id = self.r_session_id
        self.w3c = False

    if __name__ == '__main__':
        '''禁用 w3c'''
        o = webdriver.ChromeOptions()
        o.add_experimental_option('w3c', False)
        try:
            Start().close()
        except:
            pass
        driver = webdriver.Chrome(executable_path="../static/chromedriver/chromedriver", options=o)
        driver.maximize_window()
        executor_url = driver.command_executor._url
        session_id = driver.session_id
        with open('config.txt', 'w') as f:
            f.write(executor_url + '\n')
            f.write(session_id + '\n')
        Start().main()
