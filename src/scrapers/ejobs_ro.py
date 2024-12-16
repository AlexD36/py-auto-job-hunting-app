"""
Scraper for eJobs.ro website
"""
from typing import List, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from .base import BaseScraper, JobPosting

class EJobsRoScraper(BaseScraper):
    """Scraper for eJobs.ro website"""
    
    def __init__(self):
        super().__init__("https://www.ejobs.ro")
        # Add specific headers for eJobs
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse eJobs.ro date format to ISO format
        
        Args:
            date_str: Date string from eJobs (e.g., "Actualizat azi", "Publicat acum 3 zile")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            if "azi" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "ieri" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "acum 3 zile" or "3 zile în urmă"
            days_match = re.search(r"(?:acum\s+)?(\d+)\s+zile?(?:\s+[îi]n\s+urm[aă])?", date_str)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _parse_salary(self, salary_elem) -> Optional[str]:
        """
        Parse salary information from job listing
        
        Args:
            salary_elem: BeautifulSoup element containing salary info
            
        Returns:
            Formatted salary string or None if not available
        """
        if not salary_elem:
            return None
            
        try:
            salary_text = salary_elem.get_text(strip=True)
            # Remove currency symbols and normalize format
            salary_text = re.sub(r'[^\d\s-]+', '', salary_text)
            salary_text = re.sub(r'\s+', ' ', salary_text).strip()
            return salary_text if salary_text else None
        except Exception as e:
            self.logger.error(f"Error parsing salary: {str(e)}")
            return None

    def _build_search_url(self, keyword: str, location: str = "") -> str:
        """
        Build search URL for eJobs.ro
        
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
        url = f"{self.base_url}/locuri-de-munca/cautare/{keyword_encoded}"
        
        # Add location if specified
        if location_encoded:
            url = f"{url}/in-{location_encoded}"
            
        return url

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from eJobs.ro
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        for keyword in keywords:
            try:
                search_url = self._build_search_url(keyword)
                self.logger.info(f"Scraping eJobs.ro for keyword: {keyword}")
                
                page = 1
                while True:
                    # Add page parameter for pagination
                    page_url = f"{search_url}/page{page}" if page > 1 else search_url
                    soup = self._fetch_page(page_url)
                    
                    if not soup:
                        break
                        
                    # Find all job cards
                    job_cards = soup.find_all("div", class_="JCContent")
                    
                    if not job_cards:
                        break
                        
                    for card in job_cards:
                        try:
                            # Extract job details
                            title_elem = card.find("h2", class_="JCTitle")
                            company_elem = card.find("span", class_="JCCompany")
                            location_elem = card.find("span", class_="JCLocation")
                            date_elem = card.find("span", class_="JCDate")
                            salary_elem = card.find("span", class_="JCSalary")
                            
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
                                description_elem = job_soup.find("div", class_="JDDescription")
                                if description_elem:
                                    description = description_elem.get_text(strip=True)
                            
                            # Parse salary if available
                            salary = self._parse_salary(salary_elem)
                            if salary:
                                description = f"Salary: {salary}\n\n{description}"
                            
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
                self.logger.error(f"Error scraping eJobs.ro for keyword {keyword}: {str(e)}")
                continue
                
        return jobs