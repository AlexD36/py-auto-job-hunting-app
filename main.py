"""
Job Alert Notifier - Main entry point
"""
from typing import List
from src.config.config import load_config
from src.utils.logger import setup_logger
from src.scrapers.weworkremotely import WeWorkRemotelyScraper

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
        
        # Scrape jobs
        jobs = scraper.scrape_jobs(config.scraper.keywords)
        
        logger.info(f"Found {len(jobs)} matching jobs")
        
        # Print jobs (for testing)
        for job in jobs:
            print(f"\nTitle: {job.title}")
            print(f"Company: {job.company}")
            print(f"Location: {job.location}")
            print(f"URL: {job.url}")
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
