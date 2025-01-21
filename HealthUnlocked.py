import os
import random
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import time
import requests
from fake_useragent import UserAgent
from datetime import datetime, timedelta, timezone

# ------For IP Rotating-------
ua = UserAgent(browsers='chrome')
url = 'https://healthunlocked.com'
headers = {'User-Agent': ua.random if ua else None}
response = requests.get(url, headers=headers)

# --------Healthunlocked Login---------
if not os.path.exists('data'):
    os.makedirs('data')

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

def create_driver():
    """Creates a new WebDriver instance."""
    return webdriver.Chrome(options=chrome_options)

def login(driver):
    """Logs into HealthUnlocked."""
    try:
        driver.get("https://healthunlocked.com/login")

        email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        password = driver.find_element(By.ID, "password")

        email.send_keys("furic360@gmail.com")
        password.send_keys("(niky31)?")
        password.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.url_changes("https://healthunlocked.com/login"))
        print("Login successful")
    except TimeoutException:
        print("Login failed due to timeout")
        driver.quit()

# ----------Smart Wait----------
def smart_wait(min_time=2, max_time=5):
    """Introduce a smart wait to make interactions seem more human-like."""
    time.sleep(random.uniform(min_time, max_time))

# ----------Post Collection with Date Filtering----------
def collect_post_urls(driver, page_number, query, cutoff_days=20):
    """Collects post URLs from the current page, filtering by date."""
    post_urls = []
    try:
        driver.get(f"https://healthunlocked.com/search/posts?community=all&query={query}&sort=newest&page={page_number}")
        time.sleep(1)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "results-post")))
        elems = driver.find_elements(By.CLASS_NAME, "results-post")
        print(f"Page {page_number}: {len(elems)} items found")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
        for elem in elems:
            try:
                time_elem = elem.find_element(By.TAG_NAME, "time")
                post_date_str = time_elem.get_attribute("datetime")
                post_date = datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))

                if post_date < cutoff_date:
                    print(f"Skipping post dated {post_date}, older than cutoff date {cutoff_date}")
                    continue

                a_tag = elem.find_element(By.TAG_NAME, "a")
                href = a_tag.get_attribute("href")
                post_urls.append(href)
            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"Error while collecting URL: {e}")

        return post_urls

    except TimeoutException:
        print(f"Timeout while loading page {page_number}")
        return post_urls

# ----------Post Scraping----------
def scrape_post_data(driver, post_urls):
    """Scrapes the data from the given post URLs."""
    post = 0
    for url in post_urls:
        try:
            retries = 3
            for attempt in range(retries):
                try:
                    driver.get(url)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post-body")))
                    break
                except TimeoutException:
                    if attempt == retries - 1:
                        print(f"Timeout occurred after {retries} retries for post {post}")
                        driver.back()
                        continue
                    else:
                        print(f"Retrying to load post {post}...")

            post_html = driver.page_source
            with open(f"data/post_{post}.html", "w", encoding="utf-8") as f:
                f.write(post_html)

            print(f"Post {post} saved.")
            post += 1

            smart_wait()

        except (NoSuchElementException, StaleElementReferenceException) as e:
            print(f"Error with post {post}: {e}")
        except TimeoutException:
            print(f"Timeout occurred while loading page for post {post}")

# ----------Process Keywords from CSV----------
def process_keywords_from_csv(csv_filename):
    """Reads keywords from a CSV file."""
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]

# ----------Main Function----------
def main():
    keywords = process_keywords_from_csv('keywords.csv')  # Replace with your CSV file

    driver = create_driver()
    login(driver)

    try:
        for query in keywords:
            print(f"Scraping for keyword: {query}")
            page_number = 1
            all_post_urls = []

            while True:
                post_urls = collect_post_urls(driver, page_number, query, cutoff_days=20)
                if not post_urls:
                    break

                all_post_urls.extend(post_urls)
                page_number += 1

            print(f"Collected {len(all_post_urls)} post URLs for {query}.")

            scrape_post_data(driver, all_post_urls)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
