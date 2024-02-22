import unittest
import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import json
import datetime
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from functools import wraps
import logging
import traceback
import warnings

from iterators.factory import IteratorFactory
from iterators.iterlist import IteratorAsList




class LongDurationShortVideoTests(unittest.TestCase):
    '''
        LongDurationShortVideoTests(self, *args, **kwargs)
        A class with tests that take longer to run (i.e. tests that parse 500 or 1000 comments, tests that specify
        to scrape for 30 minutes or an hour, etc.)
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_done = False
        self.selector_to_search = '#shorts-inner-container'
        self.youtube_url = 'https://www.youtube.com/shorts/JfbnpYLe3Ms'
        self.video_available = True


    def get_selector(self, driver, css_selector, wait_time=10):
        '''
            get_selector(self, driver, css_selector, wait_time) -> selenium.webdriver.remote.webelement.WebElement
            get_selector(self, driver, css_selector) -> selenium.webdriver.remote.webelement.WebElement
            Get the element with the CSS selector passed into css_selector, with an optional argument to
            specify the time to wait before an exception is thrown using the wait_time keyword
            argument (default is 10 seconds). This function is not exception safe and will throw exceptions
            if the element with the specified CSS selector is not found. The driver parameter passed in is the
            webdriver that will be used.
        '''
        element_to_find = WebDriverWait(driver, timeout=wait_time, poll_frequency=0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element_to_find


    def ignore_resource_warning(func):
        '''
            ignore_resource_warnings_func(func) -> func
            decorator to ignore resource warnings
        '''
        def ignore_resource_warnings_func(self, *args, **kwargs):
            # Code to ignore warnings found in this stack overflow question(below):
            # https://stackoverflow.com/questions/26563711/disabling-python-3-2-resourcewarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                return func(self, *args, **kwargs)
        return ignore_resource_warnings_func


    @ignore_resource_warning
    def setUp(self):
        if not self.setup_done:
            self.setup_done = True
            driver = webdriver.Chrome()
            try:
                driver.get(self.youtube_url)
                shorts_container = self.get_selector(driver, self.selector_to_search)
                driver.quit()
            except Exception as err:
                self.video_available = False


    def video_not_there(func):
        '''
            video_not_there(func) -> func
            decorator the function to check if the video is not there, and skip the
            test if the video is not there
        '''
        @wraps(func)
        def skip_unless_video_exists(self, *args, **kwargs):
            if not self.video_available:
                self.skipTest('Video not available')
            return func(self, *args, **kwargs)
        return skip_unless_video_exists


    @video_not_there
    @ignore_resource_warning
    def test_500_comment_limit(self):
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=500):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 500)


    @video_not_there
    @ignore_resource_warning
    def test_1000_comment_limit(self):
        comments = []
        length = 0
        for item in IteratorFactory(self.youtube_url, limit=1000):
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 1000)


    @video_not_there
    @ignore_resource_warning
    def test_5_minute_limit(self):
        comments = []
        threshold = 20
        time_limit = datetime.timedelta(seconds = ((60 * 5) + threshold))
        comment_iterator = IteratorFactory(self.youtube_url, minutes=5)
        comments_threads_parsed = 0
        start_time = datetime.datetime.now()
        for item in comment_iterator:
            comments_threads_parsed += 1
        ending_time = datetime.datetime.now()
        elapsed_time = ending_time - start_time
        self.assertLessEqual(elapsed_time, time_limit)


    @video_not_there
    @ignore_resource_warning
    def test_30_minute_limit(self):
        comments = []
        threshold = 20
        time_limit = datetime.timedelta(seconds = ((60 * 30) + threshold))
        comment_iterator = IteratorFactory(self.youtube_url, minutes=30)
        comments_threads_parsed = 0
        start_time = datetime.datetime.now()
        for item in comment_iterator:
            comments_threads_parsed += 1
        ending_time = datetime.datetime.now()
        elapsed_time = ending_time - start_time
        self.assertLessEqual(elapsed_time, time_limit)


    @video_not_there
    @ignore_resource_warning
    def test_one_hour_limit(self):
        comments = []
        threshold = 20
        time_limit = datetime.timedelta(seconds = ((60 * 60) + threshold))
        comment_iterator = IteratorFactory(self.youtube_url, hours=1)
        comments_threads_parsed = 0
        start_time = datetime.datetime.now()
        for item in comment_iterator:
            comments_threads_parsed += 1
        ending_time = datetime.datetime.now()
        elapsed_time = ending_time - start_time
        self.assertLessEqual(elapsed_time, time_limit)


if __name__ == '__main__':
    unittest.main()

