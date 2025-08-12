import time
import requests
import logging
from bs4 import BeautifulSoup
import concurrent.futures
from typing import List, Dict, Union
from core.logger_config import setup_logging

logger = logging.getLogger(__name__)

class ScraperV2:
    """
    A robust and efficient web scraper for Yahoo Finance, based on requests and BeautifulSoup.
    It supports concurrent scraping with retries and exponential backoff.
    """

    def __init__(self, max_workers: int = 5, max_retries: int = 3, delay: float = 0.5):
        """
        Initializes the ScraperV2.

        Args:
            max_workers: The maximum number of concurrent threads for scraping.
            max_retries: The maximum number of retries for a single URL.
            delay: A small delay to add between requests to avoid being blocked.
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def _scrape_single_article(self, url: str) -> Dict[str, Union[str, bool, int]]:
        """
        Scrapes a single article with a retry mechanism.

        Args:
            url: The URL of the article to scrape.

        Returns:
            A dictionary containing the scraped content or an error message.
        """
        for attempt in range(self.max_retries):
            try:
                # Add a small random delay before each request
                time.sleep(self.delay * (attempt + 1))

                response = self.session.get(url, timeout=15)

                if response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited for {url}. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                # Try multiple selectors to find the article content
                selectors = [
                    ('div', {'data-testid': 'article-content-wrapper'}),
                    ('article', {'class': 'article-wrap no-bb'}),
                    ('div', {'class': 'caas-body'}),
                ]

                content_wrapper = None
                for tag, attrs in selectors:
                    content_wrapper = soup.find(tag, attrs)
                    if content_wrapper:
                        break
                
                if content_wrapper:
                    # Clean up scripts and styles
                    for script_or_style in content_wrapper.find_all(['script', 'style']):
                        script_or_style.decompose()

                    paragraphs = content_wrapper.find_all('p')
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    
                    if content:
                        return {
                            'url': url,
                            'success': True,
                            'content': content,
                            'attempt': attempt + 1
                        }

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url} on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {'url': url, 'success': False, 'error': str(e)}
                time.sleep(2 ** attempt)  # Exponential backoff

        return {'url': url, 'success': False, 'error': 'Failed after max retries'}

    def scrape_articles(self, urls: List[str]) -> List[Dict]:
        """
        Scrapes multiple articles in parallel.

        Args:
            urls: A list of article URLs to scrape.

        Returns:
            A list of dictionaries, each containing the result for a single URL.
        """
        logger.info(f"Starting to scrape {len(urls)} articles with {self.max_workers} workers...")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._scrape_single_article, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                results.append(result)
                if result['success']:
                    logger.info(f"Successfully scraped: {result['url'][:70]}...")
                else:
                    logger.error(f"Failed to scrape: {result['url'][:70]}... Error: {result['error']}")

        return results

# Example Usage:
if __name__ == '__main__':
    setup_logging()
    logger.info("--- [SCRAPER_V2] Example Usage ---")
    
    # Create an instance of the new scraper
    scraper_v2 = ScraperV2(max_workers=3, max_retries=2, delay=0.5)
    
    # A list of example URLs to test
    example_urls = [
        "https://finance.yahoo.com/news/live/stock-market-today-dow-sp-500-nasdaq-close-higher-as-nvidia-pops-google-slides-210836970.html",
        "https://finance.yahoo.com/news/live/stock-market-today-dow-sp-500-nasdaq-fall-as-wall-street-digests-earnings-trump-tariffs-200020392.html",
        "https://finance.yahoo.com/news/this-is-a-non-existent-url-for-testing.html" # A failing URL
    ]
    
    # Run the scraping process
    scraped_results = scraper_v2.scrape_articles(example_urls)
    
    logger.info("--- [SCRAPER_V2] Results ---")
    for res in scraped_results:
        if res['success']:
            logger.info(f"URL: {res['url']}\nContent Length: {len(res['content'])}")
            # Save the first successful scrape to a file
            if "https://finance.yahoo.com/news/live/stock-market-today-dow-sp-500-nasdaq-close-higher-as-nvidia-pops-google-slides-210836970.html" in res['url']:
                with open("scraped_content_example.txt", "w", encoding="utf-8") as f:
                    f.write(f"URL: {res['url']}\n\n")
                    f.write(res['content'])
                logger.info("--- Content of the first article has been saved to scraped_content_example.txt ---")
        else:
            logger.error(f"URL: {res['url']}\nError: {res['error']}")