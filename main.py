"""
Job Alert Notifier - Main entry point
"""
from src.config.config import load_config
from src.utils.logger import setup_logger
from src.utils.filters import JobFilter, ROMANIA_FILTER_CRITERIA
from src.scrapers.remoteco import RemoteCoScraper
from src.scrapers.linkedin import LinkedInScraper
from src.scrapers.weworkremotely import WeWorkRemotelyScraper
from src.scrapers.ejobs_ro import EJobsRoScraper
from src.scrapers.hipo_ro import HipoRoScraper
from src.scrapers.bestjobs_ro import BestJobsRoScraper
from src.scrapers.base import BaseScraper
from src.notifications.email_notifier import EmailNotifier
from src.notifications.telegram_notifier import TelegramNotifier
from typing import List, Type
import os
import asyncio

# Define all available scrapers
SCRAPERS: List[Type[BaseScraper]] = [
    RemoteCoScraper,
    LinkedInScraper,
    WeWorkRemotelyScraper,
    EJobsRoScraper,
    HipoRoScraper,
    BestJobsRoScraper
]

async def main() -> None:
    """Main application entry point"""
    # Load configuration
    config = load_config()
    
    # Setup logger
    logger = setup_logger(config.log_file)
    logger.info("Starting Job Alert Notifier")
    
    try:
        # Initialize job filter
        job_filter = JobFilter(ROMANIA_FILTER_CRITERIA)
        
        # Initialize notifiers
        email_notifier = EmailNotifier(
            smtp_server=config.email.smtp_server,
            smtp_port=config.email.smtp_port,
            sender_email=config.email.sender_email,
            sender_password=config.email.sender_password,
            recipient_email=config.email.recipient_email
        )
        
        telegram_notifier = await TelegramNotifier.create(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID")
        )
        
        # Aggregate jobs from all scrapers
        all_jobs = []
        for scraper_class in SCRAPERS:
            try:
                scraper = scraper_class()
                jobs = scraper.scrape_jobs(ROMANIA_FILTER_CRITERIA.keywords)
                logger.info(f"Found {len(jobs)} jobs from {scraper_class.__name__}")
                all_jobs.extend(jobs)
            except Exception as scraper_error:
                logger.error(f"Error with {scraper_class.__name__}: {str(scraper_error)}")
                continue
        
        logger.info(f"Found {len(all_jobs)} total jobs across all sources")
        
        # Filter jobs
        filtered_jobs = job_filter.filter_jobs(all_jobs)
        logger.info(f"Found {len(filtered_jobs)} matching jobs for Romania")
        
        # Send notifications if there are matching jobs
        if filtered_jobs:
            email_notifier.send_notification(filtered_jobs)
            telegram_notifier.send_notification(filtered_jobs)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
