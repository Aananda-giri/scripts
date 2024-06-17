import csv
from praw_code import sub_exists, get_reddit_posts
from gemini_response import is_mero_school_related_post
from drive_crawler import get_owner_info
from bloom import get_bloom_thread

# Bloom Filter to store crawled page links
crawled_page_links = get_bloom_thread()

# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']

# sleep duration:12 hours; after each crawl operation
sleep_duration = 12 * 60 * 60   # 12 hours

# Subreddits to crawl
subreddit_names = ['IOENepal']

datetime_now = datetime.datetime.now() 
# previous crawl time
datetime_previous = datetime_now - datetime.timedelta(seconds=sleep_duration)

piracy_data = []

for subreddit_name in subreddit_names:
    reddit_posts = get_reddit_posts(subreddit=subreddit_name, datetime_before=datetime_now, datetime_after=datetime_previous, how_many=None)
    for each_post in reddit_posts:
        if each_post['url'] not in crawled_page_links:
            # Save crwaled page link using bloom filter
            crawled_page_links.add(each_post['url'])
        else:
            # Skip subreddit if page is already crawled
            # Since subreddits are fetched using 'new' filter, we can use `break` instead of `continue`
            break
        
        for comment in each_post['comments']:
            # check if post is about mero-school
            if is_post_about_mero_school(post['title'] + '\n\n' + comment['body']):
                for link in comment['links_contained']:
                    # returns owner info if link is google drive link so no need to check if it is google drive link
                    owner_info = get_owner_info(link)
                    if owner_info:
                        piracy_data.append({
                            'comment_link' : comment['comment_link'],
                            'post_link' : each_post['url'],
                            'link' : link,
                            'link_type' : 'google-drive',
                            'owner_info' : [{'displayName': '078bme038', 'emailAddress': '078bme038@student.ioepc.edu.np'}],
                        })
                    else:
                        piracy_data.append({
                            'comment_link': comment['comment_link'],
                            'post_link':each_post['url'],
                            'link': link,
                            'link_type':'other',
                            'owner_info':None
                        })

# Save privacy_data to csv file
csv_file = 'piracy_data.csv'

# Define the CSV column names
fieldnames = ['comment_link', 'post_link', 'link', 'link_type', 'user_email', 'user_name']

# Writing to the CSV file
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    # Write the header
    writer.writeheader()
    
    # Write the data
    for data in piracy_data:
        writer.writerow(data)

print(f"Piracy data has been saved to {csv_file}")