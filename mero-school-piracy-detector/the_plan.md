[ ] Steps to get new drive api_key and gemini api keys

[ ] <One time operation> Crawl all posts since inception of IOENepal
[ ] Test if code is working for custom link: https://reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/#chat-image#lightbox
[ ] Test if code is working for past 24 hours
[ ] Make it async. + Mongo Db

## Pseudocode:
while True:
    for post in new_posts:
        [X] if post_is_already_crawled:
            break
        [X] Get all reddit <posts, comments> from <list> sub_reddits after <last_crawl_datetime>
        [X] if comment contains link and link belong to <list> storge_providers
            * using gemini: 
            [X] check: function is_post_about_mero_school(post, comment): -> <Bool>
                    * if it is about mero_school:
                    [X] use drive crawler to get email, name
                    * store to json :
                    [ ] <avoid redundancy of entire data>
                    [X] url, reddit_post_link, reddit_comment_link, url_extracted, <name, email if google drive link>
        [X] save data to 'privacy_data.csv'
    time.sleep(sleep_duration)

[ ] Log Errors

# Variable types:

* ## piracy_data: <list>
[
    {
        'comment_link' : comment['comment_link'],
        'post_link' : each_post['url'],
        'link' : link,
        'link_type' : 'google-drive',
        'owner_info' : [{'displayName': '078bme038', 'emailAddress': '078bme038@student.ioepc.edu.np'}],
    },
    {
        'comment_link': comment['comment_link'],
        'post_link':each_post['url'],
        'link': link,
        'link_type':'other',
        'owner_info':None
    }
]
# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']
sleep_duration = 12 * 60 * 60   # 12 hours