"""
Scraper for BestJobs.ro website
"""
from typing import List, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from .base import BaseScraper, JobPosting

class BestJobsRoScraper(BaseScraper):
    """Scraper for BestJobs.ro website"""
    
    def __init__(self):
        super().__init__("https://www.bestjobs.ro")
        
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse BestJobs.ro date format to ISO format
        
        Args:
            date_str: Date string from BestJobs (e.g., "Publicat azi", "Publicat acum 2 zile")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower()
            today = datetime.now()
            
            if "azi" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "ieri" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "acum 2 zile"
            days_match = re.search(r"acum\s+(\d+)\s+zile?", date_str)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _build_search_url(self, keyword: str, location: str = "") -> str:
        """
        Build search URL for BestJobs.ro
        
        Args:
            keyword: Job title or keyword
            location: Location to search in
            
        Returns:
            str: Formatted search URL
        """
        # Encode parameters for URL
        keyword_encoded = quote(keyword)
        location_encoded = quote(location) if location else ""
        
        # Base search URL
        url = f"{self.base_url}/locuri-de-munca/{keyword_encoded}"
        
        # Add location if specified
        if location_encoded:
            url = f"{url}/in-{location_encoded}"
            
        return url

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from BestJobs.ro
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        for keyword in keywords:
            try:
                # Search in Romania by default
                search_url = self._build_search_url(keyword)
                self.logger.info(f"Scraping BestJobs.ro for keyword: {keyword}")
                
                page = 1
                while True:
                    # Add page parameter for pagination
                    page_url = f"{search_url}?page={page}"
                    soup = self._fetch_page(page_url)
                    
                    if not soup:
                        break
                        
                    # Find all job cards
                    job_cards = soup.find_all("div", class_="job-card")
                    
                    if not job_cards:
                        break
                        
                    for card in job_cards:
                        try:
                            # Extract job details
                            title_elem = card.find("h2", class_="title")
                            company_elem = card.find("div", class_="company-name")
                            location_elem = card.find("div", class_="location")
                            date_elem = card.find("div", class_="posting-date")
                            
                            if not all([title_elem, company_elem]):
                                continue
                                
                            # Get job URL
                            title_link = title_elem.find("a", href=True)
                            if not title_link:
                                continue
                                
                            job_url = urljoin(self.base_url, title_link["href"])
                            
                            # Get detailed description
                            job_soup = self._fetch_page(job_url)
                            description = ""
                            if job_soup:
                                description_elem = job_soup.find("div", class_="job-description")
                                if description_elem:
                                    description = description_elem.get_text(strip=True)
                            
                            job = JobPosting(
                                title=title_elem.get_text(strip=True),
                                company=company_elem.get_text(strip=True),
                                location=location_elem.get_text(strip=True) if location_elem else "Not specified",
                                url=job_url,
                                description=description,
                                posted_date=self._parse_date(date_elem.get_text(strip=True)) if date_elem else None
                            )
                            
                            jobs.append(job)
                            
                        except Exception as e:
                            self.logger.error(f"Error parsing job card: {str(e)}")
                            continue
                    
                    # Move to next page
                    page += 1
                    
                    # Break if we've processed too many pages (avoid infinite loops)
                    if page > 10:
                        break
                    
            except Exception as e:
                self.logger.error(f"Error scraping BestJobs.ro for keyword {keyword}: {str(e)}")
                continue
                
        return jobs 