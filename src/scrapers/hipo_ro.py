"""
Scraper for Hipo.ro website, focusing on student and entry-level positions
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from .base import BaseScraper, JobPosting

class HipoRoScraper(BaseScraper):
    """Scraper for Hipo.ro website"""
    
    # Job type mappings
    JOB_TYPES = {
        "internship": "Internship",
        "entry": "Entry Level",
        "student": "Student",
        "junior": "Junior",
        "trainee": "Trainee"
    }
    
    def __init__(self):
        super().__init__("https://www.hipo.ro")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Cache-Control": "no-cache"
        })

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse Hipo.ro date format to ISO format
        
        Args:
            date_str: Date string from Hipo.ro (e.g., "Adăugat astăzi", "Acum 2 zile")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            if "astăzi" in date_str or "azi" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "ieri" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "Acum 2 zile"
            days_match = re.search(r"acum\s+(\d+)\s+zile?", date_str)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _detect_job_type(self, title: str, description: str) -> str:
        """
        Detect job type from title and description
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            str: Detected job type or "Not specified"
        """
        text = f"{title} {description}".lower()
        
        for key, job_type in self.JOB_TYPES.items():
            if key in text:
                return job_type
                
        return "Not specified"

    def _build_search_url(self, keyword: str, location: str = "", page: int = 1) -> str:
        """
        Build search URL for Hipo.ro
        
        Args:
            keyword: Job title or keyword
            location: Location to search in
            page: Page number
            
        Returns:
            str: Formatted search URL
        """
        # Encode parameters for URL
        keyword_encoded = quote(keyword)
        location_encoded = quote(location) if location else ""
        
        # Base search URL
        url = f"{self.base_url}/locuri-de-munca"
        
        # Add filters
        filters = []
        if keyword_encoded:
            filters.append(f"keyword={keyword_encoded}")
        if location_encoded:
            filters.append(f"location={location_encoded}")
            
        # Add page number if not first page
        if page > 1:
            filters.append(f"page={page}")
            
        # Combine URL with filters
        if filters:
            url = f"{url}?{'&'.join(filters)}"
            
        return url

    def _extract_job_details(self, job_url: str) -> Dict[str, str]:
        """
        Extract detailed job information from job page
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dict containing job details
        """
        details = {
            "description": "",
            "requirements": "",
            "benefits": ""
        }
        
        soup = self._fetch_page(job_url)
        if not soup:
            return details
            
        try:
            # Find job description
            desc_elem = soup.find("div", class_="job-description")
            if desc_elem:
                details["description"] = desc_elem.get_text(strip=True)
                
            # Find requirements
            req_elem = soup.find("div", class_="job-requirements")
            if req_elem:
                details["requirements"] = req_elem.get_text(strip=True)
                
            # Find benefits
            benefits_elem = soup.find("div", class_="job-benefits")
            if benefits_elem:
                details["benefits"] = benefits_elem.get_text(strip=True)
                
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {str(e)}")
            
        return details

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from Hipo.ro
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        for keyword in keywords:
            try:
                self.logger.info(f"Scraping Hipo.ro for keyword: {keyword}")
                page = 1
                
                while True:
                    search_url = self._build_search_url(keyword, page=page)
                    soup = self._fetch_page(search_url)
                    
                    if not soup:
                        break
                        
                    # Find all job cards
                    job_cards = soup.find_all("div", class_="job-card")
                    
                    if not job_cards:
                        break
                        
                    for card in job_cards:
                        try:
                            # Extract job details
                            title_elem = card.find("h2", class_="job-title")
                            company_elem = card.find("div", class_="company-name")
                            location_elem = card.find("div", class_="job-location")
                            date_elem = card.find("div", class_="post-date")
                            
                            if not all([title_elem, company_elem]):
                                continue
                                
                            # Get job URL
                            title_link = title_elem.find("a", href=True)
                            if title_link:
                                job_url = urljoin(self.base_url, title_link["href"])
                                
                                # Extract job details
                                details = self._extract_job_details(job_url)
                                
                                # Create JobPosting object
                                job = JobPosting(
                                    title=title_elem.get_text(strip=True),
                                    company=company_elem.get_text(strip=True),
                                    location=location_elem.get_text(strip=True),
                                    date=self._parse_date(date_elem.get_text(strip=True)),
                                    description=details["description"],
                                    requirements=details["requirements"],
                                    benefits=details["benefits"]
                                )
                                
                                jobs.append(job)
                                
                        except Exception as e:
                            self.logger.error(f"Error scraping job from {job_url}: {str(e)}")
                            
                        break
                        
                    page += 1
                    
            except Exception as e:
                self.logger.error(f"Error scraping Hipo.ro for keyword: {keyword}: {str(e)}")
                
        return jobs 