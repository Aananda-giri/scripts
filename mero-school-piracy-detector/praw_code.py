import datetime
import math
import praw
from prawcore import NotFound
import os
import re
from dotenv import load_dotenv
load_dotenv()
import urllib

reddit = praw.Reddit(
    client_id= os.environ['RD_CLIENT_ID'],          # config.RD_CLIENT_ID,
    client_secret= os.environ['RD_CLIENT_SECRET'],  # config.RD_CLIENT_SECRET,
    password= os.environ['RD_PASS'],                # config.RD_PASS, 
    user_agent="praw_test",
    username=os.environ['USERNAME'],
)

# it is a read-only instance i.e. it can't be used to modify reddit
reddit.read_only = True

def sub_exists(sub):
    exists = True
    try:
        reddit.subreddits.search_by_name(sub, exact=True)
    except NotFound:
        exists = False
    return exists

# sub_exists('IOENepal')
# sub_exists('IOENepaldsfa3')

import re


def convert_facebook_link(link):
    '''
    convert facebook follow links to actual links
    e.g.
    facebook follow link: https://l.facebook.com/l.php?u=https%3A%2F%2Fdrive.google.com%2Fdrive%2Ffolders%2F1HLW6uCzIqTHYLC_qyDgJuG5TFlvuQXLg%3Fusp%3Ddrive_link&h=AT11bALWUdEIJkMteYsptSXhxkhyqO1J19pq-o9pyhbBH29ulnEOYXX_mo7wHAH6fJ0RniWozmViIyfVKeaMDSqjCqR_L4Peka30YqdDaCp0NEAn95ZyxWNq4l30wLtV0eZnERkkYjMKAFU&s=1
    '''
    if not link.startswith('https://l.facebook.com/l.php?u='):
        # print('not facebook follow link')
        return link
    else:
        # print('isfacebook follow link')
        # Extract the actual link from the facebook follow link
        actual_link = re.search(r'u=(.*?)&', link).group(1)
        # Decode the URL
        actual_link = urllib.parse.unquote(actual_link)
        return actual_link

def extract_links(text):
    # Regular expression to find URLs within parentheses in markdown format
    markdown_pattern = r'\[.*?\]\((.*?)\)'
    # Extract markdown links
    markdown_links = re.findall(markdown_pattern, text)
    
    # Remove markdown links from the text
    text_without_markdown = re.sub(markdown_pattern, '', text)
    
    # Regular expression to find direct URLs
    url_pattern = r'https?://\S+'
    # Extract direct links
    direct_links = re.findall(url_pattern, text_without_markdown)
    
    # Combine both types of links
    all_links = markdown_links + direct_links
    
    # Convert facebook follow links to actual links
    all_links = [convert_facebook_link(link) for link in all_links]
    
    return all_links

# Test

# text = '''
# You can find here
# [https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive\\_link](https://drive.google.com/drive/folders/first_type_again?usp=drive_link)
# also maybe here: [https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive\\_link](https://drive.google.com/drive/folders/first_type?usp=drive_link)

# this is the link: https://drive.google.com/drive/folders/second_type?usp=drive_link
# '''
# links = extract_links(text)
# print(links)
# output: ['https://drive.google.com/drive/folders/first_type_again?usp=drive_link', 'https://drive.google.com/drive/folders/first_type?usp=drive_link', 'https://drive.google.com/drive/folders/second_type?usp=drive_link']

# other links contains direct links like
text = "this is the link: https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive_link"


def get_reddit_posts(subreddit_name, datetime_before=None, datetime_after=None, how_many=None):
    '''
        * Returns posts and comments only if the comments contain links
    '''
    if not sub_exists(subreddit_name):
        print(f"Subreddit {subreddit_name} does not exist")
        return
    
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    before_timestamp = int(datetime_before.timestamp()) if datetime_before else math.inf
    after_timestamp = int(datetime_after.timestamp()) if datetime_after else 0
    
    # for submission in [reddit.submission(id='1cizbg3')]:
    for submission in subreddit.new(limit=how_many):
        if (submission.created_utc < before_timestamp) and (submission.created_utc > after_timestamp):
            post_data = {
                'title': submission.title,
                'author': submission.author.name if submission.author else 'deleted',
                'created_utc': submission.created_utc,
                'selftext': submission.selftext,
                'url': submission.url,
                'comments': []
            }
            # 
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                links_contained = extract_links(comment.body)
                if links_contained:
                    # only add comments with links
                    post_data['comments'].append({
                        'author': comment.author.name if comment.author else 'deleted',
                        'body': comment.body,
                        'created_utc': comment.created_utc,
                        'comment_link': f'https://reddit.com{comment.permalink}',
                        
                        # These are links contained in the comment body
                        'links_contained': links_contained
                    })
                # time.sleep(0.2) # for praw rate limit
                
            if post_data['comments']:
                # only yield if there are links in the comments
                yield post_data
            
            # posts.append(post_data)
    # return posts

if __name__ == "__main__":
    # # Example usage:
    subreddit_name = 'IOENepal'  # specify your subreddit
    sleep_duration = 12 * 60 * 60   # 12 hours

    datetime_now = datetime.datetime.now() 

    # previous crawl time
    datetime_previous = datetime_now - datetime.timedelta(seconds=sleep_duration)

    # reddit_posts = list(get_reddit_posts(subreddit=subreddit_name, datetime_before=datetime_now, datetime_after=datetime_previous, how_many=None))
    reddit_posts = list(get_reddit_posts(subreddit=subreddit_name, datetime_before=None, datetime_after=None, how_many=None))
    print(len(reddit_posts))
    urls = set()
    for comment in reddit_posts[0]['comments']:
        # print(comment['links_contained'])
        [urls.add(link) for link in comment['links_contained']]
