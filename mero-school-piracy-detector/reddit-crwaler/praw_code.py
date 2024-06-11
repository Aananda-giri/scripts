import config
import datetime
import math
import praw
from prawcore import NotFound
import re


reddit = praw.Reddit(
    client_id= config.RD_CLIENT_ID,# os.environ['RD_CLIENT_ID'],
    client_secret= config.RD_CLIENT_SECRET, # os.environ['rd_client_secret'],
    password= config.RD_PASS,    # os.environ['rd_pass'],
    user_agent="praw_test",
    username="Alternative-Ad-8849",
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




def extract_urls(text):
    # Regular expression pattern to match URLs
    url_pattern = re.compile(
        r'http[s]?://'  # http:// or https://
        r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'  # Domain name
        r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # or URL-encoded characters
    )
    urls = url_pattern.findall(text)
    return list(set(urls))


def get_reddit_posts(subreddit, datetime_before, datetime_after=None, how_many=None):
    if not sub_exists(subreddit_name):
        print(f"Subreddit {subreddit_name} does not exist")
        return
    
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    before_timestamp = int(datetime_before.timestamp()) if datetime_before else math.inf
    after_timestamp = int(datetime_after.timestamp()) if datetime_after else 0
    
    
    # for submission in subreddit.new(limit=how_many):
    for submission in [reddit.submission(id='1cizbg3')]:
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
                
            if post_data['comments']:
                # only yield if there are links in the comments
                yield post_data
            
            # posts.append(post_data)
    # return posts

# if __name__ == "__main__":
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