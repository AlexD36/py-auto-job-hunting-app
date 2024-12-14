"""
Job filtering utilities
"""
from dataclasses import dataclass
from typing import List, Optional
from src.scrapers.base import JobPosting

@dataclass
class FilterCriteria:
    """Data class for job filtering criteria"""
    keywords: List[str]
    locations: List[str]
    include_unspecified_locations: bool = True
    max_days_old: Optional[int] = None

class JobFilter:
    """Job filtering implementation"""
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
        # Convert all criteria to lowercase for case-insensitive matching
        self.keywords = [k.lower() for k in criteria.keywords]
        self.locations = [l.lower() for l in criteria.locations]

    def matches_keywords(self, job: JobPosting) -> bool:
        """
        Check if job matches any keywords
        
        Args:
            job: JobPosting to check
            
        Returns:
            bool: True if job matches any keywords
        """
        # Check title and description for keywords
        text_to_check = f"{job.title} {job.description}".lower()
        return any(keyword in text_to_check for keyword in self.keywords)

    def matches_location(self, job: JobPosting) -> bool:
        """
        Check if job matches location criteria
        
        Args:
            job: JobPosting to check
            
        Returns:
            bool: True if job matches location criteria
        """
        job_location = job.location.lower()
        
        # Check for direct location match
        if any(location in job_location for location in self.locations):
            return True
            
        # Check for unspecified location
        if self.criteria.include_unspecified_locations and (
            not job_location or 
            job_location == "not specified" or 
            "remote" in job_location
        ):
            return True
            
        return False

    def filter_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """
        Filter jobs based on criteria
        
        Args:
            jobs: List of JobPosting objects to filter
            
        Returns:
            List[JobPosting]: Filtered list of jobs
        """
        filtered_jobs = []
        
        for job in jobs:
            # Skip if job doesn't match keywords
            if not self.matches_keywords(job):
                continue
                
            # Skip if job doesn't match location
            if not self.matches_location(job):
                continue
                
            filtered_jobs.append(job)
            
        return filtered_jobs

# Default criteria for Romanian jobs
ROMANIA_FILTER_CRITERIA = FilterCriteria(
    keywords=[
        "Python",
        "Software Developer",
        "Data Scientist",
        "Machine Learning",
        "Internship",
        "Romania",
        "Developer",
        "Engineer"
    ],
    locations=[
        "Bucharest",
        "București", # Romanian spelling
        "Cluj-Napoca",
        "Cluj",
        "Timișoara",
        "Iași",
        "Brașov",
        "Constanța",
        "Remote"
    ],
    include_unspecified_locations=True
) 