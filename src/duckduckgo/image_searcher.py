import re
import sys
import traceback
from typing import List, Tuple

import httpx

from utils.rate_limiter import RateLimiter
from models.models import ImageResult


class DuckDuckGoImageSearcher:
    SEARCH_URL = "https://duckduckgo.com/"
    IMAGES_URL = "https://duckduckgo.com/i.js"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # The i.js endpoint is an XHR-only API and 403s without these extra headers
    IMAGES_HEADERS = {
        **HEADERS,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://duckduckgo.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    async def _get_vqd(self, client: httpx.AsyncClient, query: str) -> str:
        """Retrieve the vqd search token DuckDuckGo requires for the image API."""
        response = await client.get(
            self.SEARCH_URL, params={"q": query}, headers=self.HEADERS, timeout=30.0
        )
        response.raise_for_status()

        match = re.search(r"vqd=['\"]?([\d-]+)['\"&]", response.text)
        if not match:
            raise ValueError("Could not retrieve DuckDuckGo search token (vqd)")

        return match.group(1)

    async def search_images(
        self, query: str, max_results: int = 10
    ) -> List[ImageResult]:
        try:
            await self.rate_limiter.acquire()

            async with httpx.AsyncClient() as client:
                vqd = await self._get_vqd(client, query)

                response = await client.get(
                    self.IMAGES_URL,
                    params={"q": query, "vqd": vqd, "o": "json", "f": ",,,", "p": "1"},
                    headers=self.IMAGES_HEADERS,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    ImageResult(
                        title=item.get("title", ""),
                        image_url=item.get("image", ""),
                        thumbnail_url=item.get("thumbnail", ""),
                        source=item.get("url", ""),
                        width=item.get("width", 0),
                        height=item.get("height", 0),
                    )
                )

                if len(results) >= max_results:
                    break

            return results

        except httpx.TimeoutException:
            return []
        except httpx.HTTPError:
            return []
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return []

    async def get_image(self, query: str) -> Tuple[bytes, str]:
        """Search for *query* and download the bytes of the first matching image."""
        results = await self.search_images(query, max_results=1)
        if not results:
            raise ValueError(f"No images found for query: {query}")

        image_url = results[0].image_url

        await self.rate_limiter.acquire()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                image_url, headers=self.HEADERS, follow_redirects=True, timeout=30.0
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/jpeg").split(";")[0]

        return response.content, content_type
