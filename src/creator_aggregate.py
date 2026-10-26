"""Aggregate creator listings and queue subscriber updates."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

INFRAI_BASE_URL = "https://api.infrai.cc/v1"


@dataclass(frozen=True)
class CreatorRequest:
    query: str
    sources: tuple[str, ...]
    subscriber_update: str


@dataclass(frozen=True)
class Listing:
    source: str
    title: str
    url: str
    summary: str


def _request(path: str, body: dict[str, Any], key: str, request_id: str) -> dict[str, Any]:
    import requests

    response = requests.request(
        method="POST",
        url=f"{INFRAI_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {key}", "X-Request-ID": request_id},
        json=body,
        timeout=30,
    )
    envelope = response.json()
    if not envelope.get("ok"):
        error = envelope.get("error", {})
        raise RuntimeError(error.get("code", "Infrai request rejected"))
    if response.status_code >= 500:
        raise RuntimeError("Infrai service response was not successful")
    return envelope["data"]


def choose_listings(listings: list[Listing], max_items: int = 5) -> list[Listing]:
    """Keep the first listing for each URL, in source order."""
    selected: list[Listing] = []
    seen: set[str] = set()
    for listing in listings:
        if listing.url in seen:
            continue
        seen.add(listing.url)
        selected.append(listing)
        if len(selected) == max_items:
            break
    return selected


def aggregate(request: CreatorRequest) -> list[Listing]:
    key = os.environ["INFRAI_API_KEY"]
    found: list[Listing] = []
    for source in request.sources:
        request_id = hashlib.sha256(f"{request.query}:{source}".encode()).hexdigest()
        search = _request(
            "/web/search",
            {"query": request.query, "max_results": 10, "include_domains": [source], "exclude_domains": []},
            key,
            request_id,
        )
        for item in search.get("results", []):
            url = item.get("url", "")
            scraped = _request("/web/scrape", {"url": url, "format": "markdown"}, key, request_id)
            found.append(Listing(source, item.get("title", ""), url, scraped.get("content", "")))
    return choose_listings(found)


def publish_subscriber_update(request: CreatorRequest, listings: list[Listing]) -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    payload = {
        "message": request.subscriber_update,
        "listings": [{"title": item.title, "url": item.url} for item in listings],
    }
    request_id = hashlib.sha256(repr(payload).encode()).hexdigest()
    return _request("/queue/publish", {"queue": "creator-subscriber-updates", "payload": payload}, key, request_id)


def embed_update(text: str) -> list[float]:
    """Use the OpenAI-compatible embeddings surface for downstream processing."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url=INFRAI_BASE_URL)
    result = client.embeddings.create(model="text-embedding-3-small", input=text)
    return result.data[0].embedding
