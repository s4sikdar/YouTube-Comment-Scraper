from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time
import json

class CommentIterator:
    def __init__(self, youtube_url, comment_limit=10, regex=None):
        self.comment_count = 0
        self.limit = comment_limit
        self.driver = webdriver.Chrome()
        self.driver.get(youtube_url)
        self.driver.maximize_window()
        self.title_selector = '#title > h1 > yt-formatted-string'
        self.current_comment = None
        self.comment_channel_name = None
        self.comment_link = None
        self.amount_scrolled = 0
        comment_number_selector = '#count > yt-formatted-string > span'
        title = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.title_selector))
        )
        #print(title.text)
        #video = self.driver.find_element(By.CSS_SELECTOR, '#movie_player')
        #video.click()
        y_pos = title.location_once_scrolled_into_view['y'] - 100
        ActionChains(self.driver).scroll_by_amount(0,y_pos).perform()
        self.amount_scrolled += y_pos
        #comment_number = WebDriverWait(self.driver, 5).until(
        #    EC.presence_of_element_located((By.CSS_SELECTOR, comment_number_selector))
        #)
        #comment_number_location = comment_number.location
        #ActionChains(self.driver).scroll_to_element(title).pause(5).perform()
        #print(comment_number.text)
        self.comment_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #content-text'
        self.commenter_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #author-text > span'
        self.comment_link_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #header-author > yt-formatted-string > a'
        #print(self.comment_selector)


    def __iter__(self):
        return self

    def __next__(self):
        if self.comment_count == self.limit:
            self.driver.quit()
            raise StopIteration
        #current_comment = self.driver.find_element(By.CSS_SELECTOR, self.comment_selector)
        self.current_comment = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.comment_selector))
        )
        self.comment_channel_name = self.driver.find_element(By.CSS_SELECTOR, self.commenter_selector)
        name = self.comment_channel_name.text.strip()[1:]
        self.comment_link = self.driver.find_element(By.CSS_SELECTOR, self.comment_link_selector)
        comment_link = self.comment_link.get_attribute('href')
        #self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.comment_count += 1
        y_pos = self.current_comment.location_once_scrolled_into_view['y'] - 100
        ActionChains(self.driver).scroll_by_amount(0, y_pos).perform()
        self.amount_scrolled += y_pos
        #print(self.comment_count)
        comment_content = self.current_comment.text.strip()
        resulting_comment = {
            'commenter': name,
            'main comment': comment_content,
            'link': comment_link
        }
        #print(comment_content)
        self.comment_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #content-text'
        self.commenter_selector = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #author-text > span'
        self.comment_link = f'#contents > ytd-comment-thread-renderer:nth-child({(self.comment_count + 1)}) #header-author > yt-formatted-string > a'
        #return comment_content
        return resulting_comment

comments = []

with open('comments.json', 'w') as comment_json:
    for comment in CommentIterator('https://www.youtube.com/watch?v=mqxHzWJlqps', 500):
        comments.append(comment)
    json_comments = json.dumps({'comments': comments})
    comment_json.write(json_comments)
