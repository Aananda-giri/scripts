import gdown
import os
import requests

def download_pdf(url, save_path):
    # Download normal pdf if size is lesss than 5MB

    # Send a HEAD request to get the file size without downloading the entire file
    response = requests.head(url)
    file_size = int(response.headers.get('Content-Length', 0))
    file_type = response.headers.get('Content-Type')
    
    if file_type != 'application/pdf':
        print(f"\n\n File type is not PDF. File type: {file_type} \n\n ")
        return False

    # # Convert 5 MB to bytes
    # max_size = 5 * 1024 * 1024  # 5 MB in bytes
    # print(f'\n file_size: {file_size / (1024**2)}')
    # if file_size > max_size:
    #     print(f"File size ({file_size} bytes) exceeds 5 MB. Download canceled.")
    #     return False
    
    # If file size is acceptable, proceed with download
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"PDF downloaded successfully to {save_path}")
        return True
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")
        return False

def is_google_drive_link(link):
  # return id of drive link

  if link.startswith('https://drive.google.com/file/d/'):
    drive_id = link.split('https://drive.google.com/file/d/')[1].split(
        '/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/folders/'):
    drive_id = link.split('https://drive.google.com/drive/folders/')[1].split(
        '/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/open?id='):
    drive_id = link.split('https://drive.google.com/open?id=')[1].split(
        '/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/0/folders/'):
    drive_id = link.split('https://drive.google.com/drive/u/0/folders/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/1/folders/'):
    drive_id = link.split('https://drive.google.com/drive/u/1/folders/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/2/folders/'):
    drive_id = link.split('https://drive.google.com/drive/u/2/folders/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/3/folders/'):
    drive_id = link.split('https://drive.google.com/drive/u/3/folders/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/0/file/d'):
    drive_id = link.split('https://drive.google.com/drive/u/0/file/d/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/1/file/d/'):
    drive_id = link.split('https://drive.google.com/drive/u/1/file/d/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/2/file/d/'):
    drive_id = link.split('https://drive.google.com/drive/u/2/file/d/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/u/3/file/d/'):
    drive_id = link.split('https://drive.google.com/drive/u/3/file/d/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/drive/mobile/folders/'):
    drive_id = link.split('https://drive.google.com/drive/mobile/folders/'
                          )[1].split('/')[0].split('?')[0]
  elif link.startswith('https://drive.google.com/folderview?id='):
    drive_id = link.split('https://drive.google.com/folderview?id=')[1].split(
        '/')[0].split('?')[0]
  else:
    # return original link
    return False, link

  return True, drive_id


def download_google_drive_file(drive_id, output_path):
    # Download google drive link
    output = gdown.download(id=drive_id, output=output_path, quiet=False)
    if output:
        print(f"File downloaded successfully to {output_path}")
        return True
    else:
        print("Failed to download the file")
        return False

if __name__ == "__main__":

    # (Google Drive pdf) Example usage
    url = "https://drive.google.com/file/1d/1CvR4EunDLNqakb9rvYuN5hR2kkMSfG7A/view"
    output_path = "of_studies.pdf"

    download_google_drive_file(url, output_path)

    # (Normal pdf) Example usage
    url = "https://abhashacharya.com.np/wp-content/uploads/2017/12/Spot-Speed-Study.pdf"
    save_path = "Spot-Speed-Study.pdf"

    download_pdf(url, save_path)