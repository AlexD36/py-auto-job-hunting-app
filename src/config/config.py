"""
Configuration settings for the Job Alert Notifier
"""
import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_email: str

@dataclass
class ScraperConfig:
    """Scraper configuration settings"""
    keywords: List[str]
    locations: List[str]
    check_interval: int  # in hours
    max_results_per_site: int

@dataclass
class Config:
    """Main configuration class"""
    email: EmailConfig
    scraper: ScraperConfig
    log_file: str

def load_config() -> Config:
    """Load configuration from environment variables"""
    load_dotenv()
    
    email_config = EmailConfig(
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        sender_email=os.getenv("SENDER_EMAIL", ""),
        sender_password=os.getenv("SENDER_PASSWORD", ""),
        recipient_email=os.getenv("RECIPIENT_EMAIL", "")
    )
    
    scraper_config = ScraperConfig(
        keywords=os.getenv("KEYWORDS", "python,developer").split(","),
        locations=os.getenv("LOCATIONS", "remote").split(","),
        check_interval=int(os.getenv("CHECK_INTERVAL", "24")),
        max_results_per_site=int(os.getenv("MAX_RESULTS", "10"))
    )
    
    return Config(
        email=email_config,
        scraper=scraper_config,
        log_file="logs/job_alert.log"
    ) 