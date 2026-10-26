from creator_aggregate import CreatorRequest, aggregate, publish_subscriber_update


def main() -> None:
    request = CreatorRequest(
        query="digital creator asset delivery",
        sources=("gumroad.com", "itch.io"),
        subscriber_update="New creator listings are ready for review.",
    )
    listings = aggregate(request)
    result = publish_subscriber_update(request, listings)
    print({"listing_count": len(listings), "queue_message": result})


if __name__ == "__main__":
    main()
