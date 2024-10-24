import csv
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def smart_wait(min_time=2, max_time=5):
    """Random wait to mimic human interaction."""
    time.sleep(random.uniform(min_time, max_time))

def get_post_content(url):
    """Fetch the content of the post using BeautifulSoup."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            post_title_tag = soup.find('h1')
            post_title = post_title_tag.get_text() if post_title_tag else "N/A"
            
            user_tag = soup.find('div', id=lambda x: x and x.startswith('postmenu_'))
            user = user_tag.get_text(strip=True) if user_tag else "N/A"
    
            full_date_tag = soup.find('td', class_='thead')
            full_date = full_date_tag.get_text(strip=True) if full_date_tag else "N/A"
            date = full_date.split(',')[0] if full_date != "N/A" else full_date
             
            post_body_tag = soup.find('td', {'class': 'alt1'})
            post_body = post_body_tag.get_text(strip=True) if post_body_tag else "N/A"
            
            title_tag = soup.find('b')
            if title_tag:
                full_title = title_tag.get_text().strip()
                cleaned_title = full_title.replace("Message Board", "").strip()
            else:
                cleaned_title = "Keyword not found"
            
            replies_section = soup.find_all('div', {'class': 'threadpost'})
            replies_data = []

            # Loop through replies,
            for reply_section in replies_section[1:]:
                reply_username = reply_section.find('div', id=lambda x: x and x.startswith('postmenu_'))
                reply_username = reply_username.get_text(strip=True) if reply_username else 'N/A'

                reply_date = reply_section.find('td', class_='thead')
                reply_date = reply_date.get_text(strip=True).split(',')[0] if reply_date else 'N/A'

                reply_comment = reply_section.find('td', {'class': 'alt1'})
                reply_comment = reply_comment.get_text(strip=True) 
                reply_comment = reply_comment.replace("Re: ", "") if reply_comment else 'N/A'

                replies_data.append({
                    'URL': url,
                    'Title': post_title,
                    'User': user,
                    'Date': date,
                    'Body': post_body,
                    'Keyword': cleaned_title,
                    'Reply Username': reply_username,
                    'Reply Date': reply_date,
                    'Reply Comment': reply_comment
                })

            return replies_data
        
        else:
            print(f"Failed to retrieve {url} with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def read_urls_from_csv(input_csv):
    """Read URLs from the input CSV file."""
    urls = []
    try:
        with open(input_csv, mode='r', encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  
            for row in reader:
                if row:  
                    urls.append(row[0]) 
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return urls

def save_extracted_data_to_csv(post_data, output_csv):
    """Save the extracted data into a new CSV file."""
    try:
        with open(output_csv, mode='w', newline='', encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["URL", "Title", "User", "Date", "Body", "Keyword", "Reply Username", "Reply Date", "Reply Comment"])
            writer.writeheader()
            for data in post_data:
                writer.writerow(data)
        print(f"Extracted data saved to {output_csv}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

def main(input_csv, output_csv):
    """Main function to orchestrate the process."""
    urls = read_urls_from_csv(input_csv)
    post_data = []
    
    for url in urls:
        smart_wait() 
        post_content = get_post_content(url)
        if post_content:
            post_data.extend(post_content) 

    if post_data:
        save_extracted_data_to_csv(post_data, output_csv)
    else:
        print("No data to save.")


input_csv_file = "cancer_post_urls.csv"
output_csv_file = "extracted_post_data.csv"


main(input_csv_file, output_csv_file)
