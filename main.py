"""
Job Alert Notifier - Main entry point
"""
from src.config.config import load_config
from src.utils.logger import setup_logger
from src.utils.filters import JobFilter, ROMANIA_FILTER_CRITERIA
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
        
        # Initialize job filter
        job_filter = JobFilter(ROMANIA_FILTER_CRITERIA)
        
        # Scrape jobs
        all_jobs = scraper.scrape_jobs(ROMANIA_FILTER_CRITERIA.keywords)
        logger.info(f"Found {len(all_jobs)} total jobs")
        
        # Filter jobs
        filtered_jobs = job_filter.filter_jobs(all_jobs)
        logger.info(f"Found {len(filtered_jobs)} matching jobs for Romania")
        
        # Print filtered jobs (for testing)
        for job in filtered_jobs:
            print("\n" + "="*50)
            print(f"Title: {job.title}")
            print(f"Company: {job.company}")
            print(f"Location: {job.location}")
            print(f"URL: {job.url}")
            print("="*50)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
