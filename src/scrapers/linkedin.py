"""
LinkedIn Jobs scraper implementation with rate limiting and ethical practices
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import re
import time
import random
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base import BaseScraper, JobPosting

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs with ethical rate limiting"""
    
    def __init__(self):
        super().__init__("https://www.linkedin.com/jobs")
        self.driver = None
        self._setup_driver()
        
    def _setup_driver(self) -> None:
        """Initialize Selenium WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Add random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
    def __del__(self):
        """Clean up WebDriver on object destruction"""
        if self.driver:
            self.driver.quit()

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse LinkedIn date format to ISO format
        
        Args:
            date_str: Date string from LinkedIn (e.g., "2 days ago", "1 week ago")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            if "just now" in date_str or "today" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "yesterday" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "2 days ago", "1 week ago", "3 months ago"
            time_map = {
                "day": 1,
                "week": 7,
                "month": 30,
                "hour": 1/24,
                "minute": 1/1440
            }
            
            for period, multiplier in time_map.items():
                pattern = rf"(\d+)\s+{period}s?\s+ago"
                match = re.search(pattern, date_str)
                if match:
                    value = int(match.group(1))
                    days = value * multiplier
                    return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _wait_random(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """
        Wait for a random amount of time between requests
        
        Args:
            min_seconds: Minimum wait time in seconds
            max_seconds: Maximum wait time in seconds
        """
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _build_search_url(self, keyword: str, location: str = "") -> str:
        """
        Build LinkedIn Jobs search URL
        
        Args:
            keyword: Job title or keyword
            location: Location to search in
            
        Returns:
            str: Formatted search URL
        """
        # Encode parameters for URL
        keyword_encoded = quote(keyword)
        location_encoded = quote(location) if location else ""
        
        url = f"{self.base_url}/search?keywords={keyword_encoded}"
        if location_encoded:
            url = f"{url}&location={location_encoded}"
            
        return url

    def _extract_job_details(self, job_card) -> Optional[Dict[str, str]]:
        """
        Extract job details from a job card element
        
        Args:
            job_card: Selenium WebElement representing a job card
            
        Returns:
            Dictionary containing job details or None if extraction fails
        """
        try:
            # Extract basic information with explicit waits
            wait = WebDriverWait(self.driver, 10)
            
            title = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3.job-title"))
            ).text.strip()
            
            company = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h4.company-name"))
            ).text.strip()
            
            location = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.job-location"))
            ).text.strip()
            
            date_posted = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time.job-posted-date"))
            ).text.strip()
            
            job_link = job_card.find_element(By.CSS_SELECTOR, "a.job-link").get_attribute("href")
            
            # Click to expand job description
            try:
                show_more = job_card.find_element(By.CSS_SELECTOR, "button.show-more-less-button")
                show_more.click()
                self._wait_random(1.0, 2.0)
            except NoSuchElementException:
                pass
                
            description = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-description"))
            ).text.strip()
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "date_posted": date_posted,
                "url": job_link,
                "description": description
            }
            
        except (TimeoutException, NoSuchElementException) as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return None

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from LinkedIn
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        for keyword in keywords:
            try:
                self.logger.info(f"Scraping LinkedIn Jobs for keyword: {keyword}")
                search_url = self._build_search_url(keyword)
                
                # Navigate to search URL
                self.driver.get(search_url)
                self._wait_random()
                
                # Scroll through results (LinkedIn loads jobs dynamically)
                for _ in range(3):  # Limit to 3 scrolls for ethical scraping
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    self._wait_random(1.0, 2.0)
                    
                # Find all job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-card-container")
                
                for card in job_cards:
                    try:
                        details = self._extract_job_details(card)
                        if not details:
                            continue
                            
                        job = JobPosting(
                            title=details["title"],
                            company=details["company"],
                            location=details["location"],
                            url=details["url"],
                            description=details["description"],
                            posted_date=self._parse_date(details["date_posted"])
                        )
                        
                        jobs.append(job)
                        
                        # Ethical rate limiting
                        self._wait_random()
                        
                    except Exception as e:
                        self.logger.error(f"Error processing job card: {str(e)}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error scraping LinkedIn for keyword {keyword}: {str(e)}")
                continue
                
        return jobs