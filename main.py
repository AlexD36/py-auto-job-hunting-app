"""
Job Alert Notifier - Main entry point
"""
from src.config.config import load_config
from src.utils.logger import setup_logger
from src.utils.filters import JobFilter, ROMANIA_FILTER_CRITERIA
from src.scrapers.weworkremotely import WeWorkRemotelyScraper
from src.notifications.email_notifier import EmailNotifier
from src.notifications.telegram_notifier import TelegramNotifier

def main() -> None:
    """Main application entry point"""
    # Load configuration
    config = load_config()
    
    # Setup logger
    logger = setup_logger(config.log_file)
    logger.info("Starting Job Alert Notifier")
    
    try:
        # Initialize scraper
        scraper = WeWorkRemotelyScraper()
        
        # Initialize job filter
        job_filter = JobFilter(ROMANIA_FILTER_CRITERIA)
        
        # Initialize notifier (example with email)
        notifier = EmailNotifier(
            smtp_server=config.email.smtp_server,
            smtp_port=config.email.smtp_port,
            sender_email=config.email.sender_email,
            sender_password=config.email.sender_password,
            recipient_email=config.email.recipient_email
        )
        
        # Scrape jobs
        all_jobs = scraper.scrape_jobs(ROMANIA_FILTER_CRITERIA.keywords)
        logger.info(f"Found {len(all_jobs)} total jobs")
        
        # Filter jobs
        filtered_jobs = job_filter.filter_jobs(all_jobs)
        logger.info(f"Found {len(filtered_jobs)} matching jobs for Romania")
        
        # Send notifications if there are matching jobs
        if filtered_jobs:
            notifier.send_notification(filtered_jobs)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
