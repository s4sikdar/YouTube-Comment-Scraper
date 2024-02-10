'''
This module provides an Iterlist class that serves as a wrapper for the YouTube comment iterator classes. This is so that you have an iterator that
can be used with json.dump. This allows for you to write dictionaries to json objects as they are read in. This way the entire dictionary is never
read in memory. I found the code from this stack overflow answer: https://stackoverflow.com/questions/52137608/writing-a-large-json-array-to-file
'''

class IteratorAsList(list):
    def __init__(self, it):
        self.it = it

    def __iter__(self):
        return self.it

    def __len__(self):
        return 1
