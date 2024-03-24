from abc import ABC, abstractmethod


class ABCIterator(ABC):

    @abstractmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "You should not see this exception message. Just in case, the problem is that the __init__ method has not been implemented"
        )

    @abstractmethod
    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        raise NotImplementedError(
            "You should not see this exception message. Just in case, the problem is that the __next__ method has not been implemented"
        )

    @staticmethod
    @abstractmethod
    def regex_pattern():
        raise NotImplementedError(
            "You should not see this exception message. Just in case, the problem is that the regex_pattern method has not been implemented"
        )
