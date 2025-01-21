from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import csv
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
 
# Set up Selenium with Chrome
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  # Disable GPU rendering for headless mode
    chrome_options.add_argument("--ignore-certificate-errors") 
    chrome_options.add_argument("--window-size=1920x1080")  # For running in certain Linux environments
 
    # Set path to chromedriver
    chrome_driver_path = "C:/WebDrivers/chromedriver.exe"  # Change this to the actual path of your chromedriver
 
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver
 
# Function to clean the keyword row and format for the URL
def format_keywords(keywords):
    keywords_list = keywords.strip().split(" ")
    query = "+".join([f'{k}' for k in keywords_list])
    return query
 
# Function to scrape individual post data
def scrape_post_data(driver, post_url):
    # Navigate to the individual post page
    driver.get(post_url)
    time.sleep(2)  # Give the page some time to load
 
    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
 
    try:
        post_id = post_url.rstrip('/').split('/')[-1].split('-')[-1]
        post_container = soup.find('div', id=f'js-post-{post_id}')        
        
        if post_container:
            post_content = post_container.find('div', class_='bbWrapper').get_text(strip=True)
        else:
                print(f"No post found on page: {post_url}")

        return post_content
    
    except Exception as e:
            print(f"Error extracting post details: {e}")
    
    return None
 
# Function to scrape data from the search result page
def scrape_data(driver, query, start_date="2012-06-01", end_date="2024-09-20"):
    # Open the search page with specific filters
    driver.get(f'https://www.paw-talk.net/search/?q={query}&t=post&c[child_nodes]=1&c[newer_than]={start_date}&c[older_than]={end_date}&o=relevance')
 
    # Scroll the element into view using JavaScript
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[qid="search-button"]')
    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
 
    # Click the button to start search
    submit_button.click()
 
    time.sleep(3)  # Allow time for the page to fully load
 
    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = []
 
    # Collect all post elements from the search result
    for item in soup.find_all('li', class_='block-row'):
        title_element = item.find('h3', class_ = 'contentRow-title')
        target_user = item.find('span', class_='overflow-wrap').find('a')
        date = item.find('time')
        
        if title_element:
            url = title_element.find('a')['href']
            full_url = f"https://www.paw-talk.net{url}"
            
            post_title = title_element.get_text(strip=True) 
 
            target_user = target_user.get_text(strip=True)

            if date:
                date = date['datetime']
                date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").strftime('%Y-%m-%d')

        post_divs = soup.find_all('div', {'data-dmt-json': True})        
        for post_div in post_divs:
            try:
                post_link = post_div.find('a')['href']
                full_post_url = f"https://www.paw-talk.net{post_link}"
                scrape_post_data(full_post_url)
            
            except (KeyError, TypeError, json.JSONDecodeError):
                # Handle any JSON parsing errors or missing attributes
                continue
            
        # Call the scrape_post_data function to get details from each post page
        text = scrape_post_data(driver, full_post_url)
            
        posts.append((post_title, full_url, target_user, date, text))  
 
    return posts
 
# Main function to read keywords, scrape the data, and save results
def main():
    driver = setup_selenium()  # Initialize ChromeDriver
    
    # Load the keywords CSV file
    keywords_df = pd.read_csv('keywords 1.csv', header=None)
 
    # List to store all results
    all_results = []
 
    # Iterate over each keyword in the CSV
    for index, row in keywords_df.iterrows():
        keywords = row[0]  
        query = format_keywords(keywords)  
        print(f"Searching for: {query}")
 
        # Scrape the data for this keyword query
        posts = scrape_data(driver, query)
        if posts:
            print(f"Found {len(posts)} posts for {keywords}")
            for post in posts:
                all_results.append([keywords, post[0], post[1], post[2], post[3], post[4]])
        else:
            print(f"No posts found for {keywords}")
 
    # Save the result to CSV
    if all_results:
        with open('scraped_results.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Keywords', 'Post Title', 'Post URL', 'User', 'Date', 'comment'])
            writer.writerows(all_results) 
 
        print(f"Scraping completed. {len(all_results)} results saved to scraped_results.csv")
    else:
        print("No results found for any of the keywords.")
 
    driver.quit()
 
if __name__ == "__main__":
    main()
 