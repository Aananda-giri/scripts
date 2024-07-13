import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from dotenv import load_dotenv
load_dotenv()
import sys
import re

class DriveFunctions:
    @staticmethod
    def login_with_service_account(credentials=None):
        """
        Google Drive service with a service account.
        note: for the service account to work, you need to share the folder or
        files with the service account email.

        :return: google auth
        """
        # Define the settings dict to use a service account
        # We also can use all options available for the settings dict like
        # oauth_scope,save_credentials,etc.
        if not credentials:
            print('\n\n -----------not cred')
        settings = {
                    "client_config_backend": "service",
                    "service_config": {
                        "client_json_file_path": "son-of-anton-368302-5d69bab81ff0.json" if not credentials else None,
                        "client_json_dict": credentials,
                    }
                }
        # Create instance of GoogleAuth
        gauth = GoogleAuth(settings=settings)
        # Authenticate
        gauth.ServiceAuth()
        return gauth

    # -----------------
    # Login
    # -----------------
    @staticmethod
    def login():
        
        import sys

        if 'google.colab' in sys.modules:
            print('Code is running in Google Colab.')
            
            from google.colab import userdata
            GOOGLE_DRIVE_CREDENTIALS = userdata.get('GOOGLE_DRIVE_CREDENTIALS')
            drive = GoogleDrive(DriveFunctions.login_with_service_account(json.loads(GOOGLE_DRIVE_CREDENTIALS)))
        else:
            # print('Code is not running in Google Colab.')
            
            GOOGLE_DRIVE_CREDENTIALS = json.loads(os.environ.get('GOOGLE_DRIVE_CREDENTIALS'))
            # print(f'\n creds: {GOOGLE_DRIVE_CREDENTIALS} \n')
            drive = GoogleDrive(DriveFunctions.login_with_service_account(GOOGLE_DRIVE_CREDENTIALS))
        return drive

    # -----------------
    # listing files
    # -----------------
    # Auto-iterate through all files that matches this query
    @staticmethod
    def list_files(folder_id=None):
        drive = DriveFunctions.login()
        if folder_id is None:
            # search in root folder
            file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        else:
            # search in a specific folder
            file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
        for file1 in file_list:
            print('title: %s, id: %s' % (file1['title'], file1['id']))
    
    @staticmethod
    def is_google_drive_link(link):
        # return id of drive link

        if link.startswith('https://drive.google.com/file/d/'):
            drive_id = link.split('https://drive.google.com/file/d/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/folders/'):
            drive_id = link.split('https://drive.google.com/drive/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/open?id='):
            drive_id = link.split('https://drive.google.com/open?id=')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/0/folders/'):
            drive_id = link.split('https://drive.google.com/drive/u/0/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/1/folders/'):
            drive_id = link.split('https://drive.google.com/drive/u/1/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/2/folders/'):
            drive_id = link.split('https://drive.google.com/drive/u/2/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/3/folders/'):
            drive_id = link.split('https://drive.google.com/drive/u/3/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/0/file/d'):
            drive_id = link.split('https://drive.google.com/drive/u/0/file/d/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/1/file/d/'):
            drive_id = link.split('https://drive.google.com/drive/u/1/file/d/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/2/file/d/'):
            drive_id = link.split('https://drive.google.com/drive/u/2/file/d/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/u/3/file/d/'):
            drive_id = link.split('https://drive.google.com/drive/u/3/file/d/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/drive/mobile/folders/'):
            drive_id = link.split('https://drive.google.com/drive/mobile/folders/')[1].split('/')[0].split('?')[0]
        elif link.startswith('https://drive.google.com/folderview?id='):
            drive_id = link.split('https://drive.google.com/folderview?id=')[1].split('/')[0].split('?')[0]
        else:
            # return original link
            return False, link
        
        return True, drive_id

