from drive_functions import DriveFunctions
import json
import os
import sys

def get_owner_info(link):
    '''
    input: drive link.
    return: user info

    e.g.
    # input
    link = "https://drive.google.com/drive/mobile/folders/1jeQcQA0jdzvLCz-cTTR3LVioVO5bqPh9?usp=drive_link&pli=1"

    # output:
    owner_info = [{'displayName': '078bme038', 'emailAddress': '078bme038@student.ioepc.edu.np'}]
    '''
    try:
        owner_data = []
        is_drive_id, drive_id = DriveFunctions.is_google_drive_link(link)
        if is_drive_id and drive_id:
            folders_to_crawl = [drive.CreateFile({'id': drive_id})]
            if folders_to_crawl:
                folder = folders_to_crawl[0]
                try:
                    folder.FetchMetadata()
                except Exception as ex:
                    err = {'Exception': str(ex), 'link': link, 'note': 'folder.FetchMetadata()'}
                    print(err)
                    # save_to_json(new_data = err, filename = 'exceptions.json')
                for owner in folder['owners']:
                    owner_data.append({
                        'displayName': owner['displayName'],
                        'emailAddress': owner['emailAddress']
                        })
                return owner_data
    except Exception as ex:
        print(ex)

if __name__=="__main__":
    # Example: get owner of test link
    link='https://drive.google.com/drive/mobile/folders/1jeQcQA0jdzvLCz-cTTR3LVioVO5bqPh9?usp=drive_link&pli=1'
    drive = DriveFunctions.login()
    print(get_owner_info(link))
