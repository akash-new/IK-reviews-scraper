# config/scraper_config.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PlatformConfig:
    """Represents configuration for a single platform."""
    name: str
    url: str
    scrape_allowed: bool
    search_query: Optional[str] = None  # Optional query for search-based platforms like Reddit

    def __str__(self) -> str:
        return f"Platform(name={self.name}, url={self.url}, scrape_allowed={self.scrape_allowed})"


class ScraperConfig:
    """Manages configuration for all platforms to be scraped."""
    
    def __init__(self):
        # Hardcoded platform configurations (can be replaced with JSON loading later)
        self._platforms = [
            # Reddit removed as we'll implement a different approach
            PlatformConfig(
                name="Quora",
                url="https://www.quora.com/search?q=Interview%20Kickstart",
                scrape_allowed=False  # Quora prohibits scraping in its ToS
            ),
            PlatformConfig(
                name="Course Report",
                url="https://www.coursereport.com/schools/interview-kickstart",
                scrape_allowed=True  # Assuming allowed for POC; verify ToS
            ),
            PlatformConfig(
                name="Trustpilot",
                url="https://www.trustpilot.com/review/interviewkickstart.com",
                scrape_allowed=True  # Assuming allowed for POC; verify ToS
            ),
            PlatformConfig(
                name="Yelp",
                url="https://www.yelp.com/biz/interview-kickstart-santa-clara",  # Example URL
                scrape_allowed=False  # Yelp typically prohibits scraping
            ),
            PlatformConfig(
                name="Google Reviews",
                url="https://www.google.com/search?q=Interview+Kickstart+reviews",  # Placeholder
                scrape_allowed=False  # Google prohibits scraping; requires API
            ),
            PlatformConfig(
                name="Facebook",
                url="https://www.facebook.com/InterviewKickstart/reviews",  # Placeholder
                scrape_allowed=False  # Facebook prohibits scraping
            )
        ]

    @property
    def platforms(self) -> List[PlatformConfig]:
        """Returns the list of configured platforms."""
        return self._platforms

    def get_platform(self, name: str) -> Optional[PlatformConfig]:
        """Retrieve a platform's config by name."""
        for platform in self._platforms:
            if platform.name.lower() == name.lower():
                return platform
        return None

    def get_scrapeable_platforms(self) -> List[PlatformConfig]:
        """Returns a list of platforms where scraping is allowed."""
        return [p for p in self._platforms if p.scrape_allowed]


if __name__ == "__main__":
    # Test the configuration module
    config = ScraperConfig()
    print("All Platforms:")
    for platform in config.platforms:
        print(platform)
    
    print("\nScrapeable Platforms:")
    for platform in config.get_scrapeable_platforms():
        print(platform)
    
    print("\nGet specific platform (Reddit):")
    reddit_config = config.get_platform("Reddit")
    print(reddit_config)