# import re
def is_social_media_link(link):
  social_media_patterns = {
      'facebook': r"facebook\.com",
      'instagram': r"instagram\.com",
      'twitter': r"twitter\.com",
      'x': r"x\.com",
      'tiktok': r"tiktok\.com",
      'linkedin': r"linkedin\.com",
      'pinterest': r"pinterest\.com",
      'youtube': r"youtube\.com|youtu\.be",
      'reddit': r"reddit\.com",
      'snapchat': r"snapchat\.com",
      'quora': r"quora\.com",
      'tumblr': r"tumblr\.com",
      'flickr': r"flickr\.com",
      'medium': r"medium\.com",
      'vimeo': r"vimeo\.com",
      'vine': r"vine\.co",
      'periscope': r"periscope\.tv",
      'meetup': r"meetup\.com",
      'mix': r"mix\.com",
      'soundcloud': r"soundcloud\.com",
      'behance': r"behance\.net",
      'dribbble': r"dribbble\.com",
      'vk': r"vk\.com",
      'weibo': r"weibo\.com",
      'ok': r"ok\.ru",
      'deviantart': r"deviantart\.com",
      'slack': r"slack\.com",
      'telegram': r"t\.me|telegram\.me",
      'whatsapp': r"whatsapp\.com",
      'line': r"line\.me",
      'wechat': r"wechat\.com",
      'kik': r"kik\.me",
      'discord': r"discord\.gg",
      'skype': r"skype\.com",
      'twitch': r"twitch\.tv",
      'myspace': r"myspace\.com",
      'badoo': r"badoo\.com",
      'tagged': r"tagged\.com",
      'meetme': r"meetme\.com",
      'xing': r"xing\.com",
      'renren': r"renren\.com",
      'skyrock': r"skyrock\.com",
      'livejournal': r"livejournal\.com",
      'fotolog': r"fotolog\.com",
      'foursquare': r"foursquare\.com",
      'cyworld': r"cyworld\.com",
      'gaiaonline': r"gaiaonline\.com",
      'blackplanet': r"blackplanet\.com",
      'care2': r"care2\.com",
      'cafemom': r"cafemom\.com",
      'nextdoor': r"nextdoor\.com",
      'kiwibox': r"kiwibox\.com",
      'cellufun': r"cellufun\.com",
      'tinder': r"tinder\.com",
      'bumble': r"bumble\.com",
      'hinge': r"hinge\.co",
      'match': r"match\.com",
      'okcupid': r"okcupid\.com",
      'zoosk': r"zoosk\.com",
      'plentyoffish': r"pof\.com",
      'eharmony': r"eharmony\.com",
      'coffee_meets_bagel': r"coffeemeetsbagel\.com",
      'her': r"weareher\.com",
      'grindr': r"grindr\.com",
      'happn': r"happn\.com",
      'hily': r"hily\.com",
      'huggle': r"huggle\.com",
      'jdate': r"jdate\.com",
      'lovoo': r"lovoo\.com",
      'meetmindful': r"meetmindful\.com",
      'once': r"once\.com",
      'raya': r"raya\.app",
      'ship': r"getshipped\.com",
      'silversingles': r"silversingles\.com",
      'tastebuds': r"tastebuds\.fm",
      'the_league': r"theleague\.com",
      'tudder': r"tudder\.com",
      'twoo': r"twoo\.com",
  }

  for social_media, pattern in social_media_patterns.items():
    if (re.search(r'https://www\.' + pattern, link, flags=re.IGNORECASE)) or (
        (re.search(r'https://www\.m\.' + pattern, link, flags=re.IGNORECASE))):
      return True, social_media

  return False, None

if __name__ == '__main__':
    # Example usage
    links = [
        {'url':'https://www.google.com', 'text':'hello world'},
        {'url':'https://www.google.com', 'text':'hello there'},
        {'url':'https://www.google.com', 'text':'hello there'},

        {'url':'https://www.google1.com', 'text':'hello there'},
        # Add more links as needed
    ]
