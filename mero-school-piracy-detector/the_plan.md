# pdf-engine
[ ] Crawler: crawl notes & pdfs links from reddit 'r/IOENepal'
[ ] Crawler: scrapy to detect the link belong to pdf and get title, url
[ ] Searching: include results from web pages and not only google drive
[ ] Searching: Optimize mongo serch, index <unique> url field, index <searching> file_name or title
[ ] Implement Semantic search
[ ] How to Get Google drive api key.

# Reddit Crawler
[ ] Steps to get new drive api_key and gemini api keys
[ ] Data visualization
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
* **Format**:
```
'comment_link' : <str>comment_link,
'post_link' : <str>url,
'link' : <str>link,         # link to the file shared
'link_type' : <str> <one of 'google-drive', 'google-drive-private', None>
'owner_info' : <either> [{'displayName': <str>, 'emailAddress': <str>}] <or> None
```
e.g.
```
[
    {
        'comment_link': 'https://reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/l2t0d4j/', 'post_link': 'https://www.reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/',
        'link': 'https://m1e1ga.nz/file/NPdWGaab',
        'link_type': 'other',
        'owner_info': ''
    },
    {
        'comment_link': 'https://reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/l2daq6o/', 'post_link': 'https://www.reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/',
        'link': 'https://drive.google.com/drive/folders/1tva4PlBOjHUDyJzDlnBVSP1n-UR4pWO6?usp=drive_link',
        'link_type': 'google-drive',
        'owner_info': [{'displayName': '078bme038', 'emailAddress': '078bme038@student.ioepc.edu.np'}]
    }
]
```
# Add one_drive, mega, others
storage_service_providers = ['https://drive.google.com/']
sleep_duration = 12 * 60 * 60   # 12 hours











#
praw_code: 
`for submission in subreddit.new(limit=how_many):`

main.py: 
    `reddit_posts = get_reddit_posts(subreddit=subreddit_name, datetime_before=datetime_now, datetime_after=datetime_previous, how_many=None)`


# Gemini Free quota
* https://ai.google.dev/pricing
```
Rate Limits**

15 RPM (requests per minute)

1 million TPM (tokens per minute)

1,500 RPD (requests per day)
```


# Praw Tiimeout
  even after sleeping for 1s after each request
  `prawcore.exceptions.TooManyRequests: received 429 HTTP response`



# Unsecure
csv_functions.py: eval is unsecure for data from unknown sources