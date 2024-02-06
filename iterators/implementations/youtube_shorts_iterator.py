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
        self.pixels_left_from_parent = 0
        # Comment selectors
        self.play_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(1) button'
        self.mute_button_selector = 'ytd-shorts-player-controls yt-icon-button:nth-child(2) button'
        self.expand_comments_button = '#comments-button ytd-button-renderer yt-button-shape label button'
        self.comment_box_selector = '#shorts-container #watch-while-engagement-panel #contents #contents'
        #self.comment_container_selector = '#shorts-container #watch-while-engagement-panel #contents'
        # CSS selectors for the section containing comments
        self.current_thread_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)})'
        self.commenter_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                '#body #main #header-author > h3 #author-text'
        self.comment_link_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#body #main #header-author yt-formatted-string a'
        self.comment_text_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#body #main #expander #content #content-text'
        self.expand_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) ' \
                                    '#replies #expander #more-replies > yt-button-shape > button'
        self.less_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) ' \
                                    '#replies #expander #less-replies > yt-button-shape > button'
        self.reply_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) ' \
                                '#replies #expander #expander-contents #contents > '\
                                f'ytd-comment-renderer:nth-child({(self.comment_thread_count + 1)})'
        self.reply_author_name_selector = f'{self.reply_selector} #body #author-text > yt-formatted-string'
        self.reply_link_selector = f'{self.reply_selector} #header-author > yt-formatted-string > a'
        self.reply_text_selector = f'{self.reply_selector} #comment-content #content #content-text'
        self.first_reply_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#replies #expander #expander-contents #contents > '\
                                    'ytd-comment-renderer:nth-child(1) #content-text'
        self.more_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({(self.comment_thread_count + 1)}) '\
                                    '#replies #expander #expander-contents #contents > '\
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
            self.logger.exception(f'element with css selector {css_selector} was not found (error below)')
            self.logger.exception(err)
            return False
        else:
            return True


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
            play_video(self) -> None
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
                self.driver.get(self.youtube_url)
                self.driver.maximize_window()
                self.pause_video()
                self.mute_video()
                expand_comments_button = self.get_selector(self.expand_comments_button)
                expand_comments_button.click()
                self.set_time_limit(self.hours, self.minutes, self.seconds)
                #time.sleep(10)
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
        #self.comment_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #content-text'
        #self.commenter_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #author-text'
        #self.comment_link_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #header-author > yt-formatted-string > a'
        #self.replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #more-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        #self.less_replies_button_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #less-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        #self.comment_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #content-text'
        #self.comment_reply_channel = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #author-text > yt-formatted-string'
        #self.comment_reply_link = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child({child_count}) #header-author > yt-formatted-string > a'
        #self.more_replies_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies #button > ytd-button-renderer > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill'
        #self.first_reply_selector = f'#contents > ytd-comment-thread-renderer:nth-child({count}) #replies > ytd-comment-replies-renderer #contents > ytd-comment-renderer:nth-child(1) #content-text'
        self.commenter_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) '\
                                '#body #main #header-author > h3 #author-text'
        self.comment_link_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) '\
                                    '#body #main #header-author yt-formatted-string a'
        self.comment_text_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) '\
                                    '#body #main #expander #content #content-text'
        self.expand_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) ' \
                                    '#replies #expander #more-replies > yt-button-shape > button'
        self.less_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) ' \
                                    '#replies #expander #less-replies > yt-button-shape > button'
        self.reply_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) ' \
                                '#replies #expander #expander-contents #contents > '\
                                f'ytd-comment-renderer:nth-child({child_count})'
        self.reply_author_name_selector = f'{self.reply_selector} #body #author-text > yt-formatted-string'
        self.reply_link_selector = f'{self.reply_selector} #header-author > yt-formatted-string > a'
        self.reply_text_selector = f'{self.reply_selector} #comment-content #content #content-text'
        self.first_reply_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) '\
                                    '#replies #expander #expander-contents #contents > '\
                                    'ytd-comment-renderer:nth-child(1) #content-text'
        self.more_replies_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count}) '\
                                    '#replies #expander #expander-contents #contents > '\
                                    'ytd-continuation-item-renderer #button ytd-button-renderer yt-button-shape button'
        self.current_thread_selector = f'{self.comment_box_selector} ytd-comment-thread-renderer:nth-child({count})'


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
            #comment_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.commenter_selector)
            #commenter_name = comment_channel_name.text.strip()[1:]
            #reply_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.comment_reply_channel)
            #name = reply_channel_name.text.strip()[1:]
            #commenter_name = self.current_comment_json['commenter']
            self.logger.debug(f'comment number: {(self.comment_thread_count + 1)}, comment info: {self.current_comment_json}')
            #self.logger.debug(f'comment reply number: {(self.reply_count + 1)}, comment reply name: {name}')
            return func(self, *args, **kwargs)
        return log_output


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
        comment_text_element = element.find_element(By.CSS_SELECTOR, '#body #main #expander #content #content-text')
        # Log element location and dimension info
        self.logger.debug(f'element id: {element.id}')
        self.logger.debug(f'element text: {comment_text_element.text}')
        self.logger.debug(f'element location: {element.location}')
        self.logger.debug(f'element size: {element.size}')
        self.logger.debug(f'margin-top of element: {margin_top}, margin-bottom of element: {margin_bottom}')
        self.logger.debug(f'padding-top of element: {padding_top}, padding-bottom of element: {padding_bottom}')
        self.logger.debug(f'border-top of element: {border_top}, border-bottom of element: {border_bottom}\n')
        amount_to_scroll = max(scroll_amount, 0)
        #self.pixels_left_from_parent = margin
        # offset the scrolling responsibilities to JavaScript
        try:
            self.driver.execute_script(f'document.querySelector("{self.comment_box_selector}").scrollTop += {amount_to_scroll}')
            #time.sleep(1)
            #breakpoint()
            #ActionChains(self.driver).scroll_to_element(element).perform()
        except Exception as err:
            #breakpoint()
            print(err)
            self.logger.debug(err)
            self.logger.debug(err.__traceback__)
            self.logger.debug(err.__cause__)
            self.logger.debug(err.__context__)
            #self.logger.debug(traceback.print_tb())
            #self.logger.debug(traceback.print_exception())
            #self.logger.debug(traceback.print_stack())
            self.logger.debug('traceback')
            self.logger.debug(traceback.print_tb(err.__traceback__))
            self.logger.debug(traceback.print_exception(err))
            self.logger.debug(traceback.print_stack())
        #self.amount_scrolled += 100


    def go_to_next(self):
        #breakpoint()
        if self.time_to_stop_scraping():
            self.driver.quit()
            self.driver_started = False
            raise StopIteration
        else:
            try:
                #self.current_comment = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
                #    EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_text_selector))
                #)
                self.current_comment = self.get_selector(self.comment_text_selector, wait_time=20)
                current_thread = self.get_selector(self.current_thread_selector, wait_time=20)
                #current_thread = WebDriverWait(self.driver, timeout=20, poll_frequency=0.1).until(
                #    EC.presence_of_element_located((By.CSS_SELECTOR, self.current_thread_selector))
                #)
                # current_thread_selector
            except Exception as err:
                self.driver.quit()
                self.driver_started = False
                if not self.element_exists(self.current_thread_selector):
                    self.driver.quit()
                    self.driver_started = False
                    raise StopIteration
                #self.logger.debug(err.__traceback__)
                #self.logger.debug(err.__cause__)
                #self.logger.debug(err.__context__)
                #self.logger.debug('traceback')
                #self.logger.debug(traceback.print_tb(err.__traceback__))
                #self.logger.debug(traceback.print_exception(err))
                #self.logger.debug(traceback.print_stack())
                self.logger.exception(err)
                raise StopIteration
            self.comment_channel_name = self.get_selector(self.commenter_selector)
            #self.comment_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.commenter_selector)
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
            self.scroll_out_of_view(current_thread)
            #y_pos = self.current_comment.location_once_scrolled_into_view['y'] - 100
            #ActionChains(self.driver).scroll_by_amount(0, y_pos).perform()
            self.total_comments_parsed += 1
            self.comment_thread_count += 1
            self.reset_elements()
            self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
            #if self.element_exists(self.replies_button_selector):
            #    try:
            #        self.parent_comment = self.current_comment
            #        self.parent_comment_pos = self.amount_scrolled
            #        self.current_comments_json = resulting_comment
            #        self.comment_replies_button = self.driver.find_element(By.CSS_SELECTOR, self.replies_button_selector)
            #        ActionChains(self.driver).move_to_element(self.comment_replies_button).pause(0.5).click(self.comment_replies_button).perform()
            #    except:
            #        return resulting_comment
            #    else:
            #        if self.regex_pattern and (not self.thread_has_pattern):
            #            comment_match = re.search(self.regex_pattern, resulting_comment['comment content'], re.IGNORECASE)
            #            if comment_match:
            #                self.thread_has_pattern = True
            #        return self.iterate_child()
            #else:
            #    self.comment_thread_count += 1
            #    self.update_selectors((self.comment_thread_count + 1), (self.reply_count + 1))
            #    if self.regex_pattern:
            #        comment_match = re.search(self.regex_pattern, resulting_comment['comment content'], re.IGNORECASE)
            #        if comment_match:
            #            return resulting_comment
            #        else:
            #            return None
            #    return resulting_comment
            return resulting_comment


    def __iter__(self):
        return self


    @setup
    def __next__(self):
        #self.driver.quit()
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