import datetime
import math
import praw
from prawcore import NotFound
import os
import re
from dotenv import load_dotenv
load_dotenv()

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

# def extract_urls(text):
#     # Regular expression pattern to match URLs
#     url_pattern = re.compile(
#         r'http[s]?://'  # http:// or https://
#         r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'  # Domain name
#         r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # or URL-encoded characters
#     )
#     urls = url_pattern.findall(text)
#     return list(set(urls))

def extract_urls(text):
    '''
    # links are values within () if pattern [link_text](actual_link) exists

    r'\[.*?\]\((.*?)\)' is the regular expression pattern used to match the links.
    \[.*?\] matches the text within the square brackets.
    \(.*?\) matches the text within the parentheses, which is the actual link we want to extract.
    The ? after * makes the match non-greedy, ensuring it stops at the first closing parenthesis.
    '''
    # Regular expression to find URLs within parentheses
    pattern = r'\[.*?\]\((.*?)\)'
    
    # Find all matches in the text
    links = re.findall(pattern, text)
    
    return list(set(links))


# # E.g.
# text = '''You can find here
# [https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive\\_link](https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive_link)
# also maybe here: [https://drive.google.com/drive/folders/1Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive\\_link](https://drive.google.com/drive/folders/2Ruot2y65dzKW5vf7FYmlpXyK1w76Eqf8?usp=drive_link)'''
# print(extract_urls(text))


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
                links_contained = extract_urls(comment.body)
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