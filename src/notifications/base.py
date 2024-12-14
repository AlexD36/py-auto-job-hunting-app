"""
Base notification class
"""
from abc import ABC, abstractmethod
from typing import List
from src.scrapers.base import JobPosting
from src.utils.logger import setup_logger

class BaseNotifier(ABC):
    """Base class for notification systems"""
    
    def __init__(self, logger=None):
        self.logger = logger or setup_logger("logs/notifications.log")
    
    @abstractmethod
    def send_notification(self, jobs: List[JobPosting]) -> bool:
        """
        Send notification for new job postings
        
        Args:
            jobs: List of JobPosting objects to notify about
            
        Returns:
            bool: True if notification was sent successfully
        """
        pass
        
    def format_message(self, jobs: List[JobPosting]) -> str:
        """
        Format job listings into a readable message
        
        Args:
            jobs: List of JobPosting objects
            
        Returns:
            str: Formatted message
        """
        if not jobs:
            return "No new job matches found."
            
        message = "🔍 New Job Matches Found!\n\n"
        
        for job in jobs:
            message += f"🏢 {job.company}\n"
            message += f"💼 {job.title}\n"
            message += f"📍 {job.location}\n"
            message += f"🔗 {job.url}\n"
            message += "─" * 40 + "\n\n"
            
        return message
