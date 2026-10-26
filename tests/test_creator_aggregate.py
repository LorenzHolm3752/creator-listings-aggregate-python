from src.creator_aggregate import Listing, choose_listings


def test_choose_listings_deduplicates_urls_and_caps_the_batch() -> None:
    listings = [
        Listing("one", "First", "https://example.test/a", "a"),
        Listing("two", "Same item", "https://example.test/a", "duplicate"),
        Listing("three", "Second", "https://example.test/b", "b"),
    ]

    chosen = choose_listings(listings, max_items=2)

    assert [(item.source, item.url) for item in chosen] == [
        ("one", "https://example.test/a"),
        ("three", "https://example.test/b"),
    ]
