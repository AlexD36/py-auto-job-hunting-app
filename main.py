"""
Job Alert Notifier - Main entry point
"""
from src.config.config import load_config
from src.utils.logger import setup_logger

def main() -> None:
    """Main application entry point"""
    # Load configuration
    config = load_config()
    
    # Setup logger
    logger = setup_logger(config.log_file)
    logger.info("Starting Job Alert Notifier")
    
    try:
        # TODO: Implement main logic
        logger.info("Environment setup successful")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
