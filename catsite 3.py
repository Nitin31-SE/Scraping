from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import csv
import json
import random
import time

# Set up Selenium with Chrome
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  # Disable GPU rendering for headless mode
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--window-size=1920x1080")  # For running in certain Linux environments
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Function to clean the keyword row and format for the URL
def format_keywords(keywords):
    keywords_list = keywords.strip().split(" ")
    query = "+".join([f'{k}' for k in keywords_list])
    return query

# Function to fetch post details
def fetch_post_details(driver, post_url):
    try:
        driver.get(post_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "bbWrapper")))
        
        # Extracting post details
        post_id = post_url.split('/')[-1].split('-')[-1]
        username = driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="name"]').get_attribute('content')
        post_date = driver.find_element(By.CSS_SELECTOR, 'time.u-dt').get_attribute('datetime')
        post_content = driver.find_element(By.CLASS_NAME, 'bbWrapper').text

        # Return the extracted details
        return (post_id, username, post_date, post_content)

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        print(f"Error fetching post details: {e}")
        return None

# Function to scrape data from the search result page and fetch details from each post
def scrape_data(driver, query, start_date="2012-06-01", end_date="2024-09-20"):
    # Open the search page with specific filters
    search_url = f'https://www.paw-talk.net/search/?q={query}&t=post&c[child_nodes]=1&c[newer_than]={start_date}&c[older_than]={end_date}&o=relevance'
    driver.get(search_url)
    
    # Wait for search results to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-dmt-json]")))

    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = []

    # Collect all post elements from the search result
    post_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-dmt-json]")

    for post_div in post_divs:
        try:
            # Extract the post link from the div
            post_link = post_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
            print(f"Found post: {post_link}")
            
            # Fetch details from the post page
            post_details = fetch_post_details(driver, post_link)

            if post_details:
                post_id, username, post_date, post_content = post_details
                posts.append({
                    'Post ID': post_id,
                    'Username': username,
                    'Post Date': post_date,
                    'Post Content': post_content,
                    'Post URL': post_link
                })

            # Introduce a random wait to avoid detection
            time.sleep(random.uniform(3, 6))

        except NoSuchElementException as e:
            print(f"Error extracting post link: {e}")

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
                all_results.append([
                    keywords, 
                    post['Post ID'], 
                    post['Username'], 
                    post['Post Date'], 
                    post['Post Content'], 
                    post['Post URL']
                ])
        else:
            print(f"No posts found for {keywords}")

    # Save the result to CSV
    if all_results:
        with open('scraped_results.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Keywords', 'Post ID', 'Username', 'Post Date', 'Post Content', 'Post URL'])
            writer.writerows(all_results) 

        print(f"Scraping completed. {len(all_results)} results saved to scraped_results.csv")
    else:
        print("No results found for any of the keywords.")

    driver.quit()

if __name__ == "__main__":
    main()
