'''
This module provides an interface to iterate over Youtube Comments for YouTube shorts.
'''
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


class YoutubeShortsIterator:
    '''
        YoutubeShortsIterator(video_url, limit=10, pattern=None, hours=0, minutes=0, seconds=0, enabled_logging=False, logfile='debug.log') -> Iterator
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
    def __init__(self, video_url, limit=None, pattern=None, hours=0, minutes=0, seconds=0, enabled_logging=False, logfile='debug.log'):
        self.comment_thread_count = 0
        self.reply_count = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.total_comments_parsed = 0
        self.video_url = video_url
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
        self.pixels_left_from_parent = 0
        # Comment selectors
        self.play_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(1) button'
        self.mute_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(2) button'
        self.expand_comments_button = '#comments-button ytd-button-renderer yt-button-shape label button'
        self.comment_box_selector = '#shorts-container #watch-while-engagement-panel #contents #contents'
        # CSS selectors for the section containing comments
        self.current_thread_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)})'
        self.commenter_selector = f'{self.current_thread_selector} #body #main #header-author > h3 #author-text'
        self.comment_link_selector = f'{self.current_thread_selector} #body #main #header-author yt-formatted-string a'
        self.comment_text_selector = f'{self.current_thread_selector} #body #main #expander #content #content-text'
        self.expand_replies_selector = f'{self.current_thread_selector} #replies #expander #more-replies > yt-button-shape > button'
        self.less_replies_selector = f'{self.current_thread_selector} #replies #expander #less-replies > yt-button-shape > button'
        self.reply_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > ' \
                                f'ytd-comment-renderer:nth-child({(self.comment_thread_count + 1)})'
        self.reply_author_name_selector = f'{self.reply_selector} #body #header-author #author-text yt-formatted-string'
        self.reply_link_selector = f'{self.reply_selector} #header-author yt-formatted-string a'
        self.reply_text_selector = f'{self.reply_selector} #comment-content #content #content-text'
        self.first_reply_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > ytd-comment-renderer:nth-child(1) #content-text'
        self.more_replies_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > '\
                                    'ytd-continuation-item-renderer #button ytd-button-renderer yt-button-shape button'
        self.current_comment_json = {}
        self.started_yet = False
        self.log_file = logfile
        self.enabled_logging = enabled_logging
        self.driver_started = False


    @staticmethod
    def regex_pattern():
        return r'^https://www\.youtube\.com/(shorts\/)[^\.\s]+$'


    def get_selector(self, css_selector, wait_time=10):
        '''
            get_selector(self, css_selector, wait_time) -> selenium.webdriver.remote.webelement.WebElement
            get_selector(self, css_selector) -> selenium.webdriver.remote.webelement.WebElement
            Get the element with the CSS selector passed into css_selector, with an optional argument to
            specify the time to wait before an exception is thrown using the wait_time keyword
            argument (default is 10 seconds). This function is not exception safe and will throw exceptions
            if the element with the specified CSS selector is not found.
        '''
        element_to_find = WebDriverWait(self.driver, timeout=wait_time, poll_frequency=0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element_to_find


    def element_exists(self, css_selector, wait_time=5):
        '''
            element_exists(self, css_selector) -> Bool
            a method to check if a css selector exists, returns True if so, False otherwise. You can
            also specify a wait time to wait till the exception is thrown using the wait_time keyword
            argument (default is 5 seconds).
        '''
        try:
            element_to_find = WebDriverWait(self.driver, timeout=wait_time, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
        except (NoSuchElementException, selenium.common.exceptions.TimeoutException) as err:
            self.logger.debug(f'element with css selector {css_selector} was not found')
            return False
        else:
            return True


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


    def mute_video(self):
        '''
            mute_video(self) -> None
            find the mute button on the youtube short video, and ensure the video is muted
        '''
        mute_button = self.get_selector(self.mute_button_selector, wait_time=60)
        aria_label_value = mute_button.get_attribute('aria-label')
        if aria_label_value:
           aria_label_value = aria_label_value.casefold()
           if aria_label_value.find('unmute') == -1:
               mute_button.click()


    def pause_video(self):
        '''
            pause_video(self) -> None
            find the play button on the youtube short video, and ensure the video is paused
        '''
        play_button = self.get_selector(self.play_button_selector, wait_time=60)
        aria_label_value = play_button.get_attribute('aria-label')
        if aria_label_value:
           aria_label_value = aria_label_value.casefold()
           if aria_label_value.find('play') == -1:
               play_button.click()


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
                if self.enabled_logging:
                    self.logger.setLevel(logging.DEBUG)
                self.started_yet = True
                self.driver_started = True
                self.driver.get(self.video_url)
                self.driver.maximize_window()
                self.pause_video()
                self.mute_video()
                expand_comments_button = self.get_selector(self.expand_comments_button)
                expand_comments_button.click()
                self.set_time_limit(self.hours, self.minutes, self.seconds)
            return func(self, *args, **kwargs)
        return setup_beforehand


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
        self.current_thread_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count})'
        self.commenter_selector = f'{self.current_thread_selector} #body #main #header-author > h3 #author-text'
        self.comment_link_selector = f'{self.current_thread_selector} #body #main #header-author yt-formatted-string a'
        self.comment_text_selector = f'{self.current_thread_selector} #body #main #expander #content #content-text'
        self.expand_replies_selector = f'{self.current_thread_selector} #replies #expander #more-replies > yt-button-shape > button'
        self.less_replies_selector = f'{self.current_thread_selector} #replies #expander #less-replies > yt-button-shape > button'
        self.reply_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > '\
                                f'ytd-comment-renderer:nth-child({child_count})'
        self.reply_author_name_selector = f'{self.reply_selector} #body #header-author #author-text yt-formatted-string'
        self.reply_link_selector = f'{self.reply_selector} #header-author yt-formatted-string a'
        self.reply_text_selector = f'{self.reply_selector} #comment-content #content #content-text'
        self.first_reply_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > '\
                                    'ytd-comment-renderer:nth-child(1) #content-text'
        self.more_replies_selector = f'{self.current_thread_selector} #replies #expander #expander-contents #contents > '\
                                    'ytd-continuation-item-renderer #button ytd-button-renderer yt-button-shape button'


    def time_to_stop_scraping(self):
        '''
            time_to_stop_scraping(self) -> Bool
            a helper method to determine if we should stop scraping comments, and
            if the webdriver should shut down. If the total number of comments parsed
            is greater than or equal to the limit, or if we have passed the specified
            time limit, then we return True (indicating we should stop scraping comments).
            Otherwise, return False.
        '''
        if self.limit and self.total_comments_parsed >= self.limit:
        #if self.total_comments_parsed >= 30:
            return True
        elif self.time_limit_exists:
            current_time = datetime.datetime.now()
            elapsed_time = current_time - self.start_time
            if (elapsed_time > self.total_time_limit):
                return True
        return False


    def log_debug_output(func):
        @wraps(func)
        def log_output(self, *args, **kwargs):
            if self.enabled_logging:
                self.logger.setLevel(logging.DEBUG)
            self.logger.debug(f'comment number: {(self.comment_thread_count + 1)}, comment info: {self.current_comment_json}')
            return func(self, *args, **kwargs)
        return log_output


    def return_scrolltop_value(self):
        '''
            return_scrolltop_value(self) -> Float
            return the amount that the container element has scrolled from the top
        '''
        return self.driver.execute_script(f'return document.querySelector("{self.comment_box_selector}").scrollTop;')


    def scroll_out_of_view(self, element):
        '''
            scroll_out_of_view(self, element) -> None
            scroll_out_of_view: YouTubeShortsIterator selenium.webdriver.remote.webelement.WebElement -> None
            scrolls the container of the element by the total height of the given element (including margins).
            This is normally used with the top-most visible element in the container so that it is scrolled out
            of visibility. The element passed in is of type selenium.webdriver.remote.webelement.WebElement .
        '''
        comment_box_container = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_box_selector))
        )
        comment_box_location = comment_box_container.location
        y_offset = comment_box_location['y']
        margin_top = element.value_of_css_property('margin-top').split('px')[0]
        margin_bottom = element.value_of_css_property('margin-bottom').split('px')[0]
        padding_top = element.value_of_css_property('padding-top').split('px')[0]
        padding_bottom = element.value_of_css_property('padding-bottom').split('px')[0]
        border_top = element.value_of_css_property('border-top-width').split('px')[0]
        border_bottom = element.value_of_css_property('border-bottom-width').split('px')[0]
        margin_top = int(margin_top)
        margin_bottom = int(margin_bottom)
        padding_top = int(padding_top)
        padding_bottom = int(padding_bottom)
        border_top = int(border_top)
        border_bottom = int(border_bottom)
        scroll_amount = element.size['height'] + margin_top + margin_bottom + padding_top + padding_bottom + border_top + border_bottom
        scrolltop_value = self.return_scrolltop_value()
        # Log element location and dimension info
        self.logger.debug(f'element id: {element.id}')
        self.logger.debug(f'amount container has scrolled down: {scrolltop_value}')
        self.logger.debug(f'element location: {element.location}')
        self.logger.debug(f'element size: {element.size}')
        self.logger.debug(f'margin-top of element: {margin_top}, margin-bottom of element: {margin_bottom}')
        self.logger.debug(f'padding-top of element: {padding_top}, padding-bottom of element: {padding_bottom}')
        self.logger.debug(f'border-top of element: {border_top}, border-bottom of element: {border_bottom}\n')
        amount_to_scroll = max(scroll_amount, 0)
        # offset the scrolling responsibilities to JavaScript
        try:
            self.driver.execute_script(f'document.querySelector("{self.comment_box_selector}").scrollTop += {amount_to_scroll}')
        except Exception as err:
            self.logger.exception(err)


    def iterate_child(self):
        '''
            iterate_child(self) -> (anyOf Dict None)
            Iterates through the replies of a youtube comment, aggregates the comment into a dictionary, and returns it.
        '''
        try:
            self.first_reply_comment = self.get_selector(self.first_reply_selector, wait_time=20)
            more_comments = self.element_exists(self.reply_selector) or self.element_exists(self.more_replies_selector)
        except:
            current_comment = self.current_comments_json
            # log these errors if the logger level is set to debug
            self.logger.debug(f'failed to find replies for comment number {(self.comment_thread_count + 1)} and css selector {self.first_reply_selector}')
            self.logger.debug(f'comment info for comment number {(self.comment_thread_count + 1)}: {current_comment}')
        else:
            self.scroll_out_of_view(self.parent_comment)
            while more_comments:
                self.current_reply = self.driver.find_element(By.CSS_SELECTOR, self.reply_text_selector)
                self.reply_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.reply_author_name_selector)
                name = self.reply_channel_name.text.strip()[1:]
                self.reply_link = self.driver.find_element(By.CSS_SELECTOR, self.reply_link_selector)
                reply_text = self.current_reply.text.strip()
                comment_link = ''
                full_reply = self.get_selector(self.reply_selector)
                self.scroll_out_of_view(full_reply)
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
                if not self.element_exists(self.reply_text_selector, wait_time=0.1):
                    if self.element_exists(self.more_replies_selector, wait_time=0.1):
                        more_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.more_replies_selector)
                        ActionChains(self.driver).move_to_element(more_replies_button).pause(0.5).click(more_replies_button).perform()
                        try:
                            next_comment = self.get_selector(self.reply_text_selector, wait_time=20)
                        except TimeoutException:
                            break
                more_comments = self.element_exists(self.reply_text_selector, wait_time=0.1) or\
                                self.element_exists(self.more_replies_selector, wait_time=0.1)
        finally:
            scrolltop_value = self.return_scrolltop_value()
            amount_to_scroll_up = scrolltop_value - self.parent_comment_pos
            self.driver.execute_script(f'document.querySelector("{self.comment_box_selector}").scrollTop -= {amount_to_scroll_up}')
            self.comment_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.less_replies_selector)
            ActionChains(self.driver).move_to_element(self.comment_replies_button).pause(0.5).click(self.comment_replies_button).perform()
            self.scroll_out_of_view(self.get_selector(self.current_thread_selector, wait_time=20))
            self.reply_count = 0
            self.comment_thread_count += 1
            resulting_comment = self.current_comments_json
            self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
            comment_thread_has_regex = self.thread_has_pattern
            self.reset_elements()
            if self.regex_pattern:
                if comment_thread_has_regex:
                    return resulting_comment
                else:
                    return None
            return resulting_comment


    def go_to_next(self):
        if self.time_to_stop_scraping():
            self.driver.quit()
            self.driver_started = False
            raise StopIteration
        else:
            try:
                self.current_comment = self.get_selector(self.comment_text_selector, wait_time=20)
                current_thread = self.get_selector(self.current_thread_selector, wait_time=20)
            except Exception as err:
                self.driver.quit()
                self.driver_started = False
                if not self.element_exists(self.current_thread_selector):
                    self.driver.quit()
                    self.driver_started = False
                    raise StopIteration
                self.logger.exception(err)
                raise StopIteration
            self.comment_channel_name = self.get_selector(self.commenter_selector)
            name = self.comment_channel_name.text.strip()[1:]
            self.comment_link = self.get_selector(self.comment_link_selector)
            comment_link = self.comment_link.get_attribute('href')
            comment_content = self.current_comment.text.strip()
            resulting_comment = {
                'commenter': name,
                'comment content': comment_content,
                'link': comment_link,
                'children': []
            }
            if self.element_exists(self.expand_replies_selector, wait_time=0.1):
                try:
                    self.parent_comment = self.current_comment
                    self.parent_comment_pos = self.return_scrolltop_value()
                    self.current_comments_json = resulting_comment
                    self.comment_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.expand_replies_selector)
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
                self.scroll_out_of_view(current_thread)
                self.total_comments_parsed += 1
                self.comment_thread_count += 1
                self.reset_elements()
                self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
                if self.regex_pattern:
                    comment_match = re.search(self.regex_pattern, resulting_comment['comment content'], re.IGNORECASE)
                    if comment_match:
                        return resulting_comment
                    else:
                        return None
                return resulting_comment
            return resulting_comment


    def __iter__(self):
        return self


    @setup
    def __next__(self):
        try:
            return self.go_to_next()
        except:
            if self.driver_started:
                self.driver.quit()
            raise StopIteration


if __name__ == '__main__':
    # Another video to test: https://www.youtube.com/shorts/re6MHKI-t-g
    for comment in YoutubeShortsIterator('https://www.youtube.com/shorts/7uctTsKeLdM'):
        print('hello world')
