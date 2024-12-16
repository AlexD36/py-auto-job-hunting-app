"""
Scraper factory and initialization
"""
from typing import List
from .base import BaseScraper
from .indeed import IndeedScraper
from .bestjobs import BestJobsRoScraper
from .weworkremotely import WeWorkRemotelyScraper
from .ejobs import EJobsRoScraper
from .hipo import HipoRoScraper
from .linkedin import LinkedInScraper
from .remoteco import RemoteCoScraper

def get_all_scrapers() -> List[BaseScraper]:
    """
    Get instances of all available scrapers
    
    Returns:
        List of scraper instances
    """
    return [
        IndeedScraper(),
        BestJobsRoScraper(),
        WeWorkRemotelyScraper(),
        EJobsRoScraper(),
        HipoRoScraper(),
        LinkedInScraper(),
        RemoteCoScraper()
    ]
