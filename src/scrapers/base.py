"""
Base scraper class for job websites
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from src.utils.logger import setup_logger

@dataclass
class JobPosting:
    """Data class for storing job posting information"""
    title: str
    company: str
    location: str
    url: str
    description: str
    posted_date: Optional[str] = None

class BaseScraper(ABC):
    """Base class for job website scrapers"""
    
    def __init__(self, base_url: str, logger=None):
        self.base_url = base_url
        self.logger = logger or setup_logger("logs/scraper.log")
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch fails
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    @abstractmethod
    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape job postings from the website
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        pass