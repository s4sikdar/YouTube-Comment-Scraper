import re
from pkgutil import iter_modules
from importlib import import_module
from inspect import isclass
from iterators.implementations.abstract_base import ABCIterator
import iterators.implementations as impl


class IteratorFactory:

    def __new__(cls, url, *args, **kwargs):
        # This code dynamically imports all classes from the iterators/implementations/ folder, and puts all imported
        # subclasses from ABCIterator in the iterators dictionary. This dictionary is iterated over and the url is matched
        # with the regex pattern respective to that class (by running re.match with the regex returned by the regex_pattern method).
        # Here is a link to the article where I found the code snippet to go off of:
        # https://julienharbulot.com/python-dynamical-import.html
        iterators = {}
        for (_, module_name, _) in iter_modules(impl.__path__):
            module = import_module(f"iterators.implementations.{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if (not (attribute is ABCIterator)) and \
                    (isclass(attribute) and issubclass(attribute, ABCIterator)):
                    iterators[attribute.__name__] = attribute
        for category in iterators:
            if re.match(iterators[category].regex_pattern(), url):
                return iterators[category](url, *args, **kwargs)
        raise Exception('The link "{}" is for a site/post/video that does not have an iterator to support scraping it.'.format(url))

