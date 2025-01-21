import os
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import pandas as pd  
from bs4 import BeautifulSoup


chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

# Initialize Chrome driver
driver = webdriver.Chrome(options=chrome_options)


def smart_wait(min_time=2, max_time=5):
    time.sleep(random.uniform(min_time, max_time))

# WebMD login
def login():
    pass  

# Step 1: Search for the drug
def search_drug(query):
    """Search for a specific drug and get the reviews page URL."""
    try:
        driver.get(f"https://www.webmd.com/drugs/2/search?type=drugs&query={query}")
        smart_wait()
        # Check if the drug exists
        search_results = driver.find_elements(By.CSS_SELECTOR, '.drugs-exact-search-list a')
        if not search_results:
            print(f"No results found for {query}")
            return None

        # Navigate to the drug details page
        drug_link = search_results[0].get_attribute('href')
        driver.get(drug_link)
        smart_wait()

        # Locate the reviews tab
        reviews_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Reviews')]")
        reviews_url = reviews_tab.get_attribute('href')
        return reviews_url

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error during search: {e}")
        return None

# Step 2: Collect all review post URLs from pagination
def collect_review_urls(reviews_url, since_date):
    """Collect all review URLs from the reviews page."""
    page_number = 1
    review_urls = []

    try:
        while True:
            driver.get(f"{reviews_url}&pagenumber={page_number}")
            smart_wait()

            # Collect all reviews
            reviews = driver.find_elements(By.CLASS_NAME, 'review-details-holder')
            if not reviews:
                break  

            for review in reviews:
                try:
                    date_str = review.find_element(By.CLASS_NAME, 'date').text.strip()
                    review_date = datetime.strptime(date_str, "%m/%d/%Y")

                    # Stop collecting
                    if review_date < since_date:
                        print(f"Reached date limit: {review_date}")
                        return review_urls

                    # Get the review URL
                    review_url = review.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    review_urls.append(review_url)

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            page_number += 1

    except TimeoutException as e:
        print(f"Error during URL collection: {e}")
    
    return review_urls

# Step 3: Scraping the review data and save using BeautifulSoup
def scrape_review_data(review_urls, drug_name):
    """Scrape data from collected review URLs using BeautifulSoup and save them."""
    scraped_data = []  
    source = "webmd"  

    for url in review_urls:
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'review-details-holder')))

           
            soup = BeautifulSoup(driver.page_source, 'html.parser')

           
            author_tag = soup.find('div', class_='details')
            author = author_tag.get_text(strip=True).split(" |")[0] if author_tag else 'N/A'

            date_tag = soup.find('span', class_='date')
            date_str = date_tag.get_text(strip=True) if date_tag else 'N/A'
            review_date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d") if date_str != 'N/A' else 'N/A'

            title_tag = soup.find('div', class_='condition')
            title = title_tag.get_text(strip=True) if title_tag else 'No title'

            content_tag = soup.find('p', class_='description')
            content = content_tag.get_text(strip=True) if content_tag else 'No content'

            
            scraped_data.append({
                "date": review_date,
                "headline": title,
                "content": content,
                "author": author,
                "url": url,
                "source": source
            })

            smart_wait()

        except TimeoutException as e:
            print(f"Timeout while scraping review: {e}")
        except (NoSuchElementException, StaleElementReferenceException):
            continue

    # Save the data to an Excel file
    save_to_excel(scraped_data, f"{drug_name}_reviews.xlsx")

# Function to save scraped data to Excel
def save_to_excel(scraped_data, filename):
    """Save the scraped data to an Excel file using pandas."""
    df = pd.DataFrame(scraped_data)
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Data successfully saved to {filename}")

# Main function to manage the process
def main():
    if not os.path.exists('data'):
        os.makedirs('data')

    # Define the drug and date limit for scraping
    drug_name = "depakote"  
    since_date = datetime.now() - timedelta(days=365)  

    # Step 1: Search for the drug and get the reviews page URL
    reviews_url = search_drug(drug_name)
    if not reviews_url:
        print(f"No reviews found for {drug_name}")
        return

    # Step 2: Collect all review post URLs
    review_urls = collect_review_urls(reviews_url, since_date)
    print(f"Collected {len(review_urls)} review URLs.")

    # Step 3: Scrape the data from the collected URLs
    scrape_review_data(review_urls, drug_name)

    driver.quit()

if __name__ == "__main__":
    main()
