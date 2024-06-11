[ ] Make it async.

## Pseudocode:
while True:
    [X] Get all reddit <posts, comments> from <list> sub_reddits after <last_crawl_datetime>
    [X] if comment contains link and link belong to <list> storge_providers
        * using gemini: 
          [ ] check: function is_post_about_mero_school(post, comment): -> <Bool>
                * if it is about mero_school:
                   [ ] use drive crawler to get email, name
                * store to json :
                   [ ] <avoid redundancy of entire data>
                   [ ] url, reddit_post_link, reddit_comment_link, url_extracted, <name, email if google drive link>

    [X] save data to 'privacy_data.csv'
time.sleep(duration)

# Variable types:

# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']
sleep_duration = 12 * 60 * 60   # 12 hours