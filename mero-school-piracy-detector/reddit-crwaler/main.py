import csv
from praw_code import sub_exists, get_reddit_posts
from gemini_functions import is_post_about_mero_school
from drive_functions import is_this_drive_link, process_drive_link


# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']

# sleep duration after each crawl
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
        for comment in each_post['comments']:
            # check if post is about mero-school
            if is_post_about_mero_school(post['title'], comment['body']):
                for link in comment['links_contained']:
                    if is_this_drive_link(link):
                        user_name, email = process_drive_link(link)

                        piracy_data.append({
                            'comment_link' : comment['comment_link'],
                            'post_link' : each_post['url'],
                            'link' : link,
                            'link_type' : 'google-drive',
                            'user_email' : user_email,
                            'user_name' : user_name
                        })
                    else:
                        piracy_data.append({
                            'comment_link': comment['comment_link'],
                            'post_link':each_post['url']
                            'link': link,
                            'link_type':'other',
                            'user_email': None,
                            'user_name': None
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