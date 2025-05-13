import httpx
import asyncio
from selectolax.parser import HTMLParser
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Document(BaseModel):
    source: HttpUrl
    content: str
    metadata: Dict[str, Any] = {}

async def fetch_html(url: HttpUrl) -> str | None:
    """
    Asynchronously fetches HTML content from a given URL.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(str(url))
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching {url}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching {url}: {e}")
    return None

def parse_content(html: str, selectors: List[str]) -> str:
    """
    Parses HTML content and extracts text from specified selectors.
    A simple implementation, might need to be more robust based on actual filing structures.
    """
    tree = HTMLParser(html)
    extracted_texts = []
    for selector in selectors:
        nodes = tree.css(selector)
        for node in nodes:
            extracted_texts.append(node.text(separator=' ', strip=True))
    return " ".join(extracted_texts)

async def scrape_filing(url: HttpUrl, content_selectors: List[str] = ["body"]) -> Document | None:
    """
    Scrapes a single filing document from a URL.
    For now, this is a generic scraper. It might need to be adapted for specific
    filing types (e.g., SEC EDGAR, specific news sites).

    A simpler alternative for "filings" could be to use a news API that aggregates
    financial news/press releases, or RSS feeds from relevant regulatory bodies.
    This would avoid direct web scraping complexities.
    """
    logger.info(f"Attempting to scrape: {url}")
    html_content = await fetch_html(url)
    if html_content:
        # This is a very basic content extraction.
        # For actual filings, more sophisticated parsing rules would be needed.
        # For example, identifying main content, tables, specific sections.
        text_content = parse_content(html_content, content_selectors)
        if not text_content:
            logger.warning(f"No content extracted from {url} with selectors {content_selectors}")
            # Fallback: attempt to get all text if specific selectors fail
            text_content = parse_content(html_content, ["body"])


        logger.info(f"Successfully scraped and parsed content from {url}")
        return Document(source=url, content=text_content, metadata={"parser": "basic_html"})
    else:
        logger.warning(f"Failed to fetch HTML from {url}")
        return None

async def scrape_multiple_filings(urls: List[HttpUrl], content_selectors: List[str] = ["body"]) -> List[Document]:
    """
    Asynchronously scrapes multiple filing documents.
    """
    tasks = [scrape_filing(url, content_selectors) for url in urls]
    results = await asyncio.gather(*tasks)
    return [doc for doc in results if doc is not None]

if __name__ == "__main__":
    async def main():
        # Example usage:
        # Replace with actual URLs of filings you want to scrape.
        # These are placeholder URLs and will likely not work as intended for "filings".
        example_urls = [
            HttpUrl("https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000077/aapl-20230701.htm"), # Example Apple 10-Q
            HttpUrl("https://www.example.com/another-filing") # Placeholder
        ]
        
        # Define CSS selectors for the content you want to extract.
        # This will HIGHLY depend on the structure of the target websites.
        # For SEC filings, you'd need specific selectors for the main document body.
        # For a generic body selector:
        selectors = ["body"] 
        # For a more specific (but still generic example) selector from an SEC filing text part:
        # selectors = ["div.html-content", "div.text-block"] # This is illustrative

        logger.info(f"Starting scraping process for {len(example_urls)} URLs...")
        documents = await scrape_multiple_filings(example_urls, content_selectors=selectors)

        if documents:
            for doc in documents:
                logger.info(f"Scraped from: {doc.source}")
                logger.info(f"Extracted content snippet: {doc.content[:200]}...") # Print a snippet
                logger.info(f"Metadata: {doc.metadata}")
                logger.info("-" * 20)
        else:
            logger.info("No documents were successfully scraped.")

    # Running the async main function
    # In a real FastAPI app, you would call these functions within your route handlers.
    # For direct execution:
    # asyncio.run(main())
    logger.info("Scraping agent module loaded. Run main() for an example.")
    logger.info("NOTE: The example URLs in main() are for demonstration and might not be suitable for actual filings.")
    logger.info("You will need to identify appropriate URLs and CSS selectors for your target financial documents.")
    logger.info("Consider simpler alternatives like News APIs or RSS feeds if direct scraping is too complex for your use case.") 