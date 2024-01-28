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

