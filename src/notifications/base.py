"""
Base notification class with enhanced logging and extensibility
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
import os
from src.scrapers.base import JobPosting
from src.utils.logger import setup_logger

class FormatType(Enum):
    """Enumeration of supported message format types"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"

class NotificationError(Exception):
    """Base exception for notification-related errors"""
    pass

class BaseNotifier(ABC):
    """
    Base class for notification systems with enhanced logging and extensibility
    
    Attributes:
        logger: Configured logging instance
        format_type: Message format type (text, markdown, html)
    """
    
    def __init__(self, 
                 log_file: str = "logs/notifications.log",
                 format_type: FormatType = FormatType.TEXT) -> None:
        """
        Initialize base notifier with logging setup
        
        Args:
            log_file: Path to log file
            format_type: Message format type to use
            
        Raises:
            NotificationError: If logger setup fails
        """
        try:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            self.logger = setup_logger(log_file)
            self.format_type = format_type
            
            self.logger.info(
                f"Initialized {self.__class__.__name__} with {format_type.value} formatting"
            )
            
        except Exception as e:
            raise NotificationError(f"Failed to initialize notifier: {str(e)}")
            
    def __init_subclass__(cls, **kwargs):
        """
        Validate that child classes implement required methods
        
        Raises:
            TypeError: If required methods are not implemented
        """
        super().__init_subclass__(**kwargs)
        
        # Check for send_notification implementation
        if not any(
            'send_notification' in B.__dict__ for B in [cls] + list(cls.__bases__)
        ):
            raise TypeError(
                f"{cls.__name__} must implement send_notification method"
            )
            
    def prepare_notification(self, jobs: List[JobPosting]) -> str:
        """
        Prepare notification message with customizable formatting
        
        Args:
            jobs: List of job postings to format
            
        Returns:
            str: Formatted notification message
            
        Note:
            This method can be overridden by child classes for custom formatting
        """
        self.log_job_details(jobs)
        return self.format_message(jobs, self.format_type)
        
    def format_message(self, 
                      jobs: List[JobPosting], 
                      format_type: FormatType = FormatType.TEXT) -> str:
        """
        Format job listings into a readable message with specified format
        
        Args:
            jobs: List of JobPosting objects
            format_type: Desired format type (text, markdown, html)
            
        Returns:
            str: Formatted message
            
        Raises:
            ValueError: If jobs list is empty or format_type is invalid
        """
        if not jobs:
            return "No new job matches found."
            
        if format_type == FormatType.TEXT:
            return self._format_text(jobs)
        elif format_type == FormatType.MARKDOWN:
            return self._format_markdown(jobs)
        elif format_type == FormatType.HTML:
            return self._format_html(jobs)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
            
    def _format_text(self, jobs: List[JobPosting]) -> str:
        """Format message in plain text"""
        message = "New Job Matches Found!\n\n"
        
        for job in jobs:
            message += f"Company: {job.company}\n"
            message += f"Title: {job.title}\n"
            message += f"Location: {job.location or 'Not specified'}\n"
            if job.salary:
                message += f"Salary: {job.salary}\n"
            if job.url:
                message += f"URL: {job.url}\n"
            message += "-" * 40 + "\n\n"
            
        return message
        
    def _format_markdown(self, jobs: List[JobPosting]) -> str:
        """Format message in Markdown"""
        message = "**🔍 New Job Matches Found!**\n\n"
        
        for job in jobs:
            message += f"**{job.title}**\n"
            message += f"🏢 *{job.company}*\n"
            message += f"📍 {job.location or 'Not specified'}\n"
            if job.salary:
                message += f"💰 {job.salary}\n"
            if job.url:
                message += f"🔗 [View Job]({job.url})\n"
            message += "---\n\n"
            
        return message
        
    def _format_html(self, jobs: List[JobPosting]) -> str:
        """Format message in HTML"""
        message = "<h2>🔍 New Job Matches Found!</h2>\n\n"
        
        for job in jobs:
            message += f"<h3>{job.title}</h3>\n"
            message += f"<p><strong>Company:</strong> {job.company}</p>\n"
            message += f"<p><strong>Location:</strong> {job.location or 'Not specified'}</p>\n"
            if job.salary:
                message += f"<p><strong>Salary:</strong> {job.salary}</p>\n"
            if job.url:
                message += f"<p><a href='{job.url}'>View Job</a></p>\n"
            message += "<hr>\n\n"
            
        return message
        
    def log_job_details(self, jobs: List[JobPosting]) -> None:
        """
        Log detailed information about jobs for debugging
        
        Args:
            jobs: List of job postings to log
        """
        if not jobs:
            self.logger.debug("No jobs to log")
            return
            
        self.logger.debug(f"Logging details for {len(jobs)} jobs:")
        for i, job in enumerate(jobs, 1):
            self.logger.debug(
                f"Job {i}/{len(jobs)}:\n"
                f"  Title: {job.title}\n"
                f"  Company: {job.company}\n"
                f"  Location: {job.location or 'Not specified'}\n"
                f"  URL: {job.url or 'Not available'}"
            )
            
    @abstractmethod
    def send_notification(self, jobs: List[JobPosting]) -> bool:
        """
        Send notification for new job postings
        
        Args:
            jobs: List of JobPosting objects to notify about
            
        Returns:
            bool: True if notification was sent successfully
            
        Note:
            This method must be implemented by child classes
        """
        self.logger.info(
            f"Attempting to send notifications for {len(jobs)} jobs"
        )
        if not jobs:
            self.logger.info("No new jobs to notify about")
            return False
