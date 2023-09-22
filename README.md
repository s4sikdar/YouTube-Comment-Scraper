# Youtube-Comment-Scraper
An iterator that provides you with dictionaries containing key value pairs about youtube comments under a YouTube videos of your choice. It uses the iterator pattern with Selenium to abstract away the scraping of YouTube videos (public videos with comments enabled), and allows you to iterate over dictionaries representing comments for your own purposes. 
## Installation Steps for Windows
1) Clone the repository.
2) Open git bash. Navigate to the location of this repository.
3) Run the following command below.
```
python -m venv ./{directory name of your choice for the virtual environment}/
```
4) Run the following in git bash.
```
source ./{directory name of your choice for the virtual environment}/Scripts/activate
```
5) Run the following commannd.
```
pip install -r requirements.txt
```
6) Open `comment_iterator.py` and change the constructor for CommentIterator to be the link of a YouTube video you want scraped as shown below. You can also add regular expressions by specifying the regex parameter in the constructor as shown below.
```
with open('comments.json', 'w') as comment_json:
    for comment in CommentIterator('https://www.youtube.com/watch?v=sp1rkgx_aik', regex=r'phrase to search'):
        if comment:
            comments.append(comment)
    json_comments = json.dumps({'comments': comments})
    comment_json.write(json_comments)
```
