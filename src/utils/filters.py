"""
Job filtering utilities with enhanced text normalization and logging
"""
from dataclasses import dataclass
from typing import List, Optional, Set
import re
import logging
from datetime import datetime, timedelta
from src.scrapers.base import JobPosting
from src.utils.logger import setup_logger

@dataclass
class FilterCriteria:
    """
    Data class for job filtering criteria
    
    Attributes:
        keywords: List of keywords to match against job title/description
        locations: List of acceptable job locations
        include_unspecified_locations: Whether to include jobs with unspecified locations
        max_days_old: Maximum age of job posting in days
        exact_match: Whether to require exact keyword matches
        use_regex: Whether to treat keywords as regular expressions
    """
    keywords: List[str]
    locations: List[str]
    include_unspecified_locations: bool = True
    max_days_old: Optional[int] = None
    exact_match: bool = False
    use_regex: bool = False

def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text for consistent matching
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text string
        
    Note:
        - Converts to lowercase
        - Removes extra whitespace
        - Removes special characters except hyphens
    """
    if not text:
        return ""
        
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    
    # Remove special characters except hyphens
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    return normalized

class JobFilter:
    """
    Job filtering implementation with enhanced matching and logging
    
    Attributes:
        criteria: FilterCriteria instance
        keywords: Set of normalized keywords
        locations: Set of normalized locations
        logger: Logging instance
    """
    
    def __init__(self, criteria: FilterCriteria):
        """
        Initialize job filter with criteria
        
        Args:
            criteria: FilterCriteria instance defining filter rules
        """
        self.criteria = criteria
        self.logger = setup_logger("logs/job_filter.log")
        
        # Normalize and store keywords
        self.keywords: Set[str] = {
            normalize_text(k) for k in criteria.keywords if k
        }
        
        # Normalize and store locations
        self.locations: Set[str] = {
            normalize_text(l) for l in criteria.locations if l
        }
        
        # Compile regex patterns if enabled
        self.keyword_patterns = None
        if criteria.use_regex:
            try:
                self.keyword_patterns = [
                    re.compile(k, re.IGNORECASE) for k in self.keywords
                ]
            except re.error as e:
                self.logger.error(f"Invalid regex pattern: {str(e)}")
                raise ValueError(f"Invalid regex pattern: {str(e)}")
                
        self.logger.info(
            f"Initialized filter with {len(self.keywords)} keywords "
            f"and {len(self.locations)} locations"
        )

    def matches_keywords(self, job: JobPosting) -> bool:
        """
        Check if job matches any keywords
        
        Args:
            job: JobPosting to check
            
        Returns:
            bool: True if job matches keywords criteria
        """
        # Normalize job text
        title = normalize_text(job.title)
        description = normalize_text(job.description)
        text_to_check = f"{title} {description}"
        
        if not text_to_check.strip():
            self.log_filter_reason(job, "Empty title and description")
            return False
            
        # Handle regex matching
        if self.criteria.use_regex and self.keyword_patterns:
            for pattern in self.keyword_patterns:
                if pattern.search(text_to_check):
                    return True
            self.log_filter_reason(job, "No regex keyword matches")
            return False
            
        # Handle exact matching
        if self.criteria.exact_match:
            words = set(text_to_check.split())
            if not any(keyword in words for keyword in self.keywords):
                self.log_filter_reason(job, "No exact keyword matches")
                return False
            return True
            
        # Handle partial matching
        if not any(keyword in text_to_check for keyword in self.keywords):
            self.log_filter_reason(job, "No partial keyword matches")
            return False
            
        return True

    def matches_location(self, job: JobPosting) -> bool:
        """
        Check if job matches location criteria
        
        Args:
            job: JobPosting to check
            
        Returns:
            bool: True if job matches location criteria
        """
        job_location = normalize_text(job.location)
        
        # Handle unspecified locations
        if not job_location:
            if self.criteria.include_unspecified_locations:
                return True
            self.log_filter_reason(job, "Unspecified location not allowed")
            return False
            
        # Check for remote work indicators
        if "remote" in job_location:
            return True
            
        # Tokenize location for more accurate matching
        location_tokens = set(job_location.split())
        
        # Check for location matches
        for location in self.locations:
            location_tokens_to_match = set(location.split())
            if location_tokens_to_match.issubset(location_tokens):
                return True
                
        self.log_filter_reason(
            job, 
            f"Location '{job_location}' not in allowed locations"
        )
        return False

    def matches_date_criteria(self, job: JobPosting) -> bool:
        """
        Check if job matches date criteria
        
        Args:
            job: JobPosting to check
            
        Returns:
            bool: True if job matches date criteria
        """
        if not self.criteria.max_days_old or not job.posted_date:
            return True
            
        cutoff_date = datetime.now() - timedelta(days=self.criteria.max_days_old)
        
        if job.posted_date < cutoff_date:
            self.log_filter_reason(
                job,
                f"Job too old (posted {job.posted_date.date()})"
            )
            return False
            
        return True

    def filter_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """
        Filter jobs based on all criteria
        
        Args:
            jobs: List of JobPosting objects to filter
            
        Returns:
            List[JobPosting]: Filtered list of jobs
        """
        if not jobs:
            self.logger.info("No jobs to filter")
            return []
            
        self.logger.info(f"Filtering {len(jobs)} jobs")
        filtered_jobs = []
        
        for job in jobs:
            try:
                # Skip if job doesn't match keywords
                if not self.matches_keywords(job):
                    continue
                    
                # Skip if job doesn't match location
                if not self.matches_location(job):
                    continue
                    
                # Skip if job doesn't match date criteria
                if not self.matches_date_criteria(job):
                    continue
                    
                filtered_jobs.append(job)
                
            except Exception as e:
                self.logger.error(
                    f"Error filtering job {job.title}: {str(e)}"
                )
                continue
                
        self.logger.info(
            f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)} matches"
        )
        return filtered_jobs

    def log_filter_reason(self, job: JobPosting, reason: str) -> None:
        """
        Log the reason why a job was filtered out
        
        Args:
            job: JobPosting that was filtered
            reason: Reason for filtering
        """
        self.logger.debug(
            f"Filtered out: {job.title} ({job.company}) - {reason}"
        )

# Default criteria for Romanian jobs
ROMANIA_FILTER_CRITERIA = FilterCriteria(
    keywords=[
        # Internship-related keywords
        "Intern",
        "Internship",
        "Student",
        "Trainee",
        "Graduate Program",
        "Student Program",
        # Programming-related keywords
        "Developer",
        "Software",
        "Programming",
        "Engineer",
        "Development",
        "IT",
        "Tech",
        "Application",
        "Web",
        "Mobile",
        "Full Stack",
        "Frontend",
        "Backend",
        "DevOps",
        "QA"
    ],
    locations=[
        "Bucharest",
        "București",
        "Cluj-Napoca",
        "Cluj",
        "Timișoara",
        "Iași",
        "Brașov",
        "Constanța",
        "Remote",
        "Hybrid",
        "Romania"
    ],
    include_unspecified_locations=True,
    max_days_old=30,
    exact_match=False,
    use_regex=False
) 