import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


# Function to extract data from a single HTML file
def extract_data_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Extracting main comment details with error handling
    main_comment_id = soup.find('h1', {'data-testid': 'post-heading'})
    main_comment_id = main_comment_id.get_text(strip=True) if main_comment_id else 'N/A'

    main_comment = soup.find('div', {'class': 'post-body'})
    main_comment = main_comment.get_text(strip=True) if main_comment else 'N/A'

    main_comment_url = soup.find('link', {'rel': 'canonical'})
    main_comment_url = main_comment_url['href'] if main_comment_url else 'N/A'

    main_username = soup.find('a', {'class': 'author'})
    main_username = main_username.get_text(strip=True) if main_username else 'N/A'

    main_user_profile_url = soup.find('a', {'class': 'author'})
    main_user_profile_url = main_user_profile_url['href'] if main_user_profile_url else 'N/A'

    # Extracting additional details: gender, age, country
    gender = 'N/A'
    age = 'N/A'
    country = 'N/A'

    additional_info = soup.find('div', {'class': 'sc-923ebc0e-8 iLCUdU'})
    if additional_info:
        details = additional_info.find_all('span')
        if len(details) >= 1:
            gender = details[0].get_text(strip=True)
        if len(details) >= 2:
            age = details[1].get_text(strip=True)
        if len(details) >= 3:
            country = details[2].get_text(strip=True)

    # Extracting replies
    replies_section = soup.find_all('div', {'class': 'sc-6389dadc-0 hhIaYi'})

    replies_data = []
    for reply_section in replies_section:
        reply_username = reply_section.find('a', {'class': 'sc-6389dadc-2'})
        reply_username = reply_username.get_text(strip=True) if reply_username else 'N/A'

        reply_user_profile_url = reply_section.find('a', {'class': 'sc-6389dadc-2'})
        reply_user_profile_url = reply_user_profile_url['href'] if reply_user_profile_url else 'N/A'

        reply_date = reply_section.find('time')
        if reply_date:
            reply_date = reply_date['datetime']
            # Convert reply date to yyyy-mm-dd format
            reply_date = datetime.strptime(reply_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%Y-%m-%d')
        else:
            reply_date = 'N/A'

        reply_comment = reply_section.find_next_sibling('p')
        reply_comment = reply_comment.get_text(strip=True) if reply_comment else 'N/A'

        replies_data.append({
            'Main Comment ID': main_comment_id,
            'Main Comment': main_comment,
            'Main Comment URL': main_comment_url,
            'Main Username': main_username,
            'Main User Profile URL': main_user_profile_url,
            'Gender': gender,
            'Age': age,
            'Country': country,
            'Reply Username': reply_username,
            'Reply User Profile URL': reply_user_profile_url,
            'Reply Date': reply_date,
            'Reply Comment': reply_comment
        })

    return replies_data


# Function to read all .html files from a directory and save the extracted data into a CSV file
def process_directory(directory_path, output_csv_file):
    all_data = []

    # Loop through all .html files in the directory
    for file_name in os.listdir(directory_path):
        if file_name.endswith('.html'):
            file_path = os.path.join(directory_path, file_name)
            all_data.extend(extract_data_from_html(file_path))

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(all_data)

    # Save the data to a CSV file, appending if the file already exists
    df.to_csv(output_csv_file, index=False, mode='a', header=not os.path.exists(output_csv_file))


# Example usage:
directory_path = 'dace'  # Replace with the path to your directory
output_csv_file = 'user_data1.csv'  # Output CSV file name

# Process the directory and extract data
process_directory(directory_path, output_csv_file)
