# Youtube-Comment-Scraper
An iterator that provides you with dictionaries containing key value pairs about youtube comments under a YouTube videos of your choice. It uses the iterator pattern with Selenium to abstract away the scraping of YouTube videos (public videos with comments enabled), and allows you to iterate over dictionaries representing comments for your own purposes. There is a script called `main.py` that you can invoke, and it will put the results of the parsing into a json file called "comments.json". You can also import the iterator and use it for your own purposes. You may have to periodically update the selectors used by the script, as YouTube's HTML selectors are subject to change. You can specify a regular expression to filter for comments as well.
### YouTube Video Requirements
The video must be public and have comments enabled. The module only returns back what it sees on the page. It returns the following information in the dictionary:
1. The comment text, with key "comment content"
2. The channel name, with key "commenter"
3. The link to the comment, with key "link"
4. A list of children comments, with dictionaries that have the above keys except for their own list of children
### Options taken by the script
Script usage: `python main.py [-h] [-l LIMIT] --url URL [--pattern PATTERN] [-o OUTPUT] [--hours HOURS] [--minutes MINUTES] [--seconds SECONDS]`
Arguments taken:
```
  -h, --help            	show this help message and exit

  -l LIMIT, --limit LIMIT	the maximum number of comments we will scrape

  --url URL             	the YouTube video url for the video you want to scrape
                        	(should be available)

  --pattern PATTERN     	The regular expression pattern you use to parse and
                        	match text patterns in comments. By default, all
                        	comments are matched and added to the JSON.

  -o OUTPUT, --output OUTPUT	The output file you will store the JSON in. Defaults
                        	to "comments.json".

  --hours HOURS         	The maximum number of hours you want the program to
                        	run.

  --minutes MINUTES     	The maximum number of minutes you want the program to
                        	run.

  --seconds SECONDS     	The maximum number of seconds you want the program to
                        	run.
```
### Setup steps
1. Ensure you have git bash installed.
2. Clone the following repository by using `git clone https://github.com/s4sikdar/YouTube-Comment-Scraper.git`
3. Run `source env_setup.sh` to setup the virtual environmnent and install all required dependencies. You can also have the script download the latest version of chromedriver if you specify the `-d` flag. **You should run `./env_setup.sh -h` first before you specify any flags.**
4. From there, once you install the latest version of chromedriver and add it to a directory in your $PATH environment variable, you can run the script from there. **First run **`python main.py --help`** for usage documentation.**
