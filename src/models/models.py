from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int

@dataclass
class ImageResult:
    title: str
    image_url: str
    thumbnail_url: str
    source: str
    width: int
    height: int