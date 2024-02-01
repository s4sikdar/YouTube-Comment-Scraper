import re
from iterators.implementations.comment_iterator import CommentIterator
from iterators.implementations.youtube_shorts_iterator import YoutubeShortsIterator


class IteratorFactory:
    iterators = {
        CommentIterator.__name__: CommentIterator,
        YoutubeShortsIterator.__name__: YoutubeShortsIterator
    }

    def __new__(cls, url, *args, **kwargs):
        for category in cls.iterators:
            if re.match(cls.iterators[category].regex_pattern(), url):
                return cls.iterators[category](url, *args, **kwargs)
        raise Exception('The link "{}" is for a site/post/video that does not have an iterator to support scraping it.'.format(url))

