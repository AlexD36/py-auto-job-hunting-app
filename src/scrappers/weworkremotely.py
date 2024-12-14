"""
Scraper for WeWorkRemotely website
"""
from typing import List
from datetime import datetime
from urllib.parse import urljoin
from .base import BaseScraper, JobPosting

class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for WeWorkRemotely website"""
    
    def __init__(self):
        super().__init__("https://weworkremotely.com")
        
    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape jobs from WeWorkRemotely
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        
        # WeWorkRemotely has a programming category
        url = f"{self.base_url}/categories/remote-programming-jobs"
        
        soup = self._fetch_page(url)
        if not soup:
            return jobs
            
        try:
            # Find all job listings
            job_sections = soup.find_all("section", class_="jobs")
            
            for section in job_sections:
                job_items = section.find_all("li")
                
                for item in job_items:
                    # Skip feature/view-all items
                    if "feature" in item.get("class", []) or "view-all" in item.get("class", []):
                        continue
                        
                    try:
                        # Extract job details
                        link = item.find("a", href=True)
                        if not link:
                            continue
                            
                        company = item.find("span", class_="company").text.strip()
                        title = item.find("span", class_="title").text.strip()
                        location = item.find("span", class_="region").text.strip()
                        
                        # Check if job matches any keywords
                        if not any(keyword.lower() in title.lower() for keyword in keywords):
                            continue
                            
                        # Get full job URL
                        job_url = urljoin(self.base_url, link["href"])
                        
                        # Get job description from the job page
                        job_soup = self._fetch_page(job_url)
                        description = ""
                        if job_soup:
                            description_div = job_soup.find("div", class_="listing-container")
                            description = description_div.text.strip() if description_div else ""
                        
                        job = JobPosting(
                            title=title,
                            company=company,
                            location=location,
                            url=job_url,
                            description=description
                        )
                        
                        jobs.append(job)
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing job listing: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error scraping WeWorkRemotely: {str(e)}")
            
        return jobs
