# Youtube-Comment-Scraper
An iterator that provides you with dictionaries containing key value pairs about youtube comments under a YouTube videos of your choice. It uses the iterator pattern with Selenium to abstract away the scraping of YouTube videos (public videos with comments enabled), and allows you to iterate over dictionaries representing comments for your own purposes. The code is under construction for standalone use, but the package itself can be used for your own personal projects.
### YouTube Video Requirements
The video must be public and have comments enabled. The module only returns back what it sees on the page. It returns the following information in the dictionary:
1. The comment text, with key "comment content"
2. The channel name, with key "commenter"
3. The link to the comment, with key "link"
4. A list of children comments, with dictionaries that have the above keys except for their own list of children
