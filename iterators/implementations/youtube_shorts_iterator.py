'''
This module provides an interface to iterate over Youtube Comments for YouTube shorts.
'''
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

class YoutubeShortsIterator:
    def __init__(self, youtube_url, limit=None, pattern=None, hours=0, minutes=0, seconds=0, enabled_logging=False, logfile='debug.log'):
        self.comment_thread_count = 0
        self.reply_count = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.total_comments_parsed = 0
        self.youtube_url = youtube_url
        self.limit = limit
        self.driver = webdriver.Chrome()
        self.title_selector = '#title > h1 > yt-formatted-string'
        self.current_comment = None
        self.comment_channel_name = None
        self.comment_link = None
        self.comment_replies_button = None
        self.current_reply = None
        self.reply_link = None
        self.reply_channel_name = None
        self.regex_pattern = pattern
        self.amount_scrolled = 0
        self.thread_has_pattern = False
        self.parent_comment = None
        self.parent_comment_pos = 0
        self.time_limit_exists = False
        # Comment selectors
        self.play_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(1) button'
        self.mute_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(2) button'
        self.expand_comments_button = '#comments-button ytd-button-renderer yt-button-shape label button'
        # CSS selectors for the section containing comments
        self.comment_box_selector = '#shorts-container #watch-while-engagement-panel #contents #contents'
        self.commenter_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                '#body #main #header-author > h3 #author-text > span'
        self.comment_link_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#body #main #header-author #published-time-text > a'
        self.comment_text_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#body #main #expander #content #content-text > span'
        self.current_comment_json = {}
        self.started_yet = False
        self.log_file = logfile
        self.enabled_logging = enabled_logging
        self.driver_started = False


    @staticmethod
    def regex_pattern():
        return r'^https://www\.youtube\.com/(shorts\/)[^\.\s]+$'


    def get_selector(self, css_selector):
        element_to_find = WebDriverWait(self.driver, timeout=5, poll_frequency=0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element_to_find


    def mute_video(self):
        '''
            mute_video(self) -> None
            find the mute button on the youtube short video, and ensure the video is muted
        '''
        mute_button = self.get_selector(self.mute_button_selector)
        aria_label_value = mute_button.get_attribute('aria-label')
        if aria_label_value:
           aria_label_value = aria_label_value.casefold()
           if aria_label_value.find('unmute') == -1:
               mute_button.click()


    def pause_video(self):
        '''
            play_video(self) -> None
            find the play button on the youtube short video, and ensure the video is paused
        '''
        play_button = self.get_selector(self.play_button_selector)
        aria_label_value = play_button.get_attribute('aria-label')
        if aria_label_value:
           aria_label_value = aria_label_value.casefold()
           if aria_label_value.find('play') == -1:
               play_button.click()


    def setup(func):
        '''
            startup(function) -> function
            a decorator to do setup steps before iteration
        '''
        @wraps(func)
        def setup_beforehand(self, *args, **kwargs):
            if not self.started_yet:
                # format string taken from logging documentation: https://docs.python.org/3/library/logging.html
                FORMAT = '%(asctime)s %(message)s'
                logging.basicConfig(filename=self.log_file, level=logging.ERROR, format=FORMAT)
                self.logger = logging.getLogger(__name__)
                self.started_yet = True
                self.driver_started = True
                self.driver.get(self.youtube_url)
                self.driver.maximize_window()
                self.pause_video()
                self.mute_video()
                expand_comments_button = self.get_selector(self.expand_comments_button)
                expand_comments_button.click()
                time.sleep(10)
            return func(self, *args, **kwargs)
        return setup_beforehand


    def log_debug_output(func):
        @wraps(func)
        def log_output(self, *args, **kwargs):
            if self.enabled_logging:
                self.logger.setLevel(logging.DEBUG)
            #comment_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.commenter_selector)
            #commenter_name = comment_channel_name.text.strip()[1:]
            #reply_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.comment_reply_channel)
            #name = reply_channel_name.text.strip()[1:]
            #commenter_name = self.current_comment_json['commenter']
            self.logger.debug(f'comment number: {(self.comment_thread_count + 1)}, comment info: {self.current_comment_json}')
            #self.logger.debug(f'comment reply number: {(self.reply_count + 1)}, comment reply name: {name}')
            return func(self, *args, **kwargs)
        return log_output


    def __iter__(self):
        return self


    @setup
    def __next__(self):
        self.driver.quit()
        raise StopIteration


if __name__ == '__main__':
    for comment in YoutubeShortsIterator('https://www.youtube.com/shorts/re6MHKI-t-g'):
        print('hello world')
