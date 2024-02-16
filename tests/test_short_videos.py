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

from iterators.factory import IteratorFactory
from iterators.iterlist import IteratorAsList




class TestShortVideos(unittest.TestCase):


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


    def setUp(self):
        self.selector_to_search = '#shorts-inner-container'
        self.youtube_url = 'https://www.youtube.com/shorts/ZyP6Ele5HqY'
        self.video_available = True
        driver = webdriver.Chrome()
        try:
            driver.get(self.youtube_url)
            shorts_container = self.get_selector(driver, self.selector_to_search)
            driver.quit()
        except Exception as err:
            self.video_available = False


    def test_comment_limit(self):
        if not self.video_available:
            self.skipTest('Video not available')
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=30):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 30)


    def test_zero_comments(self):
        if not self.video_available:
            self.skipTest('Video not available')
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=0):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 0)


    def test_100_comment_limit(self):
        if not self.video_available:
            self.skipTest('Video not available')
        comments = []
        for item in IteratorFactory(self.youtube_url, limit=100):
            comments.append(item)
        length = 0
        for item in comments:
            length += 1
            for reply in item['children']:
                length += 1
        self.assertEqual(length, 100)



if __name__ == '__main__':
    unittest.main()
