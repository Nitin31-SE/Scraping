import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Function to extract data from a URL
def extract_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting main comment details with error handling
        main_comment_id = soup.find('h1', {'class': 'thread-title'})
        main_comment_id = main_comment_id.get_text(strip=True) if main_comment_id else 'N/A'

        main_comment = soup.find('div', {'class': 'text-first-commentaire'})
        main_comment = main_comment.get_text(strip=True) if main_comment else 'N/A'

        main_comment_url = soup.find('link', {'rel': 'canonical'})
        main_comment_url = main_comment_url['href'] if main_comment_url else 'N/A'  # Use the provided URL

        main_username = soup.find('div', {'class': 'contribs-meta'})
        main_username = main_username.get_text(strip=True) if main_username else 'N/A'

        main_comment_date = soup.find('div', {'class': 'date'})
        if main_comment_date:
                # Extract raw text and clean it
                raw_date_text = main_comment_date.get_text(strip=True).replace("Edited on", "").split("at")[0].strip()

                try:
                    # Parse the date and convert it to yyyy/mm/dd format
                    extracted_main_date = datetime.strptime(raw_date_text, "%m/%d/%Y").strftime("%Y/%m/%d")
                    print("Extracted Date:", extracted_main_date)
                except ValueError as e:
                    print(f"Error parsing date: {e}")

        # Extracting replies
        replies_section = soup.find_all('div', {'class': 'all-comments'})

        replies_data = []
        for reply_section in replies_section:
            reply_username = reply_section.find('p', {'class': 'name'})
            reply_username = reply_username.get_text(strip=True) if reply_username else 'N/A'

            reply_user_profile_url = reply_section.find('a', {'class': 'sc-6389dadc-2'})
            reply_user_profile_url = reply_user_profile_url['href'] if reply_user_profile_url else 'N/A'

            date_div = soup.find('div', class_='date')
            if date_div:
                # Extract raw text and clean it
                raw_date_text = date_div.get_text(strip=True).replace("Edited on", "").split("at")[0].strip()

                try:
                    # Parse the date and convert it to yyyy/mm/dd format
                    extracted_date = datetime.strptime(raw_date_text, "%m/%d/%Y").strftime("%Y/%m/%d")
                    print("Extracted Date:", extracted_date)
                except ValueError as e:
                    print(f"Error parsing date: {e}")
            else:
                print("Date element not found.")

            reply_comment = reply_section.find('div', {'class': 'message'})
            reply_comment = reply_comment.get_text(strip=True) if reply_comment else 'N/A'

            replies_data.append({
                'Main Comment ID': main_comment_id,
                'Main Comment': main_comment,
                'Main Comment URL': main_comment_url,
                'Main Username': main_username,
                'Main Comment Date': extracted_main_date,
                'Reply Username': reply_username,
                'Reply User Profile URL': reply_user_profile_url,
                'Reply Date': extracted_date,
                'Reply Comment': reply_comment
            })

        return replies_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

# Function to read URLs from a CSV and save the extracted data into another CSV file
def process_urls(input_csv_file, output_csv_file):
    all_data = []

    # Read the CSV containing URLs
    try:
        input_data = pd.read_csv(input_csv_file)
    except Exception as e:
        print(f"Error reading input CSV file: {e}")
        return

    # Ensure the CSV contains a column with URLs
    if 'Post URL' not in input_data.columns:
        print("The input CSV must contain a 'Post URL' column with URLs to process.")
        return

    # Loop through the URLs in the CSV
    for url in input_data['Post URL']:
        all_data.extend(extract_data_from_url(url))

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(all_data)

    # Save the data to a CSV file, appending if the file already exists
    if not df.empty:
        df.to_csv(output_csv_file, index=False, mode='a', header=not os.path.exists(output_csv_file))
        print(f"Data saved to {output_csv_file}.")
    else:
        print("No data extracted. Output CSV file not created.")

# Example usage:
input_csv_file = 'asthma_post_urls.csv'  # Input CSV file containing URLs
output_csv_file = 'caternity.csv'  # Output CSV file name

# Process the CSV and extract data
process_urls(input_csv_file, output_csv_file)
