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
from iterators.implementations.comment_iterator import CommentIterator
from iterators.implementations.youtube_shorts_iterator import YoutubeShortsIterator
from iterators.iterlist import IteratorAsList
from tests.youtube_shorts.test_short_duration_tests import ShortDurationShortVideoTests




class ShortDurationRegularVideoTests(ShortDurationShortVideoTests):
    '''
        ShortDurationRegularVideoTests(self, *args, **kwargs)
        A class with tests that take less time to run (i.e. tests that parse 0, 30 or 100 comments, tests that specify
        to scrape for comments for only 30 seconds, 1 minute, etc.)
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_done = False
        self.selector_to_search = '#above-the-fold #title h1'
        self.youtube_url = 'https://www.youtube.com/watch?v=okIwFBdbEOc'
        self.video_available = True


