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
import os
import platform

from iterators.factory import IteratorFactory
from iterators.iterlist import IteratorAsList




class ShortDurationShortVideoTests(unittest.TestCase):
    '''
        ShortDurationShortVideoTests(self, *args, **kwargs)
        A class with tests that take less time to run (i.e. tests that parse 0, 30 or 100 comments, tests that specify
        to scrape for comments for only 30 seconds, 1 minute, etc.)
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_done = False
        self.selector_to_search = '#shorts-inner-container'
        self.youtube_url = 'https://www.youtube.com/shorts/ZyP6Ele5HqY'
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


    def check_and_remove_logfile(logfile, after=False):
        '''
            check_and_remove_logfile(logfile) -> func
            a decorator function to check if the logfile specified is in the current
            directory, and remove the logfile if it is there. By default it only does
            this before the test is run, but if specified, the file can remove the logfile
            in question after the test is run by specifying after=True.
        '''
        def decorator_func(func):
            @wraps(func)
            def remove_logfile_before_test(self, *args, **kwargs):
                current_dir = os.getcwd()
                files = os.listdir(current_dir)
                os_name = platform.system()
                if os_name == 'Windows':
                    file_path = f'.\\{logfile}'
                else:
                    file_path = './{logfile}'
                if logfile in files:
                    os.remove(file_path)
                result = func(self, *args, **kwargs)
                if after:
                    files_after = os.listdir(current_dir)
                    if logfile in files_after:
                        os.remove(file_path)
                return result
            return remove_logfile_before_test
        return decorator_func


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


    @video_not_there
    @ignore_resource_warning
    def test_30_comment_limit(self):
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=30):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 30)


    @video_not_there
    @ignore_resource_warning
    def test_zero_comments(self):
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=0):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 0)


    @video_not_there
    @ignore_resource_warning
    def test_100_comment_limit(self):
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=100):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 100)


    @video_not_there
    @ignore_resource_warning
    def test_30_second_limit(self):
        comments = []
        threshold = 20
        time_limit = datetime.timedelta(seconds = (30 + threshold))
        comment_iterator = IteratorFactory(self.youtube_url, seconds=30)
        start_time = datetime.datetime.now()
        for item in comment_iterator:
            comments.append(item)
        ending_time = datetime.datetime.now()
        elapsed_time = ending_time - start_time
        self.assertLessEqual(elapsed_time, time_limit)


    @video_not_there
    @ignore_resource_warning
    def test_one_minute_limit(self):
        comments = []
        threshold = 20
        time_limit = datetime.timedelta(seconds = (60 + threshold))
        comment_iterator = IteratorFactory(self.youtube_url, minutes=1)
        start_time = datetime.datetime.now()
        for item in comment_iterator:
            comments.append(item)
        ending_time = datetime.datetime.now()
        elapsed_time = ending_time - start_time
        self.assertLessEqual(elapsed_time, time_limit)


    @check_and_remove_logfile('debug.log')
    @video_not_there
    @ignore_resource_warning
    def test_logging_default_logfile(self):
        current_dir = os.getcwd()
        files = os.listdir(path=current_dir)
        self.assertFalse('debug.log' in files)
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=30, enabled_logging=True):
            comments.append(item)
        files = os.listdir(path=current_dir)
        self.assertTrue('debug.log' in files)


    @check_and_remove_logfile('non_default_file.log', after=True)
    @video_not_there
    @ignore_resource_warning
    def test_logging_non_default_logfile(self):
        current_dir = os.getcwd()
        files = os.listdir(path=current_dir)
        self.assertFalse('non_default_file.log' in files)
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=30, enabled_logging=True, logfile='non_default_file.log'):
            comments.append(item)
        files_after = os.listdir(path=current_dir)
        self.assertTrue('non_default_file.log' in files_after)


if __name__ == '__main__':
    unittest.main()
