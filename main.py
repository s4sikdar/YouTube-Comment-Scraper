import argparse
from iterators.comment_iterator import CommentIterator

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--limit', type=int, default=None)
parser.add_argument('--url', type=str, default=None, required=True)
parser.add_argument('--pattern', type=str, default=None)
parser.add_argument('-o', '--output', type=str, default=None)

if __name__ == '__main__':
    print(0)
