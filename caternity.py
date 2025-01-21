import os
import random
import time
import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Chrome driver
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(options=chrome_options)

post_urls = []  # Store all post URLs here
page_number = 1

def smart_wait(min_time=2, max_time=5):
    """Introduce a smart wait to make interactions seem more human-like."""
    time.sleep(random.uniform(min_time, max_time))

def collect_post_urls(page_number):
    """Collects all post URLs from the current page and stores them in post_urls list."""
    try:
        driver.get(f"https://www.carenity.us/forum/asthma-88?page={page_number}")
        smart_wait()  # Wait to mimic natural behavior
        
        try:
            # Handle cookie modal if present
            con = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "didomi-continue-without-agreeing"))
            ).click()
            logging.info("Accepted cookies.")
        except TimeoutException:
            logging.info("No cookie modal found.")
        
        # Wait for the relevant section to load
        try:
            discussion_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "module-discussions.box-list-thread"))
            )
        except TimeoutException:
            logging.error(f"Timeout waiting for discussion section on page {page_number}. Skipping.")
            return True  # Continue to the next page

        # Collect URLs from the loaded section
        elems = discussion_section.find_elements(By.CLASS_NAME, "title-discussion")
        logging.info(f"Page {page_number}: {len(elems)} posts found")

        if not elems:
            logging.info("No posts found on this page.")
            return False  # Stop pagination if no posts are found

        for elem in elems:
            try:
                a_tag = elem.find_element(By.TAG_NAME, "a")
                href = a_tag.get_attribute("href")
                post_urls.append(href)  # Store the URL
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logging.error(f"Error while collecting URL: {e}")

        return True

    except Exception as e:
        logging.error(f"Unexpected error on page {page_number}: {e}")
        return False  # Stop pagination in case of unexpected errors

def save_urls_to_csv(post_urls, output_file):
    """Save collected URLs to a CSV file."""
    if not post_urls:
        logging.warning("No URLs collected. CSV file will not be created.")
        return
    
    with open(output_file, mode='w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Post URL"])
        for url in post_urls:
            writer.writerow([url])
    logging.info(f"Post URLs saved to {output_file}")

# Step 1: Collect all post URLs across pages
try:
    while True:
        if not collect_post_urls(page_number):
            break
        page_number += 1
finally:
    logging.info(f"Collected {len(post_urls)} post URLs.")
    driver.quit()

output_csv_file = "asthma_post_urls.csv"
save_urls_to_csv(post_urls, output_csv_file)
