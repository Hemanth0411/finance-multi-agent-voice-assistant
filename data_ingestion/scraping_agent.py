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

# Removed if __name__ == "__main__" block for deployment
# if __name__ == "__main__":
#     # Example usage:
#     async def main():
#         urls = [
#             HttpUrl("http://example.com"),
#             HttpUrl("https://www.google.com/search?q=web+scraping+python"), # Example with query params
#             HttpUrl("http://nonexistentwebsite.invalid") # Example of a URL that will likely fail
#         ]
# 
#         logger.info("Starting scraping process for example URLs...")
#         # For this example, let's assume a simple parsing function or use the generic one.
#         # If specific parsers were defined (like parse_example_com), they could be used.
#         # For simplicity, we'll call scrape_multiple_filings which uses generic parsing.
#         # For demonstration, content_selectors might be customized per URL or a generic one used.
#         documents = await scrape_multiple_filings(urls) # Uses default body selector
# 
#         if documents:
#             logger.info(f"Scraped {len(documents)} documents successfully:")
#             for i, doc in enumerate(documents):
#                 logger.info(f"Document {i+1} from {doc.source}:")
#                 # logger.info(f"  Title: {doc.metadata.get('title', 'N/A')}") # Title not extracted by default
#                 logger.info(f"  Content preview (first 100 chars): {doc.content[:100]}...")
#                 # if doc.metadata.get('links'): # Links not extracted by default
#                 #     logger.info(f"  Found {len(doc.metadata['links'])} links.")
#         else:
#             logger.warning("No documents were scraped from the example URLs.")
# 
#     asyncio.run(main()) 