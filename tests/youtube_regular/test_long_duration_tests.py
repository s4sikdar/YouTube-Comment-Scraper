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
from tests.youtube_shorts.test_long_duration_tests import LongDurationShortVideoTests



class LongDurationLongVideoTests(LongDurationShortVideoTests):
    '''
        LongDurationLongVideoTests(self, *args, **kwargs)
        A class with tests that take longer to run (i.e. tests that parse 500 or 1000 comments, tests that specify
        to scrape for 30 minutes or an hour, etc.)
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_done = False
        self.selector_to_search = '#above-the-fold #title h1'
        self.youtube_url = 'https://www.youtube.com/watch?v=0e3GPea1Tyg'
        self.video_available = True


