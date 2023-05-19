'''
# ----------------------------
# Merge two paths
# ----------------------------
- inputs: source, destination
- Functions:
    i. iterate through each item in source
    ii. if item is file
            if file exist in destination
                * replace in destination if source_file_size is greater than destination
                * skip otherwise
            if file doesnt exist in destination : copy from source to destination
    iii. if item is folder:
            if folder_name doesn't exist in destination:
                create folder at destination 
                repeat from step i.
            item exist in destination but  is file:
                * change destination_path to destination_path+'_folder'
                * repeat from step i.
            if folder exist in destination:
                * repeat from step i.
'''

import os
import shutil


def merge(source, destination):
    for path in os.listdir(source):
        source_path = os.path.join(source, path)
        destination_path = os.path.join(destination,path)
        
        if not os.path.isdir(source_path):
            # path is file: copy from source to destination
            
            if os.path.exists(destination_path):
                print(source_path, destination_path)
                # file exist in destination
                if os.path.getsize(source_path) > os.path.getsize(destination_path):
                    # source file is larger than destination file
                    os.remove(destination_path)
                else:
                    continue    # destination file path has larger size than source file :: skip
            shutil.copy(source_path, destination_path)
        else:
            # path is folder: 
                if not os.path.exists(destination_path):
                    # destination folder does not exist
                    os.mkdir(destination_path)
                elif not os.path.isdir(destination_path):
                    # destination exists but is file not folder
                    destination_path = os.path.join(destination, path+'_folder')
                    os.mkdir(destination_path)
                merge(source_path, destination_path)

if __name__ == "__main__":
    merge('folder1', 'folder2')

# def merge_folders(source_folder, destination_folder):
#     for root, dirs, files in os.walk(source_folder):
#         relative_path = os.path.relpath(root, source_folder)
#         destination_path = os.path.join(destination_folder, relative_path)
#         os.mkdirs(destination_path, exist_ok=True)
        
#         for file in files:
#             source_file = os.path.join(root, file)
#             destination_file = os.path.join(destination_path, file)
#             shutil.copy2(source_file, destination_file)

#     print("Folders merged successfully!")


# if __name__ == "__main__":
#     source_folder = input("Enter the source folder path: ")
#     destination_folder = input("Enter the destination folder path: ")
    
#     merge_folders(source_folder, destination_folder)
