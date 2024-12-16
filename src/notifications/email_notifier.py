"""
Email notification implementation with retry logic and connection optimization
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import socket
import time
from functools import wraps
from smtplib import (
    SMTPException,
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPServerDisconnected,
    SMTPDataError,
    SMTPHeloError,
    SMTPNotSupportedError,
    SMTPSenderRefused,
    SMTPRecipientsRefused
)
from .base import BaseNotifier
from src.scrapers.base import JobPosting

class EmailNotifierError(Exception):
    """Base exception for email notification errors"""
    pass

def retry_smtp(max_tries: int = 3, delay: int = 2, backoff: float = 1.5, 
               exceptions: tuple = (SMTPException, socket.error)):
    """
    Retry decorator for SMTP operations
    
    Args:
        max_tries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            tries_remaining = max_tries
            current_delay = delay
            
            while tries_remaining > 0:
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    tries_remaining -= 1
                    if tries_remaining == 0:
                        raise
                    
                    self.logger.warning(
                        f"SMTP operation failed: {str(e)}. "
                        f"Retrying in {current_delay} seconds... "
                        f"({tries_remaining} tries remaining)"
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return False
        return wrapper
    return decorator

class EmailNotifier(BaseNotifier):
    """Email notification system with retry logic and connection optimization"""
    
    # HTML email template
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f5f5f5; }
            tr:hover { background-color: #f9f9f9; }
            .job-title { color: #2c5282; font-weight: bold; }
            .company-name { color: #444; }
            .location { color: #666; }
            .date { color: #888; font-size: 0.9em; }
            .description { color: #444; margin: 10px 0; }
            .view-job { 
                display: inline-block;
                padding: 5px 10px;
                background-color: #3182ce;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .view-job:hover {
                background-color: #2b6cb0;
            }
            .header { margin-bottom: 20px; }
            .footer { margin-top: 20px; color: #666; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>New Job Alerts ({job_count} matches)</h2>
            <p>Found on {current_date}</p>
        </div>
        
        <table>
            <tr>
                <th>Job Title & Company</th>
                <th>Location</th>
                <th>Posted Date</th>
                <th>Action</th>
            </tr>
            {job_rows}
        </table>
        
        <div class="footer">
            <p>Job details and descriptions are provided below:</p>
            {job_details}
        </div>
    </body>
    </html>
    """
    
    # Connection cache timeout (5 minutes)
    CONNECTION_TIMEOUT = 300
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 sender_email: str, sender_password: str, 
                 recipient_email: str):
        """Initialize email notifier with connection caching"""
        super().__init__()
        
        # Validate input parameters
        if not all([smtp_server, smtp_port, sender_email, sender_password, recipient_email]):
            raise ValueError("All email configuration parameters must be provided")
            
        if not isinstance(smtp_port, int) or smtp_port <= 0:
            raise ValueError("SMTP port must be a positive integer")
            
        if not "@" in sender_email or not "@" in recipient_email:
            raise ValueError("Invalid email address format")
            
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        
        # Connection caching
        self._smtp_connection: Optional[smtplib.SMTP] = None
        self._last_connection_time: Optional[datetime] = None
        
    def __del__(self):
        """Cleanup SMTP connection on object destruction"""
        self._close_connection()
        
    def _close_connection(self) -> None:
        """Safely close SMTP connection"""
        if self._smtp_connection:
            try:
                self._smtp_connection.quit()
            except Exception as e:
                self.logger.warning(f"Error closing SMTP connection: {str(e)}")
            finally:
                self._smtp_connection = None
                self._last_connection_time = None
                
    def _get_connection(self) -> smtplib.SMTP:
        """
        Get SMTP connection, reusing existing one if valid
        
        Returns:
            smtplib.SMTP: Active SMTP connection
            
        Raises:
            SMTPException: If connection fails
        """
        current_time = datetime.now()
        
        # Check if existing connection is valid and not expired
        if (self._smtp_connection and self._last_connection_time and 
            (current_time - self._last_connection_time).total_seconds() < self.CONNECTION_TIMEOUT):
            try:
                # Test connection with NOOP
                self._smtp_connection.noop()
                return self._smtp_connection
            except (SMTPException, socket.error):
                self._close_connection()
        
        # Create new connection if needed
        if not self._smtp_connection:
            try:
                connection = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                connection.starttls()
                connection.login(self.sender_email, self.sender_password)
                
                self._smtp_connection = connection
                self._last_connection_time = current_time
                
            except Exception as e:
                self._close_connection()
                raise
                
        return self._smtp_connection

    def format_message(self, jobs: List[JobPosting]) -> Tuple[str, str]:
        """
        Format job listings into both plain text and HTML formats
        
        Args:
            jobs: List of JobPosting objects
            
        Returns:
            Tuple[str, str]: (plain_text_message, html_message)
            
        Raises:
            EmailNotifierError: If message formatting fails
        """
        try:
            # Format plain text version
            plain_text = self._format_plain_text(jobs)
            
            # Format HTML version
            html = self._format_html(jobs)
            
            return plain_text, html
            
        except Exception as e:
            self.logger.error(f"Error formatting email message: {str(e)}")
            raise EmailNotifierError(f"Failed to format email message: {str(e)}")

    def _format_plain_text(self, jobs: List[JobPosting]) -> str:
        """Format jobs as plain text"""
        lines = ["New Job Matches:\n"]
        
        for i, job in enumerate(jobs, 1):
            lines.extend([
                f"\n{i}. {job.title}",
                f"Company: {job.company}",
                f"Location: {job.location}",
                f"Posted: {job.posted_date or 'Date not available'}",
                f"URL: {job.url}",
                "\nDescription:",
                job.description[:500] + "..." if len(job.description) > 500 else job.description,
                "-" * 80
            ])
            
        return "\n".join(lines)

    def _format_html(self, jobs: List[JobPosting]) -> str:
        """Format jobs as HTML"""
        job_rows = []
        job_details = []
        
        for i, job in enumerate(jobs, 1):
            # Format table row
            job_rows.append(f"""
                <tr>
                    <td>
                        <div class="job-title">{job.title}</div>
                        <div class="company-name">{job.company}</div>
                    </td>
                    <td class="location">{job.location}</td>
                    <td class="date">{job.posted_date or 'Date not available'}</td>
                    <td><a href="{job.url}" class="view-job">View Job</a></td>
                </tr>
            """)
            
            # Format detailed description
            job_details.append(f"""
                <div style="margin-bottom: 30px;">
                    <h3>{i}. {job.title}</h3>
                    <div class="company-name">Company: {job.company}</div>
                    <div class="location">Location: {job.location}</div>
                    <div class="date">Posted: {job.posted_date or 'Date not available'}</div>
                    <div class="description">
                        <h4>Description:</h4>
                        <p>{job.description[:500] + "..." if len(job.description) > 500 else job.description}</p>
                    </div>
                    <a href="{job.url}" class="view-job">View Full Job Details</a>
                </div>
                <hr>
            """)
        
        # Fill template
        html = self.HTML_TEMPLATE.format(
            job_count=len(jobs),
            current_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            job_rows="\n".join(job_rows),
            job_details="\n".join(job_details)
        )
        
        return html

    @retry_smtp(max_tries=3, delay=2)
    def send_notification(self, jobs: List[JobPosting]) -> bool:
        """
        Send email notification with retry logic and connection reuse
        
        Args:
            jobs: List of JobPosting objects to notify about
            
        Returns:
            bool: True if notification was sent successfully
            
        Raises:
            SMTPException: If all retry attempts fail
            EmailNotifierError: For other persistent errors
        """
        if not jobs:
            self.logger.warning("No jobs provided for notification")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"New Job Alerts ({len(jobs)} matches)"
            
            # Add both plain text and HTML versions
            plain_text, html = self.format_message(jobs)
            msg.attach(MIMEText(plain_text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            # Get connection and send message
            connection = self._get_connection()
            connection.send_message(msg)
            
            self.logger.info(f"Successfully sent email notification for {len(jobs)} jobs")
            return True
            
        except SMTPServerDisconnected:
            self._close_connection()
            raise
            
        except (SMTPException, socket.error) as e:
            self.logger.error(f"Error sending email: {str(e)}")
            self._close_connection()
            raise
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self._close_connection()
            raise EmailNotifierError(f"Failed to send email notification: {str(e)}")
