"""
WeWorkRemotely job board scraper implementation
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin
import time
from bs4 import BeautifulSoup
from .base import BaseScraper, JobPosting

class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for WeWorkRemotely website"""
    
    # Job categories mapping
    CATEGORIES = {
        "programming": "Programming",
        "devops-sysadmin": "DevOps & SysAdmin",
        "quality-assurance": "Quality Assurance",
        "product": "Product",
        "all": "All Remote Jobs"
    }
    
    def __init__(self):
        super().__init__("https://weworkremotely.com")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
        
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse WeWorkRemotely date format to ISO format
        
        Args:
            date_str: Date string from WWR (e.g., "2 days ago", "< 1 week ago")
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        try:
            date_str = date_str.lower().strip()
            today = datetime.now()
            
            if "today" in date_str or "< 24h" in date_str:
                return today.strftime("%Y-%m-%d")
                
            if "yesterday" in date_str:
                return (today - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Match patterns like "2 days ago"
            days_match = re.search(r"(\d+)\s+days?\s+ago", date_str)
            if days_match:
                days = int(days_match.group(1))
                return (today - timedelta(days=days)).strftime("%Y-%m-%d")
                
            # Match patterns like "< 1 week ago"
            weeks_match = re.search(r"<?\s*(\d+)\s+weeks?\s+ago", date_str)
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
        if category == "all":
            return f"{self.base_url}/remote-jobs"
        return f"{self.base_url}/categories/remote-{category}-jobs"

    def _extract_job_type(self, tags: List[str]) -> str:
        """
        Extract job type from job tags
        
        Args:
            tags: List of job tags
            
        Returns:
            str: Job type (e.g., "Full-Time", "Contract")
        """
        type_mapping = {
            "full-time": "Full-Time",
            "contract": "Contract",
            "part-time": "Part-Time",
            "freelance": "Freelance"
        }
        
        for tag in tags:
            tag_lower = tag.lower()
            for key, value in type_mapping.items():
                if key in tag_lower:
                    return value
                    
        return "Not specified"

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
            "salary_range": "",
            "job_type": "",
            "tags": []
        }
        
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        soup = self._fetch_page(job_url)
        if not soup:
            return details
            
        try:
            # Find job description
            content_div = soup.find("div", class_="listing-container")
            if content_div:
                # Extract salary range if available
                salary_elem = content_div.find("div", class_="salary")
                if salary_elem:
                    details["salary_range"] = salary_elem.get_text(strip=True)
                
                # Extract job requirements
                req_section = content_div.find("div", class_="requirements")
                if req_section:
                    details["requirements"] = req_section.get_text(strip=True)
                
                # Extract full description
                details["description"] = content_div.get_text(strip=True)
                
            # Extract job tags
            tags = soup.find_all("span", class_="listing-tag")
            details["tags"] = [tag.get_text(strip=True) for tag in tags]
            details["job_type"] = self._extract_job_type(details["tags"])
            
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {str(e)}")
            
        return details

    def _matches_keyword(self, job_data: dict, keyword: str) -> bool:
        """Enhanced keyword matching with more flexible criteria"""
        keyword_lower = keyword.lower()
        title_lower = job_data["title"].lower()
        description_lower = job_data["description"].lower() if job_data["description"] else ""
        
        # Direct matches
        if any(kw in title_lower for kw in keyword_lower.split()):
            return True
        
        if description_lower and any(kw in description_lower for kw in keyword_lower.split()):
            return True
        
        # Related terms with broader matching
        related_terms = {
            "developer": ["engineer", "programmer", "dev", "coding", "software", "application"],
            "engineer": ["developer", "programming", "technical", "software", "systems"],
            "devops": ["sysadmin", "infrastructure", "cloud", "aws", "azure", "kubernetes", "docker"],
            "frontend": ["react", "vue", "angular", "javascript", "typescript", "ui", "web"],
            "backend": ["python", "java", "node", "api", "database", "server"],
            "intern": ["internship", "student", "graduate", "junior", "entry", "trainee", "entry-level"],
            "junior": ["entry level", "graduate", "intern", "trainee", "entry-level", "junior"],
            "entry level": ["junior", "graduate", "intern", "trainee", "entry-level"],
            "software engineer": ["developer", "programmer", "swe", "software developer"],
            "qa": ["quality", "test", "testing", "qe", "quality engineer"],
            "data": ["analytics", "scientist", "analysis", "ml", "ai"],
            "security": ["cybersecurity", "infosec", "cyber", "security engineer"]
        }
        
        # Check for related terms
        base_keyword = next((k for k in related_terms.keys() if k in keyword_lower), None)
        if base_keyword:
            return any(term in title_lower or term in description_lower 
                      for term in related_terms[base_keyword])
        
        return False

    def scrape_jobs(self, keywords: List[str]) -> List[JobPosting]:
        """
        Scrape all jobs from WeWorkRemotely programming category first,
        then filter by keywords
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of JobPosting objects
        """
        jobs: List[JobPosting] = []
        processed_urls = set()  # Track processed URLs to avoid duplicates
        
        # Search only in programming category first
        category = "programming"
        try:
            self.logger.info(f"Scraping all jobs from WWR category {category}")
            
            url = self._get_category_url(category)
            soup = self._fetch_page(url)
            
            if not soup:
                return jobs
            
            # Find all job sections
            job_sections = soup.find_all("section", class_="jobs")
            
            for section in job_sections:
                job_items = section.find_all("li")
                
                for item in job_items:
                    try:
                        # Skip feature/view-all items
                        if "feature" in item.get("class", []) or "view-all" in item.get("class", []):
                            continue
                        
                        # Extract basic job details
                        link = item.find("a", href=True)
                        if not link:
                            continue
                        
                        job_url = urljoin(self.base_url, link["href"])
                        
                        # Skip if already processed
                        if job_url in processed_urls:
                            continue
                        
                        processed_urls.add(job_url)
                        
                        # Extract job information
                        company = item.find("span", class_="company").text.strip()
                        title = item.find("span", class_="title").text.strip()
                        location = item.find("span", class_="region").text.strip()
                        date_elem = item.find("span", class_="date")
                        
                        # Get detailed job information
                        details = self._extract_job_details(job_url)
                        
                        # Format full description
                        full_description = "\n\n".join([
                            f"Category: {self.CATEGORIES[category]}",
                            f"Job Type: {details['job_type']}",
                            f"Salary Range: {details['salary_range']}" if details['salary_range'] else "",
                            "Description:",
                            details["description"],
                            "Requirements:",
                            details["requirements"],
                            "Tags:",
                            ", ".join(details["tags"])
                        ])
                        
                        job = JobPosting(
                            title=title,
                            company=company,
                            location=location,
                            url=job_url,
                            description=full_description,
                            posted_date=self._parse_date(date_elem.text.strip()) if date_elem else None
                        )
                        
                        # Add all jobs first, filtering will be done later
                        jobs.append(job)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing job item: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error scraping WWR category {category}: {str(e)}")
        
        # Now filter jobs by keywords
        filtered_jobs = []
        for job in jobs:
            for keyword in keywords:
                if self._matches_keyword({"title": job.title, "company": job.company, 
                                        "description": job.description}, keyword):
                    filtered_jobs.append(job)
                    break  # Move to next job once we find a match
        
        self.logger.info(f"Found {len(jobs)} total jobs, filtered to {len(filtered_jobs)} matching jobs")
        return filtered_jobs
