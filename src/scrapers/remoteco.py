"""
Remote.co job board scraper implementation
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from .base import BaseScraper, JobPosting

class RemoteCoScraper(BaseScraper):
    """Scraper for Remote.co website"""
    
    # Job categories mapping
    CATEGORIES = {
        "software-dev": "Software Development",
        "customer-service": "Customer Service",
        "design": "Design",
        "marketing": "Marketing",
        "sales": "Sales",
        "writing": "Writing",
        "hr": "Human Resources",
        "data": "Data",
        "devops": "DevOps & SysAdmin",
        "product": "Product",
        "qa": "QA & Testing"
    }
    
    def __init__(self):
        super().__init__("https://remote.co")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse Remote.co date format to ISO format
        
        Args:
            date_str: Date string from Remote.co (e.g., "Posted 2 days ago")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            if "today" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "yesterday" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "Posted 2 days ago"
            days_match = re.search(r"(\d+)\s+days?\s+ago", date_str)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                
            # Match patterns like "Posted 3 weeks ago"
            weeks_match = re.search(r"(\d+)\s+weeks?\s+ago", date_str)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return (today - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def _get_category_url(self, category: str) -> str:
        """
        Get URL for specific job category
        
        Args:
            category: Category key from CATEGORIES dict
            
        Returns:
            str: Category URL
        """
        return f"{self.base_url}/remote-jobs/{category}"

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
            "category": ""
        }
        
        soup = self._fetch_page(job_url)
        if not soup:
            return details
            
        try:
            # Find job description
            desc_elem = soup.find("div", class_="job_description")
            if desc_elem:
                details["description"] = desc_elem.get_text(strip=True)
                
            # Find job requirements
            req_elem = soup.find("div", class_="job_requirements")
            if req_elem:
                details["requirements"] = req_elem.get_text(strip=True)
                
            # Find job category
            cat_elem = soup.find("span", class_="job_category")
            if cat_elem:
                details["category"] = cat_elem.get_text(strip=True)
                
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {str(e)}")
            
        return details

    def _scrape_category(self, category: str) -> List[JobPosting]:
        """
        Scrape jobs from a specific category
        
        Args:
            category: Category key from CATEGORIES dict
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        page = 1
        
        while True:
            try:
                url = self._get_category_url(category)
                if page > 1:
                    url = f"{url}/page-{page}"
                    
                soup = self._fetch_page(url)
                if not soup:
                    break
                    
                # Find all job listings
                job_cards = soup.find_all("div", class_="job_listing")
                
                if not job_cards:
                    break
                    
                for card in job_cards:
                    try:
                        # Extract job details
                        title_elem = card.find("h2", class_="job_title")
                        company_elem = card.find("span", class_="company_name")
                        date_elem = card.find("span", class_="job_date")
                        
                        if not all([title_elem, company_elem]):
                            continue
                            
                        # Get job URL
                        title_link = title_elem.find("a", href=True)
                        if not title_link:
                            continue
                            
                        job_url = urljoin(self.base_url, title_link["href"])
                        
                        # Get detailed job information
                        details = self._extract_job_details(job_url)
                        
                        # Combine description with requirements
                        full_description = "\n\n".join([
                            f"Category: {details['category'] or self.CATEGORIES.get(category, 'Unknown')}",
                            "Description:",
                            details["description"],
                            "Requirements:",
                            details["requirements"]
                        ])
                        
                        job = JobPosting(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True),
                            location="Remote",  # All jobs are remote
                            url=job_url,
                            description=full_description,
                            posted_date=self._parse_date(date_elem.get_text(strip=True)) if date_elem else None
                        )
                        
                        jobs.append(job)
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing job card: {str(e)}")
                        continue
                        
                page += 1
                
                # Break if we've processed too many pages
                if page > 10:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error scraping category {category}: {str(e)}")
                break
                
        return jobs

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from Remote.co
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        # Map keywords to categories
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Find matching categories
            matching_categories = [
                cat for cat, name in self.CATEGORIES.items()
                if keyword_lower in name.lower() or keyword_lower in cat
            ]
            
            # If no matching categories, use software-dev as default
            if not matching_categories:
                matching_categories = ["software-dev"]
                
            # Scrape jobs from matching categories
            for category in matching_categories:
                category_jobs = self._scrape_category(category)
                
                # Filter jobs by keyword if not in category name
                if keyword_lower not in self.CATEGORIES[category].lower():
                    category_jobs = [
                        job for job in category_jobs
                        if keyword_lower in job.title.lower() or
                        keyword_lower in job.description.lower()
                    ]
                
                jobs.extend(category_jobs)
                
        return jobs 