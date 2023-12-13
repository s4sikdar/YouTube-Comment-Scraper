import argparse
import json
from iterators.comment_iterator import CommentIterator

def main():
    parser = argparse.ArgumentParser(
        description=(
            'A YouTube comment scraper that scrapes the comments in the YouTube comments section for a video of your choice, matching a regular expression of your choosing.'
            'The comments are scraped and added to the a JSON file whose name you can specify.'
        )
    )
    parser.add_argument(
        '-l', '--limit', type=int, default=None, help='the maximum number of comments we will scrape'
    )
    parser.add_argument(
        '--url', type=str, default=None, required=True, help='the YouTube video url for the video you want to scrape (should be available)'
    )
    parser.add_argument(
        '--pattern', type=str, default=None,
        help='The regular expression pattern you use to parse and match text patterns in comments. By default, all comments are matched and added to the JSON.'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='comments.json', help='The output file you will store the JSON in. Defaults to "comments.json".'
    )
    arguments = parser.parse_args()
    comments = {
        'comments': []
    }
    with open(arguments.output, 'w') as output_file:
        for item in CommentIterator(arguments.url, arguments.limit, arguments.pattern):
            comments['comments'].append(item)
        output_file.write(json.dumps(comments))

if __name__ == '__main__':
    main()
