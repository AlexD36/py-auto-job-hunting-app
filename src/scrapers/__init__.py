"""
Scraper factory and initialization
"""
from typing import List
from .base import BaseScraper
from .bestjobs_ro import BestJobsRoScraper
from .weworkremotely import WeWorkRemotelyScraper
from .ejobs_ro import EJobsRoScraper
from .hipo_ro import HipoRoScraper
from .linkedin import LinkedInScraper
from .remoteco import RemoteCoScraper

def get_all_scrapers() -> List[BaseScraper]:
    """
    Get instances of all available scrapers
    
    Returns:
        List of scraper instances
    """
    return [
        BestJobsRoScraper(),
        WeWorkRemotelyScraper(),
        EJobsRoScraper(),
        HipoRoScraper(),
        LinkedInScraper(),
        RemoteCoScraper()
    ]
