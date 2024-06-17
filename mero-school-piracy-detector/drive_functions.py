import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from dotenv import load_dotenv
load_dotenv()
import sys

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
            print('Code is not running in Google Colab.')
            
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

if __name__ == '__main__':
    # Example usage
    links = [
        {'url':'https://www.google.com', 'text':'hello world'},
        {'url':'https://www.google.com', 'text':'hello there'},
        {'url':'https://www.google.com', 'text':'hello there'},

        {'url':'https://www.google1.com', 'text':'hello there'},
        # Add more links as needed
    ]
