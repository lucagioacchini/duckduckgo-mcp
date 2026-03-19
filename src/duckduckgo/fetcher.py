import httpx
import re

from bs4 import BeautifulSoup

from utils.rate_limiter import RateLimiter
from llm.client import ContentExtractor


class WebContentFetcher:
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)
        self.extractor = ContentExtractor()

    async def fetch_and_parse(self, url: str, query: str) -> str:
        """Fetch a webpage and return only the content relevant to *query*."""
        try:
            await self.rate_limiter.acquire()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get the text content
            text = soup.get_text()

            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return await self.extractor.extract_relevant(text, query)

        except httpx.TimeoutException:
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"