'''
This module provides an interface to iterate over Youtube Comments for regular YouTube videos (not YouTube shorts).
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


SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600


class CommentIterator:
    '''
        CommentIterator(video_url, limit=10, pattern=None, hours=0, minutes=0, seconds=0, enabled_logging=False, logfile='debug.log') -> Iterator
        A class that provides an interface to iterate over youtube comments.
        When iterating over an instance of the CommentIterator class, information for one comment
        thread is gathered and returned to you in the form of a dictionary. The dictionary has the following keys:
            'commenter' - the channel name of the commenter
            'comment content' - the text content of the main comment, with all leading and trailing whitespace stripped
            'link' - the link to the YouTube comment itself. If the link cannot be obtained, the value is an empty string
            'children' - a list of all children comments. Each list item contains a dictionary with the keys 'commenter', 'comment content' and 'link'

        If the regex parameter is not None, then None can possibly be returned for a comment thread.
        Parameters:

            video_url - the link to the exact video. The link must be valid and this interface is not responsible
                        for handling exceptions regarding videos not available, or videos that are private

            limit - the maximum number of comments to iterate over. This refers to the maximum number of comment threads,
                    and the number does not include comment replies. The default is 10 comment threads.

            pattern - an optional regular expression that will match text in a comment or its replies. If the comment thread has no replies,
                    the regular expression is tested against the main comment, and if it finds a match, then the comment information is returned
                    back. If the comment has replies, the regular expression is tested against the replies, and the information is returned if at
                    least one reply (or the original comment) matches the regular expression. If there are no matches, None is returned.

            hours - the number of hours you want to spend scraping if you intend to specify a time limit. The hour count is multiplied by the number of
                    seconds per hour (3600 seconds per hour) to get the total number of seconds specified by the hour-count. This is added to the number
                    of seconds represented by the number of passed in minutes, and the number of seconds passed in to get the total time limit.
                    The number of hours passed in by default (when it is not specified) is 0.

            minutes - the number of minutes you want to spend scraping if you intend to specify a time limit. The hour count is multiplied by the number of
                    seconds per hour (3600 seconds per hour) to get the total number of seconds specified by the hour-count. This is added to the number
                    of seconds represented by the number of minutes specified in the minutes parameter (i.e. add 60 * number of minutes specified),
                    and the number of seconds passed in to get the total time limit. The number of minutes passed in by default (when it is not specified)
                    is 0.

            seconds - the number of seconds you want to spend scraping if you intend to specify a time limit. The hour count is multiplied by the number of
                    seconds per hour (3600 seconds per hour) to get the total number of seconds specified by the hour-count. This is added to the number
                    of seconds represented by the number of minutes specified in the minutes parameter (i.e. add 60 * number of minutes specified),
                    and the number of seconds passed in to get the total time limit. The number of minutes passed in by default (when it is not specified)
                    is 0.

            enabled_logging - when set to true, the logger level is set to the DEBUG level. All logger.debug calls are made.

            logfile - the name of the logfile that you want to use to log messages to. By default, the log file name is 'debug.log'
    '''
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
        self.comment_number_selector = '#sections #count > yt-formatted-string > span:nth-child(1)'
        self.comment_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #content-text'
        self.commenter_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #author-text'
        self.comment_link_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #header-author > yt-formatted-string > a'
        self.replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #more-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.less_replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #less-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.comment_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({(self.reply_count + 1)}) #content-text'
        self.comment_reply_channel = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({(self.reply_count + 1)}) #author-text > yt-formatted-string'
        self.comment_reply_link = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({(self.reply_count + 1)}) #header-author > yt-formatted-string > a'
        self.more_replies_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #replies #button > ytd-button-renderer > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.first_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child(1) #content-text'
        #self.video_author_commenter_selector = f'{self.current_thread_selector} ytd-author-comment-badge-renderer #container #text-container #text'
        #self.reply_video_author_commenter_selector = f'{self.reply_selector} ytd-author-comment-badge-renderer #container #text-container #text'
        self.current_comment_json = {}
        self.started_yet = False
        self.log_file = logfile
        self.enabled_logging = enabled_logging
        self.driver_started = False


    def log_debug_output(func):
        '''
            log_debug_output(func) -> function
            a decorator function that logs the values (self.comment_thread_count + 1) and self.current_comment_json before
            running a modified function that is originally based on the function passed in as a parameter
        '''
        @wraps(func)
        def log_output(self, *args, **kwargs):
            self.logger.debug(f'comment number: {(self.comment_thread_count + 1)}, comment info: {self.current_comment_json}')
            return func(self, *args, **kwargs)
        return log_output


    def startup(self):
        '''
            startup(self) -> None
            startup steps to start the scraping process.
        '''
        if not self.started_yet:
            # format string taken from logging documentation: https://docs.python.org/3/library/logging.html
            FORMAT = '%(asctime)s %(message)s'
            logging.basicConfig(filename=self.log_file, level=logging.ERROR, format=FORMAT)
            self.logger = logging.getLogger(__name__)
            self.started_yet = True
            self.driver_started = True
            self.driver.get(self.youtube_url)
            self.driver.maximize_window()
            title = WebDriverWait(self.driver, timeout=10, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.title_selector))
            )
            y_pos = title.location_once_scrolled_into_view['y'] - 100
            ActionChains(self.driver).scroll_by_amount(0,y_pos).perform()
            self.amount_scrolled += y_pos
            comment_number = WebDriverWait(self.driver, timeout=10, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_number_selector))
            )
            total_comments = int(''.join(comment_number.text.strip().split(',')))
            if self.limit == None:
                self.limit = total_comments
            self.set_time_limit(self.hours, self.minutes, self.seconds)
            if self.enabled_logging:
                self.logger.setLevel(logging.DEBUG)


    @staticmethod
    def regex_pattern():
        return r'^https://www\.youtube\.com/(?!shorts/)[^\.\s]+$'


    def set_time_limit(self, hours, minutes, seconds):
        '''
            set_time_limit(self, hours, seconds, minutes) -> None
            a helper method to setup the time limit attributes if necessary,
            and to set a starting time if applicable as well. There is an attribute
            (self.time_limit_exists) set to True if the hours, minutes or seconds
            are specified to be non-zero. Otherwise, it is set to False (attribute is
            used elsewhere).
        '''
        if ((hours == 0) and (minutes == 0) and (seconds == 0)):
            self.time_limit_exists = False
        else:
            # total time limit in seconds, then converted to datetime.timedelta instance, since timedelta
            # instances can be compared with other time delta instances (to check if elapsed time is greater than
            # a threshold)
            self.time_limit_exists = True
            self.total_seconds = (hours * SECONDS_PER_HOUR) + (minutes * SECONDS_PER_MINUTE) + seconds
            self.total_time_limit = datetime.timedelta(seconds = self.total_seconds)
            self.start_time = datetime.datetime.now()


    def time_to_stop_scraping(self):
        '''
            time_to_stop_scraping(self) -> Bool
            a helper method to determine if we should stop scraping comments, and
            if the webdriver should shut down. If the total number of comments parsed
            is greater than or equal to the limit, or if we have passed the specified
            time limit, then we return True (indicating we should stop scraping comments).
            Otherwise, return False.
        '''
        if self.total_comments_parsed >= self.limit:
            return True
        elif self.time_limit_exists:
            current_time = datetime.datetime.now()
            elapsed_time = current_time - self.start_time
            if (elapsed_time > self.total_time_limit):
                return True
        return False


    def get_attribute(self, element, attribute):
        '''
            get_attribute(self, element, attribute) -> Str
            a method to return the attribute from the element, returns an
            empty string if any exceptions are raised
        '''
        try:
            result = element.get_attribute(attribute)
            return result
        except:
            return ''


    def element_exists(self, css_selector):
        '''
            element_exists(self, css_selector) -> Bool
            a method to check if a css selector exists, returns True if so, False otherwise
        '''
        try:
            self.driver.find_element(By.CSS_SELECTOR, css_selector)
        except NoSuchElementException:
            return False
        return True


    def reset_elements(self):
        '''
            reset_eleemnts(self) -> None
            resets all of the attributes used for finding elements to be None, and the dictionary for
            keeping comment information to be an empty dictinary.
        '''
        self.current_comment = None
        self.comment_channel_name = None
        self.comment_link = None
        self.comment_replies_button = None
        self.thread_has_pattern = False
        self.current_reply = None
        self.reply_link = None
        self.reply_channel_name = None
        self.parent_comment = None
        self.current_comment_json = {}


    def update_selectors(self, count, child_count):
        '''
            update_selectors(self, count, child_count) -> None
            updates the values of the necessary selectors for iterating through comments. It uses count and child count
            for the current comment thread count and the current reply count respectively (i.e. self.comment_thread_count
            would be used for count, and self.reply_count would be used for child_count).
        '''
        self.comment_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #content-text'
        self.commenter_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #author-text'
        self.comment_link_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #header-author > yt-formatted-string > a'
        self.replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #more-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.less_replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #less-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.comment_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #content-text'
        self.comment_reply_channel = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #author-text > yt-formatted-string'
        self.comment_reply_link = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #header-author > yt-formatted-string > a'
        self.more_replies_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies #button > ytd-button-renderer > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        self.first_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child(1) #content-text'


    @log_debug_output
    def iterate_child(self):
        '''
            iterate_child(self) -> (anyOf Dict None)
            Iterates through the replies of a youtube comment, aggregates the comment into a dictionary, and returns it.
        '''
        try:
            self.first_reply_comment = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.first_reply_selector))
            )
            more_comments = self.element_exists(self.comment_reply_selector) or self.element_exists(self.more_replies_selector)
        except:
            current_comment = self.current_comments_json
            # log these errors if the logger level is set to debug
            self.logger.debug(f'failed to find replies for comment number {(self.comment_thread_count + 1)} and css selector {self.first_reply_selector}')
            self.logger.debug(f'comment info for comment number {(self.comment_thread_count + 1)}: {current_comment}')
        else:
            while more_comments:
                self.current_reply = self.driver.find_element(By.CSS_SELECTOR, self.comment_reply_selector)
                self.reply_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.comment_reply_channel)
                name = self.reply_channel_name.text.strip()[1:]
                self.reply_link = self.driver.find_element(By.CSS_SELECTOR, self.comment_reply_link)
                reply_text = self.current_reply.text.strip()
                comment_link = ''
                y_pos = self.current_reply.location_once_scrolled_into_view['y'] - 100
                ActionChains(self.driver).scroll_by_amount(0, y_pos).perform()
                comment_link = self.get_attribute(self.reply_link, 'href')
                reply_json = {
                    'commenter': name,
                    'comment content': reply_text,
                    'link': comment_link,
                }
                if self.regex_pattern and (not self.thread_has_pattern):
                    comment_match = re.search(self.regex_pattern, reply_text, re.IGNORECASE)
                    if comment_match:
                        self.thread_has_pattern = True
                self.current_comments_json['children'].append(reply_json)
                self.reply_count += 1
                self.total_comments_parsed += 1
                self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
                if not self.element_exists(self.comment_reply_selector):
                    if self.element_exists(self.more_replies_selector):
                        more_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.more_replies_selector)
                        ActionChains(self.driver).move_to_element(more_replies_button).pause(0.5).click(more_replies_button).perform()
                        try:
                            next_comment = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_reply_selector))
                            )
                        except TimeoutException:
                            break
                more_comments = self.element_exists(self.comment_reply_selector) or self.element_exists(self.more_replies_selector)
        finally:
            self.reply_count = 0
            self.comment_thread_count += 1
            resulting_comment = self.current_comments_json
            ActionChains(self.driver).scroll_to_element(self.parent_comment).perform()
            self.comment_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.less_replies_button_selector)
            ActionChains(self.driver).scroll_to_element(self.comment_replies_button).move_to_element(self.comment_replies_button).pause(0.5).click(self.comment_replies_button).perform()
            self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
            comment_thread_has_regex = self.thread_has_pattern
            self.reset_elements()
            if self.regex_pattern:
                if comment_thread_has_regex:
                    return resulting_comment
                else:
                    return None
            return resulting_comment


    def __iter__(self):
        return self

    def go_to_next(self):
        '''
            iterate_comment_threads(self) -> Dict
            iterate over comment threads (both the comments and their replies), and return the JSON at the
            end. This goes on till one of the following conditions below is reached:
            1) we no longer find the next element
            2) we reach a point where we have to stop scraping (i.e. we exceed the comment limit or the time limit),
               or another expected error occurs.
            For both cases above, we raise a StopIteration exception, indicating to the method that uses this method (__next__)
            that there is nothing left to iterate over.
        '''
        if self.time_to_stop_scraping():
            self.driver.quit()
            raise StopIteration
        else:
            try:
                self.current_comment = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_selector))
                )
            except:
                self.driver.quit()
                self.driver_started = False
                raise StopIteration
            self.comment_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.commenter_selector)
            name = self.comment_channel_name.text.strip()[1:]
            self.comment_link = self.driver.find_element(By.CSS_SELECTOR, self.comment_link_selector)
            comment_link = self.get_attribute(self.comment_link, 'href')
            comment_content = self.current_comment.text.strip()
            resulting_comment = {
                'commenter': name,
                'comment content': comment_content,
                'link': comment_link,
                'children': []
            }
            y_pos = self.current_comment.location_once_scrolled_into_view['y'] - 100
            ActionChains(self.driver).scroll_by_amount(0, y_pos).perform()
            self.amount_scrolled += y_pos
            self.total_comments_parsed += 1
            if self.element_exists(self.replies_button_selector):
                try:
                    self.parent_comment = self.current_comment
                    self.parent_comment_pos = self.amount_scrolled
                    self.current_comments_json = resulting_comment
                    self.comment_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.replies_button_selector)
                    ActionChains(self.driver).move_to_element(self.comment_replies_button).pause(0.5).click(self.comment_replies_button).perform()
                except:
                    return resulting_comment
                else:
                    if self.regex_pattern and (not self.thread_has_pattern):
                        comment_match = re.search(self.regex_pattern, resulting_comment['comment content'], re.IGNORECASE)
                        if comment_match:
                            self.thread_has_pattern = True
                    return self.iterate_child()
            else:
                self.comment_thread_count += 1
                self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
                if self.regex_pattern:
                    comment_match = re.search(self.regex_pattern, resulting_comment['comment content'], re.IGNORECASE)
                    if comment_match:
                        return resulting_comment
                    else:
                        return None
                return resulting_comment

    def __next__(self):
        try:
            self.startup()
            return self.go_to_next()
        except Exception as err:
            if self.driver_started:
                self.driver.quit()
            raise StopIteration
