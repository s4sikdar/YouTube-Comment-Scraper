import argparse
import json
import sys
import re
from iterators.factory import IteratorFactory


def valid_arguments(argument_parser):
    '''
        valid_arguments(argument_parser) -> Bool
        Check if the arguments passed in are valid, and return True if so.
        Return False otherwise.
    '''
    invalid_time_limit = (
        ((argument_parser.hours < 0) or \
         (argument_parser.minutes < 0) or \
         (argument_parser.seconds < 0))
    )
    too_few_seconds = ((argument_parser.hours == 0) and (argument_parser.minutes == 0) and ((argument_parser.seconds > 0) and (argument_parser.seconds < 30)))
    invalid_comment_limit = (argument_parser.limit != None) and (argument_parser.limit <= 0)

    if invalid_time_limit:
        print(
            'If time limits are specified, input for one of --hours, --minutes, and --seconds must be greater than 0. You entered a negative value for one of them. Exiting with an error code of 1.',
            file=sys.stderr, flush=True
        )
        return False
    elif invalid_comment_limit:
        print(
            'Input for the --limit parameter must be greater than 0. Exiting with an error code of 1.',
            file=sys.stderr, flush=True
        )
        return False
    elif too_few_seconds:
        print(
        'The combined total of minutes, hours and seconds specified is less than 30. The combined total of minutes, hours and seconds specified must be at least 30 seconds. Exiting with an error code of 1.',
        file=sys.stderr, flush=True
        )
        return False
    return True


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
        help='The regular expression pattern you use to parse and match text patterns in comments (case insensitive). By default, all comments are matched and added to the JSON.'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='comments.json', help='The output file you will store the JSON in. Defaults to "comments.json".'
    )
    parser.add_argument(
        '--hours', type=int, default=0, help='The maximum number of hours you want the program to run.'
    )
    parser.add_argument(
        '--minutes', type=int, default=0, help='The maximum number of minutes you want the program to run.'
    )
    parser.add_argument(
        '--seconds', type=int, default=0, help='The maximum number of seconds you want the program to run.'
    )
    arguments = parser.parse_args()
    if not valid_arguments(arguments):
        exit(1)
    comments = {
        'comments': []
    }
    with open(arguments.output, 'w') as output_file:
        for item in IteratorFactory(arguments.url, arguments.limit, arguments.pattern, arguments.hours, arguments.minutes, arguments.seconds):
            comments['comments'].append(item)
        output_file.write(json.dumps(comments))


if __name__ == '__main__':
    main()
