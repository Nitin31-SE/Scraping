import os
import random
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

post_urls = []
page_number = 1

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(options=chrome_options)

def smart_wait(min_time=2, max_time=5):
    time.sleep(random.uniform(min_time, max_time))

def search_query(query):
    """Perform the search only once for the first page."""
    driver.get(f"https://www.healthboards.com/boards/search.php?query={query}")

    dropdown_element = driver.find_element(By.NAME, "searchmethod")
    select = Select(dropdown_element)
    select.select_by_visible_text("Match Phrase")

    dropdown_element = driver.find_element(By.NAME, "searchdate")
    select = Select(dropdown_element)
    select.select_by_visible_text("A Year Ago")

    driver.find_element(By.NAME, "dosearch").click()

def post_url(page_number):
    """Collect URLs of the posts from the current page."""
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tborder")))

        table = driver.find_element(By.XPATH, "//table[contains(@id, 'threadslist')]//tbody")

        # Iterate through each row in the table and collect URLs
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"Page {page_number}: {len(rows)} items found")

        if len(rows) == 0:
            print("No more posts found on this page")
            return False

        # Collect URLs from the rows
        for row in rows:
            try:
                a_tag = row.find_element(By.XPATH, ".//td[@class='alt1']//a")
                href = a_tag.get_attribute("href")
                post_urls.append(href)
            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"Error while collecting URL: {e}")

        return True

    except TimeoutException:
        print(f"Timeout while loading page {page_number}")
        return False

def go_to_next_page():
    """Check if 'Next' button exists and click it to go to the next page."""
    try:
        # Check if the "Next" button is present on the page
        next_page = driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
        if next_page:
            next_page.click()
            smart_wait()
            return True
    except NoSuchElementException:
        print("No 'Next' button found, ending pagination.")
        return False

def save_urls_to_csv(post_urls, query):
    """Save the collected URLs to a CSV file if URLs were found."""
    output_file = f"{query}_post_urls.csv"
    with open(output_file, mode='w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Post URL"])
        for url in post_urls:
            writer.writerow([url])
    print(f"Post URLs saved to {output_file}")

# Read queries from CSV file
with open("disease specific keyword diabetes.csv", mode='r', encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    queries = [row[0] for row in reader]

# Process each query from the CSV file
for query in queries:
    post_urls.clear()
    page_number = 1

    print(f"Processing query: {query}")
    try:
        search_query(query)

        # Collect URLs for the first page and navigate to subsequent pages
        while True:
            if not post_url(page_number):
                break
            if not go_to_next_page():
                break
            page_number += 1

    except Exception as e:
        print(f"Error encountered while processing query '{query}': {e}")

    # If URLs were collected, save them to CSV; otherwise, print "No data found"
    if post_urls:
        save_urls_to_csv(post_urls, query)
    else:
        print(f"No data found for query '{query}'")

# Quit the driver after processing all queries
driver.quit()
