import csv
def save_to_csv(piracy_data, csv_file = 'piracy_data.csv'):
    # Define the CSV column names
    fieldnames = ['comment_link', 'post_link', 'link', 'link_type', 'owner_info']

    # Writing to the CSV file
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write the data
        for data in piracy_data:
            writer.writerow(data)

    print('============================================================')
    print(f"CSV Writer: Piracy data has been saved to {csv_file}")
    print('============================================================', end='\n\n')
    print(f"")


def read_csv(csv_file='piracy_data.csv', how_many=10):
    # read csv file/
    data=[]
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for _ in range(how_many):
            try:
                data.append(next(reader))
            except StopIteration:
                break
        # data=[row for row in reader]
    return data

def get_drive_links(csv_file='piracy_data.csv'):
    # read csv file/
    data=[]
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['link_type'] == 'google-drive':
                data.append({'link':row['link'], 'owner_info':eval(row['owner_info'])[0]['emailAddress']})
            elif row['link_type'] != None:
                data.append({'link':row['link']})
    return data


# a=get_drive_links()
# len(a)

if __name__=="__main__":
    # Example data to save to csv
    # from csv_functions import save_to_csv, read_csv
    # data = [
    #     {
    #         'comment_link': 'https://reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/l2t0d4j/', 'post_link': 'https://www.reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/',
    #         'link': 'https://m1e1ga.nz/file/NPdWGaab',
    #         'link_type': 'other',
    #         'owner_info': ''
    #     },
    #     {
    #         'comment_link': 'https://reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/l2daq6o/', 'post_link': 'https://www.reddit.com/r/IOENepal/comments/1cizbg3/mero_school_ko_videos_haru_bhako_jati_share_garum/',
    #         'link': 'https://drive.google.com/drive/folders/1tva4PlBOjHUDyJzDlnBVSP1n-UR4pWO6?usp=drive_link',
    #         'link_type': 'google-drive',
    #         'owner_info': "[{'displayName': '078bme038', 'emailAddress': '078bme038@student.ioepc.edu.np'}]"
    #     }
    # ]
    # save_to_csv(data, 'test.csv')

    # # Reading the data
    # print(f'reading data: {read_csv('test.csv')}')

    # drive_links
    print(get_drive_links())
