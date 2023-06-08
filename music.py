import asyncio
import unicodedata
import yt_dlp
import boto3
import os, random, string

output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
loop = asyncio.get_event_loop()
print(output_directory)


class AudioYTDLP:
    def __init__(self) -> None:
        '''
        import asyncio
        loop = asyncio.get_event_loop()
        a=loop.run_until_complete(MusicOperations.upload_to_s3('/home/ec2-user/downloads', True))
        '''
        pass

    @staticmethod
    async def download_one(link, part_of_playlist=False, output_directory = output_directory):
        print(f'\n\n DownloadOne: \n\n')
        with yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',                         # Ensure the best audio format is chosen
            'ignoreerrors':True,                                # Ignore errors
            'extract_audio': True,                              # Only keep the audio
            # 'outtmpl': output_directory + '/%(title)s.mp3'
            'outtmpl': output_directory + '/%(title)s.%(ext)s', # download location
            'yesplaylist': False,                         # True/False: download from playlist
            'verbose': False,                # print more info
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp3',
                #  'preferredquality': '192',
            }]
        }) as video:
            if link.startswith("http"):
                    # If input is a URL, download the video from the URL
                    video_url = link
            else:
                    # If input is a song name, search for the song and download the first result
                    search_results = video.extract_info(f"ytsearch:{link}", download=False)
                    video_url = search_results['entries'][0]['webpage_url']
            # if not yesplaylist:
            # remove playlist parameters
            video_url = video_url.split('&list')[0]
            info_dict = video.extract_info(video_url, download = True)
            # info_dict = await loop.run_in_executor(None, video.extract_info, video_url, True)
            # print(f'\n\n info_dict: {info_dict}')
            
            video_title = info_dict['title']
            print(video_title)
            video.download(video_url)
            # await loop.run_in_executor(None, video.download, video_url)
            print("Successfully Downloaded")
        
        song_path = output_directory + info_dict['title'] + '.mp3'
        normalized_listdirs = [output_directory + unicodedata.normalize('NFKC', file) for file in os.listdir(output_directory)]
        if part_of_playlist:
            print('returning')
            return output_directory +'/' + os.listdir(output_directory)[normalized_listdirs.index(song_path)]

        # For playlists
        # -------------------
        # move files to folder named after playlist
        # if 'playlist_count' in info_dict:
        
        # For single files
        # -------------------
        # normalize because `os.listdir()` gives this character : `｜` in python instead of this character:`|`
        # print("2")
        
        # print("3")
        
        # print("4")
        full_download_path = output_directory +'/' + os.listdir(output_directory)[normalized_listdirs.index(song_path)]
        # print("5")
        url = info_dict['webpage_url']
        # print("6")
        thumbnail = info_dict['thumbnail']
        # print("7")
        title = info_dict['title']
        # print("8")
        description = info_dict['description']
        # print("9")
        duration = info_dict['duration']
        return url, thumbnail, title, description, duration, full_download_path
    
    @staticmethod
    async def download_playlist(link):
        # For playlists
        # -------------------
        print(f'\n\n --------------- Download Playlist --------------- \n\n')
        def get_playlist_info(playlist_url):
            ydl_opts = {
                'ignoreerrors': True,  # Ignore any download errors
                'extract_flat': True,  # Extract only playlist entries, not individual videos
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)

            return playlist_info

        # playlist_url = "https://www.youtube.com/playlist?list=PLg2ADfnejD6H4weUDZWPyfXLVbBZIgBpf"
        playlist_info = get_playlist_info(link)
        
        if 'entries' in playlist_info:
            print('\n\n entries ')
            for video in playlist_info['entries']:
                
                video_url = video['url']
                
                # info_dict = video.extract_info(video_url, download = False)
                # video_titlqqe = info_dict['title']
                # print(video_title)
                file = await AudioYTDLP.download_one(video_url, True, os.path.join(output_directory, playlist_info['title']))
                print(f'returned : {file} exists:{os.path.exists(file)}')
                yield file
                # print(f'yielding : {file}')
        else:
            print('\n\n no entries ')
            file = await AudioYTDLP.download_one(video_url, True)
            yield file[-1]
    

    @staticmethod
    async def upload_to_s3(path, is_folder=False):
        def random_string(string_length=6):
            """Generate a random string of fixed length """
            letters = string.ascii_lowercase + string.digits + string.ascii_uppercase
            return ''.join(random.choice(letters) for i in range(string_length))
        

        # Function to upload a file to S3 and return the link
        async def upload_file_to_s3(file_path, bucket_name, object_key):
            s3_client = boto3.client('s3')
            try:
                s3_client.upload_file(file_path, bucket_name, object_key)
                # object_url = f"https://{bucket}.s3.{region_name}.amazonaws.com/{object_key}"
                object_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=172800
                )
                return object_url
            except Exception as e:
                print(f"Error uploading file '{file_path}' to S3: {e}")
                return None

        async def upload_folder_to_s3(folder_path, bucket_name):
            # Upload folder contents to S3
            uploaded_files = []
            folder_path = '/home/ec2-user/saneora/cogs/downloads'
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    print(file_path)
                    object_key = os.path.relpath(file_path, folder_path)
                    object_url = upload_file_to_s3(file_path, bucket_name, object_key)
                    if object_url:
                        uploaded_files.append(object_url)

            # Print the list of uploaded file links
            # for file_url in uploaded_files:
            #     print(file_url)
            return uploaded_files

        async def get_file_url(bucket_name, object_name, expiration=172800):
            s3_client = boto3.client('s3')
            try:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_name},
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                print(f"Error generating file URL: {e}")
                return None

        # S3 bucket details
        bucket_name = 'discord-bot'
        region_name = 'ap-southeast-1'
        # object_name = random_string()
        object_name = path.split('/')[-1]
        if is_folder:
            url = await upload_folder_to_s3(path, bucket_name)
        else:
            url = await upload_file_to_s3(path, bucket_name, object_name)
        return url
