from bloom import get_bloom_thread
import time
import csv
import datetime
from drive_crawler import get_owner_info
from gemini_response import is_mero_school_related_post
from praw_code import sub_exists, get_reddit_posts
from csv_functions import save_to_csv, read_csv
from functions import is_social_media_link
# Bloom Filter to store crawled page links
crawled_page_links = get_bloom_thread()

# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']

# sleep duration:12 hours; after each crawl operation
sleep_duration = 12 * 60 * 60   # 12 hours

# Subreddits to crawl
subreddit_datas = [
    {
        'subreddit': 'IOENepal',
        'crwal_since_beginning': False  # False by default. (it is set to true later if subreddit is not already crawled from the beginning)
    }
]

# Check if subreddit is already crawled from the beginning: if yes only crawl from past 12 hours
for subreddit_data in subreddit_datas:
    subreddit = subreddit_data['subreddit']
    subreddit_link = "https://www.reddit.com/r/" + subreddit_data['subreddit']
    if subreddit_link not in crawled_page_links:
        # Not already crawled from the beginning
        crawled_page_links.add(subreddit_link)
        subreddit_data['crwal_since_beginning']=True    # Enable to crawl from begining.

datetime_now = datetime.datetime.now() 
# previous crawl time
datetime_previous = datetime_now - datetime.timedelta(seconds=sleep_duration)

# Data for pdf engine
pdf_engine_data = []

# To store piracy data
piracy_data = []
posts_crawled = 0
comments_crawled = 0

for subreddit_data in subreddit_datas:
    subreddit = subreddit_data['subreddit']
    if subreddit_data['crwal_since_beginning']:
        # Crawl all posts from the beginning
        print('--------------------------------------------------------------------')
        print(f'\t subreddit: {subreddit}. Crawling all posts from the beginning')
        print('--------------------------------------------------------------------', end="\n\n")
        reddit_posts = get_reddit_posts(subreddit_name=subreddit, datetime_before=None, datetime_after=None, how_many=None)
        print('got reddit posts')
    else:
        print('--------------------------------------------------------------------')
        print(f'\t subreddit: {subreddit}. Crawling from past {sleep_duration/(60*60)} hours')
        print('--------------------------------------------------------------------', end='\n\n')
        # reddit_posts = get_reddit_posts(subreddit=subreddit, datetime_before=None, datetime_after=None, how_many=None)
        reddit_posts = get_reddit_posts(subreddit_name=subreddit, datetime_before=datetime_now, datetime_after=datetime_previous, how_many=None)
        print('got reddit posts')
    for each_post in reddit_posts:
        posts_crawled += 1
        print('$') # To know that the code is running
        if each_post['url'] not in crawled_page_links:
            # Save crwaled page link using bloom filter
            crawled_page_links.add(each_post['url'])
        else:
            # page is already crawled: Skip subreddit 
            # Since subreddits are fetched using 'new' filter, we can use `break` instead of `continue`
            # break
            # But again gemini is giving "429:quota exhausted" error so we are using `continue`
            continue
        
        for comment in each_post['comments']:
            comments_crawled += 1
            # check if post is about mero-school
            # if is_mero_school_related_post(each_post['title'] + each_post['selftext'] + '\n\n' + comment['body']):
            mero_school_post = is_mero_school_related_post(each_post['title'] + each_post['selftext'] + '\n\n' + comment['body'])
            print(f'Post: {each_post["title"]} {each_post["url"]}')
            '''comment['links_contained'] are Links within the comment content.
            e.g. 
            if comment_content = "yo drawing ko ho hai: https://drive.google.com/drive/mobile/folders/1jeQcQA0jdzvLCz-cTTR3LVioVO5bqPh9?usp=drive_link&pli=1"
            then comment['links_contained'] = ['https://drive.google.com/drive/mobile/folders/1jeQcQA0jdzvLCz-cTTR3LVioVO5bqPh9?usp=drive_link&pli=1']
            '''
            for link in comment['links_contained']:
                # returns owner info if link is google drive link so no need to check if it is google drive link
                owner_info, is_drive_link = get_owner_info(link)
                
                link_type = None
                if is_drive_link and owner_info:
                    link_type = 'google-drive'    
                elif is_drive_link and not owner_info:
                    link_type = 'google-drive-private'
                else:
                    # Check if link belongs to social media (e.g. facebook, twitter, instagram, youtube, etc.)
                    is_social_media, social_media_name = is_social_media_link(link)
                    if is_social_media:
                        link_type = social_media_name
                    else:    
                        link_type = 'other'
                new_data = {
                    'comment_link' : comment['comment_link'],
                    'post_link' : each_post['url'],
                    'link' : link,
                    'link_type' : link_type,
                    'owner_info' : owner_info,
                }
                if mero_school_post:
                    # mero school piracy data
                    piracy_data.append(new_data)
                # Data for pdf engine
                pdf_engine_data.append(new_data)
                    
            print('.', end='') # To know that the code is running
            
            # For gemini & praw Rate limits
            time.sleep(1)
    
    # For each subreddit
    print('============================================================')
    print(f"Posts crawled: {posts_crawled}   Comments crawled: {comments_crawled}")
    print('============================================================', end='\n\n')
    # Save the crawled page links to the file
    crawled_page_links.save_bloom_filter()

    # Save piracy data csv file
    save_to_csv(piracy_data, 'piracy_data.csv')

    # Save pdf engine data csv file
    save_to_csv(pdf_engine_data, 'pdf_engine_data.csv')
    